import subprocess
import asyncio
import logging
from utils import wait_for_image, click_on_template, ADB_PATH,  BLUM_BOT_URL
from ldplayer_manager import start_ld
from autoclicker import start_autoclicker, stop_autoclicker
import time

async def automate_instance(ldplayer_path, index, device_id, position, services_to_run):
    await start_ld(ldplayer_path, index, position)
    window_title = f"LDPlayer{index}"

    try:
        if "blum_auto" in services_to_run:
            await automate_blum_bot_autoclicker(device_id, window_title)

    except Exception as e:
        logging.error(f"Error in automate_instance: {e}")


async def automate_blum_bot_autoclicker(device_id, window_title):
    exit_all_loops = False
    try:
        logging.info("Waiting for Telegram icon...")
        if await wait_for_image("icon/telegram.png"):
            logging.info("Telegram icon found, starting bot...")
            subprocess.run([ADB_PATH, "-s", device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", BLUM_BOT_URL])
            await asyncio.sleep(1)
            subprocess.run([ADB_PATH, "-s", device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", BLUM_BOT_URL])
            await asyncio.sleep(1)
            await click_on_template(window_title, "icon/play_menu_blum.png", timeout=60, interval=3)
            await asyncio.sleep(1)
            await click_on_template(window_title, "icon/blum_start.png", timeout=15, interval=3)
            await asyncio.sleep(1)
            await click_on_template(window_title, "icon/continue.png", timeout=15, interval=3)
            await asyncio.sleep(1)
            await click_on_template(window_title, "icon/play.png", timeout=15, interval=3)
            await asyncio.sleep(1)
            logging.info("Starting autoclicker...")
            start_autoclicker(window_title)
            logging.info("50 seconds elapsed, stopping autoclicker...")
            await asyncio.sleep(50)
            stop_autoclicker()

            # Добавьте переменную для отслеживания времени последнего нажатия
            last_click_time = 0
            click_delay = 15  # Задержка в секундах между нажатиями

            while not exit_all_loops:
                logging.info("Checking for start farming icon...")

                if await wait_for_image("icon/play_for_autoreplay.png", timeout=85, interval=1, confidence=0.8):
                    current_time = time.time()
                    # Проверьте, прошло ли достаточно времени с последнего нажатия
                    if current_time - last_click_time > click_delay:
                        stop_autoclicker()
                        logging.info("Stop 10 second")
                        await asyncio.sleep(10)
                        await click_on_template(window_title, "icon/play_for_autoreplay.png", timeout=10, interval=1)
                        logging.info("Start farming icon found, restarting autoclicker...")
                        start_autoclicker(window_title)
                        last_click_time = current_time  # Обновите время последнего нажатия
                else:
                    stop_autoclicker()
                    exit_all_loops = True

    except Exception as e:
        logging.error(f"Exit from loop: {e}")
