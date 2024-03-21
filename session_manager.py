import json, os, logging, shutil

class SessionManager:
    def __init__(self, directory='sessions'):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

# Update the save_session method in the SessionManager class to include the 'file_path' argument
    def save_session(self, name, games, stats, save_states, file_path=None):
        """Save a session to disk within a dedicated folder for the session."""
        # Create the session folder if it doesn't exist
        session_folder = os.path.join(self.directory, name)
        os.makedirs(session_folder, exist_ok=True)
    
        # If a custom file_path is not provided, define the default path
        if not file_path:
            file_path = os.path.join(session_folder, 'session.json')
    
        # Save the session data
        session_data = {
            'name': name,
            'games': games,
            'stats': stats,
            'save_states': save_states,
        }
        with open(file_path, 'w') as file:
            json.dump(session_data, file, indent=4)

    def load_session(self, name):
        file_path = os.path.join(self.directory, name, 'session.json')
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

    
    def delete_session(self, session_name):
        session_folder = os.path.join(self.directory, session_name)
        try:
            if os.path.isdir(session_folder):
                shutil.rmtree(session_folder)  # Delete the directory and all its contents
            return True
        except FileNotFoundError:
            return False
        except OSError as e:  # To handle any error while deleting the directory
            logging.exception(f"Error while deleting save state directory: {e}")
            return False
        
    def rename_session(self, old_name, new_name):
        old_folder = os.path.join(self.directory, old_name)
        new_folder = os.path.join(self.directory, new_name)

        if os.path.exists(new_folder):
            logging.error(f"Session folder '{new_name}' already exists.")
            return False

        try:
            return self.rename_session_logic(old_folder, new_folder, new_name)
        except OSError as e:
            logging.exception(f"Error while renaming session folder: {e}")
            return False

    def rename_session_logic(self, old_folder, new_folder, new_name):
        # Rename the session folder
        os.rename(old_folder, new_folder)

        # Update the 'name' inside the session.json file
        session_file = os.path.join(new_folder, 'session.json')
        if os.path.isfile(session_file):
            with open(session_file, 'r+') as file:
                session_data = json.load(file)
                session_data['name'] = new_name  # Update the session name
                file.seek(0)  # Move to the start of the file
                json.dump(session_data, file, indent=4)
                file.truncate()  # Remove any remaining part of the old content

        # Rename the savestates folder if it exists
        old_savestates_folder = os.path.join(old_folder, 'savestates')
        new_savestates_folder = os.path.join(new_folder, 'savestates')
        if os.path.exists(old_savestates_folder):
            os.rename(old_savestates_folder, new_savestates_folder)

        return True

    def get_session_info(self, session_name):
        session_file = os.path.join(self.directory, session_name, 'session.json')
        try:
            with open(session_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

     