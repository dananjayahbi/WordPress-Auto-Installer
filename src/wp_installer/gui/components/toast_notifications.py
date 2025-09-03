#!/usr/bin/env python3
"""
Toast Notifications Component
Handles success, error, warning, and info notifications
"""

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.toast import ToastNotification
    MODERN_UI = True
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    MODERN_UI = False

class ToastManager:
    def __init__(self):
        self.modern_ui = MODERN_UI
    
    def show_toast(self, message, style="info"):
        """Show toast notification"""
        if self.modern_ui:
            if style == "success":
                ToastNotification(title="Success", message=message, duration=3000, bootstyle="success").show_toast()
            elif style == "error":
                ToastNotification(title="Error", message=message, duration=5000, bootstyle="danger").show_toast()
            elif style == "warning":
                ToastNotification(title="Warning", message=message, duration=4000, bootstyle="warning").show_toast()
            else:
                ToastNotification(title="Info", message=message, duration=3000, bootstyle="info").show_toast()
        else:
            # Fallback to messagebox for non-modern UI
            if style == "error":
                messagebox.showerror("Error", message)
            elif style == "warning":
                messagebox.showwarning("Warning", message)
            else:
                messagebox.showinfo("Info", message)
