#!/usr/bin/env python3
"""
Database operations for WordPress Auto Installer
Handles MySQL database creation, deletion, and management
"""

import subprocess
from pathlib import Path
from typing import Optional, List
from ..utils.logger import logger
from ..utils.config import config_manager

class DatabaseManager:
    def __init__(self):
        self.mysql_command = None
        self._find_mysql_executable()
    
    def _find_mysql_executable(self) -> None:
        """Find MySQL executable in common XAMPP locations"""
        mysql_paths = [
            'mysql',  # If it's in PATH
            'E:/xampp/mysql/bin/mysql.exe',
            'C:/xampp/mysql/bin/mysql.exe',
            'D:/xampp/mysql/bin/mysql.exe',
            '/opt/lampp/bin/mysql',  # Linux
            '/Applications/XAMPP/xamppfiles/bin/mysql'  # macOS
        ]
        
        for mysql_path in mysql_paths:
            try:
                if mysql_path == 'mysql':
                    result = subprocess.run([mysql_path, '--version'], capture_output=True, text=True, shell=True)
                else:
                    result = subprocess.run([mysql_path, '--version'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.success(f"MySQL found at: {mysql_path}")
                    self.mysql_command = mysql_path
                    return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        
        # If not found, try to auto-detect based on htdocs path
        htdocs_path = Path(config_manager.get('xampp.htdocs_path', ''))
        if htdocs_path.exists():
            xampp_root = htdocs_path.parent
            mysql_bin = xampp_root / 'mysql' / 'bin' / 'mysql.exe'
            
            if mysql_bin.exists():
                logger.success(f"MySQL found at: {mysql_bin}")
                self.mysql_command = str(mysql_bin)
                return
        
        logger.error("MySQL executable not found in common locations")
        self.mysql_command = 'mysql'  # Fallback to system PATH
    
    def run_mysql_command(self, command: str) -> subprocess.CompletedProcess:
        """Execute MySQL command"""
        cmd = [
            self.mysql_command,
            f"-u{config_manager.get('xampp.mysql_user')}",
            f"-h{config_manager.get('xampp.mysql_host')}",
            '-e', command
        ]
        
        mysql_password = config_manager.get('xampp.mysql_password')
        if mysql_password:
            cmd.insert(2, f"-p{mysql_password}")
        
        return subprocess.run(cmd, capture_output=True, text=True, shell=True)
    
    def test_connection(self) -> tuple[bool, str]:
        """Test MySQL connection"""
        try:
            result = self.run_mysql_command('SELECT VERSION();')
            if result.returncode == 0:
                version_info = result.stdout.strip()
                logger.success("MySQL connection successful")
                return True, version_info
            else:
                error_msg = result.stderr.strip() or "Unknown MySQL error"
                logger.error(f"MySQL connection failed: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = f"MySQL connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def database_exists(self, db_name: str) -> bool:
        """Check if database exists"""
        try:
            result = self.run_mysql_command(f"SHOW DATABASES LIKE '{db_name}';")
            return db_name in result.stdout
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
            return False
    
    def create_database(self, db_name: str, drop_if_exists: bool = True) -> bool:
        """Create a new database"""
        try:
            logger.step(f"Creating database: {db_name}")
            
            if self.database_exists(db_name):
                if drop_if_exists:
                    logger.info(f"Database {db_name} already exists, dropping it first...")
                    if not self.drop_database(db_name):
                        return False
                else:
                    logger.warning(f"Database {db_name} already exists")
                    return True
            
            result = self.run_mysql_command(
                f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create database: {result.stderr}")
                return False
            
            logger.success(f"Database {db_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database {db_name}: {e}")
            return False
    
    def drop_database(self, db_name: str) -> bool:
        """Drop a database"""
        try:
            result = self.run_mysql_command(f"DROP DATABASE IF EXISTS {db_name};")
            if result.returncode != 0:
                logger.error(f"Failed to drop database {db_name}: {result.stderr}")
                return False
            
            logger.success(f"Database {db_name} dropped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error dropping database {db_name}: {e}")
            return False
    
    def list_databases(self) -> List[str]:
        """List all databases"""
        try:
            result = self.run_mysql_command("SHOW DATABASES;")
            if result.returncode == 0:
                databases = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and line not in ['Database', 'information_schema', 'performance_schema', 'mysql', 'sys']:
                        databases.append(line)
                return databases
            else:
                logger.error(f"Failed to list databases: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return []
    
    def get_database_size(self, db_name: str) -> Optional[str]:
        """Get database size in human readable format"""
        try:
            query = f"""
                SELECT 
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size in MB'
                FROM information_schema.tables 
                WHERE table_schema='{db_name}';
            """
            result = self.run_mysql_command(query)
            
            if result.returncode == 0:
                # Parse the result to get the size
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    size_mb = lines[1].strip()
                    if size_mb and size_mb != 'NULL':
                        return f"{size_mb} MB"
            
            return "Unknown"
            
        except Exception as e:
            logger.debug(f"Error getting database size for {db_name}: {e}")
            return "Unknown"
    
    def backup_database(self, db_name: str, backup_path: str) -> bool:
        """Backup database to SQL file"""
        try:
            # Build mysqldump command
            mysqldump_cmd = [
                self.mysql_command.replace('mysql.exe', 'mysqldump.exe').replace('mysql', 'mysqldump'),
                f"-u{config_manager.get('xampp.mysql_user')}",
                f"-h{config_manager.get('xampp.mysql_host')}",
                db_name
            ]
            
            mysql_password = config_manager.get('xampp.mysql_password')
            if mysql_password:
                mysqldump_cmd.insert(2, f"-p{mysql_password}")
            
            # Execute backup
            with open(backup_path, 'w', encoding='utf-8') as backup_file:
                result = subprocess.run(mysqldump_cmd, stdout=backup_file, stderr=subprocess.PIPE, text=True, shell=True)
            
            if result.returncode == 0:
                logger.success(f"Database {db_name} backed up to {backup_path}")
                return True
            else:
                logger.error(f"Failed to backup database {db_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error backing up database {db_name}: {e}")
            return False
    
    def restore_database(self, db_name: str, backup_path: str) -> bool:
        """Restore database from SQL file"""
        try:
            # Create database first
            if not self.create_database(db_name):
                return False
            
            # Build mysql command for import
            mysql_cmd = [
                self.mysql_command,
                f"-u{config_manager.get('xampp.mysql_user')}",
                f"-h{config_manager.get('xampp.mysql_host')}",
                db_name
            ]
            
            mysql_password = config_manager.get('xampp.mysql_password')
            if mysql_password:
                mysql_cmd.insert(2, f"-p{mysql_password}")
            
            # Execute restore
            with open(backup_path, 'r', encoding='utf-8') as backup_file:
                result = subprocess.run(mysql_cmd, stdin=backup_file, stderr=subprocess.PIPE, text=True, shell=True)
            
            if result.returncode == 0:
                logger.success(f"Database {db_name} restored from {backup_path}")
                return True
            else:
                logger.error(f"Failed to restore database {db_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring database {db_name}: {e}")
            return False

# No global instance - create instances as needed
