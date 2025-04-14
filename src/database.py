import sqlite3
import logging
from collections import namedtuple

Game = namedtuple("Game", ["id", "url", "name", "activePlayerId"])


class Game:
    def __init__(self, id, url, name, activePlayerId):
        self.id = id
        self.url = url
        self.name = name
        self.activePlayerId = activePlayerId


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def createTables(self):
        self.connect()

        # Create the user_data table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_data (
                discord_id INTEGER PRIMARY KEY,
                bga_id INTEGER
            )
        """
        )

        # Create the game table with a foreign key to user_data
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_data (
                id INTEGER PRIMARY KEY,
                url STRING,
                game_name STRING,
                active_player_id INTEGER NULL
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_games (
                discord_id INTEGER,
                game_id INTEGER,
                PRIMARY KEY (discord_id, game_id)
            )
            """
        )

        self.conn.commit()

    def insertUserData(self, discordId, bgaId):
        self.connect()
        try:
            self.cursor.execute(
                "INSERT INTO user_data (discord_id, bga_id) VALUES (?, ?)",
                (discordId, bgaId),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
        finally:
            self.close()

    def deleteUserData(self, discord_id):
        self.connect()
        try:
            self.cursor.execute(
                "DELETE FROM user_data WHERE discord_id = ?", (discord_id,)
            )
            self.conn.commit()

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")

        finally:
            self.close()

    def getDiscordIdByBgaId(self, bga_id):
        self.connect()
        try:
            self.cursor.execute(
                "SELECT discord_id FROM user_data WHERE bga_id = ?", (bga_id,)
            )
            result = self.cursor.fetchone()
            if result:
                discord_id = result[0]
                return discord_id

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            self.close()

    def insertGameData(self, id, url, gameName, activePlayerId, discordId):
        self.connect()
        try:
            self.cursor.execute(
                "INSERT INTO game_data (id, url, game_name, active_player_id) VALUES (?, ?, ?, ?)",
                (id, url, gameName, activePlayerId),
            )

            # If a discordId is provided, associate the user with the game
            if discordId:
                self.cursor.execute(
                    "INSERT INTO user_games (discord_id, game_id) VALUES (?, ?)",
                    (discordId, id),
                )

            self.conn.commit()
            return Game(id, url, gameName, activePlayerId)

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
        finally:
            self.close()

    def deleteGameData(self, id):
        self.connect()
        try:
            self.cursor.execute("DELETE FROM game_data WHERE id = ?", (id,))
            self.conn.commit()

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")

        finally:
            self.close()

    def updateActivePlayer(self, id, activePlayerId):
        self.connect()
        try:
            self.cursor.execute(
                "UPDATE game_data SET active_player_id = ? WHERE id = ?",
                (activePlayerId, id),
            )
            self.conn.commit()

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")

        finally:
            self.close()

    def getActivePlayer(self, id):
        self.connect()
        try:
            self.cursor.execute(
                "SELECT active_player_id FROM game_data WHERE id = ?", (id,)
            )
            result = self.cursor.fetchone()
            if result:
                active_player_id = result[0]
                return active_player_id

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")

        finally:
            self.close()

    def getGameById(self, game_id):
        self.connect()
        try:
            self.cursor.execute(
                "SELECT id, url, game_name, active_player_id FROM game_data WHERE id = ?",
                (game_id,),
            )
            result = self.cursor.fetchone()

            if result:
                game = Game(
                    id=result[0],
                    url=result[1],
                    name=result[2],
                    activePlayerId=result[3],
                )
                return game
            else:
                logging.error(f"No data found for game ID {game_id}")
                return None

        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            return None

        finally:
            self.close()

    def getAllGames(self):
        self.connect()
        try:
            self.cursor.execute(
                "SELECT id, url, game_name, active_player_id FROM game_data"
            )
            all_games = self.cursor.fetchall()

            Game = namedtuple("Game", ["id", "url", "name", "activePlayerId"])

            game_objects = [Game(*game_data) for game_data in all_games]

            return game_objects
        finally:
            self.close()

    def getAllBgaIds(self):
        self.connect()
        try:
            self.cursor.execute("SELECT bga_id FROM user_data")
            rows = self.cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")

        finally:
            self.close()

    def getAllUsers(self):
        self.connect()
        try:
            self.cursor.execute("SELECT discord_id, bga_id FROM user_data")
            all_users = self.cursor.fetchall()

            User = namedtuple("User", ["discord_id", "bga_id"])

            user_objects = [User(*user_data) for user_data in all_users]

            return user_objects
        finally:
            self.close()

    def getGameIdsForUser(self, discord_id):
        self.connect()
        try:
            self.cursor.execute(
                "SELECT game_id FROM user_games WHERE discord_id = ?", (discord_id,)
            )
            rows = self.cursor.fetchall()
            game_ids = [row[0] for row in rows]
            return game_ids
        except sqlite3.Error as e:
            logging.error(f"SQLite error: {e}")
            return []
        finally:
            self.close()

    def close(self):
        if self.conn:
            self.conn.close()
