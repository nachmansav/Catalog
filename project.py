#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, jsonify
from flask import session as login_session
import random
import string
import httplib2
import json
import requests
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Recipe, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import make_response, url_for, flash

app = Flask(__name__)

logged_in = False

CLIENT_ID = json.loads(
  open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine(
    'sqlite:///recipes.db',
    connect_args={'check_same_thread': False}
    )
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase
                    + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # upgrade the authorization code into the credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade'
                                            ' the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?'
           'access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID soesn't match given user ID."), 401)
        response.header['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check to see if the user is already logged in.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current User is'
                                            ' already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't, create a new user
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    ' 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(username=login_session['username'], email=login_session
                   ['email'], picture=login_session['picture'])
    session.add(newUser)
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
    except NoUserEmailFound:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('credentials')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current'
                                 'user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %\
          login_session['credentials']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash('Successfully logged out.')
        return redirect(url_for('showCategories', logged_in=logged_in))
    else:
        response = make_response(json.dumps(
          'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


def loggedIn():
    if 'username' not in login_session:
        return False
    else:
        return True

# JSON API to view all categories.
@app.route('/JSON')
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

# JSON API to view all recipes in a category.
@app.route('/categories/<int:cat_id>/JSON')
def recipeCatJSON(cat_id):
    items = session.query(Recipe).filter_by(cat_id=cat_id).all()
    return jsonify(items=[i.serialize for i in items])

# JSON API to view a specific recipe.
@app.route('/categories/<int:cat_id>/<int:rec_id>/JSON')
def recipeJSON(cat_id, rec_id):
    recipe = session.query(Recipe).filter_by(id=rec_id).one()
    return jsonify(recipe=recipe.serialize)


# Show all categories
@app.route('/')
@app.route('/categories/')
def showCategories():
    logged_in = loggedIn()
    categories = session.query(Category).all()
    return render_template(
      'categories.html', categories=categories, logged_in=logged_in)


# Show all recipes in a category
@app.route('/categories/<int:cat_id>/')
def showRecipes(cat_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    items = session.query(Recipe).filter_by(cat_id=cat_id).all()
    logged_in = loggedIn()
    if 'username' not in login_session:
        return render_template(
          'publicrecipes.html', category=category, items=items,
          logged_in=logged_in)
    else:
        return render_template(
          'recipes.html', category=category, items=items,
          logged_in=logged_in)


# Show specific recipe
@app.route('/categories/<int:cat_id>/<int:rec_id>/')
def showRecipe(cat_id, rec_id):
    recipe = session.query(Recipe).filter_by(id=rec_id).one()
    creator = getUserInfo(recipe.creator_id)
    logged_in = loggedIn()
    if 'username' not in login_session or\
            creator.id != login_session['user_id']:
        return render_template(
          'publicrecipe.html', recipe=recipe, cat_id=cat_id,
          creator=creator, logged_in=logged_in)
    else:
        return render_template(
          'recipe.html', recipe=recipe, cat_id=cat_id,
          creator=creator, logged_in=logged_in)

# Create a new recipe
@app.route('/categories/<int:cat_id>/new/', methods=['GET', 'POST'])
def newRecipe(cat_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=cat_id).one()
    creator_id = login_session['user_id']
    logged_in = loggedIn()
    if request.method == 'POST':
        newRecipe = Recipe(
          name=request.form['name'], ingredients=request.form[
           'ingredients'], directions=request.form['directions'],
          picture=request.form['picture'], cat_id=cat_id,
          creator_id=creator_id)
        session.add(newRecipe)
        session.commit()
        flash('New Recipe %s Successfully Created' % (newRecipe.name))
        return redirect(url_for(
          'showRecipes', cat_id=cat_id, logged_in=logged_in))
    else:
        return render_template(
          'newrecipe.html', cat_id=cat_id, logged_in=logged_in)


# Edit a recipe
@app.route('/categories/<int:cat_id>/<int:rec_id>/edit',
           methods=['GET', 'POST'])
def editRecipe(cat_id, rec_id):
    editedItem = session.query(Recipe).filter_by(id=rec_id).one()
    category = session.query(Category).filter_by(id=cat_id).one()
    logged_in = loggedIn()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.creator.username != login_session['username']:
        return "<script>function myFunction() {alert('you are not"
        " authorized to edit this recipe. please create your own "
        "recipe.');}</script><bodyonload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['ingredients']:
            editedItem.ingredients = request.form['ingredients']
        if request.form['directions']:
            editedItem.directions = request.form['directions']
        if request.form['picture']:
            editedItem.picture = request.form['picture']
        if request.form['category']:
            editedItem.cat_id = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Recipe Successfully Edited')
        return redirect(url_for(
          'showRecipes', cat_id=cat_id, logged_in=logged_in))
    else:
        return render_template(
          'editrecipe.html', rec_id=rec_id, cat_id=cat_id,
          item=editedItem, logged_in=logged_in)


# Delete a recipe
@app.route('/categories/<int:cat_id>/<int:rec_id>/delete',
           methods=['GET', 'POST'])
def deleteRecipe(cat_id, rec_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    itemToDelete = session.query(Recipe).filter_by(id=rec_id).one()
    logged_in = loggedIn()
    if 'username' not in login_session:
        return redirect('/login')
    if itemToDelete.creator.username != login_session['username']:
        return "<script>function myFunction() {alert('you are not"
        " authorized to delete this recipe. please create your own"
        " recipe.');}</script><bodyonload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Recipe Successfully Deleted')
        return redirect(url_for(
          'showRecipes', cat_id=cat_id, logged_in=logged_in))
    else:
        return render_template(
          'deleterecipe.html', item=itemToDelete,
          cat_id=cat_id, logged_in=logged_in)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
