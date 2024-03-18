import time

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

    def load_session_data(self):
        session_name = self.session_manager.get_current_session_name()
        session_data = self.session_manager.load_session(session_name)
        
        if session_data:
            self.games = session_data.get('games', {})
            
            # Assuming the structure of the stats array is consistent 
            # with the example you provided.
            game_stats = session_data.get('stats', [])[0] if len(session_data.get('stats', [])) > 0 else {}
            total_swaps = session_data.get('stats', [])[1] if len(session_data.get('stats', [])) > 1 else 0
            total_time_spent = session_data.get('stats', [])[2] if len(session_data.get('stats', [])) > 2 else 0
            
            # Initialize StatsTracker with the parsed stats.
            initial_stats = {
                'game_stats': game_stats,
                'total_swaps': total_swaps,
                'total_shuffling_time': total_time_spent
            }
            self.stats_tracker = StatsTracker(initial_stats)
            
            self.save_states = session_data.get('save_states', {})
        else:
            self.games = {}
            self.stats_tracker = StatsTracker()
            self.save_states = {}