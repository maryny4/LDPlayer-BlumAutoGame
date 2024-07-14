import asyncio
import logging
import sys
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import time
import json
import os
from ldplayer_manager import start_ld, close_ld, wait_for_all_devices
from automation_tasks import automate_instance

SCREEN_WIDTH, SCREEN_HEIGHT = 440, 820

# Конфигурация логирования
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_FILE = 'config.json'

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config_data, config_file, indent=4)

def load_config():
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            return json.load(config_file)
    return None

async def click_on_template(template_path, timeout=60, interval=5):
    start_time = time.time()
    template = cv2.imread(template_path, 0)
    w, h = template.shape[::-1]

    while time.time() - start_time < timeout:
        screen = np.array(ImageGrab.grab())
        gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.8)

        for pt in zip(*loc[::-1]):
            pyautogui.click(pt[0] + w / 2, pt[1] + h / 2)
            logging.info(f"Clicked on template at location: {pt}")
            return

        await asyncio.sleep(interval)

async def run_batch(ldplayer_path, indices, max_emulators, service_name, service_timeout, active_instances):
    logging.info(f"Starting LDPlayer instances for service: {service_name} with indices: {indices}")
    total_batches = (len(indices) + max_emulators - 1) // max_emulators

    for batch in range(total_batches):
        start_index = batch * max_emulators
        end_index = min(start_index + max_emulators, len(indices))
        current_batch_indices = indices[start_index:end_index]

        logging.info(f"Starting batch {batch + 1}/{total_batches} for service: {service_name} with indices: {current_batch_indices}")

        # Check and close unnecessary instances
        active_indices_needed = set(current_batch_indices)
        to_close_indices = [index for index in active_instances.keys() if index not in active_indices_needed]

        logging.info(f"Active instances before cleanup: {list(active_instances.keys())}")
        logging.info(f"Active indices needed for current batch: {active_indices_needed}")
        logging.info(f"Indices to close: {to_close_indices}")

        for index in to_close_indices:
            logging.info(f"Closing unnecessary LDPlayer instance with index {index}.")
            try:
                await close_ld(ldplayer_path, index)
                del active_instances[index]
            except Exception as e:
                logging.error(f"Error closing unnecessary LDPlayer instance {index}: {e}")

        screen_width, screen_height = pyautogui.size()
        positions = [(i * SCREEN_WIDTH, 0, SCREEN_WIDTH, SCREEN_HEIGHT) for i in range(screen_width // SCREEN_WIDTH)]

        # Start or reuse LDPlayer instances
        start_tasks = []
        for i, index in enumerate(current_batch_indices):
            if index not in active_instances:
                start_tasks.append(start_ld(ldplayer_path, index, positions[i % len(positions)]))

        try:
            await asyncio.gather(*start_tasks)
        except Exception as e:
            logging.error(f"Error starting LDPlayer instances for service: {service_name}: {e}")
            continue

        # Click on templates
        template_paths = ['icon/fixld1.png', 'icon/fixld.png', 'icon/fixld3.png']
        for template_path in template_paths:
            try:
                await click_on_template(template_path, timeout=5, interval=1)
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"Error clicking on template: {e}")
                continue

        expected_devices = min(len(current_batch_indices), max_emulators)
        try:
            device_ids = await wait_for_all_devices(expected_devices, timeout=60, interval=5)
        except Exception as e:
            logging.error(f"Error waiting for devices for service: {service_name}: {e}")
            close_tasks = [close_ld(ldplayer_path, index) for index in current_batch_indices]
            await asyncio.gather(*close_tasks)
            return

        tasks = [automate_instance(ldplayer_path, index, device_id, positions[i % len(positions)], [service_name])
                 for i, (index, device_id) in enumerate(zip(current_batch_indices, device_ids))]
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logging.error(f"Error automating instances for service: {service_name}: {e}")
            continue

        logging.info(f"Completed tasks for batch {batch + 1}/{total_batches} for service: {service_name}.")

        # Update active instances
        for index in current_batch_indices:
            active_instances[index] = service_name

    logging.info(f"Completed tasks for all instances for service: {service_name}.")

async def main_loop(ldplayer_path, max_emulators, services_queue):
    active_instances = {}  # Mapping of LDPlayer indices to active services

    while True:
        current_time = time.time()
        due_services = [service for service in services_queue if current_time - service['last_run'] >= service['timeout']]
        due_services.sort(key=lambda s: s['last_run'])

        for service in due_services:
            service_name = service['name']
            service_timeout = service['timeout']
            service_indices = service['indices']

            logging.info(f"Running service: {service_name}")
            try:
                await run_batch(ldplayer_path, service_indices, max_emulators, service_name, service_timeout, active_instances)
                service['last_run'] = time.time()
            except Exception as e:
                logging.error(f"Error in main loop for service: {service_name}: {e}")
                for index in service_indices:
                    try:
                        await close_ld(ldplayer_path, index)
                    except Exception as e:
                        logging.error(f"Error closing LDPlayer instance {index} for service: {service_name}: {e}")

        # Close LDPlayer instances not needed for upcoming services
        active_indices_needed = {index for service in services_queue for index in service['indices']}
        to_close_indices = [index for index in active_instances.keys() if index not in active_indices_needed]

        logging.info(f"Active instances before cleanup: {list(active_instances.keys())}")
        logging.info(f"Active indices needed for upcoming services: {active_indices_needed}")
        logging.info(f"Indices to close: {to_close_indices}")

        for index in to_close_indices:
            logging.info(f"Closing unnecessary LDPlayer instance with index {index}.")
            try:
                await close_ld(ldplayer_path, index)
                del active_instances[index]
            except Exception as e:
                logging.error(f"Error closing unnecessary LDPlayer instance {index}: {e}")

        # Final check and cleanup of all unnecessary instances
        all_active_indices = set(active_instances.keys())

        logging.info(f"Final cleanup: Active instances before final cleanup: {all_active_indices}")

        # Close all active instances
        for index in all_active_indices:
            logging.info(f"Final cleanup: Closing unnecessary LDPlayer instance with index {index}.")
            try:
                await close_ld(ldplayer_path, index)
                del active_instances[index]
            except Exception as e:
                logging.error(f"Final cleanup: Error closing unnecessary LDPlayer instance {index}: {e}")

        logging.info("All tasks completed. Entering pause mode.")
        for service in services_queue:
            time_remaining = service['timeout'] - (time.time() - service['last_run'])
            logging.info(f"Service '{service['name']}' will restart in {time_remaining} seconds.")

        await asyncio.sleep(120)

if __name__ == "__main__":
    config = load_config()
    if config:
        ldplayer_path = config['ldplayer_path']
        max_emulators = config['max_emulators']
        services_queue = config['services_queue']
    else:
        ldplayer_path = input(r"Enter the full path to LDPlayer (example, D:\LDPlayer\LDPlayer9\dnconsole.exe): ").strip()
        if not os.path.isfile(ldplayer_path):
            logging.error(f"File {ldplayer_path} not found")
            sys.exit(1)

        max_emulators_input = input("Enter the maximum number of emulators to run at once: ")
        max_emulators = int(max_emulators_input)

        services_queue = []
        while True:
            service_name = input("Enter the service name (or type 'done' to finish): ")
            if service_name.lower() == 'done':
                break
            service_timeout = int(input(f"Enter the timeout for service {service_name} (in seconds): "))
            indices_input = input(f"Enter the LDPlayer indices for service {service_name} separated by spaces (e.g., 0 1 2): ")
            indices = [int(i) for i in indices_input.split()]
            services_queue.append({'name': service_name, 'timeout': service_timeout, 'indices': indices, 'last_run': 0})

        config_data = {
            'ldplayer_path': ldplayer_path,
            'max_emulators': max_emulators,
            'services_queue': services_queue
        }
        save_config(config_data)

    asyncio.run(main_loop(ldplayer_path, max_emulators, services_queue))
