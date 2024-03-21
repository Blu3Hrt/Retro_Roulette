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

    def ensure_output_directory_exists(self, session_path):
        stats_output_path = os.path.join(session_path, 'output')
        os.makedirs(stats_output_path, exist_ok=True)
        return stats_output_path

    def write_stat_to_file(self, stats_output_path, filename, value):
        file_path = os.path.join(stats_output_path, filename)
        with open(file_path, 'w') as f:
            f.write(str(value))

    def write_individual_game_stats_to_files(self, session_path):
        stats_output_path = self.ensure_output_directory_exists(session_path)

        for game_path, stats in self.game_stats.items():
            game_filename = os.path.splitext(os.path.basename(game_path))[0]
            self.write_stat_to_file(stats_output_path, f'{game_filename}_swaps.txt', stats['swaps'])
            formatted_time = self.format_time(stats['time_spent'])
            self.write_stat_to_file(stats_output_path, f'{game_filename}_time.txt', formatted_time)

    def write_total_stats_to_files(self, session_path):
        stats_output_path = self.ensure_output_directory_exists(session_path)

        self.write_stat_to_file(stats_output_path, 'total_swaps.txt', self.total_swaps)
        formatted_total_shuffling_time = self.format_time(self.total_shuffling_time)
        self.write_stat_to_file(stats_output_path, 'total_shuffling_time.txt', formatted_total_shuffling_time)

    def write_current_game_stats_to_files(self, session_path, current_game_name):
        if current_game_name and current_game_name in self.game_stats:
            stats_output_path = self.ensure_output_directory_exists(session_path)
            current_game_stats = self.game_stats[current_game_name]

            self.write_stat_to_file(stats_output_path, 'current_swaps.txt', current_game_stats['swaps'])
            formatted_current_game_time = self.format_time(current_game_stats['time_spent'])
            self.write_stat_to_file(stats_output_path, 'current_time.txt', formatted_current_game_time)
            self.write_stat_to_file(stats_output_path, 'current_game_name.txt', current_game_name)


                

                
                    