import sqlite3

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
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_stats (
            user_id INTEGER,
            correct_answers INTEGER DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
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
    
    conn.commit()
    conn.close()

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

# Функции для работы с корзиной (заглушки, будут реализованы позже)
def add_to_cart(user_id, product_id):
    pass

def get_cart(user_id):
    pass

def update_cart_item(user_id, product_id, quantity):
    pass

def remove_from_cart(user_id, product_id):
    pass
