import json, os
from datetime import datetime

class SessionManager:
    def __init__(self, directory='sessions'):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save_session(self, session_name, games, stats, save_states):
        session_data = {
            'games': games,
            'stats': stats,
            'save_states': save_states
        }
        file_path = os.path.join(self.directory, f"{session_name}.json")
        with open(file_path, 'w') as file:
            json.dump(session_data, file, indent=4)

    def load_session(self, session_name):
        file_path = os.path.join(self.directory, f"{session_name}.json")
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def get_saved_sessions(self):
        return [f.replace('.json', '') for f in os.listdir(self.directory) if f.endswith('.json')]
    
    def delete_session(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        try:
            os.remove(session_file)
            return True
        except FileNotFoundError:
            return False
        
    def rename_session(self, old_name, new_name):
        old_file = os.path.join(self.directory, f"{old_name}.json")
        new_file = os.path.join(self.directory, f"{new_name}.json")
        if os.path.exists(new_file):
            return False  # New session name already exists
        try:
            os.rename(old_file, new_file)
            return True
        except FileNotFoundError:
            return False            

    def get_session_info(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        try:
            with open(session_file, 'r') as file:
                session_data = json.load(file)
            
            file_stats = os.stat(session_file)
            last_modified = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

            # Extract other info from session_data as needed
            num_games = len(session_data.get('games', {}))
            # Assuming you track total playtime or other stats in your session_data
            total_playtime = session_data.get('total_playtime', 'Not available')

            info = (
                f"Session Name: {session_name}\n"
                f"Last Modified: {last_modified}\n"
                f"Number of Games: {num_games}\n"
                f"Total Playtime: {total_playtime}"
            )
            return info
        except FileNotFoundError:
            return "Session file not found."
        except json.JSONDecodeError:
            return "Error reading session data."