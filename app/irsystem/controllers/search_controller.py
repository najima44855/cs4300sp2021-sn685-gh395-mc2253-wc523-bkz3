from . import *  
from app.irsystem.models.helpers import *
from app.accounts.controllers.sessions_controller import *
from app.accounts.controllers.users_controller import *
from app.accounts.controllers.favorites_controller import *
from app.accounts.models.session import *
from app.accounts.models.user import *
from methods import *
from flask_login import login_user, login_required, current_user, logout_user
import os

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

@irsystem.route('/', methods=['GET'])
def home():
	query = request.args.get('query')
	mlst = request.args.get('input_list')
	has_match = False
	sim_keywords = ''
	unmatched_manga = ''
	sim_data = []
	sim_ids = []
	sim_synopses = []
	sim_images = []
	sim_scores = []
	pmatch_keyword =[]
	pmatch_mlist = []
	fav_url = os.environ['BASE_URL'] + 'favorite/'
	unfav_url = os.environ['BASE_URL'] + 'unfavorite/'
	insertion_list=[]

	if not query and not mlst:
		output_query = ''
		output_list = ''
	else:
		output_query = query
		output_list = mlst
		query_value = query
		input_list_value = [y.strip() for y in mlst.split(',')]
		if not query:
			output_query = ''
			query_value = []
		if not mlst:
			input_list_value = []
			output_list = ''
		output_query = query
		output_list = mlst
		x = requests.post(os.environ['BASE_URL'] + 'api/', \
			json = {'query': query_value, \
				'input_list': input_list_value})

		has_match = x.json()['has_match']
		sim_keywords = (", ").join(x.json()['similar_keywords'])
		unmatched_manga = (", ").join(x.json()['unmatched_manga'])
		sim_data = x.json()['similar']
		temp_sim_ids = x.json()['similar_ids']
		sim_ids = [os.environ['BASE_URL'] + 'manga/' + str(x) + '/' for x in temp_sim_ids]
		sim_synopses = x.json()['similar_synopses']
		insertion_list = x.json()['insertion_list']
		sim_images = x.json()['similar_images']
		sim_scores = x.json()['similar_scores']
		pmatch_keyword = x.json()['pmatch_keyword']
		pmatch_mlist = x.json()['pmatch_mlist']
	return render_template('search.html', name=project_name, netid=net_id, has_match=has_match,\
		unmatched_manga=unmatched_manga, output_query=output_query, output_list=output_list, \
		sim_keywords = sim_keywords, sim_data=sim_data, sim_ids=sim_ids, insertion_list=insertion_list,\
		manga_list=manga_titles, sim_synopses=sim_synopses, sim_images=sim_images, \
		sim_scores=sim_scores, pmatch_keyword=pmatch_keyword, pmatch_mlist=pmatch_mlist, \
		len=len(sim_data), home_class="active", profile_class = "", login_class = "", \
		register_class = "", logout_class = "", fav_url=fav_url)

def myconverter(o):
	if isinstance(o, datetime.datetime):
		return o.__str__()

@irsystem.route('/register/', methods=['GET'])
def register():
	return render_template('signup.html', \
		home_class="", profile_class = "", login_class = "", \
		register_class = "active", logout_class = "")

@irsystem.route('/register/', methods=['POST'])
def register_account():
	username = request.form.get('username')
	fname = request.form.get('fname')
	lname = request.form.get('lname')
	password = request.form.get('password')

	if username == '' or fname == '' or lname == '' or password == '':
		flash('Please enter a username, first/last name, and password')
		return redirect(url_for('irsystem.register'))
	
	was_created, user = create_user(username, fname, lname, password)

	if not was_created: 
		flash('That username is already taken')
		return redirect(url_for('irsystem.register'))

	sess = get_session_by_user_id(user.id)
	return redirect(url_for('irsystem.login'))

@irsystem.route('/login/', methods=['GET'])
def login():
	return render_template('login.html', \
		home_class="", profile_class = "", login_class = "active", \
		register_class = "", logout_class = "")

@irsystem.route('/login/', methods=['POST'])
def login_post():
	username = request.form.get('username')
	password = request.form.get('password')
	remember = True if request.form.get('remember') else False

	if username == '' or password == '':
		flash('Please enter a username and password.')
		return redirect(url_for('irsystem.login'))

	was_successful, user = verify_credentials(username, password)

	if not was_successful:
		flash('Incorrect username and/or password.')
		return redirect(url_for('irsystem.login'))

	login_user(user, remember=remember)
	return redirect(url_for('irsystem.profile'))

@irsystem.route('/logout/', methods=['GET'])
def logout():
	logout_user()
	return redirect(url_for('irsystem.home'))
	
@irsystem.route('/profile/', methods=['GET'])
def profile():
	was_successful, favorites = get_favorites(current_user.username)
	unfav_url = os.environ['BASE_URL'] + 'unfavorite/'

	if not was_successful:
		return render_template('profile.html', name=current_user.fname, \
			home_class="", profile_class = "active", login_class = "", \
			register_class = "", logout_class = "", no_favorites = True, \
			unfav_url=unfav_url)

	sim_data = []
	sim_images = []
	sim_ids = []

	for f in favorites:
		sim_data.append(f.title)
		sim_images.append(f.img_url)
		sim_ids.append(f.manga_url)

	return render_template('profile.html', name=current_user.fname, \
		home_class="", profile_class = "active", login_class = "", \
		register_class = "", logout_class = "", no_favorites = False, \
		sim_data=sim_data, sim_images=sim_images, sim_ids=sim_ids, \
		len=len(sim_data))

