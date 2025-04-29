import logging
from . import webscraper
from src.database import Database
import sqlite3
from . import utils
import os
from dotenv import load_dotenv


load_dotenv()
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))

database = None


def set_database(db):
    global database
    database = db


async def handle_command(bot, message):
    command = message.content.lower()

    if command.startswith("!remove_me"):
        database.deleteUserData(message.author.id)
        await message.channel.send("User deleted!")

    #!Add_user command handling
    elif command.startswith("!add_user"):
        try:
            _, bga_id = command.split(" ", 1)
        except Exception as e:
            await message.channel.send("Provide a BGA user ID")
            return

        discord_id = message.author.id

        try:
            database.insertUserData(discordId=discord_id, bgaId=bga_id)
            await message.channel.send("user added!")
        except sqlite3.IntegrityError as e:
            logging.error(f"Error when adding user: {e}")
            await message.channel.send("Discord user ID already added!")


async def notifyer(bot, bgaId, gameId):
    discord_id = database.getDiscordIdByBgaId(bgaId)
    if discord_id:
        mention = f"<@{discord_id}>"
        channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        game = database.getGameById(gameId)
        await channel.send(f"It's your turn {mention} in [{game.name}]({game.url})")


async def notify_game_removed(bot, game):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await channel.send(
        f"{game.name} with id: {game.id} is finished! Congratz to the winner!"
    )


async def notify_new_game_monitored(bot, game):
    if not database.getGameById(game.id):
        channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        await channel.send(
            f"Found new game to monitor: {game.name} with id: {game.id} at url: {game.url}"
        )
