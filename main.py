#!/usr/bin/env python3
"""
WordPress Auto Installer - Main Entry Point

This is the single entry point for the WordPress Auto Installer application.
It can run in either GUI mode (default) or CLI mode based on arguments.

Usage:
    python main.py                    # Launch GUI
    python main.py --cli [command]    # Use CLI mode
    python main.py --help             # Show help
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    """Main entry point - decide between GUI and CLI modes"""
    # Parse initial arguments to determine mode
    parser = argparse.ArgumentParser(
        description="WordPress Auto Installer",
        add_help=False  # We'll handle help ourselves
    )
    parser.add_argument('--cli', action='store_true', help='Use command line interface')
    parser.add_argument('--gui', action='store_true', help='Use graphical interface (default)')
    parser.add_argument('--version', action='version', version='WordPress Auto Installer 1.0.0')
    
    # Parse known args to separate GUI/CLI choice from actual commands
    known_args, remaining_args = parser.parse_known_args()
    
    # Handle help for main script
    if '--help' in sys.argv and not known_args.cli:
        print(__doc__)
        parser.print_help()
        print("\nFor CLI help: python main.py --cli --help")
        print("For GUI: python main.py --gui (or just python main.py)")
        return 0
    
    try:
        if known_args.cli:
            # CLI Mode - import only when needed
            from wp_installer.utils.cli import WordPressCLI
            cli = WordPressCLI()
            return cli.run(remaining_args)
        else:
            # GUI Mode (default) - import only when needed 
            from wp_installer.gui.main_window import run_gui
            run_gui()
            return 0
            
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure all dependencies are installed:")
        print("- tkinter (for GUI)")
        print("- PyYAML (for configuration)")
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
