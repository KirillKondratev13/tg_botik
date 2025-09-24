# Обновить товар
def update_product(product_name, category_id, param, new_value):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    if param == "цена":
        cursor.execute('UPDATE products SET price = ? WHERE name = ? AND category_id = ?', (float(new_value), product_name, category_id))
    elif param == "название":
        cursor.execute('UPDATE products SET name = ? WHERE name = ? AND category_id = ?', (new_value, product_name, category_id))
    elif param == "описание":
        cursor.execute('UPDATE products SET description = ? WHERE name = ? AND category_id = ?', (new_value, product_name, category_id))
    conn.commit()
    conn.close()

# Добавить товар
def add_product(name, category_id, price, description):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, category_id, price, description) VALUES (?, ?, ?, ?)', (name, category_id, float(price), description))
    conn.commit()
    conn.close()

# Удалить товар
def delete_product(product_name, category_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE name = ? AND category_id = ?', (product_name, category_id))
    conn.commit()
    conn.close()

# Получить заказы по статусу
def get_orders_by_status(status):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT order_number, user_id, address, phone, total_amount, created_at FROM orders WHERE status = ? ORDER BY created_at DESC', (status,))
    orders = cursor.fetchall()
    conn.close()
    return orders

# Изменить статус заказа
def update_order_status(order_number, new_status):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE order_number = ?', (new_status, order_number))
    conn.commit()
    conn.close()
# Регистрировать пользователя при первом взаимодействии
def register_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()
# Получить все новые вопросы поддержки
def get_support_questions():
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_id, question, created_at FROM support_questions WHERE status = 'new' ORDER BY created_at ASC
    ''')
    questions = cursor.fetchall()
    conn.close()
    return questions

# Ответить на вопрос поддержки
def answer_support_question(question_id, answer):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE support_questions SET status = 'answered', answer = ? WHERE id = ?
    ''', (answer, question_id))
    conn.commit()
    conn.close()
import sqlite3
import random
import string

def init_db():
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    
    # Существующие таблицы

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    # Таблица администраторов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administrators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            password TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_stats (
            user_id INTEGER PRIMARY KEY,
            correct_answers INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0
        )
    ''')
    
    # Новая таблица для вопросов в поддержку
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            status TEXT DEFAULT 'new',
            answer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Таблицы для корзины
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category_id INTEGER,
            price REAL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Таблица для справочника групп
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bands_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_name TEXT UNIQUE,
            country TEXT
        )
    ''')
    
    # Заполняем справочник групп
    bands_data = [
        ('The Beatles', 'Великобритания'),
        ('Queen', 'Великобритания'),
        ('Nirvana', 'США'),
        ('Led Zeppelin', 'Великобритания'),
        ('AC/DC', 'Австралия'),
        ('Rammstein', 'Германия'),
        ('Кино', 'Россия'),
        ('DDT', 'Россия'),
        ('Ария', 'Россия'),
        ('Scorpions', 'Германия')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO bands_directory (band_name, country)
        VALUES (?, ?)
    ''', bands_data)
    
    # Заполняем категории и товары
    categories_data = [
        ('Гитары',),
        ('Барабаны',),
        ('Басс-гитары',),
        ('Пианино',)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO categories (name)
        VALUES (?)
    ''', categories_data)
    
    products_data = [
        ('Fender Stratocaster', 1, 45000, 'Легендарная электрогитара'),
        ('Gibson Les Paul', 1, 65000, 'Классическая электрогитара'),
        ('Yamaha Stage Custom', 2, 80000, 'Барабанная установка для начинающих'),
        ('Pearl Export', 2, 120000, 'Профессиональная барабанная установка'),
        ('Fender Precision Bass', 3, 50000, 'Басс-гитара для любого стиля'),
        ('Ibanez SR500', 3, 55000, 'Универсальная басс-гитара'),
        ('Yamaha P-125', 4, 70000, 'Цифровое пианино для дома'),
        ('Kawai ES920', 4, 120000, 'Профессиональное цифровое пианино')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO products (name, category_id, price, description)
        VALUES (?, ?, ?, ?)
    ''', products_data)
    
    # Таблица для заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            user_id INTEGER,
            address TEXT,
            phone TEXT,
            status TEXT DEFAULT 'new',
            total_amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Таблица для товаров в заказах
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            price REAL,
            quantity INTEGER,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    conn.commit()
    conn.close()

# Проверка, является ли пользователь администратором
def is_admin(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM administrators WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# Проверка пароля администратора
def check_admin_password(user_id, password):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM administrators WHERE user_id = ? AND password = ?', (user_id, password))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

# Получить список всех пользователей
def get_all_users():
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, first_name, last_name, is_blocked FROM users ORDER BY registration_date DESC')
    users = cursor.fetchall()
    conn.close()
    return users

# Заблокировать пользователя
def block_user(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Разблокировать пользователя
def unblock_user(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# Проверить, заблокирован ли пользователь
def is_user_blocked(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def get_quiz_stats(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT correct_answers, total_attempts FROM quiz_stats WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return 0, 0

def update_quiz_stats(user_id, is_correct):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()

    # Пробуем обновить существующую запись
    cursor.execute('''
        UPDATE quiz_stats 
        SET correct_answers = correct_answers + ?, total_attempts = total_attempts + 1 
        WHERE user_id = ?
    ''', (1 if is_correct else 0, user_id))

    # Если запись не была обновлена (не найдена), вставляем новую
    if cursor.rowcount == 0:
        cursor.execute('''
            INSERT INTO quiz_stats (user_id, correct_answers, total_attempts)
            VALUES (?, ?, 1)
        ''', (user_id, 1 if is_correct else 0))

    conn.commit()
    conn.close()

# ... остальные функции из предыдущего кода ...

# Функции для работы с поддержкой
def add_support_question(user_id, question):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO support_questions (user_id, question)
        VALUES (?, ?)
    ''', (user_id, question))
    conn.commit()
    conn.close()

