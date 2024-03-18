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
        self.config = self.config_manager.load_config()              
        self.current_session_name = None  # Initialize with None or a default session name
        self.create_default_session()  # Create a default session if one doesn't exist
        # Initialize tabs
        self.init_tabs()
        self.init_ui()  
        self.refresh_game_list()
        self.update_session_info()
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
        layout.addWidget(self.game_list)

        self.game_list.itemDoubleClicked.connect(self.handle_double_click)

        return tab

    def show_game_context_menu(self, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove Selected Game")
        complete_action = menu.addAction("Mark as Completed")
        rename_action = menu.addAction("Rename Selected Game")
        goals_action = menu.addAction("Set Goals for Selected Game")

        action = menu.exec_(self.game_list.mapToGlobal(pos))
        if action == remove_action:
            self.remove_selected_game()
        elif action == complete_action:
            self.mark_game_as_completed()
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
                goals = self.game_manager.games[game_path]['goals']
                details += f"\nGoals: {goals if goals else 'No goals set'}"
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
            self.refresh_game_list()
            self.update_session_info()
            

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
                self.refresh_game_list()
                self.update_session_info()

    def remove_selected_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected for removal")
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.remove_game(game_path)
        self.refresh_game_list()

    def mark_game_as_completed(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected to mark as completed")
            return

        for item in selected_items:
            game_path = self.find_game_path_by_name(item.text())
            if game_path:
                self.game_manager.mark_game_as_completed(game_path)
        self.refresh_game_list()
            
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
        # Skip shuffling if there are no games or shuffling is disabled 
        if not self.is_shuffling or not self.game_manager.games:
            return
        # Remove current game from available games
        available_games = list(self.game_manager.games.keys())  
        if self.current_game_path and len(available_games) > 1:
            available_games.remove(self.current_game_path)

        try:
            # Select a random game and switch to it
            next_game_path = random.choice(available_games)  
            next_game_name = self.game_manager.games[next_game_path]['name']
            self.game_manager.switch_game(next_game_name)

            # Save and load game state
            if self.current_game_path:
                self.save_game_state(self.current_game_path)
                self.session_manager.save_session(self.current_session_name, self.game_manager.games, self.game_manager.stats_tracker.get_stats(), self.game_manager.save_states, self.get_session_path(self.current_session_name) + '.json')
            self.load_game(next_game_path)
            self.load_game_state(next_game_path)
            self.session_manager.save_session(self.current_session_name, self.game_manager.games, self.game_manager.stats_tracker.get_stats(), self.game_manager.save_states, self.get_session_path(self.current_session_name) + '.json')
            self.update_session_info()

        except Exception as e:
            logging.error("Error shuffling games: " + str(e))

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
        Python_Client.save_state(state_path)  # Save the game state

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
        save_session_button = QPushButton("Save Current Session")
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
                    self.current_session_name = os.path.basename(session_path)
                    self.game_manager.load_games(session_data['games'])
                    stats = self.stat_tracker.get_stats()
                    self.game_manager.load_save_states(session_data['save_states'])
                    self.refresh_game_list()
                    self.statusBar().showMessage(f"Session '{self.current_session_name}' has been loaded successfully.", 5000)
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
            
    def delete_current_session(self):
        """Delete the currently loaded session"""
        if self.current_session_name:
            result = QMessageBox.question(self, "Delete Session", f"Are you sure you want to delete the '{self.current_session_name}' session?", QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                session_file = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")
                if self.session_manager.delete_session(self.current_session_name):
                    self.current_session_name = None
                    self.statusBar().showMessage(f"The '{self.current_session_name}' session has been deleted.", 5000)
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
                else:
                    QMessageBox.warning(self, "Rename Error", f"Failed to rename the session to '{new_name}'.")
        else:
            self.statusBar().showMessage("No session selected for renaming.", 5000)

    def get_session_path(self, session_name):
        return os.path.join(self.session_manager.directory, session_name)
            
    def update_session_info(self):
        if self.current_session_name:
            session_file = os.path.join(self.session_manager.directory, f"{self.current_session_name}.json")
            try:
                if os.path.exists(session_file):
                    with open(session_file, 'r') as file:
                        session_data = json.load(file)
                        game_count = len(session_data['games'])
                        stats = session_data['stats']
                        total_swaps = stats[1]
                        total_time = stats[2]
                        self.session_info_label.setText(f"Session: {self.current_session_name}\n" +
                                                        f"Games: {game_count}\n" +
                                                        f"Swaps: {total_swaps}\n" +
                                                        f"Time: {self.format_time(total_time)}")
                else:
                    raise FileNotFoundError
            except FileNotFoundError:
                self.session_info_label.setText(f"Session: {self.current_session_name}\n" +
                                                f"Games: 0\n" +
                                                f"Swaps: 0\n" +
                                                f"Time: 00:00:00\n" +
                                                "Session file does not exist.")
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Load Error", "Failed to load the session file. It may be corrupted.")
            except:
                self.statusBar().showMessage("An unexpected error occurred while loading the session.", 5000)

        else:
            self.session_info_label.setText("Load a session to view details")


