import yaml
from pathlib import Path

app_dir = Path(__file__).parent
config_file_path = app_dir / "config.yaml"

with open(config_file_path, "rt") as config_file:
    config_data = yaml.safe_load(config_file)

    # update relative paths if needed
    config_data_weather = config_data["API_CONFIG"]["weather"]
    if config_data_weather["cache_file_relative"]:
        _weather_cache_file_path = app_dir / config_data_weather["cache_file"]
        _weather_cache_file_path = _weather_cache_file_path.resolve()
        config_data_weather["cache_file"] = _weather_cache_file_path


class Config:
    pass


# apply base config from config file
if config_data is not None:
    for k, v in config_data.items():
        setattr(Config, k, v)
