#!/usr/bin/env python

import argparse
import os
from billdb import Bill

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
            bill.exchange_rate = "1"
            bill.country = "serbia"
            bill.insert(force_dup=args.force)
    
    elif args.insert_bill:
        bill = Bill(
            name=args.name,
            date=args.date,
            price=args.price,
            currency=args.currency,
            exchange_rate=args.exchange_rate,
            country=args.country,
            tags=args.tags
        )
        bill.insert(force_dup=args.force)

    Bill.close_sqlite()
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
        '--exchange-rate',
        help="Exchange rate of the currency.",
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
    parser.add_argument(
        '-f', '--force',
        help="if duplicates founded in the db, forcfully push transaction.",
        action='store_true',
        default=False,
        required=False
    )
    args = parser.parse_args()
    return args

def main():
    args = args_init()
    process_actions(args)

if __name__ == "__main__":
    main()
