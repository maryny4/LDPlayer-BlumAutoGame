import subprocess
import logging
import asyncio
import time
from utils import get_adb_device_ids, move_and_resize_window


async def start_ld(ldplayer_path, index, position):
    logging.info(f"Starting LDPlayer instance with index {index}.")
    process = subprocess.Popen([ldplayer_path, "launch", "--index", str(index)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        logging.error(f"Failed to start LDPlayer instance {index}. Error: {stderr.decode().strip()}")
    else:
        logging.info(f"LDPlayer instance {index} started successfully.")
    await asyncio.sleep(1)
    await move_and_resize_window(index, position)

async def close_ld(ldplayer_path, index):
    """Close LDPlayer instance."""
    process = subprocess.Popen([ldplayer_path, "quit", "--index", str(index)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        logging.error(f"Failed to close LDPlayer instance {index}. Error: {stderr.decode().strip()}")
    else:
        logging.info(f"LDPlayer instance {index} closed successfully.")


async def wait_for_all_devices(expected_count, timeout=60, interval=5):
    """Wait for all devices to come online, checking at regular intervals."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        device_ids = get_adb_device_ids()
        if len(device_ids) == expected_count:
            logging.info(f"All expected devices are online: {device_ids}")
            return device_ids
        logging.info(f"Expected {expected_count} devices, but found {len(device_ids)}. Retrying in {interval} seconds...")
        await asyncio.sleep(interval)
    logging.error(f"Mismatch between the number of LDPlayer instances and ADB devices after {timeout} seconds.")
    raise Exception("Timeout waiting for devices to come online.")

