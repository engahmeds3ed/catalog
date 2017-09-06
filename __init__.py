from flask import Flask, render_template, request, redirect,jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random, string

import datetime

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import urllib
from login_decorator import login_required

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

#Connect to Database and create database session
engine = create_engine('postgresql:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template("login.html",state=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# Obtain authorization code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
		   % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_access_token = login_session.get('access_token')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_access_token is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'),
								 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()

	login_session['name'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)

	login_session['user_id'] = user_id
	output = ''
	output += '<h1>Welcome, '
	output += login_session['name']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['name'])
	print "done!"
	return output

@app.route('/gdisconnect')
def gdisconnect():
	access_token = login_session.get('access_token')
	if access_token is None:
		print 'Access Token is None'
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	print 'In gdisconnect access token is %s', access_token
	print 'User name is: '
	print login_session['name']
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']

	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'result is '
	print result
	if result['status'] == '200':
		del login_session['user_id']
		del login_session['access_token']
		del login_session['gplus_id']
		del login_session['name']
		del login_session['email']
		del login_session['picture']
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response

def createUser(login_session):
	newuser = User(name=login_session['name'],
		email=login_session['email'],
		picture=login_session['picture'])
	session.add(newuser)
	session.commit()
	user = session.query(User).filter_by(email=login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	user = session.query(User).filter_by(id=user_id).one()
	return user

def getUserID(email):
	try:
		user = session.query(User).filter_by(email=email).one()
		return user.id
	except:
		return None

#JSON

#good
@app.route('/JSON/category')
def categoriesJSON():
	categories = session.query(Category).all()
	return jsonify(categories=[c.serialize for c in categories])

#good
@app.route('/JSON/catalog/<path:category_name>')
def categoryItemsJSON(category_name):
	category = session.query(Category).filter_by(name=category_name).one()
	allitems = session.query(Item).filter_by(category_id=category.id).all()
	return jsonify(items=[i.serialize for i in allitems])

#good
@app.route('/JSON/catalog/<path:category_name>/<path:item_name>')
def ItemJSON(category_name, item_name):
	category = session.query(Category).filter_by(name=category_name).one()
	item = session.query(Item).filter_by(name=item_name,\
										category=category).one()
	return jsonify(item=[item.serialize])


#Show all categories
@app.route('/')
@app.route('/catalog/')
def showCategories():
	categories = session.query(Category).order_by(asc(Category.name)).all()
	latestItems = session.query(Item).order_by(asc(Item.created)).limit(10).all()
	return render_template('category-list.html', categories = categories, latestItems=latestItems)

#Create a new category
@app.route('/catalog/new/', methods=['GET','POST'])
@login_required
def newCategory():
	if request.method == 'POST':
		newCategory = Category(name = request.form['name'],
								user_id = login_session['user_id'])
		session.add(newCategory)
		flash('New Category %s Successfully Created' % newCategory.name)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('category-add.html')

#Edit a category
@app.route('/catalog/<path:cat_name>/edit/', methods = ['GET', 'POST'])
@login_required
def editCategory(cat_name):
	editedCategory = session.query(Category).filter_by(name = cat_name).one()
	if editedCategory.user_id != login_session['user_id']:
		flash ("You cannot edit this Category. This Category belongs to another user!")
		return redirect(url_for('showCategories'))

	if request.method == 'POST':
		if request.form['name']:
			editedCategory.name = request.form['name']
			flash('Category Successfully Edited %s' % editedCategory.name)
			return redirect(url_for('showCategories'))
	else:
		return render_template('category-edit.html', category = editedCategory)

#Delete a category
@app.route('/catalog/<path:cat_name>/delete/', methods = ['GET','POST'])
@login_required
def deleteCategory(cat_name):
	categoryToDelete = session.query(Category).filter_by(name = cat_name).one()
	if categoryToDelete.user_id != login_session['user_id']:
		flash ("You cannot delete this Category. This Category belongs to another user")
		return redirect(url_for('showCategories'))

	if request.method == 'POST':
		session.delete(categoryToDelete)
		flash('%s Successfully Deleted' % categoryToDelete.name)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('category-delete.html',category = categoryToDelete)

#view category items
@app.route('/catalog/<path:cat_name>/')
def viewCategory(cat_name):
	category = session.query(Category).filter_by(name = cat_name).one()
	items = session.query(Item).filter_by(category_id = category.id).all()
	
	isAdmin = False
	if 'user_id' in login_session and login_session['user_id'] == category.user_id:
		isAdmin = True
		
	return render_template('category-view.html', items=items, category=category, isAdmin=isAdmin)

#view item
@app.route('/catalog/<path:cat_name>/<path:item_name>', methods=['GET','POST'])
def viewItem(cat_name,item_name):
	category = session.query(Category).filter_by(name = cat_name).one()
	item = session.query(Item).filter_by(name = item_name).one()
	
	isAdmin = False
	if 'user_id' in login_session and login_session['user_id'] == item.user_id:
		isAdmin = True

	return render_template('item-view.html', category = category, item = item, isAdmin=isAdmin)

#Create a new item
@app.route('/catalog/<path:cat_name>/new/',methods=['GET','POST'])
@login_required
def newItem(cat_name):
	category = session.query(Category).filter_by(name = cat_name).one()
	if request.method == 'POST':
		newItem = Item(name = request.form['name'], 
						description = request.form['description'], 
						picture = request.form['picture'], 
						created = datetime.datetime.now(),
						user_id = login_session['user_id'], 
						category = category)
		session.add(newItem)
		session.commit()
		flash('New Category %s Item Successfully Created' % (newItem.name))
		return redirect(url_for('viewCategory', cat_name = category.name))
	else:
		categories = session.query(Category).all()
		return render_template('item-add.html', categories=categories, cat_id = category.id)

#Edit category item
@app.route('/catalog/<path:cat_name>/<path:item_name>/edit', methods=['GET','POST'])
@login_required
def editItem(cat_name, item_name):
	editedItem = session.query(Item).filter_by(name = item_name).one()
	category = session.query(Category).filter_by(name = cat_name).one()
	
	if editedItem.user_id != login_session['user_id']:
		flash ("You cannot edit this Item. This Item belongs to another user")
		return redirect(url_for('viewCategory',cat_name=category.name))

	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']
		if request.form['picture']:
			editedItem.picture = request.form['picture']
		selectedCategory = session.query(Category).filter_by(id = request.form['cat_id']).one()
		if request.form['cat_id'] and selectedCategory:
			editedItem.category = selectedCategory
			cat_name = selectedCategory.name

		if not editedItem.user_id:
			editedItem.user_id = login_session['user_id']

		session.add(editedItem)
		session.commit() 
		flash('Category Item Successfully Edited')
		return redirect(url_for('viewCategory', cat_name = cat_name))
	else:
		categories = session.query(Category).all()
		return render_template('item-edit.html', item = editedItem, categories=categories)

#Delete category item
@app.route('/catalog/<path:cat_name>/<path:item_name>/delete', methods = ['GET','POST'])
@login_required
def deleteItem(cat_name,item_name):
	category = session.query(Category).filter_by(name = cat_name).one()
	itemToDelete = session.query(Item).filter_by(name = item_name).one()

	if itemToDelete.user_id != login_session['user_id']:
		flash ("You cannot delete this Item. This Item belongs to another user")
		return redirect(url_for('viewCategory',cat_name=cat_name))

	if request.method == 'POST':
		session.delete(itemToDelete)
		session.commit()
		flash('Category Item Successfully Deleted')
		return redirect(url_for('viewCategory', cat_name = cat_name))
	else:
		return render_template('item-delete.html', item = itemToDelete)

@app.context_processor
def inject_user():
	if 'user_id' in login_session and 'name' in login_session:
		loggedinUser = getUserInfo(login_session['user_id'])
		return dict(user=loggedinUser)
	else:
		return dict(user=None)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
