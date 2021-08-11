from flask import Flask, session, redirect, request, render_template
from requests_oauthlib import OAuth2Session
from common.config import Config
import requests

HOST = Config["host"]
PORT = Config["port"]
DEBUG = bool(Config["debug"])
CLIENT_ID = Config["ClientID"]
CLIENT_SECRET = Config["ClientSecret"]
REDIRECT_URI = Config["RedirectURL"]
API_BASE_URL = "https://discordapp.com/api"
AUTHORIZATION_BASE_URL = f"{API_BASE_URL}/oauth2/authorize"
TOKEN_URL = f"{API_BASE_URL}/oauth2/token"

app = Flask('DiscordOauth2Invite')
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = CLIENT_SECRET

def token_updater(token):
    session['oauth2_token'] = token

def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)

@app.route("/")
def index():
    scope = request.args.get(
        'scope',
        'identify guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    url = request.url.replace("http://", "https://")
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        authorization_response=url)
    session['oauth2_token'] = token
    userID = discord.get(f"{API_BASE_URL}/users/@me").json()["id"]
    res = requests.put(f"{API_BASE_URL}/guilds/{Config['ServerID']}/members/{userID}",
        headers = {
            "Authorization": f"Bot {Config['BotToken']}",
            "Content-Type": "application/json"
        },
        json = {
            'access_token': f"{session['oauth2_token']['access_token']}"
        })
    if res.status_code == 201 or res.status_code == 204:
        return render_template("redirect.html", server_id=Config["ServerID"])

if __name__ == '__main__':
    app.run(port=PORT, host=HOST, debug=DEBUG)