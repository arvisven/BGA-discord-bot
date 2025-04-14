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

    if command.startswith("!hello"):
        await message.channel.send("hello!")

    if command.startswith("!remove_me"):
        database.deleteUserData(message.author.id)
        await message.channel.send("User deleted!")

    #!Listen_to command handling:
    elif command.startswith("!monitor"):
        # Get url from command
        try:
            _, url_parameter = command.split(" ", 1)
        except Exception:
            await message.channel.send("Provide a URL to a board game arena table")
            return

        try:
            # Get game id from game url
            game_id = utils.extractGameId(url_parameter)

            # Get game name and current active player
            game_name, active_player_id = await webscraper.get_game_info(url_parameter)

            database.insertGameData(
                game_id, url_parameter, game_name, active_player_id, message.author.id
            )

            await message.channel.send(
                f"Monitoring to {game_name} with id: {game_id} at url: {url_parameter}"
            )
            await notifyer(bot, active_player_id, game_id)

        except Exception as e:
            logging.error(f"Error when monitoring: {e}")
            await message.channel.send(
                f"Something went wrong when trying to monitoring to game with url: {url_parameter}"
            )

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
        await channel.send(
            f"Det är din tur {mention} i {game.name}! [Länk]({game.url})"
        )


async def notify_game_removed(bot, game):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await channel.send(
        f"{game.name} med id: {game.id} är avslutat! Grattis till vinnaren!"
    )


async def notify_new_game_monitored(bot, game):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await channel.send(
        f"Found new game to monitor: {game.name} with id: {game.id} at url: {game.url}"
    )
