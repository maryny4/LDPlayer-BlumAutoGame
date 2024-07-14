import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import logging
import time
import asyncio
import subprocess

ADB_PATH = r"platform-tools\adb.exe"
BLUM_BOT_URL = "https://t.me/BlumCryptoBot"
SCREEN_WIDTH, SCREEN_HEIGHT = 440, 820


def capture_window(window_title):
    windows = gw.getWindowsWithTitle(window_title)
    if windows:
        window = windows[0]
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    return None


async def stop_all_apps(device_id):
    """Stop all running apps on the device."""
    cmd = f'{ADB_PATH} -s {device_id} shell "pm list packages -3"'
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    packages = result.stdout.splitlines()
    for package in packages:
        package_name = package.replace("package:", "")
        stop_cmd = f"{ADB_PATH} -s {device_id} shell am force-stop {package_name}"
        subprocess.run(stop_cmd, shell=True)
        logging.info(f"Stopped app: {package_name}")


async def wait_for_image(image_path, confidence=0.7, timeout=120, interval=5):
    """Wait for the specified image to appear on the screen."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            location = await asyncio.to_thread(pyautogui.locateOnScreen, image_path, confidence=confidence, minSearchTime=1)
            if location:
                logging.info(f"Image '{image_path}' found on the screen at {location}.")
                return location
            else:
                logging.info(f"Waiting for image '{image_path}' to appear...")
        except pyautogui.ImageNotFoundException:
            logging.info(f"Image '{image_path}' not found. Retrying...")

        await asyncio.sleep(interval)

    logging.error(f"Timeout reached while waiting for image '{image_path}' after {timeout} seconds.")
    return None


def find_template_coordinates(screenshot, template_path):
    """Find coordinates of the template in the screenshot."""
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_loc, max_val


async def click_on_template(window_title, template_path, timeout=60, interval=5):
    """Click on the specific template in the window."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        screenshot = capture_window(window_title)
        if screenshot is not None:
            max_loc, max_val = find_template_coordinates(screenshot, template_path)
            if max_val > 0.8:  # Adjust the threshold as needed
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                w, h = template.shape[::-1]
                window = gw.getWindowsWithTitle(window_title)[0]
                click_x = window.left + max_loc[0] + w // 2
                click_y = window.top + max_loc[1] + h // 2
                pyautogui.click(click_x, click_y)
                logging.info(f"Clicked on template at ({click_x}, {click_y}) in window '{window_title}'.")
                return
            else:
                logging.info("Template not found, retrying...")
        else:
            logging.error("Failed to capture the window for template matching.")

        await asyncio.sleep(interval)

    logging.error(f"Failed to find the template in window '{window_title}' within {timeout} seconds.")


def get_adb_device_ids():
    """Get the list of ADB device IDs."""
    result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
    lines = result.stdout.splitlines()
    device_ids = [line.split()[0] for line in lines if "emulator" in line and "device" in line]
    return device_ids


def get_window_title_by_index(index):
    """Get the window title of the emulator based on its index."""
    titles = gw.getAllTitles()
    for title in titles:
        if f"LDPlayer{index}" in title:
            return title
    logging.error(f"No window title found for LDPlayer with index {index}.")
    return None


async def move_and_resize_window(index, position):
    """Move and resize the window to the specified position."""
    window_title = get_window_title_by_index(index)
    if window_title:
        left, top, width, height = position
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                windows = gw.getWindowsWithTitle(window_title)
                if not windows:
                    raise IndexError
                window = windows[0]
                logging.info(f"Attempt {attempt + 1}: Current window position and size for '{window_title}': "
                             f"({window.left}, {window.top}, {window.width}, {window.height})")
                window.moveTo(left, top)
                window.resizeTo(width, height)
                logging.info(f"Moved and resized window '{window_title}' to ({left}, {top}, {width}, {height}).")
                return
            except IndexError:
                logging.warning(f"Window with title '{window_title}' not found. Retrying...")
                await asyncio.sleep(0.5)
        logging.error(f"Window with title '{window_title}' not found after {max_attempts} attempts.")
    else:
        logging.error(f"No window title found for LDPlayer with index {index}.")


