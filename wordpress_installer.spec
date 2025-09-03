# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for WordPress Auto Installer
This builds a standalone executable with all dependencies
"""

import os
import sys
from pathlib import Path

# Get the base directory
base_dir = Path(SPECPATH)

# Add src directory to the path
src_dir = base_dir / 'src'
sys.path.insert(0, str(src_dir))

# Analysis phase - collect all Python files and dependencies
a = Analysis(
    ['main.py'],
    pathex=[str(base_dir), str(src_dir)],
    binaries=[],
    datas=[
        # NOTE: assets, logs, and config folders are kept external to the executable
        # for user accessibility and modification
    ],
    hiddenimports=[
        # GUI dependencies
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'ttkbootstrap',
        'ttkbootstrap.themes',
        'ttkbootstrap.validation',
        'ttkbootstrap.constants',
        'ttkbootstrap.toast',
        'ttkbootstrap.style',
        'ttkbootstrap.window',
        'ttkbootstrap.dialogs',
        'ttkbootstrap.localization',
        'ttkbootstrap.scrolled',
        'ttkbootstrap.utility',
        'ttkbootstrap.tableview',
        # Core dependencies
        'yaml',
        'pathlib',
        'subprocess',
        'threading',
        'webbrowser',
        'shutil',
        're',
        'zipfile',
        'mysql.connector',
        'logging',
        'queue',
        'datetime',
        'os',
        # Application modules - use full paths
        'wp_installer',
        'wp_installer.core',
        'wp_installer.core.database',
        'wp_installer.core.wordpress',
        'wp_installer.utils',
        'wp_installer.utils.config',
        'wp_installer.utils.logger',
        'wp_installer.utils.helpers',
        'wp_installer.utils.cli',
        'wp_installer.gui',
        'wp_installer.gui.main_window',
        'wp_installer.gui.components',
        'wp_installer.gui.components.console_panel',
        'wp_installer.gui.components.single_install_tab',
        'wp_installer.gui.components.bulk_install_tab',
        'wp_installer.gui.components.management_tab',
        'wp_installer.gui.components.settings_tab',
        'wp_installer.gui.components.toast_notifications',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'test',
        'tests',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Add the entire src directory as a data directory
a.datas += Tree(str(src_dir), prefix='src')

# Add ttkbootstrap data files
try:
    import ttkbootstrap
    ttkbootstrap_path = Path(ttkbootstrap.__file__).parent
    # Include entire ttkbootstrap package data
    a.datas += Tree(str(ttkbootstrap_path), prefix='ttkbootstrap', excludes=['*.py', '*.pyc', '__pycache__'])
    
    # Also add all hidden imports for ttkbootstrap
    a.hiddenimports.extend([
        'ttkbootstrap.themes.dark',
        'ttkbootstrap.themes.light',
        'ttkbootstrap.localization',
        'ttkbootstrap.scrolled',
        'ttkbootstrap.utility',
        'ttkbootstrap.window',
        'ttkbootstrap.style',
        'ttkbootstrap.dialogs',
        'ttkbootstrap.tableview',
    ])
except ImportError:
    pass

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WordPress_Auto_Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an icon file here later: icon='icon.ico'
    version_file=None,
)

# Copy additional files to dist folder
import shutil

# Ensure external folders exist
external_folders = ['assets', 'config', 'logs']
for folder in external_folders:
    dist_folder = Path(DISTPATH) / folder
    dist_folder.mkdir(exist_ok=True)

# Copy required files to assets folder
assets_dest = Path(DISTPATH) / 'assets'
# Copy WordPress zip if it exists
wp_zip_source = base_dir / 'assets' / 'wordpress-6.8.2.zip'
if wp_zip_source.exists():
    shutil.copy2(wp_zip_source, assets_dest / 'wordpress-6.8.2.zip')

# Copy wp-cli.phar if it exists
wp_cli_source = base_dir / 'assets' / 'wp-cli.phar'
if wp_cli_source.exists():
    shutil.copy2(wp_cli_source, assets_dest / 'wp-cli.phar')

# Copy config file
config_source = base_dir / 'config' / 'wp_installer_config.yaml'
config_dest = Path(DISTPATH) / 'config'
if config_source.exists():
    shutil.copy2(config_source, config_dest / 'wp_installer_config.yaml')

# Copy README files
readme_files = [
    ('README.md', 'README.md'),
    ('README_PORTABLE.md', 'README_PORTABLE.md'),
    ('Launch_WordPress_Installer.bat', 'Launch_WordPress_Installer.bat')
]

for src_name, dest_name in readme_files:
    src_file = base_dir / src_name
    if src_file.exists():
        shutil.copy2(src_file, Path(DISTPATH) / dest_name)

print("✅ External folders and files copied to dist/")
