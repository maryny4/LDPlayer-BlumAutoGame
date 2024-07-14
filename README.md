[Contact me on Telegram if u have any problem](https://t.me/maryny4)

[![IMAGE ALT TEXT](http://img.youtube.com/vi/Sfw5QXhddK0/maxresdefault.jpg)](http://www.youtube.com/watch?v=Sfw5QXhddK0 "Video Title")
# LDPlayer Automation Script

This script automates the management of LDPlayer emulators to run and execute specific tasks. The script allows starting emulators, performing actions within them, and closing unused instances on a schedule.

## Requirements

- Python 3.x
- Python modules: asyncio, logging, pyautogui, opencv-python, numpy, Pillow
- LDPlayer

## Installation

1. Ensure Python 3.x is installed on your computer.
2. Install the required Python modules:
    ```bash
    pip install asyncio logging pyautogui opencv-python numpy pillow
    ```
3. Download and install LDPlayer from the official website.

## Configuration

1. Create a configuration file named `config.json` with the following structure:
    ```json
    {
        "ldplayer_path": "path_to_ldplayer_ldconsole.exe",
        "max_emulators": 2,
        "services_queue": [
            {
                "name": "blum_auto",
                "timeout": 86400,
                "indices": [0, 1, 2],
                "last_run": 0
            }
        ]
    }
    ```
    - `ldplayer_path`: The full path to the LDPlayer ldconsole.exe.
    - `max_emulators`: The maximum number of emulators to run simultaneously.
    - `services_queue`: A list of services to be automated.
        - `name`: The name of the service.
        - `timeout`: The time interval (in seconds) to run the service.
        - `indices`: The LDPlayer indices used by the service.
        - `last_run`: The timestamp of the last run (set to 0 initially).

2. Alternatively, you can input the configuration interactively when running the script for the first time.

## Usage

1. Run the script:
    ```bash
    python main.py
    ```
2. Follow the prompts to enter the LDPlayer path, maximum emulators, and service details if you haven't created a `config.json` file.

## Functions

- `save_config(config_data)`: Saves the configuration to `config.json`.
- `load_config()`: Loads the configuration from `config.json`.
- `click_on_template(template_path, timeout=60, interval=5)`: Finds and clicks on a template image on the screen.
- `run_batch(ldplayer_path, indices, max_emulators, service_name, service_timeout, active_instances)`: Runs a batch of emulators for a specific service.
- `main_loop(ldplayer_path, max_emulators, services_queue)`: The main loop that manages the scheduling and execution of services.

## Logging

The script logs information and errors to the standard output. Adjust the logging level and format in the `logging.basicConfig` configuration as needed.

## License

This project is licensed under the MIT License.
