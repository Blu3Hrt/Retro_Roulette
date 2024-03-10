import json

class GameManager:
    def __init__(self, file_path='games.json'):
        self.file_path = file_path
        self.games = self.load_games()

    def load_games(self):
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_games(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.games, file, indent=4)
            print("Games saved")

    def add_game(self, path, name=None):
        if path in self.games:
            return  # Game already exists, do not add

        self.games[path] = {'name': name or path, 'completed': False}
        self.save_games()

    def remove_game(self, path):
        if path in self.games:
            del self.games[path]
            self.save_games()

    def mark_game_as_completed(self, path):
        if path in self.games:
            self.games[path]['completed'] = True
            self.save_games()

    def rename_game(self, path, new_name):
        if path in self.games:
            self.games[path]['name'] = new_name
            self.save_games()
