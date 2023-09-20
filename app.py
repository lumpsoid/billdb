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

if __name__ == '__main__':
    app.run(debug=True)
