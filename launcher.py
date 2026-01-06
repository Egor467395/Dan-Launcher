import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import minecraft_launcher_lib
import subprocess
import os
import json
import threading
import shutil
from pathlib import Path
from datetime import datetime

# Try to import Minecraft font renderer
try:
    from minecraft_font import load_font_renderer, create_title_with_font
    FONT_RENDERER_AVAILABLE = True
except ImportError:
    FONT_RENDERER_AVAILABLE = False
    print("Minecraft font renderer not available (Pillow may not be installed)")

class MinecraftLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Dan Launcher v0.5 - First Open Beta - Minecraft")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        # Set window background
        self.root.configure(bg='#f8fafc')
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Minecraft directory
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.versions_dir = os.path.join(self.minecraft_directory, "versions")
        self.mods_dir = os.path.join(self.minecraft_directory, "mods")
        self.resourcepacks_dir = os.path.join(self.minecraft_directory, "resourcepacks")
        
        # Ensure directories exist
        os.makedirs(self.mods_dir, exist_ok=True)
        os.makedirs(self.resourcepacks_dir, exist_ok=True)
        
        # Settings
        self.settings = self.load_settings()
        self.selected_version = self.settings.get("selected_version", "")
        self.selected_mod_loader = self.settings.get("selected_mod_loader", "vanilla")
        self.java_path = self.settings.get("java_path", self.find_java())
        self.allocated_ram = self.settings.get("allocated_ram", 4096)
        self.username = self.settings.get("username", "Player")
        self.window_width = self.settings.get("window_width", 854)
        self.window_height = self.settings.get("window_height", 480)
        self.fullscreen = self.settings.get("fullscreen", False)
        self.custom_jvm_args = self.settings.get("custom_jvm_args", "")
        self.server_ip = self.settings.get("server_ip", "")
        self.server_port = self.settings.get("server_port", "25565")
        self.favorite_versions = set(self.settings.get("favorite_versions", []))
        self.recent_versions = self.settings.get("recent_versions", [])
        self.theme = self.settings.get("theme", "light")
        
        # Enhanced settings
        self.disabled_mods = set(self.settings.get("disabled_mods", []))
        self.enabled_resourcepacks = set(self.settings.get("enabled_resourcepacks", []))
        self.current_profile = self.settings.get("current_profile", "default")
        
        # Statistics
        if "statistics" not in self.settings:
            self.settings["statistics"] = {
                "total_launches": 0,
                "total_playtime": 0,
                "most_used_version": "",
                "last_launch": ""
            }
        
        # Load Minecraft font renderer if available
        self.font_renderer = None
        if FONT_RENDERER_AVAILABLE:
            try:
                self.font_renderer = load_font_renderer("assets")
                if self.font_renderer:
                    print("Minecraft font loaded successfully!")
            except Exception as e:
                print(f"Could not load Minecraft font: {e}")
        
        # Installation queue
        self.installation_queue = []
        self.current_installation = None
        
        # Create UI
        self.create_ui()
        self.load_versions()
        self.load_favorite_versions()
        
    def configure_styles(self):
        """Configure custom styles for a modern, beautiful look"""
        # Color scheme - Modern gradient-inspired colors
        self.colors = {
            'primary': '#6366f1',  # Indigo
            'primary_dark': '#4f46e5',
            'secondary': '#8b5cf6',  # Purple
            'success': '#10b981',  # Green
            'danger': '#ef4444',  # Red
            'warning': '#f59e0b',  # Orange
            'bg_light': '#f8fafc',
            'bg_dark': '#1e293b',
            'text_primary': '#0f172a',
            'text_secondary': '#64748b',
            'border': '#e2e8f0',
            'hover': '#f1f5f9'
        }
        
        # Title style
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 22, 'bold'), 
                           foreground=self.colors['primary'],
                           background=self.colors['bg_light'])
        
        # Heading style
        self.style.configure('Heading.TLabel', 
                           font=('Segoe UI', 13, 'bold'),
                           foreground=self.colors['text_primary'],
                           background=self.colors['bg_light'])
        
        # Button styles
        self.style.configure('Action.TButton', 
                           font=('Segoe UI', 10, 'bold'),
                           padding=[12, 6],
                           background=self.colors['primary'],
                           foreground='white')
        self.style.map('Action.TButton',
                      background=[('active', self.colors['primary_dark']),
                                ('pressed', self.colors['primary_dark'])])
        
        self.style.configure('Big.TButton', 
                           font=('Segoe UI', 15, 'bold'), 
                           padding=[20, 12],
                           background=self.colors['success'],
                           foreground='white')
        self.style.map('Big.TButton',
                      background=[('active', '#059669'),
                                ('pressed', '#047857')])
        
        # Success button
        self.style.configure('Success.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           padding=[12, 6],
                           background=self.colors['success'],
                           foreground='white')
        
        # Danger button
        self.style.configure('Danger.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           padding=[12, 6],
                           background=self.colors['danger'],
                           foreground='white')
        
        # Configure notebook style - Modern tabs
        self.style.configure('TNotebook', 
                           tabposition='n',
                           background=self.colors['bg_light'],
                           borderwidth=0)
        self.style.configure('TNotebook.Tab', 
                           padding=[25, 12], 
                           font=('Segoe UI', 11, 'bold'),
                           background=self.colors['border'],
                           foreground=self.colors['text_secondary'],
                           borderwidth=0)
        self.style.map('TNotebook.Tab',
                      background=[('selected', self.colors['primary']),
                                ('active', self.colors['hover'])],
                      foreground=[('selected', 'white'),
                                ('active', self.colors['text_primary'])],
                      expand=[('selected', [1, 1, 1, 0])])
        
        # Configure treeview style
        self.style.configure('Treeview', 
                           rowheight=28,
                           background='white',
                           foreground=self.colors['text_primary'],
                           fieldbackground='white',
                           borderwidth=1,
                           relief='flat')
        self.style.configure('Treeview.Heading', 
                           font=('Segoe UI', 11, 'bold'),
                           background=self.colors['bg_light'],
                           foreground=self.colors['text_primary'],
                           relief='flat',
                           borderwidth=1)
        self.style.map('Treeview',
                      background=[('selected', self.colors['primary'])],
                      foreground=[('selected', 'white')])
        
        # Frame styles
        self.style.configure('TFrame', background=self.colors['bg_light'])
        self.style.configure('TLabel', 
                           background=self.colors['bg_light'],
                           foreground=self.colors['text_primary'],
                           font=('Segoe UI', 10))
        
        # LabelFrame styles
        self.style.configure('TLabelframe',
                           background=self.colors['bg_light'],
                           borderwidth=2,
                           relief='flat',
                           bordercolor=self.colors['border'])
        self.style.configure('TLabelframe.Label',
                           background=self.colors['bg_light'],
                           foreground=self.colors['primary'],
                           font=('Segoe UI', 11, 'bold'))
        
    def load_settings(self):
        """Load settings from JSON file"""
        settings_file = "launcher_settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_settings(self):
        """Save settings to JSON file"""
        settings_file = "launcher_settings.json"
        self.settings = {
            "selected_version": self.selected_version,
            "selected_mod_loader": self.selected_mod_loader,
            "java_path": self.java_path,
            "allocated_ram": self.allocated_ram,
            "username": self.username,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "fullscreen": self.fullscreen,
            "custom_jvm_args": self.custom_jvm_args,
            "server_ip": self.server_ip,
            "server_port": self.server_port,
            "favorite_versions": list(self.favorite_versions),
            "recent_versions": self.recent_versions[-10:],  # Keep last 10
            "theme": self.theme
        }
        with open(settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def find_java(self):
        """Try to find Java installation"""
        try:
            # Try java_utils from minecraft_launcher_lib
            java_path = minecraft_launcher_lib.java_utils.get_java_path()
            if java_path:
                return java_path
        except:
            pass
        
        # Fallback to checking common locations
        common_paths = [
            "java",
            "javaw",
            "C:\\Program Files\\Java\\jdk-17\\bin\\javaw.exe",
            "C:\\Program Files\\Java\\jre-17\\bin\\javaw.exe",
            "C:\\Program Files (x86)\\Java\\jre-17\\bin\\javaw.exe",
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run([path, "-version"], capture_output=True, timeout=5)
                if result.returncode == 0 or result.returncode == 1:
                    return path
            except:
                continue
        return "java"
    
    def create_ui(self):
        """Create the main UI"""
        # Main container with modern padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title with logo (using logo image if available, otherwise text)
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Try to load and display logo image
        logo_paths = [
            "assets/logo.png",
            "assets/dan_launcher_logo.png",
            "assets/launcher_logo.png",
            "logo.png"
        ]
        
        logo_image = None
        logo_path = None
        for path in logo_paths:
            if os.path.exists(path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path)
                    # Resize if too large (max width 600px)
                    max_width = 600
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_size = (max_width, int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    logo_image = ImageTk.PhotoImage(img)
                    logo_path = path
                    break
                except Exception as e:
                    print(f"Could not load logo from {path}: {e}")
                    continue
        
        if logo_image:
            # Display logo
            # Get background color from root window (ttk.Frame doesn't have background option)
            try:
                bg_color = self.root.cget('bg')
            except:
                bg_color = 'white'
            
            logo_label = tk.Label(title_frame, image=logo_image, bg=bg_color)
            logo_label.image = logo_image  # Keep a reference
            logo_label.grid(row=0, column=0, pady=5)
            subtitle_label = ttk.Label(title_frame, text="Minecraft Launcher with Mod Support", 
                                      font=('Segoe UI', 9), foreground='#7f8c8d')
            subtitle_label.grid(row=1, column=0, pady=(5, 0))
        else:
            # Fallback to text title
            if self.font_renderer:
                try:
                    title_canvas = create_title_with_font(
                        title_frame, "DAN LAUNCHER", 
                        self.font_renderer, 
                        fallback_text="🎮 Dan Launcher"
                    )
                    title_canvas.grid(row=0, column=0)
                except:
                    title_label = ttk.Label(title_frame, text="🎮 Dan Launcher", style='Title.TLabel')
                    title_label.grid(row=0, column=0)
            else:
                title_label = ttk.Label(title_frame, text="🎮 Dan Launcher", style='Title.TLabel')
                title_label.grid(row=0, column=0)
            
            subtitle_label = ttk.Label(title_frame, text="Minecraft Launcher with Mod Support", 
                                      font=('Segoe UI', 9), foreground='#7f8c8d')
            subtitle_label.grid(row=1, column=0, pady=(5, 0))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Play Tab
        self.create_play_tab()
        
        # Versions Tab
        self.create_versions_tab()
        
        # Mods Tab
        self.create_mods_tab()
        
        # Resource Packs Tab
        self.create_resourcepacks_tab()
        
        # Servers Tab
        self.create_servers_tab()
        
        # Profiles Tab (NEW)
        self.create_profiles_tab()
        
        # Statistics Tab (NEW)
        self.create_statistics_tab()
        
        # News Tab (NEW)
        self.create_news_tab()
        
        # Settings Tab
        self.create_settings_tab()
        
        # Apply theme
        self.apply_theme()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_play_tab(self):
        """Create the Play tab"""
        play_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(play_frame, text="▶ Play")
        
        # Version selection with modern styling
        version_frame = ttk.LabelFrame(play_frame, text="🎮 Version Selection", padding="15")
        version_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(version_frame, text="Minecraft Version:").grid(row=0, column=0, padx=5, pady=5)
        self.version_var = tk.StringVar(value=self.selected_version if self.selected_version else "")
        self.version_combo = ttk.Combobox(version_frame, textvariable=self.version_var, state="readonly", width=30)
        self.version_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Set placeholder if no version selected
        if not self.selected_version:
            self.version_combo.set("")  # Clear any placeholder text
        
        # Mod loader selection
        ttk.Label(version_frame, text="Mod Loader:").grid(row=1, column=0, padx=5, pady=5)
        self.mod_loader_var = tk.StringVar(value=self.selected_mod_loader)
        mod_loader_combo = ttk.Combobox(version_frame, textvariable=self.mod_loader_var, 
                                       values=["vanilla", "forge", "fabric", "quilt"], 
                                       state="readonly", width=30)
        mod_loader_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Username with modern styling
        username_frame = ttk.LabelFrame(play_frame, text="👤 Player Info", padding="15")
        username_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(username_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_var = tk.StringVar(value=self.username)
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Launch button with info
        launch_frame = ttk.Frame(play_frame, padding="10")
        launch_frame.grid(row=2, column=0, pady=20)
        
        button_container = ttk.Frame(launch_frame)
        button_container.grid(row=0, column=0)
        
        self.launch_button = ttk.Button(button_container, text="▶ Launch Minecraft", 
                                       style='Big.TButton', command=self.launch_minecraft)
        self.launch_button.grid(row=0, column=0, padx=10)
        
        info_label = ttk.Label(launch_frame, 
                              text="💡 Tip: Make sure you have Java installed and the version is downloaded!",
                              font=('Segoe UI', 9), 
                              foreground=self.colors['text_secondary'])
        info_label.grid(row=1, column=0, pady=(15, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(play_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Log output with modern styling
        log_frame = ttk.LabelFrame(play_frame, text="📋 Log", padding="15")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        play_frame.rowconfigure(4, weight=1)
        
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(log_button_frame, text="Export Log", command=self.export_log).pack(side=tk.RIGHT, padx=5)
        ttk.Button(log_button_frame, text="Clear Log", command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.RIGHT, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_versions_tab(self):
        """Create the Versions tab"""
        versions_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(versions_frame, text="Versions")
        
        # Search/Filter frame (NEW)
        search_frame = ttk.Frame(versions_frame)
        search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.version_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.version_search_var, width=30)
        search_entry.grid(row=0, column=1, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_versions())
        
        ttk.Button(search_frame, text="Clear", command=lambda: [self.version_search_var.set(""), self.filter_versions()]).grid(row=0, column=2, padx=5)
        
        # Available versions list with modern styling
        list_frame = ttk.LabelFrame(versions_frame, text="📦 Available Versions", padding="15")
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        versions_frame.columnconfigure(0, weight=1)
        versions_frame.rowconfigure(1, weight=1)
        
        # Treeview for versions
        columns = ('version', 'type', 'installed')
        self.version_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        self.version_tree.heading('#0', text='')
        self.version_tree.heading('version', text='Version')
        self.version_tree.heading('type', text='Type')
        self.version_tree.heading('installed', text='Status')
        self.version_tree.column('#0', width=0, stretch=False)
        self.version_tree.column('version', width=200)
        self.version_tree.column('type', width=100)
        self.version_tree.column('installed', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.version_tree.yview)
        self.version_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click to select version in play tab
        self.version_tree.bind("<Double-1>", self.on_version_tree_double_click)
        
        self.version_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        # Mod Loader Installation Frame with modern styling
        mod_loader_frame = ttk.LabelFrame(versions_frame, text="🔧 Mod Loader Installation", padding="15")
        mod_loader_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(mod_loader_frame, text="For Minecraft Version:").grid(row=0, column=0, padx=5, pady=5)
        self.mod_loader_version_var = tk.StringVar()
        self.mod_loader_version_combo = ttk.Combobox(mod_loader_frame, textvariable=self.mod_loader_version_var, 
                                                     state="readonly", width=25)
        self.mod_loader_version_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(mod_loader_frame, text="Mod Loader:").grid(row=0, column=2, padx=5, pady=5)
        self.mod_loader_type_var = tk.StringVar(value="fabric")
        mod_loader_type_combo = ttk.Combobox(mod_loader_frame, textvariable=self.mod_loader_type_var,
                                            values=["fabric", "forge", "quilt"], state="readonly", width=15)
        mod_loader_type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(mod_loader_frame, text="Install Mod Loader", 
                  command=self.install_mod_loader).grid(row=0, column=4, padx=5, pady=5)
        
        # Buttons with modern styling
        button_frame = ttk.Frame(versions_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 0))
        
        ttk.Button(button_frame, text="Refresh List", command=self.load_versions).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Install Selected", command=self.install_version).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete Version", command=self.delete_version).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="⭐ Add to Favorites", command=self.toggle_favorite).grid(row=0, column=3, padx=5)
    
    def create_mods_tab(self):
        """Create the Mods tab"""
        mods_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(mods_frame, text="🔌 Mods")
        
        # Installed mods list with modern styling
        mods_list_frame = ttk.LabelFrame(mods_frame, text="📦 Installed Mods", padding="15")
        mods_list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        mods_frame.columnconfigure(0, weight=1)
        mods_frame.rowconfigure(0, weight=1)
        
        self.mods_listbox = tk.Listbox(mods_list_frame, height=15)
        mods_scrollbar = ttk.Scrollbar(mods_list_frame, orient=tk.VERTICAL, command=self.mods_listbox.yview)
        self.mods_listbox.configure(yscrollcommand=mods_scrollbar.set)
        
        self.mods_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        mods_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        mods_list_frame.rowconfigure(0, weight=1)
        mods_list_frame.columnconfigure(0, weight=1)
        
        # Mod buttons
        mod_button_frame = ttk.Frame(mods_frame)
        mod_button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(mod_button_frame, text="Add Mod", command=self.add_mod).grid(row=0, column=0, padx=5)
        ttk.Button(mod_button_frame, text="Remove Mod", command=self.remove_mod).grid(row=0, column=1, padx=5)
        ttk.Button(mod_button_frame, text="Enable/Disable", command=self.toggle_mod).grid(row=0, column=2, padx=5)
        ttk.Button(mod_button_frame, text="Refresh List", command=self.load_mods).grid(row=0, column=3, padx=5)
        ttk.Button(mod_button_frame, text="Open Mods Folder", command=self.open_mods_folder).grid(row=0, column=4, padx=5)
        
        self.load_mods()
    
    def create_settings_tab(self):
        """Create the Settings tab"""
        settings_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Create scrollable frame
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Java settings
        java_frame = ttk.LabelFrame(scrollable_frame, text="☕ Java Settings", padding="15")
        java_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(java_frame, text="Java Path:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.java_path_var = tk.StringVar(value=self.java_path)
        java_entry = ttk.Entry(java_frame, textvariable=self.java_path_var, width=50)
        java_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(java_frame, text="Browse", command=self.browse_java).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(java_frame, text="Auto-detect", command=self.auto_detect_java).grid(row=0, column=3, padx=5, pady=5)
        java_frame.columnconfigure(1, weight=1)
        
        # Memory settings with modern styling
        memory_frame = ttk.LabelFrame(scrollable_frame, text="💾 Memory Settings", padding="15")
        memory_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(memory_frame, text="Allocated RAM (MB):").grid(row=0, column=0, padx=5, pady=5)
        self.ram_var = tk.IntVar(value=self.allocated_ram)
        ram_scale = ttk.Scale(memory_frame, from_=1024, to=16384, variable=self.ram_var, 
                             orient=tk.HORIZONTAL, length=400)
        ram_scale.grid(row=0, column=1, padx=5, pady=5)
        
        ram_label = ttk.Label(memory_frame, textvariable=self.ram_var)
        ram_label.grid(row=0, column=2, padx=5, pady=5)
        
        def update_ram_label(value):
            ram_label.config(text=f"{int(float(value))} MB")
        ram_scale.configure(command=update_ram_label)
        
        # Window settings
        window_frame = ttk.LabelFrame(scrollable_frame, text="Window Settings", padding="10")
        window_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(window_frame, text="Window Width:").grid(row=0, column=0, padx=5, pady=5)
        self.window_width_var = tk.IntVar(value=self.window_width)
        width_entry = ttk.Entry(window_frame, textvariable=self.window_width_var, width=10)
        width_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(window_frame, text="Window Height:").grid(row=0, column=2, padx=5, pady=5)
        self.window_height_var = tk.IntVar(value=self.window_height)
        height_entry = ttk.Entry(window_frame, textvariable=self.window_height_var, width=10)
        height_entry.grid(row=0, column=3, padx=5, pady=5)
        
        self.fullscreen_var = tk.BooleanVar(value=self.fullscreen)
        fullscreen_check = ttk.Checkbutton(window_frame, text="Fullscreen", variable=self.fullscreen_var)
        fullscreen_check.grid(row=0, column=4, padx=5, pady=5)
        
        # Custom JVM Arguments
        jvm_frame = ttk.LabelFrame(scrollable_frame, text="Custom JVM Arguments", padding="10")
        jvm_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        self.custom_jvm_args_var = tk.StringVar(value=self.custom_jvm_args)
        jvm_text = scrolledtext.ScrolledText(jvm_frame, height=4, width=60)
        jvm_text.insert("1.0", self.custom_jvm_args)
        jvm_text.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        jvm_frame.columnconfigure(0, weight=1)
        self.jvm_text_widget = jvm_text
        
        info_jvm = ttk.Label(jvm_frame, 
                            text="💡 Add custom JVM arguments here (one per line)",
                            font=('Segoe UI', 8), foreground='#7f8c8d')
        info_jvm.grid(row=1, column=0, padx=5, pady=5)
        
        # Theme settings
        theme_frame = ttk.LabelFrame(scrollable_frame, text="Appearance", padding="10")
        theme_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, padx=5, pady=5)
        self.theme_var = tk.StringVar(value=self.theme)
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                  values=["light", "dark"], state="readonly", width=20)
        theme_combo.grid(row=0, column=1, padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_theme())
        
        # Export/Import settings
        export_frame = ttk.LabelFrame(scrollable_frame, text="Settings Management", padding="10")
        export_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(export_frame, text="Export Settings", command=self.export_settings).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(export_frame, text="Import Settings", command=self.import_settings).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(export_frame, text="Reset to Defaults", command=self.reset_settings).grid(row=0, column=2, padx=5, pady=5)
        
        # Save button
        ttk.Button(scrollable_frame, text="💾 Save All Settings", command=self.save_settings_ui, 
                  style='Action.TButton').grid(row=6, column=0, pady=20)
        
        # Pack canvas and scrollbar
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        settings_frame.rowconfigure(0, weight=1)
        settings_frame.columnconfigure(0, weight=1)
    
    def browse_java(self):
        """Browse for Java executable"""
        file_path = filedialog.askopenfilename(
            title="Select Java Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.java_path_var.set(file_path)
    
    def save_settings_ui(self):
        """Save settings from UI"""
        self.username = self.username_var.get()
        self.java_path = self.java_path_var.get()
        self.allocated_ram = self.ram_var.get()
        self.selected_version = self.version_var.get()
        self.selected_mod_loader = self.mod_loader_var.get()
        self.window_width = self.window_width_var.get()
        self.window_height = self.window_height_var.get()
        self.fullscreen = self.fullscreen_var.get()
        self.custom_jvm_args = self.jvm_text_widget.get("1.0", tk.END).strip()
        self.theme = self.theme_var.get()
        self.server_ip = self.server_ip_var.get()
        self.server_port = self.server_port_var.get()
        self.save_settings()
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def auto_detect_java(self):
        """Auto-detect Java installation"""
        java_path = self.find_java()
        if java_path:
            self.java_path_var.set(java_path)
            messagebox.showinfo("Java Detected", f"Java found at:\n{java_path}")
        else:
            messagebox.showwarning("Java Not Found", "Could not auto-detect Java.\nPlease browse for Java manually.")
    
    def apply_theme(self):
        """Apply theme to the launcher"""
        theme = self.theme_var.get() if hasattr(self, 'theme_var') else self.theme
        if theme == "dark":
            # Dark theme colors
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            self.root.configure(bg=bg_color)
            self.style.configure('TFrame', background=bg_color, foreground=fg_color)
            self.style.configure('TLabel', background=bg_color, foreground=fg_color)
            self.style.configure('TButton', background="#3d3d3d", foreground=fg_color)
        else:
            # Light theme (default)
            bg_color = "white"
            fg_color = "#000000"
            self.root.configure(bg=bg_color)
            self.style.configure('TFrame', background=bg_color, foreground=fg_color)
            self.style.configure('TLabel', background=bg_color, foreground=fg_color)
            self.style.configure('TButton', background=bg_color, foreground=fg_color)
    
    def export_settings(self):
        """Export settings to a JSON file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.settings, f, indent=2)
                messagebox.showinfo("Success", f"Settings exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export settings:\n{str(e)}")
    
    def import_settings(self):
        """Import settings from a JSON file"""
        file_path = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)
                self.settings.update(imported_settings)
                # Reload settings
                self.selected_version = self.settings.get("selected_version", "")
                self.selected_mod_loader = self.settings.get("selected_mod_loader", "vanilla")
                self.java_path = self.settings.get("java_path", self.find_java())
                self.allocated_ram = self.settings.get("allocated_ram", 4096)
                self.username = self.settings.get("username", "Player")
                self.window_width = self.settings.get("window_width", 854)
                self.window_height = self.settings.get("window_height", 480)
                self.fullscreen = self.settings.get("fullscreen", False)
                self.custom_jvm_args = self.settings.get("custom_jvm_args", "")
                self.theme = self.settings.get("theme", "light")
                self.save_settings()
                messagebox.showinfo("Success", "Settings imported successfully!\nPlease restart the launcher for all changes to take effect.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings:\n{str(e)}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            self.settings = {}
            self.selected_version = ""
            self.selected_mod_loader = "vanilla"
            self.java_path = self.find_java()
            self.allocated_ram = 4096
            self.username = "Player"
            self.window_width = 854
            self.window_height = 480
            self.fullscreen = False
            self.custom_jvm_args = ""
            self.theme = "light"
            self.save_settings()
            messagebox.showinfo("Settings Reset", "Settings have been reset to defaults.\nPlease restart the launcher.")
    
    def add_server(self):
        """Add a server to saved list"""
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        if not ip:
            messagebox.showwarning("No IP", "Please enter a server IP address")
            return
        if not port:
            port = "25565"
        server_info = f"{ip}:{port}"
        if server_info not in self.settings.get("saved_servers", []):
            if "saved_servers" not in self.settings:
                self.settings["saved_servers"] = []
            self.settings["saved_servers"].append(server_info)
            self.save_settings()
            self.load_saved_servers()
            messagebox.showinfo("Success", f"Server {server_info} added!")
    
    def remove_server(self):
        """Remove selected server"""
        selected = self.saved_servers_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a server to remove")
            return
        server_info = self.saved_servers_listbox.get(selected[0])
        if server_info in self.settings.get("saved_servers", []):
            self.settings["saved_servers"].remove(server_info)
            self.save_settings()
            self.load_saved_servers()
    
    def connect_to_server(self):
        """Connect to selected server"""
        selected = self.saved_servers_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a server")
            return
        server_info = self.saved_servers_listbox.get(selected[0])
        if ":" in server_info:
            ip, port = server_info.split(":")
            self.server_ip_var.set(ip)
            self.server_port_var.set(port)
            messagebox.showinfo("Server Selected", f"Server {server_info} selected.\nLaunch Minecraft to connect.")
    
    def load_saved_servers(self):
        """Load saved servers list"""
        self.saved_servers_listbox.delete(0, tk.END)
        for server in self.settings.get("saved_servers", []):
            self.saved_servers_listbox.insert(tk.END, server)
    
    def load_favorite_versions(self):
        """Load favorite versions"""
        pass  # Will be implemented with version tree enhancements
    
    def toggle_favorite(self):
        """Toggle favorite status of selected version"""
        selected = self.version_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a version")
            return
        item = self.version_tree.item(selected[0])
        version = item['values'][0]
        if version in self.favorite_versions:
            self.favorite_versions.remove(version)
            messagebox.showinfo("Favorite Removed", f"{version} removed from favorites")
        else:
            self.favorite_versions.add(version)
            messagebox.showinfo("Favorite Added", f"{version} added to favorites")
        self.save_settings()
    
    def load_versions(self):
        """Load available Minecraft versions"""
        self.status_var.set("Loading versions...")
        self.log("Fetching Minecraft versions...")
        
        def fetch_versions():
            try:
                # Get version list
                version_list = minecraft_launcher_lib.utils.get_version_list()
                
                # Clear tree
                for item in self.version_tree.get_children():
                    self.version_tree.delete(item)
                
                # Check installed versions
                installed_versions = set()
                if os.path.exists(self.versions_dir):
                    for version_dir in os.listdir(self.versions_dir):
                        version_path = os.path.join(self.versions_dir, version_dir, f"{version_dir}.json")
                        if os.path.exists(version_path):
                            installed_versions.add(version_dir)
                
                # Collect version IDs for combo box (including installed mod loader versions)
                version_ids = []
                
                # Add vanilla versions to tree
                for version_info in version_list:
                    version_id = version_info["id"]
                    version_type = version_info["type"]
                    is_installed = "Installed" if version_id in installed_versions else "Not Installed"
                    
                    self.version_tree.insert('', tk.END, values=(version_id, version_type, is_installed))
                    version_ids.append(version_id)
                
                # Also add installed mod loader versions
                for installed_version in installed_versions:
                    if installed_version not in version_ids:
                        # This might be a mod loader version (e.g., fabric-1.20.1)
                        self.version_tree.insert('', tk.END, values=(installed_version, "modded", "Installed"))
                        version_ids.append(installed_version)
                
                # Update combo boxes
                sorted_versions = sorted(version_ids, reverse=True)
                self.root.after(0, lambda: self.update_version_combos(sorted_versions))
                
                self.root.after(0, lambda: self.status_var.set("Versions loaded"))
                self.log(f"Loaded {len(version_list)} versions")
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Error loading versions: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Error loading versions"))
        
        threading.Thread(target=fetch_versions, daemon=True).start()
    
    def install_version(self):
        """Install selected version"""
        selected = self.version_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a version to install")
            return
        
        item = self.version_tree.item(selected[0])
        version = item['values'][0]
        
        if messagebox.askyesno("Install Version", f"Install Minecraft {version}?"):
            self.status_var.set(f"Installing {version}...")
            self.launch_button.config(state=tk.DISABLED)
            
            def install():
                try:
                    callback = {
                        "setStatus": lambda text: self.root.after(0, lambda: self.update_status(text)),
                        "setProgress": lambda progress: self.root.after(0, lambda: self.update_progress(progress)),
                        "setMax": lambda max_val: self.root.after(0, lambda: self.progress_bar.config(maximum=max_val))
                    }
                    
                    minecraft_launcher_lib.install.install_minecraft_version(
                        version, self.minecraft_directory, callback=callback
                    )
                    
                    self.root.after(0, lambda: self.log(f"Successfully installed {version}"))
                    self.root.after(0, lambda: self.status_var.set(f"Installed {version}"))
                    self.root.after(0, lambda: self.load_versions())
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    
                    # Update version combo
                    versions = [self.version_tree.item(item)['values'][0] 
                               for item in self.version_tree.get_children()]
                    if version not in self.version_combo['values']:
                        self.version_combo['values'] = versions
                    self.version_var.set(version)
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"Error installing version: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Installation failed"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    messagebox.showerror("Installation Error", f"Failed to install version:\n{str(e)}")
            
            threading.Thread(target=install, daemon=True).start()
    
    def on_version_tree_double_click(self, event):
        """Handle double-click on version tree to select it in play tab"""
        item = self.version_tree.selection()[0] if self.version_tree.selection() else None
        if item:
            version_data = self.version_tree.item(item)
            version = version_data['values'][0]
            if version:
                self.version_var.set(version)
                # Switch to Play tab
                self.notebook.select(0)
                self.log(f"Selected version: {version}")
    
    def delete_version(self):
        """Delete selected version"""
        selected = self.version_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a version to delete")
            return
        
        item = self.version_tree.item(selected[0])
        version = item['values'][0]
        
        if messagebox.askyesno("Delete Version", f"Delete Minecraft {version}?\n\nThis will remove the version files."):
            try:
                version_dir = os.path.join(self.versions_dir, version)
                if os.path.exists(version_dir):
                    shutil.rmtree(version_dir)
                    self.log(f"Deleted {version}")
                    self.load_versions()
                    messagebox.showinfo("Success", f"Version {version} deleted")
                else:
                    messagebox.showwarning("Not Found", "Version directory not found")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete version:\n{str(e)}")
    
    def install_mod_loader(self):
        """Install a mod loader for a Minecraft version"""
        minecraft_version = self.mod_loader_version_var.get()
        loader_type = self.mod_loader_type_var.get()
        
        if not minecraft_version:
            messagebox.showwarning("No Version", "Please select a Minecraft version")
            return
        
        # First ensure the base version is installed
        version_json = os.path.join(self.versions_dir, minecraft_version, f"{minecraft_version}.json")
        if not os.path.exists(version_json):
            if not messagebox.askyesno("Version Not Installed", 
                                      f"Minecraft {minecraft_version} is not installed.\n"
                                      f"Would you like to install it first?"):
                return
            # Install the base version first
            try:
                callback = {
                    "setStatus": lambda text: self.root.after(0, lambda: self.update_status(text)),
                    "setProgress": lambda progress: self.root.after(0, lambda: self.update_progress(progress)),
                    "setMax": lambda max_val: self.root.after(0, lambda: self.progress_bar.config(maximum=max_val))
                }
                minecraft_launcher_lib.install.install_minecraft_version(
                    minecraft_version, self.minecraft_directory, callback=callback
                )
            except Exception as e:
                messagebox.showerror("Installation Error", f"Failed to install base version:\n{str(e)}")
                return
        
        # Now install the mod loader
        if messagebox.askyesno("Install Mod Loader", 
                              f"Install {loader_type.capitalize()} for Minecraft {minecraft_version}?"):
            self.status_var.set(f"Installing {loader_type.capitalize()}...")
            self.launch_button.config(state=tk.DISABLED)
            
            def install_loader():
                try:
                    callback = {
                        "setStatus": lambda text: self.root.after(0, lambda: self.update_status(text)),
                        "setProgress": lambda progress: self.root.after(0, lambda: self.update_progress(progress)),
                        "setMax": lambda max_val: self.root.after(0, lambda: self.progress_bar.config(maximum=max_val))
                    }
                    
                    java_path = self.java_path_var.get()
                    
                    if loader_type == "fabric":
                        minecraft_launcher_lib.fabric.install_fabric(
                            minecraft_version, self.minecraft_directory, 
                            callback=callback, java=java_path
                        )
                    elif loader_type == "forge":
                        minecraft_launcher_lib.forge.install_forge_version(
                            minecraft_version, self.minecraft_directory, 
                            callback=callback, java=java_path
                        )
                    elif loader_type == "quilt":
                        minecraft_launcher_lib.quilt.install_quilt(
                            minecraft_version, self.minecraft_directory,
                            callback=callback, java=java_path
                        )
                    
                    loader_version_id = f"{loader_type}-{minecraft_version}"
                    self.root.after(0, lambda: self.log(f"Successfully installed {loader_type.capitalize()} for {minecraft_version}"))
                    self.root.after(0, lambda: self.status_var.set(f"Installed {loader_type.capitalize()}"))
                    self.root.after(0, lambda: self.load_versions())
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: messagebox.showinfo("Success", 
                        f"{loader_type.capitalize()} installed successfully!\n"
                        f"You can now select it in the Play tab."))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log(f"Error installing mod loader: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Installation failed"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    messagebox.showerror("Installation Error", 
                                       f"Failed to install {loader_type.capitalize()}:\n{str(e)}")
            
            threading.Thread(target=install_loader, daemon=True).start()
    
    def load_mods(self):
        """Load list of installed mods"""
        self.mods_listbox.delete(0, tk.END)
        disabled_mods_dir = os.path.join(self.mods_dir, "disabled")
        os.makedirs(disabled_mods_dir, exist_ok=True)
        
        if os.path.exists(self.mods_dir):
            mod_files = [f for f in os.listdir(self.mods_dir) 
                        if f.endswith(('.jar', '.zip')) and os.path.isfile(os.path.join(self.mods_dir, f))]
            disabled_files = [f for f in os.listdir(disabled_mods_dir) 
                             if f.endswith(('.jar', '.zip')) and os.path.isfile(os.path.join(disabled_mods_dir, f))]
            for mod in sorted(mod_files):
                self.mods_listbox.insert(tk.END, f"✓ {mod}")
            for mod in sorted(disabled_files):
                self.mods_listbox.insert(tk.END, f"✗ {mod}")
    
    def toggle_mod(self):
        """Enable or disable a mod"""
        selected = self.mods_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a mod")
            return
        
        mod_display = self.mods_listbox.get(selected[0])
        is_enabled = mod_display.startswith("✓ ")
        mod_name = mod_display[2:] if is_enabled else mod_display[2:]
        
        disabled_mods_dir = os.path.join(self.mods_dir, "disabled")
        os.makedirs(disabled_mods_dir, exist_ok=True)
        
        try:
            if is_enabled:
                # Disable mod
                src = os.path.join(self.mods_dir, mod_name)
                dst = os.path.join(disabled_mods_dir, mod_name)
                if os.path.exists(src):
                    shutil.move(src, dst)
                    self.log(f"Disabled mod: {mod_name}")
            else:
                # Enable mod
                src = os.path.join(disabled_mods_dir, mod_name)
                dst = os.path.join(self.mods_dir, mod_name)
                if os.path.exists(src):
                    shutil.move(src, dst)
                    self.log(f"Enabled mod: {mod_name}")
            self.load_mods()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle mod:\n{str(e)}")
    
    def add_mod(self):
        """Add a mod file"""
        file_path = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[("JAR files", "*.jar"), ("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if file_path:
            mod_name = os.path.basename(file_path)
            dest_path = os.path.join(self.mods_dir, mod_name)
            try:
                shutil.copy2(file_path, dest_path)
                self.load_mods()
                self.log(f"Added mod: {mod_name}")
                messagebox.showinfo("Success", f"Mod {mod_name} added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add mod:\n{str(e)}")
    
    def remove_mod(self):
        """Remove selected mod"""
        selected = self.mods_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a mod to remove")
            return
        
        mod_name_full = self.mods_listbox.get(selected[0])
        # Remove [DISABLED] prefix if present
        mod_name = mod_name_full.replace("[DISABLED] ", "")
        
        if messagebox.askyesno("Remove Mod", f"Remove mod {mod_name}?"):
            mod_path = os.path.join(self.mods_dir, mod_name)
            try:
                os.remove(mod_path)
                # Remove from disabled mods if it was disabled
                if mod_name in self.disabled_mods:
                    self.disabled_mods.remove(mod_name)
                    self.settings["disabled_mods"] = list(self.disabled_mods)
                    self.save_settings()
                self.load_mods()
                self.log(f"Removed mod: {mod_name}")
                messagebox.showinfo("Success", f"Mod {mod_name} removed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove mod:\n{str(e)}")
    
    def open_mods_folder(self):
        """Open mods folder in file explorer"""
        os.makedirs(self.mods_dir, exist_ok=True)
        os.startfile(self.mods_dir)
    
    def create_resourcepacks_tab(self):
        """Create the Resource Packs tab"""
        rp_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(rp_frame, text="🎨 Resource Packs")
        
        # Installed resource packs list with modern styling
        rp_list_frame = ttk.LabelFrame(rp_frame, text="📦 Installed Resource Packs", padding="15")
        rp_list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        rp_frame.columnconfigure(0, weight=1)
        rp_frame.rowconfigure(0, weight=1)
        
        self.rp_listbox = tk.Listbox(rp_list_frame, height=15)
        rp_scrollbar = ttk.Scrollbar(rp_list_frame, orient=tk.VERTICAL, command=self.rp_listbox.yview)
        self.rp_listbox.configure(yscrollcommand=rp_scrollbar.set)
        
        self.rp_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        rp_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        rp_list_frame.rowconfigure(0, weight=1)
        rp_list_frame.columnconfigure(0, weight=1)
        
        # Resource pack buttons
        rp_button_frame = ttk.Frame(rp_frame)
        rp_button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(rp_button_frame, text="Add Resource Pack", command=self.add_resourcepack).grid(row=0, column=0, padx=5)
        ttk.Button(rp_button_frame, text="Remove Resource Pack", command=self.remove_resourcepack).grid(row=0, column=1, padx=5)
        ttk.Button(rp_button_frame, text="Refresh List", command=self.load_resourcepacks).grid(row=0, column=2, padx=5)
        ttk.Button(rp_button_frame, text="Open Resource Packs Folder", command=self.open_resourcepacks_folder).grid(row=0, column=3, padx=5)
        
        self.load_resourcepacks()
    
    def load_resourcepacks(self):
        """Load list of installed resource packs"""
        self.rp_listbox.delete(0, tk.END)
        if os.path.exists(self.resourcepacks_dir):
            rp_items = [f for f in os.listdir(self.resourcepacks_dir) 
                       if os.path.isdir(os.path.join(self.resourcepacks_dir, f)) or 
                       f.endswith(('.zip', '.rar'))]
            for rp in sorted(rp_items):
                self.rp_listbox.insert(tk.END, rp)
    
    def add_resourcepack(self):
        """Add a resource pack file"""
        file_path = filedialog.askopenfilename(
            title="Select Resource Pack File",
            filetypes=[("ZIP files", "*.zip"), ("RAR files", "*.rar"), ("All files", "*.*")]
        )
        if file_path:
            rp_name = os.path.basename(file_path)
            dest_path = os.path.join(self.resourcepacks_dir, rp_name)
            try:
                shutil.copy2(file_path, dest_path)
                self.load_resourcepacks()
                self.log(f"Added resource pack: {rp_name}")
                messagebox.showinfo("Success", f"Resource pack {rp_name} added successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add resource pack:\n{str(e)}")
    
    def remove_resourcepack(self):
        """Remove selected resource pack"""
        selected = self.rp_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a resource pack to remove")
            return
        
        rp_name = self.rp_listbox.get(selected[0])
        if messagebox.askyesno("Remove Resource Pack", f"Remove resource pack {rp_name}?"):
            rp_path = os.path.join(self.resourcepacks_dir, rp_name)
            try:
                if os.path.isdir(rp_path):
                    shutil.rmtree(rp_path)
                else:
                    os.remove(rp_path)
                self.load_resourcepacks()
                self.log(f"Removed resource pack: {rp_name}")
                messagebox.showinfo("Success", f"Resource pack {rp_name} removed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove resource pack:\n{str(e)}")
    
    def open_resourcepacks_folder(self):
        """Open resource packs folder in file explorer"""
        os.makedirs(self.resourcepacks_dir, exist_ok=True)
        os.startfile(self.resourcepacks_dir)
    
    def create_servers_tab(self):
        """Create the Servers tab for quick connect"""
        servers_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(servers_frame, text="🌐 Servers")
        
        # Quick connect frame with modern styling
        connect_frame = ttk.LabelFrame(servers_frame, text="⚡ Quick Connect", padding="15")
        connect_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(connect_frame, text="Server IP:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_ip_var = tk.StringVar(value=self.server_ip)
        server_ip_entry = ttk.Entry(connect_frame, textvariable=self.server_ip_var, width=30)
        server_ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(connect_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_port_var = tk.StringVar(value=self.server_port)
        server_port_entry = ttk.Entry(connect_frame, textvariable=self.server_port_var, width=15)
        server_port_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        info_label = ttk.Label(connect_frame, 
                              text="💡 Server will be automatically connected when you launch Minecraft",
                              font=('Segoe UI', 8), foreground='#3498db')
        info_label.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # Saved servers with modern styling
        saved_frame = ttk.LabelFrame(servers_frame, text="⭐ Saved Servers", padding="15")
        saved_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        servers_frame.rowconfigure(1, weight=1)
        
        self.saved_servers_listbox = tk.Listbox(saved_frame, height=10)
        servers_scrollbar = ttk.Scrollbar(saved_frame, orient=tk.VERTICAL, command=self.saved_servers_listbox.yview)
        self.saved_servers_listbox.configure(yscrollcommand=servers_scrollbar.set)
        
        self.saved_servers_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        servers_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        saved_frame.rowconfigure(0, weight=1)
        saved_frame.columnconfigure(0, weight=1)
        
        # Server buttons
        server_button_frame = ttk.Frame(servers_frame)
        server_button_frame.grid(row=2, column=0, pady=10)
        
        ttk.Button(server_button_frame, text="Add Server", command=self.add_server).grid(row=0, column=0, padx=5)
        ttk.Button(server_button_frame, text="Remove Server", command=self.remove_server).grid(row=0, column=1, padx=5)
        ttk.Button(server_button_frame, text="Connect to Selected", command=self.connect_to_server).grid(row=0, column=2, padx=5)
        
        self.load_saved_servers()
    
    def create_profiles_tab(self):
        """Create Profiles tab for managing multiple launch profiles"""
        profiles_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(profiles_frame, text="👤 Profiles")
        
        list_frame = ttk.LabelFrame(profiles_frame, text="📋 Profiles", padding="15")
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        profiles_frame.columnconfigure(0, weight=1)
        profiles_frame.rowconfigure(0, weight=1)
        
        self.profiles_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.profiles_listbox.yview)
        self.profiles_listbox.configure(yscrollcommand=scrollbar.set)
        self.profiles_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        button_frame = ttk.Frame(profiles_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="New Profile", command=self.create_new_profile).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Load Profile", command=self.load_profile).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete Profile", command=self.delete_profile).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Export Profile", command=self.export_profile).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Import Profile", command=self.import_profile).grid(row=0, column=4, padx=5)
        
        self.load_profiles_list()
    
    def create_statistics_tab(self):
        """Create Statistics tab"""
        stats_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(stats_frame, text="📊 Statistics")
        
        stats_text = scrolledtext.ScrolledText(stats_frame, height=20, wrap=tk.WORD, state=tk.DISABLED)
        stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        
        stats = self.settings.get("statistics", {})
        total_launches = stats.get("total_launches", 0)
        total_playtime = stats.get("total_playtime", 0)
        favorite_version = stats.get("most_used_version", "None")
        last_launch = stats.get("last_launch", "Never")
        installed_count = len([v for v in os.listdir(self.versions_dir) if os.path.isdir(os.path.join(self.versions_dir, v))]) if os.path.exists(self.versions_dir) else 0
        
        stats_text.config(state=tk.NORMAL)
        stats_text.insert(tk.END, "📊 Launcher Statistics\n")
        stats_text.insert(tk.END, "=" * 40 + "\n\n")
        stats_text.insert(tk.END, f"Total Launches: {total_launches}\n\n")
        stats_text.insert(tk.END, f"Total Playtime: {total_playtime // 3600}h {(total_playtime % 3600) // 60}m\n\n")
        stats_text.insert(tk.END, f"Most Used Version: {favorite_version}\n\n")
        stats_text.insert(tk.END, f"Last Launch: {last_launch}\n\n")
        stats_text.insert(tk.END, f"Installed Versions: {installed_count}\n\n")
        stats_text.config(state=tk.DISABLED)
        self.stats_text_widget = stats_text
    
    def create_news_tab(self):
        """Create News tab"""
        news_frame = ttk.Frame(self.notebook, padding="25")
        self.notebook.add(news_frame, text="📰 News")
        
        news_text = scrolledtext.ScrolledText(news_frame, height=20, wrap=tk.WORD)
        news_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        news_frame.columnconfigure(0, weight=1)
        news_frame.rowconfigure(0, weight=1)
        
        news_text.insert(tk.END, "📰 Dan Launcher News & Updates\n")
        news_text.insert(tk.END, "=" * 40 + "\n\n")
        news_text.insert(tk.END, "✅ Dan Launcher v0.5 - First Open Beta!\n\n")
        news_text.insert(tk.END, "New Features:\n")
        news_text.insert(tk.END, "• Profile system for multiple configurations\n")
        news_text.insert(tk.END, "• Statistics tracking\n")
        news_text.insert(tk.END, "• Enhanced mod management\n")
        news_text.insert(tk.END, "• Dark theme support\n")
        news_text.insert(tk.END, "• Export/Import profiles\n")
        news_text.insert(tk.END, "• Server favorites\n")
        news_text.insert(tk.END, "• Version search/filter\n\n")
        news_text.insert(tk.END, "For the latest Minecraft news, visit:\n")
        news_text.insert(tk.END, "https://www.minecraft.net/en-us/news\n")
        news_text.config(state=tk.DISABLED)
    
    def filter_versions(self):
        """Filter versions based on search"""
        search_term = self.version_search_var.get().lower()
        for item in self.version_tree.get_children():
            item_values = self.version_tree.item(item)['values']
            version_text = item_values[0].lower() if item_values else ""
            if search_term in version_text or search_term == "":
                self.version_tree.item(item, open=True)
            else:
                self.version_tree.item(item, open=False)
    
    def create_new_profile(self):
        """Create a new profile"""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Profile")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Profile Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Minecraft Version:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        version_var = tk.StringVar()
        version_combo = ttk.Combobox(dialog, textvariable=version_var, width=27, values=list(self.version_combo['values']))
        version_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="RAM (MB):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        ram_var = tk.IntVar(value=4096)
        ttk.Spinbox(dialog, from_=1024, to=16384, textvariable=ram_var, width=27).grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Mod Loader:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        loader_var = tk.StringVar(value="vanilla")
        loader_combo = ttk.Combobox(dialog, textvariable=loader_var, values=["vanilla", "forge", "fabric", "quilt"], width=27)
        loader_combo.grid(row=3, column=1, padx=10, pady=10)
        
        def save_profile():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a profile name")
                return
            
            profiles = self.settings.get("profiles", {})
            if name in profiles:
                if not messagebox.askyesno("Overwrite", f"Profile '{name}' already exists. Overwrite?"):
                    return
            
            profiles[name] = {
                "version": version_var.get(),
                "ram": ram_var.get(),
                "mod_loader": loader_var.get(),
                "username": self.username,
                "created": datetime.now().isoformat()
            }
            self.settings["profiles"] = profiles
            self.save_settings()
            self.load_profiles_list()
            dialog.destroy()
        
        ttk.Button(dialog, text="Create", command=save_profile).grid(row=4, column=0, columnspan=2, pady=20)
    
    def load_profile(self):
        """Load selected profile"""
        selected = self.profiles_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to load")
            return
        
        profile_name = self.profiles_listbox.get(selected[0])
        profiles = self.settings.get("profiles", {})
        if profile_name not in profiles:
            messagebox.showerror("Error", "Profile not found")
            return
        
        profile = profiles[profile_name]
        self.version_var.set(profile.get("version", ""))
        self.mod_loader_var.set(profile.get("mod_loader", "vanilla"))
        self.ram_var.set(profile.get("ram", 4096))
        if "username" in profile:
            self.username_var.set(profile["username"])
        self.current_profile = profile_name
        self.settings["current_profile"] = profile_name
        self.save_settings()
        self.notebook.select(0)  # Switch to Play tab
        messagebox.showinfo("Profile Loaded", f"Profile '{profile_name}' loaded successfully!")
    
    def delete_profile(self):
        """Delete selected profile"""
        selected = self.profiles_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to delete")
            return
        
        profile_name = self.profiles_listbox.get(selected[0])
        if messagebox.askyesno("Delete Profile", f"Delete profile '{profile_name}'?"):
            profiles = self.settings.get("profiles", {})
            if profile_name in profiles:
                del profiles[profile_name]
                self.settings["profiles"] = profiles
                self.save_settings()
                self.load_profiles_list()
    
    def export_profile(self):
        """Export selected profile"""
        selected = self.profiles_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to export")
            return
        
        profile_name = self.profiles_listbox.get(selected[0])
        profiles = self.settings.get("profiles", {})
        if profile_name not in profiles:
            messagebox.showerror("Error", "Profile not found")
            return
        
        file_path = filedialog.asksaveasfilename(title="Export Profile", defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump({profile_name: profiles[profile_name]}, f, indent=2)
                messagebox.showinfo("Success", f"Profile exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export profile: {str(e)}")
    
    def import_profile(self):
        """Import profile from file"""
        file_path = filedialog.askopenfilename(title="Import Profile", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                profiles = self.settings.get("profiles", {})
                profiles.update(imported)
                self.settings["profiles"] = profiles
                self.save_settings()
                self.load_profiles_list()
                messagebox.showinfo("Success", "Profile imported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import profile: {str(e)}")
    
    def load_profiles_list(self):
        """Load profiles into listbox"""
        self.profiles_listbox.delete(0, tk.END)
        profiles = self.settings.get("profiles", {})
        for name in sorted(profiles.keys()):
            self.profiles_listbox.insert(tk.END, name)
    
    def update_version_combos(self, version_list):
        """Update version combo boxes with version list"""
        self.version_combo.config(values=version_list)
        self.mod_loader_version_combo.config(values=version_list)
        self.mod_loader_version_var.set("")
        
        # If current selection is not in the list, clear it
        current_val = self.version_var.get()
        if current_val and current_val not in version_list:
            self.version_var.set("")
    
    def update_status(self, text):
        """Update status text"""
        self.status_var.set(text)
        self.log(text)
    
    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_var.set(progress)
        self.root.update_idletasks()
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def export_log(self):
        """Export log to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("Success", f"Log exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export log:\n{str(e)}")
    
    def launch_minecraft(self):
        """Launch Minecraft"""
        version = self.version_var.get().strip()
        
        # Validate version selection
        if not version or version.lower() == "value" or version == "":
            messagebox.showerror("No Version", "Please select a Minecraft version from the dropdown list")
            return
        
        # Check if version is a valid version string (contains numbers)
        if not any(char.isdigit() for char in version):
            messagebox.showerror("Invalid Version", f"Invalid version selected: '{version}'\n\nPlease select a valid Minecraft version.")
            self.log(f"ERROR: Invalid version value: '{version}'")
            return
        
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("No Username", "Please enter a username")
            return
        
        # Save settings before launch
        self.save_settings_ui()
        
        self.status_var.set(f"Launching Minecraft {version}...")
        self.launch_button.config(state=tk.DISABLED)
        self.log(f"Preparing to launch Minecraft {version}...")
        
        def launch():
            try:
                # Check if version is installed
                version_json = os.path.join(self.versions_dir, version, f"{version}.json")
                if not os.path.exists(version_json):
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Version Not Installed", 
                        f"Version {version} is not installed. Please install it first."
                    ))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    return
                
                # Determine which version to launch (might be mod loader version)
                mod_loader = self.mod_loader_var.get()
                launch_version = version
                
                # Check if a mod loader version exists
                if mod_loader != "vanilla":
                    # Look for mod loader version (e.g., fabric-1.20.1, forge-1.20.1)
                    possible_versions = [
                        f"{mod_loader}-{version}",
                        f"{version}-{mod_loader}",
                    ]
                    
                    for poss_version in possible_versions:
                        poss_version_json = os.path.join(self.versions_dir, poss_version, f"{poss_version}.json")
                        if os.path.exists(poss_version_json):
                            launch_version = poss_version
                            self.root.after(0, lambda: self.log(f"Found mod loader version: {launch_version}"))
                            break
                
                # Generate launch options
                options = minecraft_launcher_lib.utils.generate_test_options()
                options["username"] = username
                
                # Add JVM arguments for memory
                ram_mb = self.ram_var.get()
                jvm_args = [
                    f"-Xmx{ram_mb}M",
                    f"-Xms{ram_mb // 2}M"
                ]
                
                # Add custom JVM arguments
                if hasattr(self, 'jvm_text_widget'):
                    custom_args = self.jvm_text_widget.get("1.0", tk.END).strip()
                    if custom_args:
                        jvm_args.extend([arg.strip() for arg in custom_args.split('\n') if arg.strip()])
                elif self.custom_jvm_args:
                    jvm_args.extend([arg.strip() for arg in self.custom_jvm_args.split('\n') if arg.strip()])
                
                options["jvmArguments"] = jvm_args
                
                # Set Java path
                options["executablePath"] = self.java_path_var.get()
                
                # Window settings
                if hasattr(self, 'fullscreen_var') and self.fullscreen_var.get():
                    options["customResolution"] = True
                    options["resolutionWidth"] = str(self.window_width_var.get() if hasattr(self, 'window_width_var') else self.window_width)
                    options["resolutionHeight"] = str(self.window_height_var.get() if hasattr(self, 'window_height_var') else self.window_height)
                elif hasattr(self, 'window_width_var'):
                    options["customResolution"] = True
                    options["resolutionWidth"] = str(self.window_width_var.get())
                    options["resolutionHeight"] = str(self.window_height_var.get())
                
                # Server connection
                server_ip = self.server_ip_var.get().strip() if hasattr(self, 'server_ip_var') else self.server_ip
                server_port = self.server_port_var.get().strip() if hasattr(self, 'server_port_var') else self.server_port
                if server_ip:
                    options["server"] = server_ip
                    if server_port:
                        options["port"] = server_port
                
                # Add to recent versions
                if launch_version not in self.recent_versions:
                    self.recent_versions.append(launch_version)
                else:
                    self.recent_versions.remove(launch_version)
                    self.recent_versions.append(launch_version)  # Move to end
                self.recent_versions = self.recent_versions[-10:]  # Keep last 10
                
                # Get launch command
                self.root.after(0, lambda: self.log(f"Building launch command for version: {launch_version}"))
                self.root.after(0, lambda: self.log(f"Java: {options['executablePath']}"))
                self.root.after(0, lambda: self.log(f"RAM: {ram_mb}MB"))
                
                try:
                    command = minecraft_launcher_lib.command.get_minecraft_command(
                        launch_version, self.minecraft_directory, options
                    )
                    self.root.after(0, lambda: self.log(f"Launch command created successfully"))
                except minecraft_launcher_lib.exceptions.VersionNotFound as e:
                    error_msg = f"Version '{launch_version}' not found.\n\nPlease make sure the version is installed correctly."
                    self.root.after(0, lambda: self.log(f"ERROR: {error_msg}"))
                    self.root.after(0, lambda: self.status_var.set("Version not found"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: messagebox.showerror("Version Not Found", error_msg))
                    return
                except Exception as e:
                    error_msg = f"Failed to create launch command:\n{str(e)}\n\nVersion: {launch_version}"
                    self.root.after(0, lambda: self.log(f"ERROR: {error_msg}"))
                    self.root.after(0, lambda: self.status_var.set("Command creation failed"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: messagebox.showerror("Launch Error", error_msg))
                    return
                
                self.root.after(0, lambda: self.log("Starting Minecraft..."))
                self.root.after(0, lambda: self.status_var.set("Minecraft is starting..."))
                
                # Launch Minecraft
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=self.minecraft_directory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Update statistics
                    stats = self.settings.get("statistics", {})
                    stats["total_launches"] = stats.get("total_launches", 0) + 1
                    stats["last_launch"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if launch_version not in stats.get("version_counts", {}):
                        stats.setdefault("version_counts", {})[launch_version] = 0
                    stats["version_counts"][launch_version] = stats["version_counts"].get(launch_version, 0) + 1
                    # Find most used version
                    if stats.get("version_counts"):
                        stats["most_used_version"] = max(stats["version_counts"], key=stats["version_counts"].get)
                    self.settings["statistics"] = stats
                    self.save_settings()
                    
                    self.root.after(0, lambda: self.log(f"Minecraft launched! (PID: {process.pid})"))
                    self.root.after(0, lambda: self.status_var.set("Minecraft is running"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                except FileNotFoundError:
                    error_msg = f"Java executable not found at: {options['executablePath']}\n\nPlease check your Java installation in Settings."
                    self.root.after(0, lambda: self.log(f"ERROR: {error_msg}"))
                    self.root.after(0, lambda: self.status_var.set("Java not found"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: messagebox.showerror("Java Not Found", error_msg))
                    return
                except Exception as e:
                    error_msg = f"Failed to start Minecraft process:\n{str(e)}"
                    self.root.after(0, lambda: self.log(f"ERROR: {error_msg}"))
                    self.root.after(0, lambda: self.status_var.set("Process start failed"))
                    self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                    self.root.after(0, lambda: messagebox.showerror("Launch Error", error_msg))
                    return
                
            except Exception as e:
                error_msg = f"Unexpected error launching Minecraft:\n{str(e)}\n\nVersion selected: {version}"
                self.root.after(0, lambda: self.log(f"ERROR: {error_msg}"))
                self.root.after(0, lambda: self.status_var.set("Launch failed"))
                self.root.after(0, lambda: self.launch_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: messagebox.showerror("Launch Error", error_msg))
        
        threading.Thread(target=launch, daemon=True).start()


def main():
    root = tk.Tk()
    app = MinecraftLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()

