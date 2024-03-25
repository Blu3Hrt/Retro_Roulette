import requests
import keyring
import websocket
import webbrowser
import json
import os
import logging
import time
from dotenv import load_dotenv
from urllib.parse import urlencode
from PySide6.QtCore import QObject, Signal

from Python_Client import send_command
import logging


class TwitchIntegration(QObject):
    force_swap_signal = Signal()
    pause_shuffle_signal = Signal()
    def __init__(self, main_window):
        super().__init__()
        logging.basicConfig(filename='Main.log', encoding='utf-8', level=logging.DEBUG)
        load_dotenv()
        self.client_id = os.environ.get('TWITCH_CLIENT_ID')
        self.client_secret = os.environ.get('TWITCH_CLIENT_SECRET')
        self.redirect_uri = os.environ.get('TWITCH_REDIRECT_URI')
        self.scopes = os.environ.get('TWITCH_SCOPES').split('+')
        self.main_window = main_window
        self.main_window.force_swap()
    
        

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

    def refresh_access_token(self):
        refresh_token = self.get_tokens_securely()[1]
        if not refresh_token:
            print("No refresh token available. Please sign in again.")
            return
    
        refresh_url = "https://id.twitch.tv/oauth2/token"
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        response = requests.post(refresh_url, data=params)
        
        if response.status_code == requests.codes.ok:
            new_tokens = response.json()
            access_token = new_tokens.get('access_token')
            refresh_token = new_tokens.get('refresh_token')
            if access_token:
                self.save_tokens_securely(access_token, refresh_token)
                print("Token refreshed successfully.")
            else:
                print("Failed to refresh token. Please sign in again.")
        else:
            print(f"Failed to refresh token: {response.status_code}")

    def make_authenticated_request(self, url):
        access_token = self.get_tokens_securely()[0]
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
    
        if response.status_code == 401:
            print("Received 401 Client Error. Refreshing access token...")
            self.refresh_access_token()
            # Retry the request with the new token
            access_token = self.get_tokens_securely()[0]
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers)
    
        # Continue processing the response
        return response


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
        return response.json()['data']
    
    def handle_reward_redemption(self, reward_id):
        # Get the name of the redeemed reward
        reward_name = self.get_reward_name(reward_id)

        # Emit a signal to perform an action based on the redeemed reward
        if reward_name =="Force Swap":
            self.force_swap_signal.emit()
        if reward_name == "Pause Shuffle":
            self.pause_shuffle_signal.emit()
               
            
    def listen_for_rewards(self):
        # Connect to Twitch's PubSub server
        ws = websocket.WebSocketApp(
            'wss://pubsub-edge.twitch.tv',
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        

        # Get the access token
        access_token, _ = self.get_tokens_securely()

        # Get the user's channel ID
        channel_id = self.get_broadcaster_id()

        # Start the websocket connection
        ws.run_forever()
        logging.info("WebSocket connection started.")

        # Check if the WebSocket connection is open
        if ws.sock and ws.sock.connected:
            logging.info("WebSocket connection is open.")
            # Subscribe to the channel points topic for the user's channel
            ws.send(json.dumps({
                'type': 'LISTEN',
                'data': {
                    'topics': [f'channel-points-channel-v1.{channel_id}'],
                    'auth_token': access_token
                }
            }))
        else:
            logging.info("WebSocket connection is not open.")
            time.sleep(5)
            self.listen_for_rewards()

    def on_message(self, ws, message):        
        try:
            message_dict = json.loads(message)
            if message_dict.get('type') == 'MESSAGE':
                message_data = json.loads(message_dict.get('data', {}).get('message', '{}'))  # Parse the JSON string into a dictionary
                if message_data.get('type') == 'reward-redeemed':
                    if (
                        reward_id := message_data.get('data', {})
                        .get('redemption', {})
                        .get('reward', {})
                        .get('id')
                    ):
                        self.handle_reward_redemption(reward_id)
                    else:
                        print('No reward ID found in the message.')
                else:
                    print('Message data does not contain a "reward-redeemed" event.')
            elif message_dict.get('type') == 'reward-redeemed':
                # Existing code to handle reward redemptions
                if (
                    reward_id := message_dict.get('data', {})
                    .get('redemption', {})
                    .get('reward', {})
                    .get('id')
                ):
                    self.handle_reward_redemption(reward_id)
                else:
                    print('No reward ID found in the message.')

        except json.JSONDecodeError:
            print(f'Failed to parse message: {message}')
        except Exception as e:
            print(f'An error occurred while handling the message: {e}')

    def on_error(self, ws, error):
        print(f'Error: {error}')

    def on_close(self, ws, *args, **kwargs):
        print(f'Connection closed with args: {args}, kwargs: {kwargs}')
        # Reconnect after a delay
        time.sleep(5)
        self.listen_for_rewards()
    
    def get_reward_id(self, reward_name):
        rewards = self.get_rewards()
        for reward in rewards:
            if reward['title'] == reward_name:
                return reward['id']
        logging.warning(f"Reward ID not found for {reward_name}")
        return None
    
    def get_reward_name(self, reward_id):
        rewards = self.get_rewards()
        for reward in rewards:
            if reward['id'] == reward_id:
                return reward['title']
        logging.warning(f"Reward name not found for {reward_id}")
        return "Reward Name"
    
    def on_open(self, ws):
        # Get the access token
        access_token, _ = self.get_tokens_securely()
        logging.debug(f"Access token: {access_token}")

        # Get the user's channel ID
        channel_id = self.get_broadcaster_id()
        logging.debug(f"Channel ID: {channel_id}")

        # Subscribe to the channel points topic for the user's channel
        ws.send(json.dumps({
            'type': 'LISTEN',
            'data': {
                'topics': [f'channel-points-channel-v1.{channel_id}'],
                'auth_token': access_token
            }
        }))
