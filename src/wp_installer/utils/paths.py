#!/usr/bin/env python3
"""
Path utilities for WordPress Auto Installer
Handles application directory resolution for both development and executable environments
"""

import sys
from pathlib import Path

class PathUtils:
    @staticmethod
    def get_app_base_dir() -> Path:
        """Get the application base directory for both development and executable environments"""
        if getattr(sys, 'frozen', False):
            # Running as executable
            return Path(sys.executable).parent
        else:
            # Running in development
            return Path(__file__).parent.parent.parent.parent
    
    @staticmethod
    def get_app_data_dir(folder_name: str) -> Path:
        """Get application data directory (config, assets, logs) with fallback creation"""
        base_dir = PathUtils.get_app_base_dir()
        data_dir = base_dir / folder_name
        data_dir.mkdir(exist_ok=True)
        return data_dir
    
    @staticmethod
    def make_relative_to_app(absolute_path: str) -> str:
        """Convert absolute path to relative path from app base directory"""
        try:
            abs_path = Path(absolute_path)
            base_dir = PathUtils.get_app_base_dir()
            
            # If the path is already inside the app directory, make it relative
            if abs_path.is_relative_to(base_dir):
                return str(abs_path.relative_to(base_dir))
            else:
                # If it's outside the app directory, keep it absolute
                return str(abs_path)
        except (ValueError, TypeError):
            return str(absolute_path)
    
    @staticmethod
    def resolve_app_path(path: str) -> Path:
        """Resolve a path that may be relative to the app base directory"""
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        else:
            # Relative to app base directory
            return PathUtils.get_app_base_dir() / path
