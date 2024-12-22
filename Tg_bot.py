import telebot
from telebot import types
from telebot.storage import StateMemoryStorage
from config import (API_TOKEN, MEDIUM_GAME_PRICE, MEDIUM_GAME_DESCRIPTION,
                    BIG_GAME_PRICE, BIG_GAME_DESCRIPTION,
                    VERY_BIG_GAME_PRICE, VERY_BIG_GAME_DESCRIPTION,
                    OTHER_OFFERS_PRICE, OTHER_OFFERS_DESCRIPTION)
from PIL import Image
import sqlite3

bot = telebot.TeleBot(API_TOKEN, parse_mode=None)
storage = StateMemoryStorage()

# Клавиатуры
kb1 = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = types.KeyboardButton(text='Рассчитать')
button2 = types.KeyboardButton(text='Информация')
button3 = types.KeyboardButton(text='Купить')
button4 = types.KeyboardButton(text='О нас')
button5 = types.KeyboardButton(text='Регистрация')
kb1.add(button1, button2).add(button3, button4).add(button5)


def buy_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Продукт № 1", callback_data="medium_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 2", callback_data="big_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 3", callback_data="very_big_game"))
    markup.add(types.InlineKeyboardButton("Продукт № 4", callback_data="other_offers"))
    return markup


def resize_image(input_path, output_path, size):
    with Image.open(input_path) as img:
        img.thumbnail(size)
        img.save(output_path)


# База данных
def initiate_db():
    connection = sqlite3.connect('products.dp')
    cursor = connection.cursor()

    # Создание таблицы Products, если она ещё не создана
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        price TEXT NOT NULL
    )
    ''')

    # Создание таблицы Users, если она ещё не создана
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users(
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER NOT NULL,
        balance INTEGER NOT NULL DEFAULT 1000
    )
    ''')

    connection.commit()
    connection.close()


def check_and_populate_products():
    connection = sqlite3.connect('products.dp')
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Products')
    count = cursor.fetchone()[0]

    if count == 0:
        for i in range(1, 5):
            cursor.execute(
                'INSERT INTO Products(title, description, price) VALUES (?, ?, ?)',
                (f'Продукт {i}', f'Описание {i}', f'{i * 100}')
            )
    else:
        pass

    connection.commit()
    connection.close()


def get_all_products():
    connection = sqlite3.connect('products.dp')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Products')
    products = cursor.fetchall()
    connection.commit()
    connection.close()
    return products


def add_user(username, email, age):
    connection = sqlite3.connect('products.dp')
    cursor = connection.cursor()

    cursor.execute(
        'INSERT INTO Users(username, email, age) VALUES (?, ?, ?)',
        (username, email, age)
    )

    connection.commit()
    connection.close()


def is_included(username):
    connection = sqlite3.connect('products.dp')
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Users WHERE username = ?', (username,))
    count = cursor.fetchone()[0]

    connection.close()

    return count > 0


@bot.message_handler(commands=['start'])
def start(message):
    initiate_db()  # Инициализация базы данных при старте
    bot.send_message(message.chat.id, "Привет! Я бот, помогающий твоему здоровью.", reply_markup=kb1)


@bot.message_handler(func=lambda message: message.text == "О нас")
def about_us(message):
    bot.send_message(message.chat.id,
                     "Мы команда профессионалов, помогающих вам заботиться о своем здоровье и достигать ваших целей!")


@bot.message_handler(func=lambda message: message.text == "Информация")
def info(message):
    bot.send_message(message.chat.id,
                     "Расчет по формуле Миффлина-Сан Жеора:\n"
                     "10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) - 161 (для женщин)\n"
                     "10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5 (для мужчин)")


@bot.message_handler(func=lambda message: message.text == "Рассчитать")
def schet(message):
    bot.send_message(message.chat.id, 'Выберите ваш пол:',
                     reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('Мужчина', 'Женщина'))
    bot.register_next_step_handler(message, process_gender)


def process_gender(message):
    gender = message.text
    if gender not in ['Мужчина', 'Женщина']:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Мужчина' или 'Женщина'.")
        return
    bot.send_message(message.chat.id, 'Введите свой возраст:')
    bot.register_next_step_handler(message, lambda msg: process_age(msg, gender))


def process_age(message, gender):
    age = int(message.text)
    bot.send_message(message.chat.id, 'Введите свой рост (в см):')
    bot.register_next_step_handler(message, lambda msg: process_growth(msg, age, gender))


