"""
Classes for executing operations with premint website.
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup


class PremintWebsiteInterface:
    """
    Class that stores all paths to premint website elements for easy access.
    """

    def __init__(self):
        self.heading_div_xpath = '//*[@id="st-container"]/div/div/div/section[2]/div/div/div[2]/form/div/div[1]/div[1]'
        self.requirements_ul_xpath =\
            '//*[@id="st-container"]/div/div/div/section[2]/div/div/div[2]/form/div'


class PremintEvent:
    """
    Class that stores all required info regarding premint event.
    """

    def __init__(self, link):
        self.link = link
        self.is_active = None
        self.discord_links = []
        self.twitter_links = []
        self.balance_required = None

    def parse_event_data(self, _driver):
        """
        Function that parses all missing data for a specific premint event.
        :return: bool
        """

        interface = PremintWebsiteInterface()
        wait = WebDriverWait(_driver, 30)
        _driver.get(self.link)

        try:
            event_status = wait.until(ec.presence_of_element_located((By.XPATH, interface.heading_div_xpath))) \
                .get_attribute('innerHTML').strip()
        except:
            self.is_active = False
            return False

        if event_status != 'Register':
            self.is_active = False
            return False
        else:
            self.is_active = True
            requirements_ul = wait.until(ec.presence_of_element_located((By.XPATH, interface.requirements_ul_xpath))) \
                .get_attribute('innerHTML')

            parser = 'html.parser'
            soup = BeautifulSoup(requirements_ul, parser)
            for link in soup.find_all('a', href=True):
                url = link['href']
                if 'twitter' in url:
                    self.twitter_links.append(url)
                elif 'discord' in url:
                    self.discord_links.append(url)
            return True
