import requests
import config
from routes.auth import auth
from flask import Flask, render_template, redirect, url_for, session, request, json
from flask_oauthlib.client import OAuth


app = Flask(__name__)
app.register_blueprint(auth)
oauth = OAuth(app)
app.secret_key = 'development'
github = oauth.remote_app(
    'github',
    consumer_key=config.consumer_key,
    consumer_secret=config.consumer_secret,
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)


@app.route('/')
def index():
    home_str = "Welcome to Git Manager"
    return render_template('index.html', msg=home_str)


@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True))


@app.route('/logout')
def logout():
    session.pop('github_token', None)
    return redirect(url_for('index'))


@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason=%s error=%s resp=%s' % (
            request.args['error'],
            request.args['error_description'],
            resp
        )
    session['github_token'] = (resp['access_token'], '')
    me = github.get('user')
    print(me.data)
    return redirect(url_for('manage'))


@app.route('/manage')
def manage():
    # check if user is authenticated
    if 'github_token' in session:
        user = github.get('user')

        url = user.data["repos_url"]

        try:
            response = json.loads(requests.get(url).text)
        except requests.ConnectionError:
            return "Connection Error"

        return render_template('manage.html', user=user, repos=response)

    return redirect(url_for('login'))


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run(debug=True)
