import argparse
import json
import logging
import typing
from dataclasses import dataclass

import comfyapi

import discord
from loguru import logger

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

args = parse_args()
config = load_config(args.config)

comfy = comfyapi.Client(config.comfy_url)

def default_workflow_injector(positive_prompt_key: str, negative_prompt_key: str) -> comfyapi.WorkflowCustomizer:
    def inject_prompts(workflow: typing.Dict[str, typing.Any], positive_prompt: str, negative_prompt: str) -> typing.Dict[str, typing.Any]:
        workflow[positive_prompt_key]["inputs"]["text"] = positive_prompt
        workflow[negative_prompt_key]["inputs"]["text"] = negative_prompt

        return workflow

    return inject_prompts

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)


def register_genai(name: str, workflow: typing.Dict[str, typing.Any], inject_prompts: comfyapi.WorkflowCustomizer):
    async def callback(interaction: discord.Interaction, positive_prompt: str, negative_prompt: str):
        injected_workflow = inject_prompts(workflow, positive_prompt, negative_prompt)
        resp = comfy.queue_prompt(injected_workflow)

        await interaction.response.send_message(f'Workflow {name} has been queued.', ephemeral=True)

        imgs = comfy.wait_for_image(resp.prompt_id)

        img_paths = []

        for img in imgs:
            data = comfy.get_image(img.filename, img.subfolder, img.image_type)

            img_path = f'local/output/{img.filename}'
            with open(img_path, 'wb') as fd:
                fd.write(data)
            
            img_paths.append(img_path)

        logger.debug(resp)

        await client.get_channel(interaction.channel_id).send(f'Workflow {name} - {resp.prompt_id} is done.\nPositive Prompt: {positive_prompt}\nNegative Prompt: {negative_prompt}', files=[discord.File(img) for img in img_paths])

    with_desc = discord.app_commands.describe(
        positive_prompt='What should be in the image?',
        negative_prompt='What should not be in the image?')(callback)
    tree.command(name=name)(with_desc)

@client.event
async def on_ready():
    for wf in config.workflows:
        with open(wf.file) as fd:
            decoded = json.load(fd)

        injector = default_workflow_injector(wf.positive_prompt_key, wf.negative_prompt_key)

        logger.debug("Registering workflow {}", wf.name)
        register_genai(wf.name, decoded, injector)

    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$sync') and message.author.id == config.owner_id:
        for gid in config.guild_ids:
            logger.info("Syncing guild {}", gid)
            await tree.sync(discord.Object(id=gid))

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(config.discord_token, log_handler=logging.StreamHandler(), log_level=logging.DEBUG)
