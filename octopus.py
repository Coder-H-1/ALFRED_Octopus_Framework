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
    in_function_block = False
    in_command_uses_block = False
    used_function = None
    uses_args = []
    
    python_indent_level = 0
    func_name = ""
    cmd_func_name = ""

    def process_value(val):
        if '$' in val:
            val = re.sub(r'\$([a-zA-Z_]\w*(?:\[.*?\])?)', r'{\1}', val)
            return f'f"{val}"'
        return f'"{val}"'

    for line in lines:
        stripped = line.strip()

        # Ignore comments and empty lines outside of python block
        if not in_python_block and (not stripped or stripped.startswith("//")):
            continue

        if stripped.startswith("module"):
            module_name = stripped.split('"')[1]
            python_code.append(f"# Module: {module_name}\n")
            continue

        if stripped.startswith("function "):
            parts = stripped.split(None, 2)
            if len(parts) >= 2:
                func_name = parts[1].split('(')[0].strip()
                args = ""
                args_match = re.search(r'\((.*?)\)', line)
                if args_match:
                    args = args_match.group(1).strip()
                
                python_code.append(f"def {func_name} ( {args} ):")
                in_function_block = True
            continue

        if stripped.startswith("command") and "uses" in stripped:
            cmd_match = re.search(r'command\s+"(.*?)"\s+uses\s+([a-zA-Z_]\w*)\s*\{', line)
            if cmd_match:
                cmd_trigger = cmd_match.group(1)
                used_function = cmd_match.group(2)
                current_command = cmd_trigger
                safe_name = re.sub(r'\W+', '_', cmd_trigger).strip('_')
                cmd_func_name = f"oct_cmd_{safe_name}"
                python_code.append(f"def {cmd_func_name}(command):")
                python_code.append(f"    if '{cmd_trigger}' in command:")
                in_command_uses_block = True
                uses_args = []
            continue

        if stripped.startswith("command") and "{" in stripped and not in_command_uses_block:
            cmd_trigger = stripped.split('"')[1]
            current_command = cmd_trigger
            safe_name = re.sub(r'\W+', '_', cmd_trigger).strip('_')
            cmd_func_name = f"oct_cmd_{safe_name}"
            python_code.append(f"def {cmd_func_name}(command):")
            python_code.append(f"    if '{cmd_trigger}' in command:")
            continue

        if in_function_block:
            if stripped == "{":
                continue
            if stripped == "}":
                in_function_block = False
                if python_code[-1].startswith("def "):
                    python_code.append("    pass")
                python_code.append("")
                continue
            
            if stripped.startswith("system ") or stripped.startswith("start "):
                val_str = stripped.split(" ", 1)[1].strip().strip('"')
                val = process_value(val_str)
                python_code.append(f"    os.system({val})")
            elif stripped.startswith("print "):
                val_str = stripped.split(" ", 1)[1].strip().strip('"')
                val = process_value(val_str)
                python_code.append(f"    print({val})")
            elif stripped.startswith("response "):
                val_str = stripped.split(" ", 1)[1].strip().strip('"')
                val = process_value(val_str)
                python_code.append(f"    return {val}")
            else:
                leading_spaces = len(line) - len(line.lstrip(' '))
                user_indent = leading_spaces - 8 if leading_spaces >= 8 else 0
                processed_line = line.lstrip().rstrip('\r\n')
                if '$' in processed_line:
                    processed_line = re.sub(r'\$([a-zA-Z_]\w*(?:\[.*?\])?)', r'{\1}', processed_line)
                python_code.append(" " * (4 + user_indent) + processed_line)
            continue

        if in_command_uses_block:
            if stripped == "}":
                in_command_uses_block = False
                args_str = ", ".join(uses_args)
                python_code.append(f"        {used_function}([{args_str}])")
                python_code.append("    return None\n")
                python_code.append(f"DYNAMIC_COMMANDS['{current_command}'] = {cmd_func_name}\n")
                current_command = None
                used_function = None
                uses_args = []
            else:
                arg_match = re.search(r'"(.*)"', line)
                if arg_match:
                    uses_args.append(f'"{arg_match.group(1)}"')
            continue

        if current_command and stripped == "}":
            if in_python_block:
                in_python_block = False
            else:
                # End of command block
                python_code.append("    return None\n")
                python_code.append(f"DYNAMIC_COMMANDS['{current_command}'] = {cmd_func_name}\n")
                current_command = None
            continue

        if current_command and not in_python_block:
            if stripped.startswith("response generate"):
                resp_gen_match = re.search(r'response\s+generate\s*\(\s*"(.*?)"\s*\)', line)
                if resp_gen_match:
                    val = process_value(resp_gen_match.group(1))
                    python_code.append(f"        return Responder({val})")

            elif stripped.startswith("response"):
                # Extract string between quotes properly
                resp_match = re.search(r'response\s+"(.*)"', line)
                if resp_match:
                    val = process_value(resp_match.group(1))
                    python_code.append(f"        return {val}")

            elif stripped.startswith("system"):
                sys_match = re.search(r'system\s+"(.*)"', line)
                if sys_match:
                    val = process_value(sys_match.group(1))
                    python_code.append(f"        os.system({val})")

            elif stripped.startswith("python {"):
                in_python_block = True
                
        elif in_python_block:
            # We preserve indentation but add 8 spaces (4 for func, 4 for if)
            # Remove the first 8 spaces or 2 tabs if present from the user's .oct file
            leading_spaces = len(line) - len(line.lstrip(' '))
            if stripped == "}":
                in_python_block = False
                continue
                
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
    path = os.path.join(os.path.dirname(__file__), "oct", name)
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
    oct_path = os.path.join(os.path.dirname(__file__), "oct", name)
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
                     filepath = os.path.join(os.path.dirname(__file__), "oct", filepath)
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
