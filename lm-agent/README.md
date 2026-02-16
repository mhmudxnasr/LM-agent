# LM Agent

Local CLI coding agent for LM Studio using the OpenAI-compatible `/v1/chat/completions` API.

## What It Does

- Runs an interactive terminal chat loop.
- Supports model tool/function calling.
- Executes local tools for file operations.
- Executes local tools for shell commands.
- Executes local tools for code search and project inspection.
- Prompts before destructive actions (unless `--yolo` is enabled).
- Streams model output while generating.

## Project Structure

```text
lm-agent/
|-- agent.py                  # Backward-compatible launcher
|-- start.cmd                 # Windows launcher
|-- requirements.txt
|-- lm_agent/
|   |-- __init__.py
|   |-- agent.py              # Main runtime
|   |-- cli.py                # python -m lm_agent.cli entrypoint
|   |-- config.py
|   |-- config.yaml
|   |-- llm_client.py
|   |-- safety.py
|   |-- ui.py
|   `-- core/
|       |-- __init__.py       # Tool registry + tool schemas
|       |-- filesystem.py
|       |-- shell.py
|       `-- code.py
`-- tests/
```

## Requirements

- Python 3.11+
- LM Studio running locally with at least one loaded model
- Windows PowerShell available on PATH

## Install

```powershell
cd E:\Visuals\lm-agent
python -m pip install -r requirements.txt
```

## Run

```powershell
start.cmd
```

or:

```powershell
python agent.py
```

or:

```powershell
python -m lm_agent.cli
```

## Useful Flags

- `--health`: verify LM Studio connectivity and list models
- `--url http://localhost:1234/v1`: override API URL
- `--model <model-id>`: pick a specific model
- `--cwd <path>`: set tool working directory
- `--yolo`: disable destructive-action confirmations
- `--command-timeout <seconds>`: tool command timeout

Examples:

```powershell
python agent.py --health
python agent.py --model openai/gpt-oss-20b --cwd E:\Visuals
python agent.py --yolo --cwd E:\Visuals\lm-agent
```

## Testing

```powershell
python -m pytest tests
```

## Safety

- Destructive tools (`write_file`, `edit_file`, `delete_file`, `move_file`, `run_command`, `run_python`) require confirmation by default.
- A blocked-command filter prevents high-risk patterns such as disk formatting and recursive forced deletion commands.
