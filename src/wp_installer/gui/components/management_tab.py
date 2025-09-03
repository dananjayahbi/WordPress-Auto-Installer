#!/usr/bin/env python3
"""
Management Tab Component
Handles WordPress site management, deletion, and operations
"""

import threading
import re
import webbrowser
from pathlib import Path
from tkinter import messagebox

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.logger import logger
from ...utils.config import config_manager

class ManagementTab:
    def __init__(self, main_window, notebook):
        self.main_window = main_window
        self.notebook = notebook
        
        # Create the tab
        self.create_tab()
    
    def create_tab(self):
        """Create site management tab"""
        if MODERN_UI:
            self.frame = ttk.Frame(self.notebook, bootstyle="light")
        else:
            self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="🔧 Site Management")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        # Components
        self.create_header()
        self.create_controls()
        self.create_sites_list()
    
    def create_header(self):
        """Create tab header"""
        if MODERN_UI:
            header_label = ttk.Label(self.frame, text="WordPress Site Management", 
                                   font=("Segoe UI", 14, "bold"), bootstyle="primary")
        else:
            header_label = ttk.Label(self.frame, text="WordPress Site Management", 
                                   font=("Segoe UI", 14, "bold"))
        header_label.grid(row=0, column=0, pady=10)
    
    def create_controls(self):
        """Create management controls"""
        # Main controls frame
        if MODERN_UI:
            controls_frame = ttk.Labelframe(self.frame, text="🎛️ Site Operations", 
                                          bootstyle="warning")
        else:
            controls_frame = ttk.Labelframe(self.frame, text="🎛️ Site Operations")
        controls_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Top row - Basic operations
        top_frame = ttk.Frame(controls_frame)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        if MODERN_UI:
            refresh_btn = ttk.Button(top_frame, text="🔄 Refresh List", 
                                   bootstyle="info",
                                   command=self.refresh_sites_list)
            phpmyadmin_btn = ttk.Button(top_frame, text="🗃️ Open phpMyAdmin", 
                                      bootstyle="success",
                                      command=self.open_phpmyadmin)
        else:
            refresh_btn = ttk.Button(top_frame, text="🔄 Refresh List", 
                                   command=self.refresh_sites_list)
            phpmyadmin_btn = ttk.Button(top_frame, text="�️ Open phpMyAdmin", 
                                      command=self.open_phpmyadmin)
        
        refresh_btn.pack(side="left", padx=5)
        phpmyadmin_btn.pack(side="left", padx=5)
        
        # Middle row - Site operations
        middle_frame = ttk.Frame(controls_frame)
        middle_frame.pack(fill="x", padx=5, pady=5)
        
        if MODERN_UI:
            open_website_btn = ttk.Button(middle_frame, text="🌐 Open Website", 
                                        bootstyle="primary",
                                        command=self.open_selected_website)
            open_admin_btn = ttk.Button(middle_frame, text="⚙️ Open WP-Admin", 
                                      bootstyle="primary-outline",
                                      command=self.open_selected_admin)
            reset_selected_btn = ttk.Button(middle_frame, text="� Reset Selected", 
                                          bootstyle="warning",
                                          command=self.reset_selected_sites)
        else:
            open_website_btn = ttk.Button(middle_frame, text="🌐 Open Website", 
                                        command=self.open_selected_website)
            open_admin_btn = ttk.Button(middle_frame, text="⚙️ Open WP-Admin", 
                                      command=self.open_selected_admin)
            reset_selected_btn = ttk.Button(middle_frame, text="🔄 Reset Selected", 
                                          command=self.reset_selected_sites)
        
        open_website_btn.pack(side="left", padx=5)
        open_admin_btn.pack(side="left", padx=5)
        reset_selected_btn.pack(side="left", padx=5)
        
        # Bottom row - Destructive operations
        bottom_frame = ttk.Frame(controls_frame)
        bottom_frame.pack(fill="x", padx=5, pady=5)
        
        if MODERN_UI:
            delete_selected_btn = ttk.Button(bottom_frame, text="🗑️ Delete Selected", 
                                           bootstyle="danger",
                                           command=self.delete_selected_sites)
            delete_all_btn = ttk.Button(bottom_frame, text="💥 Delete All Test Sites", 
                                      bootstyle="danger-outline",
                                      command=self.delete_all_test_sites)
        else:
            delete_selected_btn = ttk.Button(bottom_frame, text="🗑️ Delete Selected", 
                                           command=self.delete_selected_sites)
            delete_all_btn = ttk.Button(bottom_frame, text="💥 Delete All Test Sites", 
                                      command=self.delete_all_test_sites)
        
        delete_selected_btn.pack(side="left", padx=5)
        delete_all_btn.pack(side="left", padx=5)
    
    def create_sites_list(self):
        """Create sites list with treeview"""
        if MODERN_UI:
            list_frame = ttk.Labelframe(self.frame, text="📋 Installed Sites", bootstyle="info")
        else:
            list_frame = ttk.Labelframe(self.frame, text="📋 Installed Sites")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.sites_tree = ttk.Treeview(tree_frame, columns=("site", "database", "url", "status"), 
                                     show="headings", selectmode="extended")
        
        # Define columns
        self.sites_tree.heading("site", text="Site Name")
        self.sites_tree.heading("database", text="Database")
        self.sites_tree.heading("url", text="URL")
        self.sites_tree.heading("status", text="Status")
        
        self.sites_tree.column("site", width=150)
        self.sites_tree.column("database", width=150)
        self.sites_tree.column("url", width=200)
        self.sites_tree.column("status", width=100)
        
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", 
                                     command=self.sites_tree.yview)
        self.sites_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.sites_tree.grid(row=0, column=0, sticky="nsew")
        tree_scrollbar.grid(row=0, column=1, sticky="ns")
    
    def refresh_sites_list(self):
        """Refresh the sites list"""
        def refresh():
            try:
                # Clear current items
                for item in self.sites_tree.get_children():
                    self.sites_tree.delete(item)
                
                # Get htdocs path
                htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
                base_url = config_manager.get('wordpress.base_url', 'http://localhost')
                
                if not htdocs_path.exists():
                    logger.error(f"htdocs path not found: {htdocs_path}")
                    return
                
                # Scan for WordPress sites
                for site_dir in htdocs_path.iterdir():
                    if site_dir.is_dir():
                        wp_config = site_dir / 'wp-config.php'
                        if wp_config.exists():
                            # Extract database name from wp-config.php
                            db_name = self.extract_db_name_from_config(wp_config)
                            
                            # Check if database exists
                            status = "Active" if self.main_window.db_manager.database_exists(db_name) else "DB Missing"
                            
                            url = f"{base_url}/{site_dir.name}"
                            
                            self.sites_tree.insert("", "end", values=(
                                site_dir.name, db_name, url, status
                            ))
                
                logger.info("Sites list refreshed")
                
            except Exception as e:
                logger.error(f"Failed to refresh sites list: {e}")
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def open_phpmyadmin(self):
        """Open phpMyAdmin in browser"""
        try:
            phpmyadmin_url = config_manager.get('mysql.phpmyadmin_url', 'http://localhost/phpmyadmin')
            webbrowser.open(phpmyadmin_url)
            logger.info(f"Opening phpMyAdmin: {phpmyadmin_url}")
            self.main_window.toast_manager.show_toast("phpMyAdmin opened in browser", "success")
        except Exception as e:
            logger.error(f"Failed to open phpMyAdmin: {e}")
            self.main_window.toast_manager.show_toast("Failed to open phpMyAdmin", "error")
    
    def open_selected_website(self):
        """Open selected site's website in browser"""
        selected_items = self.sites_tree.selection()
        if not selected_items:
            self.main_window.toast_manager.show_toast("Please select a site to open", "warning")
            return
        
        try:
            for item in selected_items:
                site_values = self.sites_tree.item(item)['values']
                site_url = site_values[2]  # URL column
                webbrowser.open(site_url)
                logger.info(f"Opening website: {site_url}")
            
            self.main_window.toast_manager.show_toast("Website(s) opened in browser", "success")
        except Exception as e:
            logger.error(f"Failed to open website: {e}")
            self.main_window.toast_manager.show_toast("Failed to open website", "error")
    
    def open_selected_admin(self):
        """Open selected site's WP-Admin in browser"""
        selected_items = self.sites_tree.selection()
        if not selected_items:
            self.main_window.toast_manager.show_toast("Please select a site to open", "warning")
            return
        
        try:
            for item in selected_items:
                site_values = self.sites_tree.item(item)['values']
                site_url = site_values[2]  # URL column
                admin_url = f"{site_url}/wp-admin"
                webbrowser.open(admin_url)
                logger.info(f"Opening WP-Admin: {admin_url}")
            
            self.main_window.toast_manager.show_toast("WP-Admin opened in browser", "success")
        except Exception as e:
            logger.error(f"Failed to open WP-Admin: {e}")
            self.main_window.toast_manager.show_toast("Failed to open WP-Admin", "error")
    
    def reset_selected_sites(self):
        """Reset selected sites to clean WordPress installation"""
        selected_items = self.sites_tree.selection()
        if not selected_items:
            self.main_window.toast_manager.show_toast("Please select sites to reset", "warning")
            return
        
        site_names = [self.sites_tree.item(item)['values'][0] for item in selected_items]
        
        if not messagebox.askyesno("Confirm Reset", 
                                 f"Are you sure you want to reset {len(site_names)} site(s)?\n"
                                 f"This will delete all content and reinstall WordPress.\n\n"
                                 f"Sites: {', '.join(site_names)}"):
            return
        
        def reset_sites():
            try:
                self.main_window.update_status("Resetting sites...")
                
                for site_name in site_names:
                    logger.info(f"Resetting site: {site_name}")
                    
                    # Get site info
                    site_values = None
                    for item in selected_items:
                        if self.sites_tree.item(item)['values'][0] == site_name:
                            site_values = self.sites_tree.item(item)['values']
                            break
                    
                    if not site_values:
                        continue
                    
                    db_name = site_values[1]
                    
                    # Reset the site using WordPress installer
                    if self.main_window.wp_installer.reset_site(site_name, db_name):
                        logger.success(f"Site {site_name} reset successfully")
                    else:
                        logger.error(f"Failed to reset site {site_name}")
                
                self.refresh_sites_list()
                self.main_window.update_status("Ready")
                self.main_window.toast_manager.show_toast("Sites reset completed", "success")
                
            except Exception as e:
                logger.error(f"Error resetting sites: {e}")
                self.main_window.toast_manager.show_toast("Error resetting sites", "error")
                self.main_window.update_status("Ready")
        
        threading.Thread(target=reset_sites, daemon=True).start()

    def extract_db_name_from_config(self, config_path):
        """Extract database name from wp-config.php"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for DB_NAME definition
                match = re.search(r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]", content)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return "Unknown"
    
    def delete_selected_sites(self):
        """Delete selected sites"""
        selected_items = self.sites_tree.selection()
        if not selected_items:
            self.main_window.toast_manager.show_toast("Please select sites to delete", "warning")
            return
        
        site_names = [self.sites_tree.item(item)['values'][0] for item in selected_items]
        
        if messagebox.askyesno("Confirm Deletion", 
                             f"Delete {len(site_names)} selected site(s)?\n\nThis will remove:\n"
                             f"- Site files\n- Database\n\nThis action cannot be undone."):
            
            def delete_sites():
                try:
                    for site_name in site_names:
                        logger.info(f"Deleting site: {site_name}")
                        self.main_window.wp_installer.delete_site(site_name)
                    
                    self.main_window.toast_manager.show_toast(f"Deleted {len(site_names)} site(s)", "success")
                    self.refresh_sites_list()
                    
                except Exception as e:
                    logger.error(f"Failed to delete sites: {e}")
                    self.main_window.toast_manager.show_toast(f"Error deleting sites: {e}", "error")
            
            threading.Thread(target=delete_sites, daemon=True).start()
    
    def delete_all_test_sites(self):
        """Delete all test sites (sites starting with test prefix)"""
        if messagebox.askyesno("Confirm Bulk Deletion", 
                             "Delete ALL test sites?\n\n"
                             "This will remove all sites and databases whose names start with common test prefixes.\n\n"
                             "This action cannot be undone!"):
            
            def delete_all():
                try:
                    htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
                    test_prefixes = ['test', 'wp_test', 'sample', 'demo', 'dev']
                    
                    deleted_count = 0
                    for site_dir in htdocs_path.iterdir():
                        if site_dir.is_dir():
                            site_name = site_dir.name
                            # Check if it's a test site
                            if any(site_name.lower().startswith(prefix) for prefix in test_prefixes):
                                wp_config = site_dir / 'wp-config.php'
                                if wp_config.exists():
                                    logger.info(f"Deleting test site: {site_name}")
                                    self.main_window.wp_installer.delete_site(site_name)
                                    deleted_count += 1
                    
                    self.main_window.toast_manager.show_toast(f"Deleted {deleted_count} test site(s)", "success")
                    self.refresh_sites_list()
                    
                except Exception as e:
                    logger.error(f"Failed to delete test sites: {e}")
                    self.main_window.toast_manager.show_toast(f"Error deleting test sites: {e}", "error")
            
            threading.Thread(target=delete_all, daemon=True).start()
