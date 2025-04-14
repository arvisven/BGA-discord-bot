import logging
import requests
import re
from . import utils
from playwright.async_api import async_playwright
from urllib.parse import urljoin

BASE_URL = "https://sv.boardgamearena.com"


async def get_current_table_ids(player_id: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a new page to get the list of table IDs
        page = await browser.new_page()
        await page.goto(
            f"{BASE_URL}/playertables?player={player_id}",
            wait_until="networkidle",
        )
        await page.wait_for_selector(".bga-table-list-item__background")

        # Get all links from the element containing table ids
        table_links = await page.eval_on_selector_all(
            'div.bga-table-list-item__background a[href*="?table="]',
            "els => els.map(el => el.href)",
        )
        # Extract table ids from the hrefs
        table_ids = list(
            {
                match.group(1)
                for link in table_links
                if (match := re.search(r"table=(\d+)", link))
            }
        )
        await page.close()  # We're done with the player tables page

        # Prepare the results list.
        results = []

        # For each table, load the corresponding game page to scrape the full URL
        for game_id in table_ids:
            new_page = await browser.new_page()
            await new_page.goto(
                f"{BASE_URL}/table?table={game_id}",
                wait_until="networkidle",
            )

            # Try to locate the element with id 'view_end_btn'
            element = await new_page.query_selector("a#view_end_btn")
            if element is not None:
                href_value = await element.get_attribute("href")
                full_url = urljoin(BASE_URL, href_value)
            else:
                full_url = None

            results.append({"game_id": game_id, "full_url": full_url})
            await new_page.close()

        await browser.close()
        return results


async def fetchActivePlayer(url):
    r = requests.get(url).text

    pattern = re.compile(r'"active_player":"(\d+)"')
    result = pattern.search(r)

    if result:
        active_player_value = result.group(1)
        return int(active_player_value)


async def checkIfGameEnded(url):
    r = requests.get(url).text
    # Checking if 1° is in the text, this occurs when a list of results is avaiable
    match = re.search(r"1°", r)

    if match:
        return True
    else:
        return False


async def getGameInfo(url):
    r = requests.get(url).text

    gameName = re.search(r'completesetup\([^,]+,\s*("[^"]+")', r)
    activePlayerIdPattern = re.compile(r'"active_player":"(\d+)"')
    resultActivePlayerId = activePlayerIdPattern.search(r)

    if gameName and resultActivePlayerId:
        gameTitle = gameName.group(1)
        convertedGameTitle = utils.convertHtmlEntitiesToCharacters(gameTitle)
        activePlayerId = resultActivePlayerId.group(1)
        logging.info(
            f"Found game title: {convertedGameTitle} \nFound active player: {activePlayerId}"
        )
        return convertedGameTitle, activePlayerId
    else:
        logging.error(
            f"Failed to fetch game info:\nGame name: {gameName}\nActive Player Id: {resultActivePlayerId}"
        )


async def getGameTitle(url):
    page_content = requests.get(url).text

    # Extract the game name from the <title> tag
    title_match = re.search(r"<title>(.*?)</title>", page_content, re.IGNORECASE)
    if title_match:
        full_title = title_match.group(1).strip()
        # Try common delimiters to isolate the game name.
        if " - " in full_title:
            game_name_raw = full_title.split(" - ")[0].strip()
        elif "|" in full_title:
            game_name_raw = full_title.split("|")[0].strip()
        elif "#" in full_title:
            game_name_raw = full_title.split("#")[0].strip()
        else:
            game_name_raw = full_title

        # Convert HTML entities if necessary
        convertedGameTitle = utils.convertHtmlEntitiesToCharacters(game_name_raw)
    else:
        logging.error("Failed to extract game title from <title> tag.")
        return None

    return convertedGameTitle
