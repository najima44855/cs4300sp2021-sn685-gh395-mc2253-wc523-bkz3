from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import numpy as np 
import pickle

# Todo: weighted similarity score, document embeddings
# Optional: add alternative names/titles to manga

# Input Processing
with open('dataset_1000_d.pickle','rb') as f:
    manga_list = pickle.load(f) #a dictionary

index_to_manga_name = dict()
index_to_manga = dict()
for i, manga_item in enumerate(manga_list.values()):
    index_to_manga_name[i] = manga_item['title']
    index_to_manga[i] = (manga_item['synopsis'], manga_item['main_picture']['large'])

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
        return np.arrange(num_manga), np.zeros(num_manga)
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
        return np.arrange(num_manga), np.zeros(num_manga)

    input_manga_list = list(set(input_manga_list)) #avoid dealing with duplicates
    #if genre in half or more of the manga in the input manga list, use the genre in the sim measure
    genre_count = defaultdict(int)
    for m in input_manga_list:
        for genre in input_manga_to_genre_dict[m]:
            genre_count[genre] += 1
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