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
    
    def get_broadcaster_id(self):
        access_token, _ = self.get_tokens_securely()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': self.client_id
        }
        response = requests.get('https://api.twitch.tv/helix/users', headers=headers)
        response.raise_for_status()  # raise exception if request failed
        return response.json()['data'][0]['id']

    def get_rewards(self):
        broadcaster_id = self.get_broadcaster_id()
        access_token, _ = self.get_tokens_securely()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': self.client_id
        }
        response = requests.get(f'https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id={broadcaster_id}', headers=headers)
        response.raise_for_status()  # raise exception if request failed
        logging.debug(f"Rewards: {response.json()['data']}")
        return response.json()['data']    
    
    def create_rewards(self, pause_shuffle_cost, force_swap_cost, pause_shuffle_cooldown, force_swap_cooldown, pause_shuffle_enabled, force_swap_enabled):
        existing_rewards = self.get_rewards()

        pause_shuffle_settings = {
            'cost': pause_shuffle_cost,
            'is_global_cooldown_enabled': True,
            'global_cooldown_seconds': pause_shuffle_cooldown,
            'should_redemptions_skip_request_queue': True
        }

        force_swap_settings = {
            'cost': force_swap_cost,
            'is_global_cooldown_enabled': True,
            'global_cooldown_seconds': force_swap_cooldown,
            'should_redemptions_skip_request_queue': True
            
        }
        
        pause_shuffle_settings['is_enabled'] = pause_shuffle_enabled
        force_swap_settings['is_enabled'] = force_swap_enabled        

        if 'Pause Shuffle' not in [reward['title'] for reward in existing_rewards]:
            self.create_reward('Pause Shuffle', **pause_shuffle_settings)
        else:
            self.update_reward('Pause Shuffle', **pause_shuffle_settings)

        if 'Force Swap' not in [reward['title'] for reward in existing_rewards]:
            self.create_reward('Force Swap', **force_swap_settings)
        else:
            self.update_reward('Force Swap', **force_swap_settings)

    def update_reward(self, reward_name, **settings):
        # get the id of the reward
        reward_id = next((reward['id'] for reward in self.get_rewards() if reward['title'] == reward_name), None)
        if reward_id is None:
            return

        broadcaster_id = self.get_broadcaster_id()
        access_token, _ = self.get_tokens_securely()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': self.client_id
        }
        data = {
            'broadcaster_id': broadcaster_id,
            'id': reward_id,
            **settings
        }
        response = requests.patch(f'https://api.twitch.tv/helix/channel_points/custom_rewards?id={reward_id}', headers=headers, json=data)
        response.raise_for_status()  # raise exception if request failed
        logging.debug(f"Updated reward: {response.json()['data']}")
        return response.json()['data']
            

    def create_reward(self, reward_name, **settings):
        broadcaster_id = self.get_broadcaster_id()
        access_token, _ = self.get_tokens_securely()
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Client-Id': self.client_id
        }
        data = {
            'broadcaster_id': broadcaster_id,
            'title': reward_name,
            **settings
        }
        response = requests.post('https://api.twitch.tv/helix/channel_points/custom_rewards', headers=headers, json=data)
        response.raise_for_status()  # raise exception if request failed
        logging.debug(f"Created reward: {response.json()['data']}")
        return response.json()['data']