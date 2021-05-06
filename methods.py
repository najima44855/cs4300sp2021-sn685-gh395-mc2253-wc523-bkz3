from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from collections import defaultdict
import numpy as np 
import pickle
import re
from gensim.models import Word2Vec

# Todo: weighted similarity score, document embeddings
# Optional: add alternative names/titles to manga

# Input Processing
with open('dataset_1000_d.pickle','rb') as f:
    manga_list = pickle.load(f) #a dictionary

"""
Given a list/set containing keywords in original query, a list/set containing keywords found
by word embeddings, and a synopsis, return the synopsis with the appropriate span html tag.
Parameters: 
orig_query: list/set of strings
sim_query: list/set of strings
text: string
Returns:
-modified with words in orig_query and sim_query highlighted by html tags.
"""
def highlight(orig_query, sim_query, text):
    if len(orig_query)==0:
        return text
    else:
        text = get_new_query(orig_query, text, True)
        text = get_new_query(sim_query, text, False)
        return text

"""
helper function for highlight. Given terms to highlight in text, returns the text with 
the appropriate highlighting given by is_orig_term
Parameters:
terms: list/set of strings
text: string
is_orig_term: True if from original query, false otherwise
Returns:
-text with highlight html tags
"""        
def get_new_query(terms, text, is_orig_term):
    for term in terms:
        p = re.compile(r"\b"+term+r"\b", re.IGNORECASE)
        word_len = len(term)
        start_idx = []
        groups = []
        for m in p.finditer(text):
            start_idx.append(m.start())
            groups.append(m.group())
        for r in range(len(start_idx)):
            start_idx[r] = start_idx[r]+r*30
        if is_orig_term:
            for i, idx in enumerate(start_idx):
                text = text[:idx]+"<span class=highlight1>"+groups[i]+"</span>"+text[idx+word_len:]
        else:
            for i, idx in enumerate(start_idx):
                text = text[:idx]+"<span class=highlight2>"+groups[i]+"</span>"+text[idx+word_len:]
    return text

#need these dictionaries to get info from top matches later
index_to_id = dict()
id_to_index = dict()
index_to_manga_name = dict()
index_to_manga_synopsis = dict()
index_to_manga_pic = dict()
index_to_rating = dict()
index_to_readers = dict()
name_to_id = dict()
for i, manga_item in enumerate(manga_list.values()):
    index_to_id[i] = manga_item['id']
    id_to_index[manga_item['id']] = i
    index_to_manga_name[i] = manga_item['title']
    index_to_manga_synopsis[i] = manga_item['synopsis']
    index_to_manga_pic[i] = manga_item['main_picture']['large']
    index_to_rating[i] = manga_item['mean']
    index_to_readers[i] = manga_item['num_list_users']
    name_to_id[manga_item['title']] = manga_item['id']

manga_synonym_dict = dict() #manga title-> main title
manga_titles = set() #contains every manga name (capitalized)
for manga_item in manga_list.values():
    all_names = set()
    main_title = manga_item['title']
    all_names.add(main_title.lower())
    manga_titles.add(main_title)
    for title in manga_item['alternative_titles']['synonyms']:
        all_names.add(title.lower())
        manga_titles.add(title)
    if manga_item['alternative_titles']['en'] != '':
        all_names.add(manga_item['alternative_titles']['en'].lower())
        manga_titles.add(manga_item['alternative_titles']['en'])
    if manga_item['alternative_titles']['ja'] != '':
        all_names.add(manga_item['alternative_titles']['ja'].lower()) 
        manga_titles.add(manga_item['alternative_titles']['ja']) 
    for title in all_names:
        manga_synonym_dict[title] = main_title


