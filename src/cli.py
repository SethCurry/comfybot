import argparse
import json
import typing

from dataclasses import dataclass

@dataclass
class WorkflowConfig:
    name: str
    file: str
    positive_prompt_key: str
    negative_prompt_key: str


@dataclass
class Config:
    owner_id: int
    comfy_url: str
    discord_token: str
    guild_ids: typing.List[int]
    workflows: typing.List[WorkflowConfig]


def load_config(config_path: str) -> Config:
    """Attempts to load the configuration file from the given path.
    
    load_config attempts to load the provided path as a JSON
    configuration file for comfybot.  It does not attempt to validate
    the parsed config.
    
    Args:
        config_path (str): The path to the configuration file.
    
    Returns:
        Config: The parsed configuration.
    
    """
    with open(config_path, 'r') as fd:
        config = json.load(fd)
    
    return Config(
        owner_id=config['owner_id'],
        comfy_url=config['comfy_url'],
        discord_token=config['discord_token'],
        guild_ids=config['guild_ids'],
        workflows=[WorkflowConfig(**wf) for wf in config['workflows']])

@dataclass
class Arguments:
    config: str


def parse_args() -> Arguments:
    """Parses the CLI flags and returns the parsed arguments.
    
    Returns:
        Arguments: The parsed arguments.

    """
    parser = argparse.ArgumentParser(description='Comfy Discord bot')
    parser.add_argument('-c', '--config', default="comfybot.json")

    args = parser.parse_args()

    return Arguments(config=args.config)
