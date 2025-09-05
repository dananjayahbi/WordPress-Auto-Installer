#!/usr/bin/env python3
"""
WordPress installation core functionality
Handles WordPress extraction, configuration, and WP-CLI operations
"""

import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from ..utils.logger import logger
from ..utils.config import config_manager
from ..utils.helpers import Helpers
from .database import DatabaseManager

# Import winreg for Windows systems
if sys.platform == "win32":
    import winreg

class WordPressInstaller:
    def __init__(self):
        self.wp_cli_command = None
        self.db_manager = DatabaseManager()
        self._find_wp_cli()
    
    def _find_wp_cli(self) -> None:
        """Find WP-CLI executable"""
        wp_cli_paths = [
            'wp',  # If it's in PATH
            'wp.bat',  # Windows batch file
            'C:/wp-cli/wp-cli.phar',  # Global Windows installation
            'C:/Users/Public/wp-cli.phar',  # Alternative Windows location
            'E:/xampp/htdocs/wp-cli.phar',
            'C:/xampp/htdocs/wp-cli.phar',
            'D:/xampp/htdocs/wp-cli.phar',
            '/usr/local/bin/wp',  # Linux/macOS
            '/opt/lampp/htdocs/wp-cli.phar'  # Linux XAMPP
        ]
        
        # Try to detect WP-CLI from common Windows installation paths
        if sys.platform == "win32":
            try:
                # Check if WP-CLI is in Windows PATH via registry
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
                path_value, _ = winreg.QueryValueEx(key, "PATH")
                winreg.CloseKey(key)
                
                # Check common WP-CLI Windows installation paths
                if 'wp-cli' in path_value.lower():
                    wp_cli_paths.insert(0, 'wp')  # Prioritize system PATH
            except (OSError, FileNotFoundError):
                pass
        
        for wp_path in wp_cli_paths:
            try:
                if wp_path.endswith('.phar'):
                    if sys.platform == "win32":
                        # Use cmd /c for better Windows compatibility
                        result = subprocess.run(['cmd', '/c', 'php', wp_path, '--version'], 
                                              capture_output=True, text=True, shell=False)
                    else:
                        result = subprocess.run(['php', wp_path, '--version'], 
                                              capture_output=True, text=True, shell=False)
                else:
                    if sys.platform == "win32":
                        # Try with cmd /c for Windows PATH resolution
                        result = subprocess.run(['cmd', '/c', wp_path, '--version'], 
                                              capture_output=True, text=True, shell=False)
                    else:
                        result = subprocess.run([wp_path, '--version'], 
                                              capture_output=True, text=True, shell=False)
                
                if result.returncode == 0:
                    logger.success(f"WP-CLI found at: {wp_path}")
                    if wp_path.endswith('.phar'):
                        if sys.platform == "win32":
                            self.wp_cli_command = ['cmd', '/c', 'php', wp_path]
                        else:
                            self.wp_cli_command = ['php', wp_path]
                    else:
                        if sys.platform == "win32":
                            self.wp_cli_command = ['cmd', '/c', wp_path]
                        else:
                            self.wp_cli_command = [wp_path]
                    return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        
        # If not found in common locations, try to auto-detect based on htdocs path
        htdocs_path = Path(config_manager.get('xampp.htdocs_path', ''))
        if htdocs_path.exists():
            wp_cli_phar = htdocs_path / 'wp-cli.phar'
            if wp_cli_phar.exists():
                logger.success(f"WP-CLI found at: {wp_cli_phar}")
                if sys.platform == "win32":
                    self.wp_cli_command = ['cmd', '/c', 'php', str(wp_cli_phar)]
                else:
                    self.wp_cli_command = ['php', str(wp_cli_phar)]
                return
        
        logger.error("WP-CLI not found. Please install WP-CLI or check the configuration.")
        if sys.platform == "win32":
            self.wp_cli_command = ['cmd', '/c', 'wp']  # Fallback to system PATH
        else:
            self.wp_cli_command = ['wp']  # Fallback to system PATH
    
    def test_wp_cli(self) -> tuple[bool, str]:
        """Test WP-CLI availability"""
        try:
            cmd = self.wp_cli_command + ['--version']
            result = subprocess.run(cmd, capture_output=True, text=True, shell=False)
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                logger.success("WP-CLI is working correctly")
                return True, version_info
            else:
                error_msg = result.stderr.strip() or "Unknown WP-CLI error"
                logger.error(f"WP-CLI test failed: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = f"WP-CLI error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def extract_wordpress(self, zip_path: str, site_path: str) -> bool:
        """Extract WordPress from zip file"""
        try:
            logger.step(f"Extracting WordPress to: {site_path}")
            
            if not os.path.exists(zip_path):
                logger.error(f"WordPress zip file not found: {zip_path}")
                return False
            
            # Create site directory if it doesn't exist
            os.makedirs(site_path, exist_ok=True)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(site_path)
                
                # WordPress typically extracts to a 'wordpress' folder
                wordpress_dir = os.path.join(site_path, 'wordpress')
                if os.path.exists(wordpress_dir):
                    # Move all files from wordpress folder to site_path
                    for item in os.listdir(wordpress_dir):
                        src = os.path.join(wordpress_dir, item)
                        dst = os.path.join(site_path, item)
                        if os.path.isdir(src):
                            if os.path.exists(dst):
                                shutil.rmtree(dst)
                            shutil.move(src, dst)
                        else:
                            if os.path.exists(dst):
                                os.remove(dst)
                            shutil.move(src, dst)
                    
                    # Remove the now-empty wordpress directory
                    os.rmdir(wordpress_dir)
            
            logger.success(f"WordPress extracted successfully to {site_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting WordPress: {e}")
            return False
    
    def configure_wordpress(self, site_path: str, db_config: Dict[str, str]) -> bool:
        """Configure WordPress using WP-CLI"""
        try:
            logger.step("Configuring WordPress...")
            
            # Change to site directory
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # Create wp-config.php
                cmd = self.wp_cli_command + [
                    'config', 'create',
                    f'--dbname={db_config["db_name"]}',
                    f'--dbuser={db_config["db_user"]}',
                    f'--dbpass={db_config["db_password"]}',
                    f'--dbhost={db_config["db_host"]}',
                    '--force'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to create wp-config.php: {result.stderr}")
                    return False
                
                logger.success("wp-config.php created successfully")
                return True
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error configuring WordPress: {e}")
            return False
    
    def install_wordpress(self, site_path: str, site_config: Dict[str, str]) -> bool:
        """Install WordPress using WP-CLI"""
        try:
            logger.step("Installing WordPress...")
            
            # Change to site directory
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # Run WordPress installation
                cmd = self.wp_cli_command + [
                    'core', 'install',
                    f'--url={site_config["site_url"]}',
                    f'--title={site_config["site_title"]}',
                    f'--admin_user={site_config["admin_user"]}',
                    f'--admin_password={site_config["admin_password"]}',
                    f'--admin_email={site_config["admin_email"]}'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode != 0:
                    logger.error(f"WordPress installation failed: {result.stderr}")
                    return False
                
                logger.success("WordPress installed successfully!")
                return True
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error installing WordPress: {e}")
            return False
    
    def install_theme(self, site_path: str, theme: str) -> bool:
        """Install and activate a WordPress theme"""
        try:
            logger.step(f"Installing theme: {theme}")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # Install theme
                cmd = self.wp_cli_command + ['theme', 'install', theme, '--activate']
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode != 0:
                    logger.error(f"Failed to install theme {theme}: {result.stderr}")
                    return False
                
                logger.success(f"Theme {theme} installed and activated")
                return True
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error installing theme {theme}: {e}")
            return False
    
    def install_plugins(self, site_path: str, plugins: List[str]) -> bool:
        """Install and activate WordPress plugins"""
        try:
            if not plugins:
                logger.info("No plugins to install")
                return True
            
            logger.step(f"Installing {len(plugins)} plugins...")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                success = True
                for plugin in plugins:
                    cmd = self.wp_cli_command + ['plugin', 'install', plugin, '--activate']
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    
                    if result.returncode == 0:
                        logger.success(f"Plugin {plugin} installed and activated")
                    else:
                        logger.error(f"Failed to install plugin {plugin}: {result.stderr}")
                        success = False
                
                return success
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error installing plugins: {e}")
            return False
    
    def create_wordpress_site(self, site_name: str, site_config: Optional[Dict[str, Any]] = None) -> bool:
        """Complete WordPress site creation process"""
        try:
            if site_config is None:
                site_config = {}
            
            logger.header(f"Creating WordPress site: {site_name}")
            
            # Get configuration values
            htdocs_path = config_manager.get('xampp.htdocs_path')
            wordpress_zip = config_manager.get('wordpress.zip_path')
            
            # Prepare paths
            site_path = os.path.join(htdocs_path, site_name)
            
            # Database configuration
            db_config = {
                'db_name': site_config.get('db_name', f"wp_{site_name}"),
                'db_user': config_manager.get('xampp.mysql_user'),
                'db_password': config_manager.get('xampp.mysql_password'),
                'db_host': config_manager.get('xampp.mysql_host')
            }
            
            # Site configuration
            site_info = {
                'site_url': site_config.get('site_url', f"http://localhost/{site_name}"),
                'site_title': site_config.get('site_title', site_name.replace('_', ' ').title()),
                'admin_user': site_config.get('admin_user', config_manager.get('wordpress.admin_user')),
                'admin_password': site_config.get('admin_password', config_manager.get('wordpress.admin_password')),
                'admin_email': site_config.get('admin_email', config_manager.get('wordpress.admin_email'))
            }
            
            # Step 1: Check if site directory already exists
            if os.path.exists(site_path):
                logger.warning(f"Site directory already exists: {site_path}")
                if not site_config.get('overwrite', False):
                    logger.error("Site already exists. Use overwrite option to replace it.")
                    return False
                else:
                    logger.info("Removing existing site directory...")
                    shutil.rmtree(site_path)
            
            # Step 2: Create database
            if not self.db_manager.create_database(db_config['db_name']):
                return False
            
            # Step 3: Extract WordPress
            if not self.extract_wordpress(wordpress_zip, site_path):
                return False
            
            # Step 4: Configure WordPress
            if not self.configure_wordpress(site_path, db_config):
                return False
            
            # Step 5: Install WordPress
            if not self.install_wordpress(site_path, site_info):
                return False
            
            # Step 6: Install theme (if specified)
            theme = site_config.get('theme')
            if theme and theme != 'default':
                self.install_theme(site_path, theme)
            
            # Step 7: Install plugins (if specified)
            plugins = site_config.get('plugins', [])
            if plugins:
                self.install_plugins(site_path, plugins)
            
            # Step 8: Log success information
            logger.header("WordPress Installation Complete!")
            logger.success(f"Site URL: {site_info['site_url']}")
            logger.success(f"Admin URL: {site_info['site_url']}/wp-admin")
            logger.success(f"Admin User: {site_info['admin_user']}")
            logger.success(f"Admin Password: {site_info['admin_password']}")
            logger.success(f"Database: {db_config['db_name']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating WordPress site: {e}")
            return False
    
    def delete_wordpress_site(self, site_name: str, delete_db: bool = True) -> bool:
        """Delete a WordPress site and optionally its database"""
        try:
            logger.header(f"Deleting WordPress site: {site_name}")
            
            htdocs_path = config_manager.get('xampp.htdocs_path')
            site_path = os.path.join(htdocs_path, site_name)
            
            success = True
            
            # Delete site directory
            if os.path.exists(site_path):
                logger.step(f"Removing site directory: {site_path}")
                shutil.rmtree(site_path)
                logger.success("Site directory removed")
            else:
                logger.warning(f"Site directory not found: {site_path}")
            
            # Delete database
            if delete_db:
                db_name = f"wp_{site_name}"
                if self.db_manager.database_exists(db_name):
                    if not self.db_manager.drop_database(db_name):
                        success = False
                else:
                    logger.warning(f"Database not found: {db_name}")
            
            if success:
                logger.success(f"WordPress site '{site_name}' deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting WordPress site: {e}")
            return False
    
    def list_wordpress_sites(self) -> List[Dict[str, Any]]:
        """List all WordPress sites in htdocs"""
        try:
            htdocs_path = config_manager.get('xampp.htdocs_path')
            if not os.path.exists(htdocs_path):
                return []
            
            sites = []
            
            for item in os.listdir(htdocs_path):
                item_path = os.path.join(htdocs_path, item)
                
                # Check if it's a directory and contains wp-config.php
                if os.path.isdir(item_path):
                    wp_config = os.path.join(item_path, 'wp-config.php')
                    if os.path.exists(wp_config):
                        site_info = {
                            'name': item,
                            'path': item_path,
                            'url': f"http://localhost/{item}",
                            'has_database': self.db_manager.database_exists(f"wp_{item}"),
                            'size': Helpers.get_directory_size(item_path)
                        }
                        
                        # Try to get more info from wp-config.php
                        try:
                            with open(wp_config, 'r', encoding='utf-8') as f:
                                config_content = f.read()
                                if 'DB_NAME' in config_content:
                                    # Extract database name
                                    import re
                                    db_match = re.search(r"'DB_NAME',\s*'([^']+)'", config_content)
                                    if db_match:
                                        site_info['database'] = db_match.group(1)
                                        site_info['has_database'] = self.db_manager.database_exists(db_match.group(1))
                        except:
                            pass
                        
                        sites.append(site_info)
            
            return sites
            
        except Exception as e:
            logger.error(f"Error listing WordPress sites: {e}")
            return []
    
    def create_complete_site(self, site_name: str, site_title: str, db_name: str, theme: str = "twentytwentyfour") -> bool:
        """Create a complete WordPress site with all configurations"""
        try:
            logger.info(f"==================================================")
            logger.info(f"Creating WordPress site: {site_name}")
            logger.info(f"==================================================")
            
            # Get configuration
            htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
            site_path = htdocs_path / site_name
            
            # Create database
            logger.step(f"Creating database: {db_name}")
            if not self.db_manager.create_database(db_name):
                return False
            
            # Extract WordPress
            from ..utils.paths import PathUtils
            default_zip_path = "assets/wordpress-6.8.2.zip"
            zip_path_config = config_manager.get('wordpress.zip_path', default_zip_path)
            
            # Resolve the path (could be relative or absolute)
            zip_path = str(PathUtils.resolve_app_path(zip_path_config))
            if not self.extract_wordpress(zip_path, str(site_path)):
                return False
            
            # Configure WordPress
            logger.step("Configuring WordPress...")
            db_config = {
                'db_name': db_name,
                'db_user': config_manager.get('mysql.username', 'root'),
                'db_password': config_manager.get('mysql.password', ''),
                'db_host': config_manager.get('mysql.host', 'localhost')
            }
            if not self.configure_wordpress(str(site_path), db_config):
                return False
            
            # Install WordPress via WP-CLI
            logger.step("Installing WordPress...")
            admin_user = config_manager.get('wordpress.admin_user', 'admin')
            admin_password = config_manager.get('wordpress.admin_password', 'admin123')
            admin_email = config_manager.get('wordpress.admin_email', 'admin@localhost.com')
            base_url = config_manager.get('wordpress.base_url', 'http://localhost')
            
            if not self.install_wordpress(
                str(site_path), 
                {
                    'site_url': f"{base_url}/{site_name}",
                    'site_title': site_title,
                    'admin_user': admin_user,
                    'admin_password': admin_password,
                    'admin_email': admin_email
                }
            ):
                return False
            
            # Install and activate theme
            if theme and theme != "twentytwentyfour":  # Skip if default theme
                logger.step(f"Installing theme: {theme}")
                if not self.install_theme(str(site_path), theme):
                    logger.warning(f"Failed to install theme: {theme}")
            
            logger.info("==================================================")
            logger.info("WordPress Installation Complete!")
            logger.info("==================================================")
            logger.success(f"Site URL: {base_url}/{site_name}")
            logger.success(f"Admin URL: {base_url}/{site_name}/wp-admin")
            logger.success(f"Admin User: {admin_user}")
            logger.success(f"Admin Password: {admin_password}")
            logger.success(f"Database: {db_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating complete site: {e}")
            return False
    
    def delete_site(self, site_name: str) -> bool:
        """Delete a WordPress site and its database"""
        try:
            logger.info(f"==================================================")
            logger.info(f"Deleting WordPress site: {site_name}")
            logger.info(f"==================================================")
            
            success = True
            
            # Get paths
            htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
            site_path = htdocs_path / site_name
            
            # Remove site directory
            if site_path.exists():
                logger.step(f"Removing site directory: {site_path}")
                shutil.rmtree(site_path)
                logger.success("Site directory removed")
            else:
                logger.warning(f"Site directory not found: {site_path}")
            
            # Extract and delete database
            db_name = None
            wp_config_path = site_path / 'wp-config.php'
            
            # If config still exists, try to extract DB name
            if wp_config_path.exists():
                try:
                    with open(wp_config_path, 'r') as f:
                        content = f.read()
                        import re
                        db_match = re.search(r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]", content)
                        if db_match:
                            db_name = db_match.group(1)
                except:
                    pass
            
            # Fallback to standard naming convention
            if not db_name:
                db_name = f"wp_{site_name.replace('-', '_').replace(' ', '_')}"
            
            # Delete database
            if self.db_manager.database_exists(db_name):
                logger.step(f"Removing database: {db_name}")
                if self.db_manager.drop_database(db_name):
                    logger.success("Database removed")
                else:
                    logger.error("Failed to remove database")
                    success = False
            else:
                logger.warning(f"Database not found: {db_name}")
            
            if success:
                logger.success(f"WordPress site '{site_name}' deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting WordPress site: {e}")
            return False
    
    def reset_site(self, site_name: str, db_name: str) -> bool:
        """Reset a WordPress site to clean installation"""
        try:
            logger.info(f"Resetting WordPress site: {site_name}")
            
            htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
            site_path = htdocs_path / site_name
            
            if not site_path.exists():
                logger.error(f"Site directory not found: {site_path}")
                return False
            
            # Drop and recreate database
            if self.db_manager.database_exists(db_name):
                logger.step(f"Resetting database: {db_name}")
                if not self.db_manager.drop_database(db_name):
                    logger.error("Failed to drop database")
                    return False
            
            if not self.db_manager.create_database(db_name):
                logger.error("Failed to recreate database")
                return False
            
            # Remove existing WordPress files
            logger.step("Removing existing WordPress files...")
            import shutil
            shutil.rmtree(str(site_path))
            
            # Extract fresh WordPress
            from ..utils.paths import PathUtils
            default_zip_path = "assets/wordpress-6.8.2.zip"
            zip_path_config = config_manager.get('wordpress.zip_path', default_zip_path)
            
            # Resolve the path (could be relative or absolute)
            zip_path = str(PathUtils.resolve_app_path(zip_path_config))
            if not self.extract_wordpress(zip_path, str(site_path)):
                return False
            
            # Configure WordPress
            db_config = {
                'db_name': db_name,
                'db_user': config_manager.get('mysql.username', 'root'),
                'db_password': config_manager.get('mysql.password', ''),
                'db_host': config_manager.get('mysql.host', 'localhost')
            }
            if not self.configure_wordpress(str(site_path), db_config):
                return False
            
            # Install WordPress
            base_url = config_manager.get('wordpress.base_url', 'http://localhost')
            admin_user = config_manager.get('wordpress.admin_user', 'admin')
            admin_password = config_manager.get('wordpress.admin_password', 'admin123')
            admin_email = config_manager.get('wordpress.admin_email', 'admin@localhost.com')
            
            if not self.install_wordpress(
                str(site_path), 
                {
                    'site_url': f"{base_url}/{site_name}",
                    'site_title': f"Reset {site_name.replace('-', ' ').title()}",
                    'admin_user': admin_user,
                    'admin_password': admin_password,
                    'admin_email': admin_email
                }
            ):
                return False
            
            logger.success(f"WordPress site '{site_name}' reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting WordPress site: {e}")
            return False
    
    def install_plugin_from_file(self, site_path: str, plugin_file: str) -> bool:
        """Install a plugin from a zip file"""
        try:
            logger.step(f"Installing plugin from file: {os.path.basename(plugin_file)}")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # Install plugin from file
                cmd = self.wp_cli_command + ['plugin', 'install', plugin_file, '--activate']
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    logger.success(f"Plugin installed from file: {os.path.basename(plugin_file)}")
                    return True
                else:
                    logger.error(f"Failed to install plugin from file: {result.stderr}")
                    return False
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error installing plugin from file: {e}")
            return False
    
    def get_installed_plugins(self, site_path: str) -> List[Dict[str, str]]:
        """Get list of installed plugins with their status"""
        try:
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # Get plugin list with details
                cmd = self.wp_cli_command + ['plugin', 'list', '--format=json']
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    import json
                    plugins_data = json.loads(result.stdout)
                    
                    plugins = []
                    for plugin in plugins_data:
                        plugins.append({
                            'name': plugin.get('name', ''),
                            'status': plugin.get('status', ''),
                            'version': plugin.get('version', ''),
                            'description': plugin.get('description', ''),
                            'title': plugin.get('title', '')
                        })
                    
                    return plugins
                else:
                    logger.error(f"Failed to get plugin list: {result.stderr}")
                    return []
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error getting installed plugins: {e}")
            return []
    
    def activate_plugin(self, site_path: str, plugin_name: str) -> bool:
        """Activate a specific plugin"""
        try:
            logger.step(f"Activating plugin: {plugin_name}")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                cmd = self.wp_cli_command + ['plugin', 'activate', plugin_name]
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    logger.success(f"Plugin activated: {plugin_name}")
                    return True
                else:
                    logger.error(f"Failed to activate plugin {plugin_name}: {result.stderr}")
                    return False
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error activating plugin {plugin_name}: {e}")
            return False
    
    def deactivate_plugin(self, site_path: str, plugin_name: str) -> bool:
        """Deactivate a specific plugin"""
        try:
            logger.step(f"Deactivating plugin: {plugin_name}")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                cmd = self.wp_cli_command + ['plugin', 'deactivate', plugin_name]
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    logger.success(f"Plugin deactivated: {plugin_name}")
                    return True
                else:
                    logger.error(f"Failed to deactivate plugin {plugin_name}: {result.stderr}")
                    return False
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_name}: {e}")
            return False
    
    def delete_plugin(self, site_path: str, plugin_name: str) -> bool:
        """Delete a specific plugin (deactivate first if active)"""
        try:
            logger.step(f"Deleting plugin: {plugin_name}")
            
            original_cwd = os.getcwd()
            os.chdir(site_path)
            
            try:
                # First, check if plugin is active and deactivate if needed
                cmd = self.wp_cli_command + ['plugin', 'list', '--name=' + plugin_name, '--format=json']
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    import json
                    plugin_data = json.loads(result.stdout)
                    if plugin_data and len(plugin_data) > 0:
                        if plugin_data[0].get('status') == 'active':
                            logger.info(f"Plugin {plugin_name} is active, deactivating first...")
                            # Deactivate inline to maintain directory context
                            deactivate_cmd = self.wp_cli_command + ['plugin', 'deactivate', plugin_name]
                            deactivate_result = subprocess.run(deactivate_cmd, capture_output=True, text=True, shell=True)
                            
                            if deactivate_result.returncode == 0:
                                logger.success(f"Plugin deactivated: {plugin_name}")
                            else:
                                logger.warning(f"Failed to deactivate plugin {plugin_name}: {deactivate_result.stderr}")
                                logger.warning("Attempting to delete anyway...")
                
                # Delete the plugin (ensure we're still in the correct directory)
                logger.info(f"Current directory: {os.getcwd()}")
                cmd = self.wp_cli_command + ['plugin', 'delete', plugin_name]
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    logger.success(f"Plugin deleted: {plugin_name}")
                    return True
                else:
                    logger.error(f"Failed to delete plugin {plugin_name}: {result.stderr}")
                    return False
                
            finally:
                os.chdir(original_cwd)
            
        except Exception as e:
            logger.error(f"Error deleting plugin {plugin_name}: {e}")
            return False

# No global instance - create instances as needed
