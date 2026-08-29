# Python in Practice

## Discord training bot

The Discord bot runs as a separate worker process. GitHub Pages can host the static website, but it cannot keep a Discord bot connected, so use a host that supports a persistent Python worker for the `bot` process in the `Procfile`.

Set these environment variables on the bot worker:

- `DISCORD_BOT_TOKEN`: the bot token from the Discord Developer Portal
- `TRAINING_CHANNEL_ID`: the channel that receives requests (defaults to `1543063952920027206`)
- `DATABASE_PATH`: optional path to a persistent SQLite file

Install dependencies with `pip install -r requirements.txt`, then start the bot with `python bot.py`. Invite the bot with the `bot` and `applications.commands` scopes and grant it permission to view/send messages in the configured channel, embed links, and send direct messages.

Users can run `/request-training` with their goals, Python level, availability, and helper preference. A helper can claim each request once; the bot records the claim in SQLite, updates the button with the helper's username, and DMs the requester.