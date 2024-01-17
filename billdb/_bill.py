import re
import logging
import sqlite3
import time
from typing import List, Union

from ._item import Item
from .helpers import is_valid_time
from ._utils.logging import get_logger
from ._parsers import _serbia

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


class Bill:
    connector = None
    cursor = None
    LOGGER = get_logger(__name__)

    @classmethod
    def connect_to_sqlite(cls, path_to_db: str) -> None:
        if cls.connector is None:
            cls.connector = sqlite3.connect(path_to_db)
            cls.cursor = cls.connector.cursor()

    @classmethod
    def close_sqlite(cls) -> None:
        if cls.connector is not None:
            cls.connector.commit()

            cls.cursor.close()
            cls.cursor = None

            cls.connector.close()
            cls.connector = None

    @classmethod
    def check_unique_names(cls) -> None:
        unique_name_query = """
            SELECT DISTINCT i.name
            FROM items as i
            LEFT JOIN items_meta as im ON i.name = im.name
            WHERE im.name IS NULL;
        """
        add_unique_names_query = "INSERT INTO items_meta (name)\n" + unique_name_query

        cls.cursor.execute(unique_name_query)
        data_unique_names = cls.cursor.fetchall()
        if len(data_unique_names) == 0:
            Bill.LOGGER.info("No new unique names of items")
        else:
            cls.cursor.execute(add_unique_names_query)
            result = cls.commit_transaction()
            if result == 1:
                Bill.LOGGER.info(f"{len(data_unique_names)} new unique items")
            else:
                Bill.LOGGER.warning(
                    "Something wrong with transaction. Is there a connector?"
                )

    @classmethod
    def commit_transaction(cls) -> int:
        output = 0
        if cls.connector is not None:
            cls.connector.commit()
            output = 1
        return output

    def __init__(
        self,
        path_to_db: Union[str, None] = None,
        name: Union[str, None] = None,
        date: Union[str, None] = None,
        price: Union[int, None] = None,
        currency: Union[str, None] = None,
        exchange_rate: Union[str, None] = None,
        country: Union[str, None] = None,
        items: Union[List[Item], None] = None,
        tags: Union[str, None] = None,
    ):
        if path_to_db and Bill.connector is None:
            if not isinstance(path_to_db, str):
                raise ValueError("path_to_db must be str")
            Bill.connect_to_sqlite(path_to_db)

        if items is None:
            items = []

        if date and not is_valid_time(date):
            raise ValueError("date must be in ISO format YYYY-MM-DD")

        self.db = path_to_db
        self.timestamp = time.time_ns()
        self.name = name
        self.date = date
        self.price = price
        self.currency = currency
        self.exchange_rate = exchange_rate
        self.country = country
        self.items = items
        self.tags = tags
        self.link = None
        self.bill_text = None
        self.dup_list = None

    def __repr__(self):
        # params = vars(self)
        params = f"timestamp: {self.timestamp}\nname: {self.name}\ndate: {self.date}\nprice: {self.price}\ncurrency: {self.currency}\ncountry: {self.country}\nitems: {len(self.items)}\ntags: {self.tags}\nlink: {self.link}"
        return params

    def add_item(self, name, price, price_one, quantity, photo_path=None) -> object:
        item = Item(
            name=name,
            price=price,
            price_one=price_one,
            quantity=quantity,
            photo_path=photo_path,
        )
        self.items.append(item)
        return self

    def update_info(
        self,
        name=None,
        date=None,
        price=None,
        currency=None,
        exchange_rate=None,
        country=None,
        bill_text=None,
        items=None,
        tags=None,
    ):
        """Updating info about the bill if provided."""
        if name:
            self.name = name
        if date:
            self.date = date
        if price:
            self.price = price
        if currency:
            self.currency = currency
        if country:
            self.country = country
        if bill_text:
            self.bill_text = bill_text
        if items:
            self.items = items
        if tags:
            self.tags = tags
        if exchange_rate:
            self.exchange_rate = exchange_rate
        return

    def check_duplicates(self) -> None:
        Bill.cursor.execute(
            f"""
        SELECT id, name, dates, price, currency, bill
        FROM bills
        WHERE
            dates = '{self.date}'
            AND price = {self.price}
            AND currency = '{self.currency}';
        """
        )

        self.dup_list = Bill.cursor.fetchall()

    def from_qr(self, link) -> object:
        if re.match(r"https://suf.purs.gov.rs", link):
            Bill.LOGGER.debug("using serbian parser.")
            # name, date, price, currency, country, bill_text, items
            (
                self.name,
                self.date,
                self.price,
                self.currency,
                self.country,
                self.bill_text,
                self.items,
            ) = _serbia.get_bill_info(link)
            self.exchange_rate = "1"
            self.link = link

        return self

    def insert(self, force_dup) -> None:
        # explicite check of all importatnt parts
        # make sure that all in its final form
        if self.db and Bill.connector is None:
            Bill.connect_to_sqlite(self.db)
        if self.db is None and Bill.connector is None:
            raise ValueError("add connection to database")
        if not is_valid_time(self.date):
            raise ValueError("date must be in ISO format YYYY-MM-DD")
        if self.name is None:
            raise ValueError("name must be specified")
        if self.price is None:
            raise ValueError("price must be specified")
        if self.currency is None:
            raise ValueError("currency must be specified")
        if self.exchange_rate is None:
            if self.currency == "rsd":
                self.exchange_rate = 1
            else:
                raise ValueError("exchange rate must be specified")
        if self.country is None:
            raise ValueError("country must be specified")
        if self.tags is None:
            if self.link is None:
                raise ValueError("tags must be specified")
            self.tags = ""

        # checking duplicates
        self.check_duplicates()
        if len(self.dup_list) and not force_dup:
            Bill.LOGGER.info(
                f"Maybe duplicates ({len(self.dup_list)}). Nothing was changed."
            )
            return

        Bill.cursor.execute(
            "INSERT INTO bills (id, name, dates, price, currency, exchange_rate, country, tag, link, bill) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                self.timestamp,
                self.name,
                self.date,
                self.price,
                self.currency,
                self.exchange_rate,
                self.country,
                self.tags,
                self.link,
                self.bill_text,
            ),
        )
        if self.items != []:
            insert_query = "INSERT INTO items (id, name, price, price_one, quantity) VALUES (?,?,?,?,?)"
            for item in self.items:
                Bill.cursor.execute(
                    insert_query,
                    (
                        self.timestamp,
                        item.name,
                        item.price,
                        item.price_one,
                        item.quantity,
                    ),
                )
        else:
            Bill.LOGGER.info("items are empty.")

        result = Bill.commit_transaction()
        if result == 1:
            Bill.LOGGER.info("Transaction commited")
        else:
            Bill.LOGGER.warning(
                "Something wrong with transaction. Is there a connector?"
            )
