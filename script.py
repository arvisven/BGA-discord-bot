from src import loggingConfig
import logging
import os
from dotenv import load_dotenv
from src import messageController
import discord
from discord.ext import commands
from src.database import Database
from src import taskService


def create_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    return bot


def main():
    load_dotenv()
    loggingConfig.setupLogging()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        logging.error("DISCORD_TOKEN is not set in the environment variables.")
        exit(1)

    database = Database("database.db")
    messageController.set_database(database)
    taskService.set_database(database)
    bot = create_bot()

    @bot.event
    async def on_ready():
        logging.info(f"We have logged in as {bot.user}")
        database.createTables()
        taskService.process_games.start(bot)
        taskService.process_find_new_games.start(bot)

    @bot.event
    async def on_message(message):
        if not message.author.bot:
            await messageController.handle_command(bot, message)

    try:
        bot.run(TOKEN)
    finally:
        logging.info("Closing down.")
        database.close()


if __name__ == "__main__":
    main()
