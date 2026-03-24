import os
import sys
import socket
import re
import subprocess

PORT = 65432
HOST = '127.0.0.1'

def compile_oct_file(filepath: str) -> str:
    """Parses a .oct file and converts it into a Python payload string."""
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return ""

    with open(filepath, "r") as f:
        lines = f.readlines()

    python_code = [
        "import os",
        "import re",
        "try:",
        "    from FILES.utils import Responder",
        "except Exception:",
        "    pass\n"
    ]

    current_command = None
    in_python_block = False
    python_indent_level = 0
    func_name = ""

    for line in lines:
        stripped = line.strip()

        # Ignore comments and empty lines outside of python block
        if not in_python_block and (not stripped or stripped.startswith("//")):
            continue

        if stripped.startswith("module"):
            module_name = stripped.split('"')[1]
            python_code.append(f"# Module: {module_name}\n")
            continue

        if stripped.startswith("command") and "{" in stripped:
            cmd_trigger = stripped.split('"')[1]
            current_command = cmd_trigger
            # safe function name
            safe_name = re.sub(r'\W+', '_', cmd_trigger).strip('_')
            func_name = f"oct_cmd_{safe_name}"
            python_code.append(f"def {func_name}(command):")
            python_code.append(f"    if '{cmd_trigger}' in command:")
            continue

        if current_command and stripped == "}":
            if in_python_block:
                in_python_block = False
            else:
                # End of command block
                python_code.append("    return None\n")
                python_code.append(f"DYNAMIC_COMMANDS['{current_command}'] = {func_name}\n")
                current_command = None
            continue

        if current_command and not in_python_block:
            if stripped.startswith("response generate"):
                resp_gen_match = re.search(r'response\s+generate\s*\(\s*"(.*?)"\s*\)', line)
                if resp_gen_match:
                    python_code.append(f"        return Responder(\"{resp_gen_match.group(1)}\")")

            elif stripped.startswith("response"):
                # Extract string between quotes properly
                resp_match = re.search(r'response\s+"(.*)"', line)
                if resp_match:
                    python_code.append(f"        return \"{resp_match.group(1)}\"")

            elif stripped.startswith("system"):
                sys_match = re.search(r'system\s+"(.*)"', line)
                if sys_match:
                    python_code.append(f"        os.system(\"{sys_match.group(1)}\")")

            elif stripped.startswith("python {"):
                in_python_block = True
                
        elif in_python_block:
            # We preserve indentation but add 8 spaces (4 for func, 4 for if)
            # Remove the first 8 spaces or 2 tabs if present from the user's .oct file
            # Wait, best is to just take the line, strip it, and apply 8 spaces base + whatever internal indentation.
            # Let's count leading spaces of the original line.
            leading_spaces = len(line) - len(line.lstrip(' '))
            # Adjust indentation (assuming 4 spaces inside python { block )
            # We'll just prefix with 8 spaces and append the lstrip() line, but we need to keep python block indents
            # Example: "        return val"
            if stripped == "}":
                in_python_block = False
                continue
                
            # Naive indent handling: if leading_spaces > 8 in .oct, we keep the relative diff
            # Actually just prepend 8 spaces to whatever they wrote, minus their base indent.
            base_indent = 8 # spaces we inject
            user_indent = leading_spaces - 8 if leading_spaces >= 8 else 0
            python_code.append(" " * (8 + user_indent) + line.lstrip())

    return "\n".join(python_code)

def send_payload(payload: str):
    """Sends the compiled payload to the Main program."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(payload.encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            print(f"Main Program Response:\n{response}")
    except ConnectionRefusedError:
        print("Error: Could not connect to Main program. Is it running?")
        
def status_check():
    """Pings the Main program for status."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall("STATUS_CHECK".encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            print(f"Status:\n{response}")
    except ConnectionRefusedError:
        print("Main program offline or plugin listener not running.")

def save_compiled(filename: str, payload: str):
    """Saves the compiled Python payload to the compiled_plugins directory."""
    save_dir = os.path.join(os.path.dirname(__file__), "compiled_plugins")
    os.makedirs(save_dir, exist_ok=True)
    base_name = os.path.basename(filename).replace(".oct", ".py")
    save_path = os.path.join(save_dir, base_name)
    with open(save_path, "w") as f:
        f.write(payload)
    print(f"Compiled plugin natively saved to: {save_path}")

def add_function(name: str):
    """Creates a new .oct file template."""
    if not name.endswith(".oct"):
        name += ".oct"
    path = os.path.join(os.path.dirname(__file__), name)
    if os.path.exists(path):
        print(f"Error: {name} already exists.")
        return
    template = f'module "{name.replace(".oct","")}"\n\ncommand "hello {name.replace(".oct","")}" {{\n    response "Hello from {name}"\n}}\n'
    with open(path, "w") as f:
        f.write(template)
    print(f"Successfully created function: {name}")

def delete_function(name: str):
    """Deletes a .oct file and its compiled plugin."""
    if not name.endswith(".oct"):
        name += ".oct"
    oct_path = os.path.join(os.path.dirname(__file__), name)
    py_path = os.path.join(os.path.dirname(__file__), "compiled_plugins", name.replace(".oct", ".py"))
    
    deleted = False
    if os.path.exists(oct_path):
        os.remove(oct_path)
        print(f"Deleted source: {oct_path}")
        deleted = True
    if os.path.exists(py_path):
        os.remove(py_path)
        print(f"Deleted compiled: {py_path}")
        deleted = True
    
    if not deleted:
        print(f"Error: Could not find function '{name}' to delete.")

def main():
    if len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])
        # ... logic for CLI ...
        if cmd == "status":
            status_check()
        elif cmd.startswith("add "):
            add_function(cmd.split(" ", 1)[1])
        elif cmd.startswith("delete "):
            delete_function(cmd.split(" ", 1)[1])
        elif cmd.startswith("load "):
            parts = cmd.split(" ", 1)
            if len(parts) > 1:
                filepath = parts[1]
                if "\\" not in filepath and "/" not in filepath:
                     filepath = os.path.join(os.path.dirname(__file__), filepath)
                print(f"Compiling {filepath}...")
                payload = compile_oct_file(filepath)
                if payload:
                    print("Compilation successful. Injecting...")
                    save_compiled(filepath, payload)
                    send_payload(payload)
            else:
                print("Missing filename to load.")
        return

    # If no arguments, launch GUI
    try:
        from octopus_gui import main as launch_gui
        launch_gui()
    except ImportError:
        print("Welcome to Octopus Framework CLI (GUI dependencies missing)")
        print("Commands: 'add <name>', 'delete <name>', 'load <filename.oct>', 'status', 'exit'")
        
        while True:
            # ... CLI loop ...
            try:
                cmd = input("octopus> ").strip()
                if not cmd or cmd == "exit": break
                elif cmd == "status": status_check()
                elif cmd.startswith("add "): add_function(cmd.split(" ", 1)[1])
                elif cmd.startswith("delete "): delete_function(cmd.split(" ", 1)[1])
                elif cmd.startswith("load "):
                    filepath = cmd.split(" ", 1)[1]
                    if "\\" not in filepath and "/" not in filepath:
                        filepath = os.path.join(os.path.dirname(__file__), filepath)
                    payload = compile_oct_file(filepath)
                    if payload:
                        save_compiled(filepath, payload)
                        send_payload(payload)
                else: print("Unknown command.")
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    main()
