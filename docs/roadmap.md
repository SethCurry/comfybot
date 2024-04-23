# Roadmap

## P2P Generation

- Allow users to register a ComfyUI instance that jobs can be sent to.
- Allow restricting generation based on participation in this
  - Multiple accounting modes
    - Only allow users that have a ComfyUI instance registered to run jobs
    - Same with limited credits for people without a registered instance
    - "Karma" system, where members of the channel can use emotes to "upvote" a generated image
      - The person generating it can then use these upvotes to generate more images

### Open Questions

- How to handle assets?
  - Models will need to be downloaded
  - Could wrap the prompt in a JSON object that includes dependencies

## Queued Generation

Allow disabling generation under certain conditions

- VRAM usage already high
- Particular processes are running
  - E.g. video games, so we don't run if a process starting with `C:/$pathToSteam/.*` is running
