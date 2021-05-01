from . import *  
from app.irsystem.models.helpers import *
from app.accounts.controllers.sessions_controller import *
from app.accounts.controllers.users_controller import *
from app.accounts.models.session import *
from app.accounts.models.user import *
from methods import *

import secrets
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import numpy as np 
import requests
import pickle

project_name = 'Manga Recs'
net_id = 'Shungo Najima: sn685, Gary Ho: gh395, Michael Chen: mc2253, Winston Chen: wc523, Brian Zhu: bkz3'

def extract_token(request):
	auth_header = request.headers.get('Authorization')
	if auth_header is None:
		return False, json.dumps({"error": "Missing Authorization token"})

	bearer_token = auth_header.replace("Bearer ", "").strip()
	if bearer_token is None or not bearer_token:
		return False, json.dumps({"error": "Invalid Authorization header"})

	return True, bearer_token

# @irsystem.route('/', methods=['GET'])
# def home():
# 	query = request.args.get('search')
# 	if not query:
# 		print('bruh')
# 		data = []
# 		output_message = ''
# 	else:
# 		print('boi')
# 		output_message = 'Your search: ' + query
# 		data = range(5)
# 	return render_template('search.html', name=project_name, \
# 		netid=net_id, output_message=output_message, data=data)

@irsystem.route('/', methods=['GET'])
def home():
	query = request.args.get('query')
	mlst = request.args.get('input_list')
	sim_data = []
	dis_data = []
	sim_synopses = []
	sim_images = []
	sim_scores = []

	if not query:
		output_query = ''
		output_list = ''
	else:
		output_query = query
		output_list = mlst
		x = requests.post('https://manga-recs-2.herokuapp.com/api/', \
			json = {'query': [y.strip() for y in query.split(',')], \
				'input_list': [y.strip() for y in mlst.split(',')]})

		sim_data = x.json()['similar']
		dis_data = x.json()['dissimilar']
		sim_synopses = x.json()['similar_synopses']
		sim_images = x.json()['similar_images']
		sim_scores = x.json()['similar_scores']
	return render_template('search.html', name=project_name, \
		netid=net_id, output_query=output_query, output_list=output_list, \
		sim_data=sim_data, dis_data=dis_data, sim_synopses=sim_synopses, \
		sim_images=sim_images, sim_scores=sim_scores, len=len(sim_data))

def myconverter(o):
	if isinstance(o, datetime.datetime):
		return o.__str__()

@irsystem.route('/register/', methods=['POST'])
def register_account():
	body = json.loads(request.data)
	email = body.get('email')
	fname = body.get('fname')
	lname = body.get('lname')
	password = body.get('password')

	if email is None or fname is None or lname is None or password is None:
		return json.dumps({'error': 'Invalid email, name(s) or password'})
	
	was_created, user = create_user(email, fname, lname, password)

	if not was_created: 
		return json.dumps({'error': 'User already exists'})

	sess = get_session_by_user_id(user.id)

	return json.dumps(
		{
			'session_token': sess.session_token,
			'update_token': sess.update_token,
			'expires_at': sess.expires_at
		},
		default = myconverter
	)

@irsystem.route('/login/', methods=['POST'])
def login():
	body = json.loads(request.data)
	email = body.get('email')
	password = body.get('password')

	if email is None or password is None:
		return json.dumps({'error': 'Invalid email or password'})

	was_successful, user = verify_credentials(email, password)

	if not was_successful:
		return json.dumps({'error': 'Incorrect email or password'})

	sess = get_session_by_user_id(user.id)

	return json.dumps(
		{
			'session_token': sess.session_token,
			'update_token': sess.update_token,
			'expires_at': sess.expires_at
		},
		default = myconverter
	)

@irsystem.route('/api/', methods=['POST'])
def api():
	body = json.loads(request.data)
	query = body.get('query')
	input_list = body.get('input_list')

	tfidf_vec = TfidfVectorizer(stop_words='english')
	#tfidf matrix for synopses
	tfidfmatrix = tfidf_vec.fit_transform([d['synopsis'] for d in manga_list.values()]).toarray() 
	tfidfquery = tfidf_vec.transform(query).toarray() 
	#tfidf_vec.vocabulary_ to get the mappings of words to index 

	num_manga, num_features = tfidfmatrix.shape

	manga_name_to_index = {v:k for k,v in index_to_manga_name.items()}

	#keys = manga names, values= genre list
	manga_to_genre_dict= dict()
	for manga_item in manga_list.values():
		manga_to_genre_dict[manga_item['title']] = set()
		if 'genres' in manga_item:
			for genre in manga_item['genres']:
				manga_to_genre_dict[manga_item['title']].add(genre['name'])

	cos_sim_rank_name, cos_sim_rank_idx, cos_sim_scores = \
		cos_sim_rank(tfidfmatrix, tfidfquery, index_to_manga_name, num_manga)

	jac_sim_rank_name, jac_sim_rank_idx, jac_sim_scores = \
		grouped_jac_rank(input_list, manga_to_genre_dict, manga_name_to_index, \
		index_to_manga_name, num_manga)

	combined_scores = cos_sim_scores + 0.25 * jac_sim_scores
	overall_rank_idx = combined_scores.argsort()[::-1]
	overall_rank_names = []
	overall_rank_synopses = []
	overall_rank_images = []
	overall_rank_scores = []
	for manga_idx in overall_rank_idx:
		if index_to_manga_name[manga_idx] not in input_list:
			overall_rank_names.append(index_to_manga_name[manga_idx])
			overall_rank_synopses.append(index_to_manga[manga_idx][0])
			overall_rank_images.append(index_to_manga[manga_idx][1])
			overall_rank_scores.append(combined_scores[manga_idx])
	
	return json.dumps(
		{
			'similar': overall_rank_names[:10],
			'dissimilar': overall_rank_names[-10:],
			'similar_synopses': overall_rank_synopses[:10],
			'dissimilar_synopses': overall_rank_synopses[-10:],
			'similar_images': overall_rank_images[:10],
			'dissimilar_images': overall_rank_images[-10:],
			'similar_scores': overall_rank_scores[:10],
			'dissimilar_scores': overall_rank_scores[-10:]
		}
	)

# @irsystem.route('/connect/', methods=['GET'])
# def connect():
# 	code_verifier = secrets.token_urlsafe(100)[:128]
# 	user_auth_url = 'https://myanimelist.net/v1/oauth2/authorize' + '?response_type=code' \
# 		+ '&client_id=' + str(os.environ["CLIENT_ID"]) + '&code_challenge=' \
# 		+ str(code_verifier) + '&state=RequestID42'
# 	print('Go to the following URL:', user_auth_url)

# @irsystem.route('/oauth/', methods=['GET'])
# def oauth():
# 	code = request.args.get('code')
#   password = request.args.get('password')

@irsystem.route('/session/', methods=['POST'])
def session():
	was_successful, update_token = extract_token(request)

	if not was_successful:
		return update_token

	try:
		user = sessions_controller.renew_session(update_token)
	except Exception as e:
		return json.dumps({'error': f"Invalid update token: {str(e)}"})

	sess = get_session_by_user_id(user.id)

	return json.dumps(
		{
			'session_token': sess.session_token,
			'update_token': sess.update_token,
			'expires_at': sess.expires_at
		},
		default = myconverter
	)

# @irsystem.route('/search/', methods=['GET'])
# def search():

