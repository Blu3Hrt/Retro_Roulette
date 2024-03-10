from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QMessageBox, QInputDialog
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QFileDialog, QLineEdit
from game_manager import GameManager
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retro Roulette")
        self.setGeometry(100, 100, 800, 600)  # Adjust size as needed

        # Create Tab Widget
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Initialize tabs
        self.init_tabs()

        self.game_manager = GameManager()
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

        return tab

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
        # Placeholder for Shuffle Management tab content
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Add widgets to layout here...
        return tab




    def create_configuration_tab(self):
        # Placeholder for Configuration tab content
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Add widgets to layout here...
        return tab





    def create_stats_tab(self):
        # Placeholder for Stats tab content
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Add widgets to layout here...
        return tab





    def create_twitch_integration_tab(self):
        # Placeholder for Twitch Integration tab content
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # Add widgets to layout here...
        return tab
