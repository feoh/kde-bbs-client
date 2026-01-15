"""
Configuration management for KDE BBS Client.
"""

from pathlib import Path

import yaml


class ConfigManager:
    """Manages configuration file reading and writing."""

    def __init__(self):
        """Initialize the configuration manager."""
        self.config_dir = Path.home() / '.config' / 'kdebbsclient'
        self.config_file = self.config_dir / 'client-config.yaml'

    def config_exists(self) -> bool:
        """Check if the configuration file exists."""
        return self.config_file.exists()

    def load_config(self) -> dict:
        """Load configuration from the YAML file."""
        if not self.config_exists():
            return {'bbs_systems': []}

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
                return config if config else {'bbs_systems': []}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {'bbs_systems': []}

    def save_config(self, config_data: dict) -> None:
        """Save configuration to the YAML file."""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing config if it exists
        existing_config = self.load_config()

        # If this is new BBS data from the dialog, add it to the list
        if 'name' in config_data and 'address' in config_data:
            # This is a single BBS entry from the config dialog
            bbs_entry = {
                'name': config_data['name'],
                'address': config_data['address'],
                'port': config_data.get('port', 23),
                'username': config_data.get('username', ''),
                'password': config_data.get('password', '')
            }

            # Add to existing systems if not already present
            if 'bbs_systems' not in existing_config:
                existing_config['bbs_systems'] = []

            # Check if this BBS already exists (by name and address)
            exists = False
            for idx, system in enumerate(existing_config['bbs_systems']):
                name_match = system['name'] == bbs_entry['name']
                address_match = system['address'] == bbs_entry['address']
                if name_match and address_match:
                    # Update existing entry
                    existing_config['bbs_systems'][idx] = bbs_entry
                    exists = True
                    break

            if not exists:
                existing_config['bbs_systems'].append(bbs_entry)

            config_to_save = existing_config
        else:
            # This is a full config update
            config_to_save = config_data

        # Write to file
        try:
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(config_to_save, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error saving config: {e}")
            raise

    def add_bbs_system(self, name: str, address: str, port: int = 23,
                       username: str = '', password: str = '') -> None:
        """Add a new BBS system to the configuration."""
        config_data = {
            'name': name,
            'address': address,
            'port': port,
            'username': username,
            'password': password
        }
        self.save_config(config_data)

    def get_bbs_systems(self) -> list[dict]:
        """Get list of configured BBS systems."""
        config = self.load_config()
        return config.get('bbs_systems', [])
