import threading
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Any, Optional

from pynput import keyboard, mouse


@dataclass
class RecordedEvent:
    delay: float
    event_type: str
    data: dict[str, Any]

    def describe(self) -> str:
        detail = ""
        if self.event_type == "mouse_move":
            detail = f"x={self.data['x']}, y={self.data['y']}"
        elif self.event_type == "mouse_click":
            detail = (
                f"x={self.data['x']}, y={self.data['y']}, "
                f"button={self.data['button']}, pressed={self.data['pressed']}"
            )
        elif self.event_type == "mouse_scroll":
            detail = (
                f"x={self.data['x']}, y={self.data['y']}, "
                f"dx={self.data['dx']}, dy={self.data['dy']}"
            )
        elif self.event_type == "key_press":
            detail = f"key={self.data['key']}"
        elif self.event_type == "key_release":
            detail = f"key={self.data['key']}"
        return f"[{self.delay:0.3f}s] {self.event_type} ({detail})"


class AutomationRecorderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Local Automation Recorder")
        self.root.geometry("900x520")

        self.recorded_events: list[RecordedEvent] = []
        self.is_recording = False
        self.is_playing = False

        self._last_timestamp: Optional[float] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None

        self._mouse_controller = mouse.Controller()
        self._keyboard_controller = keyboard.Controller()

        self._build_ui()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text="Python Local Automation (Record + Playback)",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor=tk.W, pady=(0, 8))

        controls = ttk.Frame(container)
        controls.pack(fill=tk.X, pady=(0, 8))

        self.start_btn = ttk.Button(controls, text="Start Recording", command=self.start_recording)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(controls, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.play_btn = ttk.Button(controls, text="Play", command=self.play_recording)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.clear_btn = ttk.Button(controls, text="Clear", command=self.clear_recording)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.status_var = tk.StringVar(value="Idle")
        status = ttk.Label(controls, textvariable=self.status_var, foreground="#0f4c81")
        status.pack(side=tk.LEFT, padx=(16, 0))

        self.event_count_var = tk.StringVar(value="Events: 0")
        event_count_label = ttk.Label(controls, textvariable=self.event_count_var)
        event_count_label.pack(side=tk.RIGHT)

        columns = ("idx", "delay", "type", "details")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=19)
        self.tree.heading("idx", text="#")
        self.tree.heading("delay", text="Delay (s)")
        self.tree.heading("type", text="Event Type")
        self.tree.heading("details", text="Details")

        self.tree.column("idx", width=52, anchor=tk.CENTER)
        self.tree.column("delay", width=90, anchor=tk.E)
        self.tree.column("type", width=130, anchor=tk.W)
        self.tree.column("details", width=580, anchor=tk.W)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        footer = ttk.Label(
            self.root,
            text=(
                "Tip: Start recording, perform your actions, stop, then click Play. "
                "The same delays are preserved for local automation playback."
            ),
            padding=(12, 0, 12, 12),
        )
        footer.pack(anchor=tk.W)

    def _record_event(self, event_type: str, **data: Any) -> None:
        if not self.is_recording:
            return
        now = time.monotonic()
        delay = 0.0 if self._last_timestamp is None else max(0.0, now - self._last_timestamp)
        self._last_timestamp = now

        event = RecordedEvent(delay=delay, event_type=event_type, data=data)
        self.recorded_events.append(event)
        self.root.after(0, self._append_event_to_tree, event)

    def _append_event_to_tree(self, event: RecordedEvent) -> None:
        index = len(self.recorded_events)
        details = event.describe().split("(", 1)[-1].rstrip(")")
        self.tree.insert(
            "",
            tk.END,
            values=(index, f"{event.delay:0.3f}", event.event_type, details),
        )
        self.event_count_var.set(f"Events: {len(self.recorded_events)}")

    def _on_move(self, x: int, y: int) -> None:
        self._record_event("mouse_move", x=x, y=y)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        self._record_event("mouse_click", x=x, y=y, button=str(button), pressed=pressed)

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self._record_event("mouse_scroll", x=x, y=y, dx=dx, dy=dy)

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._record_event("key_press", key=self._serialize_key(key))

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        self._record_event("key_release", key=self._serialize_key(key))

    @staticmethod
    def _serialize_key(key: keyboard.Key | keyboard.KeyCode) -> str:
        if isinstance(key, keyboard.KeyCode):
            return key.char if key.char is not None else str(key)
        return str(key)

    @staticmethod
    def _deserialize_key(value: str) -> keyboard.Key | str:
        if value.startswith("Key."):
            key_name = value.split(".", 1)[1]
            if hasattr(keyboard.Key, key_name):
                return getattr(keyboard.Key, key_name)
        return value

    def start_recording(self) -> None:
        if self.is_recording:
            return
        if self.is_playing:
            messagebox.showwarning("Playback in progress", "Stop playback before recording again.")
            return

        self.is_recording = True
        self._last_timestamp = None
        self.status_var.set("Recording...")
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.play_btn.configure(state=tk.DISABLED)

        self._mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop_recording(self) -> None:
        if not self.is_recording:
            return
        self.is_recording = False
        self.status_var.set("Idle")
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.play_btn.configure(state=tk.NORMAL)

        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def clear_recording(self) -> None:
        if self.is_recording or self.is_playing:
            messagebox.showwarning("Busy", "Stop recording/playback before clearing events.")
            return
        self.recorded_events.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.event_count_var.set("Events: 0")
        self.status_var.set("Idle")

    def play_recording(self) -> None:
        if self.is_recording:
            messagebox.showwarning("Still recording", "Stop recording before playback.")
            return
        if self.is_playing:
            return
        if not self.recorded_events:
            messagebox.showinfo("Nothing to play", "Record some events first.")
            return

        self.is_playing = True
        self.status_var.set("Playing...")
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.DISABLED)
        self.play_btn.configure(state=tk.DISABLED)
        self.clear_btn.configure(state=tk.DISABLED)

        thread = threading.Thread(target=self._playback_worker, daemon=True)
        thread.start()

    def _playback_worker(self) -> None:
        try:
            for event in self.recorded_events:
                if event.delay > 0:
                    time.sleep(event.delay)
                self._execute_event(event)
        finally:
            self.root.after(0, self._finish_playback)

    def _execute_event(self, event: RecordedEvent) -> None:
        if event.event_type == "mouse_move":
            self._mouse_controller.position = (event.data["x"], event.data["y"])
        elif event.event_type == "mouse_click":
            btn = self._parse_mouse_button(event.data["button"])
            self._mouse_controller.position = (event.data["x"], event.data["y"])
            if event.data["pressed"]:
                self._mouse_controller.press(btn)
            else:
                self._mouse_controller.release(btn)
        elif event.event_type == "mouse_scroll":
            self._mouse_controller.position = (event.data["x"], event.data["y"])
            self._mouse_controller.scroll(event.data["dx"], event.data["dy"])
        elif event.event_type == "key_press":
            key = self._deserialize_key(event.data["key"])
            self._keyboard_controller.press(key)
        elif event.event_type == "key_release":
            key = self._deserialize_key(event.data["key"])
            self._keyboard_controller.release(key)

    @staticmethod
    def _parse_mouse_button(button_value: str) -> mouse.Button:
        if button_value.endswith(".left"):
            return mouse.Button.left
        if button_value.endswith(".right"):
            return mouse.Button.right
        if button_value.endswith(".middle"):
            return mouse.Button.middle
        return mouse.Button.left

    def _finish_playback(self) -> None:
        self.is_playing = False
        self.status_var.set("Idle")
        self.start_btn.configure(state=tk.NORMAL)
        self.play_btn.configure(state=tk.NORMAL)
        self.clear_btn.configure(state=tk.NORMAL)


def main() -> None:
    root = tk.Tk()
    app = AutomationRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_recording(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
