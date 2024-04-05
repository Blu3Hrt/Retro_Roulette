import time, os, logging

class StatsTracker:
    def __init__(self, initial_stats=None):
        if initial_stats is not None:
            self.game_stats = initial_stats.get('game_stats', {})
            self.total_swaps = initial_stats.get('total_swaps', 0)
            self.total_shuffling_time = initial_stats.get('total_shuffling_time', 0)
        else:
            self.game_stats = {}
            self.total_swaps = 0
            self.total_shuffling_time = 0
        self.start_time = None

    def start_game(self, game_name):
        self.total_swaps += 1
        self.start_time = time.time()
        if game_name not in self.game_stats:
            self.game_stats[game_name] = {'swaps': 0, 'time_spent': 0}
        self.game_stats[game_name]['swaps'] += 1

    def end_game(self, game_name):
        if game_name in self.game_stats and self.start_time:
            time_spent = time.time() - self.start_time
            self.game_stats[game_name]['time_spent'] += time_spent
            self.game_stats[game_name]['formatted_time_spent'] = self.format_time(time_spent)
            self.total_shuffling_time += time_spent
            self.total_formatted_shuffling_time = self.format_time(self.total_shuffling_time)

    def format_time(self, seconds):
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_stats(self):
        return self.game_stats, self.total_swaps, self.total_shuffling_time

    def reset_stats(self):
        self.game_stats = {}
        self.total_swaps = 0
        self.total_shuffling_time = 0
        self.start_time = None



                

                
                    