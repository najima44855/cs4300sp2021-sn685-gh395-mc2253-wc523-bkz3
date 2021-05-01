from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import numpy as np 
import pickle
import requests
import secrets
import os
import json
from gensim.models import Word2Vec

# Todo: weighted similarity score, document embeddings
# Optional: add alternative names/titles to manga

# Input Processing
# with open('dataset_1000_d.pickle','rb') as f:
#    manga_list = pickle.load(f) # a dictionary

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

# Generate new code verifier and code challenge (a randomly generated string 
# 128 characters long)
token = secrets.token_urlsafe(100)
token = token[:128]

url = f'https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&code_challenge={token}'
print(f'Use this url to authroize the application: {url}\n')
authorisation_code = input('Please enter the Authorisation Code: ').strip()

AUTH_URL = 'https://myanimelist.net/v1/oauth2/token'
auth_response = requests.post(AUTH_URL, {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': authorisation_code,
    'code_verifier': token,
    'grant_type': 'authorization_code'
})
# print('\n')
# print(auth_response)
# print('\n')

# Convert the response to json
auth_response_data = auth_response.json()
# auth_response.close()
# print(auth_response_data)

# Save the access and refresh tokens
access_token = auth_response_data['access_token']
refresh_token = auth_response_data['refresh_token']
# print(f"access token: {access_token}")
# print(f"refresh token: {refresh_token}")

# Request the top 1000 manga by ranking (needs 2 calls)
ranking_url_1 = 'https://api.myanimelist.net/v2/manga/ranking?ranking_type=manga&limit=500'
ranking_url_2 = 'https://api.myanimelist.net/v2/manga/ranking?ranking_type=manga&limit=500&offset=500'
header = {
    'Authorization': f'Bearer {access_token}'
}
# print(f"header: {header}")

ranking_response_1 = requests.get(ranking_url_1, headers = header)
ranking_1 = ranking_response_1.json()
# ranking_response_1.close()

ranking_response_2 = requests.get(ranking_url_2, headers = header)
ranking_2 = ranking_response_2.json()
# ranking_response_2.close()

# print(ranking_1)
# print(ranking_2)

manga_list= dict()

for x in ranking_1['data']:
    manga_list[x["ranking"]["rank"]] = x["node"]
print(list(manga_list.values())[:10])

index_to_manga_name = dict()
index_to_manga = dict()
for i, manga_item in enumerate(manga_list.values()):
    index_to_manga_name[i] = manga_item['title']
    index_to_manga[i] = (manga_item['synopsis'], manga_item['main_picture']['large'])

manga_synonym_dict = dict() #manga title-> main title
for manga_item in manga_list.values():
    all_names = set()
    main_title = manga_item['title']
    all_names.add(main_title.lower())
    for title in manga_item['alternative_titles']['synonyms']:
        all_names.add(title.lower())
    if manga_item['alternative_titles']['en'] != '':
        all_names.add(manga_item['alternative_titles']['en'].lower())
    if manga_item['alternative_titles']['ja'] != '':
        all_names.add(manga_item['alternative_titles']['ja'].lower()) 
    for title in all_names:
        manga_synonym_dict[title] = main_title


model = Word2Vec.load('word2vec.model')
def add_to_query(query):
    words_in_model= set(model.wv.key_to_index.keys())
    new_query = ""
    for word in query:
        new_query += query + " "
        if word in words_in_model:
            for ele in model.wv.most_similar(word, topn=3):
                new_query += ele[0] + " "
    return new_query

"""
Given a manga, return the cosine similarity between the it and the query.
Parameters:
manga_name: String (The name of the manga to be compared)
tfidf: TfidfVectorizer
Returns: 

def cos_sim(manga_name, tfidf):
    query = manga_name_to_index['query']
    manga_index = manga_name_to_index[manga_name]
    query_norm = np.linalg.norm(tfidf[query])
    manga_norm = np.linalg.norm(tfidf[manga_index])

    return np.dot(tfidf[manga_index], tfidf[query]) / np.dot(query_norm, manga_norm)
"""

