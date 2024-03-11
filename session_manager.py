import json, os

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
