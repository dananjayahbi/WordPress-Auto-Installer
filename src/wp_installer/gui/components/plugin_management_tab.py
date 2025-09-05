#!/usr/bin/env python3
"""
Plugin Management Tab Component
Handles WordPress plugin installation, activation, deactivation, and deletion
"""

import os
import threading
import shutil
from pathlib import Path
from tkinter import filedialog, messagebox
import zipfile

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.logger import logger
from ...utils.config import config_manager
from ...utils.helpers import Helpers

class PluginManagementTab:
    def __init__(self, main_window, notebook):
        self.main_window = main_window
        self.notebook = notebook
        self.selected_site = None
        self.installed_plugins = []
        self.selected_plugins = []
        
        # Create the tab
        self.create_tab()
        
        # Load sites when tab is created
        self.refresh_sites()
    
    def create_tab(self):
        """Create plugin management tab"""
        if MODERN_UI:
            self.frame = ttk.Frame(self.notebook, bootstyle="light")
        else:
            self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text="🔌 Plugin Management")
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(3, weight=1)
        
        # Components
        self.create_header()
        self.create_site_selection()
        self.create_plugin_upload_section()
        self.create_installed_plugins_section()
    
    def create_header(self):
        """Create tab header"""
        if MODERN_UI:
            header_frame = ttk.Frame(self.frame, bootstyle="primary")
        else:
            header_frame = ttk.Frame(self.frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.columnconfigure(1, weight=1)
        
        # Title
        if MODERN_UI:
            title_label = ttk.Label(header_frame, text="🔌 Plugin Management", 
                                  font=("Segoe UI", 16, "bold"), bootstyle="inverse-primary")
        else:
            title_label = ttk.Label(header_frame, text="🔌 Plugin Management", 
                                  font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Description
        if MODERN_UI:
            desc_label = ttk.Label(header_frame, text="Install, activate, deactivate, and delete WordPress plugins", 
                                 font=("Segoe UI", 10), bootstyle="secondary")
        else:
            desc_label = ttk.Label(header_frame, text="Install, activate, deactivate, and delete WordPress plugins", 
                                 font=("Segoe UI", 10))
        desc_label.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Refresh button
        if MODERN_UI:
            refresh_btn = ttk.Button(header_frame, text="🔄 Refresh Sites", 
                                   bootstyle="info-outline", command=self.refresh_sites)
        else:
            refresh_btn = ttk.Button(header_frame, text="🔄 Refresh Sites", 
                                   command=self.refresh_sites)
        refresh_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))
    
    def create_site_selection(self):
        """Create site selection section"""
        if MODERN_UI:
            site_frame = ttk.LabelFrame(self.frame, text="Select WordPress Site", bootstyle="primary")
        else:
            site_frame = ttk.LabelFrame(self.frame, text="Select WordPress Site")
        site_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        site_frame.columnconfigure(1, weight=1)
        
        # Site selection
        if MODERN_UI:
            site_label = ttk.Label(site_frame, text="WordPress Site:", bootstyle="primary")
        else:
            site_label = ttk.Label(site_frame, text="WordPress Site:")
        site_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        if MODERN_UI:
            self.site_var = ttk.StringVar()
            self.site_combo = ttk.Combobox(site_frame, textvariable=self.site_var, 
                                         state="readonly", bootstyle="primary")
        else:
            self.site_var = ttk.StringVar()
            self.site_combo = ttk.Combobox(site_frame, textvariable=self.site_var, 
                                         state="readonly")
        self.site_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        self.site_combo.bind('<<ComboboxSelected>>', self.on_site_selected)
        
        # Site info
        if MODERN_UI:
            self.site_info_label = ttk.Label(site_frame, text="Select a site to manage plugins", 
                                           bootstyle="secondary")
        else:
            self.site_info_label = ttk.Label(site_frame, text="Select a site to manage plugins")
        self.site_info_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))
    
    def create_plugin_upload_section(self):
        """Create plugin upload and installation section"""
        if MODERN_UI:
            upload_frame = ttk.LabelFrame(self.frame, text="Install New Plugins", bootstyle="success")
        else:
            upload_frame = ttk.LabelFrame(self.frame, text="Install New Plugins")
        upload_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        upload_frame.columnconfigure(1, weight=1)
        
        # Plugin files selection
        if MODERN_UI:
            files_label = ttk.Label(upload_frame, text="Plugin Files:", bootstyle="success")
        else:
            files_label = ttk.Label(upload_frame, text="Plugin Files:")
        files_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        if MODERN_UI:
            self.selected_files_var = ttk.StringVar(value="No files selected")
            files_display = ttk.Label(upload_frame, textvariable=self.selected_files_var, 
                                    bootstyle="secondary", wraplength=400)
        else:
            self.selected_files_var = ttk.StringVar(value="No files selected")
            files_display = ttk.Label(upload_frame, textvariable=self.selected_files_var, 
                                    wraplength=400)
        files_display.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # Buttons frame
        if MODERN_UI:
            buttons_frame = ttk.Frame(upload_frame, bootstyle="success")
        else:
            buttons_frame = ttk.Frame(upload_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        if MODERN_UI:
            select_btn = ttk.Button(buttons_frame, text="📁 Select Plugin Files", 
                                  bootstyle="success-outline", command=self.select_plugin_files)
            install_btn = ttk.Button(buttons_frame, text="⚡ Install Selected Plugins", 
                                   bootstyle="success", command=self.install_selected_plugins)
        else:
            select_btn = ttk.Button(buttons_frame, text="📁 Select Plugin Files", 
                                  command=self.select_plugin_files)
            install_btn = ttk.Button(buttons_frame, text="⚡ Install Selected Plugins", 
                                   command=self.install_selected_plugins)
        
        select_btn.pack(side="left", padx=5)
        install_btn.pack(side="left", padx=5)
        
        self.plugin_files = []
    
    def create_installed_plugins_section(self):
        """Create installed plugins management section"""
        if MODERN_UI:
            plugins_frame = ttk.LabelFrame(self.frame, text="Installed Plugins", bootstyle="warning")
        else:
            plugins_frame = ttk.LabelFrame(self.frame, text="Installed Plugins")
        plugins_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        plugins_frame.columnconfigure(0, weight=1)
        plugins_frame.rowconfigure(1, weight=1)
        
        # Control buttons
        if MODERN_UI:
            control_frame = ttk.Frame(plugins_frame, bootstyle="warning")
        else:
            control_frame = ttk.Frame(plugins_frame)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        if MODERN_UI:
            activate_btn = ttk.Button(control_frame, text="✅ Activate Selected", 
                                    bootstyle="success-outline", command=self.activate_selected_plugins)
            deactivate_btn = ttk.Button(control_frame, text="⏸️ Deactivate Selected", 
                                      bootstyle="warning-outline", command=self.deactivate_selected_plugins)
            delete_btn = ttk.Button(control_frame, text="🗑️ Delete Selected", 
                                  bootstyle="danger", command=self.delete_selected_plugins)
            refresh_plugins_btn = ttk.Button(control_frame, text="🔄 Refresh List", 
                                           bootstyle="info-outline", command=self.refresh_installed_plugins)
        else:
            activate_btn = ttk.Button(control_frame, text="✅ Activate Selected", 
                                    command=self.activate_selected_plugins)
            deactivate_btn = ttk.Button(control_frame, text="⏸️ Deactivate Selected", 
                                      command=self.deactivate_selected_plugins)
            delete_btn = ttk.Button(control_frame, text="🗑️ Delete Selected", 
                                  command=self.delete_selected_plugins)
            refresh_plugins_btn = ttk.Button(control_frame, text="🔄 Refresh List", 
                                           command=self.refresh_installed_plugins)
        
        activate_btn.pack(side="left", padx=5)
        deactivate_btn.pack(side="left", padx=5)
        delete_btn.pack(side="left", padx=5)
        refresh_plugins_btn.pack(side="left", padx=5)
        
        # Plugins list with scrollbar
        list_frame = ttk.Frame(plugins_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for plugins list
        columns = ("Status", "Name", "Version", "Description")
        if MODERN_UI:
            self.plugins_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", 
                                           bootstyle="warning")
        else:
            self.plugins_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings")
        
        # Configure column headings and widths
        self.plugins_tree.heading("#0", text="✓")
        self.plugins_tree.heading("Status", text="Status")
        self.plugins_tree.heading("Name", text="Plugin Name")
        self.plugins_tree.heading("Version", text="Version")
        self.plugins_tree.heading("Description", text="Description")
        
        self.plugins_tree.column("#0", width=30, minwidth=30)
        self.plugins_tree.column("Status", width=80, minwidth=80)
        self.plugins_tree.column("Name", width=200, minwidth=150)
        self.plugins_tree.column("Version", width=100, minwidth=80)
        self.plugins_tree.column("Description", width=300, minwidth=200)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.plugins_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=self.plugins_tree.xview)
        self.plugins_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.plugins_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind selection event
        self.plugins_tree.bind("<Button-1>", self.on_plugin_click)
    
    def safe_update_status(self, message):
        """Safely update status bar, fallback to logging if not available"""
        try:
            self.safe_update_status(message)
        except:
            logger.info(f"Status: {message}")
    
    def refresh_sites(self):
        """Refresh the list of WordPress sites"""
        try:
            htdocs_path = config_manager.get('xampp.htdocs_path')
            if not htdocs_path or not os.path.exists(htdocs_path):
                self.site_combo['values'] = []
                return
            
            sites = []
            for item in os.listdir(htdocs_path):
                item_path = os.path.join(htdocs_path, item)
                if os.path.isdir(item_path):
                    # Check if it's a WordPress site by looking for wp-config.php
                    wp_config = os.path.join(item_path, 'wp-config.php')
                    if os.path.exists(wp_config):
                        sites.append(item)
            
            self.site_combo['values'] = sites
            if sites and not self.site_var.get():
                self.site_var.set(sites[0])
                self.on_site_selected()
                
        except Exception as e:
            logger.error(f"Error refreshing sites: {e}")
    
    def on_site_selected(self, event=None):
        """Handle site selection"""
        selected_site = self.site_var.get()
        if not selected_site:
            return
        
        self.selected_site = selected_site
        htdocs_path = config_manager.get('xampp.htdocs_path')
        site_path = os.path.join(htdocs_path, selected_site)
        
        # Update site info
        self.site_info_label.config(text=f"Selected: {selected_site} | Path: {site_path}")
        
        # Refresh installed plugins for this site
        self.refresh_installed_plugins()
    
    def select_plugin_files(self):
        """Select plugin files for installation"""
        try:
            files = filedialog.askopenfilenames(
                title="Select Plugin Files",
                filetypes=[
                    ("Plugin files", "*.zip"),
                    ("All files", "*.*")
                ]
            )
            
            if files:
                # Validate each selected file
                valid_files = []
                invalid_files = []
                
                for file_path in files:
                    if Helpers.validate_plugin_file(file_path):
                        valid_files.append(file_path)
                        logger.success(f"Valid plugin file: {os.path.basename(file_path)}")
                    else:
                        invalid_files.append(file_path)
                        logger.warning(f"Invalid plugin file: {os.path.basename(file_path)}")
                
                # Update the file list with only valid files
                self.plugin_files = valid_files
                
                if valid_files:
                    file_names = [os.path.basename(f) for f in valid_files]
                    status_msg = f"Selected {len(valid_files)} valid files: {', '.join(file_names)}"
                    if invalid_files:
                        status_msg += f" ({len(invalid_files)} invalid files excluded)"
                    self.selected_files_var.set(status_msg)
                else:
                    self.selected_files_var.set("No valid plugin files selected")
                    if invalid_files:
                        messagebox.showwarning("Invalid Files", 
                                             f"{len(invalid_files)} invalid plugin files were excluded.")
            else:
                self.plugin_files = []
                self.selected_files_var.set("No files selected")
                
        except Exception as e:
            logger.error(f"Error selecting plugin files: {e}")
            messagebox.showerror("Error", f"Failed to select plugin files: {e}")
    
    def install_selected_plugins(self):
        """Install the selected plugin files"""
        if not self.selected_site:
            messagebox.showwarning("No Site Selected", "Please select a WordPress site first.")
            return
        
        if not self.plugin_files:
            messagebox.showwarning("No Files Selected", "Please select plugin files to install.")
            return
        
        def install_task():
            try:
                htdocs_path = config_manager.get('xampp.htdocs_path')
                site_path = os.path.join(htdocs_path, self.selected_site)
                
                self.safe_update_status(f"Installing plugins for {self.selected_site}...")
                
                success_count = 0
                for plugin_file in self.plugin_files:
                    logger.info(f"Installing plugin: {os.path.basename(plugin_file)}")
                    
                    if self.main_window.wp_installer.install_plugin_from_file(site_path, plugin_file):
                        success_count += 1
                        logger.success(f"Plugin installed: {os.path.basename(plugin_file)}")
                    else:
                        logger.error(f"Failed to install plugin: {os.path.basename(plugin_file)}")
                
                # Show results
                if success_count == len(self.plugin_files):
                    self.main_window.toast_manager.show_toast(
                        f"All {success_count} plugins installed successfully!", "success")
                elif success_count > 0:
                    self.main_window.toast_manager.show_toast(
                        f"{success_count}/{len(self.plugin_files)} plugins installed successfully", "warning")
                else:
                    self.main_window.toast_manager.show_toast("No plugins were installed", "error")
                
                # Clear selection and refresh
                self.plugin_files = []
                self.selected_files_var.set("No files selected")
                self.refresh_installed_plugins()
                
                # Update status safely
                self.safe_update_status("Ready")
                
            except Exception as e:
                logger.error(f"Error installing plugins: {e}")
                self.main_window.toast_manager.show_toast(f"Error installing plugins: {e}", "error")
                self.safe_update_status("Ready")
        
        threading.Thread(target=install_task, daemon=True).start()
    
    def refresh_installed_plugins(self):
        """Refresh the list of installed plugins"""
        if not self.selected_site:
            return
        
        def refresh_task():
            try:
                htdocs_path = config_manager.get('xampp.htdocs_path')
                site_path = os.path.join(htdocs_path, self.selected_site)
                
                # Update status safely
                try:
                    self.safe_update_status("Loading installed plugins...")
                except:
                    logger.info("Loading installed plugins...")
                
                # Get installed plugins using WP-CLI
                plugins = self.main_window.wp_installer.get_installed_plugins(site_path)
                
                # Update UI in main thread safely
                try:
                    self.main_window.root.after(0, self.update_plugins_list, plugins)
                except:
                    # Fallback if main loop is not available
                    self.update_plugins_list(plugins)
                
            except Exception as e:
                logger.error(f"Error refreshing installed plugins: {e}")
                try:
                    self.main_window.root.after(0, self.update_plugins_list, [])
                except:
                    self.update_plugins_list([])
        
        threading.Thread(target=refresh_task, daemon=True).start()
    
    def update_plugins_list(self, plugins):
        """Update the plugins list in the UI"""
        try:
            # Clear current items
            for item in self.plugins_tree.get_children():
                self.plugins_tree.delete(item)
            
            # Add plugins to the tree
            for plugin in plugins:
                status = "Active" if plugin.get('status') == 'active' else "Inactive"
                status_icon = "✅" if plugin.get('status') == 'active' else "⏸️"
                
                self.plugins_tree.insert("", "end", 
                                       text="",
                                       values=(status_icon + " " + status, 
                                             plugin.get('name', 'Unknown'),
                                             plugin.get('version', ''),
                                             plugin.get('description', '')[:100] + "..." if len(plugin.get('description', '')) > 100 else plugin.get('description', '')),
                                       tags=(plugin.get('name', ''),))
            
            self.installed_plugins = plugins
            
            # Update status safely
            try:
                self.safe_update_status("Ready")
            except:
                logger.info("Plugin list updated")
            
        except Exception as e:
            logger.error(f"Error updating plugins list: {e}")
    
    def on_plugin_click(self, event):
        """Handle plugin item click for selection"""
        item = self.plugins_tree.selection()[0] if self.plugins_tree.selection() else None
        if item:
            # Toggle selection visual feedback
            current_text = self.plugins_tree.item(item, "text")
            if current_text == "":
                self.plugins_tree.item(item, text="✓")
            else:
                self.plugins_tree.item(item, text="")
    
    def get_selected_plugin_names(self):
        """Get the names of selected plugins"""
        selected_names = []
        for item in self.plugins_tree.get_children():
            if self.plugins_tree.item(item, "text") == "✓":
                plugin_values = self.plugins_tree.item(item, "values")
                if len(plugin_values) > 1:
                    selected_names.append(plugin_values[1])  # Plugin name is at index 1
        return selected_names
    
    def activate_selected_plugins(self):
        """Activate selected plugins"""
        selected_plugins = self.get_selected_plugin_names()
        if not selected_plugins:
            messagebox.showwarning("No Selection", "Please select plugins to activate.")
            return
        
        if not self.selected_site:
            messagebox.showwarning("No Site Selected", "Please select a WordPress site first.")
            return
        
        def activate_task():
            try:
                htdocs_path = config_manager.get('xampp.htdocs_path')
                site_path = os.path.join(htdocs_path, self.selected_site)
                
                self.safe_update_status(f"Activating {len(selected_plugins)} plugins...")
                
                success_count = 0
                for plugin_name in selected_plugins:
                    if self.main_window.wp_installer.activate_plugin(site_path, plugin_name):
                        success_count += 1
                        logger.success(f"Plugin activated: {plugin_name}")
                    else:
                        logger.error(f"Failed to activate plugin: {plugin_name}")
                
                # Show results
                if success_count == len(selected_plugins):
                    self.main_window.toast_manager.show_toast(
                        f"All {success_count} plugins activated!", "success")
                else:
                    self.main_window.toast_manager.show_toast(
                        f"{success_count}/{len(selected_plugins)} plugins activated", "warning")
                
                self.refresh_installed_plugins()
                
            except Exception as e:
                logger.error(f"Error activating plugins: {e}")
                self.main_window.toast_manager.show_toast(f"Error activating plugins: {e}", "error")
                self.safe_update_status("Ready")
        
        threading.Thread(target=activate_task, daemon=True).start()
    
    def deactivate_selected_plugins(self):
        """Deactivate selected plugins"""
        selected_plugins = self.get_selected_plugin_names()
        if not selected_plugins:
            messagebox.showwarning("No Selection", "Please select plugins to deactivate.")
            return
        
        if not self.selected_site:
            messagebox.showwarning("No Site Selected", "Please select a WordPress site first.")
            return
        
        def deactivate_task():
            try:
                htdocs_path = config_manager.get('xampp.htdocs_path')
                site_path = os.path.join(htdocs_path, self.selected_site)
                
                self.safe_update_status(f"Deactivating {len(selected_plugins)} plugins...")
                
                success_count = 0
                for plugin_name in selected_plugins:
                    if self.main_window.wp_installer.deactivate_plugin(site_path, plugin_name):
                        success_count += 1
                        logger.success(f"Plugin deactivated: {plugin_name}")
                    else:
                        logger.error(f"Failed to deactivate plugin: {plugin_name}")
                
                # Show results
                if success_count == len(selected_plugins):
                    self.main_window.toast_manager.show_toast(
                        f"All {success_count} plugins deactivated!", "success")
                else:
                    self.main_window.toast_manager.show_toast(
                        f"{success_count}/{len(selected_plugins)} plugins deactivated", "warning")
                
                self.refresh_installed_plugins()
                
            except Exception as e:
                logger.error(f"Error deactivating plugins: {e}")
                self.main_window.toast_manager.show_toast(f"Error deactivating plugins: {e}", "error")
                self.safe_update_status("Ready")
        
        threading.Thread(target=deactivate_task, daemon=True).start()
    
    def delete_selected_plugins(self):
        """Delete selected plugins"""
        selected_plugins = self.get_selected_plugin_names()
        if not selected_plugins:
            messagebox.showwarning("No Selection", "Please select plugins to delete.")
            return
        
        if not self.selected_site:
            messagebox.showwarning("No Site Selected", "Please select a WordPress site first.")
            return
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion", 
            f"Are you sure you want to delete {len(selected_plugins)} plugin(s)?\n\n"
            f"Plugins: {', '.join(selected_plugins)}\n\n"
            "This action cannot be undone."
        )
        
        if not result:
            return
        
        def delete_task():
            try:
                htdocs_path = config_manager.get('xampp.htdocs_path')
                site_path = os.path.join(htdocs_path, self.selected_site)
                
                self.safe_update_status(f"Deleting {len(selected_plugins)} plugins...")
                
                success_count = 0
                for plugin_name in selected_plugins:
                    if self.main_window.wp_installer.delete_plugin(site_path, plugin_name):
                        success_count += 1
                        logger.success(f"Plugin deleted: {plugin_name}")
                    else:
                        logger.error(f"Failed to delete plugin: {plugin_name}")
                
                # Show results
                if success_count == len(selected_plugins):
                    self.main_window.toast_manager.show_toast(
                        f"All {success_count} plugins deleted!", "success")
                else:
                    self.main_window.toast_manager.show_toast(
                        f"{success_count}/{len(selected_plugins)} plugins deleted", "warning")
                
                self.refresh_installed_plugins()
                
            except Exception as e:
                logger.error(f"Error deleting plugins: {e}")
                self.main_window.toast_manager.show_toast(f"Error deleting plugins: {e}", "error")
                self.safe_update_status("Ready")
        
        threading.Thread(target=delete_task, daemon=True).start()
