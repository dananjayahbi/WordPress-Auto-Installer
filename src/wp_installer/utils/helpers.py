#!/usr/bin/env python3
"""
Utility functions for WordPress Auto Installer
File operations, validation, and helper functions
"""

import os
import sys
import subprocess
import shutil
import zipfile
import winreg
import platform
from pathlib import Path
from typing import Optional, List, Tuple
from .logger import logger
from .config import config_manager
from .paths import PathUtils

# Windows-specific subprocess configuration to prevent CMD window flashing
if platform.system() == 'Windows':
    # Create startupinfo to hide console windows
    STARTUP_INFO = subprocess.STARTUPINFO()
    STARTUP_INFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    STARTUP_INFO.wShowWindow = subprocess.SW_HIDE
else:
    STARTUP_INFO = None

class Helpers:
    @staticmethod
    def find_wp_cli_executable() -> Optional[str]:
        """Find WP-CLI executable"""
        wp_commands = [
            'wp',
            'wp.bat', 
            'wp.cmd',
            'php C:/wp-cli/wp-cli.phar',
            'php C:\\wp-cli\\wp-cli.phar'
        ]
        
        for wp_cmd in wp_commands:
            try:
                if wp_cmd.startswith('php'):
                    cmd_list = wp_cmd.split()
                    result = subprocess.run(cmd_list + ['--version'], capture_output=True, text=True, 
                                          shell=True, startupinfo=STARTUP_INFO)
                else:
                    result = subprocess.run([wp_cmd, '--version'], capture_output=True, text=True, 
                                          shell=True, startupinfo=STARTUP_INFO)
                
                if result.returncode == 0:
                    logger.success(f"WP-CLI found: {result.stdout.strip()}")
                    return wp_cmd
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        
        logger.error("WP-CLI not found!")
        return None
    
    @staticmethod
    def run_wp_cli_command(wp_command: str, command: List[str], path: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Execute WP-CLI command"""
        if wp_command.startswith('php'):
            # For PHAR-based installation
            cmd = wp_command.split() + command
        else:
            # For standard installation
            cmd = [wp_command] + command
        
        # Use cwd parameter instead of --path for better compatibility
        cwd = str(path) if path else None
        return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, shell=True, startupinfo=STARTUP_INFO)
    
    @staticmethod
    def get_directory_size(path: Path) -> str:
        """Get human readable directory size"""
        try:
            total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    return f"{total_size:3.1f} {unit}"
                total_size /= 1024.0
            return f"{total_size:.1f} TB"
        except Exception as e:
            logger.debug(f"Error calculating directory size for {path}: {e}")
            return "Unknown"
    
    @staticmethod
    def extract_wordpress_zip(zip_path: Path, destination: Path) -> bool:
        """Extract WordPress from zip file"""
        try:
            logger.step(f"Extracting WordPress from {zip_path.name}")
            
            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)
            
            # Extract WordPress zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files to a temporary directory first
                temp_extract = destination / "temp_extract"
                zip_ref.extractall(temp_extract)
                
                # WordPress zip typically contains a 'wordpress' folder
                wordpress_folder = temp_extract / "wordpress"
                if wordpress_folder.exists():
                    # Move contents of wordpress folder to destination
                    for item in wordpress_folder.iterdir():
                        shutil.move(str(item), str(destination / item.name))
                    # Remove the temporary extraction directory
                    shutil.rmtree(temp_extract)
                else:
                    # If no wordpress folder, assume files are at root level
                    for item in temp_extract.iterdir():
                        shutil.move(str(item), str(destination / item.name))
                    # Remove the temporary extraction directory
                    shutil.rmtree(temp_extract)
            
            logger.success(f"WordPress extracted successfully to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract WordPress zip: {str(e)}")
            return False
    
    @staticmethod
    def find_wordpress_zip() -> Optional[Path]:
        """Find WordPress zip file in the assets directory"""
        # Look in assets directory first
        assets_dir = PathUtils.get_app_data_dir("assets")
        wp_zip_files = list(assets_dir.glob("wordpress*.zip"))
        
        if wp_zip_files:
            wp_zip_file = wp_zip_files[0]  # Use the first WordPress zip found
            logger.info(f"Using WordPress zip: {wp_zip_file.name}")
            return wp_zip_file
        
        # Fallback to script directory (backward compatibility)
        script_dir = Path(__file__).parent.parent.parent.parent
        wp_zip_files = list(script_dir.glob("wordpress*.zip"))
        
        if wp_zip_files:
            wp_zip_file = wp_zip_files[0]
            logger.info(f"Using WordPress zip: {wp_zip_file.name}")
            return wp_zip_file
        
        logger.error("WordPress zip file not found. Please ensure wordpress-*.zip is in the assets directory.")
        return None
    
    @staticmethod
    def cleanup_directory(path: Path, force: bool = False) -> bool:
        """Safely remove directory"""
        try:
            if not path.exists():
                return True
            
            if not force:
                # Basic safety check - don't delete system directories
                system_paths = ['C:\\', 'D:\\', '/', '/usr', '/etc', '/var']
                if str(path) in system_paths or len(str(path)) < 5:
                    logger.error(f"Refusing to delete system path: {path}")
                    return False
            
            shutil.rmtree(path)
            logger.success(f"Removed directory: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove directory {path}: {e}")
            return False
    
    @staticmethod
    def validate_instance_name(name: str) -> Tuple[bool, str]:
        """Validate WordPress instance name"""
        if not name:
            return False, "Instance name cannot be empty"
        
        if len(name) < 3:
            return False, "Instance name must be at least 3 characters long"
        
        if len(name) > 50:
            return False, "Instance name must be less than 50 characters"
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return False, "Instance name can only contain letters, numbers, underscores, and hyphens"
        
        # Check if name starts with letter or number
        if not name[0].isalnum():
            return False, "Instance name must start with a letter or number"
        
        return True, "Valid instance name"
    
    @staticmethod
    def get_next_instance_name() -> Optional[str]:
        """Get the next available instance name"""
        prefix = config_manager.get('instances.prefix', 'wp_test_')
        max_instances = config_manager.get('instances.max_instances', 50)
        htdocs = Path(config_manager.get('xampp.htdocs_path', ''))
        
        if not htdocs.exists():
            logger.error(f"htdocs path does not exist: {htdocs}")
            return None
        
        for i in range(1, max_instances + 1):
            instance_name = f"{prefix}{i:02d}"
            if not (htdocs / instance_name).exists():
                return instance_name
        
        logger.error(f"Maximum number of instances ({max_instances}) reached")
        return None
    
    @staticmethod
    def get_available_instances() -> List[dict]:
        """Get list of all WordPress instances"""
        instances = []
        htdocs = Path(config_manager.get('xampp.htdocs_path', ''))
        prefix = config_manager.get('instances.prefix', 'wp_test_')
        base_url = config_manager.get('wordpress.base_url', 'http://localhost')
        
        if not htdocs.exists():
            return instances
        
        for item in htdocs.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                wp_config = item / 'wp-config.php'
                if wp_config.exists():
                    instances.append({
                        'name': item.name,
                        'path': str(item),
                        'url': f"{base_url}/{item.name}",
                        'size': Helpers.get_directory_size(item),
                        'wp_config_exists': True
                    })
        
        return sorted(instances, key=lambda x: x['name'])
    
    @staticmethod
    def set_file_permissions(path: Path) -> bool:
        """Set appropriate file permissions (mainly for non-Windows)"""
        try:
            if os.name != 'nt':  # Not Windows
                os.chmod(path, 0o755)
                logger.debug(f"Set permissions for {path}")
            return True
        except Exception as e:
            logger.debug(f"Could not set permissions for {path}: {e}")
            return False
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:3.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def is_port_available(port: int, host: str = 'localhost') -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return False
    
    @staticmethod
    def get_system_info() -> dict:
        """Get system information"""
        import platform
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'current_directory': str(Path.cwd())
        }
    
    @staticmethod
    def check_php_installation() -> Tuple[bool, str]:
        """Check if PHP is accessible via command line"""
        try:
            result = subprocess.run(['php', '--version'], capture_output=True, text=True, 
                                  shell=True, startupinfo=STARTUP_INFO)
            if result.returncode == 0:
                return True, result.stdout.strip().split('\n')[0]
            else:
                return False, "PHP command failed"
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            return False, f"PHP not found: {e}"
    
    @staticmethod
    def add_to_system_path(directory: str) -> bool:
        """Add directory to system PATH variable"""
        try:
            # Open the system environment variables key
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                              0, winreg.KEY_ALL_ACCESS) as key:
                
                # Get current PATH value
                current_path, _ = winreg.QueryValueEx(key, "PATH")
                
                # Check if directory is already in PATH
                paths = [p.strip() for p in current_path.split(';')]
                if directory not in paths:
                    # Add new directory to PATH
                    new_path = current_path + ';' + directory
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                    
                    # Broadcast WM_SETTINGCHANGE to notify other processes
                    import win32gui
                    import win32con
                    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')
                    
                    logger.success(f"Added {directory} to system PATH")
                    return True
                else:
                    logger.info(f"{directory} already in system PATH")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to add to system PATH: {e}")
            return False
    
    @staticmethod
    def setup_php_path(php_exe_path: str) -> bool:
        """Add PHP directory to system PATH"""
        php_dir = str(Path(php_exe_path).parent)
        return Helpers.add_to_system_path(php_dir)
    
    @staticmethod
    def install_wp_cli() -> bool:
        """Install WP-CLI from assets to C:/wp-cli/"""
        try:
            # Check if wp-cli.phar exists in assets
            assets_dir = PathUtils.get_app_data_dir("assets")
            wp_cli_source = assets_dir / "wp-cli.phar"
            
            if not wp_cli_source.exists():
                logger.error("wp-cli.phar not found in assets directory")
                return False
            
            # Create C:/wp-cli directory
            wp_cli_dir = Path("C:/wp-cli")
            wp_cli_dir.mkdir(exist_ok=True)
            
            # Copy wp-cli.phar to C:/wp-cli/
            wp_cli_target = wp_cli_dir / "wp-cli.phar"
            shutil.copy2(wp_cli_source, wp_cli_target)
            
            # Add C:/wp-cli to system PATH
            if not Helpers.add_to_system_path(str(wp_cli_dir)):
                return False
            
            # Test WP-CLI installation
            try:
                result = subprocess.run(['php', str(wp_cli_target), '--info'], 
                                      capture_output=True, text=True, shell=True, startupinfo=STARTUP_INFO)
                if result.returncode == 0:
                    logger.success("WP-CLI installed successfully")
                    return True
                else:
                    logger.error(f"WP-CLI test failed: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"WP-CLI test error: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to install WP-CLI: {e}")
            return False
    
    @staticmethod
    def validate_plugin_file(file_path: str) -> bool:
        """Validate if a file is a valid WordPress plugin zip"""
        try:
            if not file_path.endswith('.zip'):
                logger.error("Plugin file must be a ZIP archive")
                return False
            
            if not os.path.exists(file_path):
                logger.error(f"Plugin file not found: {file_path}")
                return False
            
            # Try to open the zip file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Check if it contains PHP files (basic plugin check)
                has_php = any(f.endswith('.php') for f in file_list)
                if not has_php:
                    logger.warning("ZIP file doesn't contain PHP files - may not be a WordPress plugin")
                    return False
                
                # Look for plugin header in main PHP files
                for file_name in file_list:
                    if file_name.endswith('.php') and not '/' in file_name:  # Main directory PHP files
                        try:
                            with zip_ref.open(file_name) as php_file:
                                content = php_file.read(2048).decode('utf-8', errors='ignore')
                                if 'Plugin Name:' in content or 'plugin name:' in content.lower():
                                    logger.success(f"Valid WordPress plugin detected: {file_name}")
                                    return True
                        except:
                            continue
                
                logger.warning("No WordPress plugin header found - proceeding anyway")
                return True  # Allow installation even if header not found
                
        except zipfile.BadZipFile:
            logger.error("Invalid ZIP file")
            return False
        except Exception as e:
            logger.error(f"Error validating plugin file: {e}")
            return False
    
    @staticmethod
    def get_plugin_info_from_zip(file_path: str) -> dict:
        """Extract plugin information from ZIP file"""
        plugin_info = {
            'name': os.path.basename(file_path).replace('.zip', ''),
            'version': 'Unknown',
            'description': 'No description available',
            'author': 'Unknown',
            'plugin_uri': '',
            'valid': False
        }
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Look for main plugin file
                for file_name in file_list:
                    if file_name.endswith('.php') and not '/' in file_name:
                        try:
                            with zip_ref.open(file_name) as php_file:
                                content = php_file.read(4096).decode('utf-8', errors='ignore')
                                
                                # Parse plugin header
                                if 'Plugin Name:' in content or 'plugin name:' in content.lower():
                                    plugin_info['valid'] = True
                                    
                                    # Extract plugin information using regex
                                    import re
                                    
                                    # Plugin Name
                                    name_match = re.search(r'Plugin Name:\s*(.+)', content, re.IGNORECASE)
                                    if name_match:
                                        plugin_info['name'] = name_match.group(1).strip()
                                    
                                    # Version
                                    version_match = re.search(r'Version:\s*(.+)', content, re.IGNORECASE)
                                    if version_match:
                                        plugin_info['version'] = version_match.group(1).strip()
                                    
                                    # Description
                                    desc_match = re.search(r'Description:\s*(.+)', content, re.IGNORECASE)
                                    if desc_match:
                                        plugin_info['description'] = desc_match.group(1).strip()
                                    
                                    # Author
                                    author_match = re.search(r'Author:\s*(.+)', content, re.IGNORECASE)
                                    if author_match:
                                        plugin_info['author'] = author_match.group(1).strip()
                                    
                                    # Plugin URI
                                    uri_match = re.search(r'Plugin URI:\s*(.+)', content, re.IGNORECASE)
                                    if uri_match:
                                        plugin_info['plugin_uri'] = uri_match.group(1).strip()
                                    
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Error reading {file_name}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error extracting plugin info: {e}")
        
        return plugin_info
    
    @staticmethod
    def create_temp_plugin_dir() -> str:
        """Create a temporary directory for plugin operations"""
        try:
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='wp_plugin_')
            logger.debug(f"Created temporary plugin directory: {temp_dir}")
            return temp_dir
        except Exception as e:
            logger.error(f"Error creating temporary directory: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_dir(temp_dir: str) -> bool:
        """Clean up temporary directory"""
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
            return False

# No global instance - create instances as needed
