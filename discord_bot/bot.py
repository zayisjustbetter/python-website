import os
import sqlite3
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

DATABASE = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "python_practice.sqlite3"))
CHANNEL_ID = int(os.environ.get("TRAINING_CHANNEL_ID", "1543063952920027206"))
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()


def get_db():
    database = sqlite3.connect(DATABASE)
    database.row_factory = sqlite3.Row
    return database


def init_db():
    database = get_db()
    database.execute(
        """
        CREATE TABLE IF NOT EXISTS training_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL UNIQUE,
            requester_id INTEGER NOT NULL,
            requester_name TEXT NOT NULL,
            goals TEXT NOT NULL,
            level TEXT NOT NULL,
            availability TEXT NOT NULL,
            helper_preference TEXT NOT NULL,
            claimed_by INTEGER,
            claimed_name TEXT,
            claimed_at TEXT
        )
        """
    )
    database.commit()
    database.close()


def create_request(message_id, requester, goals, level, availability, helper_preference):
    database = get_db()
    cursor = database.execute(
        """
        INSERT INTO training_requests
        (message_id, requester_id, requester_name, goals, level, availability, helper_preference)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (message_id, requester.id, str(requester), goals, level, availability, helper_preference),
    )
    request_id = cursor.lastrowid
    database.commit()
    database.close()
    return request_id


def claim_request(message_id, helper):
    database = get_db()
    claimed_at = datetime.now(timezone.utc).isoformat()
    cursor = database.execute(
        """
        UPDATE training_requests
        SET claimed_by = ?, claimed_name = ?, claimed_at = ?
        WHERE message_id = ? AND claimed_by IS NULL
        """,
        (helper.id, str(helper), claimed_at, message_id),
    )
    database.commit()
    result = database.execute("SELECT * FROM training_requests WHERE message_id = ?", (message_id,)).fetchone()
    database.close()
    return result if cursor.rowcount else None


def pending_message_ids():
    database = get_db()
    rows = database.execute("SELECT message_id FROM training_requests WHERE claimed_by IS NULL").fetchall()
    database.close()
    return [row["message_id"] for row in rows]


class ClaimTrainingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim this request", style=discord.ButtonStyle.success, custom_id="training:claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        request_record = claim_request(interaction.message.id, interaction.user)
        if request_record is None:
            await interaction.followup.send("This request has already been claimed.", ephemeral=True)
            return

        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        await interaction.message.edit(view=self)
        try:
            requester = await interaction.client.fetch_user(request_record["requester_id"])
            await requester.send(
                f"Hi {request_record['requester_name']}! {interaction.user.display_name} will help you learn Python. "
                "They will get in touch with you soon."
            )
        except discord.HTTPException:
            await interaction.followup.send(
                f"Claimed by {interaction.user.display_name}, but I could not DM the requester.", ephemeral=True
            )
            return
        await interaction.followup.send(
            f"Claimed by {interaction.user.display_name}. The requester has been notified by DM.", ephemeral=True
        )


class TrainingBot(commands.Bot):
    async def setup_hook(self):
        init_db()
        for message_id in pending_message_ids():
            self.add_view(ClaimTrainingView(), message_id=message_id)
        await self.tree.sync()


intents = discord.Intents.default()
bot = TrainingBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Training bot logged in as {bot.user} | channel {CHANNEL_ID}")


@bot.tree.command(name="request-training", description="Request help learning Python")
@app_commands.describe(
    goals="What would you like to learn or build?",
    level="How advanced are you in Python?",
    availability="When are you usually available?",
    helper_preference="Trainer, volunteer helper, owner, or no preference",
)
async def request_training(
    interaction: discord.Interaction,
    goals: str,
    level: str,
    availability: str,
    helper_preference: str,
):
    values = (goals.strip(), level.strip(), availability.strip(), helper_preference.strip())
    if any(not value for value in values) or any(len(value) > 1_000 for value in values):
        await interaction.response.send_message("Please provide complete answers under 1,000 characters each.", ephemeral=True)
        return

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
        except discord.HTTPException:
            await interaction.response.send_message("The training channel is not available right now.", ephemeral=True)
            return
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("The configured training channel is not a text channel.", ephemeral=True)
        return

    embed = discord.Embed(title="Python training request", description=goals, color=0xEF765F)
    embed.add_field(name="Learner", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
    embed.add_field(name="Python level", value=level, inline=True)
    embed.add_field(name="Helper preference", value=helper_preference, inline=True)
    embed.add_field(name="Availability", value=availability, inline=False)
    embed.set_footer(text="One helper can claim this request")
    message = await channel.send(embed=embed, view=ClaimTrainingView())
    create_request(message.id, interaction.user, goals, level, availability, helper_preference)
    await interaction.response.send_message("Your training request has been posted. A helper will contact you by DM.", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("Set DISCORD_BOT_TOKEN before starting the bot.")
    init_db()
    bot.run(TOKEN)
