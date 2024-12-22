def populate_db():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    products = [
        ('Средняя игра', 'Описание средней игры', 1000),
        ('Большая игра', 'Описание большой игры', 2000),
        ('Очень большая игра', 'Описание очень большой игры', 3000),
        ('Другие предложения', 'Описание других предложений', 500)
    ]

    cursor.executemany("INSERT INTO Products (title, description, price) VALUES (?, ?, ?)", products)

    conn.commit()
    conn.close()


# Вызов функции для пополнения базы данных (один раз)
populate_db()
