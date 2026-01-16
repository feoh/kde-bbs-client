"""
Configuration dialog for initial BBS setup.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class ConfigDialog(QDialog):
    """Dialog for configuring a BBS connection."""

    def __init__(self, parent=None):
        """Initialize the configuration dialog."""
        super().__init__(parent)
        self.setWindowTitle("BBS Configuration")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title label
        title_label = QLabel("Configure BBS Connection")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Enter the details for your BBS system. "
            "This information will be saved for future connections."
        )
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        # Form layout for input fields
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # BBS Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., My Favorite BBS")
        form_layout.addRow("BBS Name:", self.name_input)

        # BBS Address
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., bbs.example.com or 192.168.1.100")
        form_layout.addRow("BBS Address:", self.address_input)

        # Port (optional)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(23)
        self.port_input.setSpecialValueText("23 (default)")
        form_layout.addRow("Port (optional):", self.port_input)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Your username")
        form_layout.addRow("Username:", self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Your password")
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setDefault(True)
        self.submit_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(self.submit_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                color: #333;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #4a90d9;
            }
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                background-color: #4a90d9;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a9de5;
            }
            QPushButton:pressed {
                background-color: #3a80c9;
            }
            QPushButton#cancel_button {
                background-color: #888;
            }
            QPushButton#cancel_button:hover {
                background-color: #999;
            }
        """)
        self.cancel_button.setObjectName("cancel_button")

    def validate_and_accept(self):
        """Validate input and accept the dialog."""
        # Check required fields
        if not self.name_input.text().strip():
            self.name_input.setFocus()
            return

        if not self.address_input.text().strip():
            self.address_input.setFocus()
            return

        self.accept()

    def get_config_data(self):
        """Get the configuration data from the dialog."""
        return {
            'name': self.name_input.text().strip(),
            'address': self.address_input.text().strip(),
            'port': self.port_input.value() if self.port_input.value() != 23 else 23,
            'username': self.username_input.text().strip(),
            'password': self.password_input.text()
        }
