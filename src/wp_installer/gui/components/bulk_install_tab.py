#!/usr/bin/env python3
"""
Bulk Installation Tab Component
Handles bulk WordPress site installation with templates
"""

import threading
import time
import tkinter as tk
from pathlib import Path

try:
    import ttkbootstrap as ttk
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.logger import logger
from ...utils.config import config_manager

class BulkInstallTab:
    def __init__(self, main_window, notebook):
        self.main_window = main_window
        self.notebook = notebook
        self.bulk_running = False
        
        # Create the tab
        self.create_tab()
    
    def create_tab(self):
        """Create bulk test installation tab"""
        if MODERN_UI:
            self.frame = ttk.Frame(self.notebook, bootstyle="light")
        else:
            self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="🔄 Bulk Test Install")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(3, weight=1)
        
        # Components
        self.create_header()
        self.create_template_config()
        self.create_controls()
        self.create_progress_display()
    
    def create_header(self):
        """Create tab header"""
        if MODERN_UI:
            header_label = ttk.Label(self.frame, text="Bulk Test Site Installation", 
                                   font=("Segoe UI", 14, "bold"), bootstyle="primary")
        else:
            header_label = ttk.Label(self.frame, text="Bulk Test Site Installation", 
                                   font=("Segoe UI", 14, "bold"))
        header_label.grid(row=0, column=0, pady=10)
    
    def create_template_config(self):
        """Create template configuration for bulk installation"""
        if MODERN_UI:
            template_frame = ttk.Labelframe(self.frame, text="📋 Template Configuration", bootstyle="info")
        else:
            template_frame = ttk.Labelframe(self.frame, text="📋 Template Configuration")
        template_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        template_frame.columnconfigure(1, weight=1)
        
        # Base site name
        ttk.Label(template_frame, text="Base Site Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.base_name = ttk.Entry(template_frame, font=("Segoe UI", 10))
        self.base_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.base_name.insert(0, "test-site")
        
        # Site title template
        ttk.Label(template_frame, text="Site Title Template:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.title_template = ttk.Entry(template_frame, font=("Segoe UI", 10))
        self.title_template.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.title_template.insert(0, "Test Site {number}")
        
        # Theme selection
        ttk.Label(template_frame, text="Theme:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.theme = ttk.Combobox(template_frame, values=[
            "twentytwentyfour", "twentytwentythree", "twentytwentytwo", "astra", "generatepress"
        ], font=("Segoe UI", 10))
        self.theme.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.theme.set("twentytwentyfour")
    
    def create_controls(self):
        """Create controls for bulk installation"""
        if MODERN_UI:
            controls_frame = ttk.Labelframe(self.frame, text="🎛️ Installation Controls", bootstyle="warning")
        else:
            controls_frame = ttk.Labelframe(self.frame, text="🎛️ Installation Controls")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        controls_frame.columnconfigure(1, weight=1)
        
        # Number of installations
        ttk.Label(controls_frame, text="Number of Sites:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.count = ttk.Spinbox(controls_frame, from_=1, to=20, font=("Segoe UI", 10))
        self.count.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.count.set("3")
        
        # Start button
        if MODERN_UI:
            self.start_btn = ttk.Button(controls_frame, text="🚀 Start Bulk Installation", 
                                       bootstyle="success", command=self.start_bulk_installation)
        else:
            self.start_btn = ttk.Button(controls_frame, text="🚀 Start Bulk Installation", 
                                       command=self.start_bulk_installation)
        self.start_btn.grid(row=0, column=2, padx=20, pady=5)
        
        # Stop button
        if MODERN_UI:
            self.stop_btn = ttk.Button(controls_frame, text="⏹️ Stop", 
                                      bootstyle="danger", command=self.stop_bulk_installation, state="disabled")
        else:
            self.stop_btn = ttk.Button(controls_frame, text="⏹️ Stop", 
                                      command=self.stop_bulk_installation, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=5, pady=5)
    
    def create_progress_display(self):
        """Create progress display for bulk installation"""
        if MODERN_UI:
            progress_frame = ttk.Labelframe(self.frame, text="📊 Installation Progress", bootstyle="success")
        else:
            progress_frame = ttk.Labelframe(self.frame, text="📊 Installation Progress")
        progress_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        # Progress bar
        if MODERN_UI:
            self.progress = ttk.Progressbar(progress_frame, bootstyle="success-striped")
        else:
            self.progress = ttk.Progressbar(progress_frame)
        self.progress.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Progress text
        progress_text_frame = ttk.Frame(progress_frame)
        progress_text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        progress_text_frame.columnconfigure(0, weight=1)
        progress_text_frame.rowconfigure(0, weight=1)
        
        self.progress_text = tk.Text(progress_text_frame, height=10, font=("Consolas", 9))
        progress_scrollbar = ttk.Scrollbar(progress_text_frame, orient="vertical", 
                                         command=self.progress_text.yview)
        self.progress_text.configure(yscrollcommand=progress_scrollbar.set)
        
        self.progress_text.grid(row=0, column=0, sticky="nsew")
        progress_scrollbar.grid(row=0, column=1, sticky="ns")
    
    def start_bulk_installation(self):
        """Start bulk installation process"""
        if self.bulk_running:
            return
            
        try:
            base_name = self.base_name.get().strip()
            title_template = self.title_template.get().strip()
            theme = self.theme.get()
            count = int(self.count.get())
            
            if not all([base_name, title_template, theme]) or count < 1:
                self.main_window.toast_manager.show_toast("Please fill in all fields correctly", "error")
                return
                
            self.bulk_running = True
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.progress.configure(value=0, maximum=count)
            
            def bulk_install():
                try:
                    installed_sites = []
                    
                    for i in range(1, count + 1):
                        if not self.bulk_running:
                            logger.warning("Bulk installation stopped by user")
                            break
                            
                        site_name = f"{base_name}_{i}"
                        site_title = title_template.format(number=i)
                        db_name = f"wp_{base_name.replace('-', '_')}_{i}"
                        
                        self.update_progress(f"Installing site {i}/{count}: {site_name}")
                        logger.info(f"Installing bulk site {i}/{count}: {site_name}")
                        
                        # Check for conflicts and generate unique names if needed
                        site_name = self.get_unique_site_name(site_name)
                        db_name = self.get_unique_db_name(db_name)
                        
                        success = self.main_window.wp_installer.create_complete_site(
                            site_name=site_name,
                            site_title=site_title,
                            db_name=db_name,
                            theme=theme
                        )
                        
                        if success:
                            installed_sites.append(site_name)
                            self.update_progress(f"✓ Installed: {site_name}")
                        else:
                            self.update_progress(f"✗ Failed: {site_name}")
                        
                        self.progress.configure(value=i)
                        self.main_window.root.update_idletasks()
                    
                    self.bulk_running = False
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    
                    if installed_sites:
                        self.main_window.toast_manager.show_toast(f"Bulk installation completed! {len(installed_sites)} sites created.", "success")
                        if hasattr(self.main_window, 'management_tab'):
                            self.main_window.management_tab.refresh_sites_list()
                    else:
                        self.main_window.toast_manager.show_toast("Bulk installation completed with no successful installations.", "warning")
                    
                    self.main_window.update_status("Ready")
                    
                except Exception as e:
                    logger.error(f"Bulk installation error: {e}")
                    self.main_window.toast_manager.show_toast(f"Bulk installation error: {e}", "error")
                    self.bulk_running = False
                    self.start_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
            
            threading.Thread(target=bulk_install, daemon=True).start()
            
        except Exception as e:
            self.main_window.toast_manager.show_toast(f"Failed to start bulk installation: {e}", "error")
    
    def stop_bulk_installation(self):
        """Stop bulk installation process"""
        self.bulk_running = False
        self.stop_btn.configure(state="disabled")
        self.update_progress("Stopping installation...")
    
    def update_progress(self, message):
        """Update bulk progress text"""
        self.progress_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.progress_text.see(tk.END)
    
    def get_unique_site_name(self, base_name):
        """Generate unique site name to avoid conflicts"""
        htdocs_path = Path(config_manager.get('xampp.htdocs_path'))
        original_name = base_name
        counter = 1
        
        while (htdocs_path / base_name).exists():
            base_name = f"{original_name}_{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                break
        
        return base_name
    
    def get_unique_db_name(self, base_name):
        """Generate unique database name to avoid conflicts"""
        if not self.main_window.db_manager.database_exists(base_name):
            return base_name
            
        original_name = base_name
        counter = 1
        
        while self.main_window.db_manager.database_exists(base_name):
            base_name = f"{original_name}_{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                break
        
        return base_name
