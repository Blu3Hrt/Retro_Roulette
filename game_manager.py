import json
import os

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

    def add_game(self, path, name=None, goals=None):
        normalized_path = os.path.abspath(path)
        if normalized_path in self.games:
            return

        self.games[normalized_path] = {
            'name': name or os.path.basename(path),
            'completed': False,
            'goals': goals or ""
        }
        self.save_games()

    def set_game_goals(self, path, goals):
        if path in self.games:
            self.games[path]['goals'] = goals
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