"""
#testing for zero and nan vectors
count1 = 0
count2 = 0
for vec in tfidfmatrix:
    if not vec.any():
        count1+=1
    if True in np.isnan(vec):
        count2+=1
"""
"""
Given the tfidf representations of the data and the query, compute the ranking of 
cosine similarity scores.

Parameters:
-tfidfmat (dxf): tfidf representation of the data
-tfidfq (1xf): tfidf representation of the query

Returns:
-list of ranked manga by name
-a np array (1xd) with the ranking of each manga 
e.g. index 0 in the array is the highest ranked
-a np array (1xd) with the cos sim score of each manga
e.g. index 0 of the array gives the cos sim score to manga 0
"""
def cos_sim_rank(tfidfmat, tfidfq, idx, num_manga):
    if not tfidfq.any(): #no query
        return [], np.arange(num_manga), np.zeros(num_manga)
    docnorms = np.linalg.norm(tfidfmat, axis=1, keepdims=True) 
    docnorms[docnorms==0] = 1
    tfidfmat = tfidfmat/docnorms
    tfidfq = tfidfq/np.linalg.norm(tfidfq)
    cos_scores = np.sum(tfidfmat*tfidfq, axis=1) #index of manga -> cos sim score

    results = []#contains names ranked
    for manga_idx in cos_scores.argsort()[::-1]:
        results.append(idx[manga_idx])
    return results, cos_scores.argsort()[::-1], cos_scores


"""
Given a list of manga, return the jaccard similarity of their genres.
Parameters:
manga_list: List(String) (the list of manga to be compared)
input_manga_to_genre_dict: Dictionary
Returns: Int (The Jaccard similarity score of the given list)

def jaccard(input_manga_list, input_manga_to_genre_dict):
    if len(input_manga_list) == 0:
        return 0
    intersection_set = set(input_manga_list[0])
    union_set = set(input_manga_list[0])
    for m in input_manga_list[1:]:
        genres = set(input_manga_to_genre_dict[m])
        intersection_set = intersection_set.intersection(genres)
        union_set = union_set.union(genres)
    
    return len(intersection_set) / len(union_set)
"""

"""
Given an input manga list to be similar to, computes the common genres in this
list (50% occurance or greater).
Then compute the jaccard score for each manga in the data, and rank them.
Parameters:
-manga_list: List(String) (the list of manga to be compared)
-input_manga_to_genre_dict: Dictionary from manga names to genre
-input_manga_to_index_dict: Dictionary from manga names to index

Returns:
-list of ranked manga by name
-a np array (1xd) with the ranking of each manga 
e.g. index 0 in the array is the highest ranked
-a np array (1xd) with the jaccard sim score of each manga
e.g. index 0 of the array gives the jaccard sim score to manga 0
"""
def grouped_jac_rank(input_manga_list, input_manga_to_genre_dict, input_manga_to_index_dict, idx, num_manga):
    if len(input_manga_list) == 0: #no input manga
        return [], np.arange(num_manga), np.zeros(num_manga)

    input_manga_list = list(set(input_manga_list)) #avoid dealing with duplicates
    #if genre in half or more of the manga in the input manga list, use the genre in the sim measure
    genre_count = defaultdict(int)
    for m in input_manga_list:
        try:
            m = manga_synonym_dict[m.lower()]
            for genre in input_manga_to_genre_dict[m]:
                genre_count[genre] += 1
        except:
            continue
    thresh = len(input_manga_list)/2 #change threshhold here

    common_genres = set()
    for genre in genre_count:
        if genre_count[genre] >= thresh:
            common_genres.add(genre)

    jac_scores = np.zeros(num_manga)
    for m in input_manga_to_genre_dict:
        genres = set(input_manga_to_genre_dict[m])
        intersection_set = common_genres.intersection(genres)
        union_set = common_genres.union(genres)
        jac_scores[input_manga_to_index_dict[m]] = len(intersection_set)/len(union_set)

    results = []
    for manga_idx in jac_scores.argsort()[::-1]:
        results.append(idx[manga_idx])
    return results, jac_scores.argsort()[::-1], jac_scores