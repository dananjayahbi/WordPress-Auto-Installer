# WordPress Auto Installer v1.0

A comprehensive WordPress development tool that automates the creation and management of multiple WordPress installations. Perfect for plugin developers who need fresh WordPress environments for testing.

## 🚀 Features

- **Automated WordPress Installation**: Create new WordPress instances in seconds
- **Bulk Operations**: Create multiple instances at once
- **GUI Interface**: User-friendly graphical interface with real-time logging
- **CLI Support**: Command-line interface for automation and scripting
- **Instance Management**: Reset, delete, and manage WordPress installations
- **Configuration Management**: Easy setup and configuration through GUI
- **Error Handling**: Robust error handling with detailed logging
- **Multi-Platform**: Works on Windows, Linux, and macOS with XAMPP

## 📁 Project Structure

```
wp-bulk/
├── main.py                    # Main entry point (GUI/CLI)
├── gui.py                     # GUI application with tkinter
├── core.py                    # Core WordPress installation logic
├── config.py                  # Configuration management
├── database.py                # MySQL database operations
├── utils.py                   # Utility functions and helpers
├── logger.py                  # Logging system
├── wp_installer_config.yaml   # Configuration file
├── wordpress-6.8.2.zip       # WordPress installation zip
├── wp_installer.py            # Legacy monolithic version (deprecated)
└── README.md                  # This file
```

## 🔧 Prerequisites

### 1. XAMPP
- Download and install [XAMPP](https://www.apachefriends.org/)
- Start Apache and MySQL services
- Note your htdocs path (usually `C:/xampp/htdocs`)

### 2. WP-CLI (WordPress Command Line Interface)
Download from [wp-cli.org](https://wp-cli.org/#installing):
- **Windows**: Download `wp-cli.phar` and place in `C:/wp-cli/`
- **Linux/macOS**: Follow installation instructions on the website

### 3. WordPress Zip File
- Download WordPress from [wordpress.org](https://wordpress.org/download/)
- Place the `wordpress-x.x.x.zip` file in the application directory

### 4. Python Dependencies
All modules use only Python standard library - no additional packages required!

## 🚀 Quick Start

### GUI Mode (Recommended)
```bash
# Start the GUI application
python main.py

# Or explicitly
python main.py gui
```

### CLI Mode
```bash
# Create a single instance
python main.py create

# Create with specific name
python main.py create --name my_plugin_test

# Create multiple instances
python main.py create-multiple --count 5

# List all instances
python main.py list

# Reset an instance (clean slate)
python main.py reset --name wp_test_01

# Delete an instance
python main.py delete --name wp_test_01
```

## 📊 GUI Features

### Main Interface
- **Instance Management**: View, create, and manage WordPress installations
- **Real-time Operations**: All operations run in background threads
- **Context Menu**: Right-click instances for quick actions
- **Status Updates**: Real-time status bar with operation progress

### Configuration Tab
- **XAMPP Settings**: Configure MySQL connection and htdocs path
- **WordPress Defaults**: Set default admin credentials and site settings
- **Instance Settings**: Configure naming and limits
- **Import/Export**: Save and load configuration files
- **Connection Testing**: Test MySQL and WP-CLI connectivity

### Console Logs Tab
- **Real-time Logging**: See all operations as they happen
- **Log Levels**: Color-coded messages (Success, Warning, Error, etc.)
- **Auto-scroll**: Automatically scroll to latest messages
- **Save Logs**: Export logs to file for troubleshooting

### Help System
- **Comprehensive Guide**: Built-in help with setup instructions
- **WP-CLI Setup**: Detailed WP-CLI installation guide
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Development workflow recommendations

## ⚙️ Configuration

The application uses `wp_installer_config.yaml` for configuration:

```yaml
xampp:
  htdocs_path: "E:/xampp/htdocs"
  mysql_user: "root"
  mysql_password: ""
  mysql_host: "localhost"

wordpress:
  admin_user: "admin"
  admin_password: "your_password"
  admin_email: "your_email@example.com"
  site_title_prefix: "WP Test Site"
  base_url: "http://localhost"

instances:
  prefix: "wp_test_"
  max_instances: 50
```

## 🏗️ Architecture

### Modular Design
- **Separation of Concerns**: Each module has a specific responsibility
- **Loose Coupling**: Modules communicate through well-defined interfaces
- **Reusability**: Core logic can be used in both GUI and CLI modes
- **Maintainability**: Easy to modify and extend individual components

### Thread Safety
- **Background Operations**: Long-running tasks don't block the GUI
- **Thread-safe Logging**: Safe logging from multiple threads
- **Queue-based Communication**: Reliable communication between threads

### Error Handling
- **Graceful Degradation**: Application continues working even if some operations fail
- **Detailed Logging**: Comprehensive error messages and stack traces
- **User Feedback**: Clear error messages in both GUI and CLI modes

## 🛠️ Development

### Adding New Features
1. **Core Logic**: Add business logic to `core.py`
2. **GUI Integration**: Add UI elements to `gui.py`
3. **CLI Support**: Add command-line arguments to `main.py`
4. **Configuration**: Add settings to `config.py` if needed

### Database Operations
All database operations are handled through `database.py`:
- Connection management
- Database creation/deletion
- Backup and restore (ready for future implementation)

### Utility Functions
Common operations are centralized in `utils.py`:
- File operations
- WordPress zip extraction
- Validation functions
- System information

## 📦 Building Executable

The project is structured for easy packaging with PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (add this command later)
pyinstaller --onefile --windowed main.py
```

## 🔍 Troubleshooting

### Common Issues

**WP-CLI Not Found**
- Verify installation: `wp --info`
- Check if `wp-cli.phar` is in `C:/wp-cli/`
- Ensure PHP is in system PATH

**MySQL Connection Failed**
- Start XAMPP MySQL service
- Check credentials in configuration
- Test manually: `mysql -u root -h localhost`

**WordPress Zip Not Found**
- Download from wordpress.org
- Place in application directory
- Ensure filename starts with "wordpress"

**Permission Issues**
- Run XAMPP as administrator (Windows)
- Check htdocs directory permissions
- Ensure write access to htdocs

### Debug Mode
Enable detailed logging by:
1. Opening the Console Logs tab
2. Monitoring real-time operations
3. Saving logs for analysis

## 📝 License

This project is created for educational and development purposes. WordPress is licensed under GPL v2 or later.

## 🤝 Contributing

This is a personal development tool, but contributions are welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the built-in Help system (Help button in GUI)
2. Review the Console Logs for error details
3. Verify prerequisites are correctly installed
4. Check configuration settings

---

**WordPress Auto Installer v1.0** - Making WordPress development easier, one instance at a time! 🚀
