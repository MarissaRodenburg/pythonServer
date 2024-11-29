# First do:
#   python3 -m venv server_venv    
#   source server_venv/bin/activate
#   pip3 install flask
#   pip3 install requests requests-oauthlib

# Ravelry API key registration: https://www.ravelry.com/businesses/new?plan_type=6
# then here: https://www.ravelry.com/pro/developer
#
# Details on how to set this up: https://medium.com/data-science-at-microsoft/how-to-access-an-api-for-first-time-api-users-879002f5f58d


from flask import Flask, render_template, render_template_string, url_for 
from flask import Flask, request, redirect, session, jsonify
from requests_oauthlib import OAuth1Session
import os
import json

app = Flask(__name__) 
app.config['DEBUG'] = True

@app.route('/') 
def home(): 
    return render_template('index.html') 

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/box')
def box():
    return render_template('box.html')

@app.route('/js_sample')
def js_sample():
    return render_template('js_sample.html')

@app.route('/circle')
def circle():
    return render_template('bouncyball.html')

@app.errorhandler(404)
def not_found(e):
  return render_template('404_page.html'), 404

app.secret_key = os.urandom(24)  # Random secret key for Flask sessions

# Replace with your Ravelry API key and secret
API_KEY = "7ef1c45b4251a83c6f582809844c31d6"
API_SECRET = "XwbG9uy9SILbjRurOd_3MxZP/glvylNlnxrjRk9q"

# Ravelry API URLs
REQUEST_TOKEN_URL = "https://www.ravelry.com/oauth/request_token"
AUTHORIZE_URL = "https://www.ravelry.com/oauth/authorize"
ACCESS_TOKEN_URL = "https://www.ravelry.com/oauth/access_token"
BASE_API_URL = "https://api.ravelry.com"
CALLBACK_URI = "http://localhost:8000/callback"

# Route to initiate OAuth authentication
@app.route("/login")
def login():
    oauth = OAuth1Session(
        API_KEY, 
        client_secret=API_SECRET,
        callback_uri=CALLBACK_URI,
    )
    try:
        fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    except ValueError as e:
        return f"Error fetching request token: {e}"
    
    session['oauth_token'] = fetch_response.get('oauth_token')
    session['oauth_token_secret'] = fetch_response.get('oauth_token_secret')
    
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)
    return redirect(authorization_url)

# Callback route after user authorizes the app
@app.route("/callback")
def callback():
    global ravelry
    #user_name = request.args.get('username')
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    #print(f"username: {user_name}, oauth_token: {oauth_token}, oauth_verifier: {oauth_verifier}")
    
    if not oauth_verifier or not oauth_token:
        return "Error: Missing token or verifier", 400

    request_token_secret = session.get('oauth_token_secret')
    if not request_token_secret:
        return "Error: Missing request token secret", 400

    # Initialize OAuth1 session with request token and verifier
    ravelry = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=request_token_secret,
        verifier=oauth_verifier
    )

    # Access token URL
    access_token_url = "https://www.ravelry.com/oauth/access_token"

    try:
        access_token_response = ravelry.fetch_access_token(access_token_url)
        
        # Store access token in session for use in /stash route

        print(access_token_response)
        session['access_token'] = access_token_response.get('oauth_token')
        session['access_token_secret'] = access_token_response.get('oauth_token_secret')
        session['username'] = request.args.get('username')
        # Redirect to /stash route
        return redirect(url_for('stash'))

    except Exception as e:
        return f"Error fetching access token: {e}", 400

# Route to fetch user's stash from the API
@app.route("/stash")
def stash():
    # Retrieve the access token from session
    access_token = session.get('access_token')
    access_token_secret = session.get('access_token_secret')
    username = session.get('username')
    #print(f"username: {username}, access_token: {access_token}, access_token_secret: {access_token_secret}")
    if not access_token or not access_token_secret:
        return "Error: Missing access token", 400

    # Initialize OAuth1 session with the access token
    ravelry = OAuth1Session(
        client_key=API_KEY,
        client_secret=API_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret
    )

    # Fetch user's stash
    stash_url = f"https://api.ravelry.com/people/{username}/stash/list.json"
    print(f"stash_url: {stash_url}")    
    try:
        response = ravelry.get(stash_url)
        print(f"Response Status Code: {response.status_code}")  
        if response.status_code == 200:
            try:
                # Parse JSON response
                #print(f"Response Status Code: {response.status_code}")
                #print(f"Response Content: {response.content}")
                #print(response.headers)
                stash_data = response.json()
                print(stash_data)
                # Create HTML table
                stash_items = stash_data['stash']
                # Create an HTML table
                html_table = """
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Colorway</th>
                        <th>Yarn</th>
                        <th>Yarn Company</th>
                        <th>Weight</th>
                        <th>Rating</th>
                    </tr>
                """

                # Loop through each item in the stash and populate the table
                for item in stash_items:
                    name = item['name']
                    colorway = item['colorway_name']
                    yarn_name = item['yarn']['name']
                    yarn_company = item['yarn']['yarn_company_name']
                    yarn_weight = item['yarn']['yarn_weight']['name']
                    rating = item['yarn']['rating_average']

                    html_table += f"""
                    <tr>
                        <td>{name}</td>
                        <td>{colorway}</td>
                        <td>{yarn_name}</td>
                        <td>{yarn_company}</td>
                        <td>{yarn_weight}</td>
                        <td>{rating}</td>
                    </tr>
                    """

                # Close the table
                html_table += "</table>"

                # Return HTML page with table
                return render_template_string("""
                    <html>
                        <head>
                            <title>Your Stash</title>
                            <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
                        </head>
                        <body>
                            <div class="container mt-4">
                                <h1>Your Stash</h1>
                                {{ table_html|safe }}
                            </div>
                        </body>
                    </html>
                """, table_html=html_table)
            except Exception as e:
                return f"Error: {e}", 400
        else:
            return f"Error: No stash items found: {response.status_code}", 400
    
    except Exception as e:
        return f"Error: {e}", 400


if __name__ == '__main__': 
    app.run(port=8000, debug=True)
