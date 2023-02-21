#!/home/qq/Applications/miniconda3/bin/python

import glob
import re
import sqlite3
import time

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from lxml import etree


def proceed_test():
    while 1:
        flag = input('Are you want to procceed (Y/n) ')
        if flag in ('y', ''):
            return 0
        return 1


def qr_to_sql(path_to_qr, path_to_db):
    print(f'{glob_path=}')
    print(f'This files will be processed: {list_of_files}')
    stop_flag = proceed_test()
    if stop_flag:
        return print(f'{path_to_qr} will not be parced')

    with open(path_to_qr, 'r', encoding='utf8') as f:
        qr_codes = f.read().split('\n')
    
    qr_codes = set(qr_codes)  # if you scanned qr several times

    connector = sqlite3.connect(path_to_db)
    
    re_site_junk = re.compile(r'\r\n\s+')
    # re_price = re.compile(r'Укупан износ:\s+([0-9,.]+)\r\n')
    re_price_com = re.compile(r',')
    re_price_dot = re.compile(r'\.')
    # re_buy_time = re.compile(r'ПФР време:\s+([0-9.:]+) .*\r\n')

    for _, qr_link in enumerate(qr_codes):
        response = requests.get(qr_link)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'lxml')
        dom = etree.HTML(str(soup))

        bill = dom.xpath('//*[@id="collapse1"]/div/pre')
        # bill_img = dom.xpath('//*[@id="collapse1"]/div/pre/img')[0].attrib.get('src')

        bill_text = bill[0].text
        list_from_bill = bill_text.split('\r\n')
        shop_name = list_from_bill[2]
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())

        price = dom.xpath('/html/body/div/div/form/div[2]/div[2]/div/div[2]/div[1]/div')[0].text
        price = re_site_junk.sub('', price)
        price = re_price_dot.sub('', price)
        price = re_price_com.sub('.', price)

        buy_time = dom.xpath('/html/body/div/div/form/div[2]/div[2]/div/div[2]/div[7]/div')[0].text
        buy_time = re_site_junk.sub('', buy_time)
        buy_time = parse(buy_time, dayfirst=True)
        buy_time = buy_time.strftime("%Y-%m-%d")

        cursor = connector.cursor()
        cursor.execute('INSERT INTO bills (id, name, dates, price) VALUES (?,?,?,?)', (timestamp, shop_name, buy_time, price,))
        cursor.execute('INSERT INTO items (id, photo, name, price, price_kg) VALUES (?,?,?,?,?)', (timestamp, qr_link, bill_text, 0, 0,))
        cursor.execute('INSERT INTO currency (id, currency, place) VALUES (?,?,?)', (timestamp, "rsd", "serbia",))
        
        def form_list_for_sql(input_list):
            return (timestamp, input_list,)
        
        tag_list = input(f'{bill_text}\n\nTags list for this bill?\n<write,in,this,manner>\n>')
        # check last element on trailing `,`
        if tag_list[-1] == ',':
            tag_list = tag_list[:-1]
        tag_list = tag_list.split(",")
        # formating list to sql needed format
        tag_list = list(map(form_list_for_sql, tag_list))

        if (timestamp,'drop-pop',) in tag_list:
            print('Skiping this bill')
            continue
        cursor.executemany('INSERT INTO tags (id, tag) VALUES (?,?)', tag_list)
        # connector.commit()
        cursor.close()

    connector.close()
    return


if __name__ == "__main__":
    glob_path = '/home/qq/Downloads/qrs/*'
    list_of_files = glob.glob(glob_path)

    for file in list_of_files:
        qr_to_sql(
            path_to_qr=file,
            path_to_db='/home/qq/Documents/databaseSQL/bills/bills.db',
        )