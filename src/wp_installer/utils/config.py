#!/usr/bin/env python3
"""
Configuration management for WordPress Auto Installer
Handles loading, saving, and managing configuration settings
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from .logger import logger

class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # Use path utils to get correct path for both dev and executable
            from .paths import PathUtils
            config_dir = PathUtils.get_app_data_dir("config")
            config_file = config_dir / "wp_installer_config.yaml"
        
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'xampp': {
                'htdocs_path': 'C:/xampp/htdocs',  # Adjust for your XAMPP installation
                'mysql_user': 'root',
                'mysql_password': '',  # Default XAMPP MySQL password is empty
                'mysql_host': 'localhost'
            },
            'wordpress': {
                'admin_user': 'admin',
                'admin_password': 'admin123',
                'admin_email': 'admin@localhost.com',
                'site_title_prefix': 'WP Test Site',
                'base_url': 'http://localhost',
                'zip_path': 'assets/wordpress-6.8.2.zip'  # Relative to app base directory
            },
            'instances': {
                'prefix': 'wp_test_',
                'max_instances': 50
            },
            'logging': {
                'level': 'INFO',
                'file': 'wp_installer.log'
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = self.get_default_config()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.success(f"Loaded configuration from {self.config_file}")
                
                # Merge with defaults for any missing keys
                merged_config = self._merge_configs(default_config, config)
                return merged_config
                
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                logger.info("Using default configuration...")
        else:
            # Create default config file
            self.save_config(default_config)
            logger.success(f"Created default config file: {self.config_file}")
            logger.info("Please review and modify the configuration as needed.")
            
        return default_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        try:
            config_to_save = config if config is not None else self.config
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
            
            if config is not None:
                self.config = config
            
            logger.success(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'xampp.mysql_user')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config
        
        try:
            # Navigate to the parent key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the final value
            config[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config value {key_path}: {e}")
            return False
    
    def validate_config(self) -> tuple[bool, list]:
        """Validate configuration and return (is_valid, errors)"""
        errors = []
        
        # Check required paths
        htdocs_path = Path(self.get('xampp.htdocs_path', ''))
        if not htdocs_path.exists():
            errors.append(f"htdocs path does not exist: {htdocs_path}")
        
        # Check required fields
        required_fields = [
            'xampp.mysql_user',
            'xampp.mysql_host',
            'wordpress.admin_user',
            'wordpress.admin_password',
            'wordpress.admin_email',
            'instances.prefix'
        ]
        
        for field in required_fields:
            if not self.get(field):
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Check email format (basic)
        admin_email = self.get('wordpress.admin_email', '')
        if admin_email and '@' not in admin_email:
            errors.append("Admin email format is invalid")
        
        # Check max instances
        max_instances = self.get('instances.max_instances', 0)
        if not isinstance(max_instances, int) or max_instances <= 0:
            errors.append("Max instances must be a positive integer")
        
        return len(errors) == 0, errors
    
    def export_config(self, file_path: str) -> bool:
        """Export current configuration to a file"""
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.success(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False

    def get_config_text(self) -> str:
        """Get current configuration as YAML text"""
        try:
            return yaml.dump(self.config, default_flow_style=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to get configuration text: {e}")
            return ""
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file"""
        try:
            import_path = Path(file_path)
            if not import_path.exists():
                logger.error(f"Config file not found: {import_path}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = yaml.safe_load(f)
            
            # Validate imported config
            old_config = self.config
            self.config = imported_config
            is_valid, errors = self.validate_config()
            
            if not is_valid:
                self.config = old_config
                logger.error("Imported configuration is invalid:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            logger.success(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False

# Global config manager instance
config_manager = ConfigManager()
