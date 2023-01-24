#!/home/qq/Applications/miniconda3/bin/python

import glob
import re
import sqlite3
import time

import cv2
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from lxml import etree
from pyzbar.pyzbar import decode


def qr_to_sql(path_to_folder, path_to_db):
    qr_codes = glob.glob(path_to_folder)
    connector = sqlite3.connect(path_to_db)

    for qr in qr_codes:
        print(qr)
        img = cv2.imread(qr)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded_objects = decode(gray)
        print(decoded_objects)

        # Create a window with a specific size
        cv2.namedWindow("Image", cv2.WINDOW_NORMAL)

        # Resize the window to a specific size
        cv2.resizeWindow("Image", 800, 600)

        # Show the image
        cv2.imshow("Image", gray)

        # Wait for a key press
        cv2.waitKey(0)

        # Close all windows
        cv2.destroyAllWindows()

        try:
            response = requests.get(decoded_objects[0].data)
        except:
            continue

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

        price = re.search(r'Укупан износ:\s+([0-9,]+)\r\n', bill_text).group(1)
        price = re.sub(r',', '.', price)

        buy_time = re.search(r'ПФР време:\s+([0-9.:]+) .*\r\n', bill_text).group(1)
        buy_time = parse(buy_time)
        buy_time = buy_time.strftime("%Y-%m-%d")

        # cursor = connector.cursor()
        # cursor.execute('INSERT INTO bills (id, name, dates, price) VALUES (?,?,?,?)', (timestamp, shop_name, buy_time, price,))
        # cursor.execute('INSERT INTO items (id, photo, name, price, price_kg) VALUES (?,?,?,?,?)', (timestamp, decoded_objects[0].data, bill_text, 0, 0,))
        # cursor.execute('INSERT INTO currency (id, currency, place) VALUES (?,?,?)', (timestamp, "rsd", "serbia",))
        # input_values = []
        # tag_input = input(f'{bill_text}\nTag for this bill?\n>')
        # while tag_input != '0':
        #     input_values.append((timestamp,tag_input,))
        #     tag_input = input('One more? (0 = exit)\n>')
        # cursor.executemany('INSERT INTO tags (id, tag) VALUES (?,?)', input_values)
        # # connector.commit()
        # cursor.close()
    
    connector.close()
    return



if __name__ == "__main__":
    qr_to_sql(
        path_to_folder='/home/qq/Documents/databaseSQL/bills/qr-codes/*.jpg',
        path_to_db='/home/qq/Documents/databaseSQL/bills/bills.db',
    )
    