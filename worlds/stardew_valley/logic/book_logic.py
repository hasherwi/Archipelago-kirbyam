from Utils import cache_self1

from ..stardew_rule import StardewRule
from .base_logic import BaseLogic, BaseLogicMixin


class BookLogicMixin(BaseLogicMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.book = BookLogic(*args, **kwargs)


class BookLogic(BaseLogic):

    @cache_self1
    def has_book_power(self, book: str) -> StardewRule:
        booksanity = self.content.features.booksanity
        if booksanity.is_included(self.content.game_items[book]):
            return self.logic.received(booksanity.to_item_name(book))
        return self.logic.has(book)
