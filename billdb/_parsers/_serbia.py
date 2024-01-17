import re
import json
import requests
from time import strptime, strftime, sleep
from lxml import etree

from .._item import Item
from .._utils.logging import get_logger


def get_bill_info(link: str) -> tuple:
    """
    Parsing site with bill info.

    link: str

    Return: name, date, price, currency, country, bill_text, items
    """
    # metaparameters
    token_xpath = "/html/head/script[5]"
    invoce_xpath = '//*[@id="invoiceNumberLabel"]'
    price_xpath = '//*[@id="totalAmountLabel"]'
    buy_date_xpath = '//*[@id="sdcDateTimeLabel"]'
    bill_xpath = '//*[@id="collapse3"]/div/pre'
    name_xpath = '//*[@id="shopFullNameLabel"]'
    token_search = r"viewModel\.Token\('(.*)'\);"

    LOGGER = get_logger(__name__)

    response = requests.get(link, timeout=60)
    LOGGER.info("status code: {}".format(response.status_code))

    # Parse the HTML content
    dom = etree.HTML(response.content)

    name = get_bill_name(dom, name_xpath)
    bill_text = get_bill_text(dom, bill_xpath)
    date = get_bill_buy_date(dom, buy_date_xpath, "%d.%m.%Y.", "%Y-%m-%d")
    items = get_bill_items(dom, token_xpath, token_search, invoce_xpath)
    price = get_bill_price(dom, price_xpath)
    
    currency = "rsd"
    country = "serbia"

    return (name, date, price, currency, country, bill_text, items)


def get_bill_items(dom: str, token_xpath: str, token_search: str, invoce_xpath: str):
    """_summary_

    Args:
        dom (str): parsed html dom
        token_xpath (str): xpath to the token node
        token_search (str): pattern to get token from node
        invoce_xpath (str): xpath to the invoce node

    Returns:
        List(Item): Item's list
    """
    LOGGER = get_logger(__name__)
    token = re.search(token_search, dom.xpath(token_xpath)[0].text).group(1)
    invoce_num = dom.xpath(invoce_xpath)[0].text.strip(" \r\n")
    data_post = {"invoiceNumber": invoce_num, "token": token}
    post_r = requests.post("https://suf.purs.gov.rs//specifications", data=data_post)
    sleep(0.2)
    post_r = requests.post("https://suf.purs.gov.rs//specifications", data=data_post)
    json_data = json.loads(post_r.content.decode("utf-8"))
    if json_data.get("Success") == False:
        LOGGER.info("Items was not fetched.")
        LOGGER.info("Retring...")
        sleep(0.1)
        post_r = requests.post(
            "https://suf.purs.gov.rs//specifications", data=data_post
        )
        json_data = json.loads(post_r.content.decode("utf-8"))

    items_json = json_data.get("Items")
    items = []
    for item in items_json:
        items.append(
            Item(
                name=item.get("Name"),
                price=item.get("Total"),
                price_one=item.get("UnitPrice"),
                quantity=item.get("Quantity"),
                photo_path=None,
            )
        )
    return items

def get_bill_buy_date(dom: str, buy_date_xpath: str, date_format_parse: str, date_format_output: str) -> str:
    re_site_junk = re.compile(r"\r\n\s+")
    buy_date = dom.xpath(buy_date_xpath)[0].text
    buy_date = re_site_junk.sub("", buy_date)
    buy_date = buy_date.split(" ")[0]
    buy_date = strptime(buy_date, date_format_parse)
    date = strftime(date_format_output, buy_date)
    return date

def get_bill_price(dom: str, price_xpath: str) -> float:
    price = dom.xpath(price_xpath)[0].text
    price = float(price.replace(".", "").replace(",", "."))
    return price

def get_bill_text(dom: str, bill_text_xpath: str) -> str:
    bill = dom.xpath(bill_text_xpath)
    bill_text = "check"
    if len(bill) != 0:
        bill_text = bill[0].text
    return bill_text

def get_bill_name(dom: str, bill_name_xpath: str) -> str:
    return dom.xpath(bill_name_xpath)[0].text
