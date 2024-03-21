import json
import os
from stat_tracker import StatsTracker

class GameManager:
    def __init__(self, file_path='games.json'):
        self.file_path = file_path
        self.games = {}
        self.stats_tracker = StatsTracker()
        self.current_game = None
        self.save_states = {}

    def switch_game(self, game_name):
        try:
            if self.current_game:
                self.stats_tracker.end_game(self.current_game)
            self.current_game = game_name
            self.stats_tracker.start_game(game_name)
        except Exception as e:
            print("Error switching game:", e)
            raise



    def load_games(self, game_data):

        self.games = game_data 
        

    def save_games(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.games, file, indent=4)

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
            
    def load_save_states(self, save_states_data):
        # Implement based on how your application should handle save states
        for game_path, save_state in save_states_data.items():
            if game_path in self.games:
                self.save_states[game_path] = save_state


    def mark_game_as_not_completed(self, path):
        if path in self.games:
            self.games[path]['completed'] = False
            self.save_games()
            
