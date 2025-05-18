from utils.web_crawler.webdriver import ChromeExtended


class BasePage:
    def __init__(self, driver: ChromeExtended):
        self.driver = driver

    def open_url(self, url: str, new_tab: bool = False) -> None:
        if not new_tab:
            self.driver.get(url)
        else:
            raise NotImplementedError
