import threading
import time
import tkinter as tk
import customtkinter as ctk
import win32api
import win32con
import win32gui

# Set theme and appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ================================
# CONSTANTS & DEFAULTS
# ================================
WINDOW_TITLE = "Huntera"

DIFFICULTIES = {
    "Cauteloso": "DIFFICULTY_CAUTELOSO",
    "Ousado": "DIFFICULTY_OUSADO",
    "Agressivo": "DIFFICULTY_AGRESSIVO",
    "Suicida": "DIFFICULTY_SUICIDA",
}

DEFAULT_COORDS = {
    "INICIAR_CACADA_TOP_BUTTON": (956, 146),
    "ORGANIZAR_CACADA_CARD": (515, 490),
    "SEARCH_BAR": (394, 408),
    "FIRST_SEARCH_RESULT": (412, 480),
    "DIFFICULTY_CAUTELOSO": (366, 478),
    "DIFFICULTY_OUSADO": (480, 478),
    "DIFFICULTY_AGRESSIVO": (577, 478),
    "DIFFICULTY_SUICIDA": (650, 478),
    "INICIAR_COM_O_TIME": (999, 734),
    "SAIR_DA_CACADA": (832, 797),
}

COORD_LABELS = {
    "INICIAR_CACADA_TOP_BUTTON": "Top 'Iniciar Caçada'",
    "ORGANIZAR_CACADA_CARD": "Card 'Organizar Caçada'",
    "SEARCH_BAR": "Search Bar",
    "FIRST_SEARCH_RESULT": "First Search Result",
    "DIFFICULTY_CAUTELOSO": "Difficulty: Cauteloso",
    "DIFFICULTY_OUSADO": "Difficulty: Ousado",
    "DIFFICULTY_AGRESSIVO": "Difficulty: Agressivo",
    "DIFFICULTY_SUICIDA": "Difficulty: Suicida",
    "INICIAR_COM_O_TIME": "'Iniciar com o time'",
    "SAIR_DA_CACADA": "'Sair da Caçada'",
}

# ================================
# WIN32 HELPER FUNCTIONS
# ================================
def get_window_handle(title_substring, require_maximized=False):
    """Finds target window handle matching title."""
    hwnds = []

    def enum_windows_callback(hwnd, extra):
        if (
            win32gui.IsWindowVisible(hwnd)
            and title_substring.lower() in win32gui.GetWindowText(hwnd).lower()
        ):
            if require_maximized:
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMAXIMIZED:
                    extra.append(hwnd)
            else:
                extra.append(hwnd)

    win32gui.EnumWindows(enum_windows_callback, hwnds)
    if not hwnds:
        return None
    return hwnds[0]


def send_click(hwnd, x, y):
    """Sends a left mouse click directly to target window client coordinates."""
    l_param = win32api.MAKELONG(x, y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)


def send_text(hwnd, text):
    """Sends keystrokes directly to the target window."""
    for char in text:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.03)