# Функции для работы со справочником
def get_band_country(band_name):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT country FROM bands_directory WHERE band_name = ?', (band_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None



def get_categories():
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM categories ORDER BY name')
    categories = cursor.fetchall()
    conn.close()
    return categories

def get_products_by_category(category_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, price, description
        FROM products
        WHERE category_id = ?
        ORDER BY name
    ''', (category_id,))
    products = cursor.fetchall()
    conn.close()
    return products

def get_product(product_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.price, p.description, c.name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# Функции для работы с корзиной
def add_to_cart(user_id, product_id, quantity=1):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()

    # Проверяем, есть ли уже товар в корзине
    cursor.execute('SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    existing_item = cursor.fetchone()

    if existing_item:
        # Обновляем количество
        new_quantity = existing_item[1] + quantity
        cursor.execute('UPDATE cart_items SET quantity = ? WHERE id = ?', (new_quantity, existing_item[0]))
    else:
        # Добавляем новый товар
        cursor.execute('INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)',
                      (user_id, product_id, quantity))

    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ci.id, p.name, p.price, ci.quantity, p.id as product_id
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.id
        WHERE ci.user_id = ?
        ORDER BY p.name
    ''', (user_id,))
    cart_items = cursor.fetchall()

    # Вычисляем общую сумму
    total = sum(item[2] * item[3] for item in cart_items)

    conn.close()
    return cart_items, total

def update_cart_item(user_id, product_id, quantity):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()

    if quantity <= 0:
        # Удаляем товар, если количество <= 0
        cursor.execute('DELETE FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    else:
        # Обновляем количество
        cursor.execute('UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?',
                      (quantity, user_id, product_id))

    conn.commit()
    conn.close()

def remove_from_cart(user_id, product_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart_items WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    conn.commit()
    conn.close()

def clear_cart(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))



# Функция для генерации номера заказа
def generate_order_number():
    letters = string.ascii_uppercase
    digits = string.digits
    return f"ORD-{''.join(random.choice(letters) for _ in range(3))}{''.join(random.choice(digits) for _ in range(4))}"

# Функция для создания заказа
def create_order(user_id, address, phone, total_amount, cart_items):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    
    order_number = generate_order_number()
    
    # Создаем заказ
    cursor.execute('''
        INSERT INTO orders (order_number, user_id, address, phone, total_amount)
        VALUES (?, ?, ?, ?, ?)
    ''', (order_number, user_id, address, phone, total_amount))
    
    order_id = cursor.lastrowid
    
    # Добавляем товары в заказ
    for item_id, product_name, price, quantity, product_id in cart_items:
        cursor.execute('''
            INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, product_name, price, quantity))
    
    # Очищаем корзину
    cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    return order_number

# Функция для получения заказов пользователя
def get_user_orders(user_id):
    conn = sqlite3.connect('music_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_number, address, phone, status, total_amount, created_at
        FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders



    conn.commit()
    conn.close()
