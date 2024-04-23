from __future__ import annotations

import typing

import comfyapi
import discord

import loguru
logger = loguru.logger


def command(client, tree, comfy, name: str, workflow: typing.Dict[str, typing.Any], inject_prompts: comfyapi.WorkflowCustomizer):
    async def callback(interaction: discord.Interaction, positive_prompt: str, negative_prompt: str):
        injected_workflow = inject_prompts(workflow, positive_prompt, negative_prompt)
        resp = await comfy.queue_prompt(injected_workflow)

        await interaction.response.send_message(f'Workflow {name} has been queued.')

        img_paths = []

        for img in await comfy.wait_for_image(resp.prompt_id):
            data = await comfy.get_image(img.filename, img.subfolder, img.image_type)

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


def default_workflow_injector(positive_prompt_key: str, negative_prompt_key: str) -> comfyapi.WorkflowCustomizer:
    def inject_prompts(workflow: typing.Dict[str, typing.Any], positive_prompt: str, negative_prompt: str) -> typing.Dict[str, typing.Any]:
        workflow[positive_prompt_key]["inputs"]["text"] = positive_prompt
        workflow[negative_prompt_key]["inputs"]["text"] = negative_prompt

        return workflow

    return inject_prompts

class Bot:
    def __init__(
            self,
            discord_client: discord.Client,
            comfy_client: comfyapi.Client,
            command_tree: discord.app_commands.CommandTree = None,
            owner_id: int = None,
            guild_ids: typing.List[int] = list,
            bot_logger: loguru.Logger = None):
        self.__discord_client = discord_client
        self.__owner_id = owner_id
        self.__guild_ids = guild_ids

        if bot_logger is None:
            self.__logger = logger
        else:
            self.__logger = bot_logger

        if command_tree is None:
            self.__discord_tree = discord.app_commands.CommandTree(discord_client)
        else:
            self.__discord_tree = command_tree

        self.__comfy_client = comfy_client

        self.__discord_client.event(self.on_ready)
        self.__discord_client.event(self.on_message)
    
    async def on_ready(self):
        self.__logger.info("logged in as {}", self.__discord_client.user)

    async def on_message(self, message):
        if message.author == self.__discord_client.user:
            self.__logger.info("ignoring message from self")
            return

        if message.author.id == self.__owner_id:
            if message.content.startswith('$sync'):
                self.__logger.info("syncing commands")

                for gid in self.__guild_ids:
                    synced_commands = await self.__discord_tree.sync(guild=discord.Object(id=gid))

                    for i in synced_commands:
                        self.__logger.info("synced command {} for guild {}", i.name, gid)

            if message.content.startswith('$unload'):
                self.__comfy_client.free(unload_models=True, free_memory=True)

    def register_prompt(self, name: str, workflow: typing.Dict[str, typing.Any], inject_prompts: comfyapi.WorkflowCustomizer):
        command(self.__discord_client, self.__discord_tree, self.__comfy_client, name, workflow, inject_prompts)

    def run(self, token: str):
        self.__discord_client.run(token)