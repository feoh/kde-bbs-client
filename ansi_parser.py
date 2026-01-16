"""
ANSI escape sequence parser for terminal color and formatting support.
"""

import re

from PySide6.QtGui import QColor, QTextCharFormat


class ANSIParser:
    """Parse ANSI escape sequences and convert to Qt text formats."""

    # ANSI color codes to RGB values
    ANSI_COLORS = {
        # Standard colors (30-37 foreground, 40-47 background)
        0: QColor(0, 0, 0),          # Black
        1: QColor(170, 0, 0),        # Red
        2: QColor(0, 170, 0),        # Green
        3: QColor(170, 85, 0),       # Yellow
        4: QColor(0, 0, 170),        # Blue
        5: QColor(170, 0, 170),      # Magenta
        6: QColor(0, 170, 170),      # Cyan
        7: QColor(170, 170, 170),    # White/Gray
        # Bright colors (90-97 foreground, 100-107 background)
        8: QColor(85, 85, 85),       # Bright Black (Gray)
        9: QColor(255, 85, 85),      # Bright Red
        10: QColor(85, 255, 85),     # Bright Green
        11: QColor(255, 255, 85),    # Bright Yellow
        12: QColor(85, 85, 255),     # Bright Blue
        13: QColor(255, 85, 255),    # Bright Magenta
        14: QColor(85, 255, 255),    # Bright Cyan
        15: QColor(255, 255, 255),   # Bright White
    }

    def __init__(self):
        """Initialize the ANSI parser."""
        self.reset()
        # Regex to match ANSI escape sequences
        self.ansi_escape = re.compile(r'\x1b\[([0-9;]+)?m')

    def reset(self):
        """Reset formatting to defaults."""
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor(0, 255, 0))  # Default green
        self.current_format.setBackground(QColor(0, 0, 0))    # Default black
        self.bold = False
        self.underline = False

    def parse(self, text):
        """
        Parse text with ANSI codes and return list of (text, format) tuples.

        Args:
            text: String potentially containing ANSI escape sequences

        Returns:
            List of tuples: [(text_segment, QTextCharFormat), ...]
        """
        result = []
        last_pos = 0

        for match in self.ansi_escape.finditer(text):
            # Add text before this escape sequence
            if match.start() > last_pos:
                segment = text[last_pos:match.start()]
                result.append((segment, QTextCharFormat(self.current_format)))

            # Process the ANSI code
            codes = match.group(1)
            if codes:
                self._process_codes(codes)
            else:
                # Empty code means reset
                self.reset()

            last_pos = match.end()

        # Add remaining text
        if last_pos < len(text):
            segment = text[last_pos:]
            result.append((segment, QTextCharFormat(self.current_format)))

        return result if result else [(text, QTextCharFormat(self.current_format))]

    def _process_codes(self, codes_str):
        """Process ANSI code string and update current format."""
        codes = [int(c) for c in codes_str.split(';') if c]

        i = 0
        while i < len(codes):
            code = codes[i]

            if code == 0:
                # Reset all attributes
                self.reset()
            elif code == 1:
                # Bold/bright
                self.bold = True
                font = self.current_format.font()
                font.setBold(True)
                self.current_format.setFont(font)
            elif code == 4:
                # Underline
                self.underline = True
                self.current_format.setFontUnderline(True)
            elif code == 7:
                # Reverse video (swap foreground and background)
                fg = self.current_format.foreground().color()
                bg = self.current_format.background().color()
                self.current_format.setForeground(bg)
                self.current_format.setBackground(fg)
            elif code == 22:
                # Normal intensity (not bold)
                self.bold = False
                font = self.current_format.font()
                font.setBold(False)
                self.current_format.setFont(font)
            elif code == 24:
                # Not underlined
                self.underline = False
                self.current_format.setFontUnderline(False)
            elif 30 <= code <= 37:
                # Foreground color
                color_index = code - 30
                if self.bold:
                    color_index += 8  # Use bright variant
                self.current_format.setForeground(self.ANSI_COLORS[color_index])
            elif code == 38:
                # Extended foreground color (256-color or RGB)
                i = self._process_extended_color(codes, i, True)
            elif code == 39:
                # Default foreground color
                self.current_format.setForeground(QColor(0, 255, 0))
            elif 40 <= code <= 47:
                # Background color
                color_index = code - 40
                self.current_format.setBackground(self.ANSI_COLORS[color_index])
            elif code == 48:
                # Extended background color (256-color or RGB)
                i = self._process_extended_color(codes, i, False)
            elif code == 49:
                # Default background color
                self.current_format.setBackground(QColor(0, 0, 0))
            elif 90 <= code <= 97:
                # Bright foreground colors
                color_index = code - 90 + 8
                self.current_format.setForeground(self.ANSI_COLORS[color_index])
            elif 100 <= code <= 107:
                # Bright background colors
                color_index = code - 100 + 8
                self.current_format.setBackground(self.ANSI_COLORS[color_index])

            i += 1

    def _process_extended_color(self, codes, index, is_foreground):
        """
        Process extended color codes (38 or 48).

        Returns the new index position after processing.
        """
        if index + 1 >= len(codes):
            return index

        color_type = codes[index + 1]

        if color_type == 5:
            # 256-color mode
            if index + 2 < len(codes):
                color_index = codes[index + 2]
                color = self._get_256_color(color_index)
                if is_foreground:
                    self.current_format.setForeground(color)
                else:
                    self.current_format.setBackground(color)
                return index + 2
        elif color_type == 2:
            # RGB mode
            if index + 4 < len(codes):
                r = codes[index + 2]
                g = codes[index + 3]
                b = codes[index + 4]
                color = QColor(r, g, b)
                if is_foreground:
                    self.current_format.setForeground(color)
                else:
                    self.current_format.setBackground(color)
                return index + 4

        return index + 1

    def _get_256_color(self, index):
        """Convert 256-color palette index to QColor."""
        if index < 16:
            # Use standard colors
            return self.ANSI_COLORS[index]
        elif index < 232:
            # 216-color cube (6x6x6)
            index -= 16
            r = (index // 36) * 51
            g = ((index % 36) // 6) * 51
            b = (index % 6) * 51
            return QColor(r, g, b)
        else:
            # Grayscale ramp
            gray = 8 + (index - 232) * 10
            return QColor(gray, gray, gray)
