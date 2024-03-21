import requests
import keyring
import websocket
import webbrowser
import json
import os
import logging
import threading
from dotenv import load_dotenv
from urllib.parse import urlencode

from Python_Client import send_command


class TwitchIntegration:
    def __init__(self):
        load_dotenv()
        self.client_id = os.environ.get('TWITCH_CLIENT_ID')
        self.client_secret = os.environ.get('TWITCH_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('TWITCH_REDIRECT_URI')
        self.scopes = os.environ.get('TWITCH_SCOPES').split('+')

    def save_tokens_securely(self, access_token, refresh_token):
        keyring.set_password('TwitchIntegration', 'access_token', access_token)
        keyring.set_password('TwitchIntegration', 'refresh_token', refresh_token)

    def get_tokens_securely(self):
        access_token = keyring.get_password('TwitchIntegration', 'access_token')
        refresh_token = keyring.get_password('TwitchIntegration', 'refresh_token')
        return access_token, refresh_token

    def handle_oauth_redirect(self, code):
        token_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(token_url, params=params)
        response_data = response.json()

        if response.status_code != 200:
            logging.error(f"Failed to exchange code for tokens: {response_data}")
            return

        access_token = response_data.get('access_token')
        refresh_token = response_data.get('refresh_token')
        self.save_tokens_securely(access_token, refresh_token)
        logging.info("Tokens saved securely.")


    def revoke_access_token(self):
        access_token, _ = self.get_tokens_securely()
        if not access_token:
            print("No access token available to revoke.")
            return

        revoke_url = "https://id.twitch.tv/oauth2/revoke"
        params = {
            'client_id': self.client_id,
            'token': access_token
        }
        response = requests.post(revoke_url, params=params)
        if response.status_code == requests.codes.ok:
            print("Token revoked successfully.")
        else:
            print(f"Failed to revoke token: {response.status_code}")

    def clear_tokens_securely(self):
        keyring.delete_password('TwitchIntegration', 'access_token')
        keyring.delete_password('TwitchIntegration', 'refresh_token')

    def open_authentication_url(self):
        query_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes)
        }
        auth_url = f"https://id.twitch.tv/oauth2/authorize?{urlencode(query_params)}"
        webbrowser.open_new(auth_url)
      
    def is_authenticated(self):
        access_token, refresh_token = self.get_tokens_securely()
        return bool(access_token) and bool(refresh_token)