import time
import cv2
import numpy as np
from PIL import ImageGrab
import win32api
import win32con
import win32gui

# ================================
# USER CONFIGURATION & DEFAULTS
# ================================
WINDOW_TITLE = "Huntera"  # Title bar text of your game window

# Available difficulties mapped to their visual image templates (off and on states)
DIFFICULTIES = {
    "1": ("Cauteloso", ["cauteloso_off.png", "cauteloso_on.png"]),
    "2": ("Ousado",    ["ousado_off.png",    "ousado_on.png"]),
    "3": ("Agressivo", ["agressivo_off.png", "agressivo_on.png"]),
    "4": ("Suicida",   ["suicida_off.png",   "suicida_on.png"]),
}

# Static coordinates for fixed elements
COORDS = {
    'INICIAR_CACADA_TOP_BUTTON': (956, 146),
    'ORGANIZAR_CACADA_CARD':     (515, 490),
    'SEARCH_BAR':                (394, 408),
    'FIRST_SEARCH_RESULT':       (412, 480),
    'INICIAR_COM_O_TIME':        (999, 734),
    'SAIR_DA_CACADA':            (832, 797),
}

# ================================
# CONSOLE INTERACTIVE SETUP
# ================================
def get_user_configuration():
    print("=" * 45)
    print("      HUNTERA BOT - CONFIGURATION SETUP      ")
    print("=" * 45)

    # 1. Hunt Name
    hunt_name_input = input("Enter Hunt Name [Default: Spider Nest]: ").strip()
    hunt_name = hunt_name_input if hunt_name_input else "Spider Nest"

    # 2. Hunt Time in Minutes
    while True:
        time_input = input("Enter Hunt Duration in minutes [Default: 0.4]: ").strip()
        if not time_input:
            hunt_time_minutes = 0.4
            break
        try:
            hunt_time_minutes = float(time_input)
            if hunt_time_minutes > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input! Please enter a valid number (e.g., 0.4 or 5).")

    # 3. Difficulty
    print("\nSelect Difficulty:")
    print(" [1] Cauteloso")
    print(" [2] Ousado")
    print(" [3] Agressivo")
    print(" [4] Suicida (Default)")
    
    while True:
        diff_choice = input("Choice (1-4) [Default: 4]: ").strip()
        if not diff_choice:
            difficulty_name, template_files = DIFFICULTIES["4"]
            break
        if diff_choice in DIFFICULTIES:
            difficulty_name, template_files = DIFFICULTIES[diff_choice]
            break
        print("Invalid choice! Please enter a number between 1 and 4.")

    print("\n" + "-" * 45)
    print(f" CONFIGURATION CONFIRMED:")
    print(f"  • Hunt Name : {hunt_name}")
    print(f"  • Duration  : {hunt_time_minutes} minute(s)")
    print(f"  • Difficulty: {difficulty_name}")
    print("-" * 45 + "\n")

    return hunt_name, hunt_time_minutes, difficulty_name, template_files

# ================================
# HELPER FUNCTIONS (BACKGROUND API & VISION)
# ================================
def get_window_handle(title_substring):
    """Finds the window handle that is currently MAXIMIZED and matches the title."""
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and title_substring.lower() in win32gui.GetWindowText(hwnd).lower():
            placement = win32gui.GetWindowPlacement(hwnd)
            if placement[1] == win32con.SW_SHOWMAXIMIZED:
                extra.append(hwnd)

    hwnds = []
    win32gui.EnumWindows(enum_windows_callback, hwnds)
    if not hwnds:
        raise Exception(f"No MAXIMIZED window containing '{title_substring}' was found!")
    
    return hwnds[0]

def send_click(hwnd, x, y):
    """Sends a left mouse click directly to target coordinates inside the window."""
    l_param = win32api.MAKELONG(x, y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)

def send_text(hwnd, text):
    """Sends keystrokes directly to the target window."""
    for char in text:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.03)

def find_image_in_window(hwnd, template_paths, confidence=0.6):
    """
    Captures window screenshot and attempts template matching against one or multiple
    template image paths (useful for multi-state buttons like ON/OFF or active/inactive).
    """
    if isinstance(template_paths, str):
        template_paths = [template_paths]

    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
    bbox = (client_left, client_top, client_left + right, client_top + bottom)

    screenshot = ImageGrab.grab(bbox)
    img_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

    for path in template_paths:
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            continue

        w, h = template.shape[1], template.shape[0]
        res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= confidence:
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)

    return None

# ================================
# MAIN LOOP
# ================================
def run_bot():
    # Prompt user for settings before starting
    hunt_name, hunt_time_minutes, difficulty_name, template_files = get_user_configuration()

    hwnd = get_window_handle(WINDOW_TITLE)
    print(f"Connected to window handle: {hwnd}")
    
    loop_count = 1
    
    while True:
        print(f"\n--- Starting Hunt Loop #{loop_count} ---")
        
        # Step 1: Click top "Iniciar caçada" button
        print("Opening hunt menu...")
        send_click(hwnd, *COORDS['INICIAR_CACADA_TOP_BUTTON'])
        time.sleep(0.2)
        
        # Step 2: Select "Organizar caçada"
        send_click(hwnd, *COORDS['ORGANIZAR_CACADA_CARD'])
        time.sleep(0.2)
        
        # Step 3: Search for the hunt
        print(f"Searching for hunt: '{hunt_name}'")
        send_click(hwnd, *COORDS['SEARCH_BAR'])
        time.sleep(0.2)
        
        # Clear search box using Backspaces
        for _ in range(25):
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_BACK, 0)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_BACK, 0)
            time.sleep(0.02)
            
        send_text(hwnd, hunt_name)
        time.sleep(0.5)
        
        # Step 4: Click the search result
        print("Selecting hunt...")
        send_click(hwnd, *COORDS['FIRST_SEARCH_RESULT'])
        time.sleep(0.5)
        
        # Step 5: Dynamic difficulty detection via Template Matching
        print(f"Locating '{difficulty_name}' button on screen...")
        diff_coords = find_image_in_window(hwnd, template_files, confidence=0.75)
        
        if diff_coords:
            print(f"Button found at relative coordinates: {diff_coords}. Clicking...")
            send_click(hwnd, *diff_coords)
            time.sleep(1.5)
        else:
            print(f"Warning: Could not visually locate '{difficulty_name}' button ({template_files}). Skipping difficulty click.")
        
        # Step 6: Click "Iniciar com o time"
        print("Starting hunt ('Iniciar com o time')...")
        send_click(hwnd, *COORDS['INICIAR_COM_O_TIME'])
        time.sleep(1)
        send_click(hwnd, *COORDS['INICIAR_COM_O_TIME'])
        time.sleep(0.5)
        
        # Step 7: Wait out the duration timer
        duration_seconds = hunt_time_minutes * 60
        print(f"Hunt active. Waiting {hunt_time_minutes} minute(s) ({duration_seconds} seconds)...")
        time.sleep(duration_seconds)
        
        # Step 8: Click "SAIR DA CAÇADA"
        print("Time reached! Exiting hunt...")
        send_click(hwnd, *COORDS['SAIR_DA_CACADA'])
        
        # Step 9: Wait ~1.5 seconds after exiting
        time.sleep(1.5)
        
        loop_count += 1

if __name__ == "__main__":
    run_bot()