from flask import Flask, request, send_file
import bill as bm

app = Flask(__name__)

# Configure Flask logging
app.logger.setLevel(logging.DEBUG)  # Set the desired logging level
handler = logging.FileHandler("./flask.log")  # Replace with the desired path inside the container
handler.setLevel(logging.DEBUG)  # Set the desired logging level for Flask logs
app.logger.addHandler(handler)

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