# ================================
# GUI APPLICATION CLASS
# ================================
class HunteraBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Afonso Automation Bot")
        self.geometry("560x780")
        self.resizable(False, False)

        self.is_running = False
        self.stop_requested = False
        self.bot_thread = None

        # Store input fields for coords: {key: (entry_x, entry_y)}
        self.coord_entries = {}

        self._build_ui()

        # Start mouse tracker loop
        self._track_mouse_position()

    def _build_ui(self):
        # Header Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Afonso BOT",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.title_label.pack(pady=(15, 5))

        # Main Tabview
        self.tabview = ctk.CTkTabview(self, width=520, height=680)
        self.tabview.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        self.tab_main = self.tabview.add("Main Controls")
        self.tab_coords = self.tabview.add("Advanced Coords")

        self._build_main_tab()
        self._build_coords_tab()

    def _build_main_tab(self):
        # Configuration Frame
        self.config_frame = ctk.CTkFrame(self.tab_main)
        self.config_frame.pack(padx=10, pady=10, fill="x")

        # 1. Hunt Name Input
        self.lbl_hunt_name = ctk.CTkLabel(
            self.config_frame, text="Hunt Name:", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_hunt_name.pack(anchor="w", padx=15, pady=(10, 0))

        self.entry_hunt_name = ctk.CTkEntry(
            self.config_frame, placeholder_text="Spider Nest"
        )
        self.entry_hunt_name.insert(0, "Spider Nest")
        self.entry_hunt_name.pack(fill="x", padx=15, pady=(2, 10))

        # 2. Duration Inputs (Minutes and Seconds)
        self.lbl_duration = ctk.CTkLabel(
            self.config_frame,
            text="Duration (Min / Sec):",
            font=ctk.CTkFont(weight="bold"),
        )
        self.lbl_duration.pack(anchor="w", padx=15, pady=(5, 0))

        self.time_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.time_frame.pack(fill="x", padx=15, pady=(2, 10))

        self.entry_min = ctk.CTkEntry(self.time_frame, placeholder_text="0")
        self.entry_min.insert(0, "0")
        self.entry_min.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.lbl_min_unit = ctk.CTkLabel(self.time_frame, text="min")
        self.lbl_min_unit.pack(side="left", padx=(0, 10))

        self.entry_sec = ctk.CTkEntry(self.time_frame, placeholder_text="24")
        self.entry_sec.insert(0, "24")
        self.entry_sec.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.lbl_sec_unit = ctk.CTkLabel(self.time_frame, text="sec")
        self.lbl_sec_unit.pack(side="left")

        # 3. Difficulty Selector
        self.lbl_diff = ctk.CTkLabel(
            self.config_frame, text="Difficulty:", font=ctk.CTkFont(weight="bold")
        )
        self.lbl_diff.pack(anchor="w", padx=15, pady=(5, 0))

        self.option_diff = ctk.CTkOptionMenu(
            self.config_frame, values=list(DIFFICULTIES.keys())
        )
        self.option_diff.set("Suicida")
        self.option_diff.pack(fill="x", padx=15, pady=(2, 15))

        # Control Buttons Frame
        self.btn_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.btn_frame.pack(padx=10, pady=5, fill="x")

        self.btn_start = ctk.CTkButton(
            self.btn_frame,
            text="Start Bot",
            fg_color="#28a745",
            hover_color="#218838",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self.start_bot,
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_stop = ctk.CTkButton(
            self.btn_frame,
            text="Stop Bot",
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
            font=ctk.CTkFont(weight="bold", size=14),
            command=self.stop_bot,
        )
        self.btn_stop.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # Status & Timer Display
        self.lbl_status = ctk.CTkLabel(
            self.tab_main,
            text="Status: Idle",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#aaa",
        )
        self.lbl_status.pack(pady=(10, 2))

        self.lbl_timer = ctk.CTkLabel(
            self.tab_main, text="00:00", font=ctk.CTkFont(size=26, weight="bold")
        )
        self.lbl_timer.pack(pady=(0, 5))

        # Log Output Box
        self.log_box = ctk.CTkTextbox(self.tab_main, height=130, font=ctk.CTkFont(size=12))
        self.log_box.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        self.log_box.configure(state="disabled")

    def _build_coords_tab(self):
        # Mouse Position Tracker Frame
        self.mouse_tracker_frame = ctk.CTkFrame(self.tab_coords)
        self.mouse_tracker_frame.pack(fill="x", padx=5, pady=(5, 10))

        self.lbl_mouse_title = ctk.CTkLabel(
            self.mouse_tracker_frame,
            text="Live Client Mouse Position:",
            font=ctk.CTkFont(weight="bold", size=13),
        )
        self.lbl_mouse_title.pack(side="left", padx=15, pady=10)

        self.lbl_mouse_pos = ctk.CTkLabel(
            self.mouse_tracker_frame,
            text="X: 0 | Y: 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#17a2b8",
        )
        self.lbl_mouse_pos.pack(side="right", padx=15, pady=10)

        # Scrollable container for coordinate inputs
        scroll_frame = ctk.CTkScrollableFrame(self.tab_coords)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=0)

        # Header titles
        lbl_hdr_name = ctk.CTkLabel(scroll_frame, text="Target Name", font=ctk.CTkFont(weight="bold"))
        lbl_hdr_name.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        lbl_hdr_x = ctk.CTkLabel(scroll_frame, text="X Coord", font=ctk.CTkFont(weight="bold"))
        lbl_hdr_x.grid(row=0, column=1, padx=5, pady=5)

        lbl_hdr_y = ctk.CTkLabel(scroll_frame, text="Y Coord", font=ctk.CTkFont(weight="bold"))
        lbl_hdr_y.grid(row=0, column=2, padx=5, pady=5)

        # Dynamically create row per coordinate setting
        for idx, (key, default_val) in enumerate(DEFAULT_COORDS.items(), start=1):
            label_text = COORD_LABELS.get(key, key)

            lbl = ctk.CTkLabel(scroll_frame, text=label_text, anchor="w")
            lbl.grid(row=idx, column=0, padx=10, pady=4, sticky="w")

            entry_x = ctk.CTkEntry(scroll_frame, width=70)
            entry_x.insert(0, str(default_val[0]))
            entry_x.grid(row=idx, column=1, padx=5, pady=4)

            entry_y = ctk.CTkEntry(scroll_frame, width=70)
            entry_y.insert(0, str(default_val[1]))
            entry_y.grid(row=idx, column=2, padx=5, pady=4)

            self.coord_entries[key] = (entry_x, entry_y)

        # Reset defaults button
        self.btn_reset_coords = ctk.CTkButton(
            self.tab_coords,
            text="Reset Coords to Default",
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=self.reset_coords_to_default,
        )
        self.btn_reset_coords.pack(pady=10)

    def _track_mouse_position(self):
        """Calculates cursor position relative to target window's client area."""
        try:
            hwnd = get_window_handle(WINDOW_TITLE)
            if hwnd:
                screen_x, screen_y = win32gui.GetCursorPos()
                client_x, client_y = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
                self.lbl_mouse_pos.configure(
                    text=f"X: {client_x} | Y: {client_y}",
                    text_color="#17a2b8"
                )
            else:
                self.lbl_mouse_pos.configure(
                    text="Window Not Found",
                    text_color="#dc3545"
                )
        except Exception:
            pass

        self.after(50, self._track_mouse_position)

    def reset_coords_to_default(self):
        """Restores coordinates back to original DEFAULT_COORDS."""
        for key, (x_val, y_val) in DEFAULT_COORDS.items():
            if key in self.coord_entries:
                entry_x, entry_y = self.coord_entries[key]

                entry_x.delete(0, "end")
                entry_x.insert(0, str(x_val))

                entry_y.delete(0, "end")
                entry_y.insert(0, str(y_val))

        self.log("Coordinates reset to default settings.")

    def get_current_coords(self):
        """Parses active coordinate inputs from the Advanced tab."""
        active_coords = {}
        for key, (entry_x, entry_y) in self.coord_entries.items():
            try:
                x = int(entry_x.get().strip())
                y = int(entry_y.get().strip())
                active_coords[key] = (x, y)
            except ValueError:
                raise ValueError(f"Invalid integer coordinate for '{COORD_LABELS.get(key, key)}'")
        return active_coords

    def set_coords_enabled(self, enabled=True):
        """Enable or disable coordinate inputs during execution."""
        state = "normal" if enabled else "disabled"
        for entry_x, entry_y in self.coord_entries.values():
            entry_x.configure(state=state)
            entry_y.configure(state=state)
        self.btn_reset_coords.configure(state=state)

    def log(self, message):
        """Appends a message to the UI log box safely."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.after(0, _append)

    def set_timer(self, seconds_left):
        """Updates countdown text in the UI."""
        mins, secs = divmod(max(0, int(seconds_left)), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.after(0, lambda: self.lbl_timer.configure(text=time_str))

    def update_status(self, status_text, color="#ffffff"):
        """Updates status label text and color."""
        self.after(
            0, lambda: self.lbl_status.configure(text=status_text, text_color=color)
        )

    def start_bot(self):
        # Input Validation - Duration (Minutes & Seconds)
        hunt_name = self.entry_hunt_name.get().strip() or "Spider Nest"
        try:
            min_val = float(self.entry_min.get().strip() or 0)
            sec_val = float(self.entry_sec.get().strip() or 0)
            total_duration_seconds = (min_val * 60) + sec_val

            if total_duration_seconds <= 0:
                raise ValueError
        except ValueError:
            self.log("ERROR: Invalid hunt duration! Please enter positive numbers.")
            return

        # Input Validation - Coordinates
        try:
            active_coords = self.get_current_coords()
        except ValueError as err:
            self.log(f"ERROR: {str(err)}")
            return

        diff_name = self.option_diff.get()
        diff_coord_key = DIFFICULTIES[diff_name]

        # Toggle UI controls
        self.is_running = True
        self.stop_requested = False
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.entry_hunt_name.configure(state="disabled")
        self.entry_min.configure(state="disabled")
        self.entry_sec.configure(state="disabled")
        self.option_diff.configure(state="disabled")
        self.set_coords_enabled(False)

        self.update_status("Status: Running...", "#28a745")
        self.log("Starting automation thread...")

        # Spawn background thread
        self.bot_thread = threading.Thread(
            target=self.run_bot_loop,
            args=(hunt_name, total_duration_seconds, diff_coord_key, active_coords),
            daemon=True,
        )
        self.bot_thread.start()

    def stop_bot(self):
        if self.is_running:
            self.stop_requested = True
            self.log("Stop requested! Waiting for current step to finish...")
            self.btn_stop.configure(state="disabled")

    def _reset_ui_state(self):
        self.is_running = False
        self.stop_requested = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.entry_hunt_name.configure(state="normal")
        self.entry_min.configure(state="normal")
        self.entry_sec.configure(state="normal")
        self.option_diff.configure(state="normal")
        self.set_coords_enabled(True)
        self.update_status("Status: Idle", "#aaa")
        self.set_timer(0)

    def sleep_interruptible(self, seconds):
        """Sleeps in short intervals to allow stopping the bot mid-wait."""
        steps = int(seconds / 0.1)
        for _ in range(steps):
            if self.stop_requested:
                return False
            time.sleep(0.1)
        return True

    def run_bot_loop(self, hunt_name, duration_seconds, diff_coord_key, coords):
        hwnd = get_window_handle(WINDOW_TITLE)
        if not hwnd:
            self.log(f"ERROR: Target window '{WINDOW_TITLE}' not found!")
            self.after(0, self._reset_ui_state)
            return

        self.log(f"Connected to window handle: {hwnd}")
        loop_count = 1

        while not self.stop_requested:
            self.log(f"--- Starting Hunt Loop #{loop_count} ---")

            # Step 1: Click top "Iniciar caçada" button
            self.log("Opening hunt menu...")
            send_click(hwnd, *coords["INICIAR_CACADA_TOP_BUTTON"])
            if not self.sleep_interruptible(0.2):
                break

            # Step 2: Select "Organizar caçada"
            send_click(hwnd, *coords["ORGANIZAR_CACADA_CARD"])
            if not self.sleep_interruptible(0.2):
                break

            # Step 3: Search for the hunt
            self.log(f"Searching for hunt: '{hunt_name}'")
            send_click(hwnd, *coords["SEARCH_BAR"])
            if not self.sleep_interruptible(0.2):
                break

            # Clear search box using Backspaces
            for _ in range(25):
                if self.stop_requested:
                    break
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_BACK, 0)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_BACK, 0)
                time.sleep(0.02)

            send_text(hwnd, hunt_name)
            if not self.sleep_interruptible(0.5):
                break

            # Step 4: Click search result
            self.log("Selecting hunt...")
            send_click(hwnd, *coords["FIRST_SEARCH_RESULT"])
            if not self.sleep_interruptible(0.5):
                break

            # Step 5: Select difficulty
            if diff_coord_key in coords:
                self.log("Setting difficulty...")
                send_click(hwnd, *coords[diff_coord_key])
                if not self.sleep_interruptible(1.5):
                    break

            # Step 6: Click "Iniciar com o time"
            self.log("Starting hunt ('Iniciar com o time')...")
            send_click(hwnd, *coords["INICIAR_COM_O_TIME"])
            if not self.sleep_interruptible(1.0):
                break
            send_click(hwnd, *coords["INICIAR_COM_O_TIME"])
            if not self.sleep_interruptible(0.5):
                break

            # Step 7: Wait out duration with live UI timer
            self.log(f"Hunt active. Waiting {int(duration_seconds)}s...")
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                if self.stop_requested:
                    break
                remaining = end_time - time.time()
                self.set_timer(remaining)
                time.sleep(0.5)

            if self.stop_requested:
                break

            # Step 8: Click "SAIR DA CAÇADA"
            self.log("Time reached! Exiting hunt...")
            send_click(hwnd, *coords["SAIR_DA_CACADA"])
            if not self.sleep_interruptible(1.5):
                break

            loop_count += 1

        self.log("Bot stopped.")
        self.after(0, self._reset_ui_state)


if __name__ == "__main__":
    app = HunteraBotGUI()
    app.mainloop()