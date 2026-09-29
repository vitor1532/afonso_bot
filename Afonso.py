import time
import cv2
import numpy as np
from PIL import ImageGrab
import win32api
import win32con
import win32gui

# ================================
# USER CONFIGURATION
# ================================
WINDOW_TITLE = "Huntera"  # Title bar text of your game window

# Image file templates for UI elements
UI_TEMPLATES = {
    'INICIAR_CACADA_TOP': 'iniciar_cacada_top.png',
    'ORGANIZAR_CACADA':    'organizar_cacada.png',
    'SEARCH_BAR':          'search_bar.png',
    'FIRST_SEARCH_RESULT': 'first_search_result.png',
    'INICIAR_COM_O_TIME':  'iniciar_com_o_time.png',
    'SAIR_DA_CACADA':      'sair_da_cacada.png',
}

# Available difficulties mapped to their visual image templates
DIFFICULTIES = {
    "1": ("Cauteloso", "cauteloso.png"),
    "2": ("Ousado", "ousado.png"),
    "3": ("Agressivo", "agressivo.png"),
    "4": ("Suicida", "suicida.png"),
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
            difficulty_name, diff_template = DIFFICULTIES["4"]
            break
        if diff_choice in DIFFICULTIES:
            difficulty_name, diff_template = DIFFICULTIES[diff_choice]
            break
        print("Invalid choice! Please enter a number between 1 and 4.")

    print("\n" + "-" * 45)
    print(f" CONFIGURATION CONFIRMED:")
    print(f"  • Hunt Name : {hunt_name}")
    print(f"  • Duration  : {hunt_time_minutes} minute(s)")
    print(f"  • Difficulty: {difficulty_name}")
    print("-" * 45 + "\n")

    return hunt_name, hunt_time_minutes, difficulty_name, diff_template

# ================================
# VISION & API HELPER FUNCTIONS
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
    """Sends a left mouse click directly to target relative coordinates inside the window."""
    l_param = win32api.MAKELONG(x, y)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    time.sleep(0.05)
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)

def send_text(hwnd, text):
    """Sends keystrokes directly to the target window."""
    for char in text:
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.03)

def find_image_in_window(hwnd, template_path, confidence=0.8):
    """
    Captures window screenshot and uses OpenCV Template Matching
    to return relative (x, y) target coordinates if found.
    """
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
    bbox = (client_left, client_top, client_left + right, client_top + bottom)

    # Capture window area
    screenshot = ImageGrab.grab(bbox)
    img_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        raise FileNotFoundError(f"Template image file '{template_path}' was not found in directory!")

    w, h = template.shape[1], template.shape[0]

    # Perform Template Matching
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= confidence:
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y)

    return None

def click_template(hwnd, template_path, element_name, retries=5, delay=0.5, confidence=0.8):
    """
    Attempts to locate and click a UI template on screen with retries.
    """
    for attempt in range(1, retries + 1):
        coords = find_image_in_window(hwnd, template_path, confidence=confidence)
        if coords:
            print(f"[{element_name}] Found at {coords}. Clicking...")
            send_click(hwnd, *coords)
            return True
        time.sleep(delay)
    
    print(f"[{element_name}] Warning: Could not locate visual template ({template_path}).")
    return False

# ================================
# MAIN LOOP
# ================================
def run_bot():
    hunt_name, hunt_time_minutes, difficulty_name, diff_template = get_user_configuration()

    hwnd = get_window_handle(WINDOW_TITLE)
    print(f"Connected to window handle: {hwnd}")
    
    loop_count = 1
    
    while True:
        print(f"\n--- Starting Hunt Loop #{loop_count} ---")
        
        # Step 1: Click top "Iniciar caçada" button
        print("Opening hunt menu...")
        click_template(hwnd, UI_TEMPLATES['INICIAR_CACADA_TOP'], "Top Iniciar Caçada Button")
        time.sleep(0.3)
        
        # Step 2: Select "Organizar caçada"
        click_template(hwnd, UI_TEMPLATES['ORGANIZAR_CACADA'], "Organizar Caçada Card")
        time.sleep(0.3)
        
        # Step 3: Search for the hunt
        print(f"Searching for hunt: '{hunt_name}'")
        if click_template(hwnd, UI_TEMPLATES['SEARCH_BAR'], "Search Bar"):
            time.sleep(0.2)
            
            # Clear search box using Backspaces
            for _ in range(25):
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_BACK, 0)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_BACK, 0)
                time.sleep(0.02)
                
            send_text(hwnd, hunt_name)
            time.sleep(0.5)
        
        # Step 4: Click the search result
        print("Selecting hunt from search results...")
        click_template(hwnd, UI_TEMPLATES['FIRST_SEARCH_RESULT'], "First Search Result")
        time.sleep(0.5)
        
        # Step 5: Dynamic difficulty detection
        print(f"Selecting difficulty '{difficulty_name}'...")
        click_template(hwnd, diff_template, f"Difficulty: {difficulty_name}")
        time.sleep(1.5)
        
        # Step 6: Click "Iniciar com o time"
        print("Starting hunt ('Iniciar com o time')...")
        click_template(hwnd, UI_TEMPLATES['INICIAR_COM_O_TIME'], "Iniciar com o time")
        time.sleep(1.0)
        click_template(hwnd, UI_TEMPLATES['INICIAR_COM_O_TIME'], "Iniciar com o time (Confirm)")
        time.sleep(0.5)
        
        # Step 7: Wait out the duration timer
        duration_seconds = hunt_time_minutes * 60
        print(f"Hunt active. Waiting {hunt_time_minutes} minute(s) ({duration_seconds} seconds)...")
        time.sleep(duration_seconds)
        
        # Step 8: Click "SAIR DA CAÇADA"
        print("Time reached! Exiting hunt...")
        click_template(hwnd, UI_TEMPLATES['SAIR_DA_CACADA'], "Sair da Caçada")
        
        # Step 9: Post-exit delay
        time.sleep(1.5)
        
        loop_count += 1

if __name__ == "__main__":
    run_bot()