import logging
from flask import Flask, request, send_file
import bill as bm
import re

app = Flask(__name__)

# Configure Flask logging
app.logger.setLevel(logging.DEBUG)  # Set the desired logging level
handler = logging.FileHandler("./flask.log")  # Replace with the desired path inside the container
handler.setLevel(logging.DEBUG)  # Set the desired logging level for Flask logs
app.logger.addHandler(handler)

database_path = './bills.db'


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

def build_html_table(table_header, data):
        # Generate HTML table dynamically from the list of tuples
    table_content = '<table border="1">'

    table_content += '<tr>'
    for name in table_header:
        table_content += '<th>{}</th>'.format(name)
    table_content += '</tr>'

    for row in data:
        table_content += '<tr>'
        for item in row:
            table_content += '<td>{}</td>'.format(item)
        table_content += '</tr>'
    table_content += '</table>'
    return table_content

def build_html_list(data):
    # Generate HTML list dynamically from the Python list
    list_content = '<ul>'
    for item in data:
        if re.match(r'http', item):
            list_content += '<li><a href="{}">Link</a></li>'.format(item)
            continue
        list_content += '<li>{}</li>'.format(item)
    # Add a list item with an anchor element at the end of the list
    list_content += '</ul>'
    return list_content

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

@app.route('/bill')
def bill():
    name = request.args.get('name')
    date = request.args.get('date')
    price = float(request.args.get('price'))
    currency = request.args.get('currency')
    exchange_rate = request.args.get('exchange-rate')
    country = request.args.get('country')
    tags = request.args.get('tags')

    bm.Bill.connect_to_sqlite(database_path)
     
    bill = bm.Bill(
        name=name,
        date=date,
        price=price,
        currency=currency,
        exchange_rate=exchange_rate,
        country=country,
        tags=tags
    )
    bill.insert(force_dup=False)
    bm.Bill.close_sqlite()
    return bill.__repr__()

@app.route('/qr')
def from_qr():
    qr_link = request.args.get('link')
    forcefully = request.args.get('force', False)
    if not qr_link:
        return 'link attribute is empty'

    bm.Bill.connect_to_sqlite(database_path)

    bill = bm.Bill().from_qr(qr_link)
    bill.currency = "rsd"
    bill.country = "serbia"
    bill.exchange_rate = "1"
    bill.insert(force_dup=forcefully)

    if bill.dup_list and not forcefully:
        response = '<p>finded duplicates in db ({})<br>you can add <b>FORCE</b> attribute</p>'.format(len(bill.dup_list))
        header = ['id', 'name', 'date', 'price', 'currency', 'bill_text']
        response += build_html_table(header, bill.dup_list)
        return response

    bm.Bill.close_sqlite()

    response = []
    if forcefully:
        response.append('FORCE WAS USED')
    response.extend([str(bill.timestamp), bill.name, bill.date, str(bill.price), bill.currency, bill.exchange_rate, bill.country, str(len(bill.items)), bill.tags, bill.link])
    print(response)
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

    bm.Bill.connect_to_sqlite(database_path)

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

    bm.Bill.cursor.execute(sql_statement)
    data = bm.Bill.cursor.fetchall()
    if len(data) == 0:
        data = 'Query is empty'
    html_table = build_html_table(table_header, data)
    bm.Bill.close_sqlite()
    return html_table

@app.route('/db/delete')
def delete_rows():
    bill_id = request.args.get('id')
    confirm = request.args.get('confirm', None)
    if not bill_id:
        return 'id attribute is empty'

    bm.Bill.connect_to_sqlite(database_path)

    if confirm is None:
        return 'confirm your transaction'
    bm.Bill.cursor.execute(f'DELETE FROM items WHERE id = {bill_id};')
    bm.Bill.cursor.execute(f'DELETE FROM bills WHERE id = {bill_id};')

    bm.Bill.close_sqlite()
    return f'Bill with id = {bill_id} was deleted'

@app.route('/db/save')
def download_db():
    bm.Bill.connect_to_sqlite(database_path)
    bm.Bill.check_unique_names()
    bm.Bill.close_sqlite()

    return send_file('./bills.db', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
