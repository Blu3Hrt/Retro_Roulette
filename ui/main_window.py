from PySide6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QInputDialog, QLabel, QLineEdit, QGroupBox,
                               QPushButton, QListWidget, QFileDialog, QMenu, QComboBox, QHBoxLayout, QFormLayout, QCheckBox, QSpinBox)
from PySide6.QtCore import Qt, QTimer
from game_manager import GameManager
from config import ConfigManager
from session_manager import SessionManager
from stat_tracker import StatsTracker
from twitch.twitch_flask import flask_thread
from twitch.twitch_integration import TwitchIntegration
from ui.style import Style
from pathlib import Path
import Python_Client

import os, random, subprocess, time, json, sys, logging
import psutil, shutil, keyboard, threading

SUPPORTED_EXTENSIONS = (
    '.nes', '.snes', '.gbc', '.gba', '.md', '.nds',
    '.pce', '.sgx', '.sms', '.gg', '.sg', '.a26',
    '.sfc', '.n64', '.psx', '.ps2', '.psp', '.gb', 
    '.gc', '.3ds', '.smc', '.3ds', '.nsp', '.xci',
    '.zip', '.7z', '.rar', '.tar', '.gz', '.bz2',
    '.cue', '.z64', '.gen', '.smd', '.v64', '.gcm',
    '.gcz', '.srl', '.xiso', '.dsi', '.app', '.ids',
    '.pce', '.ngp', '.ngc', '.vpk', '.vb', '.ws',
    '.wsc', '.bin', '.dat', '.lst', '.ipa', '.apk',
    '.obb')


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        try:
            super().__init__(parent)
            main_thread_id = threading.get_ident()
            logging.info(f"MainWindow is running in thread ID: {main_thread_id}")                
            self.resize(750, 500)
            self.setWindowTitle("Retro Roulette")

            # Create Tab Widget
            self.tab_widget = QTabWidget(self)
            self.setCentralWidget(self.tab_widget)

            self.game_manager = GameManager()
            self.config_manager = ConfigManager()     
            self.session_manager = SessionManager()
            self.stat_tracker = StatsTracker()
            self.is_shuffling = False
            self.twitch_integration = TwitchIntegration(self)
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
            self.init_timer(self.update_stats_display, 1000)
            
            self.shuffle_timer = QTimer()
            self.shuffle_timer.timeout.connect(self.shuffle_games)
            self.remaining_shuffle_time = None        
            



            self.twitch_integration.force_swap_signal.connect(self.force_swap)
            self.twitch_integration.pause_shuffle_signal.connect(self.pause_shuffle_for_duration)

            configured_hotkey = self.config_manager.load_hotkey_config()
            self.register_global_hotkey(configured_hotkey)
        except Exception as e:
            logging.error(f"An error occurred in MainWindow initialization: {str(e)}")
            raise

        # Load and apply UI style from the configuration
        ui_style = self.config.get('style', 'dark')
        self.style_selector.setCurrentText(ui_style.capitalize())
        self.apply_selected_style()  # Ensures the style is applied on launch

        # Load and set the Twitch pause duration from the configuration
        twitch_pause_duration = self.config.get('twitch_pause_duration', 30)  # Default to 30 seconds
        self.pause_duration_spinbox.setValue(twitch_pause_duration)

        

    def init_ui(self):
        Style.set_dark_style(self)
        self.status_bar = self.statusBar()
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)

    def apply_selected_style(self):
        style_methods = {
            'dark': Style.set_dark_style,
            'light': Style.set_light_style
        }
        selected_style = self.style_selector.currentText().lower()
        style_method = style_methods.get(selected_style, lambda x: None)
        style_method(self)
        # Save the selected style to the configuration
        self.config['style'] = selected_style

    def init_timer(self, callback, interval):
        timer = QTimer(self)
        timer.timeout.connect(callback)
        timer.start(interval)

    def init_tabs(self):
        # Create tabs for different functionalities
        self.tab_widget.addTab(self.create_game_management_tab(), "Game Management")
        self.tab_widget.addTab(self.create_session_management_tab(), "Session Management")
        self.tab_widget.addTab(self.create_shuffle_management_tab(), "Shuffle Management")
        self.tab_widget.addTab(self.create_configuration_tab(), "Configuration")
        self.tab_widget.addTab(self.create_stats_tab(), "Stats")
        self.tab_widget.addTab(self.create_twitch_integration_tab(), "Twitch [Experimental]")


    def refresh_ui(self):
        self.update_session_info()
        self.refresh_game_list()



    def create_group_box(self, layout_class, spacing, margins):
        group = QGroupBox(self)
        layout = layout_class(group)
        layout.setSpacing(spacing)
        layout.setContentsMargins(*margins)
        return group, layout


    def create_game_management_tab(self):
        def create_group_box(title, layout_class, spacing, margins):
            group = QGroupBox(title)
            layout = layout_class(group)
            layout.setSpacing(spacing)
            layout.setContentsMargins(*margins)
            return group, layout

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        search_group, search_layout = create_group_box("Search Games", QHBoxLayout, 5, (10, 20, 10, 10))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search games...")
        self.search_input.textChanged.connect(self.filter_games)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)

        manage_group, manage_layout = create_group_box("Manage Games", QHBoxLayout, 5, (10, 20, 10, 10))
        add_games_button = QPushButton("Add Games")
        add_games_button.clicked.connect(self.add_games)
        add_directory_button = QPushButton("Add Games from Directory")
        add_directory_button.clicked.connect(self.add_games_from_directory)
        manage_layout.addWidget(add_games_button)
        manage_layout.addWidget(add_directory_button)
        layout.addWidget(manage_group)

        games_info_group_box, games_info_layout = create_group_box("Games", QVBoxLayout, 0, (0, 0, 0, 0))
        self.game_list = QListWidget()
        self.game_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_list.customContextMenuRequested.connect(self.show_game_context_menu)
        self.game_list.itemSelectionChanged.connect(self.display_game_details)
        games_info_layout.addWidget(self.game_list)
        self.game_details_label = QLabel("Select a game to view details")
        games_info_layout.addWidget(self.game_details_label)
        layout.addWidget(games_info_group_box)

        self.game_list.doubleClicked.connect(self.prompt_rename_game)

        layout.addStretch()
        return tab


    def show_game_context_menu(self, pos):
        try:
            menu = QMenu(self)
            selected_items = self.game_list.selectedItems()
            actions = {}

            if not selected_items:
                actions[menu.addAction("Add Games")] = self.add_games
                actions[menu.addAction("Add Games from Directory")] = self.add_games_from_directory
            else:
                self.game_context_menu_logic(actions, menu, selected_items)
            action = menu.exec_(self.game_list.mapToGlobal(pos))
            if action in actions:
                actions[action]()
                logging.info(f"Action '{action.text()}' executed")
        except Exception as e:
            # Handle the exception here
            logging.error(f"An error occurred in show_game_context_menu: {e}")

    def game_context_menu_logic(self, actions, menu, selected_items):
        try:
            actions[menu.addAction("Remove Selected Game")] = self.remove_selected_game
            # Use the cleaned game name from the selected item
            game_name = self.clean_game_name(selected_items[0].text())
            game_path = self.find_game_path_by_name(game_name)
            if game_path and self.game_manager.games[game_path].get('completed'):
                actions[menu.addAction("Unmark as Completed")] = self.mark_game_as_not_completed
            else:
                actions[menu.addAction("Mark as Completed")] = self.mark_game_as_completed
            actions[menu.addAction("Rename Selected Game")] = self.prompt_rename_game
            actions[menu.addAction("Set Goals for Selected Game")] = self.prompt_set_game_goals
        except Exception as e:
            # Handle the exception here
            logging.error(f"Error occurred in game_context_menu_logic: {e}")


    
    def prompt_set_game_goals(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected for setting goals")
            return

        game_name = selected_items[0].text().rsplit(" - ", 1)[0]  # Modified line
        if game_path := self.find_game_path_by_name(game_name):
            current_goals = self.game_manager.games[game_path].get('goals', '')
            new_goals, ok = QInputDialog.getMultiLineText(self, "Set Goals", "Enter goals for the game:", current_goals)

            if ok:
                try:
                    self.game_manager.set_game_goals(game_path, new_goals)
                    self.refresh_game_list()
                    # Debug logging
                    print(f"Game goals set for {game_name}: {new_goals}")
                except Exception as e:
                    # Error handling/logging
                    print(f"Error setting game goals for {game_name}: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to set goals for {game_name}. Please try again.")
    
    def filter_games(self):
        search_text = self.search_input.text().lower()  # Corrected from self.search_bar to self.search_input
        for i in range(self.game_list.count()):
            item = self.game_list.item(i)
            item.setHidden(search_text not in item.text().lower())
            

    def display_game_details(self):
        try:
            if selected_items := self.game_list.selectedItems():
                game_name = selected_items[0].text().rsplit(" - ", 1)[0]
                if game_path := self.find_game_path_by_name(game_name):
                    self.display_game_stats(game_path, game_name)
            else:
                self.game_details_label.setText("Select a game to view details")
        except Exception as e:
            # Handle the exception here
            logging.error(f"Error occurred while displaying game details: {str(e)}")
            self.game_details_label.setText("Error occurred while displaying game details")

    def display_game_stats(self, game_path, game_name):
        game_data = self.game_manager.games[game_path]
        goals = game_data.get('goals', 'No goals set')
        game_stats = self.game_manager.stats_tracker.game_stats.get(game_name, {})
        swaps = game_stats.get('swaps', 0)
        time_spent = self.game_manager.stats_tracker.format_time(game_stats.get('time_spent', 0))

        details = (
            f"Name: {game_data['name']}\n"
            f"Path: {game_path}\n"
            f"Completed: {'Yes' if game_data['completed'] else 'No'}\n"
            f"Goals: {goals}\n"
            f"Swaps: {swaps}\n"
            f"Time Spent: {time_spent}"
        )

        self.game_details_label.setText(details)

 

    def setup_games_directory(self):
        app_root = os.path.dirname(sys.modules['__main__'].__file__)
        games_dir = os.path.join(app_root, "games")
        if not os.path.exists(games_dir):
            os.makedirs(games_dir)
        return games_dir

    def add_game_if_supported(self, file_path, added_any):
        if os.path.isfile(file_path) and any(file_path.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            normalized_path = os.path.abspath(file_path)
            if normalized_path not in self.game_manager.games:
                self.game_manager.add_game(normalized_path)
                logging.info("Added game: %s", normalized_path)
                return True
            else:
                logging.info(f"Game {os.path.basename(file_path)} is already in the list.")
        return added_any

    def add_games(self):
        try:
            games_dir = self.setup_games_directory()
            file_names, _ = QFileDialog.getOpenFileNames(self, "Select Games", games_dir, 
                                                        "Game Files (" + " ".join("*" + ext for ext in SUPPORTED_EXTENSIONS) + ")")
            added_any = False
            for file_name in file_names:
                added_any = self.add_game_if_supported(file_name, added_any)

            if added_any:
                self.refresh_ui()
                self.update_and_save_session()
        except Exception as e:
            logging.error(f"An unexpected error occurred while adding games: {e}")

    def add_games_from_directory(self):
        try:
            games_dir = self.setup_games_directory()
            if directory := QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                games_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
            ):
                logging.info(f"Selected directory: {directory}")
                added_any = False
                for file_name in os.listdir(directory):
                    file_path = os.path.join(directory, file_name)
                    added_any = self.add_game_if_supported(file_path, added_any)

                if added_any:
                    self.refresh_ui()
                    self.update_and_save_session()
        except Exception as e:
            logging.error(f"An unexpected error occurred while adding games from directory: {e}")      

    def process_selected_games(self, action, no_selection_message):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", no_selection_message)
            return

        for item in selected_items:
            logging.info(f"Processing item: {item.text()}")
            if game_path := self.find_game_path_by_name(item.text()):
                logging.info(f"Found game path: {game_path}")
                action(game_path)
                logging.info(f"Action performed on: {game_path}")

        self.refresh_ui()
        logging.info("UI refreshed")
        self.update_and_save_session()
        logging.info("Session updated and saved")

    def remove_selected_game(self):
        try:
            self.process_selected_games(self.game_manager.remove_game, "No game selected to remove")
            logging.info("Selected game(s) removed")
        except Exception as e:
            logging.error(f"Error occurred while removing game: {str(e)}")

    def mark_game_as_completed(self):
        try:
            self.process_selected_games(self.game_manager.mark_game_as_completed, "No game selected to mark as completed")
            logging.info("Selected game(s) marked as completed")
        except Exception as e:
            logging.error(f"Error occurred while marking game as completed: {str(e)}")

    def mark_game_as_not_completed(self):
        try:
            self.process_selected_games(self.game_manager.mark_game_as_not_completed, "No game selected to unmark as completed")
            logging.info("Selected game(s) marked as not completed")
        except Exception as e:
            logging.error(f"Error occurred while marking game as not completed: {str(e)}")
         
    def prompt_rename_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Information", "No game selected for renaming")
            return

        current_name = self.clean_game_name(selected_items[0].text())
        new_name, ok = QInputDialog.getText(self, "Rename Game", "Enter new name:", text=current_name)

        if ok and new_name:
            try:
                self.rename_selected_game(selected_items[0], new_name)
                logging.info("Game renamed successfully")
            except Exception as e:
                logging.error(f"Error occurred while renaming game: {e}")
                QMessageBox.critical(self, "Error", "An error occurred while renaming the game. Please try again.")         

    def rename_selected_game(self, item, new_name):
        old_name = self.clean_game_name(item.text())
        if path := self.find_game_path_by_name(old_name):
            self.game_manager.rename_game(path, new_name)
            self.refresh_game_list()
            logging.info(f"Game '{old_name}' renamed to '{new_name}'")
        else:
            logging.warning(f"Game '{old_name}' not found for renaming")

    def find_game_path_by_name(self, name):
        try:
            cleaned_name = self.clean_game_name(name)
            return next(
                (
                    game_path
                    for game_path, game_data in self.game_manager.games.items()
                    if game_data['name'] == cleaned_name
                ),
                None,
            )
        except Exception as e:
            logging.error(f"Error occurred while finding game path by name: {e}")
            return None

    def clean_game_name(self, name):
        if " - In Progress" in name:
            return name.rsplit(" - In Progress", 1)[0]
        elif " - Completed" in name:
            return name.rsplit(" - Completed", 1)[0]
        return name
        
            
    def refresh_game_list(self):
        if hasattr(self, 'game_list'):
            self.game_list.clear()
            for game in self.game_manager.games.values():
                item_text = f"{game['name']} - {'Completed' if game['completed'] else 'In Progress'}"
                self.game_list.addItem(item_text)

    def toggle_game_completion(self):
        """Toggles the completion status of the current game."""
        if not self.game_manager.current_game:
            return  # No game is currently selected

        current_game_path = self.find_game_path_by_name(self.game_manager.current_game)
        if not current_game_path:
            return  # Current game path not found

        # Toggle the completion status
        if self.game_manager.games[current_game_path]['completed']:
            self.game_manager.mark_game_as_not_completed(current_game_path)
        else:
            self.game_manager.mark_game_as_completed(current_game_path)

        # Refresh the UI to reflect changes
        self.refresh_game_list()


    def create_button(self, text, slot):
        button = QPushButton(text)
        button.clicked.connect(slot)
        return button

    def create_shuffle_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Button to launch BizHawk
        launch_bizhawk_button = self.create_button("Launch BizHawk", self.launch_bizhawk)
        layout.addWidget(launch_bizhawk_button)

        # Shuffle control buttons
        shuffle_buttons = [
            ("Start Shuffle", self.start_shuffle),
            ("Pause Shuffle", self.pause_shuffle),
            ("Resume Shuffle", self.resume_shuffle),
            ("Stop Shuffle", self.stop_shuffle)
        ]
        for text, slot in shuffle_buttons:
            button = self.create_button(text, slot)
            layout.addWidget(button)

        # Initialize shuffle state
        self.is_shuffling = False
        self.current_game_path = None

        return tab


    def launch_bizhawk(self):        
        self.config = self.config_manager.load_config()
        bizhawk_path = self.config.get('bizhawk_path')
        if not bizhawk_path:
            QMessageBox.critical(self, "Configuration Error", "BizHawk path is not set.")
            return        
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
        return any(
            proc.info['name'] in ['EmuHawk.exe', 'BizHawk.exe']
            for proc in psutil.process_iter(['name'])
        )

    def start_shuffle(self):
        if self.is_shuffling:
            self.statusBar().showMessage("Shuffle is already active.", 5000)
            return

        if not self.current_session_name:
            QMessageBox.warning(self, "No Session", "No current session is set. Please load a session first.")
            return

        try:
            if session_data := self.session_manager.load_session(self.current_session_name):
                self.initialize_session_data(session_data)
            self.shuffle_interval = self.determine_shuffle_interval()

            if self.is_bizhawk_process_running():
                self.is_shuffling = True
                self.shuffle_games()
            else:
                logging.error("BizHawk/EmuHawk process is not running. Cannot start shuffle.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while starting shuffle: {e}")
            QMessageBox.critical(self, "Shuffle Error", f"An error occurred while starting shuffle: {e}")

    def initialize_session_data(self, session_data):
        required_keys = {'games', 'stats', 'save_states'}
        if not required_keys.issubset(session_data):
            raise ValueError("Session data is missing required fields")

        initial_stats = {
            'game_stats': session_data['stats'][0],
            'total_swaps': session_data['stats'][1],
            'total_shuffling_time': session_data['stats'][2]
        }
        self.game_manager.stats_tracker = StatsTracker(initial_stats)

    def determine_shuffle_interval(self):
        min_interval = self.config.get('min_shuffle_interval', 30)
        max_interval = self.config.get('max_shuffle_interval', 60)

        if min_interval > max_interval:
            logging.warning("Minimum interval is greater than maximum interval. Using default values.")
            min_interval, max_interval = 30, 60

        return random.randint(min_interval, max_interval) * 1000

    def pause_shuffle(self):
        self.is_shuffling = False
        if self.shuffle_timer.isActive():
            self.remaining_shuffle_time = self.shuffle_timer.remainingTime()
            self.shuffle_timer.stop()
            logging.info("Paused shuffle for %d seconds", self.remaining_shuffle_time // 1000)
            self.statusBar().showMessage("Shuffle paused.", 5000)

    def resume_shuffle(self):
        if not self.is_shuffling and self.game_manager.games:
            self.is_shuffling = True
            if self.remaining_shuffle_time is not None:
                self.shuffle_timer.start(self.remaining_shuffle_time)
                logging.info("Resumed shuffle for %d seconds", self.remaining_shuffle_time // 1000)
                self.statusBar().showMessage("Shuffle resumed.", 5000)
                self.remaining_shuffle_time = None
            else:
                self.shuffle_games()

    def stop_shuffle(self):
        if self.is_shuffling:
            self.is_shuffling = False
            self.shuffle_timer.stop()
            self.game_manager.stats_tracker.end_game(self.game_manager.current_game)
            self.remaining_shuffle_time = None
            self.game_manager.current_game = None
            self.update_and_save_session()
            logging.info("Shuffle stopped.")
            self.statusBar().showMessage("Shuffle stopped.", 5000)
        else:
            logging.warning("Shuffle is not active.")
            self.statusBar().showMessage("Shuffle is not active.", 5000)
            
    
    def shuffle_games(self):
        if not self.is_shuffling:
            logging.info("Shuffling is disabled.")
            return

        if not self.game_manager.games:
            logging.warning("No games available to shuffle.")
            QMessageBox.warning(self, "Shuffle Error", "No games available to shuffle.")
            self.is_shuffling = False
            return

        if not self.is_bizhawk_process_running():
            self.pause_shuffle()
            return

        available_games = {path: game for path, game in self.game_manager.games.items() if path != self.current_game_path}
        if len(available_games) <= 1 or all(game['completed'] for game in available_games.values()):
            self._handle_shuffle_unavailability(available_games)
            return

        try:
            next_game_path = random.choice(list(available_games.keys()))
            self._switch_to_game(next_game_path)
        except Exception as e:
            logging.error(f"Error switching to the next game: {e}")
            self.statusBar().showMessage(f"An error occurred while switching games: {e}")

        self.current_game_path = next_game_path
        shuffle_interval = self.determine_shuffle_interval()
        logging.info("Scheduling next shuffle in %d seconds", shuffle_interval // 1000)
        self.shuffle_timer.start(shuffle_interval)

        if not self.is_bizhawk_process_running():
            self.pause_shuffle()

    def force_swap(self):
        if self.is_shuffling:
            self.shuffle_games()
            shuffle_interval = self.determine_shuffle_interval()
        else:
            logging.warning("Shuffling is not active. Cannot force swap.")

    def _handle_shuffle_unavailability(self, available_games):
        logging.info("Cannot shuffle: Only one game available or all games are completed.")
        if all(game['completed'] for game in available_games.values()):
            QMessageBox.information(self, "Congratulations!", "Amazing! You have completed all the games.")
        else:
            QMessageBox.information(self, "Shuffle Info", "Cannot shuffle: Only one game available.")
        self.is_shuffling = False

    def _switch_to_game(self, next_game_path):
        next_game_name = self.game_manager.games[next_game_path]['name']
        self.game_manager.switch_game(next_game_name)
        if self.current_game_path:
            self.save_game_state(self.current_game_path)
            self.update_and_save_session()
        self.load_game(next_game_path)
        self.load_game_state(next_game_path)
        self.update_and_save_session()
        self.update_session_info()




    def ensure_directory_exists(self, state_path):
        directory = Path(state_path).parent
        directory.mkdir(parents=True, exist_ok=True)

    def display_critical_error(self, title, message, exception):
        logging.error(f"{message}: {exception}")
        QMessageBox.critical(self, title, f"{message}: {exception}")

    def save_game_state(self, game_path):
        if not game_path:
            return
        state_path = self.get_state_path(game_path)
        self.ensure_directory_exists(state_path)
        try:
            Python_Client.save_state(state_path)
            logging.info(f"Game state saved successfully to {state_path}")
        except Exception as e:
            self.display_critical_error("Save State Error", "Error saving game state", e)

    def load_game(self, game_path):
        if not game_path:
            return
        try:
            Python_Client.load_rom(game_path)
        except Exception as e:
            self.display_critical_error("Load Game Error", "An error occurred while loading the game", e)

    def load_game_state(self, game_path):
        state_file = self.get_state_path(game_path)
        self.ensure_directory_exists(state_file)
        if Path(state_file).exists():
            try:
                Python_Client.load_state(state_file)
                logging.info(f"Game state loaded successfully from {state_file}")
            except Exception as e:
                self.display_critical_error("Load Game State Error", "Error loading game state", e)
        else:
            self.save_game_state(game_path)



    def get_state_path(self, game_file):
        session_dir = Path(self.get_session_path(self.current_session_name))
        save_states_dir = session_dir / 'savestates'
        game_id = Path(game_file).stem
        state_file = f"{game_id}.state"
        return str(save_states_dir / state_file)

    
    


    def create_configuration_tab(self):
        def no_op(layout):
            pass

        def add_label_and_widget(layout, label, widget):
            layout.addRow(QLabel(label), widget)

        def setup_group_box(title, form_layout_setup, widgets):
            group_box = QGroupBox(title)
            group_box.setMinimumHeight(100)
            layout = QFormLayout(group_box)
            layout.setVerticalSpacing(20)
            layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            form_layout_setup(layout)
            [layout.addRow(w[0], w[1]) if isinstance(w, tuple) else layout.addWidget(w) for w in widgets]
            return group_box

        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        self.style_selector = QComboBox()
        self.style_selector.addItems(["Dark", "Light"])
        current_style = self.config.get('style', 'dark')
        self.style_selector.setCurrentText(current_style.capitalize())
        self.style_selector.currentIndexChanged.connect(self.apply_selected_style)
        style_group_box = setup_group_box(
            "Appearance",
            lambda layout: layout.setRowWrapPolicy(QFormLayout.DontWrapRows),
            [
                ("Select UI Style:", self.style_selector),
            ]
        )

        self.bizhawk_path_input = QLineEdit(self.config.get('bizhawk_path', ''))
        self.bizhawk_path_input.setPlaceholderText("Path to BizHawk executable")
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_bizhawk_path)
        bizhawk_group_box = setup_group_box(
            "BizHawk Settings",
            no_op,
            [
                ("BizHawk Path:", self.bizhawk_path_input),
                browse_button,
            ]
        )

        self.min_interval_input = QLineEdit(str(self.config.get('min_shuffle_interval', '30')))
        self.max_interval_input = QLineEdit(str(self.config.get('max_shuffle_interval', '60')))
        shuffle_interval_group_box = setup_group_box(
            "Shuffle Intervals",
            no_op,
            [
                ("Minimum Interval (seconds):", self.min_interval_input),
                ("Maximum Interval (seconds):", self.max_interval_input),
            ]
        )

        self.hotkey_input = QLineEdit(self.config_manager.load_hotkey_config())
        self.hotkey_input.editingFinished.connect(self.update_hotkey_config)
        
        hotkey_group_box = setup_group_box(
            "Hotkey Settings",
            lambda layout: layout.setRowWrapPolicy(QFormLayout.DontWrapRows),
            [
                ("Game Completion Toggle Global Hotkey:", self.hotkey_input),
            ]
        )


        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_configuration)
        
        load_default_config_button = QPushButton("Load Default Config")
        load_default_config_button.clicked.connect(self.load_default_config)
                

        [main_layout.addWidget(group_box) for group_box in [style_group_box, bizhawk_group_box, shuffle_interval_group_box]]
        main_layout.addWidget(hotkey_group_box)
        main_layout.addWidget(save_config_button)
        main_layout.addWidget(load_default_config_button)
        main_layout.addStretch()

        return tab
    
    def load_default_config(self):
        self.config = self.config_manager.default_config()
        self.config_manager.save_config(self.config)
        self.statusBar().showMessage("The configuration has been reset to the default settings.")
        # You may want to update the UI elements to reflect the default configuration here    

    def browse_bizhawk_path(self):
        if path := QFileDialog.getOpenFileName(
            self, "Select BizHawk Executable", "", "Executable Files (*.exe)"
        )[0]:
            self.bizhawk_path_input.setText(path)
            
    def execute_bizhawk_script(self):
        bizhawk_exe = Path(self.config["bizhawk_path"])
        if not bizhawk_exe.is_file():
            QMessageBox.critical(self, "Configuration Error", f"BizHawk executable not found at {bizhawk_exe}")
            return False

        lua_script = Path("bizhawk_server.lua")
        if not lua_script.is_file():
            QMessageBox.critical(self, "Configuration Error", f"Lua script not found at {lua_script}")
            return False

        command = [str(bizhawk_exe), f"--lua={lua_script}"]
        try:
            subprocess.Popen(command)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Execution Error", f"An error occurred while launching BizHawk: {e}")
            return False            

    def register_global_hotkey(self, hotkey):
        """Registers a global hotkey to toggle game completion."""
        def hotkey_action():
            self.toggle_game_completion()

        keyboard.add_hotkey(hotkey, hotkey_action)

    def update_hotkey_config(self):
        new_hotkey = self.hotkey_input.text()
        print(f"Updating hotkey to {new_hotkey}")  # Debugging statement
        self.config_manager.save_hotkey_config(new_hotkey)
        # Unregister the previous hotkey and register the new one
        keyboard.unhook_all_hotkeys()  # Assuming this function is available in the 'keyboard' library
        self.register_global_hotkey(new_hotkey)
        print(f"Hotkey {new_hotkey} saved to config")  # Corrected debugging statement

    def save_configuration(self):
        # Gather all configuration fields
        bizhawk_path = self.bizhawk_path_input.text()
        min_interval = self.min_interval_input.text()
        max_interval = self.max_interval_input.text()
        global_hotkey = self.hotkey_input.text()

        try:
            min_interval = int(min_interval)
            max_interval = int(max_interval)
            valid_intervals, message = self.validate_intervals(min_interval, max_interval)
            if not valid_intervals:
                QMessageBox.warning(self, "Invalid Input", message)
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Intervals must be numeric.")
            return

        config_data = {
            'bizhawk_path': bizhawk_path,
            'min_shuffle_interval': min_interval,
            'max_shuffle_interval': max_interval,
            'global_hotkey': global_hotkey,
            'style': self.style_selector.currentText().lower(),
            'twitch_pause_duration': self.pause_duration_spinbox.value()
        }

        self.config_manager.save_config(config_data)
        QMessageBox.information(self, "Success", "Configuration saved successfully.")


    def load_configuration(self):
        self.config = self.config_manager.load_config()
        self.bizhawk_path_input.setText(self.config.get('bizhawk_path', ''))
        self.min_interval_input.setText(str(self.config.get('min_shuffle_interval', '30')))
        self.max_interval_input.setText(str(self.config.get('max_shuffle_interval', '60')))
        self.statusBar().showMessage("Configuration loaded successfully.", 5000)

    def validate_intervals(self, min_interval, max_interval):
        if min_interval <= 0 or max_interval <= 0:
            return False, "Intervals must be positive numbers."
        elif min_interval > max_interval:
            return False, "Minimum interval cannot be greater than maximum interval."
        return True, "Valid intervals."



    def create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Labels to display stats
        self.total_swaps_label = QLabel("Total Swaps: 0")
        self.total_time_label = QLabel("Total Time: 00:00:00")
        self.game_name_label = QLabel("Current Game: None")
        self.current_game_swaps_label = QLabel("Current Game Swaps: 0")
        self.current_game_time_label = QLabel("Current Game Time: 00:00:00")
        
        self.output_individual_game_stats_checkbox = QCheckBox("Output Individual Game Stats")
        self.output_total_stats_checkbox = QCheckBox("Output Total Stats")
        self.output_current_game_stats_checkbox = QCheckBox("Output Current Game Stats")   
        self.reset_stats_button = QPushButton("Reset Stats")
        self.reset_stats_button.clicked.connect(self.reset_stats)
        

        layout.addWidget(self.total_swaps_label)
        layout.addWidget(self.total_time_label)
        layout.addWidget(self.game_name_label)
        layout.addWidget(self.current_game_swaps_label)
        layout.addWidget(self.current_game_time_label)
        layout.addWidget(self.reset_stats_button)
        return tab

        



    def update_stats_display(self):
        if hasattr(self, 'total_swaps_label'):
            game_stats, total_swaps, total_time = self.game_manager.stats_tracker.get_stats()
            real_time_total = self.calculate_real_time_total(total_time)

            self.set_label_text(self.total_swaps_label, "Total Swaps", total_swaps)
            self.set_label_text(self.total_time_label, "Total Time", self.format_time(real_time_total))

            current_game = self.game_manager.current_game
            current_game_stats = game_stats.get(current_game, {'swaps': 0, 'time_spent': 0})
            self.set_label_text(self.game_name_label, "Current Game", current_game or "None")
            self.set_label_text(self.current_game_swaps_label, "Current Game Swaps", current_game_stats['swaps'])
            self.set_label_text(self.current_game_time_label, "Current Game Time", self.format_time(current_game_stats['time_spent'] + self.calculate_real_time_total(0) if current_game else 0))
            self.update_session_info()
            
            
            self.output_stats_to_files(total_swaps, real_time_total, current_game, current_game_stats)

    def output_stats_to_files(self, total_swaps, real_time_total, current_game, current_game_stats):
        session_dir = self.get_session_path(self.current_session_name)
        stats_dir = os.path.join(session_dir, 'stats')
        os.makedirs(stats_dir, exist_ok=True)  # Ensure the stats directory exists

        # Define file paths
        total_swaps_file = os.path.join(stats_dir, 'total_swaps.txt')
        total_time_file = os.path.join(stats_dir, 'total_time.txt')
        current_game_file = os.path.join(stats_dir, 'current_game.txt')
        current_game_swaps_file = os.path.join(stats_dir, 'current_game_swaps.txt')
        current_game_time_file = os.path.join(stats_dir, 'current_game_time.txt')

        # Write stats to files
        with open(total_swaps_file, 'w') as f:
            f.write(str(total_swaps))
        with open(total_time_file, 'w') as f:
            f.write(self.format_time(real_time_total))
        with open(current_game_file, 'w') as f:
            f.write(current_game or "None")
        with open(current_game_swaps_file, 'w') as f:
            f.write(str(current_game_stats['swaps']))
        with open(current_game_time_file, 'w') as f:
            f.write(self.format_time(current_game_stats['time_spent'] + self.calculate_real_time_total(0) if current_game else 0))

    def calculate_real_time_total(self, total_time):
        start_time = self.game_manager.stats_tracker.start_time
        if start_time is None:
            start_time = time.time()  # Or some other appropriate value
        return total_time + (time.time() - start_time if self.game_manager.current_game else 0)

    def set_label_text(self, label, prefix, value):
        label.setText(f"{prefix}: {value}")

    def format_time(self, seconds):
        # Method to format seconds into hh:mm:ss
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def reset_stats(self):
        self.game_manager.stats_tracker.reset_all_stats()
        self.update_stats_display()
        self.statusBar().showMessage("Stats reset.", 5000)
        self.update_and_save_session()

    def create_button(self, text, slot):
        button = QPushButton(text)
        button.clicked.connect(slot)
        return button

    def create_session_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        buttons_info = [
            ("Create New Session", self.create_new_session),
            ("Save Current Session As...", self.save_current_session_as_new),
            ("Rename Selected Session", self.rename_current_session),
            ("Delete Selected Session", self.delete_current_session)
        ]

        [layout.addWidget(self.create_button(text, slot)) for text, slot in buttons_info]

        self.session_info_label = QLabel("Load a session to view details")
        layout.addWidget(self.session_info_label)

        self.session_dropdown = QComboBox(self)
        self.populate_session_dropdown()
        self.session_dropdown.currentIndexChanged.connect(self.load_session_from_dropdown)
        layout.addWidget(self.session_dropdown)

        tab.setLayout(layout)
        return tab


    def load_default_session(self):
        if session_data := self.session_manager.load_session('Default Session'):
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
        if selected_session_name := self.session_dropdown.itemText(
            selected_session_index
        ):
            self.load_session(selected_session_name)
        
    def load_session(self, session_name):
        session_folder = self.get_session_path(session_name)
        session_file = os.path.join(session_folder, 'session.json')
        try:
            with open(session_file, 'r') as file:
                self.session_data_load(file)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load the session '{session_name}'. It may be corrupted or missing. Error: {e}")          


    def session_data_load(self, file):
        session_data = json.load(file)
        self.current_session_name = session_data['name']
        self.game_manager.load_games(session_data['games'])
        self.game_manager.load_save_states(session_data.get('save_states', {}))
        self.refresh_ui()
        self.statusBar().showMessage(f"Session '{self.current_session_name}' has been loaded successfully.", 5000)
        self.save_last_session(self.current_session_name)            

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
                        self.session_rename_result(new_name)
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


    def session_rename_result(self, new_name):
        self.current_session_name = new_name
        self.statusBar().showMessage(f"Session renamed to '{new_name}'.", 5000)
        self.refresh_ui()
        self.save_last_session(new_name)
        self.populate_session_dropdown()
        self.load_session(new_name)         

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
# sourcery skip: simplify-constant-sum
            return
        try:
            self.sesson_info_values(session_data)
        except Exception as e:
            logging.error(f"An unexpected error occurred while updating the session info: {e}")
            self.session_info_label.setText("An error occurred while loading session details.")


    def sesson_info_values(self, session_data):
        session_name = session_data['name']
        games = session_data['games']
        game_count = len(games)

        # Corrected line: Use games.values() to iterate over dictionary values
        completed_game_count = sum(bool(game.get('completed', False))
                               for game in games.values())

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

        if last_session_name:
            if session_data := self.session_manager.load_session(
                last_session_name
            ):
                self.load_session(last_session_name)
            else:
                self.create_default_session()
                self.load_session('Default Session')
        else:
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
                self.create_session_savestate_dir(
                    new_session_path, new_session_name
                )
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Failed to save the current session as '{new_session_name}'. Error: {e}")


    def create_session_savestate_dir(self, new_session_path, new_session_name):
        # Create new session directory and savestates subdirectory
        os.makedirs(new_session_path, exist_ok=True)
        save_states_path = os.path.join(new_session_path, 'savestates')
        os.makedirs(save_states_path, exist_ok=True)

        # Assuming you have a method to get the current session data
        current_session_data = self.session_manager.get_session_info(self.current_session_name)

        # Adjust the 'name' in the session data
        current_session_data['name'] = new_session_name

        # Save the session data to 'session.json' in the new session folder
        session_file_path = os.path.join(new_session_path, 'session.json')
        with open(session_file_path, 'w') as f:
            json.dump(current_session_data, f, indent=4)

        # Copy savestates from the current session to the new session
        current_save_states_path = os.path.join(self.get_session_path(self.current_session_name), 'savestates')
        shutil.copytree(current_save_states_path, save_states_path, dirs_exist_ok=True)

        QMessageBox.information(self, "Session Saved", f"Current session has been saved as '{new_session_name}' successfully.")

     
     
            
    def create_twitch_integration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if self.twitch_integration.is_authenticated():
            self.twitch_integration.refresh_access_token()
            self.start_listening_for_rewards()
        else:
            print("User is not authenticated with Twitch.")

        self.authenticate_button = QPushButton("Sign in with Twitch")
        self.authenticate_button.clicked.connect(self.authenticate_with_twitch)
        self.signout_button = QPushButton("Sign out")
        self.signout_button.clicked.connect(self.sign_out_of_twitch)
        self.create_rewards_button = QPushButton("Create/Update Channel Point Rewards")
        self.create_rewards_button.clicked.connect(self.create_rewards_and_show_feedback)

        self.twitch_status_label = QLabel("Not Authenticated")

        self.update_twitch_display(self.twitch_integration.is_authenticated())

        layout.addWidget(self.authenticate_button)
        layout.addWidget(self.signout_button)
        layout.addWidget(self.twitch_status_label)

        # Fetch current Twitch rewards
        current_rewards = self.twitch_integration.get_rewards() if self.twitch_integration.is_authenticated() else []

        # Find "Pause Shuffle" and "Force Swap" rewards if they exist
        pause_shuffle_reward = next((reward for reward in current_rewards if reward['title'] == "Pause Shuffle"), None)
        force_swap_reward = next((reward for reward in current_rewards if reward['title'] == "Force Swap"), None)
        
        
        
        # UI for "Pause Shuffle" reward
        self.pause_shuffle_enabled_checkbox = QCheckBox("Enable Pause Shuffle Reward")
        self.pause_shuffle_cost_spinbox = QSpinBox()
        self.pause_shuffle_cost_spinbox.setRange(0, 10000)
        self.pause_shuffle_cooldown_spinbox = QSpinBox()
        self.pause_shuffle_cooldown_spinbox.setRange(0, 10000)

        # Set values from the API or use defaults
        if pause_shuffle_reward is not None:
            self.pause_shuffle_enabled_checkbox.setChecked(pause_shuffle_reward.get('is_enabled', True))
            self.pause_shuffle_cost_spinbox.setValue(pause_shuffle_reward.get('cost', 1000))
            pause_shuffle_cooldown = pause_shuffle_reward.get('global_cooldown_setting', {}).get('global_cooldown_seconds', 60)
            self.pause_shuffle_cooldown_spinbox.setValue(pause_shuffle_cooldown)
        else:
            self.pause_shuffle_enabled_checkbox.setChecked(True)
            self.pause_shuffle_cost_spinbox.setValue(1000)
            self.pause_shuffle_cooldown_spinbox.setValue(60)
       
        self.pause_duration_spinbox = QSpinBox()
        self.pause_duration_spinbox.setRange(1, 3600)
        self.pause_duration_spinbox.setValue(30)           
        
        pause_shuffle_group = QGroupBox("Pause Shuffle Reward Settings")
        pause_shuffle_layout = QVBoxLayout()

        pause_shuffle_enabled_layout = QHBoxLayout()
        pause_shuffle_enabled_layout.addWidget(self.pause_shuffle_enabled_checkbox)
        pause_shuffle_layout.addLayout(pause_shuffle_enabled_layout)        

        pause_shuffle_cost_layout = QHBoxLayout()
        pause_shuffle_cost_layout.addWidget(QLabel("Pause Shuffle Reward Cost:"))
        pause_shuffle_cost_layout.addWidget(self.pause_shuffle_cost_spinbox)
        pause_shuffle_layout.addLayout(pause_shuffle_cost_layout)

        pause_shuffle_cooldown_layout = QHBoxLayout()
        pause_shuffle_cooldown_layout.addWidget(QLabel("Pause Shuffle Cooldown (sec):"))
        pause_shuffle_cooldown_layout.addWidget(self.pause_shuffle_cooldown_spinbox)
        pause_shuffle_layout.addLayout(pause_shuffle_cooldown_layout)

        pause_shuffle_duration_layout = QHBoxLayout()
        pause_shuffle_duration_layout.addWidget(QLabel("Pause Duration (sec):"))
        pause_shuffle_duration_layout.addWidget(self.pause_duration_spinbox)
        pause_shuffle_layout.addLayout(pause_shuffle_duration_layout)

        pause_shuffle_group.setLayout(pause_shuffle_layout)
        layout.addWidget(pause_shuffle_group)
        
        
        # UI for "Force Swap" reward
        self.force_swap_enabled_checkbox = QCheckBox("Enable Force Swap Reward")
        self.force_swap_cost_spinbox = QSpinBox()
        self.force_swap_cost_spinbox.setRange(0, 10000)
        self.force_swap_cooldown_spinbox = QSpinBox()
        self.force_swap_cooldown_spinbox.setRange(0, 10000)

        # Set values from the API or use defaults
        if force_swap_reward is not None:
            self.force_swap_enabled_checkbox.setChecked(force_swap_reward.get('is_enabled', True))
            self.force_swap_cost_spinbox.setValue(force_swap_reward.get('cost', 1000))
            force_swap_cooldown = force_swap_reward.get('global_cooldown_setting', {}).get('global_cooldown_seconds', 60)
            self.force_swap_cooldown_spinbox.setValue(force_swap_cooldown)
        else:
            self.force_swap_enabled_checkbox.setChecked(True)
            self.force_swap_cost_spinbox.setValue(1000)
            self.force_swap_cooldown_spinbox.setValue(60)       
        
        
        force_swap_group = QGroupBox("Force Swap Reward Settings")
        force_swap_layout = QVBoxLayout()

        force_swap_enabled_layout = QHBoxLayout()
        force_swap_enabled_layout.addWidget(self.force_swap_enabled_checkbox)
        force_swap_layout.addLayout(force_swap_enabled_layout)        

        force_swap_cost_layout = QHBoxLayout()
        force_swap_cost_layout.addWidget(QLabel("Force Swap Reward Cost:"))
        force_swap_cost_layout.addWidget(self.force_swap_cost_spinbox)
        force_swap_layout.addLayout(force_swap_cost_layout)

        force_swap_cooldown_layout = QHBoxLayout()
        force_swap_cooldown_layout.addWidget(QLabel("Force Swap Cooldown (sec):"))
        force_swap_cooldown_layout.addWidget(self.force_swap_cooldown_spinbox)
        force_swap_layout.addLayout(force_swap_cooldown_layout)

        force_swap_group.setLayout(force_swap_layout)
        layout.addWidget(force_swap_group)

        

        layout.addWidget(self.create_rewards_button)

        tab.setLayout(layout)
        return tab

    def update_twitch_display(self, connected):
        status_message = "Connected to Twitch" if connected else "Not Connected to Twitch"
        self.twitch_status_label.setText(status_message)
        self.authenticate_button.setEnabled(not connected)
        self.signout_button.setEnabled(connected)
        self.create_rewards_button.setEnabled(connected)
        
        
    


    def start_listening_for_rewards(self):
        if self.twitch_integration.is_authenticated():
            # Start listening for rewards in a separate thread
            threading.Thread(target=self.twitch_integration.listen_for_rewards, daemon=True).start()
        else:
            print("User is not authenticated with Twitch.")
            
    def create_rewards_and_show_feedback(self):
        pause_shuffle_cost = self.pause_shuffle_cost_spinbox.value()
        force_swap_cost = self.force_swap_cost_spinbox.value()
        pause_shuffle_cooldown = self.pause_shuffle_cooldown_spinbox.value()
        force_swap_cooldown = self.force_swap_cooldown_spinbox.value()
        pause_shuffle_enabled = self.pause_shuffle_enabled_checkbox.isChecked()
        force_swap_enabled = self.force_swap_enabled_checkbox.isChecked()
        self.twitch_integration.create_rewards(pause_shuffle_cost, force_swap_cost, pause_shuffle_cooldown, force_swap_cooldown, pause_shuffle_enabled, force_swap_enabled)
        self.statusBar().showMessage("Channel Point Rewards created successfully.", 5000)

    def authenticate_with_twitch(self):
        self.twitch_integration.open_authentication_url()
        self.setup_flask_thread()
        if not self.flask_thread.isRunning():
            logging.info("Starting Flask thread...")
            self.flask_thread.start()
        else:
            logging.warning("Flask thread is already running.")

    def setup_flask_thread(self):
        self.flask_thread = flask_thread
        self.flask_thread.code_received.connect(self.on_code_received)
        self.flask_thread.auth_failed.connect(self.on_auth_failed)
        logging.info("Signals connected to slots.")

    def start_flask_thread(self):
        self.setup_flask_thread()
        if not self.flask_thread.isRunning():
            logging.info("Starting Flask thread...")
            self.flask_thread.start()
        else:
            logging.warning("Flask thread is already running.")

    def on_code_received(self, code):
        slot_thread_id = threading.get_ident()
        logging.info(f"on_code_received is running in thread ID: {slot_thread_id}")        
        logging.info("on_code_received slot called with code: %s", code)
        try:
            self.twitch_integration.handle_oauth_redirect(code)
            self.update_twitch_display(True)   
        except Exception as e:
            logging.error("An error occurred in on_code_received: %s", e)    
    
    def sign_out_of_twitch(self):
        try:
            self.twitch_integration.revoke_access_token()
            self.twitch_integration.clear_tokens_securely()
            self.update_twitch_display(False)
        except Exception as e:
            QMessageBox.warning(self, "Sign Out Error", f"An error occurred while signing out: {e}")

    def set_twitch_connection_status(self, status_message, authenticate_enabled, signout_enabled):
        self.twitch_status_label.setText(status_message)
        self.authenticate_button.setEnabled(authenticate_enabled)
        self.signout_button.setEnabled(signout_enabled)



    def on_auth_failed(self, error_message):
        logging.info("on_auth_failed slot called with error: %s", error_message)
        QMessageBox.warning(self, "Authentication Failed", error_message)
      
            
    def pause_shuffle_for_duration(self):
        if self.is_shuffling:
            self.pause_shuffle()
            QTimer.singleShot(self.pause_duration_spinbox.value() * 1000, self.resume_shuffle)
            logging.info("Shuffle paused for %d seconds", self.pause_duration_spinbox.value())
        else:
            logging.error("Cannot pause shuffle. Shuffling is not active.")   