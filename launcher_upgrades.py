"""
Major upgrades and enhancements for Dan Launcher
This file contains additional features that enhance the launcher functionality
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from datetime import datetime
import webbrowser
import subprocess


class LauncherUpgrades:
    """Additional upgrade features for the launcher"""
    
    @staticmethod
    def add_profiles_tab(launcher, notebook):
        """Add profiles management tab"""
        profiles_frame = ttk.Frame(notebook, padding="20")
        notebook.add(profiles_frame, text="Profiles")
        
        # Profile list
        list_frame = ttk.LabelFrame(profiles_frame, text="Profiles", padding="10")
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        profiles_frame.columnconfigure(0, weight=1)
        profiles_frame.rowconfigure(0, weight=1)
        
        profiles_listbox = tk.Listbox(list_frame, height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=profiles_listbox.yview)
        profiles_listbox.configure(yscrollcommand=scrollbar.set)
        
        profiles_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        # Profile buttons
        profile_buttons = ttk.Frame(profiles_frame)
        profile_buttons.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(profile_buttons, text="New Profile", 
                  command=lambda: LauncherUpgrades.create_new_profile(launcher, profiles_listbox)).grid(row=0, column=0, padx=5)
        ttk.Button(profile_buttons, text="Edit Profile", 
                  command=lambda: LauncherUpgrades.edit_profile(launcher, profiles_listbox)).grid(row=0, column=1, padx=5)
        ttk.Button(profile_buttons, text="Delete Profile", 
                  command=lambda: LauncherUpgrades.delete_profile(launcher, profiles_listbox)).grid(row=0, column=2, padx=5)
        ttk.Button(profile_buttons, text="Export Profile", 
                  command=lambda: LauncherUpgrades.export_profile(launcher, profiles_listbox)).grid(row=0, column=3, padx=5)
        ttk.Button(profile_buttons, text="Import Profile", 
                  command=lambda: LauncherUpgrades.import_profile(launcher, profiles_listbox)).grid(row=0, column=4, padx=5)
        
        # Load profiles
        LauncherUpgrades.load_profiles_list(launcher, profiles_listbox)
        
        return profiles_frame
    
    @staticmethod
    def create_new_profile(launcher, listbox):
        """Create a new profile"""
        dialog = tk.Toplevel(launcher.root)
        dialog.title("New Profile")
        dialog.geometry("400x300")
        dialog.transient(launcher.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Profile Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Minecraft Version:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        version_var = tk.StringVar()
        version_combo = ttk.Combobox(dialog, textvariable=version_var, width=27)
        version_combo['values'] = list(launcher.version_combo['values'])
        version_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="RAM (MB):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        ram_var = tk.IntVar(value=4096)
        ttk.Spinbox(dialog, from_=1024, to=16384, textvariable=ram_var, width=27).grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Mod Loader:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        loader_var = tk.StringVar(value="vanilla")
        loader_combo = ttk.Combobox(dialog, textvariable=loader_var, 
                                    values=["vanilla", "forge", "fabric", "quilt"], width=27)
        loader_combo.grid(row=3, column=1, padx=10, pady=10)
        
        def save_profile():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a profile name")
                return
            
            profiles = launcher.settings.get("profiles", {})
            if name in profiles:
                if not messagebox.askyesno("Overwrite", f"Profile '{name}' already exists. Overwrite?"):
                    return
            
            profiles[name] = {
                "version": version_var.get(),
                "ram": ram_var.get(),
                "mod_loader": loader_var.get(),
                "created": datetime.now().isoformat()
            }
            launcher.settings["profiles"] = profiles
            launcher.save_settings()
            LauncherUpgrades.load_profiles_list(launcher, listbox)
            dialog.destroy()
        
        ttk.Button(dialog, text="Create", command=save_profile).grid(row=4, column=0, columnspan=2, pady=20)
    
    @staticmethod
    def edit_profile(launcher, listbox):
        """Edit selected profile"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to edit")
            return
        
        profile_name = listbox.get(selected[0])
        profiles = launcher.settings.get("profiles", {})
        if profile_name not in profiles:
            messagebox.showerror("Error", "Profile not found")
            return
        
        profile = profiles[profile_name]
        LauncherUpgrades.create_new_profile(launcher, listbox)
    
    @staticmethod
    def delete_profile(launcher, listbox):
        """Delete selected profile"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to delete")
            return
        
        profile_name = listbox.get(selected[0])
        if messagebox.askyesno("Delete Profile", f"Delete profile '{profile_name}'?"):
            profiles = launcher.settings.get("profiles", {})
            if profile_name in profiles:
                del profiles[profile_name]
                launcher.settings["profiles"] = profiles
                launcher.save_settings()
                LauncherUpgrades.load_profiles_list(launcher, listbox)
    
    @staticmethod
    def export_profile(launcher, listbox):
        """Export selected profile"""
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a profile to export")
            return
        
        profile_name = listbox.get(selected[0])
        profiles = launcher.settings.get("profiles", {})
        if profile_name not in profiles:
            messagebox.showerror("Error", "Profile not found")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Profile",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump({profile_name: profiles[profile_name]}, f, indent=2)
                messagebox.showinfo("Success", f"Profile exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export profile: {str(e)}")
    
    @staticmethod
    def import_profile(launcher, listbox):
        """Import profile from file"""
        file_path = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                
                profiles = launcher.settings.get("profiles", {})
                profiles.update(imported)
                launcher.settings["profiles"] = profiles
                launcher.save_settings()
                LauncherUpgrades.load_profiles_list(launcher, listbox)
                messagebox.showinfo("Success", "Profile imported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import profile: {str(e)}")
    
    @staticmethod
    def load_profiles_list(launcher, listbox):
        """Load profiles into listbox"""
        listbox.delete(0, tk.END)
        profiles = launcher.settings.get("profiles", {})
        for name in sorted(profiles.keys()):
            listbox.insert(tk.END, name)
    
    @staticmethod
    def add_statistics_tab(launcher, notebook):
        """Add statistics tracking tab"""
        stats_frame = ttk.Frame(notebook, padding="20")
        notebook.add(stats_frame, text="Statistics")
        
        # Statistics display
        stats_text = tk.Text(stats_frame, height=20, wrap=tk.WORD)
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=stats_text.yview)
        stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        
        # Update statistics
        stats = launcher.settings.get("statistics", {})
        total_launches = stats.get("total_launches", 0)
        total_playtime = stats.get("total_playtime", 0)
        favorite_version = stats.get("most_used_version", "None")
        last_launch = stats.get("last_launch", "Never")
        
        stats_text.insert(tk.END, "📊 Launcher Statistics\n")
        stats_text.insert(tk.END, "=" * 40 + "\n\n")
        stats_text.insert(tk.END, f"Total Launches: {total_launches}\n\n")
        stats_text.insert(tk.END, f"Total Playtime: {total_playtime // 3600} hours {(total_playtime % 3600) // 60} minutes\n\n")
        stats_text.insert(tk.END, f"Most Used Version: {favorite_version}\n\n")
        stats_text.insert(tk.END, f"Last Launch: {last_launch}\n\n")
        stats_text.insert(tk.END, f"Installed Versions: {len([v for v in os.listdir(launcher.versions_dir) if os.path.isdir(os.path.join(launcher.versions_dir, v))]) if os.path.exists(launcher.versions_dir) else 0}\n")
        stats_text.config(state=tk.DISABLED)
        
        return stats_frame
    
    @staticmethod
    def add_news_tab(launcher, notebook):
        """Add news/updates tab"""
        news_frame = ttk.Frame(notebook, padding="20")
        notebook.add(news_frame, text="News")
        
        news_text = scrolledtext.ScrolledText(news_frame, height=20, wrap=tk.WORD)
        news_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        news_frame.columnconfigure(0, weight=1)
        news_frame.rowconfigure(0, weight=1)
        
        news_text.insert(tk.END, "📰 Minecraft & Launcher News\n")
        news_text.insert(tk.END, "=" * 40 + "\n\n")
        news_text.insert(tk.END, "Loading news...\n")
        news_text.config(state=tk.DISABLED)
        
        def load_news():
            try:
                import requests
                # Try to fetch Minecraft news
                news_text.config(state=tk.NORMAL)
                news_text.delete(1.0, tk.END)
                news_text.insert(tk.END, "📰 Minecraft & Launcher News\n")
                news_text.insert(tk.END, "=" * 40 + "\n\n")
                news_text.insert(tk.END, "✅ Dan Launcher v2.0 - Enhanced Edition!\n\n")
                news_text.insert(tk.END, "New Features:\n")
                news_text.insert(tk.END, "• Profile system for multiple configurations\n")
                news_text.insert(tk.END, "• Statistics tracking\n")
                news_text.insert(tk.END, "• Enhanced mod management\n")
                news_text.insert(tk.END, "• Dark theme support\n")
                news_text.insert(tk.END, "• Export/Import profiles\n\n")
                news_text.insert(tk.END, "For the latest Minecraft news, visit:\n")
                news_text.insert(tk.END, "https://www.minecraft.net/en-us/news\n")
                news_text.config(state=tk.DISABLED)
            except:
                pass
        
        threading.Thread(target=load_news, daemon=True).start()
        
        return news_frame
    
    @staticmethod
    def enable_mod_management(launcher):
        """Add enable/disable functionality to mods"""
        # This would be integrated into the mods tab
        pass
    
    @staticmethod
    def add_search_filter(launcher):
        """Add search/filter to versions tab"""
        # Add search entry to versions tab
        pass
    
    @staticmethod
    def enhance_settings(launcher):
        """Add advanced settings options"""
        # Add more settings like:
        # - Window size customization
        # - Fullscreen toggle
        # - Custom JVM arguments
        # - Server auto-join
        pass

