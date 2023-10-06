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

    if bill.dup_list:
        list_to_return = [f'finded duplicates in db ({len(bill.dup_list)})', 'you can add FORCE attribute']
        ids = []
        names = []
        dates = []
        prices = []
        currencies = []
        bill_texts = []
        for item in bill.dup_list:
            i_id, i_name, i_date, i_price, i_currency, i_bill_text = item
            ids.append(str(i_id))
            names.append(i_name)
            dates.append(i_date)
            prices.append(i_price)
            currencies.append(i_currency)
            bill_texts.append(i_bill_text)
        list_to_return.extend([ids, names, dates, prices, currencies, bill_texts])
        return list_to_return

    bm.Bill.close_sqlite()

    response = bill.__repr__()
    if forcefully:
        response = 'FORCE WAS USED.\n' + response

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
