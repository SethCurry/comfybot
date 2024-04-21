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
    with open(config_path, 'r') as fd:
        config = json.load(fd)
    
    return Config(
        owner_id=config['owner_id'],
        comfy_url=config['comfy_url'],
        discord_token=config['discord_token'],
        guild_ids=config['guild_ids'],
        workflows=[WorkflowConfig(**wf) for wf in config['workflows']])


def parse_args():
    parser = argparse.ArgumentParser(description='Comfy Discord bot')
    parser.add_argument('-c', '--config', default="comfybot.json")

    return parser.parse_args()
