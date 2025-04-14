import logging


def setupLogging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("bot.log"),
        ],
    )
    logging.getLogger("discord").setLevel(logging.ERROR)
