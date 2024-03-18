import json

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file

    def save_config(self, config_data):
        with open(self.config_file, 'w') as file:
            json.dump(config_data, file, indent=4)

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # If there's an issue with reading the file, return a default configuration
            return self.default_config()

    def default_config(self):
        # Returns a default configuration
        return {
            'bizhawk_path': '',
            'min_shuffle_interval': 30,
            'max_shuffle_interval': 60
        }

    def get_config_path(self):
        return self.config_file
