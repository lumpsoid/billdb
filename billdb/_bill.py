import re
import sqlite3
import time
from typing import List, Union
import json

import requests
from lxml import etree

from ._item import Item
from .helpers import is_valid_time
from ._utils.logging import get_logger

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
            Bill.LOGGER.info('No new unique names of items')
        else:
            cls.cursor.execute(add_unique_names_query)
            result = cls.commit_transaction()
            if result == 1:
                Bill.LOGGER.info(f'{len(data_unique_names)} new unique items')
            else:
                Bill.LOGGER.warning('Something wrong with transaction. Is there a connector?')

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
            tags: Union[str, None] = None
    ):

        if path_to_db and Bill.connector is None:
            if not isinstance(path_to_db, str):
                raise ValueError('path_to_db must be str')
            Bill.connect_to_sqlite(path_to_db)

        if items is None:
            items = []
        
        if date and not is_valid_time(date):
            raise ValueError('date must be in ISO format YYYY-MM-DD')

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
        params = f'timestamp: {self.timestamp}\nname: {self.name}\ndate: {self.date}\nprice: {self.price}\ncurrency: {self.currency}\ncountry: {self.country}\nitems: {len(self.items)}\ntags: {self.tags}\nlink: {self.link}'
        return params

    def add_item(self, name, price, price_one, quantity, photo_path=None) -> object:
        item = Item(
            name=name,
            price=price,
            price_one=price_one,
            quantity=quantity,
            photo_path=photo_path
        )
        self.items.append(item)
        return self

    def check_duplicates(self) -> None:
        Bill.cursor.execute(f'''
        SELECT id, name, dates, price, currency, bill
        FROM bills
        WHERE
            dates = '{self.date}'
            AND price = {self.price}
            AND currency = '{self.currency}';
        ''')

        self.dup_list = Bill.cursor.fetchall()
    
    def from_qr(self, link) -> object:
        self.link = link
        response = requests.get(link, timeout=60)
        Bill.LOGGER.info('status code:', response.status_code)

        # Parse the HTML content
        dom = etree.HTML(response.content)
        
        token_xpath = '/html/head/script[5]'
        invoce_xpath = '//*[@id="invoiceNumberLabel"]'
        price_xpath = '//*[@id="totalAmountLabel"]'
        buy_date_xpath = '//*[@id="sdcDateTimeLabel"]'
        bill_xpath = '//*[@id="collapse3"]/div/pre'

        re_site_junk = re.compile(r'\r\n\s+')        

        self.name = dom.xpath('//*[@id="shopFullNameLabel"]')[0].text

        price = dom.xpath(price_xpath)[0].text
        self.price = float(price.replace('.','').replace(',','.'))

        date_format = "%d.%m.%Y." # format of the date string
        buy_date = dom.xpath(buy_date_xpath)[0].text
        buy_date = re_site_junk.sub('', buy_date)
        buy_date = buy_date.split(' ')[0]
        buy_date = time.strptime(buy_date, date_format)
        self.date = time.strftime("%Y-%m-%d", buy_date)

        bill = dom.xpath(bill_xpath)
        if len(bill) == 0:
            self.bill_text = "check"
        else:
            self.bill_text = bill[0].text
        # bill_img = dom.xpath('//*[@id="collapse1"]/div/pre/img')[0].attrib.get('src')
        self.currency = 'rsd'
        self.country = 'serbia'
        # items fetching
        token = re.search(r"viewModel\.Token\('(.*)'\);", dom.xpath(token_xpath)[0].text).group(1)
        invoce_num = dom.xpath(invoce_xpath)[0].text.strip(' \r\n')
        data_post = {
            "invoiceNumber": invoce_num,
            "token": token
        }
        post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
        time.sleep(0.1)
        post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
        json_data = json.loads(post_r.content.decode('utf-8'))
        if json_data.get('Success') is False:
            Bill.LOGGER.info("Items was not fetched.", link)
            Bill.LOGGER.info('Retring...')
            post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
            json_data = json.loads(post_r.content.decode('utf-8'))

        items = json_data.get('Items')
        for item in items:
            self.add_item(
                name=item.get('Name'),
                price=item.get('Total'),
                price_one=item.get('UnitPrice'),
                quantity=item.get('Quantity')
            )
        return self
    

    def insert(self, force_dup) -> None:
        # explicite check of all importatnt parts
        # make sure that all in its final form
        if self.db and Bill.connector is None:
            Bill.connect_to_sqlite(self.db)
        if self.db is None and Bill.connector is None:
            raise ValueError('add connection to database')
        if not is_valid_time(self.date):
            raise ValueError('date must be in ISO format YYYY-MM-DD')
        if self.name is None:
            raise ValueError('name must be specified')
        if self.price is None:
            raise ValueError('price must be specified')
        if self.currency is None:
            raise ValueError('currency must be specified')
        if self.exchange_rate is None:
            if self.currency == 'rsd':
                self.exchange_rate = 1
            else:
                raise ValueError('exchange rate must be specified')
        if self.country is None:
            raise ValueError('country must be specified')
        if self.tags is None:
            if self.link is None:
                raise ValueError('tags must be specified')
            self.tags = ""

        # checking duplicates
        self.check_duplicates()
        if len(self.dup_list) and not force_dup:
            Bill.LOGGER.info('Maybe duplicates', len(self.dup_list))
            Bill.LOGGER.info('Nothing was changed')
            return

        Bill.cursor.execute(
                'INSERT INTO bills (id, name, dates, price, currency, exchange_rate, country, tag, link, bill) VALUES (?,?,?,?,?,?,?,?,?,?)',
                (self.timestamp, self.name, self.date, self.price, self.currency, self.exchange_rate, self.country, self.tags, self.link, self.bill_text,)
        )
        if self.items != []:
            insert_query = 'INSERT INTO items (id, name, price, price_one, quantity) VALUES (?,?,?,?,?)'
            for item in self.items:
                Bill.cursor.execute(
                        insert_query,
                        (self.timestamp, item.name, item.price, item.price_one, item.quantity,)
                )
        else:
            Bill.LOGGER.info('items are empty.')

        result = Bill.commit_transaction()
        if result == 1:
            Bill.LOGGER.info('Transaction commited')
        else:
            Bill.LOGGER.warning('Something wrong with transaction. Is there a connector?')
