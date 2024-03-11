from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QInputDialog, QLabel, QLineEdit
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit, QComboBox
from PySide6.QtCore import Qt, QTimer
from game_manager import GameManager
from config import ConfigManager
from stat_tracker import StatTracker
from session_manager import SessionManager

import os, random, subprocess

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retro Roulette")
        self.setGeometry(100, 100, 800, 600)  # Adjust size as needed

        # Create Tab Widget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.game_manager = GameManager()
        self.config_manager = ConfigManager()
        self.stat_tracker = StatTracker() 
        self.session_manager = SessionManager() 
        self.config = self.config_manager.load_config()              
        # Initialize tabs
        self.init_tabs()  
        self.refresh_game_list()    
        
     
        
                      

    def init_tabs(self):
        # Create tabs for different functionalities
        self.tab_widget.addTab(self.create_game_management_tab(), "Game Management")
        self.tab_widget.addTab(self.create_shuffle_management_tab(), "Shuffle Management")
        self.tab_widget.addTab(self.create_configuration_tab(), "Configuration")
        self.tab_widget.addTab(self.create_stats_tab(), "Stats")
        self.tab_widget.addTab(self.create_twitch_integration_tab(), "Twitch Integration")



    def create_game_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search bar for filtering games
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search games...")
        self.search_bar.textChanged.connect(self.filter_games)
        layout.addWidget(self.search_bar)

        # Button for adding multiple games
        add_games_button = QPushButton("Add Games")
        add_games_button.clicked.connect(self.add_games)
        layout.addWidget(add_games_button)

        # Button for adding games from a directory
        add_directory_button = QPushButton("Add Games from Directory")
        add_directory_button.clicked.connect(self.add_games_from_directory)
        layout.addWidget(add_directory_button)

        # List to display games
        self.game_list = QListWidget()
        layout.addWidget(self.game_list)

        # Buttons for game list management
        remove_button = QPushButton("Remove Selected Game")
        remove_button.clicked.connect(self.remove_selected_game)
        layout.addWidget(remove_button)

        mark_completed_button = QPushButton("Mark as Completed")
        mark_completed_button.clicked.connect(self.mark_game_as_completed)
        layout.addWidget(mark_completed_button)

        rename_button = QPushButton("Rename Selected Game")
        rename_button.clicked.connect(self.prompt_rename_game)
        layout.addWidget(rename_button)
        
        # Button for setting goals
        set_goals_button = QPushButton("Set Goals for Selected Game")
        set_goals_button.clicked.connect(self.prompt_set_game_goals)
        layout.addWidget(set_goals_button)
        

        # Label for displaying game details
        self.game_details_label = QLabel("Select a game to view details")
        layout.addWidget(self.game_details_label)

        # Update game list widget to connect selection change signal
        self.game_list.itemSelectionChanged.connect(self.display_game_details)

        return tab
    
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
        file_names, _ = QFileDialog.getOpenFileNames(self, "Select Games", "", 
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

    def add_games_from_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
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
        self.game_list.clear()
        for path, data in self.game_manager.games.items():
            item_text = f"{data['name']} - {'Completed' if data['completed'] else 'In Progress'}"
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
        # Path to the BizHawk executable
        bizhawk_path = "BizHawk\EmuHawk.exe"  # Update this path
        try:
            subprocess.Popen(bizhawk_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch BizHawk: {e}")

    def start_shuffle(self):
        if not self.is_shuffling:
            # Read shuffle interval configurations
            min_interval = self.config.get('min_shuffle_interval', 30)
            max_interval = self.config.get('max_shuffle_interval', 60)
            
            # Convert to milliseconds and ensure min_interval is not greater than max_interval
            self.shuffle_interval = random.randint(min(min_interval, max_interval), max(max_interval, min_interval)) * 1000
            
            self.is_shuffling = True
            self.shuffle_games()

    def determine_shuffle_interval(self):
        # Placeholder: Determine the shuffle interval based on configuration
        min_interval = self.config_manager.config.get('min_shuffle_interval', 30)
        max_interval = self.config_manager.config.get('max_shuffle_interval', 60)
        return random.randint(min_interval, max_interval) * 1000  # in milliseconds

    def pause_shuffle(self):
        self.is_shuffling = False
        # Logic to pause the game/shuffle

    def resume_shuffle(self):
        if not self.current_game_path:
            return
        self.is_shuffling = True
        # Logic to resume the game/shuffle

    def shuffle_games(self):
        if not self.is_shuffling or not self.game_manager.games:
            self.is_shuffling = False
            QMessageBox.warning(self, "Shuffle Error", "No games available to shuffle.")
            return

        game_paths = list(self.game_manager.games.keys())
        if self.current_game_path:
            game_paths.remove(self.current_game_path)  # Avoid immediate repeat

        if not game_paths:  # In case only one game is available
            game_paths.append(self.current_game_path)

        next_game_path = random.choice(game_paths)

        if self.current_game_path:
            if not self.save_game_state(self.current_game_path):
                QMessageBox.warning(self, "Save State Error", "Failed to save game state.")
                return

        if not self.load_game(next_game_path):
            QMessageBox.warning(self, "Load Game Error", "Failed to load game.")
            return

        self.current_game_path = next_game_path

        QTimer.singleShot(self.shuffle_interval, self.shuffle_games)

    def save_game_state(self, game_path):
        # Use scripting or API to save the current state
        # Placeholder for the actual implementation
        self.execute_bizhawk_script("save_state", game_path)

    def load_game(self, game_path):
        # Adjust the command as needed for your actual implementation
        command = ["E:/Coding/Retro_Roulette/BizHawk/EmuHawk.exe", "--action", "load_game", "--game", game_path]

        print(f"Attempting to load game: {game_path}")
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Example: Wait for the process to complete and capture output (stdout)
            stdout, stderr = process.communicate(timeout=15)  # Wait for 15 seconds for BizHawk to respond

            if process.returncode != 0:
                print(f"Error loading game: {stderr.decode('utf-8')}")
                return False

            # Example success check based on BizHawk's output
            if "Game loaded successfully" in stdout.decode('utf-8'):
                print("Game loaded successfully.")
                return True
            else:
                print("Game did not load successfully.")
                return False
        except subprocess.TimeoutExpired as e:
            print(f"BizHawk load game timeout: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def load_game_state(self, game_path):
        # Use scripting or API to load the saved state of the new game
        self.execute_bizhawk_script("load_state", game_path)

    def execute_bizhawk_script(self, action, game_path):
        # Example: full path to the script or modify as per your script's location
        script_path = "E:/Coding/Retro_Roulette/BizHawk/EmuHawk.exe"
        
        # Construct the command as a list
        command = [script_path, "--action", action, "--game", game_path]

        print("Executing command:", command)  # Debugging print

        try:
            subprocess.Popen(command)
        except FileNotFoundError as e:
            print(f"Error executing command: {e}")
            QMessageBox.critical(self, "Execution Error", f"Failed to execute command: {command}")




    def create_configuration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # BizHawk Path Configuration
        self.bizhawk_path_input = QLineEdit()
        self.bizhawk_path_input.setText(self.config.get('bizhawk_path', ''))
        browse_bizhawk_button = QPushButton("Browse")
        browse_bizhawk_button.clicked.connect(self.browse_bizhawk_path)
        layout.addWidget(self.bizhawk_path_input)
        layout.addWidget(browse_bizhawk_button)

        # Min Interval Input
        self.min_interval_input = QLineEdit()
        min_interval = self.config.get('min_shuffle_interval', '30')  # Default value if not set
        self.min_interval_input.setText(str(min_interval))
        layout.addWidget(self.min_interval_input)

        # Max Interval Input
        self.max_interval_input = QLineEdit()
        max_interval = self.config.get('max_shuffle_interval', '60')  # Default value if not set
        self.max_interval_input.setText(str(max_interval))
        layout.addWidget(self.max_interval_input)

        # Save Configuration Button
        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)
        layout.addWidget(save_config_button)        

        # Dropdown to select a session to load
        self.session_dropdown = QComboBox()
        self.session_dropdown.addItems(self.session_manager.get_saved_sessions())
        layout.addWidget(self.session_dropdown)

        # Load Session Button
        load_session_button = QPushButton("Load Session")
        load_session_button.clicked.connect(self.load_selected_session)
        layout.addWidget(load_session_button)

        # Save Session Button
        save_session_button = QPushButton("Save Current Session")
        save_session_button.clicked.connect(self.save_current_session)
        layout.addWidget(save_session_button)       

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

    def load_config(self):
        # Load configurations using ConfigManager
        self.config = self.config_manager.load_config()
        
    def load_selected_session(self):
        selected_session = self.session_dropdown.currentText()
        session_data = self.session_manager.load_session(selected_session)
        if session_data:
            self.game_manager.load_games(session_data['games'])
            self.stat_tracker.load_stats(session_data['stats'])
            # Assuming you have methods to handle the loading of games and stats
            # You would also handle the restoration of save states here
            QMessageBox.information(self, "Session Loaded", f"Session '{selected_session}' has been loaded successfully.")
        else:
            QMessageBox.warning(self, "Load Error", "Failed to load the selected session. It may be corrupted or missing.")

    def save_current_session(self):
        session_name, ok = QInputDialog.getText(self, "Save Session", "Enter a name for the session:")
        if ok and session_name:
            games = self.game_manager.games  # If this is how you access the current games
            stats = self.stat_tracker.get_stats()
            save_states = {}  # Placeholder for save states logic
            self.session_manager.save_session(session_name, games, stats, save_states)
            QMessageBox.information(self, "Session", f"Session '{session_name}' saved successfully")
            self.session_dropdown.addItem(session_name)    
            
    def apply_new_config(self):
        # Extract and validate interval settings
        new_min_interval = self.min_interval_input.text()
        new_max_interval = self.max_interval_input.text()
        valid, message = self.validate_intervals(new_min_interval, new_max_interval)

        # Validate and save the new configuration
        valid, message = self.validate_intervals(new_min_interval, new_max_interval)
        if valid:
            self.config_manager.save_config({'min_shuffle_interval': int(new_min_interval),
                                             'max_shuffle_interval': int(new_max_interval)})
            self.load_config()  # Reload configuration to apply changes
            QMessageBox.information(self, "Success", "Configuration updated successfully.")
        else:
            QMessageBox.warning(self, "Invalid Input", message)
            
    def validate_intervals(self, min_interval, max_interval):
        # Try converting intervals to integers and validate
        try:
            min_interval = int(min_interval)
            max_interval = int(max_interval)

            if min_interval <= 0 or max_interval <= 0:
                return False, "Intervals must be positive numbers."

            if min_interval > max_interval:
                return False, "Minimum interval cannot be greater than maximum interval."

            return True, "Valid intervals."
        
        except ValueError:
            # Raised if conversion to int fails
            return False, "Intervals must be numeric."                            





    
    def create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Dropdown to select a specific game's stats
        self.game_stats_dropdown = QComboBox()
        self.game_stats_dropdown.addItem("All Games")
        self.game_stats_dropdown.addItems(self.game_manager.games.keys())
        self.game_stats_dropdown.currentTextChanged.connect(self.update_stats_display)
        layout.addWidget(self.game_stats_dropdown)

        # Label for stats display
        self.stats_label = QLabel("Select a game to view detailed stats")
        layout.addWidget(self.stats_label)

        # Button to update stats display
        update_stats_button = QPushButton("Update Stats")
        update_stats_button.clicked.connect(self.update_stats_display)
        layout.addWidget(update_stats_button)

        # Button to export stats
        export_stats_button = QPushButton("Export Stats")
        export_stats_button.clicked.connect(self.export_stats)
        layout.addWidget(export_stats_button)

        return tab

    def update_stats_display(self, selected_game=None):
        selected_game = self.game_stats_dropdown.currentText()
        total_time, total_swaps, detailed_stats = self.stat_tracker.get_stats()

        if selected_game and selected_game != "All Games":
            game_stats = detailed_stats.get(selected_game, {})
            stats_text = f"Stats for {selected_game}:\nTotal Time: {game_stats.get('total_time', 0)} seconds"
        else:
            stats_text = f"Total Time: {total_time} seconds\nTotal Swaps: {total_swaps}\nGame Times: {detailed_stats}"

        self.stats_label.setText(stats_text)

    def export_stats(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Stats", "", "JSON Files (*.json)")
        if file_path:
            self.stat_tracker.export_stats(file_path)
            QMessageBox.information(self, "Export", "Stats exported successfully")
    





    def create_twitch_integration_tab(self):
        # Placeholder for Twitch Integration tab content
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Add widgets to layout here...
        return tab
