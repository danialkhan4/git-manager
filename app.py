import requests
import config
from routes.auth import auth
from flask import Flask, render_template, redirect, url_for, session, request, json
from flask_oauthlib.client import OAuth
from flask_sqlalchemy import SQLAlchemy


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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


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
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    # check if user is authenticated
    if 'github_token' in session:
        user = github.get('user')

        url = user.data["repos_url"]

        try:
            response = json.loads(requests.get(url).text)
        except requests.ConnectionError:
            return "Connection Error"

        return render_template('dashboard.html', user=user, repos=response)

    return redirect(url_for('login'))


@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run(debug=True)
