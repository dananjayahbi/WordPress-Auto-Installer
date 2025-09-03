#!/usr/bin/env python3
"""
Modern Main Window for WordPress Auto Installer
Modular design with separate components
"""

import sys
import threading
from pathlib import Path
import tkinter as tk

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    MODERN_UI = True
except ImportError:
    import tkinter as tk
    import tkinter.ttk as ttk
    MODERN_UI = False

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..utils.logger import logger
from ..utils.config import config_manager
from ..core.database import DatabaseManager
from ..core.wordpress import WordPressInstaller

# Import modular components
from .components.console_panel import ConsolePanel
from .components.single_install_tab import SingleInstallTab
from .components.bulk_install_tab import BulkInstallTab
from .components.management_tab import ManagementTab
from .components.settings_tab import SettingsTab
from .components.toast_notifications import ToastManager

class ModernMainWindow:
    def __init__(self):
        # Initialize GUI framework
        if MODERN_UI:
            self.root = ttk.Window(themename="superhero")
            self.setup_rounded_styles()
        else:
            self.root = tk.Tk()
            
        self.root.title("WordPress Auto Installer - Modern Edition")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Lazy initialization for managers
        self._db_manager = None
        self._wp_installer = None
        
        # Initialize toast manager
        self.toast_manager = ToastManager()
        
        # Initialize components
        self.console_panel = ConsolePanel(self)
        
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Initialize GUI
        if not self.validate_startup_requirements():
            return  # Exit if requirements not met
            
        self.setup_modern_gui()
        
        # Test connections on startup
        threading.Thread(target=self.test_connections, daemon=True).start()
    
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
    
    def setup_rounded_styles(self):
        """Setup custom rounded styles for modern UI"""
        try:
            # Simple styling for ttkbootstrap compatibility
            logger.info("Setting up modern UI styles...")
            
        except Exception as e:
            logger.error(f"Failed to setup rounded styles: {e}")
    
    def validate_startup_requirements(self):
        """Validate that XAMPP and MySQL are running"""
        import subprocess
        import sys
        from tkinter import messagebox
        
        try:
            logger.info("Validating startup requirements...")
            
            # Check if MySQL service is running
            mysql_running = False
            try:
                # Try to check MySQL service on Windows
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], 
                                      capture_output=True, text=True, shell=True)
                mysql_running = 'mysqld.exe' in result.stdout
            except Exception:
                # Alternative check - try to connect to MySQL
                try:
                    success, _ = self.db_manager.test_connection()
                    mysql_running = success
                except Exception:
                    mysql_running = False
            
            if not mysql_running:
                logger.error("MySQL service not running")
                if MODERN_UI:
                    error_window = ttk.Window(themename="superhero")
                else:
                    error_window = tk.Tk()
                
                error_window.title("WordPress Auto Installer - Requirements Check")
                error_window.geometry("500x300")
                error_window.resizable(False, False)
                
                # Center the window
                error_window.update_idletasks()
                x = (error_window.winsys_x() + error_window.winfo_width()//2)
                y = (error_window.winsys_y() + error_window.winfo_height()//2)
                error_window.geometry(f"+{x}+{y}")
                
                # Create error message
                if MODERN_UI:
                    main_frame = ttk.Frame(error_window, bootstyle="danger")
                else:
                    main_frame = ttk.Frame(error_window)
                main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                if MODERN_UI:
                    title_label = ttk.Label(main_frame, text="⚠️ Requirements Not Met", 
                                          font=("Segoe UI", 16, "bold"), bootstyle="danger")
                else:
                    title_label = ttk.Label(main_frame, text="⚠️ Requirements Not Met", 
                                          font=("Segoe UI", 16, "bold"))
                title_label.pack(pady=10)
                
                message_text = """WordPress Auto Installer requires XAMPP to be running.

Please ensure:
• XAMPP is installed and running
• MySQL service is started in XAMPP Control Panel
• MySQL is accessible on localhost

Steps to fix:
1. Open XAMPP Control Panel
2. Start Apache and MySQL services
3. Restart this application"""
                
                message_label = ttk.Label(main_frame, text=message_text, font=("Segoe UI", 10))
                message_label.pack(pady=10)
                
                button_frame = ttk.Frame(main_frame)
                button_frame.pack(pady=20)
                
                if MODERN_UI:
                    retry_btn = ttk.Button(button_frame, text="🔄 Retry", bootstyle="success",
                                         command=lambda: self.retry_requirements_check(error_window))
                    exit_btn = ttk.Button(button_frame, text="❌ Exit", bootstyle="danger",
                                        command=lambda: self.exit_application(error_window))
                else:
                    retry_btn = ttk.Button(button_frame, text="🔄 Retry",
                                         command=lambda: self.retry_requirements_check(error_window))
                    exit_btn = ttk.Button(button_frame, text="❌ Exit",
                                        command=lambda: self.exit_application(error_window))
                
                retry_btn.pack(side="left", padx=10)
                exit_btn.pack(side="left", padx=10)
                
                error_window.protocol("WM_DELETE_WINDOW", lambda: self.exit_application(error_window))
                error_window.mainloop()
                
                return False
            
            logger.success("All startup requirements validated")
            return True
            
        except Exception as e:
            logger.error(f"Error validating requirements: {e}")
            return True  # Continue anyway if validation fails
    
    def retry_requirements_check(self, error_window):
        """Retry the requirements check"""
        error_window.destroy()
        if self.validate_startup_requirements():
            self.setup_modern_gui()
    
    def exit_application(self, error_window):
        """Exit the application"""
        error_window.destroy()
        self.root.quit()
        sys.exit(0)
    
    def setup_modern_gui(self):
        """Setup the modern GUI interface"""
        # Create header
        self.create_header()
        
        # Create main content area with console
        self.create_main_content()
        
        # Create status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create modern header with title and quick actions"""
        if MODERN_UI:
            header_frame = ttk.Frame(self.root, bootstyle="dark")
        else:
            header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        if MODERN_UI:
            title_label = ttk.Label(header_frame, text="WordPress Auto Installer", 
                                  font=("Segoe UI", 18, "bold"), bootstyle="inverse-dark")
        else:
            title_label = ttk.Label(header_frame, text="WordPress Auto Installer", 
                                  font=("Segoe UI", 18, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Quick action buttons
        if MODERN_UI:
            quick_frame = ttk.Frame(header_frame, bootstyle="dark")
        else:
            quick_frame = ttk.Frame(header_frame)
        quick_frame.grid(row=0, column=2, sticky="e")
        
        if MODERN_UI:
            test_btn = ttk.Button(quick_frame, text="🔄 Test Connections", 
                                bootstyle="success-outline", command=self.quick_test_connections)
            settings_btn = ttk.Button(quick_frame, text="⚙️ Settings", 
                                    bootstyle="info-outline", command=self.open_settings)
        else:
            test_btn = ttk.Button(quick_frame, text="🔄 Test Connections", 
                                command=self.quick_test_connections)
            settings_btn = ttk.Button(quick_frame, text="⚙️ Settings", 
                                    command=self.open_settings)
        
        test_btn.pack(side="left", padx=5)
        settings_btn.pack(side="left", padx=5)
    
    def create_main_content(self):
        """Create main content area with horizontal split"""
        # Main content frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.columnconfigure(0, weight=2)  # Tabs area gets 2/3
        main_frame.columnconfigure(1, weight=1)  # Console gets 1/3
        main_frame.rowconfigure(0, weight=1)
        
        # Left side - Tabbed interface
        self.create_tabbed_interface(main_frame)
        
        # Right side - Console
        self.console_panel.create_console_panel(main_frame, row=0, column=1)
    
    def create_tabbed_interface(self, parent):
        """Create tabbed interface for different functionalities"""
        if MODERN_UI:
            self.notebook = ttk.Notebook(parent, bootstyle="dark")
        else:
            self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Initialize tab components
        self.single_install_tab = SingleInstallTab(self, self.notebook)
        self.bulk_install_tab = BulkInstallTab(self, self.notebook)
        self.management_tab = ManagementTab(self, self.notebook)
        self.settings_tab = SettingsTab(self, self.notebook)
    
    def create_status_bar(self):
        """Create status bar"""
        if MODERN_UI:
            self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w", bootstyle="inverse")
        else:
            self.status_bar = ttk.Label(self.root, text="Ready", relief="sunken", anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
    
    def quick_test_connections(self):
        """Quick test of connections"""
        def test():
            self.update_status("Testing connections...")
            logger.info("Testing database connection...")
            db_success, db_msg = self.db_manager.test_connection()
            
            logger.info("Testing WP-CLI...")
            wp_success, wp_msg = self.wp_installer.test_wp_cli()
            
            if db_success and wp_success:
                self.toast_manager.show_toast("All connections successful!", "success")
                self.update_status("Ready")
            else:
                self.toast_manager.show_toast("Some connections failed. Check console.", "error")
                self.update_status("Connection issues detected")
        
        threading.Thread(target=test, daemon=True).start()
    
    def test_connections(self):
        """Test all connections on startup"""
        def test():
            try:
                logger.info("Starting WordPress Auto Installer...")
                logger.info("Testing connections...")
                
                # Test database
                db_success, db_msg = self.db_manager.test_connection()
                if not db_success:
                    logger.error(f"Database connection failed: {db_msg}")
                
                # Test WP-CLI
                wp_success, wp_msg = self.wp_installer.test_wp_cli()
                if not wp_success:
                    logger.error(f"WP-CLI test failed: {wp_msg}")
                
                if db_success and wp_success:
                    logger.success("All systems ready!")
                    self.update_status("Ready - All connections OK")
                else:
                    self.update_status("Warning - Check console for issues")
                    
            except Exception as e:
                logger.error(f"Startup test failed: {e}")
                self.update_status("Error - Check console")
        
        threading.Thread(target=test, daemon=True).start()
    
    def open_settings(self):
        """Open settings tab"""
        self.notebook.select(3)  # Settings is the 4th tab (index 3)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.configure(text=message)
    
    def run(self):
        """Run the application"""
        try:
            # Initial refresh of sites list
            if hasattr(self, 'management_tab'):
                self.management_tab.refresh_sites_list()
            
            logger.info("WordPress Auto Installer GUI started")
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"GUI error: {e}")
            self.toast_manager.show_toast(f"Application error: {str(e)}", "error")

# Alias for backward compatibility
MainWindow = ModernMainWindow

def run_gui():
    """Entry point for GUI"""
    app = ModernMainWindow()
    app.run()

if __name__ == "__main__":
    run_gui()
