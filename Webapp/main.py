import json
import requests

from flask import Flask, Response, abort, render_template, request, session, jsonify

import controller
import settings

app = Flask(__name__)
#use os.urandom(32) to get a key for production.
app.secret_key = "secret_key"

@app.route('/')
def index():
    #This is a blank blue page for use prior to launch.
    #page = app.send_static_file('html/blank.html')
    #Use this one for production.
    page = render_template('index.html')
    return page

@app.route('/about')
def about():
    page = render_template('about.html')
    return page

@app.route('/sample')
def sample_email():
    page = render_template('sample_email.html')
    return page

@app.route('/_user', methods=['GET', 'POST'])
def get_user():
    """
    Retrieve a logged in user's data from the database (GET).
    -or-
    Updates a logged in user's data in the database (POST).

    Uses the session object's email address to query the data.

    Returns the info (as JSON) if the user is logged in, otherwise {} (GET).
    -or-
    Returns a JSON success message if the user's info is updated (POST).
    """
    userdata = {}
    authemail = session.get('email', None)
    if authemail is not None:
        if request.method == 'GET':
            userdata = controller.get_user_data(authemail)
        elif request.method == 'POST':
            jsondata = request.get_json(force=True)
            frequency = jsondata['freq']
            autoadd = jsondata['auto']
            citywide = jsondata['citywide']
            try:
                userdata['success'] = controller.update_user(authemail, frequency, autoadd, citywide)
            except controller.DataError as e:
                userdata['error'] = e.message
    return jsonify(userdata)

@app.route('/_save', methods=['POST'])
def save_area():
    """
    Save an area to the notices table in the db.

    Uses the session object's email address and the request object for data.

    Returns a JSON message indicating success or failure.
    """
    saved = {'succcess': False}
    authemail = session.get('email', None)
    if authemail is not None:
        userid, frequency, autoadd, citywide = controller.get_userinfo(authemail)
        jsondata = request.get_json(force=True)
        namehash = jsondata['namehash']
        name = jsondata['name']
        notices = json.dumps(jsondata['notices'])
        geom = json.dumps(jsondata['geom'])
        try:
            saved['succcess'] = controller.save_data(userid, namehash, name, notices, geom)
        except controller.DataError as e:
            saved['error'] = e.message
    return jsonify(saved)

@app.route('/_update', methods=['POST'])
def update_area():
    """
    Updates an area that is already in the notices table.

    Uses the session object's email address and the request object for data.
    Returns a JSON message indicating success or failure.
    """
    updated = {'succcess': False}
    authemail = session.get('email', None)
    if authemail is not None:
        userid, frequency, autoadd, citywide = controller.get_userinfo(authemail)
        jsondata = request.get_json(force=True)
        namehash = jsondata['namehash']
        name = jsondata['name']
        notices = json.dumps(jsondata['notices'])
        geom = json.dumps(jsondata['geom'])
        oldhash = jsondata['oldhash']
        try:
            updated['succcess'] = controller.update_data(oldhash, userid, namehash, name, notices, geom)
        except controller.DataError as e:
            updated['error'] = e.message
    return jsonify(updated)

@app.route('/_delete', methods=['POST'])
def del_area():
    """
    Deletes an area from the notices table.

    Uses the session object's email address and the request object for data.
    Returns a JSON message indicating success or failure.
    """
    deleted = {'succcess': False}
    authemail = session.get('email', None)
    if authemail is not None:
        userid, frequency, autoadd, citywide = controller.get_userinfo(authemail)
        jsondata = request.get_json(force=True)
        namehash = jsondata.get('namehash', None)
        if namehash is not None:
            try:
                deleted['succcess'] = controller.delete_data(userid, namehash)
            except controller.DataError as e:
                deleted['error'] = e.message
    return jsonify(deleted)

@app.route('/login', methods=['POST'])
def login():
    data = {'assertion': request.form['assertion'],
            'audience': settings.hostname}
    resp = requests.post('https://verifier.login.persona.org/verify', data=data)
    info = resp.json()
    if info['status'] != 'okay':
        abort(403)
    session['email'] = info['email']
    return Response(status=204)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return Response(status=204)

@app.route('/a_secret_to_everyone')
def chart_page():
    return render_template('chart.html')

if __name__ == '__main__':
    app.run(debug=settings.debug)