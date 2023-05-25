#!/bin/python
import argparse
import os
import re
import sqlite3
import time
from typing import List, Union

import requests
from bs4 import BeautifulSoup
from lxml import etree


def is_valid_time(time_string):
    '''
    Check if string is in right format YYYY-MM-DD
    '''
    try:
        time.strptime(time_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


class Item:
    def __init__(
            self,
            photo_path: Union[str, None] = None,
            name: Union[str, None] = None,
            price: Union[int, None] = None,
            price_kg: Union[int, None] = None
    ):
        self.photo_path = photo_path
        self.name = name
        self.price = price
        self.price_kg = price_kg


    def __repr__(self):
        # params = vars(self)
        params = f'name: {self.name}\nprice: {self.price}\nprice_kg: {self.price_kg}\nphoto_path: {self.photo_path}'
        return params


    def fill_defaults(self) -> object:
        if self.photo_path is None:
            self.photo_path = ''
        if self.name is None:
            self.photo_path = ''
        if self.price is None:
            self.price = 0
        if self.price_kg is None:
            self.price_kg = 0
        return self


class Bill:
    connector = None

    @classmethod
    def connect_to_sqlite(cls, path_to_db: str) -> None:
        if cls.connector is None:
            cls.connector = sqlite3.connect(path_to_db)
    
    @classmethod
    def disconnect_sqlite(cls) -> None:
        cls.connector.close()
        cls.connector = None

    def __init__(
            self,
            path_to_db: Union[str, None] = None,
            name: Union[str, None] = None,
            date: Union[str, None] = None,
            price: Union[int, None] = None,
            currency: Union[str, None] = None,
            country: Union[str, None] = None,
            items: List[Item] = None,
            tags: List[str] = None
    ):

        if path_to_db and not Bill.connector:
            Bill.connect_to_sqlite(path_to_db)
        if items is None:
            items = []
        if tags is None:
            tags = []
        
        if date and not is_valid_time(date):
            raise ValueError('date must be in ISO format YYYY-MM-DD')

        self.db = path_to_db
        self.timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
        self.name = name
        self.date = date
        self.price = price
        self.currency = currency
        self.country = country
        self.items = items
        self.tags = tags


    def __repr__(self):
        # params = vars(self)
        params = f'timestamp: {self.timestamp}\nname: {self.name}\ndate: {self.date}\nprice: {self.price}\ncurrency: {self.currency}\ncountry: {self.country}\nitems: {self.items}\ntags: {self.tags}\n'
        return params


    def add_tag(self, tag: str) -> object:
        self.tags.append(tag)
        return self


    def add_item(self, item: Item) -> object:
        self.items.append(item)
        return self


    def add_connection(self, path_to_db: str) -> None:
        Bill.connect_to_sqlite(path_to_db)

    
    def from_qr(self, link) -> object:
        response = requests.get(link, timeout=60)
        print(link)
        print('status code:', response.status_code)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'lxml')
        dom = etree.HTML(str(soup))
        
        re_site_junk = re.compile(r'\r\n\s+')        

        self.name = dom.xpath('//*[@id="shopFullNameLabel"]')[0].text

        price = dom.xpath('//*[@id="totalAmountLabel"]')[0].text
        self.price = float(price.replace('.','').replace(',','.'))

        date_format = "%d.%m.%Y." # format of the date string
        buy_date = dom.xpath('//*[@id="sdcDateTimeLabel"]')[0].text
        buy_date = re_site_junk.sub('', buy_date)
        buy_date = buy_date.split(' ')[0]
        buy_date = time.strptime(buy_date, date_format)
        self.date = time.strftime("%Y-%m-%d", buy_date)

        bill = dom.xpath('//*[@id="collapse3"]/div/pre')
        # bill_img = dom.xpath('//*[@id="collapse1"]/div/pre/img')[0].attrib.get('src')
        bill_text = bill[0].text
        self.add_item(Item('',bill_text,0,0))
        print(bill_text[:50])
        return self
    

    def insert(self) -> None:
        if self.db and Bill.connector is None:
            if not isinstance(self.db, str):
                raise ValueError('path_to_db must be str')
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
        if self.country is None:
            raise ValueError('country must be specified')

        cursor = Bill.connector.cursor()

        cursor.execute('INSERT INTO bills (id, name, dates, price) VALUES (?,?,?,?)', (self.timestamp, self.name, self.date, self.price,))
        cursor.execute('INSERT INTO currency (id, currency, place) VALUES (?,?,?)', (self.timestamp, self.currency, self.country,))
        if self.items != []:
            for item in self.items:
                cursor.execute('INSERT INTO items (id, photo, name, price, price_kg) VALUES (?,?,?,?,?)', (self.timestamp, item.photo_path, item.name, item.price, item.price_kg,))
        else:
            print('items are empty.')
        if self.tags != [] or self.tags != ['']:
            for tag in self.tags:
                if tag == '':
                    print('empty tag.')
                    continue
                cursor.execute('INSERT INTO tags (id, tag) VALUES (?,?)', (self.timestamp, tag,))
        else:
            print('tags are empty.')
        
        Bill.connector.commit()
        cursor.close()
        print('Transaction commited')


def process_actions(args):
    expanded_path = os.path.expanduser(args.database)
    Bill.connect_to_sqlite(expanded_path)

    if args.from_qr:
        try:
            with open(args.from_qr, 'r', encoding='utf-8') as f:
                qr_txt = f.read().split('\n')
            qr_txt = set(qr_txt)
        except IOError:
            raise FileExistsError("Error reading qr file.")

        for qr_link in qr_txt:
            bill = Bill().from_qr(qr_link)
            bill.tags = input('write tag in [tag1,tag2,tag3] manner.\n> ').split(',')
            bill.insert()
    
    elif args.insert_bill:
        bill = Bill(
            name=args.name,
            date=args.date,
            price=args.price,
            currency=args.currency,
            country=args.country,
            tags=args.tags.split(',')
        )
        bill.insert()

    Bill.disconnect_sqlite()
    return


def args_init():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--database",
        help="path to the database file",
        metavar='PATH',
        required=True,
    )
    parser.add_argument(
        '-q', "--from-qr", 
        help="Read txt file with URL form qr and parse it to the database.",
        metavar='PATH',
        default=None,
        required=False
    )
    parser.add_argument(
        '-i', "--insert-bill", 
        help="Insert bill from terminal.",
        action='store_true',
        default=None,
        required=False
    )
    parser.add_argument(
        '--name', 
        help="Name of the bill.",
        default=None,
        required=False
    )
    parser.add_argument(
        '--date', 
        help="Date of the bill in format YYYY-MM-DD.",
        default=None,
        required=False
    )
    parser.add_argument(
        '--price', 
        help="Overall price of the bill.",
        default=None,
        type=float,
        required=False
    )
    parser.add_argument(
        '--currency', 
        help="Currency of the bill.",
        default=None,
        required=False
    )
    parser.add_argument(
        '--country', 
        help="country where bill was payed.",
        default=None,
        required=False
    )
    parser.add_argument(
        '--tags', 
        help="tags for the bill. In 'tag1,tag2,tag3' manner.",
        default=None,
        required=False
    )
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = args_init()
    process_actions(args)