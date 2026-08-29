# Python training Discord bot

This folder is a standalone Discord bot. GitHub Pages cannot run a persistent bot, so use a host that supports a long-running Python worker.

## Setup

1. Create or regenerate a bot token in the Discord Developer Portal.
2. Install the dependency: `pip install -r requirements.txt`
3. Set `DISCORD_BOT_TOKEN` to the bot token.
4. Optionally set `TRAINING_CHANNEL_ID` to the request channel. It defaults to `1543063952920027206`.
5. Optionally set `DATABASE_PATH` to a persistent SQLite file path.
6. Invite the bot with the `bot` and `applications.commands` scopes.
7. Start it with `python bot.py`.

The bot needs permission to view and send messages in the request channel, embed links, and send direct messages. Users can run `/request-training`; helpers can claim a request once, and the bot records the claim and DMs the learner.
