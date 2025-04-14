import logging
from discord.ext import tasks
from . import webscraper
from src.database import Database
from . import messageController

database = Database("database.db")


async def findNewGames(bot, user):
    logging.info(f"Finding all games for player: {user} to check for new ones")
    foundGames = await webscraper.get_current_table_ids(user.bga_id)
    if foundGames == None:
        logging.info(f"Player with id {user} has no ongoing games")
    else:
        logging.info(f"Games found: {foundGames}")
        await checkForNewGames(bot, user, foundGames)


async def checkForNewGames(bot, user, foundGames):
    currentGamesMonitored = database.getGameIdsForUser(user.discord_id)
    logging.info(f"currentGamesMonitored found: {currentGamesMonitored}")

    new_games = [
        game for game in foundGames if int(game["game_id"]) not in currentGamesMonitored
    ]

    if new_games:
        print("New game IDs found:", new_games)
        for game in new_games:
            game_id = game["game_id"]
            game_url = game["full_url"]
            game_name, active_player_id = await webscraper.getGameInfo(game_url)
            game = database.insertGameData(
                game_id, game_url, game_name, active_player_id, user.discord_id
            )
            await messageController.notifyNewGameMonitored(bot, game)

    else:
        print("No new games found.")


# Fetching active player id for a game entity
# If no active player id was found:
#   1. Do new request to check for game results (game has ended)
#   2. If game didn't end, keep monitoring the game until active player is found or game ended.
#
# If the fetched player id is the same as last time, do nothing
#
# If the fetched player id is new, update game entity with new active player id and notify discord user
async def processGame(bot, game):
    logging.info(f"Fetching active player for game: {game.name} with id: {game.id}")
    activePlayerId = await webscraper.fetchActivePlayer(game.url)
    previousActivePlayerId = database.getActivePlayer(game.id)
    logging.info(f"Active player id: {activePlayerId}")
    if activePlayerId == None:
        logging.info("No active player id found. Checking if the game has ended")
        if await webscraper.checkIfGameEnded(game.url):
            logging.info("Game results list found, removing game from monitoring")
            messageController.notifyGameRemoved(bot, game)
            database.deleteGameData(game.id)

        else:
            logging.info("Game results list not found. Keep monitoring game..")

    elif activePlayerId == previousActivePlayerId:
        logging.info(f"No change of active player with id: {activePlayerId}")

    else:
        logging.info(
            f"New active player in game: {game.id} New player: {activePlayerId} Previous active player: {previousActivePlayerId}"
        )
        database.updateActivePlayer(game.id, activePlayerId)
        await messageController.notifyer(bot, activePlayerId, game.id)


# Task for fetching new games
@tasks.loop(minutes=1)
async def processFindNewGames(bot):
    users = database.getAllUsers()
    logging.info(f"Players: {users}")

    for user in users:
        await findNewGames(bot, user)


# Task for fetching active player ids and update database if active player changed
@tasks.loop(minutes=1)
async def processGames(bot):
    games = database.getAllGames()
    logging.info(f"Games: {games}")

    for game in games:
        await processGame(bot, game)
