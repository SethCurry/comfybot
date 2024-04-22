import json
import typing

import cli
import comfyapi
import genai

import discord
from loguru import logger

args = cli.parse_args()
config = cli.load_config(args.config)

comfy = comfyapi.Client(config.comfy_url)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    for wf in config.workflows:
        with open(wf.file) as fd:
            decoded = json.load(fd)

        injector = genai.default_workflow_injector(wf.positive_prompt_key, wf.negative_prompt_key)

        logger.debug("Registering workflow {}", wf.name)

        genai.command(client, tree, comfy, wf.name, decoded, injector)

    logger.info(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == config.owner_id:
        if message.content.startswith('$sync'):
            for gid in config.guild_ids:
                logger.info("Syncing guild {}", gid)
                await tree.sync(guild=discord.Object(id=gid))
        if message.content.startswith('$unload'):
            comfy.free(unload_models=True, free_memory=True)

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(config.discord_token)
