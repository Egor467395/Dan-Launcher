# 🎮 Dan Launcher - Minecraft Launcher

A feature-rich Minecraft launcher built with Python and Tkinter, supporting mod loaders and mod management.

## Features

### ✨ Core Features
- **Version Management**: Browse, install, and manage Minecraft versions
- **Mod Loader Support**: Install and use Forge, Fabric, and Quilt mod loaders
- **Mod Management**: Easily add and remove mods from the mods folder
- **Resource Pack Support**: Manage your resource packs
- **Customizable Settings**: Configure Java path, allocated RAM, and more
- **Progress Tracking**: Real-time progress updates during installation and launch
- **Modern UI**: Clean, tabbed interface for easy navigation

### 🛠️ Technical Features
- Automatic Java detection
- Offline mode support (uses test account for launching)
- Settings persistence (saved to JSON)
- Thread-safe operations (non-blocking UI)
- Log output for debugging

## Installation

### Prerequisites
- Python 3.8 or higher
- Java (for running Minecraft)
- Internet connection (for downloading versions and mod loaders)

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Launcher

```bash
python launcher.py
```

### Basic Workflow

1. **Install a Minecraft Version**
   - Go to the "Versions" tab
   - Select a version from the list
   - Click "Install Selected"
   - Wait for installation to complete

2. **Install a Mod Loader (Optional)**
   - Go to the "Versions" tab
   - Select a Minecraft version in the "Mod Loader Installation" section
   - Choose a mod loader (Forge, Fabric, or Quilt)
   - Click "Install Mod Loader"

3. **Add Mods (Optional)**
   - Go to the "Mods" tab
   - Click "Add Mod" and select your mod file (.jar)
   - Mods will be placed in the mods folder automatically

4. **Configure Settings**
   - Go to the "Settings" tab
   - Set your Java path (if needed)
   - Adjust allocated RAM
   - Click "Save Settings"

5. **Launch Minecraft**
   - Go to the "Play" tab
   - Select your desired version
   - Enter your username
   - Click "Launch Minecraft"

## Tab Descriptions

### Play Tab
- Select Minecraft version to launch
- Choose mod loader (if installed)
- Enter username
- Launch button and progress tracking
- Log output

### Versions Tab
- Browse all available Minecraft versions
- Install new versions
- Delete installed versions
- Install mod loaders (Forge, Fabric, Quilt)

### Mods Tab
- View installed mods
- Add new mod files
- Remove mods
- Open mods folder directly

### Resource Packs Tab
- Manage resource packs
- Add/remove resource packs
- Open resource packs folder

### Settings Tab
- Configure Java executable path
- Adjust allocated RAM (1024 MB - 16384 MB)
- Save all settings

## Directory Structure

The launcher uses the standard Minecraft directory structure:
```
.minecraft/
├── versions/          # Installed Minecraft versions
├── mods/              # Mod files (.jar)
├── resourcepacks/     # Resource pack files
└── ...
```

## Notes

- **Offline Mode**: The launcher uses offline mode by default. For full multiplayer support, you'll need to implement Microsoft account authentication.
- **Java Detection**: The launcher attempts to auto-detect Java, but you can manually specify the path in settings.
- **Mod Compatibility**: Make sure your mods are compatible with the selected mod loader and Minecraft version.
- **Settings**: Settings are saved to `launcher_settings.json` in the launcher directory.

## Troubleshooting

### Java Not Found
- Make sure Java is installed on your system
- Manually set the Java path in Settings tab

### Version Won't Install
- Check your internet connection
- Ensure you have enough disk space
- Check the log output for error messages

### Mods Not Loading
- Verify the mod is compatible with your mod loader
- Check that the mod loader is properly installed
- Ensure mod file is in the `.minecraft/mods/` folder

### Launch Issues
- Verify the selected version is installed
- Check Java path is correct
- Review log output for errors
- Ensure allocated RAM is sufficient

## License

This project is open source and available for modification and distribution.

## Credits

Built using:
- [minecraft-launcher-lib](https://github.com/jakobkmar/minecraft-launcher-lib) - Minecraft launcher library
- Tkinter - GUI framework
- Python Standard Library

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Enjoy your Minecraft experience with Dan Launcher!** 🎉

