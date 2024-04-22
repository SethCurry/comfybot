import json

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

bot = genai.Bot(client, comfy, tree, config.owner_id, config.guild_ids, logger)

for wf in config.workflows:
    with open(wf.file) as fd:
        decoded = json.load(fd)

    injector = genai.default_workflow_injector(wf.positive_prompt_key, wf.negative_prompt_key)

    logger.debug("Registering workflow {}", wf.name)

    bot.register_prompt(wf.name, decoded, injector)

bot.run(config.discord_token)
