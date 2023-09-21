from flask import Flask, request
import bill as bm

app = Flask(__name__)
database_path = './bills.db'

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
    country = request.args.get('country')
    tags = request.args.get('tags')

    bm.Bill.connect_to_sqlite(database_path)
     
    bill = bm.Bill(
        name=name,
        date=date,
        price=price,
        currency=currency,
        country=country,
        tags=tags
    )
    bill.insert()
    bm.Bill.disconnect_sqlite()
    return bill.__repr__()

@app.route('/qr')
def from_qr():
    qr_link = request.args.get('link')
    if not qr_link:
        return 'link attribute is empty'

    bm.Bill.connect_to_sqlite(database_path)

    bill = bm.Bill().from_qr(qr_link)
    bill.currency = "rsd"
    bill.country = "serbia"
    bill.insert()
    # test for new unique item's names
    cur = bm.Bill.connector.cursor()
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
    else:
        print(f'{len(data_unique_names)} new unique items')
        cur.execute(add_unique_names_query)
    bm.Bill.connector.commit()
    cur.close()
    bm.Bill.disconnect_sqlite()

    return 'Transaction commited'

def build_where(var_name, var, counter):
    statement = []
    if counter:
        statement.append(' AND')
    statement.append(f' {var_name} = {var},')
    statement = ''.join(statement)
    return statement


@app.route('/db/search')
def db_search():
    id = request.args.get('id', None)
    name = request.args.get('name', None)
    date = request.args.get('date', None)
    price = request.args.get('price', None)
    currency = request.args.get('cur', None)
    country = request.args.get('cy', None)

    bm.Bill.connect_to_sqlite(database_path)
    cur = bm.Bill.connector.cursor()

    sql_statement = """
        SELECT id, name, dates, price, currency, country
        FROM bills
        WHERE 
    """
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

    cur.execute(sql_statement)
    data = cur.fetchall()
    if len(data) == 0:
        data = 'Query is empty'

    cur.close()
    bm.Bill.disconnect_sqlite()
    return data


if __name__ == '__main__':
    app.run(debug=True)
