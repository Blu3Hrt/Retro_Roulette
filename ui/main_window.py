from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QInputDialog, QLabel, QLineEdit
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit, QMenu
from PySide6.QtCore import Qt, QTimer
from game_manager import GameManager
from config import ConfigManager
from session_manager import SessionManager
from stat_tracker import StatsTracker
from ui.style import Style
import Python_Client

import os, random, subprocess, time, json, sys, logging
import psutil

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(600, 600)
        self.setWindowTitle("Retro Roulette")
        
        # Create Tab Widget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        self.game_manager = GameManager()
        self.config_manager = ConfigManager()
        self.session_manager = SessionManager()
        self.stat_tracker = StatsTracker()
        self.style_setter = Style()
        
        # Load configuration
        self.config = self.config_manager.load_config()
        
        # Initialize UI tabs
        self.init_ui()
        self.init_tabs()
        
        # Initialize session name with None
        self.current_session_name = None
        
        # Load last session if it exists
        self.load_last_session()
        
        # Set up UI refresh and stats timer
        self.refresh_ui()
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats_display)
        self.stats_timer.start(1000)
        
     
    def init_ui(self):
        Style.set_dark_style(self)
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
                      

    def init_tabs(self):
        # Create tabs for different functionalities
        self.tab_widget.addTab(self.create_game_management_tab(), "Game Management")
        self.tab_widget.addTab(self.create_session_management_tab(), "Session Management")
        self.tab_widget.addTab(self.create_shuffle_management_tab(), "Shuffle Management")
        self.tab_widget.addTab(self.create_configuration_tab(), "Configuration")
        self.tab_widget.addTab(self.create_stats_tab(), "Stats")




    def create_game_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
    
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search games...")
        self.search_input.textChanged.connect(self.filter_games)
        layout.addWidget(self.search_input)
    
        add_games_button = QPushButton("Add Games")
        add_games_button.clicked.connect(self.add_games)
        layout.addWidget(add_games_button)
    
        add_directory_button = QPushButton("Add Games from Directory")
        add_directory_button.clicked.connect(self.add_games_from_directory)
        layout.addWidget(add_directory_button)
    
        self.game_list = QListWidget()
        self.game_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_list.customContextMenuRequested.connect(self.show_game_context_menu)
        self.game_list.itemSelectionChanged.connect(self.display_game_details)  # Connect to display game details method
        layout.addWidget(self.game_list)
    
        self.game_list.itemDoubleClicked.connect(self.handle_double_click)
    
        # Create a label to display the selected game's details
        self.game_details_label = QLabel("Select a game to view details")
        layout.addWidget(self.game_details_label)
    
        return tab

    def show_game_context_menu(self, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected Game")
        # Determine if the selected game is completed or not
        selected_items = self.game_list.selectedItems()
        if selected_items:
            game_name = selected_items[0].text().split(" - ")[0]
            game_path = self.find_game_path_by_name(game_name)
            if game_path and self.game_manager.games[game_path]['completed']:
                # If the game is completed, show "Unmark as Completed" option
                complete_action = menu.addAction("Unmark as Completed")
            else:
                # If the game is not completed, show "Mark as Completed" option
                complete_action = menu.addAction("Mark as Completed")
        rename_action = menu.addAction("Rename Selected Game")
        goals_action = menu.addAction("Set Goals for Selected Game")
    
        action = menu.exec_(self.game_list.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_game()
        elif action == complete_action:
            # Call the appropriate method based on the action text
            if complete_action.text() == "Mark as Completed":
                self.mark_game_as_completed()
            else:
                self.unmark_game_as_not_completed()
        elif action == rename_action:
            self.prompt_rename_game()
        elif action == goals_action:
            self.prompt_set_game_goals()

    def handle_double_click(self, item):
        self.prompt_rename_game()
    
    def prompt_set_game_goals(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected for setting goals")
            return

        game_name = selected_items[0].text().split(" - ")[0]
        game_path = self.find_game_path_by_name(game_name)
        if game_path:
            current_goals = self.game_manager.games[game_path].get('goals', '')
            new_goals, ok = QInputDialog.getMultiLineText(self, "Set Goals", "Enter goals for the game:", current_goals)
            
            if ok:
                self.game_manager.set_game_goals(game_path, new_goals)
                self.refresh_game_list()    
    
    def filter_games(self):
        search_text = self.search_bar.text().lower()
        for i in range(self.game_list.count()):
            item = self.game_list.item(i)
            item.setHidden(search_text not in item.text().lower())
            
    def set_selected_game_goals(self):
        selected_items = self.game_list.selectedItems()
        if selected_items:
            game_name = selected_items[0].text().split(" - ")[0]
            game_path = self.find_game_path_by_name(game_name)
            if game_path:
                goals = self.goal_input.text()
                self.game_manager.set_game_goals(game_path, goals)
                self.goal_input.clear()
                self.refresh_game_list()            

    def display_game_details(self):
        selected_items = self.game_list.selectedItems()
        if selected_items:
            game_name = selected_items[0].text().split(" - ")[0]
            game_path = self.find_game_path_by_name(game_name)
            if game_path:
                game_data = self.game_manager.games[game_path]
                details = f"Name: {game_data['name']}\nPath: {game_path}\nCompleted: {'Yes' if game_data['completed'] else 'No'}"
                goals = game_data.get('goals', 'No goals set')
                details += f"\nGoals: {goals}"
    
                # Retrieve game stats and format them for display
                game_stats = self.game_manager.stats_tracker.game_stats.get(game_name, {})
                swaps = game_stats.get('swaps', 0)
                time_spent = self.game_manager.stats_tracker.format_time(game_stats.get('time_spent', 0))
                
                # Append the stats to the game details
                details += f"\nSwaps: {swaps}\nTime Spent: {time_spent}"
    
                self.game_details_label.setText(details)
        else:
            self.game_details_label.setText("Select a game to view details")   

    def add_games(self):
        app_root = os.path.dirname(sys.modules['__main__'].__file__)
        games_dir = os.path.join(app_root, "games")
        if not os.path.exists(games_dir):
            os.makedirs(games_dir)

        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Games", games_dir, 
                                                     "Game Files (*.nes *.snes *.gbc *.gba *.md *.nds)")
        added_any = False
        for file_name in file_names:
            normalized_path = os.path.abspath(file_name)
            if normalized_path not in self.game_manager.games:
                self.game_manager.add_game(normalized_path)
                added_any = True
            else:
                print("Duplicate Game", f"{os.path.basename(file_name)} is already in the list.")

        if added_any:
            self.refresh_ui()
            # Prepare the session data
            current_game_stats, total_swaps, total_shuffling_time = self.game_manager.stats_tracker.get_stats()
            session_data = {
                'games': self.game_manager.games,
                'stats': [current_game_stats, total_swaps, total_shuffling_time],
                'save_states': self.game_manager.save_states
            }
            # Construct the file path for the session file
            session_file_path = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")
            # Save the session
            self.session_manager.save_session(self.current_session_name, session_data['games'], 
                                            session_data['stats'], session_data['save_states'], session_file_path)
            
            

    def add_games_from_directory(self):
        app_root = os.path.dirname(sys.modules['__main__'].__file__)
        games_dir = os.path.join(app_root, "games")
        if not os.path.exists(games_dir):
            os.makedirs(games_dir)

        directory = QFileDialog.getExistingDirectory(self, "Select Directory", games_dir, 
                                                      QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if directory:
            added_any = False
            for file in os.listdir(directory):
                if file.endswith((".nes", ".snes", ".gbc", ".gba", ".md", ".nds")):
                    full_path = os.path.abspath(os.path.join(directory, file))
                    if full_path not in self.game_manager.games:
                        self.game_manager.add_game(full_path)
                        added_any = True
                    else:
                        print("Duplicate Game", f"{file} is already in the list.")

        if added_any:
            self.refresh_ui()
            # Prepare the session data
            current_game_stats, total_swaps, total_shuffling_time = self.game_manager.stats_tracker.get_stats()
            session_data = {
                'games': self.game_manager.games,
                'stats': [current_game_stats, total_swaps, total_shuffling_time],
                'save_states': self.game_manager.save_states
            }
            # Construct the file path for the session file
            session_file_path = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")
            # Save the session
            self.session_manager.save_session(self.current_session_name, session_data['games'], 
                                            session_data['stats'], session_data['save_states'], session_file_path)
                

    def remove_selected_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.remove_game(game_path)

        self.refresh_ui()
        self.update_and_save_session()  # Save the session after removing the game

# e:/Coding/Retro_Roulette/ui/main_window.py:MainWindow.mark_game_as_completed
    def mark_game_as_completed(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected to mark as completed")
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.mark_game_as_completed(game_path)

        self.refresh_ui()
        self.update_and_save_session()  # Save the session after marking the game as completed
        
        
    def unmark_game_as_not_completed(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected to unmark as completed")
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.mark_game_as_not_completed(game_path)

        self.refresh_ui()
        self.update_and_save_session()    
        
        
            
            
    def prompt_rename_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected for renaming")
            return

        # Assuming only one game can be selected for renaming
        current_name = selected_items[0].text().split(" - ")[0]  # Extracting name before " - Completed" if present
        new_name, ok = QInputDialog.getText(self, "Rename Game", "Enter new name:", text=current_name)
        
        if ok and new_name:
            self.rename_selected_game(selected_items[0], new_name)            

    def rename_selected_game(self, item, new_name):
        path = self.find_game_path_by_name(item.text())
        if path:
            self.game_manager.rename_game(path, new_name)
            self.refresh_game_list()
            
    def find_game_path_by_name(self, name):
        # Find the original path of the game based on its displayed name
        for path, data in self.game_manager.games.items():
            if data['name'] == name.split(" - ")[0]:
                return path
        return None            
            
    def refresh_game_list(self):
        if hasattr(self, 'game_list'):
            self.game_list.clear()
        for game in self.game_manager.games.values():
            item_text = f"{game['name']} - {'Completed' if game['completed'] else 'In Progress'}"
            if hasattr(self, 'game_list'):
                self.game_list.addItem(item_text)




    def create_shuffle_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Button to launch BizHawk
        launch_bizhawk_button = QPushButton("Launch BizHawk")
        launch_bizhawk_button.clicked.connect(self.launch_bizhawk)
        layout.addWidget(launch_bizhawk_button)

        # Shuffle control buttons
        self.start_shuffle_button = QPushButton("Start Shuffle")
        self.start_shuffle_button.clicked.connect(self.start_shuffle)
        layout.addWidget(self.start_shuffle_button)

        self.pause_shuffle_button = QPushButton("Pause Shuffle")
        self.pause_shuffle_button.clicked.connect(self.pause_shuffle)
        layout.addWidget(self.pause_shuffle_button)

        self.resume_shuffle_button = QPushButton("Resume Shuffle")
        self.resume_shuffle_button.clicked.connect(self.resume_shuffle)
        layout.addWidget(self.resume_shuffle_button)

        # Initialize shuffle state
        self.is_shuffling = False
        self.current_game_path = None

        return tab

    def launch_bizhawk(self):
        if self.is_bizhawk_process_running():
            print("BizHawk is already running.")
            return

        try:
            self.execute_bizhawk_script()
        except Exception as e:
            print(f"Exception launching BizHawk: {e}")
            
    def is_bizhawk_process_running(self):
        # Check if BizHawk/EmuHawk process is running
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'EmuHawk.exe' or proc.info['name'] == 'BizHawk.exe':
                return True

        return False

    def start_shuffle(self):
        # Load the current session data
        session_data = self.session_manager.load_session(self.current_session_name)
        
        if session_data:
            # Load the stats from the session into the stats tracker
            game_stats = session_data.get('stats', [{}])[0]  # The first element is the game stats dictionary
            total_swaps = session_data.get('stats', [{}, 0])[1]  # The second element is the total swaps
            total_shuffling_time = session_data.get('stats', [{}, 0, 0])[2]  # The third element is the total shuffling time

            initial_stats = {
                'game_stats': game_stats,
                'total_swaps': total_swaps,
                'total_shuffling_time': total_shuffling_time
            }
            self.game_manager.stats_tracker = StatsTracker(initial_stats)
        if not self.is_shuffling:
            # Read shuffle interval configurations
            min_interval = self.config.get('min_shuffle_interval', 30)
            max_interval = self.config.get('max_shuffle_interval', 60)
            
            # Convert to milliseconds and ensure min_interval is not greater than max_interval
            self.shuffle_interval = random.randint(min(min_interval, max_interval), max(max_interval, min_interval)) * 1000
            
            # Check if BizHawk/EmuHawk process is running
            if self.is_bizhawk_process_running():
                self.is_shuffling = True
                self.shuffle_games()
            else:
                print("BizHawk/EmuHawk process is not running. Cannot start shuffle.")
        else:
            # Shuffle is already active, prevent starting another shuffle
            print("Shuffle is already active.")


    def determine_shuffle_interval(self):
        min_interval = self.config_manager.config.get('min_shuffle_interval', 30)
        max_interval = self.config_manager.config.get('max_shuffle_interval', 60)
        return random.randint(min_interval, max_interval) * 1000  # in milliseconds

    def pause_shuffle(self):
        self.is_shuffling = False
        # Additional logic to handle pause state

    def resume_shuffle(self):
        if not self.is_shuffling and self.game_manager.games:
            self.is_shuffling = True
            self.shuffle_games()


    def shuffle_games(self):
        # Check if shuffling is disabled or the game list is empty
        if not self.is_shuffling:
            logging.info("Shuffling is disabled.")
            return
        if not self.game_manager.games:
            logging.warning("No games available to shuffle.")
            QMessageBox.warning(self, "Shuffle Error", "No games available to shuffle.")
            self.is_shuffling = False  # Stop shuffling
            return

        # Remove current game from available games
        available_games = [game for game in self.game_manager.games if game != self.current_game_path]

        # If only one game is available, or all games are marked as completed, shuffling is not possible
        if len(available_games) <= 1:
            logging.info("Cannot shuffle: Only one game available or all games are completed.")
            QMessageBox.information(self, "Shuffle Info", "Cannot shuffle: Only one game available.")
            self.is_shuffling = False  # Stop shuffling
            return
        if all(self.game_manager.games[game]['completed'] for game in available_games):
            QMessageBox.information(self, "Congratulations!", "Amazing! You have completed all the games.")
            self.is_shuffling = False  # Stop shuffling
            return

        # Shuffle the games
        try:
            # Select a random game and switch to it
            next_game_path = random.choice(available_games)
            self.game_manager.switch_to_game(next_game_path)

            # Save and load game state
            if self.current_game_path:
                self.save_game_state(self.current_game_path)
            self.load_game(next_game_path)
            self.update_and_save_session()

        except Exception as e:
            logging.error(f"Error switching to the next game: {e}")
            self.statusBar().showMessage(f"An error occurred while switching games: {e}")
            return

        # Update current game path
        self.current_game_path = next_game_path

        # Schedule next shuffle
        shuffle_interval = self.determine_shuffle_interval()
        logging.info("Scheduling next shuffle in %d seconds", shuffle_interval // 1000)
        QTimer.singleShot(shuffle_interval, self.shuffle_games)

        # Check if BizHawk process is still running
        if not self.is_bizhawk_process_running():
            self.pause_shuffle()





    def ensure_directory_exists(self, state_path):
        directory = os.path.dirname(state_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def save_game_state(self, game_path):
        if not game_path:
            return
        state_path = self.get_state_path(game_path)
        self.ensure_directory_exists(state_path)  # Ensure the directory exists
        try:
            Python_Client.save_state(state_path)
            logging.info(f"Game state saved successfully to {state_path}")
        except Exception as e:
            logging.error(f"Error saving game state: {e}")
            QMessageBox.critical(self, "Save State Error", f"An error occurred while saving the game state: {e}")

    def load_game_state(self, game_path):
        print(f"Loading game state: {game_path}")  # Debugging line
        state_file = self.get_state_path(game_path)
        self.ensure_directory_exists(state_file)
        if os.path.exists(state_file):
            try:
                Python_Client.load_state(state_file)
                logging.info(f"Game state loaded successfully from {state_file}")
            except Exception as e:
                logging.error(f"Error loading game state: {e}")
                QMessageBox.critical(self, "Load State Error", f"An error occurred while loading the game state: {e}")
        else:
            print(f"State file does not exist: {state_file}")  # Debugging line
            # Create a new save state
            self.save_game_state(self.current_game_path)


    def load_game_state(self, game_path):
        print(f"Loading game state: {game_path}")  # Debugging line
        state_file = self.get_state_path(game_path)
        self.ensure_directory_exists(state_file)
        if os.path.exists(state_file):
            print(f"State file exists: {state_file}")  # Debugging line
            Python_Client.load_state(state_file)
        else:
            print(f"State file does not exist: {state_file}")  # Debugging line
            self.save_game_state(game_path)

    def execute_bizhawk_script(self):
        """Launch BizHawk with the Lua script"""
        bizhawk_exe = self.config["bizhawk_path"]
        lua_script = "Lua/bizhawk_server.lua"
        command = [bizhawk_exe, "--lua=" + lua_script]
        try:
            subprocess.Popen(command)
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "BizHawk executable not found.")

    def get_state_path(self, game_file):
        session_dir = os.path.join('save_states', self.current_session_name)
        game_id = os.path.splitext(os.path.basename(game_file))[0]
        state_file = f"{game_id}.state"
        return os.path.join(session_dir, state_file)
    
    


    def create_configuration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        #TODO add checkbox and logic to allow duplicate games in game list
        #TODO add ui color customization options for text, background, and font
        

        # Set up the BizHawk path input and button
        self.bizhawk_path_input = QLineEdit(self.config.get('bizhawk_path', ''))
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_bizhawk_path)
        layout.addWidget(self.bizhawk_path_input)
        layout.addWidget(browse_button)

        # Set up the min and max interval inputs
        self.min_interval_input = QLineEdit(str(self.config.get('min_shuffle_interval', '30')))
        self.max_interval_input = QLineEdit(str(self.config.get('max_shuffle_interval', '60')))
        layout.addWidget(self.min_interval_input)
        layout.addWidget(self.max_interval_input)

        # Set up the save and load buttons
        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)
        load_config_button = QPushButton("Load Configuration")
        load_config_button.clicked.connect(self.load_configuration)
        layout.addWidget(save_config_button)
        layout.addWidget(load_config_button)

        return tab


    def browse_bizhawk_path(self):
        path = QFileDialog.getOpenFileName(self, "Select BizHawk Executable", "", "Executable Files (*.exe)")[0]
        if path:
            self.bizhawk_path_input.setText(path)


    def save_configuration(self):
        # Collect configuration data from UI elements
        bizhawk_path = self.bizhawk_path_input.text()
        min_interval = self.min_interval_input.text()
        max_interval = self.max_interval_input.text()

        # Validate and prepare the configuration data
        valid_intervals, message = self.validate_intervals(min_interval, max_interval)
        if not valid_intervals:
            QMessageBox.warning(self, "Invalid Input", message)
            return

        try:
            # Ensure intervals are integers
            min_interval = int(min_interval)
            max_interval = int(max_interval)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Intervals must be numeric.")
            return

        # Compile configuration data
        config_data = {
            'bizhawk_path': bizhawk_path,
            'min_shuffle_interval': min_interval,
            'max_shuffle_interval': max_interval
        }

        # Save the configuration using ConfigManager
        self.config_manager.save_config(config_data)
        QMessageBox.information(self, "Success", "Configuration saved successfully.") 

    def load_configuration(self):
        # Load configurations using ConfigManager
        self.config = self.config_manager.load_config()
        self.bizhawk_path_input.setText(self.config.get('bizhawk_path', ''))
        self.min_interval_input.setText(str(self.config.get('min_shuffle_interval', '30')))
        self.max_interval_input.setText(str(self.config.get('max_shuffle_interval', '60')))
        self.statusBar().showMessage("Configuration loaded successfully.", 5000)              

    def load_config(self):
        # Load configurations using ConfigManager
        self.config = self.config_manager.load_config()
        

    def validate_intervals(self, min_val, max_val):
        """Validate shuffle interval settings"""
        try:
            min_interval = int(min_val)
            max_interval = int(max_val)

            if min_interval <= 0 or max_interval <= 0:
                return False, "Intervals must be positive numbers."
            elif min_interval > max_interval:
                return False, "Minimum interval cannot be greater than maximum interval."

            return True, "Valid intervals."

        except ValueError:
            return False, "Intervals must be numeric."


    def create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Labels to display stats
        self.total_swaps_label = QLabel("Total Swaps: 0")
        self.total_time_label = QLabel("Total Time: 00:00:00")
        self.game_name_label = QLabel("Current Game: None")
        self.current_game_swaps_label = QLabel("Current Game Swaps: 0")
        self.current_game_time_label = QLabel("Current Game Time: 00:00:00")

        layout.addWidget(self.total_swaps_label)
        layout.addWidget(self.total_time_label)
        layout.addWidget(self.game_name_label)
        layout.addWidget(self.current_game_swaps_label)
        layout.addWidget(self.current_game_time_label)

        return tab

    def update_stats_display(self):
        if hasattr(self, 'total_swaps_label'):
            game_stats, total_swaps, total_time = self.game_manager.stats_tracker.get_stats()
            real_time_total = total_time + (time.time() - self.game_manager.stats_tracker.start_time if self.game_manager.current_game else 0)

            self.total_swaps_label.setText(f"Total Swaps: {total_swaps}")
            self.total_time_label.setText(f"Total Time: {self.format_time(real_time_total)}")

            current_game = self.game_manager.current_game
            if current_game and current_game in game_stats:
                current_game_stats = game_stats[current_game]
                self.game_name_label.setText(f"Current Game: {current_game}")
                self.current_game_swaps_label.setText(f"Current Game Swaps: {current_game_stats['swaps']}")
                self.current_game_time_label.setText(f"Current Game Time: {self.format_time(current_game_stats['time_spent'] + (time.time() - self.game_manager.stats_tracker.start_time))}")
            else:
                self.game_name_label.setText("Current Game: None")
                self.current_game_swaps_label.setText("Current Game: None | Swaps: 0")
                self.current_game_time_label.setText("Current Game: None | Time: 00:00:00")
            self.update_session_info()

    def format_time(self, seconds):
        # Method to format seconds into hh:mm:ss
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"












    def create_session_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Add a label to display session info
        self.session_info_label = QLabel("Load a session to view details")
        layout.addWidget(self.session_info_label)

        # Set up the save, load, rename, and delete session buttons
        save_session_button = QPushButton("Save Current Session As...")
        save_session_button.clicked.connect(self.save_current_session)
        load_session_button = QPushButton("Load Session")
        load_session_button.clicked.connect(self.load_selected_session)
        rename_session_button = QPushButton("Rename Selected Session")
        rename_session_button.clicked.connect(self.rename_current_session)
        delete_session_button = QPushButton("Delete Selected Session")
        delete_session_button.clicked.connect(self.delete_current_session)
        layout.addWidget(save_session_button)
        layout.addWidget(load_session_button)
        layout.addWidget(rename_session_button)
        layout.addWidget(delete_session_button)

        return tab

    def load_default_session(self):
        session_data = self.session_manager.load_session('Default Session')
        if session_data:
            self.game_manager.games = session_data['games']
            self.game_manager.stats_tracker.get_stats()
            self.game_manager.load_save_states(session_data['save_states'])
            self.current_session_name = 'Default Session'


    def create_default_session(self):
        """Creates a default session if one doesn't already exist, or loads it if it already exists"""
        if os.path.exists('sessions/Default Session.json'):
            self.load_default_session()
        else:
            self.session_manager.save_session('Default Session', self.game_manager.games, self.game_manager.stats_tracker.get_stats(), {}, 'sessions/Default Session.json')
            self.current_session_name = 'Default Session'
            self.update_session_info()
        self.save_last_session(self.current_session_name)       
            
            
    def load_selected_session(self):
        sessions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")
        file_dialog = QFileDialog(directory=sessions_dir)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("JSON files (*.json)")
        file_dialog.setDefaultSuffix("*.json")
        if file_dialog.exec_():
            session_path = file_dialog.selectedFiles()[0]
            try:
                with open(session_path, 'r') as f:
                    session_data = json.load(f)
                    # Set session name from the content of the session file
                    self.current_session_name = session_data['name']
                    self.game_manager.load_games(session_data['games'])
                    self.game_manager.load_save_states(session_data['save_states'])
                    self.refresh_ui()
                    self.statusBar().showMessage(f"Session '{self.current_session_name}' has been loaded successfully.", 5000)
                    self.save_last_session(self.current_session_name)
            except:
                QMessageBox.warning(self, "Load Error", "Failed to load the selected session. It may be corrupted or missing.")
    def save_current_session(self):
        """Save the current session to a JSON file"""
        file_name = f"{self.current_session_name}.json"
        sessions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")

        file_dialog = QFileDialog()
        file_dialog.setDirectory(sessions_dir)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.selectFile(file_name)
        file_dialog.setDefaultSuffix("*.json")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            data = {'name': self.current_session_name, 'games': self.game_manager.games, 'stats': self.game_manager.stats_tracker.get_stats(), 'save_states': self.game_manager.save_states}
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            self.statusBar().showMessage(f"Session saved successfully to {file_path}", 5000)
            self.save_last_session(self.current_session_name)
            
    def delete_current_session(self):
        """Delete the currently loaded session"""
        if self.current_session_name:
            result = QMessageBox.question(self, "Delete Session", f"Are you sure you want to delete the '{self.current_session_name}' session?", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                session_file = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")
                if self.session_manager.delete_session(self.current_session_name):
                    self.current_session_name = None
                    self.load_default_session()
                    self.statusBar().showMessage(f"Session '{self.current_session_name}' has been deleted successfully and default session has been loaded.", 5000)
                    self.refresh_ui
                    self.save_last_session('Default Session')
                else:
                    QMessageBox.warning(self, "Delete Error", f"Failed to delete the '{self.current_session_name}' session.")
        else:
            self.statusBar().showMessage("No session selected for deletion.", 5000)
            
    def rename_current_session(self):
        """Rename the currently selected session"""
        if self.current_session_name:
            new_name, ok = QInputDialog.getText(self, "Rename Session", "Enter new name for the session:", text=self.current_session_name)
            if ok and new_name:
                if self.session_manager.rename_session(self.current_session_name, new_name):
                    self.current_session_name = new_name
                    self.statusBar().showMessage(f"Session renamed to '{new_name}'.", 5000)
                    self.refresh_ui()
                    self.save_last_session(new_name)
                else:
                    QMessageBox.warning(self, "Rename Error", f"Failed to rename the session to '{new_name}'.")
        else:
            self.statusBar().showMessage("No session selected for renaming.", 5000)
            

    def get_session_path(self, session_name):
        return os.path.join(self.session_manager.directory, session_name)
            
    def update_session_info(self):
        if not self.current_session_name:
            self.session_info_label.setText("No session available.")
            return

        session_file = self.get_session_path(f"{self.current_session_name}.json")
        if not os.path.exists(session_file):
            self.session_info_label.setText(f"Session file for '{self.current_session_name}' does not exist.")
            return

        try:
            with open(session_file, 'r') as file:
                session_data = json.load(file)
                session_name = session_data['name']
                game_count = len(session_data['games'])
                completed_game_count = sum(1 for game in session_data['games'].values() if game['completed'])
                game_stats, total_swaps, total_time = session_data['stats']

                # Formatting total_time to HH:MM:SS 
                formatted_total_time = self.stat_tracker.format_time(total_time)

                # Add completed_game_count to the label text
                self.session_info_label.setText(f"Session: {session_name}\n" +
                                                f"Games: {game_count}\n" +
                                                f"Completed: {completed_game_count}\n" +  # <-- New line for completed games
                                                f"Swaps: {total_swaps}\n" +
                                                f"Time: {formatted_total_time}")
        except FileNotFoundError:
            # This exception handler should never be reached due to the earlier check,
            # but it's kept as a safeguard.
            self.session_info_label.setText(f"Session: {self.current_session_name}\n" +
                                            f"Games: 0\n" +
                                            f"Swaps: 0\n" +
                                            f"Time: 00:00:00\n" +
                                            "Session file does not exist.")
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Load Error", "Failed to load the session file. It may be corrupted.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading the session: {e}")
            self.statusBar().showMessage("An unexpected error occurred while loading the session.", 5000)


    def update_and_save_session(self):
        # Gather the updated stats from the StatsTracker
        current_game_stats, total_swaps, total_shuffling_time = self.game_manager.stats_tracker.get_stats()

        # Update the session data with the current stats
        session_data = {
            'name': self.current_session_name,
            'games': self.game_manager.games,
            'stats': [
                current_game_stats,
                total_swaps,
                total_shuffling_time
            ],
            'save_states': self.game_manager.save_states
        }

        # Construct the file path for the session file using the directory attribute and session name
        session_file_path = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")

        # Use the SessionManager to save the session to disk
        self.session_manager.save_session(self.current_session_name, session_data['games'], 
                                        session_data['stats'], session_data['save_states'], session_file_path)
        
        
    def refresh_ui(self):
        self.update_session_info()
        self.refresh_game_list()
        
    def save_last_session(self, session_name):
        config_path = self.config_manager.get_config_path()  # Assuming this function correctly retrieves config file path
        try:
            with open(config_path, 'r+') as file:
                config_data = json.load(file)
                config_data['last_session'] = session_name
                file.seek(0)
                json.dump(config_data, file, indent=4)
                file.truncate()
        except Exception as e:
            logging.error(f"Error saving last session: {e}")       
            
    def load_last_session(self):
        last_session_name = self.config.get('last_session')
        if last_session_name:
            try:
                session_data = self.session_manager.load_session(last_session_name)
                if session_data:
                    self.current_session_name = last_session_name
                    self.game_manager.load_games(session_data['games'])
                    self.game_manager.load_save_states(session_data['save_states'])
                    self.refresh_ui()
                else:
                    logging.error(f"Session data for '{last_session_name}' could not be loaded.")
                    self.create_default_session()
            except Exception as e:
                logging.error(f"An unexpected error occurred while loading the session: {e}")
                self.create_default_session()
        else:
            self.create_default_session()           