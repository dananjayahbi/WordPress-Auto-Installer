#!/usr/bin/env python3
"""
Console Panel Component
Handles real-time log display and console functionality
"""

import queue
import time
import threading
import logging
import tkinter as tk
from tkinter import filedialog

try:
    import ttkbootstrap as ttk
    MODERN_UI = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_UI = False

from ...utils.logger import logger

class ConsoleHandler(logging.Handler):
    """Custom logging handler to capture logs for GUI console"""
    def __init__(self, console_queue):
        super().__init__()
        self.console_queue = console_queue
        
    def emit(self, record):
        try:
            msg = self.format(record)
            self.console_queue.put(msg)
        except Exception:
            self.handleError(record)

class ConsolePanel:
    def __init__(self, main_window):
        self.main_window = main_window
        self.console_queue = queue.Queue()
        self.console_text = None
        
        # Setup logging to capture console output
        self.setup_console_logging()
        
        # Start console update thread
        self.start_console_update()
    
    def setup_console_logging(self):
        """Setup logging to capture output for GUI console"""
        console_handler = ConsoleHandler(self.console_queue)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to the existing logger
        logger.addHandler(console_handler)
    
    def create_console_panel(self, parent, row=0, column=1):
        """Create console panel for real-time logs"""
        if MODERN_UI:
            console_frame = ttk.Labelframe(parent, text="📄 Console Output", bootstyle="primary")
        else:
            console_frame = ttk.Labelframe(parent, text="📄 Console Output")
        console_frame.grid(row=row, column=column, sticky="nsew")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(1, weight=1)
        
        # Console controls
        self.create_console_controls(console_frame)
        
        # Console text area
        self.create_console_text_area(console_frame)
    
    def create_console_controls(self, parent):
        """Create console control buttons"""
        if MODERN_UI:
            controls_frame = ttk.Frame(parent, bootstyle="primary")
        else:
            controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        controls_frame.columnconfigure(1, weight=1)
        
        if MODERN_UI:
            clear_btn = ttk.Button(controls_frame, text="🗑️ Clear", 
                                 bootstyle="warning-outline", command=self.clear_console)
            save_btn = ttk.Button(controls_frame, text="💾 Save Log", 
                                bootstyle="info-outline", command=self.save_console_log)
        else:
            clear_btn = ttk.Button(controls_frame, text="🗑️ Clear", command=self.clear_console)
            save_btn = ttk.Button(controls_frame, text="💾 Save Log", command=self.save_console_log)
        
        clear_btn.grid(row=0, column=0, padx=5)
        save_btn.grid(row=0, column=2, padx=5)
    
    def create_console_text_area(self, parent):
        """Create console text display area"""
        console_text_frame = ttk.Frame(parent)
        console_text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        console_text_frame.columnconfigure(0, weight=1)
        console_text_frame.rowconfigure(0, weight=1)
        
        self.console_text = tk.Text(console_text_frame, wrap="word", font=("Consolas", 9),
                                   bg="#1e1e1e", fg="#ffffff", insertbackground="#ffffff")
        console_scrollbar = ttk.Scrollbar(console_text_frame, orient="vertical", 
                                        command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scrollbar.set)
        
        self.console_text.grid(row=0, column=0, sticky="nsew")
        console_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure text tags for colored output
        self.setup_console_colors()
    
    def setup_console_colors(self):
        """Setup color tags for console output"""
        self.console_text.tag_configure("success", foreground="#4ade80")
        self.console_text.tag_configure("error", foreground="#f87171")
        self.console_text.tag_configure("warning", foreground="#fbbf24")
        self.console_text.tag_configure("info", foreground="#60a5fa")
    
    def start_console_update(self):
        """Start the console update thread"""
        def update_console():
            while True:
                try:
                    message = self.console_queue.get(timeout=0.1)
                    if self.console_text:
                        self.console_text.insert(tk.END, message + "\n")
                        self.console_text.see(tk.END)
                        
                        # Color code based on log level
                        self.apply_console_colors(message)
                        
                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"Console update error: {e}")
                time.sleep(0.1)
        
        thread = threading.Thread(target=update_console, daemon=True)
        thread.start()
    
    def apply_console_colors(self, message):
        """Apply color coding to console message"""
        if "ERROR" in message:
            last_line = self.console_text.index(tk.END + "-2l")
            self.console_text.tag_add("error", last_line, tk.END + "-1c")
        elif "SUCCESS" in message or "✓" in message:
            last_line = self.console_text.index(tk.END + "-2l")
            self.console_text.tag_add("success", last_line, tk.END + "-1c")
        elif "WARNING" in message or "⚠" in message:
            last_line = self.console_text.index(tk.END + "-2l")
            self.console_text.tag_add("warning", last_line, tk.END + "-1c")
        elif "INFO" in message:
            last_line = self.console_text.index(tk.END + "-2l")
            self.console_text.tag_add("info", last_line, tk.END + "-1c")
    
    def clear_console(self):
        """Clear console output"""
        if self.console_text:
            self.console_text.delete(1.0, tk.END)
    
    def save_console_log(self):
        """Save console log to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path and self.console_text:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.main_window.toast_manager.show_toast("Console log saved successfully!", "success")
        except Exception as e:
            self.main_window.toast_manager.show_toast(f"Failed to save log: {e}", "error")
