#!/usr/bin/env python3
"""
Command Line Interface for WordPress Auto Installer
Provides CLI commands for WordPress installation and management
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..utils.logger import logger
from ..utils.config import config_manager
from ..core.database import DatabaseManager
from ..core.wordpress import WordPressInstaller

class WordPressCLI:
    def __init__(self):
        self.parser = self.create_parser()
        self._db_manager = None
        self._wp_installer = None
    
    @property
    def db_manager(self):
        """Lazy initialization of database manager"""
        if self._db_manager is None:
            self._db_manager = DatabaseManager()
        return self._db_manager
    
    @property
    def wp_installer(self):
        """Lazy initialization of WordPress installer"""
        if self._wp_installer is None:
            self._wp_installer = WordPressInstaller()
        return self._wp_installer
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI"""
        parser = argparse.ArgumentParser(
            description="WordPress Auto Installer - Command Line Interface",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s install mysite --title "My Site" --email admin@example.com
  %(prog)s list
  %(prog)s delete mysite
  %(prog)s test
  %(prog)s config --set xampp.htdocs_path=/path/to/htdocs
            """
        )
        
        # Global options
        parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
        parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output except errors')
        parser.add_argument('--config', help='Path to configuration file')
        
        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Install command
        install_parser = subparsers.add_parser('install', help='Install WordPress site')
        install_parser.add_argument('site_name', help='Name of the site to install')
        install_parser.add_argument('--title', help='Site title')
        install_parser.add_argument('--email', help='Admin email address')
        install_parser.add_argument('--user', help='Admin username')
        install_parser.add_argument('--password', help='Admin password')
        install_parser.add_argument('--db-name', help='Database name (defaults to wp_SITENAME)')
        install_parser.add_argument('--theme', help='Theme to install')
        install_parser.add_argument('--plugins', help='Comma-separated list of plugins to install')
        install_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing site')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List WordPress sites')
        list_parser.add_argument('--format', choices=['table', 'json'], default='table',
                               help='Output format')
        
        # Delete command
        delete_parser = subparsers.add_parser('delete', help='Delete WordPress site')
        delete_parser.add_argument('site_name', help='Name of the site to delete')
        delete_parser.add_argument('--keep-db', action='store_true', help='Keep database when deleting')
        delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
        
        # Test command
        test_parser = subparsers.add_parser('test', help='Test system requirements')
        
        # Database commands
        db_parser = subparsers.add_parser('db', help='Database operations')
        db_subparsers = db_parser.add_subparsers(dest='db_command', help='Database commands')
        
        # Database list
        db_list_parser = db_subparsers.add_parser('list', help='List databases')
        
        # Database backup
        db_backup_parser = db_subparsers.add_parser('backup', help='Backup database')
        db_backup_parser.add_argument('db_name', help='Database name')
        db_backup_parser.add_argument('backup_path', help='Path to save backup file')
        
        # Database restore
        db_restore_parser = db_subparsers.add_parser('restore', help='Restore database')
        db_restore_parser.add_argument('db_name', help='Database name')
        db_restore_parser.add_argument('backup_path', help='Path to backup file')
        
        # Configuration commands
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_group = config_parser.add_mutually_exclusive_group()
        config_group.add_argument('--list', action='store_true', help='List all configuration')
        config_group.add_argument('--get', help='Get configuration value')
        config_group.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='Set configuration value')
        config_group.add_argument('--export', help='Export configuration to file')
        config_group.add_argument('--import', help='Import configuration from file')
        config_group.add_argument('--reset', action='store_true', help='Reset to default configuration')
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run CLI with given arguments"""
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Configure logging
            if parsed_args.quiet:
                logger.set_level('ERROR')
            elif parsed_args.verbose:
                logger.set_level('DEBUG')
            
            # Load custom config if specified
            if hasattr(parsed_args, 'config') and parsed_args.config:
                if not config_manager.load_from_file(parsed_args.config):
                    logger.error(f"Failed to load configuration from {parsed_args.config}")
                    return 1
            
            # Handle commands
            if not parsed_args.command:
                self.parser.print_help()
                return 0
            
            return self.execute_command(parsed_args)
            
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            return 1
        except Exception as e:
            logger.error(f"CLI error: {e}")
            return 1
    
    def execute_command(self, args) -> int:
        """Execute the specified command"""
        if args.command == 'install':
            return self.cmd_install(args)
        elif args.command == 'list':
            return self.cmd_list(args)
        elif args.command == 'delete':
            return self.cmd_delete(args)
        elif args.command == 'test':
            return self.cmd_test(args)
        elif args.command == 'db':
            return self.cmd_database(args)
        elif args.command == 'config':
            return self.cmd_config(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    
    def cmd_install(self, args) -> int:
        """Install WordPress site"""
        try:
            # Prepare site configuration
            site_config = {
                'site_title': args.title,
                'admin_email': args.email,
                'admin_user': args.user,
                'admin_password': args.password,
                'db_name': args.db_name,
                'theme': args.theme,
                'plugins': [p.strip() for p in args.plugins.split(',') if p.strip()] if args.plugins else [],
                'overwrite': args.overwrite
            }
            
            # Remove None values
            site_config = {k: v for k, v in site_config.items() if v is not None}
            
            # Install WordPress
            success = self.wp_installer.create_wordpress_site(args.site_name, site_config)
            
            return 0 if success else 1
            
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return 1
    
    def cmd_list(self, args) -> int:
        """List WordPress sites"""
        try:
            sites = self.wp_installer.list_wordpress_sites()
            
            if not sites:
                logger.info("No WordPress sites found")
                return 0
            
            if args.format == 'json':
                import json
                print(json.dumps(sites, indent=2))
            else:
                # Table format
                print(f"{'Site Name':<20} {'URL':<30} {'Database':<10} {'Size':<10}")
                print("-" * 75)
                for site in sites:
                    db_status = "✓" if site['has_database'] else "✗"
                    print(f"{site['name']:<20} {site['url']:<30} {db_status:<10} {site['size']:<10}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to list sites: {e}")
            return 1
    
    def cmd_delete(self, args) -> int:
        """Delete WordPress site"""
        try:
            # Confirm deletion unless --force is used
            if not args.force:
                response = input(f"Delete WordPress site '{args.site_name}'? [y/N]: ")
                if response.lower() not in ['y', 'yes']:
                    logger.info("Operation cancelled")
                    return 0
            
            # Delete site
            success = self.wp_installer.delete_wordpress_site(args.site_name, not args.keep_db)
            
            return 0 if success else 1
            
        except Exception as e:
            logger.error(f"Failed to delete site: {e}")
            return 1
    
    def cmd_test(self, args) -> int:
        """Test system requirements"""
        try:
            logger.header("Testing System Requirements")
            
            success = True
            
            # Test MySQL
            mysql_success, mysql_msg = self.db_manager.test_connection()
            if mysql_success:
                logger.success(f"MySQL: {mysql_msg}")
            else:
                logger.error(f"MySQL: {mysql_msg}")
                success = False
            
            # Test WP-CLI
            wpcli_success, wpcli_msg = self.wp_installer.test_wp_cli()
            if wpcli_success:
                logger.success(f"WP-CLI: {wpcli_msg}")
            else:
                logger.error(f"WP-CLI: {wpcli_msg}")
                success = False
            
            # Test paths
            htdocs_path = config_manager.get('xampp.htdocs_path')
            if Path(htdocs_path).exists():
                logger.success(f"Htdocs path: {htdocs_path}")
            else:
                logger.error(f"Htdocs path not found: {htdocs_path}")
                success = False
            
            wordpress_zip = config_manager.get('wordpress.zip_path')
            if Path(wordpress_zip).exists():
                logger.success(f"WordPress zip: {wordpress_zip}")
            else:
                logger.error(f"WordPress zip not found: {wordpress_zip}")
                success = False
            
            if success:
                logger.header("All tests passed!")
            else:
                logger.header("Some tests failed. Check configuration.")
            
            return 0 if success else 1
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            return 1
    
    def cmd_database(self, args) -> int:
        """Handle database commands"""
        try:
            if args.db_command == 'list':
                databases = self.db_manager.list_databases()
                if databases:
                    logger.info("Available databases:")
                    for db in databases:
                        size = self.db_manager.get_database_size(db)
                        logger.info(f"  {db} ({size})")
                else:
                    logger.info("No databases found")
                
            elif args.db_command == 'backup':
                success = self.db_manager.backup_database(args.db_name, args.backup_path)
                return 0 if success else 1
                
            elif args.db_command == 'restore':
                success = self.db_manager.restore_database(args.db_name, args.backup_path)
                return 0 if success else 1
                
            return 0
            
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return 1
    
    def cmd_config(self, args) -> int:
        """Handle configuration commands"""
        try:
            if args.list:
                config_text = config_manager.get_config_text()
                print(config_text)
                
            elif args.get:
                value = config_manager.get(args.get)
                print(f"{args.get}: {value}")
                
            elif args.set:
                key, value = args.set
                config_manager.set(key, value)
                if config_manager.save_config():
                    logger.success(f"Configuration updated: {key} = {value}")
                else:
                    logger.error("Failed to save configuration")
                    return 1
                    
            elif args.export:
                if config_manager.save_to_file(args.export):
                    logger.success(f"Configuration exported to {args.export}")
                else:
                    logger.error("Failed to export configuration")
                    return 1
                    
            elif args.import_:
                if config_manager.load_from_file(args.import_):
                    logger.success(f"Configuration imported from {args.import_}")
                else:
                    logger.error("Failed to import configuration")
                    return 1
                    
            elif args.reset:
                response = input("Reset configuration to defaults? [y/N]: ")
                if response.lower() in ['y', 'yes']:
                    config_manager.reset_to_defaults()
                    logger.success("Configuration reset to defaults")
                else:
                    logger.info("Operation cancelled")
                    
            return 0
            
        except Exception as e:
            logger.error(f"Configuration operation failed: {e}")
            return 1

def main():
    """Main entry point for CLI"""
    cli = WordPressCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
