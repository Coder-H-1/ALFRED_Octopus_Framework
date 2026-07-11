<p align="center">
  <img src="assets/logo.png" width="200" alt="Octopus Framework Logo">
</p>

# ALFRED's Octopus Framework

> **The ultimate command-driven extension system for ALFRED.**

Octopus Framework is a powerful, flexible, and lightweight framework designed to add custom functionality and commands to the ALFRED ecosystem. By using a custom Domain Specific Language (DSL) with the `.oct` extension, developers can rapidly prototype and deploy new features without modifying the core system logic.

---

## 🚀 Key Features

- **🎯 Custom DSL**: Intuitive syntax for defining modules and commands.
- **🐍 Python Integration**: Embed native Python logic directly within command blocks for complex operations.
- **🤖 LLM-Powered Responses**: Generate dynamic, human-like responses using ALFRED's integrated Large Language Model.
- **🖥️ Dual Interface**: Manage your framework via a robust **CLI** or a modern **Visual IDE (GUI)**.
- **⚡ Hot Reloading**: Plugins are compiled and injected into the main program in real-time.
- **📦 Plugin Management**: Easy toggling between enabled and disabled plugin states.

---

## 📂 Project Structure

| Directory / File | Description |
| :--- | :--- |
| `octopus.py` | Core compiler, CLI, and socket communication bridge. |
| `octopus_gui.py` | PyWebView-based Visual IDE for the framework. |
| `compiled_plugins/` | Compiled `.py` files injected into the main program. |
| `disabled_plugins/` | Inactive plugins stored for future use. |
| `gui/` | Frontend assets for the Octopus IDE. |
| `assets/` | Documentation assets like logos and diagrams. |
| `*.oct` | Source files for your custom commands. |

---

## 🛠️ Installation & Setup

1. **Prerequisites**: Ensure you have Python 3.x installed.
2. **Dependencies**: Install the required packages for the GUI (optional for CLI):
    ```bash
    pip install pywebview
    ```
3. **Running the Framework**:
    1. Launch the IDE (GUI) by running the main script without arguments:
        ```bash
        python octopus.py
        ```
    2. Running Framework without opening GUI 
        ```bash
        python octopus.py command <value(if-any)>
        ```
        Available commands:
            'add <name>' <= Starts the plugin,
            'delete <name>' <= Deletes the plugin,
            'load <filename.oct>' <= Loads the plugin,
            'status' <= Shows the status,
            'exit' <= Exits the program
---

## 🎮 Usage Guide

### Using the Visual IDE (GUI)
The **Octopus Framework IDE** provides a full-featured code editor and plugin manager.
- **Edit**: Write your `.oct` files with syntax highlighting.
- **Compile**: Use the "Compile" button to instantly transform `.oct` into `.py`.
- **Manage**: Toggle plugins on/off with a single click.

### Using the CLI
For power users, the framework offers a direct command-line interface:
- **Add a template**: `python octopus.py add <name>`
- **Delete a function**: `python octopus.py delete <name>`
- **Compile & Load**: `python octopus.py load <filename.oct>`
- **Check Status**: `python octopus.py status`

---

## 📝 `.oct` Syntax Reference

The Octopus Framework uses a clean, block-based syntax.

### 1. Module Definition
Every file should start with a module name.
```oct
module "MyNewFeature"
```

### 2. Basic Command & Response
Triggers a static response when the keyword is found in the user input.
```oct
command "hello world" {
    response "Greetings, User! Octopus is active."
}
```

### 3. System Execution
Run local shell commands directly.
```oct
command "launch browser" {
    system "start chrome"
    response "Opening Chrome now."
}
```

### 4. Dynamic LLM Response
Generate a response using ALFRED's internal LLM.
```oct
command "tell me a joke" {
    response generate ( "A short funny joke about octopuses" )
}
```

### 5. Advanced Python Blocks
The `command` variable (full user string) is automatically passed to the scope.
```oct
command "calculate square" {
    python {
        import re
        val = int(re.search(r'\d+', command).group())
        return f"The result is {val * val}"
    }
}
```

---

## 💡 Developer Information

### Compilation Process
The framework parses `.oct` files and generates a Python payload. This payload is then:
1.  Saved as a `.py` file in `compiled_plugins/`.
2.  Sent via a local socket (Port `65432`) to the "Main program" for live injection.

### Socket Communication
- **Host**: `127.0.0.1`
- **Port**: `65432`
- **Message Format**: Raw UTF-8 string containing the Python payload or `STATUS_CHECK` signal.

---

<p align="center">
  A.L.F.R.E.D.
</p>