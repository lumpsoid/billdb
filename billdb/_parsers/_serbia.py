import re
import json
import requests
from time import strptime, strftime, sleep
from lxml import etree

from .._item import Item
from .._utils.logging import get_logger


def get_bill_info(link):
    '''
    Parsing site with bill info.

    link: str

    Return: name, date, price, currency, country, bill_text, items
    '''
    LOGGER = get_logger(__name__)

    response = requests.get(link, timeout=60)
    LOGGER.info('status code: {}'.format(response.status_code))

    # metaparameters
    re_site_junk = re.compile(r'\r\n\s+')        
    token_xpath = '/html/head/script[5]'
    invoce_xpath = '//*[@id="invoiceNumberLabel"]'
    price_xpath = '//*[@id="totalAmountLabel"]'
    buy_date_xpath = '//*[@id="sdcDateTimeLabel"]'
    bill_xpath = '//*[@id="collapse3"]/div/pre'
    name_xpath = '//*[@id="shopFullNameLabel"]'
    token_search = r"viewModel\.Token\('(.*)'\);"
    date_format = "%d.%m.%Y." # format of the date string

    # Parse the HTML content
    dom = etree.HTML(response.content)

    price = dom.xpath(price_xpath)[0].text

    buy_date = dom.xpath(buy_date_xpath)[0].text
    buy_date = re_site_junk.sub('', buy_date)
    buy_date = buy_date.split(' ')[0]
    buy_date = strptime(buy_date, date_format)

    bill = dom.xpath(bill_xpath)

    # items fetching
    token = re.search(token_search, dom.xpath(token_xpath)[0].text).group(1)
    invoce_num = dom.xpath(invoce_xpath)[0].text.strip(' \r\n')
    data_post = {
        "invoiceNumber": invoce_num,
        "token": token
    }
    post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
    sleep(0.2)
    post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
    json_data = json.loads(post_r.content.decode('utf-8'))
    if json_data.get('Success') == False:
        LOGGER.info("Items was not fetched. {}".format(link))
        LOGGER.info('Retring...')
        sleep(0.1)
        post_r = requests.post('https://suf.purs.gov.rs//specifications', data=data_post)
        json_data = json.loads(post_r.content.decode('utf-8'))

    items_json = json_data.get('Items')
    items = []
    for item in items_json:
        items.append(Item(
            name=item.get('Name'),
            price=item.get('Total'),
            price_one=item.get('UnitPrice'),
            quantity=item.get('Quantity'),
            photo_path=None))
    price = float(price.replace('.','').replace(',','.'))
    name = dom.xpath(name_xpath)[0].text
    currency = 'rsd'
    country = 'serbia'
    date = strftime("%Y-%m-%d", buy_date)
    if len(bill) == 0:
        bill_text = "check"
    else:
        bill_text = bill[0].text

    return (
        name,
        date,
        price,
        currency,
        country,
        bill_text,
        items
    )
