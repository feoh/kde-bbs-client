"""
Terminal window for displaying BBS output and handling user input.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ansi_parser import ANSIParser
from telnet_client import TelnetClient


class TerminalWindow(QMainWindow):
    """Main terminal window for BBS interaction."""

    def __init__(self, bbs_data):
        """Initialize the terminal window."""
        super().__init__()
        self.bbs_data = bbs_data
        self.telnet_client = None
        self.ansi_parser = ANSIParser()

        self.setWindowTitle(f"KDE BBS Client - {bbs_data.get('name', 'BBS')}")
        self.setMinimumSize(800, 600)

        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Terminal display (read-only text area)
        self.terminal_display = QTextEdit()
        self.terminal_display.setReadOnly(True)
        self.terminal_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.terminal_display.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Set monospace font
        font = QFont("Monospace", 10)
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        self.terminal_display.setFont(font)

        # Install event filter to capture key presses
        self.terminal_display.installEventFilter(self)

        layout.addWidget(self.terminal_display)

        central_widget.setLayout(layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to connect")

        # Apply styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                border: none;
                font-family: monospace;
            }
            QStatusBar {
                background-color: #2a2a2a;
                color: #ccc;
            }
        """)

        # Set default text format for the terminal
        self.terminal_display.setTextColor(self.ansi_parser.current_format.foreground().color())

    def connect_to_bbs(self):
        """Establish connection to the BBS."""
        host = self.bbs_data.get('address')
        port = self.bbs_data.get('port', 23)
        username = self.bbs_data.get('username', '')
        password = self.bbs_data.get('password', '')

        if not host:
            QMessageBox.critical(self, "Error", "No host address specified")
            return

        self.status_bar.showMessage(f"Connecting to {host}:{port}...")
        self.append_to_display(f"Connecting to {host}:{port}...\n")

        # Create telnet client
        self.telnet_client = TelnetClient(host, port, username, password)
        self.telnet_client.data_received.connect(self.handle_data_received)
        self.telnet_client.connection_established.connect(self.handle_connection_established)
        self.telnet_client.connection_error.connect(self.handle_connection_error)
        self.telnet_client.connection_closed.connect(self.handle_connection_closed)

        # Start connection
        self.telnet_client.start()

    def handle_connection_established(self):
        """Handle successful connection."""
        self.status_bar.showMessage("Connected")
        self.append_to_display("Connected!\n")
        self.terminal_display.setFocus()

    def handle_connection_error(self, error_msg):
        """Handle connection error."""
        self.status_bar.showMessage(f"Error: {error_msg}")
        self.append_to_display(f"\nError: {error_msg}\n")
        QMessageBox.critical(self, "Connection Error", error_msg)

    def handle_connection_closed(self):
        """Handle connection closure."""
        self.status_bar.showMessage("Disconnected")
        self.append_to_display("\nConnection closed.\n")

    def handle_data_received(self, data):
        """Handle data received from the BBS."""
        try:
            # Try to decode as UTF-8, fall back to latin-1 if it fails
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                text = data.decode('latin-1', errors='replace')

            self.append_to_display(text)
        except Exception as e:
            self.append_to_display(f"\n[Error displaying data: {str(e)}]\n")

    def append_to_display(self, text):
        """Append text to the terminal display with ANSI color support."""
        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Parse ANSI codes and get formatted segments
        segments = self.ansi_parser.parse(text)

        # Insert each segment with its formatting
        for segment_text, text_format in segments:
            cursor.setCharFormat(text_format)
            cursor.insertText(segment_text)

        # Scroll to bottom
        self.terminal_display.setTextCursor(cursor)
        self.terminal_display.ensureCursorVisible()

    def eventFilter(self, obj, event):
        """Filter events to capture key presses for character-by-character input."""
        if obj == self.terminal_display and event.type() == event.Type.KeyPress:
            if self.telnet_client and self.telnet_client.running:
                return self.handle_key_press(event)
        return super().eventFilter(obj, event)

    def handle_key_press(self, event):
        """Handle key press events and send to BBS."""
        key = event.key()
        text = event.text()

        # Handle special keys
        if key == Qt.Key.Key_Up:
            self.telnet_client.send_data(b'\x1b[A')
            return True
        elif key == Qt.Key.Key_Down:
            self.telnet_client.send_data(b'\x1b[B')
            return True
        elif key == Qt.Key.Key_Right:
            self.telnet_client.send_data(b'\x1b[C')
            return True
        elif key == Qt.Key.Key_Left:
            self.telnet_client.send_data(b'\x1b[D')
            return True
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            self.telnet_client.send_data('\r')
            return True
        elif key == Qt.Key.Key_Backspace:
            # Try sending ctrl+H (BS) - many BBS systems expect this
            # Some systems expect 0x7F (DEL), but 0x08 (BS) is more common for BBS
            self.telnet_client.send_data(b'\x08')
            return True
        elif key == Qt.Key.Key_Tab:
            self.telnet_client.send_data(b'\t')
            return True
        elif key == Qt.Key.Key_Escape:
            self.telnet_client.send_data(b'\x1b')
            return True
        elif key == Qt.Key.Key_Delete:
            self.telnet_client.send_data(b'\x1b[3~')
            return True
        elif key == Qt.Key.Key_Home:
            self.telnet_client.send_data(b'\x1b[H')
            return True
        elif key == Qt.Key.Key_End:
            self.telnet_client.send_data(b'\x1b[F')
            return True
        elif key == Qt.Key.Key_PageUp:
            self.telnet_client.send_data(b'\x1b[5~')
            return True
        elif key == Qt.Key.Key_PageDown:
            self.telnet_client.send_data(b'\x1b[6~')
            return True
        elif text and len(text) == 1:
            # Send any printable character
            self.telnet_client.send_data(text)
            return True

        return False

    def closeEvent(self, event):
        """Handle window close event."""
        if self.telnet_client and self.telnet_client.running:
            self.telnet_client.disconnect()
            self.telnet_client.wait(1000)
        event.accept()
