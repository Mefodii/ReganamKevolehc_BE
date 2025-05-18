from typing import cast

from bs4 import BeautifulSoup, Tag

from utils.utils import dict_includes


class Soup(BeautifulSoup):
    def find_tags(self, name=None, attrs=None, recursive=True, string=None,
                  limit=None, **kwargs) -> list[Tag]:
        """
        AFAIK default findAll does not guarantee results to be ordered.
        This is an ugly workaround to ensure order.
        @param name:
        @param attrs:
        @param recursive: 
        @param string:
        @param limit:
        @param kwargs:
        @return:
        """
        if attrs is None:
            attrs = {}

        if not name:
            print("Warning: Not implemented yet")
            return []

        result: list[Tag] = []
        children = self.find_all() if recursive else self.children
        for child in children:
            if type(child) is not Tag:
                continue

            tag = cast(Tag, child)
            if tag.name == name and dict_includes(tag.attrs, attrs):
                result.append(tag)

        return result
