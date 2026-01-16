#!/usr/bin/env python3
"""
KDE BBS Client - A modern KDE client for old school telnet based BBS systems.
"""

import sys

from PySide6.QtWidgets import QApplication

from config import ConfigManager
from ui.bbs_chooser import BBSChooser
from ui.config_dialog import ConfigDialog


class KDEBBSClient:
    """Main application class for the KDE BBS Client."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("KDE BBS Client")
        self.app.setOrganizationName("KDEBBSClient")

    def run(self):
        """Run the application."""
        # Check if configuration exists
        if not self.config_manager.config_exists():
            # Show configuration dialog
            config_dialog = ConfigDialog()
            if config_dialog.exec():
                # User submitted configuration
                config_data = config_dialog.get_config_data()
                self.config_manager.save_config(config_data)
            else:
                # User cancelled
                return 0

        # Load configuration
        config = self.config_manager.load_config()

        # Show BBS chooser
        bbs_chooser = BBSChooser(config, self.config_manager)
        bbs_chooser.show()

        return self.app.exec()


def main():
    """Application entry point."""
    client = KDEBBSClient()
    sys.exit(client.run())


if __name__ == '__main__':
    main()
