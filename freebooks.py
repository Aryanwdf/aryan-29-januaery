import sqlite3
conn=sqlite3.connect('database/freebooks.db')
cur=conn.cursor()
cur.execute('''CREATE TABLE users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fname TEXT,
        lname TEXT,
        email TEXT,
        city TEXT,
        contact TEXT,
        password TEXT
        );''')

cur.execute('''CREATE TABLE total_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bookname TEXT,
        book_detail TEXT,
        book_image TEXT,
        status INTEGER DEFAULT 1 NOT NULL,
        user_id INTEGER,
        rent_user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (rent_user_id) REFERENCES users(id)
);''')


print('table created ')
conn.commit()
conn.close()

