"""
Terminal window for displaying BBS output and handling user input.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
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

    def __init__(self, bbs_data, config_manager=None):
        """Initialize the terminal window."""
        super().__init__()
        self.bbs_data = bbs_data
        self.config_manager = config_manager
        self.telnet_client = None
        self.ansi_parser = ANSIParser()

        # Load font size from config or use default
        if self.config_manager:
            self.font_size = self.config_manager.get_font_size()
        else:
            self.font_size = 10  # Default fallback

        # Load window size from config or use default
        if self.config_manager:
            self.window_width, self.window_height = self.config_manager.get_window_size()
        else:
            self.window_width, self.window_height = 1024, 768  # Default fallback

        # Cursor state
        self.cursor_visible = True
        self.cursor_char = '\u2588'  # Full block character (█)

        self.setWindowTitle(f"KDE BBS Client - {bbs_data.get('name', 'BBS')}")
        self.setMinimumSize(400, 300)
        self.resize(self.window_width, self.window_height)

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

        # Set monospace font with configured size
        font = QFont("Monospace", self.font_size)
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

        # Set up blinking cursor timer
        self.cursor_timer = QTimer(self)
        self.cursor_timer.timeout.connect(self._toggle_cursor)
        self.cursor_timer.start(500)  # Blink every 500ms

        # Draw initial cursor
        self._draw_cursor()

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

        # Ask user if they want to close the window
        reply = QMessageBox.question(
            self,
            "Connection Closed",
            "The BBS connection has been closed. Do you want to close this window?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.close()

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
        # Remove cursor before adding text
        self._remove_cursor()

        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Process control characters and collect text segments
        i = 0
        current_segment = ""

        while i < len(text):
            char = text[i]

            if char == '\x08':  # Backspace (BS)
                # First, insert any pending text
                if current_segment:
                    self._insert_with_ansi(cursor, current_segment)
                    current_segment = ""
                # Delete the previous character
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.deletePreviousChar()
                i += 1
            elif char == '\x7f':  # DEL - treat same as backspace
                if current_segment:
                    self._insert_with_ansi(cursor, current_segment)
                    current_segment = ""
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.deletePreviousChar()
                i += 1
            elif char == '\r':  # Carriage return
                # Check if followed by LF (CR+LF is common line ending)
                if i + 1 < len(text) and text[i + 1] == '\n':
                    # CR+LF - treat as single newline
                    current_segment += '\n'
                    i += 2
                else:
                    # Lone CR - treat as newline (common in old BBS systems)
                    current_segment += '\n'
                    i += 1
            elif char == '\n':  # Newline (LF)
                current_segment += '\n'
                i += 1
            else:
                current_segment += char
                i += 1

        # Insert any remaining text
        if current_segment:
            self._insert_with_ansi(cursor, current_segment)

        # Scroll to bottom
        self.terminal_display.setTextCursor(cursor)
        self.terminal_display.ensureCursorVisible()

        # Redraw cursor after adding text
        self._draw_cursor()

    def _insert_with_ansi(self, cursor, text):
        """Insert text with ANSI color parsing."""
        segments = self.ansi_parser.parse(text)
        for segment_text, text_format in segments:
            # Ensure the text format uses the current font size
            font = text_format.font()
            font.setPointSize(self.font_size)
            font.setFamily("Monospace")
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            text_format.setFont(font)
            cursor.setCharFormat(text_format)
            cursor.insertText(segment_text)

    def _toggle_cursor(self):
        """Toggle cursor visibility for blinking effect."""
        self.cursor_visible = not self.cursor_visible
        self._update_cursor_display()

    def _draw_cursor(self):
        """Draw the cursor at the current position."""
        if self.cursor_visible:
            self._update_cursor_display()

    def _update_cursor_display(self):
        """Update the cursor display based on visibility state."""
        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Check if there's already a cursor character at the end
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)
        selected_text = cursor.selectedText()

        if selected_text == self.cursor_char:
            # Remove existing cursor
            cursor.removeSelectedText()

        # Move to end
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Add cursor if visible
        if self.cursor_visible:
            # Create cursor format - bright green block on black
            cursor_format = QTextCharFormat()
            cursor_format.setForeground(QColor(0, 255, 0))  # Bright green
            cursor_format.setBackground(QColor(0, 255, 0))  # Green background for solid block

            font = QFont("Monospace", self.font_size)
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            cursor_format.setFont(font)

            cursor.setCharFormat(cursor_format)
            cursor.insertText(self.cursor_char)

        self.terminal_display.setTextCursor(cursor)

    def _remove_cursor(self):
        """Remove the cursor character from the display."""
        cursor = self.terminal_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 1)

        if cursor.selectedText() == self.cursor_char:
            cursor.removeSelectedText()

        self.terminal_display.setTextCursor(cursor)

    def eventFilter(self, obj, event):
        """Filter events to capture key presses for character-by-character input."""
        if obj == self.terminal_display and event.type() == event.Type.KeyPress:
            # Check for font size shortcuts first (work regardless of connection)
            if self._handle_font_size_shortcut(event):
                return True
            # Check for clipboard shortcuts (work regardless of connection)
            if self._handle_clipboard_shortcut(event):
                return True
            # Then handle BBS input if connected
            if self.telnet_client and self.telnet_client.running:
                return self.handle_key_press(event)
        return super().eventFilter(obj, event)

    def _handle_font_size_shortcut(self, event):
        """Handle font size keyboard shortcuts. Returns True if handled."""
        modifiers = event.modifiers()
        key = event.key()

        # Check for Ctrl modifier
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
                # Ctrl+Plus or Ctrl+= to increase font size
                self.increase_font_size()
                return True
            elif key == Qt.Key.Key_Minus:
                # Ctrl+Minus to decrease font size
                self.decrease_font_size()
                return True
            elif key == Qt.Key.Key_0:
                # Ctrl+0 to reset font size
                self.reset_font_size()
                return True

        return False

    def increase_font_size(self):
        """Increase the terminal font size."""
        if self.config_manager:
            new_size = min(self.font_size + 2, self.config_manager.MAX_FONT_SIZE)
        else:
            new_size = min(self.font_size + 2, 48)

        if new_size != self.font_size:
            self._set_font_size(new_size)

    def decrease_font_size(self):
        """Decrease the terminal font size."""
        if self.config_manager:
            new_size = max(self.font_size - 2, self.config_manager.MIN_FONT_SIZE)
        else:
            new_size = max(self.font_size - 2, 6)

        if new_size != self.font_size:
            self._set_font_size(new_size)

    def reset_font_size(self):
        """Reset font size to default."""
        if self.config_manager:
            default_size = self.config_manager.DEFAULT_FONT_SIZE
        else:
            default_size = 10

        if default_size != self.font_size:
            self._set_font_size(default_size)

    def _set_font_size(self, size):
        """Set the font size and update the display."""
        self.font_size = size

        # Update the font on the terminal display
        font = self.terminal_display.font()
        font.setPointSize(size)
        self.terminal_display.setFont(font)

        # Save to config
        if self.config_manager:
            self.config_manager.set_font_size(size)

        # Show feedback in status bar
        self.status_bar.showMessage(f"Font size: {size}pt", 2000)

    def _handle_clipboard_shortcut(self, event):
        """Handle clipboard keyboard shortcuts. Returns True if handled."""
        modifiers = event.modifiers()
        key = event.key()

        # Check for Ctrl modifier
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Shift+C or Ctrl+C for copy
            if key == Qt.Key.Key_C:
                self.copy_to_clipboard()
                return True
            # Ctrl+Shift+V or Ctrl+V for paste
            elif key == Qt.Key.Key_V:
                self.paste_from_clipboard()
                return True
            # Ctrl+X for cut (behaves like copy in terminal)
            elif key == Qt.Key.Key_X:
                self.copy_to_clipboard()
                return True

        return False

    def copy_to_clipboard(self):
        """Copy selected text to clipboard."""
        cursor = self.terminal_display.textCursor()
        selected_text = cursor.selectedText()

        if selected_text:
            # QTextEdit uses Unicode paragraph separator (U+2029) for line breaks
            # Convert them to regular newlines
            selected_text = selected_text.replace('\u2029', '\n')

            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
            self.status_bar.showMessage("Copied to clipboard", 2000)
        else:
            self.status_bar.showMessage("No text selected", 2000)

    def paste_from_clipboard(self):
        """Paste clipboard contents to the BBS."""
        if not self.telnet_client or not self.telnet_client.running:
            self.status_bar.showMessage("Not connected - cannot paste", 2000)
            return

        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if text:
            # Convert newlines to carriage returns for BBS compatibility
            text = text.replace('\r\n', '\r').replace('\n', '\r')

            # Send each character to the BBS
            for char in text:
                self.telnet_client.send_data(char)

            self.status_bar.showMessage(f"Pasted {len(text)} characters", 2000)
        else:
            self.status_bar.showMessage("Clipboard is empty", 2000)

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

    def resizeEvent(self, event):
        """Handle window resize event and save new size."""
        super().resizeEvent(event)
        # Save the new window size to config
        if self.config_manager:
            new_size = event.size()
            self.config_manager.set_window_size(new_size.width(), new_size.height())

    def closeEvent(self, event):
        """Handle window close event."""
        self.cursor_timer.stop()  # Stop cursor blinking
        if self.telnet_client and self.telnet_client.running:
            self.telnet_client.disconnect()
            self.telnet_client.wait(1000)
        event.accept()
