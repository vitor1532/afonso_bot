import time
import win32api
import win32con
import win32gui

# ================================
# USER CONFIGURATION & VARIABLES
# ================================
WINDOW_TITLE = "Huntera"  # Title bar text of your game window

HUNT_NAME = "Spider Nest"     # Name of the hunt to search
HUNT_TIME_MINUTES = 0.4         # Time in minutes per hunt session
DIFFICULTY = "Suicida"         # Options: Cauteloso, Ousado, Agressivo, Suicida

# Relative click target coordinates inside the game client window (X, Y)
# Adjust these coordinates based on your game resolution/UI layout:
COORDS = {
    'INICIAR_CACADA_TOP_BUTTON': (956, 146),  # "Iniciar caçada" button on the top bar
    'ORGANIZAR_CACADA_CARD':     (515, 490), # "Explorar caçadas" or "Organizar caçada" card
    'SEARCH_BAR':                (394, 408), # Search input field
    'FIRST_SEARCH_RESULT':       (412, 480), # First hunt result card
    'DIFFICULTY_CAUTELOSO':      (382, 479),  # Difficulty buttons
    'DIFFICULTY_OUSADO':         (465, 476),
    'DIFFICULTY_AGRESSIVO':      (551, 478),
    'DIFFICULTY_SUICIDA':        (630, 480),
    'INICIAR_COM_O_TIME':        (999, 734), # "Iniciar com o time" button
    'SAIR_DA_CACADA':            (832, 797), # "SAIR DA CAÇADA" button
}

# ================================
# HELPER FUNCTIONS (BACKGROUND API)
# ================================
def get_window_handle(title_substring):
    """Finds the window handle that is currently MAXIMIZED and matches the title."""
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and title_substring.lower() in win32gui.GetWindowText(hwnd).lower():
            # Get window placement state
            # flags, showCmd, ptMin, ptMax, rect = win32gui.GetWindowPlacement(hwnd)
            placement = win32gui.GetWindowPlacement(hwnd)
            # win32con.SW_SHOWMAXIMIZED is 3
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
        # Convert character to virtual key code / message
        win32api.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        time.sleep(0.03)

# ================================
# MAIN LOOP
# ================================
def run_bot():
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
        print(f"Searching for hunt: '{HUNT_NAME}'")
        send_click(hwnd, *COORDS['SEARCH_BAR'])
        time.sleep(0.2)
        
        # Clear search box using Backspaces
        for _ in range(25):
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_BACK, 0)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_BACK, 0)
            time.sleep(0.02)
            
        send_text(hwnd, HUNT_NAME)
        time.sleep(0.5)
        
        # Step 4: Click the search result
        print("Selecting hunt...")
        send_click(hwnd, *COORDS['FIRST_SEARCH_RESULT'])
        time.sleep(0.5)
        
        # Step 5: Select difficulty
        diff_key = f"DIFFICULTY_{DIFFICULTY.upper()}"
        if diff_key in COORDS:
            print(f"Selecting difficulty: {DIFFICULTY}")
            send_click(hwnd, *COORDS[diff_key])
            time.sleep(1.5)
        
        # Step 6: Click "Iniciar com o time"
        print("Starting hunt ('Iniciar com o time')...")
        send_click(hwnd, *COORDS['INICIAR_COM_O_TIME'])
        time.sleep(1)
        send_click(hwnd, *COORDS['INICIAR_COM_O_TIME'])
        time.sleep(0.5)
        
        # Step 7: Wait out the duration timer
        duration_seconds = HUNT_TIME_MINUTES * 60
        print(f"Hunt active. Waiting {HUNT_TIME_MINUTES} minute(s) ({duration_seconds} seconds)...")
        time.sleep(duration_seconds)
        
        # Step 8: Click "SAIR DA CAÇADA"
        print("Time reached! Exiting hunt...")
        send_click(hwnd, *COORDS['SAIR_DA_CACADA'])
        
        # Step 9: Wait ~3 seconds after exiting
        time.sleep(1.5)
        
        loop_count += 1

if __name__ == "__main__":
    run_bot()