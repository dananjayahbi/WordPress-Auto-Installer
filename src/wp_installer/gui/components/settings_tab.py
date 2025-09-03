#!/usr/bin/env python3
"""
Settings Tab Component
Handles application configuration management
"""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import shutil
import zipfile

try:
    import ttkbootstrap as ttk
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.helpers import Helpers
from ...utils.paths import PathUtils

from ...utils.logger import logger
from ...utils.config import config_manager

class SettingsTab:
    def __init__(self, main_window, notebook):
        self.main_window = main_window
        self.notebook = notebook
        
        # Create the tab
        self.create_tab()
    
    def create_tab(self):
        """Create settings configuration tab"""
        if MODERN_UI:
            self.frame = ttk.Frame(self.notebook, bootstyle="light")
        else:
            self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="⚙️ Settings")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Components
        self.create_header()
        self.create_settings_form()
    
    def create_header(self):
        """Create tab header"""
        if MODERN_UI:
            header_label = ttk.Label(self.frame, text="Application Settings", 
                                   font=("Segoe UI", 14, "bold"), bootstyle="primary")
        else:
            header_label = ttk.Label(self.frame, text="Application Settings", 
                                   font=("Segoe UI", 14, "bold"))
        header_label.grid(row=0, column=0, pady=10)
    
    def create_settings_form(self):
        """Create comprehensive settings form"""
        # Scrollable frame for settings
        if MODERN_UI:
            settings_container = ttk.Labelframe(self.frame, text="🔧 Configuration", bootstyle="info")
        else:
            settings_container = ttk.Labelframe(self.frame, text="🔧 Configuration")
        settings_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        settings_container.columnconfigure(0, weight=1)
        settings_container.rowconfigure(0, weight=1)
        
        # Create scrollable canvas
        canvas = tk.Canvas(settings_container)
        scrollbar = ttk.Scrollbar(settings_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        # Create setting sections
        self.create_xampp_settings(scrollable_frame)
        self.create_mysql_settings(scrollable_frame)
        self.create_wordpress_settings(scrollable_frame)
        self.create_wpcli_settings(scrollable_frame)
        self.create_php_setup_section(scrollable_frame)
        self.create_wpcli_setup_section(scrollable_frame)
        self.create_action_buttons(scrollable_frame)
        
        # Load current settings
        self.load_settings()
    
    def create_xampp_settings(self, parent):
        """Create XAMPP configuration section"""
        if MODERN_UI:
            xampp_frame = ttk.Labelframe(parent, text="📁 XAMPP Configuration", bootstyle="primary")
        else:
            xampp_frame = ttk.Labelframe(parent, text="📁 XAMPP Configuration")
        xampp_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        xampp_frame.columnconfigure(1, weight=1)
        
        # XAMPP htdocs path
        ttk.Label(xampp_frame, text="XAMPP htdocs Path:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.htdocs_path = ttk.Entry(xampp_frame, font=("Segoe UI", 9))
        self.htdocs_path.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(xampp_frame, text="📁", command=lambda: self.browse_folder(self.htdocs_path)).grid(row=0, column=2, padx=2)
    
    def create_mysql_settings(self, parent):
        """Create MySQL configuration section"""
        if MODERN_UI:
            mysql_frame = ttk.Labelframe(parent, text="🗄️ MySQL Configuration", bootstyle="success")
        else:
            mysql_frame = ttk.Labelframe(parent, text="🗄️ MySQL Configuration")
        mysql_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        mysql_frame.columnconfigure(1, weight=1)
        
        # MySQL settings
        ttk.Label(mysql_frame, text="MySQL Host:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.mysql_host = ttk.Entry(mysql_frame, font=("Segoe UI", 9))
        self.mysql_host.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(mysql_frame, text="MySQL User:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.mysql_user = ttk.Entry(mysql_frame, font=("Segoe UI", 9))
        self.mysql_user.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(mysql_frame, text="MySQL Password:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.mysql_password = ttk.Entry(mysql_frame, show="*", font=("Segoe UI", 9))
        self.mysql_password.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    
    def create_wordpress_settings(self, parent):
        """Create WordPress defaults section"""
        if MODERN_UI:
            wp_frame = ttk.Labelframe(parent, text="🌐 WordPress Defaults", bootstyle="warning")
        else:
            wp_frame = ttk.Labelframe(parent, text="🌐 WordPress Defaults")
        wp_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        wp_frame.columnconfigure(1, weight=1)
        
        # WordPress settings
        ttk.Label(wp_frame, text="Admin Username:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.admin_user = ttk.Entry(wp_frame, font=("Segoe UI", 9))
        self.admin_user.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(wp_frame, text="Admin Password:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.admin_password = ttk.Entry(wp_frame, show="*", font=("Segoe UI", 9))
        self.admin_password.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(wp_frame, text="Admin Email:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.admin_email = ttk.Entry(wp_frame, font=("Segoe UI", 9))
        self.admin_email.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Label(wp_frame, text="Base URL:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.base_url = ttk.Entry(wp_frame, font=("Segoe UI", 9))
        self.base_url.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        
        # WordPress ZIP file management
        ttk.Label(wp_frame, text="WordPress ZIP:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        zip_frame = ttk.Frame(wp_frame)
        zip_frame.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        zip_frame.columnconfigure(0, weight=1)
        
        self.wp_zip_path = ttk.Entry(zip_frame, font=("Segoe UI", 9))
        self.wp_zip_path.grid(row=0, column=0, sticky="ew", padx=2)
        
        if MODERN_UI:
            upload_btn = ttk.Button(zip_frame, text="📤 Upload New", 
                                  bootstyle="primary-outline", command=self.upload_wordpress_zip)
        else:
            upload_btn = ttk.Button(zip_frame, text="📤 Upload New", command=self.upload_wordpress_zip)
        upload_btn.grid(row=0, column=1, padx=2)
    
    def create_wpcli_settings(self, parent):
        """Create WP-CLI configuration section"""
        if MODERN_UI:
            wpcli_frame = ttk.Labelframe(parent, text="⚡ WP-CLI Configuration", bootstyle="danger")
        else:
            wpcli_frame = ttk.Labelframe(parent, text="⚡ WP-CLI Configuration")
        wpcli_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        wpcli_frame.columnconfigure(1, weight=1)
        
        ttk.Label(wpcli_frame, text="WP-CLI Path:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.wpcli_path = ttk.Entry(wpcli_frame, font=("Segoe UI", 9))
        self.wpcli_path.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(wpcli_frame, text="📁", command=lambda: self.browse_file(self.wpcli_path)).grid(row=0, column=2, padx=2)
    
    def create_action_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        if MODERN_UI:
            load_btn = ttk.Button(button_frame, text="🔄 Load Current Settings", 
                                bootstyle="info", command=self.load_settings)
            save_btn = ttk.Button(button_frame, text="💾 Save Settings", 
                                bootstyle="success", command=self.save_settings)
            reset_btn = ttk.Button(button_frame, text="🔙 Reset to Defaults", 
                                 bootstyle="warning", command=self.reset_settings)
        else:
            load_btn = ttk.Button(button_frame, text="🔄 Load Current Settings", command=self.load_settings)
            save_btn = ttk.Button(button_frame, text="💾 Save Settings", command=self.save_settings)
            reset_btn = ttk.Button(button_frame, text="🔙 Reset to Defaults", command=self.reset_settings)
        
        load_btn.pack(side="left", padx=5)
        save_btn.pack(side="left", padx=5)
        reset_btn.pack(side="left", padx=5)
    
    def browse_folder(self, entry_widget):
        """Browse for folder and update entry widget"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder_path)
    
    def browse_file(self, entry_widget):
        """Browse for file and update entry widget"""
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)
    
    def load_settings(self):
        """Load current settings into the form"""
        try:
            # XAMPP settings
            self.htdocs_path.delete(0, tk.END)
            self.htdocs_path.insert(0, config_manager.get('xampp.htdocs_path', ''))
            
            # MySQL settings
            self.mysql_host.delete(0, tk.END)
            self.mysql_host.insert(0, config_manager.get('xampp.mysql_host', 'localhost'))
            
            self.mysql_user.delete(0, tk.END)
            self.mysql_user.insert(0, config_manager.get('xampp.mysql_user', 'root'))
            
            self.mysql_password.delete(0, tk.END)
            self.mysql_password.insert(0, config_manager.get('xampp.mysql_password', ''))
            
            # WordPress settings
            self.admin_user.delete(0, tk.END)
            self.admin_user.insert(0, config_manager.get('wordpress.admin_user', 'admin'))
            
            self.admin_password.delete(0, tk.END)
            self.admin_password.insert(0, config_manager.get('wordpress.admin_password', ''))
            
            self.admin_email.delete(0, tk.END)
            self.admin_email.insert(0, config_manager.get('wordpress.admin_email', ''))
            
            self.base_url.delete(0, tk.END)
            self.base_url.insert(0, config_manager.get('wordpress.base_url', 'http://localhost'))
            
            # WordPress ZIP path
            self.wp_zip_path.delete(0, tk.END)
            # WordPress ZIP file path (show relative path for display)
            default_zip_path = "assets/wordpress-6.8.2.zip"
            stored_path = config_manager.get('wordpress.zip_path', default_zip_path)
            
            # If stored path is absolute, convert to relative for display
            display_path = PathUtils.make_relative_to_app(stored_path)
            self.wp_zip_path.insert(0, display_path)
            
            # WP-CLI settings
            self.wpcli_path.delete(0, tk.END)
            # Try to get current WP-CLI path
            wpcli_path = getattr(self.main_window.wp_installer, 'wp_cli_command', ['wp'])
            if isinstance(wpcli_path, list) and len(wpcli_path) > 1:
                self.wpcli_path.insert(0, ' '.join(wpcli_path))
            else:
                self.wpcli_path.insert(0, 'wp')
            
            logger.info("Settings loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.main_window.toast_manager.show_toast(f"Failed to load settings: {e}", "error")
    
    def save_settings(self):
        """Save settings from form"""
        try:
            # Update configuration
            config_manager.set('xampp.htdocs_path', self.htdocs_path.get())
            config_manager.set('xampp.mysql_host', self.mysql_host.get())
            config_manager.set('xampp.mysql_user', self.mysql_user.get())
            config_manager.set('xampp.mysql_password', self.mysql_password.get())
            
            config_manager.set('wordpress.admin_user', self.admin_user.get())
            config_manager.set('wordpress.admin_password', self.admin_password.get())
            config_manager.set('wordpress.admin_email', self.admin_email.get())
            config_manager.set('wordpress.base_url', self.base_url.get())
            
            # Save configuration
            if config_manager.save_config():
                self.main_window.toast_manager.show_toast("Settings saved successfully!", "success")
                
                # Reinitialize managers with new settings
                self.main_window._db_manager = None
                self.main_window._wp_installer = None
                
                # Test connections with new settings
                threading.Thread(target=self.main_window.test_connections, daemon=True).start()
            else:
                self.main_window.toast_manager.show_toast("Failed to save settings", "error")
                
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            self.main_window.toast_manager.show_toast(f"Failed to save settings: {e}", "error")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all settings to default values?"):
            try:
                # Load default configuration
                default_config = config_manager.get_default_config()
                config_manager.config = default_config
                
                # Reload the form
                self.load_settings()
                
                self.main_window.toast_manager.show_toast("Settings reset to defaults", "success")
                
            except Exception as e:
                logger.error(f"Failed to reset settings: {e}")
                self.main_window.toast_manager.show_toast(f"Failed to reset settings: {e}", "error")
    
    def upload_wordpress_zip(self):
        """Upload a new WordPress ZIP file"""
        try:
            # Select new WordPress ZIP file
            file_path = filedialog.askopenfilename(
                title="Select WordPress ZIP File",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
                defaultextension=".zip"
            )
            
            if not file_path:
                return
            
            # Validate that it's a valid ZIP file
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Check if it contains WordPress files
                    file_list = zip_ref.namelist()
                    has_wp_config = any('wp-config-sample.php' in f for f in file_list)
                    has_wp_admin = any('wp-admin/' in f for f in file_list)
                    
                    if not (has_wp_config and has_wp_admin):
                        messagebox.showerror("Invalid File", 
                                           "This doesn't appear to be a valid WordPress ZIP file.\n"
                                           "Please select a valid WordPress installation archive.")
                        return
                        
            except zipfile.BadZipFile:
                messagebox.showerror("Invalid File", "The selected file is not a valid ZIP archive.")
                return
            
            # Get the target assets directory using helper
            from ...utils.paths import PathUtils
            assets_dir = PathUtils.get_app_data_dir("assets")
            
            # Use the expected filename
            target_path = assets_dir / "wordpress-6.8.2.zip"
            
            # Confirm overwrite if file exists
            if target_path.exists():
                if not messagebox.askyesno("Overwrite File", 
                                         f"Replace existing WordPress file?\n{target_path}"):
                    return
            
            # Copy the file
            shutil.copy2(file_path, target_path)
            
            # Update the entry field with relative path
            relative_path = PathUtils.make_relative_to_app(str(target_path))
            self.wp_zip_path.delete(0, tk.END)
            self.wp_zip_path.insert(0, relative_path)
            
            # Update configuration with relative path
            config_manager.set('wordpress.zip_path', relative_path)
            config_manager.save_config()
            
            logger.success(f"WordPress ZIP file updated: {target_path}")
            self.main_window.toast_manager.show_toast("WordPress ZIP file updated successfully!", "success")
            
        except Exception as e:
            logger.error(f"Failed to upload WordPress ZIP: {e}")
            self.main_window.toast_manager.show_toast(f"Failed to upload WordPress ZIP: {e}", "error")
    
    def create_php_setup_section(self, parent):
        """Create PHP setup section"""
        row = 14
        
        # PHP Setup section
        php_frame = ttk.LabelFrame(parent, text="PHP Setup", padding=10)
        php_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        php_frame.columnconfigure(1, weight=1)
        
        # PHP status
        ttk.Label(php_frame, text="PHP Status:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.php_status_var = tk.StringVar(value="Checking...")
        self.php_status_label = ttk.Label(php_frame, textvariable=self.php_status_var)
        self.php_status_label.grid(row=0, column=1, sticky="w")
        
        # Check PHP button
        self.check_php_btn = ttk.Button(php_frame, text="Check PHP", command=self.check_php_installation)
        self.check_php_btn.grid(row=0, column=2, padx=(10, 0))
        
        # Setup PHP button (initially hidden)
        self.setup_php_btn = ttk.Button(php_frame, text="Setup PHP Path", command=self.setup_php_path)
        self.setup_php_btn.grid(row=1, column=1, pady=(5, 0))
        self.setup_php_btn.grid_remove()  # Hide initially
        
        # Check PHP on startup
        self.main_window.root.after(100, self.check_php_installation)
    
    def create_wpcli_setup_section(self, parent):
        """Create WP-CLI setup section"""
        row = 15
        
        # WP-CLI Setup section
        wpcli_frame = ttk.LabelFrame(parent, text="WP-CLI Auto-Setup", padding=10)
        wpcli_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        wpcli_frame.columnconfigure(1, weight=1)
        
        # WP-CLI status
        ttk.Label(wpcli_frame, text="WP-CLI Status:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.wpcli_status_var = tk.StringVar(value="Checking...")
        self.wpcli_status_label = ttk.Label(wpcli_frame, textvariable=self.wpcli_status_var)
        self.wpcli_status_label.grid(row=0, column=1, sticky="w")
        
        # Install WP-CLI button
        self.install_wpcli_btn = ttk.Button(wpcli_frame, text="Auto-Install WP-CLI", command=self.install_wp_cli)
        self.install_wpcli_btn.grid(row=1, column=1, pady=(5, 0))
        
        # Check WP-CLI on startup
        self.main_window.root.after(200, self.check_wp_cli_status)
    
    def check_php_installation(self):
        """Check if PHP is accessible"""
        self.php_status_var.set("Checking...")
        self.check_php_btn.configure(state="disabled")
        
        def check_php():
            try:
                is_available, message = Helpers.check_php_installation()
                if is_available:
                    self.php_status_var.set(f"✓ {message}")
                    self.setup_php_btn.grid_remove()
                else:
                    self.php_status_var.set(f"✗ {message}")
                    self.setup_php_btn.grid()
            except Exception as e:
                self.php_status_var.set(f"✗ Error: {e}")
                self.setup_php_btn.grid()
            finally:
                self.check_php_btn.configure(state="normal")
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=check_php, daemon=True).start()
    
    def setup_php_path(self):
        """Setup PHP path in system variables"""
        php_exe = filedialog.askopenfilename(
            title="Select PHP executable (php.exe)",
            filetypes=[("PHP Executable", "php.exe"), ("All Files", "*.*")]
        )
        
        if php_exe:
            def setup_php():
                try:
                    if Helpers.setup_php_path(php_exe):
                        self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                            "PHP path added to system variables successfully!", "success"))
                        # Recheck PHP installation
                        self.main_window.root.after(1000, self.check_php_installation)
                    else:
                        self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                            "Failed to add PHP path to system variables", "error"))
                except Exception as e:
                    self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                        f"Error setting up PHP: {e}", "error"))
            
            threading.Thread(target=setup_php, daemon=True).start()
    
    def check_wp_cli_status(self):
        """Check WP-CLI installation status"""
        self.wpcli_status_var.set("Checking...")
        
        def check_wpcli():
            try:
                wp_cli = Helpers.find_wp_cli_executable()
                if wp_cli:
                    self.wpcli_status_var.set("✓ WP-CLI found and working")
                    self.install_wpcli_btn.configure(text="WP-CLI Already Installed", state="disabled")
                else:
                    self.wpcli_status_var.set("✗ WP-CLI not found")
                    self.install_wpcli_btn.configure(text="Auto-Install WP-CLI", state="normal")
            except Exception as e:
                self.wpcli_status_var.set(f"✗ Error: {e}")
        
        threading.Thread(target=check_wpcli, daemon=True).start()
    
    def install_wp_cli(self):
        """Install WP-CLI automatically"""
        self.install_wpcli_btn.configure(state="disabled", text="Installing...")
        
        def install_wpcli():
            try:
                if Helpers.install_wp_cli():
                    self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                        "WP-CLI installed successfully!", "success"))
                    # Recheck WP-CLI status
                    self.main_window.root.after(1000, self.check_wp_cli_status)
                else:
                    self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                        "Failed to install WP-CLI", "error"))
                    self.install_wpcli_btn.configure(state="normal", text="Auto-Install WP-CLI")
            except Exception as e:
                self.main_window.root.after(0, lambda: self.main_window.toast_manager.show_toast(
                    f"Error installing WP-CLI: {e}", "error"))
                self.install_wpcli_btn.configure(state="normal", text="Auto-Install WP-CLI")
        
        threading.Thread(target=install_wpcli, daemon=True).start()
