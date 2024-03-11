import time
import json

class StatTracker:
    def __init__(self):
        self.start_time = time.time()
        self.game_times = {}
        self.total_swaps = 0

    def game_switched(self, game_path):
        current_time = time.time()
        if game_path in self.game_times:
            self.game_times[game_path]['end_time'] = current_time
        self.total_swaps += 1

    def start_game_timer(self, game_path):
        current_time = time.time()
        self.game_times[game_path] = self.game_times.get(game_path, {'start_time': current_time, 'end_time': current_time})

    def get_stats(self):
        total_time = time.time() - self.start_time
        detailed_stats = {game: {'total_time': times['end_time'] - times['start_time']}
                          for game, times in self.game_times.items()}
        return total_time, self.total_swaps, detailed_stats

    def export_stats(self, file_path):
        total_time, total_swaps, detailed_stats = self.get_stats()
        stats = {
            'Total Time': total_time,
            'Total Swaps': total_swaps,
            'Game Times': detailed_stats
        }
        with open(file_path, 'w') as file:
            json.dump(stats, file, indent=4)
