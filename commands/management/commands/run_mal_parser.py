from django.core.management.base import BaseCommand

from utils.web_crawler.pages.MyAnimeList import MyAnimeList
from utils.web_crawler.webdriver import ChromeExtended


def validation_tests():
    raise NotImplementedError


class Command(BaseCommand):
    def handle(self, **options):
        pass
        driver = ChromeExtended()
        try:
            url = "https://myanimelist.net/anime/48316/Kage_no_Jitsuryokusha_ni_Naritakute"
            mal = MyAnimeList(driver, url)
            mal.parse()
        finally:
            driver.quit()
