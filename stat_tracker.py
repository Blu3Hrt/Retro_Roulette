import time, os

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

    def write_individual_stats_to_files(self, session_path, current_game_name=None):
        print("[DEBUG] Writing individual stats to files")
        stats_output_path = os.path.join(session_path, 'output')
        os.makedirs(stats_output_path, exist_ok=True)
    
        # Write each individual game stat to separate files for swaps and formatted time
        for game_name, stats in self.game_stats.items():
            print(f"[DEBUG] Writing stats for {game_name}")
            swaps_file_path = os.path.join(stats_output_path, f'{game_name}_swaps.txt')
            time_file_path = os.path.join(stats_output_path, f'{game_name}_time.txt')
            with open(swaps_file_path, 'w') as f_swaps, open(time_file_path, 'w') as f_time:
                f_swaps.write(f"{stats['swaps']}")
                formatted_time = self.format_time(stats['time_spent'])
                f_time.write(f"{formatted_time}")
    
        # Write total swaps and shuffling time to their respective files
        print("[DEBUG] Writing total swaps and total shuffling time")
        with open(os.path.join(stats_output_path, 'total_swaps.txt'), 'w') as f:
            f.write(str(self.total_swaps))
        with open(os.path.join(stats_output_path, 'total_shuffling_time.txt'), 'w') as f:
            formatted_total_shuffling_time = self.format_time(self.total_shuffling_time)
            f.write(formatted_total_shuffling_time)
    
        # If a current game is specified, write its stats to a special set of files
        if current_game_name and current_game_name in self.game_stats:
            print(f"[DEBUG] Writing current game stats for {current_game_name}")
            current_game_stats = self.game_stats[current_game_name]
            current_game_swaps_file_path = os.path.join(stats_output_path, 'current_swaps.txt')
            current_game_time_file_path = os.path.join(stats_output_path, 'current_time.txt')
            current_game_name_file_path = os.path.join(stats_output_path, 'current_game_name.txt')  # Path for the new file

            with open(current_game_swaps_file_path, 'w') as f_swaps, \
                open(current_game_time_file_path, 'w') as f_time, \
                open(current_game_name_file_path, 'w') as f_name:  # Open the new file for writing
                f_swaps.write(f"{current_game_stats['swaps']}")
                formatted_current_game_time = self.format_time(current_game_stats['time_spent'])
                f_time.write(f"{formatted_current_game_time}")
                f_name.write(current_game_name)  # Write the current game name to the new file
                
    
                
                    