model = Word2Vec.load('word2vec.model')
"""
Given an original query, attempt to do query expansion by adding top 3 most relevant
words for each word in query as found by word embeddings model. Weights original 
terms 2x as much as relevant terms.
Parameters:
-query:string
Returns:
-a list containing a single string (modified query)
-a set containing words in original query
-a list containing words added to query
"""
def add_to_query(query):
    words_in_model= set(model.wv.key_to_index.keys())
    new_query = ""
    original_query= []
    similar_query = []
    similar_query_set = set()
    vectorizer = CountVectorizer(stop_words='english')
    query_vec = vectorizer.fit_transform([query]).toarray()
    all_words = vectorizer.get_feature_names()
    for idx, n in enumerate(query_vec[0]):
        word = all_words[idx]
        for j in range(n):
            new_query += word + " " + word + " " #weights original keyterm 2x as much as similar words
            original_query.append(word)
            if word in words_in_model:
                for ele in model.wv.most_similar(word, topn=3):
                    w = ele[0]
                    new_query += w + " "
                    if w not in similar_query_set:
                        similar_query_set.add(w)
                        similar_query.append(w)
    return [new_query], set(original_query), similar_query

"""
If text has a length greater than 350, inserts html tags for read me section to hide the extra text.
Does this in a "smart" way by inserting within spaces.
Parameters:
-text:string
Returns:
-modified text string with html tags if len>350
-True if html tags were inserted, False if not
"""
def insert_readmore(text):
    p = re.compile(r'\s')
    l = [m.start() for m in p.finditer(text)]
    idx = binsearch(l, 350)
    if idx == -1:
        return text, False
    else:
        text = text[:l[idx]] + '<span class="dots" style="display: inline;">...</span><span class="more" style="display: none;">' + text[l[idx]:] +"</span>"
        return text, True
        
"""
Helper function for insert_readmore. Does modified binary search given a list of indexes where the spaces are.
Parameters:
-arr: list of indices where spaces are
-x: desired length (index) of string before cuts off to read me
Returns:
-the index corresponding to a space <350 chars, -1 if not possible e.g. when text is too short
"""
def binsearch(arr, x):
    low = 0
    high = len(arr) - 1
    mid = 0
    if len(arr)==0:
        return -1
    elif arr[-1]<x:
        return -1
    else:
        while low <= high:
            mid = (high + low) // 2
            
            if arr[mid] < x:
                low = mid + 1
            
            elif arr[mid]> x:
                high = mid -1
                
            else:
                return mid
        return high

"""
Given the tfidf representations of the data and the query, compute the ranking of 
cosine similarity scores.

Parameters:
-tfidfmat (dxf): tfidf representation of the data
-tfidfq (1xf): tfidf representation of the query
-idx: index to manga name dictionary
-num_manga: int, the value of f 

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
Given an input manga list to be similar to, computes the common genres in this
list (50% occurance or greater).
Then compute the jaccard score for each manga in the data, and rank them.
Parameters:
-manga_list: List(String) (the list of manga to be compared)
-input_manga_to_genre_dict: Dictionary from manga names to genre
-input_manga_to_index_dict: Dictionary from manga names to index
-idx: index to manga name dictionary
-num_manga: int, the value of f 

Returns:
-list of ranked manga by name
-a np array (1xd) with the ranking of each manga 
e.g. index 0 in the array is the highest ranked
-a np array (1xd) with the jaccard sim score of each manga
e.g. index 0 of the array gives the jaccard sim score to manga 0
"""
def grouped_jac_rank(input_manga_list, input_manga_to_genre_dict, input_manga_to_index_dict, idx, num_manga):
    if len(input_manga_list) == 0: #no input manga
        return [], np.arange(num_manga), np.zeros(num_manga), []

    input_manga_list = list(set(input_manga_list)) #avoid dealing with duplicates
    #if genre in half or more of the manga in the input manga list, use the genre in the sim measure
    genre_count = defaultdict(int)
    unmatched_manga = []
    for m in input_manga_list:
        if m.lower() in manga_synonym_dict:
            m = manga_synonym_dict[m.lower()]
            for genre in input_manga_to_genre_dict[m]:
                genre_count[genre] += 1
        else:
            unmatched_manga.append(m)
    thresh = len(input_manga_list)/2 #change threshhold here (50%)

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
    return results, jac_scores.argsort()[::-1], jac_scores, unmatched_manga