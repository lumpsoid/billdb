#!/home/qq/Applications/miniconda3/bin/python

import re
import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from lxml import etree


def qr_to_sql(path_to_qr, path_to_db):
    with open(path_to_qr, 'r') as f:
        qr_codes = f.read().split('\n')

    connector = sqlite3.connect(path_to_db)
    
    re_price = re.compile(r'Укупан износ:\s+([0-9,.]+)\r\n')
    re_price_com = re.compile(r',')
    re_price_dot = re.compile(r'.')
    re_buy_time = re.compile(r'ПФР време:\s+([0-9.:]+) .*\r\n')

    for _, qr_link in enumerate(qr_codes):
        print(_)
        response = requests.get(qr_link)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'lxml')
        dom = etree.HTML(str(soup))

        bill = dom.xpath('//*[@id="collapse1"]/div/pre')
        # bill_img = dom.xpath('//*[@id="collapse1"]/div/pre/img')[0].attrib.get('src')

        bill_text = bill[0].text
        bill_text
        list_from_bill = bill_text.split('\r\n')
        shop_name = list_from_bill[2]
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())

        price = re_price.search(bill_text).group(1)
        price = re_price_dot.sub('', price)
        price = re_price_com.sub('.', price)

        buy_time = re_buy_time.search(bill_text).group(1)
        buy_time = parse(buy_time)
        buy_time = buy_time.strftime("%Y-%m-%d")

        cursor = connector.cursor()
        cursor.execute('INSERT INTO bills (id, name, dates, price) VALUES (?,?,?,?)', (timestamp, shop_name, buy_time, price,))
        cursor.execute('INSERT INTO items (id, photo, name, price, price_kg) VALUES (?,?,?,?,?)', (timestamp, qr_link, bill_text, 0, 0,))
        cursor.execute('INSERT INTO currency (id, currency, place) VALUES (?,?,?)', (timestamp, "rsd", "serbia",))
        input_values = []
        tag_input = input(f'{bill_text}\nTag for this bill?\n>')
        while tag_input != '0':
            input_values.append((timestamp,tag_input,))
            tag_input = input('One more? (0 = exit)\n>')
        cursor.executemany('INSERT INTO tags (id, tag) VALUES (?,?)', input_values)
        connector.commit()
        cursor.close()

    connector.close()
    return


if __name__ == "__main__":
    qr_to_sql(
        path_to_qr='/home/qq/Downloads/2023-01-24-qr.txt',
        path_to_db='/home/qq/Documents/databaseSQL/bills/bills.db',
    )
