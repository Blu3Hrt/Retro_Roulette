import json, os, logging, shutil

class SessionManager:
    def __init__(self, directory='sessions'):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

# Update the save_session method in the SessionManager class to include the 'file_path' argument
    def save_session(self, name, games, stats, save_states, file_path):
        """Save a session to disk."""
        session_data = {
            'name': name,
            'games': games,
            'stats': stats,
            'save_states': save_states,
        }
        with open(file_path, 'w') as file:
            json.dump(session_data, file, indent=4)

    def load_session(self, name):
        file_path = os.path.join(self.directory, f"{name}.json")
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"Session file {file_path} not found.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {file_path}.")
            return None
        except Exception as e:
            logging.error(f"An error occurred while loading session {name}: {e}")
            return None


    def get_saved_sessions(self):
        return [os.path.splitext(f)[0] for f in os.listdir(self.directory) if f.endswith('.json')]
    
    def delete_session(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        save_state_dir = os.path.join('save_states', session_name)  # Path to the save state directory
        try:
            os.remove(session_file)
            if os.path.isdir(save_state_dir):  # Check if the directory exists
                shutil.rmtree(save_state_dir)  # Delete the directory and all its contents
            return True
        except FileNotFoundError:
            return False
        except OSError as e:  # To handle any error while deleting the directory
            logging.exception(f"Error while deleting save state directory: {e}")
            return False
        
    def rename_session(self, old_name, new_name):
        old_file = os.path.join(self.directory, f"{old_name}.json")
        new_file = os.path.join(self.directory, f"{new_name}.json")
        if os.path.exists(new_file):
            return False
        try:
            if not os.path.isfile(old_file):
                raise ValueError("Old session file does not exist or is not a file")
            if not new_name:
                raise ValueError("New session name is invalid")
    
            # Rename the file first
            os.rename(old_file, new_file)
    
            # Now update the 'name' inside the session file
            with open(new_file, 'r+') as file:
                session_data = json.load(file)
                session_data['name'] = new_name  # Update the session name
                file.seek(0)  # Move to the start of the file
                json.dump(session_data, file, indent=4)
                file.truncate()  # Remove any remaining part of the old content
    
            # Check if there is a save state directory for this session
            old_save_state_dir = os.path.join('save_states', old_name)
            new_save_state_dir = os.path.join('save_states', new_name)
            if os.path.exists(old_save_state_dir):
                os.rename(old_save_state_dir, new_save_state_dir)
    
            return True
        except OSError as e:
            print(e)
        except Exception as e:
            logging.exception("Unknown error while renaming session")
        return False

    def get_session_info(self, session_name):
        session_file = os.path.join(self.directory, f"{session_name}.json")
        try:
            with open(session_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

     