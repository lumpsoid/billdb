db_bills_table = '''
CREATE TABLE bills (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    dates TEXT NOT NULL,
    price REAL NOT NULL,
    tag TEXT,
    currency TEXT,
    exchange_rate REAL,
    country TEXT,
    link TEXT,
    bill TEXT
);

'''
db_items_table = '''
CREATE TABLE items (
    id INTEGER NOT NULL,
    photo BLOB,
    name TEXT,
    price REAL,
    price_one REAL,
    quantity REAL,
    FOREIGN KEY(id) REFERENCES bills(id)
);

'''
db_items_meta_table = '''
CREATE TABLE items_meta (
    name TEXT UNIQUE,
    tag TEXT,
    PRIMARY KEY(name)
);

'''
db_template = db_bills_table + db_items_table + db_items_meta_table