@irsystem.route('/favorite/', methods=['POST'])
def favorite():
	body = json.loads(request.data)
	create_favorites(current_user.username, body.get('title'), \
		body.get('img_url'), body.get('manga_url'))

	return redirect(url_for('irsystem.profile'))

@irsystem.route('/unfavorite/', methods=['POST'])
def unfavorite():
	body = json.loads(request.data)
	remove_favorites(current_user.username, body.get('title'))

	return redirect(url_for('irsystem.profile'))

@irsystem.route('/manga/<int:manga_id>/', methods=['GET'])
def manga_details(manga_id):
	response_body = requests.get('https://api.jikan.moe/v3/manga/' + \
		str(manga_id) + '/reviews')

	manga_reviews = []
	manga_reviews_usernames = []
	manga_reviews_upvotes = []
	read_more_list = []

	for review in response_body.json()['reviews']:
		review_content, has_readmore = insert_readmore(review['content'].replace("\\n","\n"))
		manga_reviews.append(review_content)
		read_more_list.append(has_readmore)
		manga_reviews_usernames.append(review['reviewer']['username'])
		manga_reviews_upvotes.append(review['helpful_count'])
	dict_id = id_to_index[manga_id]

	sim_id = os.environ['BASE_URL'] + 'manga/' + str(manga_id) + '/'

	fav_url = os.environ['BASE_URL'] + 'favorite/'
	unfav_url = os.environ['BASE_URL'] + 'unfavorite/'

	return render_template('manga.html', \
		manga_title=index_to_manga_name[dict_id], \
		manga_synopsis=index_to_manga_synopsis[dict_id], \
		manga_image=index_to_manga_pic[dict_id], manga_reviews=manga_reviews, \
		read_more_list=read_more_list, \
		manga_reviews_usernames=manga_reviews_usernames, \
		manga_reviews_upvotes=manga_reviews_upvotes, \
		len=len(manga_reviews), \
		fav_url=fav_url, unfav_url=unfav_url, sim_id=sim_id)

@irsystem.route('/api/', methods=['POST'])
def api():
	body = json.loads(request.data)
	query = body.get('query')
	input_list = body.get('input_list')

	tfidf_vec = TfidfVectorizer(stop_words='english')
	#tfidf matrix for synopses
	tfidfmatrix = tfidf_vec.fit_transform([d['synopsis'] for d in manga_list.values()]).toarray() 
	num_manga, num_features = tfidfmatrix.shape
	if len(query)>0:
		new_query, orig_query, sim_query = add_to_query(query)
		tfidfquery = tfidf_vec.transform(new_query).toarray()
	else:
		orig_query = set()
		sim_query = []
		tfidfquery = np.zeros(num_features)

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

	jac_sim_rank_name, jac_sim_rank_idx, jac_sim_scores, unmatched_manga = \
		grouped_jac_rank(input_list, manga_to_genre_dict, manga_name_to_index, \
		index_to_manga_name, num_manga)

	input_list_lower = [i.lower() for i in input_list]
	combined_scores = cos_sim_scores + 0.25 * jac_sim_scores
	overall_rank_idx = combined_scores.argsort()[::-1]
	overall_rank_ids = []
	overall_rank_names = []
	overall_rank_synopses = []
	overall_rank_images = []
	overall_rank_scores = []
	percent_match_keyword = []
	percent_match_mlist = []
	read_more_list = []
	
	if np.all(np.isclose(combined_scores,combined_scores[0])):
		has_match = False
	else:
		has_match = True

	count = 0
	for manga_idx in overall_rank_idx:
		if count == 10:
			break
		if index_to_manga_name[manga_idx].lower() not in input_list_lower:
			synopsis = index_to_manga_synopsis[manga_idx]
			synopsis, has_readmore = insert_readmore(synopsis)
			synopsis = highlight(orig_query, sim_query, synopsis)
			overall_rank_ids.append(index_to_id[manga_idx])
			overall_rank_names.append(index_to_manga_name[manga_idx])
			overall_rank_synopses.append(synopsis)
			read_more_list.append(has_readmore)
			overall_rank_images.append(index_to_manga_pic[manga_idx])
			overall_rank_scores.append(combined_scores[manga_idx])
			if has_match:
				percent_match_keyword.append(cos_sim_scores[manga_idx]/combined_scores[manga_idx]*100)
				percent_match_mlist.append(jac_sim_scores[manga_idx]*0.25/combined_scores[manga_idx]*100)
			else:
				percent_match_keyword.append(0) #just to avoid errors in terminal
				percent_match_mlist.append(0)
			count += 1

	return json.dumps(
		{
			'has_match': has_match,
			'unmatched_manga': unmatched_manga,
			'similar_ids': overall_rank_ids[:10],
			'similar_keywords': sim_query,
			'similar': overall_rank_names[:10],
			'similar_synopses': overall_rank_synopses[:10],
			'insertion_list': read_more_list,
			'similar_images': overall_rank_images[:10],
			'similar_scores': overall_rank_scores[:10],
			'pmatch_keyword': percent_match_keyword[:10],
			'pmatch_mlist': percent_match_mlist[:10]
		}
	)

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