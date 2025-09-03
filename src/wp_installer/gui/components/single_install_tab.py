#!/usr/bin/env python3
"""
Single Installation Tab Component
Handles single WordPress site installation
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

try:
    import ttkbootstrap as ttk
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.logger import logger
from ...utils.config import config_manager

class SingleInstallTab:
    def __init__(self, main_window, notebook):
        self.main_window = main_window
        self.notebook = notebook
        
        # Create the tab
        self.create_tab()
    
    def create_tab(self):
        """Create single WordPress installation tab"""
        if MODERN_UI:
            self.frame = ttk.Frame(self.notebook, bootstyle="light")
        else:
            self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="🏠 Single Install")
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        # Header
        self.create_header()
        
        # Installation form
        self.create_installation_form()
    
    def create_header(self):
        """Create tab header"""
        if MODERN_UI:
            header_label = ttk.Label(self.frame, text="Single WordPress Installation", 
                                   font=("Segoe UI", 14, "bold"), bootstyle="primary")
        else:
            header_label = ttk.Label(self.frame, text="Single WordPress Installation", 
                                   font=("Segoe UI", 14, "bold"))
        header_label.grid(row=0, column=0, pady=10)
    
    def create_installation_form(self):
        """Create form for single installation"""
        if MODERN_UI:
            form_frame = ttk.Labelframe(self.frame, text="📝 Site Configuration", bootstyle="info")
        else:
            form_frame = ttk.Labelframe(self.frame, text="📝 Site Configuration")
        form_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        form_frame.columnconfigure(1, weight=1)
        
        # Site name
        ttk.Label(form_frame, text="Site Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.site_name = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.site_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.site_name.insert(0, "my-wp-site")
        
        # Site title
        ttk.Label(form_frame, text="Site Title:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.site_title = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.site_title.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.site_title.insert(0, "My WordPress Site")
        
        # Database name
        ttk.Label(form_frame, text="Database Name:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.db_name = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.db_name.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Auto-generate database name based on site name
        def update_db_name(*args):
            site_name = self.site_name.get().replace('-', '_').replace(' ', '_')
            self.db_name.delete(0, tk.END)
            self.db_name.insert(0, f"wp_{site_name}")
        
        self.site_name.bind('<KeyRelease>', update_db_name)
        update_db_name()  # Initial update
        
        # Theme selection
        ttk.Label(form_frame, text="Theme:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.theme = ttk.Combobox(form_frame, values=[
            "twentytwentyfour", "twentytwentythree", "twentytwentytwo", "astra", "generatepress"
        ], font=("Segoe UI", 10))
        self.theme.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.theme.set("twentytwentyfour")
        
        # Install button
        if MODERN_UI:
            install_btn = ttk.Button(form_frame, text="🚀 Install WordPress", 
                                   bootstyle="success", command=self.install_site)
        else:
            install_btn = ttk.Button(form_frame, text="🚀 Install WordPress", 
                                   command=self.install_site)
        install_btn.grid(row=4, column=0, columnspan=2, pady=20)
    
    def install_site(self):
        """Install a single WordPress site"""
        def install():
            try:
                site_name = self.site_name.get().strip()
                site_title = self.site_title.get().strip()
                db_name = self.db_name.get().strip()
                theme = self.theme.get()
                
                if not all([site_name, site_title, db_name]):
                    self.main_window.toast_manager.show_toast("Please fill in all required fields", "error")
                    return
                
                logger.info(f"Starting installation of '{site_name}'...")
                self.main_window.update_status(f"Installing {site_name}...")
                
                # Check if site already exists
                htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
                site_path = htdocs_path / site_name
                
                if site_path.exists():
                    if not messagebox.askyesno("Site Exists", 
                                             f"Site '{site_name}' already exists. Replace it?"):
                        return
                    self.main_window.wp_installer.delete_site(site_name)
                
                # Create the site
                success = self.main_window.wp_installer.create_complete_site(
                    site_name=site_name,
                    site_title=site_title,
                    db_name=db_name,
                    theme=theme
                )
                
                if success:
                    self.main_window.toast_manager.show_toast(f"Site '{site_name}' installed successfully!", "success")
                    self.main_window.update_status("Ready")
                    # Refresh sites list if management tab exists
                    if hasattr(self.main_window, 'management_tab'):
                        self.main_window.management_tab.refresh_sites_list()
                else:
                    self.main_window.toast_manager.show_toast(f"Failed to install '{site_name}'", "error")
                    self.main_window.update_status("Installation failed")
                    
            except Exception as e:
                logger.error(f"Installation error: {e}")
                self.main_window.toast_manager.show_toast(f"Installation error: {e}", "error")
                self.main_window.update_status("Error")
        
        threading.Thread(target=install, daemon=True).start()
