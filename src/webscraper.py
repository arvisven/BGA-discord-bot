import logging
import requests
import re
from . import utils
from playwright.async_api import async_playwright
from urllib.parse import urljoin

BASE_URL = "https://boardgamearena.com"


async def get_current_table_ids(player_id: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()
        await page.goto(
            f"{BASE_URL}/playertables?player={player_id}",
            wait_until="networkidle",
        )
        await page.wait_for_selector(".bga-table-list-item__background")

        table_links = await page.eval_on_selector_all(
            'div.bga-table-list-item__background a[href*="?table="]',
            "els => els.map(el => el.href)",
        )

        table_ids = list(
            {
                match.group(1)
                for link in table_links
                if (match := re.search(r"table=(\d+)", link))
            }
        )
        await page.close()

        results = []

        for game_id in table_ids:
            new_page = await browser.new_page()
            await new_page.goto(
                f"{BASE_URL}/table?table={game_id}",
                wait_until="networkidle",
            )

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


async def fetch_active_player(url):
    r = requests.get(url).text

    pattern = re.compile(r'"active_player":"(\d+)"')
    result = pattern.search(r)

    if result:
        active_player_value = result.group(1)
        return int(active_player_value)


async def check_if_game_ended(url):
    r = requests.get(url).text
    # Checking if ° is in the text, this occurs when a list of results is avaiable or if the game is abandoned
    match = re.search(r"°", r)

    if match:
        return True
    else:
        return False


async def get_game_info(url):
    r = requests.get(url).text

    game_name = re.search(r'completesetup\([^,]+,\s*("[^"]+")', r)
    active_player_id_pattern = re.compile(r'"active_player":"(\d+)"')
    result_active_player_id = active_player_id_pattern.search(r)

    if game_name and result_active_player_id:
        gameTitle = game_name.group(1)
        converted_game_title = utils.convertHtmlEntitiesToCharacters(gameTitle)
        active_player_id = result_active_player_id.group(1)
        logging.info(
            f"Found game title: {converted_game_title} \nFound active player: {active_player_id}"
        )
        return converted_game_title, active_player_id
    else:
        logging.error(
            f"Failed to fetch game info:\nGame name: {game_name}\nActive Player ID: {result_active_player_id}"
        )
