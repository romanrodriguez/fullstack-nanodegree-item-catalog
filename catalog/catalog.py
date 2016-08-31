from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import session as login_session
import random
import string
from functools import wraps
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('main'))
        return f(*args, **kwargs)
    return decorated_function


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Authenticate a user
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

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

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
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px; padding: 30px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
# Create a user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Gets user info based on user_id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Get user_id based on email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Disconnect a user and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API
@app.route('/catalog/json')
def catalog_json():
    catalog = session.query(Category)
    items = session.query(Item)

    outer_dictionary = {}
    inner_dictionary = {}

    outer_dictionary["category"] = [i.serialize for i in catalog]
    inner_dictionary["items"] = [i.serialize for i in items]
    outer_dictionary["items"] = inner_dictionary
    return jsonify(outer_dictionary)


# Main website - Catalog - show all categories
@app.route('/')
@app.route('/catalog/')
def main():
    categories = session.query(Category).all()
    all_items = session.query(Item).all()
    if 'username' not in login_session:
        return render_template('viewCatalog.html', categories=categories, items=all_items)
    else:
        return render_template('catalog.html', categories=categories, items=all_items)


# View items in a category
@app.route('/catalog/<int:category_id>/')
def view_category_items(category_id):
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(category_id=category_id).all()
    if 'username' not in login_session:
        return render_template('viewCategoryItems.html', categories=categories, items=items)
    else:
        return render_template('categoryItems.html', categories=categories, items=items)


# Add an item
@app.route('/add/', methods=['GET', 'POST'])
@login_required
def add_item():
    categories = session.query(Category).all()
    email = login_session['email']
    user_info = session.query(User).filter_by(email=email).one()
    if request.method == 'POST' and ('username' in login_session):
        newItem = Item(name=request.form['name'], description=request.form['description'], category_id=request.form['category_dropdown'], user_id=user_info.id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('main'))
    else:
        categories = session.query(Category).all()
        return render_template('addItem.html', categories=categories)


# View an item
@app.route('/catalog/<int:category_id>/<int:item_id>/')
def view_item(category_id, item_id):
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return render_template('viewItem.html', categories=categories, item=item)
    else:
        return render_template('item.html', categories=categories, item=item)


# Edit an item
@app.route('/edit/<category_id>/<item_id>/', methods=['GET', 'POST'])
@login_required
def edit_item(category_id, item_id):
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST' and ('username' in login_session) and (item.user_id == login_session['user_id']):
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category_dropdown']:
            item.category_id = request.form['category_dropdown']
        session.add(item)
        session.commit()
        return redirect(url_for('main'))
    elif (item.user_id != login_session['user_id']):
        return render_template('editItemNotAllowed.html',
                               categories=categories)
    elif ('username' in login_session) and (item.user_id == login_session['user_id']):
        return render_template('editItem.html', categories=categories, item=item)
    else:
        return redirect(url_for('main'))


# Delete an item
@app.route('/delete/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    categories = session.query(Category).all()
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST' and ('username' in login_session) and (item.user_id == login_session['user_id']):
        session.delete(item)
        session.commit()
        return redirect(url_for('main'))
    elif (item.user_id != login_session['user_id']):
        return render_template('deleteItemNotAllowed.html',
                               categories=categories)
    elif ('username' in login_session) and (item.user_id == login_session['user_id']):
        return render_template('deleteItem.html', categories=categories, item=item)
    else:
        return redirect(url_for('main'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
