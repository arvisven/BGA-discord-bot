import logging
from discord.ext import tasks
from . import webscraper
from src.database import Database
from . import messageController
import asyncio
from asyncio import Lock

db_lock = Lock()

database = None


def set_database(db):
    global database
    database = db


async def find_new_games(bot, user):
    logging.info(f"Finding all games for player: {user} to check for new ones")
    found_games = await webscraper.get_current_table_ids(user.bga_id)
    if not found_games:
        log_no_games_found(user)
    else:
        log_games_found(user, found_games)
        await check_for_new_games(bot, user, found_games)


async def check_for_new_games(bot, user, found_games):
    current_games_monitored = database.getGameIdsForUser(user.discord_id)
    logging.info(f"Current games monitored found: {current_games_monitored}")

    new_games = await filter_new_games(found_games, current_games_monitored)

    if new_games:
        logging.info(f"New game IDs found: {new_games}")
        for new_game in new_games:
            await process_new_game(bot, user, new_game)
    else:
        logging.info("No new games found.")


async def filter_new_games(found_games, current_games_monitored):
    return [
        game
        for game in found_games
        if int(game["game_id"]) not in current_games_monitored
    ]


async def process_new_game(bot, user, new_game):
    async with db_lock:
        try:
            game_id = new_game["game_id"]
            game_url = new_game["full_url"]
            game_name, active_player_id = await webscraper.get_game_info(game_url)
            game_obj = database.insertGameData(
                game_id, game_url, game_name, active_player_id, user.discord_id
            )
            await messageController.notify_new_game_monitored(bot, game_obj)
        except Exception as e:
            logging.error(f"Error inserting new game {new_game}: {e}")


# Fetching active player id for a game entity
# If no active player id was found:
#   1. Do new request to check for game results (game has ended)
#   2. If game didn't end, keep monitoring the game until active player is found or game ended.
#
# If the fetched player id is the same as last time, do nothing
#
# If the fetched player id is new, update game entity with new active player id and notify discord user
async def process_game(bot, game):
    logging.info(f"Fetching active player for game: {game.name} with ID: {game.id}")
    active_player_id = await webscraper.fetch_active_player(game.url)
    previous_active_player_id = database.getActivePlayer(game.id)
    logging.info(f"Active player ID: {active_player_id}")
    if active_player_id == None:
        logging.info("No active player ID found. Checking if the game has ended")
        if await webscraper.check_if_game_ended(game.url):
            logging.info("Game results list found, removing game from monitoring")
            messageController.notify_game_removed(bot, game)
            database.deleteGameData(game.id)

        else:
            logging.info("Game results list not found. Keep monitoring game..")

    elif active_player_id == previous_active_player_id:
        logging.info(f"No change of active player with ID: {active_player_id}")

    else:
        logging.info(
            f"New active player in game: {game.id} New player: {active_player_id} Previous active player: {previous_active_player_id}"
        )
        database.updateActivePlayer(game.id, active_player_id)
        await messageController.notifyer(bot, active_player_id, game.id)


# Task for fetching new games
@tasks.loop(minutes=15)
async def process_find_new_games(bot):
    users = database.getAllUsers()
    logging.info(f"Players: {users}")
    await asyncio.gather(*(find_new_games(bot, user) for user in users))


# Task for fetching active player ids and update database if active player changed
@tasks.loop(minutes=1)
async def process_games(bot):
    games = database.getAllGames()
    logging.info(f"Games: {games}")

    for game in games:
        await process_game(bot, game)


def log_no_games_found(user):
    logging.info(f"Player with ID {user} has no ongoing games")


def log_games_found(user, foundGames):
    logging.info(f"Games found for player {user}: {foundGames}")
