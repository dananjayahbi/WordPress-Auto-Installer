#!/usr/bin/env python3
"""
Logging module for WordPress Auto Installer
Provides consistent logging across all modules
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import threading
import os

class Logger:
    def __init__(self, log_file=None):
        if log_file is None:
            # Use path utils to get correct path for both dev and executable
            from .paths import PathUtils
            logs_dir = PathUtils.get_app_data_dir("logs")
            log_file = logs_dir / "wp_installer.log"
        
        self.log_file = Path(log_file)
        self.gui_callback = None
        self.lock = threading.Lock()
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Setup root logger
        self.logger = logging.getLogger('wp_installer')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(console_handler)
    
    def set_gui_callback(self, callback):
        """Set callback function for GUI logging"""
        with self.lock:
            self.gui_callback = callback
    
    def addHandler(self, handler):
        """Add handler to the internal logger"""
        self.logger.addHandler(handler)
    
    def _log_to_gui(self, level, message):
        """Send log message to GUI if callback is set"""
        if self.gui_callback:
            try:
                self.gui_callback(level, message)
            except Exception:
                pass  # Ignore GUI callback errors
    
    def info(self, message):
        """Log info message"""
        with self.lock:
            self.logger.info(message)
            self._log_to_gui('INFO', message)
    
    def success(self, message):
        """Log success message (special info)"""
        formatted_message = f"✓ {message}"
        with self.lock:
            self.logger.info(formatted_message)
            self._log_to_gui('SUCCESS', formatted_message)
    
    def warning(self, message):
        """Log warning message"""
        formatted_message = f"⚠ {message}"
        with self.lock:
            self.logger.warning(formatted_message)
            self._log_to_gui('WARNING', formatted_message)
    
    def error(self, message):
        """Log error message"""
        formatted_message = f"❌ {message}"
        with self.lock:
            self.logger.error(formatted_message)
            self._log_to_gui('ERROR', formatted_message)
    
    def debug(self, message):
        """Log debug message"""
        with self.lock:
            self.logger.debug(message)
            self._log_to_gui('DEBUG', message)
    
    def step(self, message):
        """Log step message (for process steps)"""
        formatted_message = f"🔄 {message}"
        with self.lock:
            self.logger.info(formatted_message)
            self._log_to_gui('STEP', formatted_message)
    
    def progress(self, message):
        """Log progress message"""
        formatted_message = f"📋 {message}"
        with self.lock:
            self.logger.info(formatted_message)
            self._log_to_gui('PROGRESS', formatted_message)
    
    def header(self, message):
        """Log header message (for major sections)"""
        separator = "=" * 50
        formatted_message = f"\n{separator}\n{message}\n{separator}"
        with self.lock:
            self.logger.info(formatted_message)
            self._log_to_gui('HEADER', formatted_message)

# Global logger instance
logger = Logger()
