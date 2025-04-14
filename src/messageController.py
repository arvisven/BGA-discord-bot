import logging
from . import webscraper
from src.database import Database
import sqlite3
from . import utils
import os
from dotenv import load_dotenv

database = Database("database.db")
load_dotenv()
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))


async def handleCommand(bot, message):
    command = message.content.lower()

    if command.startswith("!hello"):
        await message.channel.send("hello!")

    if command.startswith("!remove_me"):
        database.deleteUserData(message.author.id)
        await message.channel.send("User deleted!")

    if command.startswith("!remove_game"):
        try:
            _, gameId = command.split(" ", 1)
        except Exception:
            await message.channel.send("Provide a game id to be removed")
            return

        try:
            game = database.getGameById(gameId)
            database.deleteGameData(gameId)

            await message.channel.send(f"Not monitoring {game.name} with id: {game.id}")

        except Exception as e:
            logging.error(f"Error when remoing game: {e}")
            await message.channel.send(f"Could not remove game with id: {gameId}")

    #!Listen_to command handling:
    elif command.startswith("!monitor"):
        # Get url from command
        try:
            _, urlParameter = command.split(" ", 1)
        except Exception:
            await message.channel.send("Provide a URL to a board game arena table")
            return

        try:
            # Get game id from game url
            gameId = utils.extractGameId(urlParameter)

            # Get game name and current active player
            gameName, activePlayerId = await webscraper.getGameInfo(urlParameter)

            database.insertGameData(
                gameId, urlParameter, gameName, activePlayerId, message.author.id
            )

            await message.channel.send(
                f"Monitoring to {gameName} with id: {gameId} at url: {urlParameter}"
            )
            await notifyer(bot, activePlayerId, gameId)

        except Exception as e:
            logging.error(f"Error when monitoring: {e}")
            await message.channel.send(
                f"Something went wrong when trying to monitoring to game with url: {urlParameter}"
            )

    #!Add_user command handling
    elif command.startswith("!add_user"):
        try:
            _, bgaId = command.split(" ", 1)
        except Exception as e:
            await message.channel.send("Provide a BGA user ID")
            return

        discordId = message.author.id

        try:
            database.insertUserData(discordId=discordId, bgaId=bgaId)
            await message.channel.send("user added!")
        except sqlite3.IntegrityError as e:
            logging.error(f"Error when adding user: {e}")
            await message.channel.send("Discord user ID already added!")


async def notifyer(bot, bgaId, gameId):
    discordId = database.getDiscordIdByBgaId(bgaId)
    if discordId:
        mention = f"<@{discordId}>"
        channel = bot.get_channel(NOTIFY_CHANNEL_ID)
        game = database.getGameById(gameId)
        await channel.send(
            f"Det är din tur {mention} i {game.name}! [Länk]({game.url})"
        )


async def notifyGameRemoved(bot, game):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await channel.send(
        f"{game.name} med id: {game.id} är avslutat! Grattis till vinnaren!"
    )


async def notifyNewGameMonitored(bot, game):
    channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    await channel.send(
        f"Found new game to monitor: {game.name} with id: {game.id} at url: {game.url}"
    )
