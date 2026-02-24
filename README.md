# Local Automation GUI (Python)

A simple Tkinter desktop GUI that records mouse + keyboard actions (including delays) and then replays them locally.

## Features

- Record:
  - Mouse move
  - Mouse click (press/release)
  - Mouse scroll
  - Keyboard press/release
- Stores recorded events with timing delays in a table
- Replay events in the same order with original delays
- Clear recording

## Requirements

- Python 3.10+
- `pynput`

Install dependency:

```bash
pip install pynput
```

## Run

```bash
python local_automation_gui.py
```

## Usage

1. Click **Start Recording**.
2. Perform mouse/keyboard actions.
3. Click **Stop Recording**.
4. Click **Play** to replay actions with captured delays.

> ⚠️ Playback controls your actual local mouse and keyboard.
