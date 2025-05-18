import time
from typing import Self

from selenium import webdriver
from selenium.common import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from utils.utils import dict_includes
from utils.web_crawler.Soup import Soup


# NOTE: Waiting for page load: https://stackoverflow.com/questions/59853468/order-of-found-elements-in-selenium


class ChromeExtended(webdriver.Chrome):
    @classmethod
    def headless(cls) -> Self:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        return cls(options=options)

    def soup(self) -> Soup:
        return Soup(self.page_source, "html.parser")

    def close_other_tabs(self, main_handler: str):
        for window in self.window_handles:
            if window != main_handler:
                self.switch_to.window(window)
                self.close()

        self.switch_to.window(main_handler)

    def get_attrs(self, element: WebElement) -> dict:
        attrs: dict = self.execute_script(
            'var items = {}; '
            'for (index = 0; '
            'index < arguments[0].attributes.length; ++index) { '
            'items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value '
            '}; return items;',
            element)
        return attrs

    def scroll_into_view(self, element: WebElement) -> None:
        self.execute_script("arguments[0].scrollIntoView(true);", element)

    def find_elements_by_tag(self, name=None, attrs: dict = None) -> list[WebElement]:
        tags = self.find_elements(By.TAG_NAME, name)

        result: list[WebElement] = []
        for tag in tags:
            tag_attrs = self.get_attrs(tag)
            if dict_includes(tag_attrs, attrs):
                result.append(tag)

        return result

    def find_element_by_tag(self, name=None, attrs: dict = None) -> WebElement | None:
        tags = self.find_elements_by_tag(name, attrs)
        if len(tags) == 0:
            return None
        else:
            if len(tags) > 1:
                print(f"Warning: multiple elements found. Query: {name} / {str(attrs)}")
            return tags[0]

    def safe_click(self, element: WebElement) -> None:
        """
        Try to click the element normally.
        If that doesn't work, click it by simulating a user interaction
        :param element: element which to click
        :return:
        """
        window_id = self.current_window_handle
        try:
            element.click()
        except ElementClickInterceptedException:
            # Exception happens if there is an ad over the button.
            # Do a forced click in the area for the add to open in a new tab
            actions = ActionChains(self)
            actions.move_to_element(element).click().perform()
            time.sleep(1)

        # Other tabs a.k.a. ads / spam
        self.close_other_tabs(window_id)

    def xfinds(self, value: str) -> list[WebElement]:
        return self.find_elements(By.XPATH, value)

    def xfind(self, value: str) -> WebElement | None:
        try:
            return self.find_element(By.XPATH, value)
        except NoSuchElementException:
            return None
