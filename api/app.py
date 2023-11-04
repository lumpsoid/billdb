try:
    from flask import Flask, request, send_file, redirect
except ImportError:
    raise ImportError('flask packed was not found. Try `pip install .[api]`')

import logging
import re
import os

from billdb import Bill, db_template, build_html_table, build_html_list

app = Flask(__name__)

# Configure Flask logging
app.logger.setLevel(logging.DEBUG)  # Set the desired logging level
handler = logging.FileHandler("./flask.log")  # Replace with the desired path inside the container
handler.setLevel(logging.DEBUG)  # Set the desired logging level for Flask logs
app.logger.addHandler(handler)

database_path = './bills.db'

def check_db_exist():
    if not os.path.exists(database_path):
        redirect('/db/create')
    return

def create_new_db():
    Bill.connect_to_sqlite(database_path)
    Bill.cursor.executescript(db_template)
    Bill.close_sqlite()
    return


def build_where(var_name, var, counter):
    statement = []
    if counter:
        statement.append(' AND')
    if var_name == "dates":
        if re.search(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', var):
            statement.append(f' {var_name} = "{var}",')
        elif re.search(r'[0-9]{4}-[0-9]{2}', var):
            var += '-%'
            statement.append(f' {var_name} LIKE "{var}",')
    elif var_name == 'name':
        statement.append(f' {var_name} LIKE "%{var}%",')
    elif var_name == 'price':
        statement.append(f' {var_name} LIKE "{var}%",')
    else:
        statement.append(f' {var_name} = "{var}",')
    statement = ''.join(statement)
    return statement

@app.route('/')
def hello_world():
    return 'Working fine!'

@app.route('/greet')
def greet():
    name = request.args.get('name')
    print('name', name)
    if name:
        return f'Hello, {name}!'
    else:
        return 'Hello, Guest!'

@app.route('/db/create', methods=['GET', 'POST'])
def create_db():
    if request.method == 'GET':
        if not os.path.exists(database_path):
            create_new_db()
            return 'DB was successfully created for the first time'
        with open('./htmls/create-confirmation.html') as f:
            confirm_create = f.read()
        return confirm_create
    elif request.method == 'POST':
        last_id = request.form.get('lastBillId')
        Bill.connect_to_sqlite(database_path)
        #getting last id
        Bill.cursor.execute('SELECT MAX(id) AS last_transaction_number FROM bills;')
        fetch_data = Bill.cursor.fetchone()
        # None if there is no rows in db
        if fetch_data[0] is not None and fetch_data[0][0] != last_id:
            Bill.close_sqlite()
            return f'last id does not match the database ({fetch_data=}, {last_id=})'
        # close connection with previous db which maybe would deleted
        Bill.close_sqlite()
        if os.path.exists(database_path):
            os.remove(database_path)

        create_new_db()
        return 'DB was successfully created'


@app.route('/bill/form')
def bill_form_render():
    check_db_exist()
    with open('./htmls/custom-bill-form.html') as f:
        bill_form = f.read()
    return bill_form

@app.route('/bill')
def bill():
    name = request.args.get('name')
    date = request.args.get('date')
    price = request.args.get('price')
    currency = request.args.get('currency')
    exchange_rate = request.args.get('exchange-rate')
    country = request.args.get('country')
    tags = request.args.get('tags')

    if None in (name, date, price, currency, exchange_rate, country, tags,):
        return 'You need to provide: name, date, price, currency, exchange-rate, country, tags'

    check_db_exist()
    Bill.connect_to_sqlite(database_path)
     
    bill = Bill(
        name=name,
        date=date,
        price=float(price),
        currency=currency,
        exchange_rate=exchange_rate,
        country=country,
        tags=tags
    )
    bill.insert(force_dup=False)
    Bill.close_sqlite()
    return bill.__repr__()

@app.route('/qr')
def from_qr():
    check_db_exist()
    qr_link = request.args.get('link')
    forcefully = request.args.get('force', False)
    if not qr_link:
        return 'link attribute is empty'

    Bill.connect_to_sqlite(database_path)

    bill = Bill().from_qr(qr_link)
    bill.currency = "rsd"
    bill.country = "serbia"
    bill.exchange_rate = "1"
    bill.insert(force_dup=forcefully)

    if bill.dup_list and not forcefully:
        response = '<p>finded duplicates in db ({})<br>you can add <b>FORCE</b> attribute</p>'.format(len(bill.dup_list))
        header = ['id', 'name', 'date', 'price', 'currency', 'bill_text']
        response += build_html_table(header, bill.dup_list)
        return response

    Bill.close_sqlite()

    response = []
    if forcefully:
        response.append('FORCE WAS USED')
    response.extend([str(bill.timestamp), bill.name, bill.date, str(bill.price), bill.currency, bill.exchange_rate, bill.country, str(len(bill.items)), bill.link])
    response = build_html_list(response)

    bill = None
    return response

@app.route('/db/search')
def db_search():
    id = request.args.get('id', None)
    name = request.args.get('name', None)
    date = request.args.get('date', None)
    price = request.args.get('price', None)
    currency = request.args.get('cur', None)
    country = request.args.get('cy', None)
    item = request.args.get('item', None)

    Bill.connect_to_sqlite(database_path)

    if item:
        sql_statement = f"""
            SELECT id, name, price, price_one, quantity
            FROM items
            WHERE name LIKE '%{item}%'
        """
        table_header = ['id', 'name', 'price', 'price_one', 'quantity']
    else:
        sql_statement = """
            SELECT id, name, dates, price, currency, country
            FROM bills
            WHERE 
        """
        table_header = ['id', 'name', 'dates', 'price', 'currency', 'country']

        counter = 0
        if id:
            sql_statement += build_where('id', id, counter)
            counter += 1
        if name:
            sql_statement += build_where('name', name, counter)
            counter += 1
        if date:
            sql_statement += build_where('dates', date, counter)
            counter += 1
        if price:
            sql_statement += build_where('price', price, counter)
            counter += 1
        if currency:
            sql_statement += build_where('currency', currency, counter)
            counter += 1
        if country:
            sql_statement += build_where('country', country, counter)
            counter += 1
        if counter == 0:
            return 'Provide attributes to the url. Options name, date, price, cur, cy'
        if sql_statement[-1] == ',':
            sql_statement = sql_statement[:-1]
        sql_statement += ';'

    Bill.cursor.execute(sql_statement)
    data = Bill.cursor.fetchall()
    if len(data) == 0:
        data = 'Query is empty'
    html_table = build_html_table(table_header, data)
    Bill.close_sqlite()
    return html_table

@app.route('/db/delete')
def delete_rows():
    bill_id = request.args.get('id')
    confirm = request.args.get('confirm', None)
    if not bill_id:
        return 'id attribute is empty'

    Bill.connect_to_sqlite(database_path)

    if confirm is None:
        return 'confirm your transaction'
    Bill.cursor.execute(f'DELETE FROM items WHERE id = {bill_id};')
    Bill.cursor.execute(f'DELETE FROM bills WHERE id = {bill_id};')

    Bill.close_sqlite()
    return f'Bill with id = {bill_id} was deleted'

@app.route('/db/save')
def download_db():
    Bill.connect_to_sqlite(database_path)
    Bill.check_unique_names()
    Bill.close_sqlite()

    return send_file('./bills.db', as_attachment=True)

@app.route('/db/upload', methods=['GET'])
def upload_form_render():
    with open('./htmls/upload.html') as f:
        upload_html = f.read()
    return upload_html

@app.route('/db/upload', methods=['POST'])
def upload_db():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        # Save the uploaded file to a specific folder
        uploaded_file.save('./bills.db')
        return 'File successfully uploaded.'
    else:
        return 'No file selected for uploading.'

if __name__ == '__main__':
    app.run(debug=True)