@bot.message_handler(func=lambda message: message.text == "Купить")
def buy(message):
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=buy_keyboard())


@bot.callback_query_handler(func=lambda call: call.data in ["medium_game", "big_game", "very_big_game", "other_offers"])
def handle_buy_option(call):
    product_info = {
        "medium_game": (MEDIUM_GAME_PRICE, MEDIUM_GAME_DESCRIPTION, 'картинка 1.jpg'),
        "big_game": (BIG_GAME_PRICE, BIG_GAME_DESCRIPTION, 'картинка 2.jpg'),
        "very_big_game": (VERY_BIG_GAME_PRICE, VERY_BIG_GAME_DESCRIPTION, 'картинка 3.jpg'),
        "other_offers": (OTHER_OFFERS_PRICE, OTHER_OFFERS_DESCRIPTION, 'картинка 4.jpg')
    }

    price, description, image_path = product_info[call.data]

    resized_image_path = f"resized_{image_path}"
    resize_image(image_path, resized_image_path, (800, 800))

    # Отправляем изображение товара
    with open(image_path, 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo)

    # Отправляем информацию о продукте и цену
    bot.send_message(call.message.chat.id,
                     f"{description}\nЦена: {price} рублей.",
                     reply_markup=types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("Купить", url="https://example.com")))

    bot.answer_callback_query(call.id)  # Убираем спиннер загрузки


# Обработчик для кнопки "Регистрация"
@bot.message_handler(func=lambda message: message.text == "Регистрация")
def registration_start(message):
    print(f'Пользователь нажал кнопку: Регистрация')
    bot.send_message(message.chat.id, 'Введите имя пользователя (только латинский алфавит):')
    bot.register_next_step_handler(message, process_username)


def process_username(message):
    username = message.text.strip()
    if not username.isalpha():
        bot.send_message(message.chat.id,
                         'Имя пользователя должно содержать только латинские буквы. Пожалуйста, введите другое имя.')
        bot.register_next_step_handler(message, process_username)
        return

    if is_included(username):
        bot.send_message(message.chat.id, 'Пользователь с таким именем уже существует. Пожалуйста, введите другое имя.')
        bot.register_next_step_handler(message, process_username)
        return

    bot.send_message(message.chat.id, 'Введите свой email:')
    bot.register_next_step_handler(message, lambda msg: process_email(msg, username))


def process_email(message, username):
    email = message.text.strip()
    print(f"Получен ввод email: '{email}'")
    if is_email_included(email):
        bot.send_message(message.chat.id, 'Email уже зарегистрирован. Пожалуйста, введите другой email.')
        bot.register_next_step_handler(message, lambda msg: process_email(msg, username))
        return

    bot.send_message(message.chat.id, 'Введите свой возраст:')
    bot.register_next_step_handler(message, lambda msg: process_age_registration(msg, username, email))


def add_user(username, email, age):
    print(f"Добавлен пользователь: {username}, {email}, {age}")


def process_age_registration(message, username, email):
    try:
        age_input = message.text.strip()
        print(f"Получен ввод возраста: '{age_input}'")

        if not age_input.isdigit():
            raise ValueError("Возраст должен быть числом.")

        age = int(age_input)

        if age < 1 or age > 120:
            raise ValueError("Возраст должен быть между 1 и 120.")

        add_user(username, email, age)
        bot.send_message(message.chat.id, "Регистрация прошла успешно!")
    except ValueError as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}. Пожалуйста, введите корректный возраст.")
        bot.register_next_step_handler(message, lambda msg: process_age_registration(msg, username, email))


# Функция для проверки наличия email в базе данных
def is_email_included(email):
    connection = sqlite3.connect('products.db')
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Users WHERE email = ?', (email,))
    count = cursor.fetchone()[0]

    connection.close()

    return count > 0


# Функция для проверки наличия имени пользователя в базе данных
def is_included(username):
    connection = sqlite3.connect('products.db')
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Users WHERE username = ?', (username,))
    count = cursor.fetchone()[0]

    connection.close()

    return count > 0


# Функция для проверки наличия имени пользователя в базе данных
def is_included(username):
    connection = sqlite3.connect('products.db')
    cursor = connection.cursor()

    cursor.execute('SELECT COUNT(*) FROM Users WHERE username = ?', (username,))
    count = cursor.fetchone()[0]

    connection.close()

    return count > 0


# Остальные функции и обработчики...
@bot.message_handler(func=lambda message: True)
def all_messages(message):
    bot.send_message(message.chat.id, "Введите команду /start, чтобы начать общение.")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
