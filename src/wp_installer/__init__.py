"""
WordPress Auto Installer Package
A comprehensive tool for automating WordPress installation and management
"""

__version__ = "1.0.0"
__author__ = "WordPress Auto Installer Team"
__description__ = "Automated WordPress installation tool for developers"

# Import only the classes, not the instances
from .core.wordpress import WordPressInstaller
from .core.database import DatabaseManager
from .utils.config import ConfigManager, config_manager
from .utils.logger import Logger, logger
from .utils.helpers import Helpers
from .utils.cli import WordPressCLI
from .gui.main_window import MainWindow, run_gui

__all__ = [
    'WordPressInstaller',
    'DatabaseManager',
    'ConfigManager', 'config_manager',
    'Logger', 'logger',
    'Helpers',
    'WordPressCLI',
    'MainWindow', 'run_gui'
]
