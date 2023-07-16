import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request, jsonify
import requests


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")


oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/posts')
def get_posts():
    headers = {
        'X-RapidAPI-Key': env.get('RAPIDAPI_KEY'),
        'X-RapidAPI-Host': env.get('RAPIDAPI_HOST')
    }

    try:
        response = requests.get(env.get('RAPIDAPI_ENDPOINT'), headers=headers)
        data = response.json()

        # Extract the relevant post information from the response data
        posts = []
        for item in data:
            title = item.get('title')
            content = item.get('content')
            post = {'title': title, 'content': content}
            posts.append(post)

        return jsonify(posts)

    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
