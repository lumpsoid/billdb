import argparse
import os
import re
import sqlite3
import time
from typing import List, Union
import json

import requests
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
            price: Union[float, None] = None,
            price_one: Union[int, None] = None,
            quantity: Union[int, None] = None
    ):
        self.photo_path = photo_path
        self.name = name
        self.price = price
        self.price_one = price_one
        self.quantity = quantity


    def __repr__(self):
        # params = vars(self)
        params = f'name: {self.name}\nprice: {self.price}\nprice_one: {self.price_one}\nquantity: {self.quantity}\nphoto_path: {self.photo_path}'
        return params


    def fill_defaults(self) -> object:
        if self.photo_path is None:
            self.photo_path = ''
        if self.name is None:
            self.name = ''
        if self.price is None:
            self.price = 0
        if self.price_one is None:
            self.price_one = 0
        if self.quantity is None:
            self.quantity = 1
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
            items: Union[List[Item], None] = None,
            tags: Union[str, None] = None
    ):

        if path_to_db and not Bill.connector:
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
        self.country = country
        self.items = items
        self.tags = tags
        self.link = None
        self.bill_text = None


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


    def add_connection(self, path_to_db: str) -> None:
        Bill.connect_to_sqlite(path_to_db)

    
    def from_qr(self, link) -> object:
        self.link = link
        response = requests.get(link, timeout=60)
        print('status code:', response.status_code)

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
            print("Items was not fetched.", link)
            print('Retring...')
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
        if self.tags is None:
            if self.link is None:
                raise ValueError('tags must be specified')
            self.tags = ""

        cursor = Bill.connector.cursor()

        cursor.execute(
                'INSERT INTO bills (id, name, dates, price, currency, country, tag, link, bill) VALUES (?,?,?,?,?,?,?,?,?)',
                (self.timestamp, self.name, self.date, self.price, self.currency, self.country, self.tags, self.link, self.bill_text,)
        )
        if self.items != []:
            insert_query = 'INSERT INTO items (id, name, price, price_one, quantity) VALUES (?,?,?,?,?)'
            for item in self.items:
                cursor.execute(
                        insert_query,
                        (self.timestamp, item.name, item.price, item.price_one, item.quantity,)
                )
        else:
            print('items are empty.')
        
        Bill.connector.commit()
        cursor.close()
        print('Transaction commited')


def process_actions(args):
    expanded_path = os.path.expanduser(args.database)
    Bill.connect_to_sqlite(expanded_path)
    
    if args.from_qr:
        try:
            with open(args.from_qr, 'r', encoding='utf-8') as f:
                qr_txt = f.readlines()
        except IOError:
            raise FileExistsError("Error reading qr file.")

        qr_txt = list(set(qr_txt))
        for qr_link in qr_txt:
            qr_link = qr_link.rstrip('\n')
            bill = Bill().from_qr(qr_link)
            bill.currency = "rsd"
            bill.country = "serbia"
            bill.insert()
        # test for new unique item's names
        cur = Bill.connector.cursor()
        unique_name_query = """
            SELECT DISTINCT i.name
            FROM items as i
            LEFT JOIN items_meta as im ON i.name = im.name
            WHERE im.name IS NULL;
        """
        add_unique_names_query = "INSERT INTO items_meta (name)\n" + unique_name_query

        cur.execute(unique_name_query)
        data_unique_names = cur.fetchall()
        if len(data_unique_names) == 0:
            print('No new unique names of items')
            cur.close()
        else:
            print(f'{len(data_unique_names)} new unique items')
            cur.execute(add_unique_names_query)
            #for i in range(len(data_unique_names)):
                #    if data_unique_names[i] == "":
                #    continue
                #print(data_unique_names[i])
                #tag = input('Tag for this item\n(tag1,tag2,tag3)\n>')
                #data_unique_names[i] = (*data_unique_names[i], tag,)

            #insert_quary = "INSERT INTO items_meta (name, tag) VALUES (?, ?)"
            #cur.executemany(insert_quary, data_unique_names)
            Bill.connector.commit()
            cur.close()

    
    elif args.insert_bill:
        bill = Bill(
            name=args.name,
            date=args.date,
            price=args.price,
            currency=args.currency,
            country=args.country,
            tags=args.tags
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
