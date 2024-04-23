# comfybot

`comfybot` is a Discord bot for generating images using ComfyUI.

## Installation

Currently, only source installations are supported.

Before installing ComfyBot, you will need to create
a Discord bot and invite it to your server. discord.py
provides [some excellent instructions](https://discordpy.readthedocs.io/en/stable/discord.html) for doing so.

### From Source

First, clone the repository:

```sh
git clone https://github.com/SethCurry/comfybot
```

Then, install the dependencies:

```sh
cd comfybot
poetry update
```

Then create a configuration file wherever you want. Here is an example config file:

```json
{
  // The Discord ID of the user that owns the bot.
  // This is used for acces control to the "$sync"
  // command.
  "owner_id": 12345,

  // The URL where ComfyUI is hosted.
  // This is the URL that auto-opens when ComfyUI starts.
  "comfy_url": "http://localhost:8188",

  // The Discord token for the bot's Discord account.
  "discord_token": "your_discord_token_here",

  // A list of Discord guild IDs that the bot will install
  // commands into.
  "guild_ids": [12345, 6789],

  // The list of ComfyUI workflows that the bot will
  // install commands for.
  "workflows": [
    {
      // The name of the slash command that will be
      // created.
      //
      // E.g. this will create a /somename command.
      "name": "somename",

      // The path to the ComfyUI workflow JSON file.
      // Note: This need to be saved with the "Save API"
      // button, not the regular Save button.
      "file": "path/to/workflow.json",

      // The key for the positive prompt in the workflow
      // JSON file.  This is typically a number wrapped
      // in a string.
      "positive_prompt_key": "4",

      // The key for the negative prompt in the workflow
      // JSON file.  This is typically a number wrapped
      // in a string.
      "negative_prompt_key": "5"
    },
    {
      "name": "otherworkflow",
      "file": "path/to/otherworkflow.json",
      "positive_prompt_key": "1",
      "negative_prompt_key": "9"
    }
  ]
}
```

Finally, run the bot:

```sh
cd src
poetry run python comfybot.py -- -c /path/to/config.json
```

When the bot joins your server, send a message in any
channel it can see with the text `$sync`. This will
install the bot's commands into the server.

You will need to send this `$sync` message any time you
change the commands that Comfybot should install, e.g.
when you add a new workflow or rename an existing one.

## Running
