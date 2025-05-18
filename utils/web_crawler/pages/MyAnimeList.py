from selenium.webdriver.remote.webelement import WebElement

from utils.web_crawler.pages.BasePage import BasePage

MORE_TITLES = "More titles"
LESS_TITLES = "Less titles"


class MyAnimeList(BasePage):
    def __init__(self, driver, url: str):
        super().__init__(driver)
        self.url: str = url
        self.parsed: bool = False
        self.title: str = ""
        self.aliases: list[str] = []
        self.release_date: str = ""
        self.episode_count: int = 0
        self.related_anime_urls: list[str] = []

    def open(self):
        super().open_url(self.url)
        self.click_cookies_overlay()

    def parse(self):
        if self.parsed:
            return

        self.open()
        self.title = self.parse_title()
        self.aliases = self.parse_aliases()
        self.parsed = True

    def parse_related_anime_urls(self) -> list[str]:
        raise NotImplementedError

    def parse_release_date(self) -> str:
        raise NotImplementedError

    def parse_title(self) -> str:
        try:
            return self.driver.xfind("//*[@id='contentWrapper']/div[1]/div/div[1]/div/h1/strong").text
        except IndexError:
            raise ValueError("Title not found")

    def parse_aliases(self) -> list[str]:
        aliases = []
        main_alias = self.driver.xfinds("//*[@id='contentWrapper']/div[1]/div/div[1]/div/p")
        if main_alias:
            aliases.append(main_alias[0].text)

        title_toggler = self.get_titles_toggler()
        if title_toggler.text == MORE_TITLES:
            title_toggler.click()

        return aliases

    def parse_episode_count(self) -> str:
        raise NotImplementedError

    def get_titles_toggler(self) -> WebElement:
        btn = self.driver.xfind("//*[@id='content']/table/tbody/tr/td[1]/div/a")
        if btn:
            return btn
        raise ValueError("Toggler not found")

    def click_cookies_overlay(self) -> None:
        div = self.driver.xfind("//*[@id='qc-cmp2-ui']/div[2]/div/button[3]")
        if div:
            div.click()
