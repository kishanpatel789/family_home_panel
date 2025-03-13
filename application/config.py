import logging
from pathlib import Path

import yaml


app_dir = Path(__file__).parent
config_file_path = app_dir / "config.yaml"

with open(config_file_path, "rt") as config_file:
    config_data = yaml.safe_load(config_file)

    # update relative paths if needed
    config_data_weather = config_data["APP_CONFIG"]["weather"]
    if config_data_weather["cache_file_relative"]:
        config_data_weather["cache_file"] = (
            app_dir / config_data_weather["cache_file"]
        ).resolve()

    config_data_events = config_data["APP_CONFIG"]["events"]
    if config_data_events["cache_file_relative"]:
        config_data_events["cache_file"] = (
            app_dir / config_data_events["cache_file"]
        ).resolve()
    if config_data_events["key_file_relative"]:
        config_data_events["key_file"] = (
            app_dir / config_data_events["key_file"]
        ).resolve()


class Config:
    pass


# apply base config from config file
if config_data is not None:
    for k, v in config_data.items():
        setattr(Config, k, v)

# set up logging
log_file_path = app_dir / "logs/app.log"
if not log_file_path.exists():
    log_file_path.touch()

logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.info("Config loaded")
