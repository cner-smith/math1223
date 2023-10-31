from requests_oauthlib import OAuth2Session

# Fill in these values from your client creation on Warcraft Logs
client_id = '9a80e66c-f50e-4bd1-9128-5760c7384f9d'
client_secret = 'n8RTGEGFrbxGl4SxoNR4NjWBeje96QYap8TH12Jb'
authorize_uri = 'https://www.warcraftlogs.com/oauth/authorize'
token_uri = 'https://www.warcraftlogs.com/oauth/token'

# Set up an OAuth session
oauth = OAuth2Session(client_id, redirect_uri='https://1c2f-69-110-55-82.ngrok.io')

# Get the authorization URL
authorization_url, state = oauth.authorization_url(authorize_uri)

# Direct the user to this URL for authorization
print(f"Please go to {authorization_url} and authorize the application.")
redirect_response = input("Paste the full redirect URL here: ")

# Fetch the token using the redirect URL
token = oauth.fetch_token(
    token_uri,
    authorization_response=redirect_response,
    client_secret=client_secret
)

access_token = token['access_token']
print(f"Access Token: {access_token}")
