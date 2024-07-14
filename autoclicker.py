import pyautogui
import time
import random
from pynput.mouse import Button, Controller
import pygetwindow as gw
import logging
import sys
import threading

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

mouse = Controller()
time.sleep(0.5)

def click(xs, ys):
    mouse.position = (xs, ys + random.randint(1, 2))
    mouse.press(Button.left)
    mouse.release(Button.left)

def check_blue_color(scrnq, window_rectq):
    widthq, heightq = scrnq.size
    for xq in range(0, widthq, 20):
        for yq in range(200, heightq, 20):
            rq, gq, bq = scrnq.getpixel((xq, yq))
            if (rq in range(5, 150)) and (gq in range(102, 220)) and (bq in range(200, 245)):
                screen_xq = window_rectq[0] + xq
                screen_yq = window_rectq[1] + yq
                click(screen_xq, screen_yq)
                return True
    return False

def autoclicker(window_title):
    windows = gw.getWindowsWithTitle(window_title)

    if not windows:
        logging.info(f"Window '{window_title}' not found!")
        return

    telegram_window = windows[0]
    last_check_time = time.time()
    last_blue_check_time = time.time()
    last_pause_time = time.time()

    logging.info(f"Window '{window_title}' found, starting autoclicker.")

    while running:
        window_rect = (
            telegram_window.left, telegram_window.top, telegram_window.width, telegram_window.height
        )

        if telegram_window:
            try:
                telegram_window.activate()
            except:
                telegram_window.minimize()
                telegram_window.restore()

        scrn = pyautogui.screenshot(region=(window_rect[0], window_rect[1], window_rect[2], window_rect[3]))

        width, height = scrn.size

        for x in range(0, width, 20):
            for y in range(130, height, 20):
                r, g, b = scrn.getpixel((x, y))
                if (b in range(0, 125)) and (r in range(102, 220)) and (g in range(200, 255)):
                    screen_x = window_rect[0] + x + 3
                    screen_y = window_rect[1] + y + 5
                    click(screen_x, screen_y)
                    time.sleep(0.002)
                    break

        current_time = time.time()

        next_check_time = random.uniform(1.5, 2.50)

        if current_time - last_pause_time >= next_check_time:
            pause_time = random.uniform(0.60, 1.10)
            time.sleep(pause_time)
            last_pause_time = current_time

        if current_time - last_blue_check_time >= 0.1:
            if check_blue_color(scrn, window_rect):
                last_blue_check_time = current_time

    logging.info('Autoclicker stopped')

def start_autoclicker(window_title):
    global running, autoclicker_thread
    running = True
    autoclicker_thread = threading.Thread(target=autoclicker, args=(window_title,))
    autoclicker_thread.start()

def stop_autoclicker():
    global running
    running = False
    if autoclicker_thread.is_alive():
        autoclicker_thread.join()