import os
import webview
import subprocess
import json

class OctopusAPI:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.oct_dir = os.path.join(self.base_dir, "oct")
        self.plugins_dir = os.path.join(self.base_dir, "compiled_plugins")
        self.disabled_dir = os.path.join(self.base_dir, "disabled_plugins")
        os.makedirs(self.oct_dir, exist_ok=True)
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.disabled_dir, exist_ok=True)

    def list_functions(self):
        """Lists .oct files in the current directory."""
        files = [f for f in os.listdir(self.oct_dir) if f.endswith(".oct")]
        return [{"name": f, "path": os.path.join(self.oct_dir, f).replace('\\', '/')} for f in files]

    def list_plugins(self):
        """Lists .py files in compiled_plugins (enabled) and disabled_plugins."""
        enabled = [f for f in os.listdir(self.plugins_dir) if f.endswith(".py")]
        disabled = [f for f in os.listdir(self.disabled_dir) if f.endswith(".py")]
        
        plugins = []
        for f in enabled:
            plugins.append({"name": f, "path": os.path.join(self.plugins_dir, f).replace('\\', '/'), "enabled": True})
        for f in disabled:
            plugins.append({"name": f, "path": os.path.join(self.disabled_dir, f).replace('\\', '/'), "enabled": False})
        return plugins

    def read_file(self, path):
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.base_dir, path)
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def save_file(self, path, content):
        try:
            with open(path, "w") as f:
                f.write(content)
            return f"Saved {os.path.basename(path)} successfully."
        except Exception as e:
            return f"Error saving file: {e}"

    def compile_file(self, path):
        """Runs: python octopus.py load <path>"""
        try:
            filename = os.path.basename(path)
            proc = subprocess.run(
                ["python", "octopus.py", "load", filename],
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            return proc.stdout + proc.stderr
        except Exception as e:
            return f"Compilation Error: {e}"

    def toggle_plugin(self, name, target_state):
        """Moves file between compiled_plugins and disabled_plugins."""
        src_dir = self.disabled_dir if target_state else self.plugins_dir
        dst_dir = self.plugins_dir if target_state else self.disabled_dir
        
        src_path = os.path.join(src_dir, name)
        dst_path = os.path.join(dst_dir, name)
        
        if os.path.exists(src_path):
            os.rename(src_path, dst_path)
            status = "enabled" if target_state else "disabled"
            return f"Plugin '{name}' is now {status}."
        return f"Error: Could not find plugin '{name}'."

    def run_cli(self, command):
        """Runs a raw octopus CLI command."""
        try:
            args = command.split(" ")
            proc = subprocess.run(
                ["python", "octopus.py"] + args,
                cwd=self.base_dir,
                capture_output=True,
                text=True
            )
            return proc.stdout + proc.stderr
        except Exception as e:
            return f"CLI Error: {e}"

def main():
    api = OctopusAPI()
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
    index_path = os.path.join(gui_dir, "index.html")
    
    window = webview.create_window(
        'Octopus Framework IDE', 
        index_path, 
        js_api=api,
        width=1200,
        height=800,
        background_color='#131313'
    )
    webview.start()

if __name__ == '__main__':
    main()
