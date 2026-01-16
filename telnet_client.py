"""
Telnet client for BBS connections.
"""

import socket

from PySide6.QtCore import QThread, Signal


class TelnetClient(QThread):
    """Telnet client that runs in a separate thread."""

    # Signals
    data_received = Signal(bytes)
    connection_established = Signal()
    connection_error = Signal(str)
    connection_closed = Signal()

    # Telnet protocol commands
    IAC = bytes([255])  # Interpret As Command
    DONT = bytes([254])
    DO = bytes([253])
    WONT = bytes([252])
    WILL = bytes([251])
    SB = bytes([250])  # Subnegotiation Begin
    SE = bytes([240])  # Subnegotiation End

    def __init__(self, host, port, username='', password=''):
        """Initialize the telnet client."""
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sock = None
        self.running = False

    def run(self):
        """Run the telnet connection in a separate thread."""
        try:
            # Establish connection
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(0.1)  # Non-blocking reads with short timeout
            self.running = True
            self.connection_established.emit()

            # Buffer for incomplete telnet sequences
            buffer = b''

            # Read data continuously
            while self.running:
                try:
                    data = self.sock.recv(4096)
                    if not data:
                        # Connection closed by remote host
                        break

                    buffer += data
                    # Process telnet commands
                    processed_data, buffer = self._process_telnet_data(buffer)

                    if processed_data:
                        self.data_received.emit(processed_data)

                except TimeoutError:
                    # No data available, continue
                    self.msleep(10)
                    continue
                except BlockingIOError:
                    # No data available (non-blocking)
                    self.msleep(10)
                    continue
                except OSError as e:
                    if self.running:
                        self.connection_error.emit(f"Error reading data: {str(e)}")
                    break
                except Exception as e:
                    if self.running:
                        self.connection_error.emit(f"Error reading data: {str(e)}")
                    break

        except TimeoutError:
            self.connection_error.emit("Connection timeout")
        except socket.gaierror:
            self.connection_error.emit("Could not resolve hostname")
        except ConnectionRefusedError:
            self.connection_error.emit("Connection refused")
        except Exception as e:
            self.connection_error.emit(f"Connection error: {str(e)}")
        finally:
            self.running = False
            self.connection_closed.emit()

    def _process_telnet_data(self, data):
        """Process telnet protocol commands and return clean data."""
        result = b''
        i = 0
        while i < len(data):
            if data[i:i+1] == self.IAC:
                if i + 1 >= len(data):
                    # Incomplete IAC sequence, keep in buffer
                    return result, data[i:]

                cmd = data[i+1:i+2]
                if cmd == self.IAC:
                    # Escaped IAC (255), add literal 255 to output
                    result += self.IAC
                    i += 2
                elif cmd in (self.DO, self.DONT, self.WILL, self.WONT):
                    if i + 2 >= len(data):
                        # Incomplete sequence, keep in buffer
                        return result, data[i:]
                    # Respond to telnet negotiations
                    option = data[i+2:i+3]
                    self._handle_telnet_command(cmd, option)
                    i += 3
                elif cmd == self.SB:
                    # Subnegotiation - find SE
                    se_pos = data.find(self.IAC + self.SE, i)
                    if se_pos == -1:
                        # Incomplete subnegotiation, keep in buffer
                        return result, data[i:]
                    i = se_pos + 2
                else:
                    # Unknown command, skip
                    i += 2
            else:
                result += data[i:i+1]
                i += 1

        return result, b''

    def _handle_telnet_command(self, cmd, option):
        """Handle telnet protocol negotiation."""
        try:
            if cmd == self.DO:
                # Server asks us to enable an option - we refuse most
                self.sock.sendall(self.IAC + self.WONT + option)
            elif cmd == self.DONT:
                # Server asks us to disable an option - acknowledge
                self.sock.sendall(self.IAC + self.WONT + option)
            elif cmd == self.WILL:
                # Server will enable an option - acknowledge
                self.sock.sendall(self.IAC + self.DO + option)
            elif cmd == self.WONT:
                # Server won't enable an option - acknowledge
                self.sock.sendall(self.IAC + self.DONT + option)
        except Exception:
            # Ignore errors in telnet negotiation
            pass

    def send_data(self, data):
        """Send data to the telnet connection."""
        if self.sock and self.running:
            try:
                if isinstance(data, str):
                    data = data.encode('utf-8')
                self.sock.sendall(data)
            except Exception as e:
                self.connection_error.emit(f"Error sending data: {str(e)}")

    def disconnect(self):
        """Disconnect from the telnet connection."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
