# KDE BBS Client Usage Guide

## Installation

### Prerequisites

- Python 3.10 or higher
- uv package manager ([installation instructions](https://github.com/astral-sh/uv))

### Setup

1. Clone or download this repository
2. Run the setup script:
   ```bash
   ./setup.sh
   ```

This will install all required dependencies using uv.

## Running the Application

### Quick Start

Simply run:
```bash
./run.sh
```

Or manually with uv:
```bash
uv run python kdebbsclient.py
```

## First Run

On first launch, if no configuration file exists, you'll see a configuration dialog where you can enter:

- **BBS Name**: A friendly name for the BBS (e.g., "My Favorite BBS")
- **BBS Address**: The hostname or IP address (e.g., "bbs.example.com" or "192.168.1.100")
- **Port**: The telnet port (default is 23)
- **Username**: Your username for the BBS
- **Password**: Your password (hidden on entry)

Click **Submit** to save the configuration.

## Main Window - BBS Chooser

After initial configuration, the BBS Chooser window displays:

- A list of all configured BBS systems showing name and address
- **Add New BBS** button - Add another BBS to your collection
- **Connect** button - Connect to the selected BBS

## Terminal Window

Once connected:

- The main text area displays output from the BBS
- Type your input in the text field at the bottom
- Press Enter to send your input
- Arrow keys (↑ ↓ ← →) work for navigation in BBS menus
- The status bar shows connection status

## Configuration File

The configuration is stored at:
```
$HOME/.config/kdebbsclient/client-config.yaml
```

You can manually edit this file to add or modify BBS systems. Example format:

```yaml
bbs_systems:
  - name: Example BBS
    address: bbs.example.com
    port: 23
    username: myusername
    password: mypassword
  - name: Another BBS
    address: 192.168.1.100
    port: 2323
    username: user2
    password: pass2
```

## Development

### Code Checking

Run ruff to check code quality:
```bash
uv run ruff check .
```

Auto-fix issues:
```bash
uv run ruff check --fix .
```

### Project Structure

```
kde-bbs-client/
├── kdebbsclient.py      # Main application entry point
├── config.py            # Configuration file management
├── telnet_client.py     # Telnet connection handler
├── ui/
│   ├── config_dialog.py    # Initial setup dialog
│   ├── bbs_chooser.py      # BBS selection window
│   └── terminal_window.py  # Main terminal interface
├── pyproject.toml       # Project configuration
├── setup.sh            # Setup script
└── run.sh              # Run script
```

## Troubleshooting

### Connection Issues

- **Connection timeout**: Check that the BBS address and port are correct
- **Connection refused**: The BBS server may be down or blocking connections
- **Could not resolve hostname**: Check your internet connection and DNS settings

### Display Issues

- If characters look garbled, the BBS may be using a different character encoding
- ANSI color codes are not yet supported (planned feature)

## Planned Features

- ANSI color code support for enhanced BBS graphics
- Auto-detection of post creation to spawn external editor ($EDITOR)
- SSH support in addition to telnet
- Session logging
- Macros and hotkeys
