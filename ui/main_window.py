from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QInputDialog, QLabel, QLineEdit, QGroupBox
from PySide6.QtWidgets import QPushButton, QListWidget, QFileDialog, QLineEdit, QMenu, QComboBox, QHBoxLayout, QFormLayout
from PySide6.QtCore import Qt, QTimer
from game_manager import GameManager
from config import ConfigManager
from session_manager import SessionManager
from stat_tracker import StatsTracker
from ui.style import Style
import Python_Client

import os, random, subprocess, time, json, sys, logging
import psutil, shutil, keyboard

SUPPORTED_EXTENSIONS = (
    '.nes', '.snes', '.gbc', '.gba', '.md', '.nds',
    '.pce', '.sgx', '.sms', '.gg', '.sg', '.a26',  # Add more extensions as needed
)

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
        self.stats_update_timer = QTimer(self)
        self.stats_update_timer.timeout.connect(self.update_stats_files)
        self.stats_update_timer.start(1000)  # Timer set to trigger every 1000 milliseconds (1 second)        
        
     
    def init_ui(self):
        Style.set_dark_style(self)
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
    def apply_selected_style(self):
        selected_style = self.style_selector.currentText().lower()
        if selected_style == 'dark':
            Style.set_dark_style(self)
        elif selected_style == 'light':
            Style.set_light_style(self)
        # Save the selected style to the configuration
        self.config['style'] = selected_style
        self.config_manager.save_config(self.config)
                      

    def init_tabs(self):
        # Create tabs for different functionalities
        self.tab_widget.addTab(self.create_game_management_tab(), "Game Management")
        self.tab_widget.addTab(self.create_session_management_tab(), "Session Management")
        self.tab_widget.addTab(self.create_shuffle_management_tab(), "Shuffle Management")
        self.tab_widget.addTab(self.create_configuration_tab(), "Configuration")
        self.tab_widget.addTab(self.create_stats_tab(), "Stats")
        self.tab_widget.addTab(self.create_twitch_integration_tab(), "Twitch")





    def create_game_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
    
        # Search input with label
        search_group = QGroupBox("Search Games")
        search_layout = QHBoxLayout(search_group)
        search_layout.setSpacing(5)
        search_layout.setContentsMargins(10, 20, 10, 10)  # Adjust the top margin as necessary
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search games...")
        self.search_input.textChanged.connect(self.filter_games)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)
    
        # Buttons for managing games
        manage_group = QGroupBox("Manage Games")
        manage_layout = QHBoxLayout(manage_group)
        manage_layout.setSpacing(5)
        manage_layout.setContentsMargins(10, 20, 10, 10)  # Adjust the top margin as necessary
        add_games_button = QPushButton("Add Games")
        add_games_button.clicked.connect(self.add_games)
        add_directory_button = QPushButton("Add Games from Directory")
        add_directory_button.clicked.connect(self.add_games_from_directory)
        manage_layout.addWidget(add_games_button)
        manage_layout.addWidget(add_directory_button)
        layout.addWidget(manage_group)
    
    # New group box for games list and game details
        games_info_group_box = QGroupBox("Games")
        games_info_layout = QVBoxLayout(games_info_group_box)

        # Game list
        self.game_list = QListWidget()
        self.game_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_list.customContextMenuRequested.connect(self.show_game_context_menu)
        self.game_list.itemSelectionChanged.connect(self.display_game_details)
        games_info_layout.addWidget(self.game_list)

        # Game details label
        self.game_details_label = QLabel("Select a game to view details")
        games_info_layout.addWidget(self.game_details_label)

        # Add the new group box to the main layout
        layout.addWidget(games_info_group_box)

        layout.addStretch()  # Push everything up

        return tab


    def setup_hotkey_listener(self):
        hotkey = self.config.get('toggle_complete_hotkey', 'ctrl+t')
        keyboard.add_hotkey(hotkey, self.toggle_current_game_complete)

    def toggle_current_game_complete(self):
        # Logic to toggle the 'completed' status of the current game
        if self.current_game_path:
            if self.game_manager.games[self.current_game_path].get('completed'):
                self.game_manager.mark_game_as_not_completed(self.current_game_path)
            else:
                self.game_manager.mark_game_as_completed(self.current_game_path)
            self.refresh_game_list()  # Update the UI

    def show_game_context_menu(self, pos):
        menu = QMenu(self)
        selected_items = self.game_list.selectedItems()
        
        if not selected_items:  # Clicked on an empty space
            add_games_action = menu.addAction("Add Games")
            add_directory_action = menu.addAction("Add Games from Directory")
        else:  # Clicked on a game
            remove_action = menu.addAction("Remove Selected Game")
            complete_action = None  # Initialize complete_action to None
            game_name = selected_items[0].text().split(" - ")[0]
            game_path = self.find_game_path_by_name(game_name)
            if game_path and self.game_manager.games[game_path].get('completed'):
                complete_action = menu.addAction("Unmark as Completed")
            else:
                complete_action = menu.addAction("Mark as Completed")
            rename_action = menu.addAction("Rename Selected Game")
            goals_action = menu.addAction("Set Goals for Selected Game")
    
        action = menu.exec_(self.game_list.mapToGlobal(pos))
    
        if not selected_items:  # Actions for clicking on an empty space
            if action == add_games_action:
                self.add_games()
            elif action == add_directory_action:
                self.add_games_from_directory()
        else:  # Actions for clicking on a game
            if action == remove_action:
                self.remove_selected_game()
            elif action and complete_action and action == complete_action:
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
        search_text = self.search_input.text().lower()  # Corrected from self.search_bar to self.search_input
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
        try:
            app_root = os.path.dirname(sys.modules['__main__'].__file__)
            games_dir = os.path.join(app_root, "games")
            if not os.path.exists(games_dir):
                os.makedirs(games_dir)
        
            file_names, _ = QFileDialog.getOpenFileNames(self, "Select Games", games_dir, 
                                                         "Game Files (*.nes *.snes *.gbc *.gba *.md *.nds)")
            added_any = False
            for file_name in file_names:
                # Check if the game file has a supported extension
                if any(file_name.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    normalized_path = os.path.abspath(file_name)
                if normalized_path not in self.game_manager.games:
                    # Add the game to the game manager
                    self.game_manager.add_game(normalized_path)
                    print("Added game:", normalized_path)
                    added_any = True
                else:
                    logging.info(f"Game {os.path.basename(file_name)} is already in the list.")

            if added_any:
                # Refresh the UI and update the session after adding games
                self.refresh_ui()
                self.update_and_save_session()
        except Exception as e:
            logging.error(f"An unexpected error occurred while adding games: {e}")

            
            

    def add_games_from_directory(self):
        try:
            app_root = os.path.dirname(sys.modules['__main__'].__file__)
            games_dir = os.path.join(app_root, "games")
            if not os.path.exists(games_dir):
                os.makedirs(games_dir)
        
            directory = QFileDialog.getExistingDirectory(self, "Select Directory", games_dir, 
                                                          QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
            if directory:
                logging.info(f"Selected directory: {directory}")
                added_any = False
                # Get a list of all files in the selected directory
                for file_name in os.listdir(directory):
                    file_path = os.path.join(directory, file_name)
                    if os.path.isfile(file_path):
                        # Check if the game file has a supported extension
                        if any(file_path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                            normalized_path = os.path.abspath(file_path)
                            # Check if the game already exists in the list
                            if normalized_path not in self.game_manager.games:
                                # Add the game to the game manager
                                self.game_manager.add_game(normalized_path)
                                added_any = True
                            else:
                                logging.info(f"Game {os.path.basename(file_path)} is already in the list.")

                if added_any:
                    # Refresh the UI and update the session after adding games
                    self.refresh_ui()
                    self.update_and_save_session()
        except Exception as e:
            logging.error(f"An unexpected error occurred while adding games from directory: {e}")

                

    def remove_selected_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.remove_game(game_path)

        self.refresh_ui()
        self.update_and_save_session()  
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
        self.update_and_save_session()  
        
        
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
        old_name = item.text()  # This assumes that item.text() is the old game name
        path = self.find_game_path_by_name(old_name)
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
            QMessageBox.information(self, "BizHawk Running", "BizHawk is already running.")
            # Optional: Bring BizHawk window to the front if possible
            return
    
        try:
            self.execute_bizhawk_script()
        except Exception as e:
            logging.error(f"Exception launching BizHawk: {e}")
            QMessageBox.critical(self, "Launch Error", f"An error occurred while launching BizHawk: {e}")
            
    def is_bizhawk_process_running(self):
        # Check if BizHawk/EmuHawk process is running
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'EmuHawk.exe' or proc.info['name'] == 'BizHawk.exe':
                return True

        return False

    def start_shuffle(self):
        if self.is_shuffling:
            print("Shuffle is already active.")
            return

        if not self.current_session_name:
            QMessageBox.warning(self, "No Session", "No current session is set. Please load a session first.")
            return

        try:
            session_data = self.session_manager.load_session(self.current_session_name)
            if session_data:
                # Make sure session_data has all the required fields
                if not all(key in session_data for key in ['games', 'stats', 'save_states']):
                    raise ValueError("Session data is missing required fields")
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
        except Exception as e:
            logging.error(f"An unexpected error occurred while starting shuffle: {e}")
            QMessageBox.critical(self, "Shuffle Error", f"An error occurred while starting shuffle: {e}")

    def determine_shuffle_interval(self):
        # Define default values for shuffle intervals
        default_min_interval = 30
        default_max_interval = 60
    
        # Get shuffle intervals from the configuration, with defaults if not set
        min_interval = self.config_manager.config.get('min_shuffle_interval', default_min_interval)
        max_interval = self.config_manager.config.get('max_shuffle_interval', default_max_interval)
    
        # Ensure min_interval is not greater than max_interval
        if min_interval > max_interval:
            logging.warning("Minimum interval is greater than maximum interval. Using default values.")
            min_interval, max_interval = default_min_interval, default_max_interval
    
        # Return a random interval within the specified range
        return random.randint(min_interval, max_interval) * 1000

    def pause_shuffle(self):
        self.is_shuffling = False
        # Additional logic to handle pause state

    def resume_shuffle(self):
        if not self.is_shuffling and self.game_manager.games:
            self.is_shuffling = True
            self.shuffle_games()


    def shuffle_games(self):
        # Check if shuffling is disabled
        if not self.is_shuffling:
            logging.info("Shuffling is disabled.")
            return

        # Check if the game list is empty
        if not self.game_manager.games:
            logging.warning("No games available to shuffle.")
            QMessageBox.warning(self, "Shuffle Error", "No games available to shuffle.")
            self.is_shuffling = False  # Stop shuffling
            return

        # Remove current game from available games
        available_games = list(self.game_manager.games.keys())
        if self.current_game_path in available_games:
            available_games.remove(self.current_game_path)

        # If only one game is available, or all games are marked as completed, shuffling is not possible
        if len(available_games) <= 1 or all(self.game_manager.games[game]['completed'] for game in available_games):
            logging.info("Cannot shuffle: Only one game available or all games are completed.")
            if all(self.game_manager.games[game]['completed'] for game in available_games):
                # If all games are completed, show a congratulatory message
                QMessageBox.information(self, "Congratulations!", "Amazing! You have completed all the games.")
            else:
                QMessageBox.information(self, "Shuffle Info", "Cannot shuffle: Only one game available.")
            self.is_shuffling = False  # Stop shuffling
            return

        # Shuffle the games
        try:
            # Select a random game and switch to it
            next_game_path = random.choice(available_games)
            next_game_name = self.game_manager.games[next_game_path]['name']
            self.game_manager.switch_game(next_game_name)

            # Save and load game state
            if self.current_game_path:
                self.save_game_state(self.current_game_path)
                self.update_and_save_session()
            self.load_game(next_game_path)
            self.load_game_state(next_game_path)
            self.update_and_save_session()
            self.update_session_info()

        except Exception as e:
            logging.error(f"Error switching to the next game: {e}")
            self.statusBar().showMessage(f"An error occurred while switching games: {e}")
            
                   

        # Update current game path
        self.current_game_path = next_game_path

        # Schedule next shuffle
        min_interval, max_interval = self.config.get('min_shuffle_interval', 30), self.config.get('max_shuffle_interval', 60)
        shuffle_interval = random.randint(min_interval, max_interval)
        logging.info("Scheduling next shuffle in %d seconds", shuffle_interval)
        QTimer.singleShot(shuffle_interval * 1000, self.shuffle_games)

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

    def load_game(self, game_path):
        print(f"Loading game: {game_path}")  # Debugging line
        if not game_path:
            return
        # Call to Python client script to load the game
        Python_Client.load_rom(game_path)

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
            self.save_game_state(game_path)  # Save the state if it doesn't exist

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
        session_dir = self.get_session_path(self.current_session_name)
        save_states_dir = os.path.join(session_dir, 'savestates')
        game_id = os.path.splitext(os.path.basename(game_file))[0]
        state_file = f"{game_id}.state"
        return os.path.join(save_states_dir, state_file)
    
    


    def create_configuration_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop) 
    
       
        style_group_box = QGroupBox("Appearance")
        style_group_box.setMinimumHeight(100)  
        style_layout = QFormLayout(style_group_box)
        style_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        style_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        style_layout.setLabelAlignment(Qt.AlignLeft)
        style_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        style_layout.setVerticalSpacing(20)
        self.style_selector = QComboBox()
        self.style_selector.addItems(["Dark", "Light"])
        current_style = self.config.get('style', 'dark')
        self.style_selector.setCurrentText(current_style.capitalize())
        self.style_selector.currentIndexChanged.connect(self.apply_selected_style)
        style_layout.addRow(QLabel("Select UI Style:"), self.style_selector)
        main_layout.addWidget(style_group_box)
    
        
        bizhawk_group_box = QGroupBox("BizHawk Settings")
        bizhawk_group_box.setMinimumHeight(100)  
        bizhawk_layout = QFormLayout(bizhawk_group_box)
        bizhawk_layout.setVerticalSpacing(20)
        bizhawk_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.bizhawk_path_input = QLineEdit(self.config.get('bizhawk_path', ''))
        self.bizhawk_path_input.setPlaceholderText("Path to BizHawk executable")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_bizhawk_path)
        bizhawk_layout.addRow(QLabel("BizHawk Path:"), self.bizhawk_path_input)
        bizhawk_layout.addWidget(browse_button)
        main_layout.addWidget(bizhawk_group_box)
    
        
        shuffle_interval_group_box = QGroupBox("Shuffle Intervals")
        shuffle_interval_group_box.setMinimumHeight(100)  
        shuffle_interval_layout = QFormLayout(shuffle_interval_group_box)
        shuffle_interval_layout.setVerticalSpacing(20)
        self.min_interval_input = QLineEdit(str(self.config.get('min_shuffle_interval', '30')))
        self.max_interval_input = QLineEdit(str(self.config.get('max_shuffle_interval', '60')))
        shuffle_interval_layout.addRow(QLabel("Minimum Interval (seconds):"), self.min_interval_input)
        shuffle_interval_layout.addRow(QLabel("Maximum Interval (seconds):"), self.max_interval_input)
        main_layout.addWidget(shuffle_interval_group_box)
         
        hotkey_group_box = QGroupBox("Hotkeys")
        hotkey_layout = QFormLayout(hotkey_group_box)
        hotkey_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.toggle_complete_hotkey_input = QLineEdit(self.config.get('toggle_complete_hotkey', 'Ctrl+T'))
        self.toggle_complete_hotkey_input.setPlaceholderText("Enter hotkey (e.g., Ctrl+T)")
        hotkey_layout.addRow(QLabel("Toggle Complete Hotkey:"), self.toggle_complete_hotkey_input)
        save_hotkey_button = QPushButton("Save Hotkey")
        save_hotkey_button.clicked.connect(self.save_hotkey_configuration)
        hotkey_layout.addWidget(save_hotkey_button)
        main_layout.addWidget(hotkey_group_box)
    
        
        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)
        main_layout.addWidget(save_config_button)
    
        main_layout.addStretch() 
    
        return tab


    def browse_bizhawk_path(self):
        path = QFileDialog.getOpenFileName(self, "Select BizHawk Executable", "", "Executable Files (*.exe)")[0]
        if path:
            self.bizhawk_path_input.setText(path)


    def save_hotkey_configuration(self):
        hotkey = self.toggle_complete_hotkey_input.text()
        # Validate the hotkey format here if necessary
        # ...
        self.config['toggle_complete_hotkey'] = hotkey
        self.config_manager.save_config(self.config)
        self.setup_hotkey_listener()  # Re-setup the hotkey listener with the new hotkey    

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

    def update_stats_files(self):
        # Make sure there is a session to update
        if not self.current_session_name:
            return
        self.current_game_name = self.game_manager.current_game
        session_folder = self.get_session_path(self.current_session_name)
        self.game_manager.stats_tracker.write_individual_stats_to_files(session_folder, self.current_game_name)










    def create_session_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
            
        create_new_session_button = QPushButton("Create New Session")
        create_new_session_button.clicked.connect(self.create_new_session)        
    
        # Add a label to display session info
        self.session_info_label = QLabel("Load a session to view details")
        layout.addWidget(self.session_info_label)
    
        # Set up the save, load, rename, and delete session buttons
        save_session_button = QPushButton("Save Current Session As...")
        save_session_button.clicked.connect(self.save_current_session_as_new)  # Assuming save_current_session_as_new is implemented
        
        # Session dropdown for selecting sessions
        self.session_dropdown = QComboBox(self)
        self.populate_session_dropdown()
        self.session_dropdown.currentIndexChanged.connect(self.load_session_from_dropdown)        
        
        # Add session dropdown to layout
        layout.addWidget(self.session_dropdown)  # This line adds the dropdown to the layout
        
        # Other session management buttons
        rename_session_button = QPushButton("Rename Selected Session")
        rename_session_button.clicked.connect(self.rename_current_session)
        delete_session_button = QPushButton("Delete Selected Session")
        delete_session_button.clicked.connect(self.delete_current_session)
        
        # Add buttons to layout
        layout.addWidget(create_new_session_button)
        layout.addWidget(save_session_button)
        layout.addWidget(rename_session_button)
        layout.addWidget(delete_session_button)
    
        # Set the layout on the tab
        tab.setLayout(layout)
    
        return tab

    def load_default_session(self):
        session_data = self.session_manager.load_session('Default Session')
        if session_data:
            self.game_manager.games = session_data['games']
            self.game_manager.stats_tracker.get_stats()
            self.game_manager.load_save_states(session_data['save_states'])
            self.current_session_name = 'Default Session'

    def populate_session_dropdown(self):
        self.session_dropdown.clear()
        available_sessions = self.get_available_sessions()
        self.session_dropdown.addItems(available_sessions)


    def get_available_sessions(self):
        sessions_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")
        try:
            return [name for name in os.listdir(sessions_dir) if os.path.isdir(os.path.join(sessions_dir, name))]
        except FileNotFoundError:
            logging.error("Sessions directory not found.")
            return []
    
    def load_session_from_dropdown(self):
        selected_session_index = self.session_dropdown.currentIndex()
        selected_session_name = self.session_dropdown.itemText(selected_session_index)
        if selected_session_name:
            self.load_session(selected_session_name)
        
    def load_session(self, session_name):
        session_folder = self.get_session_path(session_name)
        session_file = os.path.join(session_folder, 'session.json')
        try:
            with open(session_file, 'r') as file:
                session_data = json.load(file)
                self.current_session_name = session_data['name']
                self.game_manager.load_games(session_data['games'])
                self.game_manager.load_save_states(session_data.get('save_states', {}))
                self.refresh_ui()
                self.statusBar().showMessage(f"Session '{self.current_session_name}' has been loaded successfully.", 5000)
                self.save_last_session(self.current_session_name)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load the session '{session_name}'. It may be corrupted or missing. Error: {e}")            

    def create_default_session(self):
        """Creates a default session if one doesn't already exist, or loads it if it already exists"""
        default_session_path = self.get_session_path('Default Session')
        default_session_file = os.path.join(default_session_path, 'session.json')
    
        if os.path.exists(default_session_file):
            self.load_default_session()
        else:
            os.makedirs(default_session_path, exist_ok=True)  # Ensure the session folder exists
            # Initialize session data with an empty structure
            session_data = {
                'name': 'Default Session',
                'games': {},  # Use an empty dictionary for games
                'stats': [],  # Use an empty list for stats
                'save_states': {}  # Use an empty dictionary for save states
            }
            with open(default_session_file, 'w') as f:
                json.dump(session_data, f, indent=4)
            self.current_session_name = 'Default Session'
            self.update_session_info()  # Assuming update_session_info is implemented to refresh UI
        self.save_last_session(self.current_session_name)      
            
    def create_session_dropdown(self):
        self.session_dropdown = QComboBox()
        self.session_dropdown.addItems(self.get_available_sessions())
        self.session_dropdown.currentIndexChanged.connect(self.load_session_from_dropdown)     
        
    def create_new_session(self):
        new_session_name, ok = QInputDialog.getText(self, 'Create New Session', 'Enter new session name:')
        if ok and new_session_name:
            new_session_path = self.get_session_path(new_session_name)
            if os.path.exists(new_session_path):
                QMessageBox.warning(self, "Session Creation Error", f"The session '{new_session_name}' already exists.")
                return
    
            os.makedirs(new_session_path, exist_ok=True)
            save_states_path = os.path.join(new_session_path, 'savestates')
            os.makedirs(save_states_path, exist_ok=True)
    
            session_file_path = os.path.join(new_session_path, 'session.json')
            session_data = {
                'name': new_session_name,
                'games': {},
                'stats': {},
                'save_states': {}
            }
    
            with open(session_file_path, 'w') as f:
                json.dump(session_data, f, indent=4)
    
            self.current_session_name = new_session_name
            self.refresh_ui()
            self.populate_session_dropdown()
            self.session_dropdown.setCurrentText(new_session_name)
            QMessageBox.information(self, "Session Created", f"Session '{new_session_name}' has been created successfully.")
                
    def save_current_session(self):
        if not self.current_session_name:
            QMessageBox.warning(self, "Save Error", "No session is currently loaded.")
            return
    
        session_folder = self.get_session_path(self.current_session_name)
        session_file = os.path.join(session_folder, 'session.json')
    
        # Gather the current session data
        session_data = {
            'name': self.current_session_name,
            'games': self.game_manager.get_current_games(),
            'stats': self.stat_tracker.get_current_stats(),
            'save_states': self.game_manager.get_current_save_states()
        }
    
        # Save the session data to 'session.json'
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=4)  
        self.statusBar().showMessage(f"Session '{self.current_session_name}' saved successfully.", 5000)
            
    def delete_current_session(self):
        """Delete the currently loaded session"""
        if self.current_session_name:
            result = QMessageBox.question(self, "Delete Session", f"Are you sure you want to delete the '{self.current_session_name}' session?", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                # Check if this is the last session available
                available_sessions = self.get_available_sessions()  # Make sure this method returns a list of session names
                is_last_session = len(available_sessions) == 1 and self.current_session_name in available_sessions
    
                if self.session_manager.delete_session(self.current_session_name):
                    self.current_session_name = None
                    self.statusBar().showMessage("Session has been deleted successfully.", 5000)
                    self.populate_session_dropdown()
    
                    if is_last_session:
                        # If it was the last session, create a default session
                        self.create_default_session()
                        self.populate_session_dropdown()
                        self.session_dropdown.setCurrentText('Default Session')
                        self.load_session('Default Session')
                    else:
                        # Load another session if available
                        self.load_session(available_sessions[0])
    
                else:
                    QMessageBox.warning(self, "Delete Error", f"Failed to delete the '{self.current_session_name}' session.")
        else:
            self.statusBar().showMessage("No session selected for deletion.", 5000)
            
    def rename_current_session(self):
        """Rename the currently selected session"""
        try:
            if self.current_session_name:
                new_name, ok = QInputDialog.getText(self, "Rename Session", "Enter new name for the session:", text=self.current_session_name)
                if ok and new_name:
                    if self.session_manager.rename_session(self.current_session_name, new_name):
                        self.current_session_name = new_name
                        self.statusBar().showMessage(f"Session renamed to '{new_name}'.", 5000)
                        self.refresh_ui()
                        self.save_last_session(new_name)
                        self.populate_session_dropdown()
                        self.load_session_from_dropdown(new_name)
                    else:
                        QMessageBox.warning(self, "Rename Error", f"Failed to rename the session to '{new_name}'.")
            else:
                self.statusBar().showMessage("No session selected for renaming.", 5000)
        except PermissionError as e:
            logging.exception("Permission denied while renaming session folder. Make sure the folder is not open and you have proper permissions.")
            return False
        except OSError as e:
            logging.exception(f"Error while renaming session folder: {e}")
            return False            

    def get_session_path(self, session_name):
        return os.path.join('sessions', session_name)  # Adjust the path as necessary
            
    def update_session_info(self):
        if not self.current_session_name:
            self.session_info_label.setText("No session available.")
            logging.debug("update_session_info called with no current session name set.")
            return

        session_data = self.session_manager.get_session_info(self.current_session_name)

        if not session_data:
            self.session_info_label.setText(f"Session file for '{self.current_session_name}' does not exist.")
            logging.debug(f"Session data for '{self.current_session_name}' could not be found.")
            return

        try:
            session_name = session_data['name']
            games = session_data['games']
            game_count = len(games)
            logging.debug(f"Session '{session_name}' has {game_count} games.")

            # Corrected line: Use games.values() to iterate over dictionary values
            completed_game_count = sum(1 for game in games.values() if game.get('completed', False))
            logging.debug(f"Session '{session_name}' has {completed_game_count} completed games.")
    
            # Check if 'stats' has the expected three elements, otherwise use default values
            if 'stats' in session_data and len(session_data['stats']) == 3:
                game_stats, total_swaps, total_time = session_data['stats']
            else:
                game_stats = {}  # Default empty dictionary for game_stats
                total_swaps = 0  # Default zero for total_swaps
                total_time = 0   # Default zero for total_time
                logging.debug(f"Session '{session_name}' stats are missing or incomplete. Using default values.")
    
            # Formatting total_time to HH:MM:SS using a method assumed to be defined elsewhere in MainWindow
            formatted_total_time = self.stat_tracker.format_time(total_time)
    
            self.session_info_label.setText(f"Session: {session_name}\n" +
                                            f"Games: {game_count}\n" +
                                            f"Completed: {completed_game_count}\n" +
                                            f"Swaps: {total_swaps}\n" +
                                            f"Time: {formatted_total_time}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while updating the session info: {e}")
            self.session_info_label.setText("An error occurred while loading session details.")



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

        session_folder = self.get_session_path(self.current_session_name)
        os.makedirs(session_folder, exist_ok=True)  # Ensure the session folder exists
        session_file_path = os.path.join(session_folder, 'session.json')

        # Use the SessionManager to save the session to disk
        self.session_manager.save_session(self.current_session_name, session_data['games'], 
                                        session_data['stats'], session_data['save_states'], session_file_path)
        self.save_last_session(self.current_session_name)
        
        
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
        # Attempt to load the last session if its name exists in the config
        last_session_name = self.config.get('last_session')
        print(f"Debug: Last session name from config is '{last_session_name}'")  # Debug line
    
        if last_session_name:
            # Check if the session data can be loaded
            session_data = self.session_manager.load_session(last_session_name)
            if session_data:
                print("Debug: Last session data loaded successfully")  # Debug line
                self.load_session(last_session_name)
            else:
                print("Debug: Last session data could not be loaded, loading default session")  # Debug line
                self.create_default_session()
                self.load_session('Default Session')
        else:
            print("Debug: No last session name in config, loading default session")  # Debug line
            self.create_default_session()
            self.load_session('Default Session')
    
        # Ensure the dropdown is reflecting the current session
        self.populate_session_dropdown()
        self.session_dropdown.setCurrentText(last_session_name)        
            
            
    def save_current_session_as_new(self):
        new_session_name, ok = QInputDialog.getText(self, 'Save Current Session As', 'Enter new session name:')
        if ok and new_session_name:
            new_session_path = self.get_session_path(new_session_name)
    
            if os.path.exists(new_session_path):
                QMessageBox.warning(self, "Session Creation Error", f"The session '{new_session_name}' already exists.")
                return
    
            # Copy the current session to the new session folder
            try:
                # Create new session directory and savestates subdirectory
                os.makedirs(new_session_path, exist_ok=False)
                save_states_path = os.path.join(new_session_path, 'savestates')
                os.makedirs(save_states_path, exist_ok=True)
    
                # Assuming you have a method to get the current session data
                current_session_data = self.get_current_session_data()
                
                # Adjust the 'name' in the session data
                current_session_data['name'] = new_session_name
    
                # Save the session data to 'session.json' in the new session folder
                session_file_path = os.path.join(new_session_path, 'session.json')
                with open(session_file_path, 'w') as f:
                    json.dump(current_session_data, f, indent=4)
    
                # Copy savestates from the current session to the new session
                current_save_states_path = os.path.join(self.get_session_path(self.current_session_name), 'savestates')
                for save_state_file in os.listdir(current_save_states_path):
                    shutil.copy2(os.path.join(current_save_states_path, save_state_file), save_states_path)
    
                QMessageBox.information(self, "Session Saved", f"Current session has been saved as '{new_session_name}' successfully.")
    
                # Update the UI
                self.populate_session_dropdown()
                self.session_dropdown.setCurrentText(new_session_name)
                self.current_session_name = new_session_name
                self.refresh_ui()
    
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Failed to save the current session as '{new_session_name}'. Error: {e}")
            
    def create_twitch_integration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create a label for the "Coming Soon" message
        coming_soon_label = QLabel("Coming Soon")
        layout.addWidget(coming_soon_label)
        
        tab.setLayout(layout)
        return tab
    
    
def closeEvent(self, event):
    # Save the current session as the last session
    if self.current_session_name:
        print("Saving the last session:", self.current_session_name)
        self.save_last_session(self.current_session_name)
    
    # Stop shuffling if it's currently active
    if self.is_shuffling:
        print("Stopping shuffling.")
        self.is_shuffling = False  # Set the flag to False to indicate shuffling should stop
        # Perform any other necessary cleanup related to stopping shuffling

    # Call the parent method to ensure proper closure
    print("Closing the main window.")
    super(MainWindow, self).closeEvent(event)
