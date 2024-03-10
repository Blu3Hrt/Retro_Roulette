import json

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_config(self, new_config):
        with open(self.config_file, 'w') as file:
            json.dump(new_config, file, indent=4)
        self.config = new_config
