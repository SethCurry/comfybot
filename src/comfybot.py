import json
import typing

import cli
import comfyapi

import discord
from loguru import logger

args = cli.parse_args()
config = cli.load_config(args.config)

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

        img_paths = []

        for img in await comfy.wait_for_image(resp.prompt_id):
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
