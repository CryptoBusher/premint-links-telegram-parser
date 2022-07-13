"""
Script for parsing active unique premint links from telegram channels history.
"""

from sys import stderr
from concurrent.futures import ThreadPoolExecutor

from loguru import logger
from selenium import webdriver

from helpers import FileManager, PremintEvent

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> |"
                          "<cyan>{line}</cyan> - <white>{message}</white>")


def init_selenium_driver():
    """
    Init selenium webdriver for parsing data.
    :return: selenium driver object
    """

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    _driver = webdriver.Chrome(options=chrome_options)
    return _driver


def parse_unique_links(_telegram_messages: dict):
    """
    Parses unique premint links from all telegram messages.
    :param _telegram_messages: dict
    :returns list
    """

    _premint_links = []
    for message in _telegram_messages:
        text = message['text']
        if type(text) == list:
            for subtext in text:
                if type(subtext) == dict:
                    if subtext['type'] == 'link':
                        if 'premint.xyz/' in subtext['text']:
                            _premint_links.append(subtext['text'])
                    elif subtext['type'] == 'text_link':
                        if 'premint.xyz/' in subtext['href']:
                            _premint_links.append(subtext['href'])

    premint_links_no_duplicates_list = []
    for link in _premint_links:
        if link[0:7] == 'premint':
            link = 'https://www.' + link
        elif link[0:11] == 'www.premint':
            link = 'https://' + link

        if link not in premint_links_no_duplicates_list:
            premint_links_no_duplicates_list.append(link)

    return premint_links_no_duplicates_list


def save_premint_event_data(_premint_event):
    """
    Saves all required data to different txt files if premint event is active.
    :param _premint_event: PremintEvent
    """

    try:
        file_manager.append_txt_file('data/final_summary_data', f'{_premint_event.link},'
                                                                f'{_premint_event.twitter_links},'
                                                                f'{_premint_event.discord_links}')

        file_manager.append_txt_file('data/active_premint_links', _premint_event.link)

        for twitter_link in _premint_event.twitter_links:
            file_manager.append_txt_file('data/twitters_to_subscribe', twitter_link)

        for discord_link in _premint_event.discord_links:
            file_manager.append_txt_file('data/discords_to_enter', discord_link)
        return {
            'success': True
        }

    except Exception as e:
        return {
            'success': False,
            'error': e
        }


def user_menu():
    """
    Simple user menu to handle input data.
    :return: _total_threads: int, _working_mode: int, _ignore_links_mode: str
    """

    _total_threads = int(input('-> Enter amount of threads: '))
    _working_mode = int(input('-> Select links origin file\n'
                              '\t1: Telegram history json file (data/result.json)\n'
                              '\t2: My own list of links (data/my_links.txt)\n'
                              '\tEnter number 1/2: '))
    _ignore_links_mode = str(input('-> Take into account links from links to ignore file '
                                   'data/links_to_ignore.txt)? y/n: '))

    return _total_threads, _working_mode, _ignore_links_mode


if __name__ == "__main__":
    total_threads, working_mode, ignore_links_mode = user_menu()
    file_manager = FileManager()

    telegram_raw_data = file_manager.read_json_file('data/result')
    telegram_messages = telegram_raw_data['messages']
    unique_premint_links = []

    if working_mode == 1:
        unique_premint_links = parse_unique_links(telegram_messages)
    elif working_mode == 2:
        all_premint_links = file_manager.read_txt_file('data/my_links')
        [unique_premint_links.append(x) for x in all_premint_links if x not in unique_premint_links]

    if ignore_links_mode == 'y':
        links_to_ignore = file_manager.read_txt_file('data/links_to_ignore')
        [unique_premint_links.remove(x) for x in links_to_ignore if x in unique_premint_links]

    logger.success(f'Parsed {len(unique_premint_links)} unique premint links from result.json file.')

    premint_event_objects = []
    [premint_event_objects.append(PremintEvent(x)) for x in unique_premint_links]

    def my_worker(premint_event):
        """
        Worker for multithreading, contains main logic.
        """

        driver = init_selenium_driver()
        premint_event.parse_event_data(driver)

        if premint_event.is_active:
            result = save_premint_event_data(premint_event)
            if result['success']:
                logger.success('Saved data about active premint event.')
            else:
                logger.error(f'Error occurred: {result["error"]}')

    with ThreadPoolExecutor(max_workers=total_threads) as executor:
        executor.map(my_worker, premint_event_objects)
