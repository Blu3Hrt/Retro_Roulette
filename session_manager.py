import json, os
from datetime import datetime

class SessionManager:
    def __init__(self, directory='sessions'):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def save_session(self, name, games, stats, save_states, file_path):
        """Save a session to disk."""
        session_data = {
            'name': name,
            'games': games,
            'stats': stats,
            'save_states': save_states,
        }
        file_path = os.path.join(self.directory, f"{name}.json")
        with open(file_path, 'w') as file:
            json.dump(session_data, file, indent=4)

    def load_session(self, session_name):
        """Check for bugs such as null pointer references, unhandled exceptions,
        and more.
        """
        file_path = os.path.join(self.directory, f"{session_name}.json")
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None
        except OSError as e:
            raise e
        except json.JSONDecodeError as e:
            raise e
        except Exception:
            raise

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
        """
        Renames a saved session.

        Parameters:
        old_name (str): The name of the saved session to rename.
        new_name (str): The new name for the saved session.

        Returns:
        bool: True if the session was renamed, False otherwise.
        """
        old_file = os.path.join(self.directory, f"{old_name}.json")
        new_file = os.path.join(self.directory, f"{new_name}.json")
        if os.path.exists(new_file):
            # New session name already exists
            return False
        try:
            if not old_file or not os.path.isfile(old_file):
                raise ValueError("Old session file does not exist or is not a file")
            if not new_name or not isinstance(new_name, str):
                raise ValueError("New session name is invalid")
            os.rename(old_file, new_file)
            return True
        except OSError as e:
            print(e)
        except Exception as e:
            print("Unknown error while renaming session:", e)
        return False

    def get_session_info(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        try:
            with open(session_file, 'r') as file:
                session_data = json.load(file)
            return session_data
        except FileNotFoundError:
            return "Session file not found."
        except json.JSONDecodeError:
            return "Error reading session data."
 
    def session_exists(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        return os.path.isfile(session_file)
    
    def get_default_session_path(self):
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions", "Default Session.json")