# DOXA MVP

This is the MVP repository for DOXA. Python dependencies and environments are managed using [Poetry](https://python-poetry.org/).

## Setup & Installation

### Prerequisites

Ensure you have Python 3.12+ and Poetry installed.

### Install Dependencies

To set up the virtual environment and install all dependencies (including `langgraph`):
```bash
poetry install
```

This will automatically create a virtual environment in a local `.venv/` directory.

## Usage

### Running Commands

To run any script or command within the virtual environment:
```bash
poetry run python your_script.py
```

### Activating the Virtual Environment Shell

To spawn a shell within the virtual environment:
```bash
poetry shell
```

### Managing Dependencies

To add a new package:
```bash
poetry add <package-name>
```

To add a dev dependency:
```bash
poetry add --group dev <package-name>
```

To remove a package:
```bash
poetry remove <package-name>
```