import os 
import pickle 
import google_auth_oauthlib.flow
import googleapiclient.discovery

api_version = "v3"
api_service_name = "youtube"
client_secrets_file = "client_secrets.json"
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
filters = ['vk','music','instagram','tiktok']

def is_auth():
    return os.path.exists("CREDENTIALS_PICKLE_FILE")

def get_auth_service():
    print("Getting service")
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    else:
        print("getting flow")
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes, redirect_uri="urn:ietf:wg:oauth:2.0:oob:auto")
        credentials = flow.run_local_server(host='localhost',
                                            port=6969, 
                                            authorization_prompt_message='Please visit this URL: {url}', 
                                            success_message='The auth flow is complete; you may close this window.',
                                            open_browser=True)
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(api_service_name, api_version, credentials = credentials)

# returns link for user to follow
def get_auth_service_link():
    return get_auth_service_link_redirect(redirect_uri="http://[::1]:80/authorise/auto")

def get_auth_service_link_redirect(redirect_uri: str):
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes, redirect_uri=redirect_uri)
    url = flow.authorization_url()
    return url,flow

def get_credentials(flow,code):
    flow.fetch_token(code=code)
    credentials = flow.credentials
    return credentials 

def verify_cached_credentials():
    return os.path.exists("CREDENTIALS_PICKLE_FILE")