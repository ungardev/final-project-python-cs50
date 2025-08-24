# YOUR PROJECT TITLE
    #### Video Demo:  <https://youtu.be/7ArvvR9gTZk>
    #### Description: A CLI To-Do Program built in Python
    TODO

# CLI To‑Do ✅

A command‑line task manager built in Python, designed with software engineering best practices, defensive validation, and atomic JSON persistence. Developed as the final project for CS50P – Introduction to Programming with Python.

## Description
CLI To‑Do lets you manage tasks entirely from your terminal. You can add, list, and delete tasks while ensuring data integrity through validation and atomic saving. The project is structured to be easy to maintain and expand.

## Features
- Simple, fast command‑line interface
- Atomic writes to `db.json`
- Defensive input validation
- Typed functions and clear docstrings
- Modular architecture with separation of concerns

## Requirements
- Python 3.10 or higher
- No external dependencies (standard library only)

## Installation
Clone or download this repository, then optionally create and activate a virtual environment:
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows PowerShell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

## Usage
Run commands from the root folder (where project.py is located):

python project.py add "Buy milk"
python project.py list
python project.py delete 1

- add: Adds a task with an auto‑incrementing id
- list: Displays all tasks in ascending order of id
- delete: Removes a task by its id

## Data Model
The db.json file follows this structure:
{
  "next_id": 3,
  "tasks": [
    { "id": 1, "title": "Buy milk", "created_at": "2025-08-15T12:00:00Z" },
    { "id": 2, "title": "Read CS50P notes", "created_at": "2025-08-15T12:05:00Z" }
  ]
}

Atomic saving: data is first written to a temp file, flushed, synced, and then replaces the original file.
Testing
If test_project.py is included:
pytest test_project.py

## Project Structure
cli-todo/
├── project.py
├── README.md
├── db.json
└── test_project.py 


##Author
Created by Ungar for the CS50P final project, focusing on robustness, validation, and atomic persistence for a clean CLI experience.