import yaml
from pathlib import Path

appDir = Path(__file__).parent
configFilePath = appDir / "config.yaml"

with open(configFilePath, "rt") as config_file:
    configData = yaml.safe_load(config_file)


class Config:
    pass


# apply base config from config file
if configData is not None:
    for k, v in configData.items():
        setattr(Config, k, v)
