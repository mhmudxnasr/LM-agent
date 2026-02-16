# LM‑Agent: Local Code Assistant

> A lightweight, Windows‑native tool that lets you run Python scripts, edit files, and execute shell commands directly from a chat interface.

## Features
- **File Operations** – Read, write, edit, delete, move, copy, and list files or directories.
- **Command Execution** – Run PowerShell or batch commands with real‑time output.
- **Python Integration** – Execute arbitrary Python snippets and capture the result.
- **Safety Prompts** – Destructive actions (delete/overwrite) ask for confirmation before proceeding.
- **Cross‑Platform Compatibility** – Works on any Windows machine with PowerShell available.

## Getting Started
```bash
# Clone the repository
git clone https://github.com/yourusername/lm-agent.git
cd lm-agent
```

### Running the Agent
The agent is a Python script that starts an interactive console.  Run it with:
```bash
python main.py
```
You’ll be greeted with a prompt where you can type commands like `read_file`, `write_file`, etc.

## Usage Examples
- **Read a file**
  ```bash
  read_file path=E:\Visuals\lm-agent\example.txt
  ```
- **Write to a file**
  ```bash
  write_file path=E:\Visuals\lm-agent\output.txt content="Hello, world!"
  ```
- **Run a PowerShell command**
  ```bash
  run_command command="Get-Process | Select-Object -First 5"
  ```
- **Execute Python code**
  ```bash
  run_python code='print("Python is running")'
  ```

## Contributing
Feel free to fork the repo, create a feature branch, and submit a pull request.  Please follow PEP‑8 for Python files and keep the README up‑to‑date.

## License
MIT © Your Name
