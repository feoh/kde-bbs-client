"""
BBS Chooser window for selecting which BBS to connect to.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.config_dialog import ConfigDialog
from ui.terminal_window import TerminalWindow


class BBSChooser(QMainWindow):
    """Main window for choosing a BBS to connect to."""

    def __init__(self, config, config_manager):
        """Initialize the BBS chooser window."""
        super().__init__()
        self.config = config
        self.config_manager = config_manager
        self.terminal_window = None

        self.setWindowTitle("KDE BBS Client - Choose BBS")
        self.setMinimumSize(600, 400)

        self.setup_ui()
        self.load_bbs_list()

    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Select a BBS to Connect")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # BBS List
        self.bbs_list = QListWidget()
        self.bbs_list.setAlternatingRowColors(True)
        self.bbs_list.itemDoubleClicked.connect(self.connect_to_bbs)
        layout.addWidget(self.bbs_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.quit_application)
        button_layout.addWidget(self.quit_button)

        self.help_button = QPushButton("Terminal Help")
        self.help_button.clicked.connect(self.show_terminal_help)
        button_layout.addWidget(self.help_button)

        button_layout.addStretch()

        self.add_button = QPushButton("Add New BBS")
        self.add_button.clicked.connect(self.add_new_bbs)
        button_layout.addWidget(self.add_button)

        self.connect_button = QPushButton("Connect")
        self.connect_button.setDefault(True)
        self.connect_button.clicked.connect(self.connect_to_bbs)
        self.connect_button.setEnabled(False)
        button_layout.addWidget(self.connect_button)

        layout.addLayout(button_layout)

        central_widget.setLayout(layout)

        # Enable/disable connect button based on selection
        self.bbs_list.itemSelectionChanged.connect(self.on_selection_changed)

        # Apply styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: #333;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #4a90d9;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f4ff;
                color: #333;
            }
            QPushButton {
                padding: 10px 24px;
                border: none;
                border-radius: 4px;
                background-color: #4a90d9;
                color: white;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a9de5;
            }
            QPushButton:pressed {
                background-color: #3a80c9;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
            QPushButton#add_button {
                background-color: #5cb85c;
            }
            QPushButton#add_button:hover {
                background-color: #6cc86c;
            }
            QPushButton#quit_button {
                background-color: #d9534f;
            }
            QPushButton#quit_button:hover {
                background-color: #e5635f;
            }
            QPushButton#help_button {
                background-color: #5bc0de;
            }
            QPushButton#help_button:hover {
                background-color: #6bd0ee;
            }
        """)
        self.add_button.setObjectName("add_button")
        self.quit_button.setObjectName("quit_button")
        self.help_button.setObjectName("help_button")

    def load_bbs_list(self):
        """Load the list of BBS systems from configuration."""
        self.bbs_list.clear()

        bbs_systems = self.config.get('bbs_systems', [])

        if not bbs_systems:
            # Show message if no BBS systems configured
            item = QListWidgetItem("No BBS systems configured. Click 'Add New BBS' to get started.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.bbs_list.addItem(item)
            return

        for bbs in bbs_systems:
            name = bbs.get('name', 'Unknown')
            address = bbs.get('address', 'Unknown')
            port = bbs.get('port', 23)

            display_text = f"{name}\n{address}:{port}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, bbs)
            self.bbs_list.addItem(item)

    def on_selection_changed(self):
        """Handle selection change in the BBS list."""
        selected_items = self.bbs_list.selectedItems()
        self.connect_button.setEnabled(len(selected_items) > 0)

    def add_new_bbs(self):
        """Show dialog to add a new BBS system."""
        dialog = ConfigDialog(self)
        if dialog.exec():
            config_data = dialog.get_config_data()
            self.config_manager.save_config(config_data)

            # Reload config and refresh list
            self.config = self.config_manager.load_config()
            self.load_bbs_list()

    def connect_to_bbs(self):
        """Connect to the selected BBS."""
        selected_items = self.bbs_list.selectedItems()
        if not selected_items:
            return

        bbs_data = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not bbs_data:
            return

        # Create and show terminal window
        self.terminal_window = TerminalWindow(bbs_data, self.config_manager)
        self.terminal_window.show()
        self.terminal_window.connect_to_bbs()

    def quit_application(self):
        """Quit the application, closing all windows cleanly."""
        # Close terminal window if it exists
        if self.terminal_window:
            self.terminal_window.close()
        # Quit the application
        QApplication.quit()

    def show_terminal_help(self):
        """Show help dialog with terminal window features."""
        help_text = """
<h2>Terminal Window Features</h2>

<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>Ctrl+Plus</b> or <b>Ctrl+=</b></td><td>Increase font size</td></tr>
<tr><td><b>Ctrl+Minus</b></td><td>Decrease font size</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Reset font size to default</td></tr>
<tr><td><b>Ctrl+C</b></td><td>Copy selected text to clipboard</td></tr>
<tr><td><b>Ctrl+V</b></td><td>Paste clipboard contents to BBS</td></tr>
<tr><td><b>Ctrl+X</b></td><td>Cut (copies selection)</td></tr>
</table>

<h3>Navigation Keys</h3>
<table>
<tr><td><b>Arrow Keys</b></td><td>Navigate menus and text</td></tr>
<tr><td><b>Page Up/Down</b></td><td>Scroll through content</td></tr>
<tr><td><b>Home/End</b></td><td>Jump to start/end of line</td></tr>
<tr><td><b>Tab</b></td><td>Send tab character</td></tr>
<tr><td><b>Escape</b></td><td>Send escape character</td></tr>
</table>

<h3>Display Features</h3>
<ul>
<li><b>ANSI Colors:</b> Full support for 16-color, 256-color, and RGB colors</li>
<li><b>Blinking Cursor:</b> Green block cursor shows typing position</li>
<li><b>Resizable Window:</b> Window size is saved between sessions</li>
<li><b>Font Size:</b> Font size is saved between sessions</li>
</ul>

<h3>Mouse Features</h3>
<ul>
<li><b>Text Selection:</b> Click and drag to select text for copying</li>
<li><b>Double-click:</b> Select a word</li>
</ul>

<h3>Configuration</h3>
<p>Settings are stored in:<br>
<code>~/.config/kdebbsclient/client-config.yaml</code></p>
"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Terminal Help")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        # Close terminal window if it exists
        if self.terminal_window:
            self.terminal_window.close()
        event.accept()
