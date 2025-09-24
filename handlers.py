from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
import random
from database import (
    update_quiz_stats, get_quiz_stats, add_support_question, get_band_country,
    get_categories, get_products_by_category, get_product, add_to_cart,
    get_cart, update_cart_item, remove_from_cart, clear_cart,
    create_order, get_user_orders, generate_order_number,
    is_admin, check_admin_password, get_all_users, block_user, unblock_user, is_user_blocked,
    get_support_questions, answer_support_question,
    update_product, add_product, delete_product, get_orders_by_status, update_order_status
)
# --- Админ функционал ---
from music_data import MUSIC_QUIZ_DATA

# Переменная для хранения состояния пользователей
user_states = {}
# Переменная для хранения состояния админов
admin_states = {}

# --- Админ функционал ---
ADMIN_PASSWORD_PROMPT = "Введите пароль администратора:"

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_states[user_id] = {"state": "waiting_password"}
    await update.message.reply_text(ADMIN_PASSWORD_PROMPT)

async def handle_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states or admin_states[user_id].get("state") != "waiting_password":
        return
    password = update.message.text.strip()
    if check_admin_password(user_id, password):
        admin_states[user_id] = {"state": "admin_menu"}
        await show_admin_menu(update, context)
    else:
        await update.message.reply_text("Неверный пароль или недостаточно прав.")
        del admin_states[user_id]

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["👥 Пользователи", "🚫 Заблокировать", "✅ Разблокировать"],
        ["🆘 Поддержка", "✉️ Ответить"],
        ["✏️ Редактировать товар", "➕ Добавить товар"],
        ["🗑️ Удалить товар", "📦 Заказы"],
        ["◀️ Выйти"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Панель администратора. Выберите действие:", reply_markup=reply_markup)

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if user_id not in admin_states:
        return

    # --- Управление товарами ---
    # Редактирование товара: выбор категории
    if admin_states[user_id].get("state") == "edit_product_category":
        categories = get_categories()
        keyboard = [[cat[1]] for cat in categories] + [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        category = update.message.text.strip()
        if category == "🔙 Назад":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        admin_states[user_id]["state"] = "edit_product_select"
        admin_states[user_id]["edit_category"] = category
        await update.message.reply_text("Выберите товар для редактирования:", reply_markup=reply_markup)
        return
    # Редактирование товара: выбор товара
    if admin_states[user_id].get("state") == "edit_product_select":
        category_name = admin_states[user_id]["edit_category"]
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        if not category_id:
            await update.message.reply_text("Категория не найдена.")
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        products = get_products_by_category(category_id)
        if not products:
            await update.message.reply_text("В этой категории нет товаров.")
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        keyboard = [[prod[1]] for prod in products] + [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        product = update.message.text.strip()
        if product == "🔙 Назад":
            admin_states[user_id]["state"] = "edit_product_category"
            await update.message.reply_text("Выберите категорию для редактирования товара.")
            return
        admin_states[user_id]["state"] = "edit_product_param"
        admin_states[user_id]["edit_product"] = product
        await update.message.reply_text("Выберите параметр для редактирования: цена, название, описание.", reply_markup=ReplyKeyboardMarkup([["цена"], ["название"], ["описание"], ["🔙 Назад"]], resize_keyboard=True, one_time_keyboard=True))
        return
    # Редактирование товара: выбор параметра
    if admin_states[user_id].get("state") == "edit_product_param":
        param = update.message.text.strip().lower()
        if param == "🔙 назад":
            admin_states[user_id]["state"] = "edit_product_select"
            await update.message.reply_text("Выберите товар для редактирования.")
            return
        if param not in ["цена", "название", "описание"]:
            await update.message.reply_text("Некорректный параметр. Выберите: цена, название, описание или нажмите 'Назад'.")
            return
        admin_states[user_id]["state"] = "edit_product_value"
        admin_states[user_id]["edit_param"] = param
        await update.message.reply_text(f"Введите новое значение для параметра '{param}':")
        return
    # Редактирование товара: ввод значения
    if admin_states[user_id].get("state") == "edit_product_value":
        new_value = update.message.text.strip()
        category_name = admin_states[user_id]["edit_category"]
        product_name = admin_states[user_id]["edit_product"]
        param = admin_states[user_id]["edit_param"]
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        if category_id:
            update_product(product_name, category_id, param, new_value)
            await update.message.reply_text("Товар успешно обновлен.")
        else:
            await update.message.reply_text("Ошибка: категория не найдена.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # --- Добавление товара ---
    if admin_states[user_id].get("state") == "add_product_category":
        category = update.message.text.strip()
        if category == "🔙 Назад":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        admin_states[user_id]["add_category"] = category
        admin_states[user_id]["state"] = "add_product_info"
        await update.message.reply_text("Введите название, цену и описание товара через запятую (пример: Гитара, 50000, Классная гитара)")
        return
    if admin_states[user_id].get("state") == "add_product_info":
        info = update.message.text.strip().split(",")
        if update.message.text.strip() == "🔙 Назад":
            admin_states[user_id]["state"] = "add_product_category"
            await update.message.reply_text("Введите категорию для нового товара.")
            return
        if len(info) != 3:
            await update.message.reply_text("Некорректный формат. Введите: название, цена, описание или нажмите 'Назад'.")
            return
        category_name = admin_states[user_id]["add_category"]
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        if category_id:
            add_product(info[0].strip(), category_id, info[1].strip(), info[2].strip())
            await update.message.reply_text("Товар успешно добавлен.")
        else:
            await update.message.reply_text("Ошибка: категория не найдена.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # --- Удаление товара ---
    if admin_states[user_id].get("state") == "delete_product_category":
        categories = get_categories()
        keyboard = [[cat[1]] for cat in categories] + [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        category = update.message.text.strip()
        if category == "🔙 Назад":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        admin_states[user_id]["state"] = "delete_product_select"
        admin_states[user_id]["delete_category"] = category
        await update.message.reply_text("Выберите товар для удаления:", reply_markup=reply_markup)
        return
    if admin_states[user_id].get("state") == "delete_product_select":
        category_name = admin_states[user_id]["delete_category"]
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        if not category_id:
            await update.message.reply_text("Категория не найдена.")
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        products = get_products_by_category(category_id)
        if not products:
            await update.message.reply_text("В этой категории нет товаров.")
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        keyboard = [[prod[1]] for prod in products] + [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        product = update.message.text.strip()
        if product == "🔙 Назад":
            admin_states[user_id]["state"] = "delete_product_category"
            await update.message.reply_text("Выберите категорию для удаления товара.")
            return
        admin_states[user_id]["state"] = "delete_product_confirm"
        admin_states[user_id]["delete_product"] = product
        await update.message.reply_text("Подтвердите удаление товара, отправив его название ещё раз или нажмите 'Назад':")
        return
    if admin_states[user_id].get("state") == "delete_product_confirm":
        category_name = admin_states[user_id]["delete_category"]
        product_name = update.message.text.strip()
        if product_name == "🔙 Назад":
            admin_states[user_id]["state"] = "delete_product_select"
            await update.message.reply_text("Выберите товар для удаления.")
            return
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        if category_id:
            delete_product(product_name, category_id)
            await update.message.reply_text("Товар успешно удалён.")
        else:
            await update.message.reply_text("Ошибка: категория не найдена.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # --- Заказы ---
    if admin_states[user_id].get("state") == "orders_status":
        status = update.message.text.strip().lower()
        status_map = {"новые": "new", "в работе": "in_progress", "выполненные": "completed"}
        if status == "🔙 назад":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        if status not in status_map:
            keyboard = [["новые"], ["в работе"], ["выполненные"], ["🔙 Назад"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Выберите статус: новые, в работе, выполненные или нажмите 'Назад'.", reply_markup=reply_markup)
            return
        orders = get_orders_by_status(status_map[status])
        if not orders:
            await update.message.reply_text("Нет заказов с этим статусом.")
        else:
            msg = f"Заказы со статусом '{status}':\n"
            for order in orders:
                msg += f"Номер: {order[0]}, UserID: {order[1]}, Сумма: {order[4]}, Адрес: {order[2]}, Телефон: {order[3]}, Время: {order[5]}\n"
            await update.message.reply_text(msg)
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return
    # Управление товарами и заказами
    if text == "✏️ Редактировать товар":
        await show_edit_product_categories(update, context)
        return
    if text == "➕ Добавить товар":
        admin_states[user_id]["state"] = "add_product_category"
        await update.message.reply_text("Введите категорию для нового товара.")
        # Реализация добавления товара далее
        return
    if text == "🗑️ Удалить товар":
        admin_states[user_id]["state"] = "delete_product_category"
        await update.message.reply_text("Выберите категорию для удаления товара.")
        # Реализация удаления товара далее
        return
    if text == "📦 Заказы":
        admin_states[user_id]["state"] = "orders_status"
        keyboard = [["новые"], ["в работе"], ["выполненные"], ["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Выберите статус заказов:", reply_markup=reply_markup)
        return
    if text == "👥 Пользователи":
        # Получаем список всех пользователей
        users = get_all_users()
        if users:
            msg = "Список пользователей:\n\n"
            for user in users:
                user_id, username, first_name, last_name, is_blocked = user
                status = "Заблокирован" if is_blocked else "Активен"
                msg += f"ID: {user_id}, Имя: {first_name} {last_name}, Логин: {username or 'не указан'}, Статус: {status}\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Пока нет зарегистрированных пользователей.")
        # Остаемся в админ-меню
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return
    if text == "🚫 Заблокировать":
        admin_states[user_id]["state"] = "block_waiting_user_id"
        await update.message.reply_text("Введите ID пользователя для блокировки:")
        return
    if text == "✅ Разблокировать":
        admin_states[user_id]["state"] = "unblock_waiting_user_id"
        await update.message.reply_text("Введите ID пользователя для разблокировки:")
        return
    if text == "🆘 Поддержка":
        # Показать новые вопросы поддержки
        questions = get_support_questions()
        if questions:
            msg = "Новые вопросы в поддержке:\n\n"
            for q in questions:
                msg += f"ID: {q[0]}, UserID: {q[1]}, Вопрос: {q[2]}, Дата: {q[3]}\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Нет новых вопросов в поддержке.")
        # Остаемся в админ-меню
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return
    if text == "✉️ Ответить":
        admin_states[user_id]["state"] = "answer_waiting"
        await update.message.reply_text("Введите ID вопроса и ответ в формате 'ID:ответ':")
        return
    if text == "◀️ Выйти":
        # Выходим из админ-режима
        if user_id in admin_states:
            del admin_states[user_id]
        # Возвращаем стандартное меню
        keyboard = [
            ["🎵 Викторина", "📊 Статистика"],
            ["🎸 Ассортимент", "🛒 Корзина"],
            ["❓ Справка", "🛟 Поддержка"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Вы вышли из режима администратора.", reply_markup=reply_markup)
        return
    if admin_states[user_id].get("state") == "orders_status":
        status = text.lower()
        status_map = {"новые": "new", "в работе": "in_progress", "выполненные": "completed"}
        if status == "🔙 назад":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
        if status not in status_map:
            await update.message.reply_text("Выберите статус: новые, в работе, выполненные или нажмите 'Назад'.")
            return
        orders = get_orders_by_status(status_map[status])
        if not orders:
            await update.message.reply_text("Нет заказов с этим статусом.")
        else:
            msg = f"Заказы со статусом '{status}':\n"
            for order in orders:
                msg += f"Номер: {order[0]}, UserID: {order[1]}, Сумма: {order[4]}, Адрес: {order[2]}, Телефон: {order[3]}, Время: {order[5]}\n"
            await update.message.reply_text(msg)
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return
async def handle_answer_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states:
        return
    if admin_states[user_id].get("state") == "answer_waiting":
        try:
            text = update.message.text.strip()
            qid, answer = text.split(":", 1)
            qid = int(qid)
            answer_support_question(qid, answer)
            await update.message.reply_text(f"Ответ на вопрос {qid} отправлен.")
        except Exception:
            await update.message.reply_text("Ошибка формата. Используйте id:ответ.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
    else:
        await update.message.reply_text("Неизвестная команда админа.")

async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states:
        return
    if admin_states[user_id].get("state") == "block_waiting_user_id":
        try:
            block_id = int(update.message.text.strip())
            block_user(block_id)
            await update.message.reply_text(f"Пользователь {block_id} заблокирован.")
        except Exception:
            await update.message.reply_text("Ошибка блокировки. Проверьте ID.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)

async def handle_unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states:
        return
    if admin_states[user_id].get("state") == "unblock_waiting_user_id":
        try:
            unblock_id = int(update.message.text.strip())
            unblock_user(unblock_id)
            await update.message.reply_text(f"Пользователь {unblock_id} разблокирован.")
        except Exception:
            await update.message.reply_text("Ошибка разблокировки. Проверьте ID.")
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)


# Функции для оформления заказа
async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart_items, total = get_cart(user_id)
    
    if not cart_items:
        await update.message.reply_text("🛒 Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return
    
    user_states[user_id] = {'state': 'checkout_waiting_address'}
    await update.message.reply_text(
        "📦 Оформление заказа\n\n"
        "Пожалуйста, введите адрес доставки:",
        reply_markup=ReplyKeyboardRemove()
    )

async def handle_address_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_states or user_states[user_id].get('state') != 'checkout_waiting_address':
        return
    
    address = update.message.text
    user_states[user_id] = {
        'state': 'checkout_waiting_phone',
        'address': address
    }
    
    # Создаем клавиатуру с кнопкой для отправки номера телефона
    keyboard = [[KeyboardButton("📱 Отправить мой номер", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📞 Теперь введите ваш номер телефона для связи:\n"
        "Вы можете ввести номер вручную или использовать кнопку ниже",
        reply_markup=reply_markup
    )

async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_states or user_states[user_id].get('state') != 'checkout_waiting_phone':
        return
    
    # Получаем номер телефона из сообщения или контакта
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    
    address = user_states[user_id]['address']
    cart_items, total = get_cart(user_id)
    
    # Создаем заказ
    order_number = create_order(user_id, address, phone, total, cart_items)
    
    # Отправляем подтверждение
    await update.message.reply_text(
        f"✅ Заказ {order_number} оформлен!\n\n"
        f"📦 Сумма заказа: {total}₽\n"
        f"🏠 Адрес доставки: {address}\n"
        f"📞 Телефон: {phone}\n\n"
        "Администратор скоро свяжется с вами для подтверждения заказа!",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Возвращаем главное меню
    keyboard = [
        ["🎵 Викторина", "📊 Статистика"],
        ["🎸 Ассортимент", "🛒 Корзина"],
        ["❓ Справка", "🛟 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)
    
    del user_states[user_id]




async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    song, artist = random.choice(list(MUSIC_QUIZ_DATA.items()))
    user_states[user_id] = {'state': 'quiz_waiting_answer', 'correct_artist': artist}
    await update.message.reply_text(f"🎵 Угадайте исполнителя песни: '{song}'")

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answer = update.message.text.strip()
    
    if user_id not in user_states or user_states[user_id].get('state') != 'quiz_waiting_answer':
        return
    
    correct_artist = user_states[user_id]['correct_artist']
    is_correct = user_answer.lower() == correct_artist.lower()
    update_quiz_stats(user_id, is_correct)

    if is_correct:
        await update.message.reply_text("✅ Верно!")
    else:
        await update.message.reply_text(f"❌ Неверно. Правильный ответ: {correct_artist}")

    del user_states[user_id]

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    correct, total = get_quiz_stats(user_id)
    await update.message.reply_text(f"📊 Ваша статистика:\nПравильных ответов: {correct}\nВсего попыток: {total}")

async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {'state': 'support_waiting_question'}
    await update.message.reply_text("Напишите ваш вопрос, и администратор ответит вам в ближайшее время.")

async def handle_support_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_states or user_states[user_id].get('state') != 'support_waiting_question':
        return
    
    question = update.message.text
    add_support_question(user_id, question)
    await update.message.reply_text("Ваш вопрос отправлен в поддержку. Мы ответим вам в ближайшее время.")
    del user_states[user_id]

async def start_reference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {'state': 'reference_waiting_band'}
    await update.message.reply_text("Введите название группы, и я покажу страну, откуда она родом.")

async def handle_reference_band(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_states or user_states[user_id].get('state') != 'reference_waiting_band':
        return
    
    band_name = update.message.text
    country = get_band_country(band_name)
    
    if country:
        await update.message.reply_text(f"Группа {band_name} родом из {country}.")
    else:
        await update.message.reply_text("К сожалению, я не знаю эту группу. Попробуйте другую.")
    
    del user_states[user_id]

async def show_assortment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    keyboard = []
    
    for category_id, category_name in categories:
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎸 Выберите категорию товаров:", reply_markup=reply_markup)

async def show_category_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split('_')[1])
    products = get_products_by_category(category_id)
    
    if not products:
        await query.edit_message_text("В этой категории пока нет товаров.")
        return
    
    keyboard = []
    for product_id, product_name, price, description in products:
        keyboard.append([InlineKeyboardButton(f"{product_name} - {price}₽", callback_data=f'product_{product_id}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад к категориям", callback_data='back_to_categories')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📦 Выберите товар:", reply_markup=reply_markup)

async def show_product_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[1])
    product = get_product(product_id)
    
    if not product:
        await query.edit_message_text("Товар не найден.")
        return
    
    product_id, product_name, price, description, category_name = product
    
    message_text = f"""
🎵 {product_name}
💵 Цена: {price}₽
📝 Описание: {description}
🏷️ Категория: {category_name}
    """
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f'add_to_cart_{product_id}')],
        [InlineKeyboardButton("⬅️ Назад к товарам", callback_data=f'category_{next((cat[0] for cat in get_categories() if cat[1] == category_name), 1)}')],
        [InlineKeyboardButton("🏠 В главное меню", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup)

async def add_product_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
   query = update.callback_query
   await query.answer()
   
   product_id = int(query.data.split('_')[3])
   user_id = query.from_user.id
   
   add_to_cart(user_id, product_id)
   await query.edit_message_text("✅ Товар добавлен в корзину!")


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart_items, total = get_cart(user_id)
    
    if not cart_items:
        await update.message.reply_text("🛒 Ваша корзина пуста.")
        return
    
    message_text = "🛒 Ваша корзина:\n\n"
    keyboard = []
    
    for item_id, product_name, price, quantity, product_id in cart_items:
        message_text += f"{product_name} - {price}₽ x {quantity} = {price * quantity}₽\n"
        
        row = [
            InlineKeyboardButton("➖", callback_data=f'decrease_{product_id}'),
            InlineKeyboardButton(f"{quantity}", callback_data=f'quantity_{product_id}'),
            InlineKeyboardButton("➕", callback_data=f'increase_{product_id}'),
            InlineKeyboardButton("❌", callback_data=f'remove_{product_id}')
        ]
        keyboard.append(row)
    
    message_text += f"\n💵 Общая сумма: {total}₽"
    
    # Добавляем кнопку оформления заказа, если корзина не пуста
    keyboard.append([InlineKeyboardButton("🚀 Оформить заказ", callback_data='checkout')])
    keyboard.append([InlineKeyboardButton("🧹 Очистить корзину", callback_data='clear_cart')])
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data='main_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)



# Добавляем обработчик для кнопки оформления заказа
async def handle_checkout_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start_checkout_from_button(query, context)

async def start_checkout_from_button(query, context):
    user_id = query.from_user.id
    cart_items, total = get_cart(user_id)
    
    if not cart_items:
        await query.edit_message_text("🛒 Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
        return
    
    user_states[user_id] = {'state': 'checkout_waiting_address'}
    await context.bot.send_message(
        chat_id=user_id,
        text="📦 Оформление заказа\n\nПожалуйста, введите адрес доставки:",
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_cart_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action, product_id = query.data.split('_')
    product_id = int(product_id)
    
    cart_items, _ = get_cart(user_id)
    current_quantity = next((item[3] for item in cart_items if item[4] == product_id), 0)

    if action == 'increase':
        update_cart_item(user_id, product_id, current_quantity + 1)
    elif action == 'decrease':
        update_cart_item(user_id, product_id, current_quantity - 1)
    elif action == 'remove':
        remove_from_cart(user_id, product_id)

    # Обновляем сообщение корзины
    cart_items, total = get_cart(user_id)

    if not cart_items:
        await query.edit_message_text("🛒 Ваша корзина пуста.")
        return

    message_text = "🛒 Ваша корзина:\n\n"
    keyboard = []

    for item_id, product_name, price, quantity, product_id in cart_items:
        message_text += f"{product_name} - {price}₽ x {quantity} = {price * quantity}₽\n"
        row = [
            InlineKeyboardButton("➖", callback_data=f'decrease_{product_id}'),
            InlineKeyboardButton(f"{quantity}", callback_data=f'quantity_{product_id}'),
            InlineKeyboardButton("➕", callback_data=f'increase_{product_id}'),
            InlineKeyboardButton("❌", callback_data=f'remove_{product_id}')
        ]
        keyboard.append(row)

    message_text += f"\n💵 Общая сумма: {total}₽"

    # Кнопка оформления заказа всегда добавляется, если корзина не пуста
    keyboard.append([InlineKeyboardButton("🚀 Оформить заказ", callback_data='checkout')])
    keyboard.append([InlineKeyboardButton("🧹 Очистить корзину", callback_data='clear_cart')])
    keyboard.append([InlineKeyboardButton("🏠 В главное меню", callback_data='main_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup)

async def clear_user_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    clear_cart(user_id)
    await query.edit_message_text("🧹 Корзина очищена!")

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    welcome_text = f"Добро пожаловать назад, {user.first_name}! 🎵"
    
    keyboard = [
        ["🎵 Викторина", "📊 Статистика"],
        ["🎸 Ассортимент", "🛒 Корзина"],
        ["❓ Справка", "🛟 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await query.edit_message_text(welcome_text)
    await context.bot.send_message(chat_id=user.id, text="Выберите опцию:", reply_markup=reply_markup)

async def back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    categories = get_categories()
    keyboard = []
    
    for category_id, category_name in categories:
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🎸 Выберите категорию товаров:", reply_markup=reply_markup)

async def show_edit_product_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать категории товаров для редактирования"""
    from database import get_categories
    user_id = update.effective_user.id
    
    # Устанавливаем состояние администратора
    admin_states[user_id] = {"state": "edit_product_category_selection"}
    
    categories = get_categories()
    keyboard = []
    
    for category_id, category_name in categories:
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'edit_category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎸 Выберите категорию товара для редактирования:", reply_markup=reply_markup)


async def show_edit_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список товаров в выбранной категории для редактирования"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    category_id = int(query.data.split('_')[2])
    
    # Устанавливаем состояние администратора
    admin_states[user_id] = {"state": "edit_product_selection", "edit_category_id": category_id}
    
    from database import get_products_by_category, get_categories
    products = get_products_by_category(category_id)
    
    if not products:
        await query.edit_message_text("В этой категории пока нет товаров для редактирования.")
        return
    
    keyboard = []
    for product_id, product_name, price, description in products:
        keyboard.append([InlineKeyboardButton(f"{product_name} - {price}₽", callback_data=f'edit_product_{product_id}')])
    
    # Добавляем кнопку "Назад к категориям"
    keyboard.append([InlineKeyboardButton("⬅️ Назад к категориям", callback_data='edit_categories')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    category_name = next((cat[1] for cat in get_categories() if cat[0] == category_id), "Неизвестная категория")
    await query.edit_message_text(f"📦 Товары в категории '{category_name}' (для редактирования):", reply_markup=reply_markup)


async def show_edit_product_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать форму редактирования товара"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    product_id = int(query.data.split('_')[2])
    
    from database import get_product
    product = get_product(product_id)
    
    if not product:
        await query.edit_message_text("Товар не найден.")
        return
    
    product_id, product_name, price, description, category_name = product
    
    # Устанавливаем состояние администратора
    admin_states[user_id] = {"state": "edit_product_form", "edit_product_id": product_id}
    
    message_text = f"""
🎵 Редактирование товара:
📝 Название: {product_name}
💵 Цена: {price}₽
📋 Описание: {description}
🏷️ Категория: {category_name}
    """
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать название", callback_data=f'edit_field_name_{product_id}')],
        [InlineKeyboardButton("✏️ Редактировать цену", callback_data=f'edit_field_price_{product_id}')],
        [InlineKeyboardButton("✏️ Редактировать описание", callback_data=f'edit_field_description_{product_id}')],
        [InlineKeyboardButton("⬅️ Назад к товарам", callback_data=f'edit_category_{next((cat[0] for cat in get_categories() if cat[1] == category_name), 1)}')],
        [InlineKeyboardButton("🏠 В админ-меню", callback_data='admin_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup)


async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать редактирование конкретного поля товара"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data_parts = query.data.split('_')
    field = data_parts[2]  # name, price, or description
    product_id = int(data_parts[3])
    
    # Устанавливаем состояние администратора
    admin_states[user_id] = {"state": "editing_field", "edit_product_id": product_id, "edit_field": field}
    
    field_names = {
        "name": "название",
        "price": "цену",
        "description": "описание"
    }
    
    await query.edit_message_text(f"Введите новое {field_names[field]} для товара:")


async def finish_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить редактирование поля товара"""
    user_id = update.effective_user.id
    
    # Проверяем, находится ли пользователь в состоянии редактирования
    if user_id not in admin_states or admin_states[user_id].get("state") != "editing_field":
        return
    
    # Получаем информацию о товаре и поле для редактирования
    product_id = admin_states[user_id]["edit_product_id"]
    field = admin_states[user_id]["edit_field"]
    new_value = update.message.text.strip()
    
    # Обновляем товар в базе данных
    from database import get_product, update_product
    
    product = get_product(product_id)
    if not product:
        await update.message.reply_text("Товар не найден.")
        return
    
    # Определяем имя категории для сохранения
    product_id_db, product_name_db, price_db, description_db, category_name_db = product
    
    # Получаем ID категории
    from database import get_categories
    categories = get_categories()
    category_id = next((cat[0] for cat in categories if cat[1] == category_name_db), None)
    
    if not category_id:
        await update.message.reply_text("Ошибка: категория не найдена.")
        return
    
    # Формируем имя товара для обновления
    update_product_name = product_name_db
    if field == "name":
        update_product_name = new_value
    elif field == "price":
        try:
            new_value = float(new_value)
        except ValueError:
            await update.message.reply_text("Ошибка: цена должна быть числом.")
            return
    elif field == "description":
        pass  # new_value уже содержит правильное значение
    
    # Обновляем товар
    update_product(update_product_name, category_id, field, new_value)
    
    await update.message.reply_text(f"✅ Поле '{field}' успешно обновлено!")
    
    # Возвращаемся к форме редактирования товара
    admin_states[user_id]["state"] = "edit_product_form"
    
    # Для корректного вызова show_edit_product_form с обычным сообщением,
    # нам нужно использовать контекст бота для отправки нового сообщения
    from database import get_categories
    categories = get_categories()
    category_name = next((cat[1] for cat in categories if cat[0] == category_id), "Неизвестная категория")
    
    # Отправляем новое сообщение с формой редактирования
    message_text = f"""
🎵 Редактирование товара:
📝 Название: {update_product_name if field == 'name' else product_name_db}
💵 Цена: {new_value if field == 'price' else price_db}₽
📋 Описание: {new_value if field == 'description' else description_db}
🏷️ Категория: {category_name}
    """
    
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать название", callback_data=f'edit_field_name_{product_id}')],
        [InlineKeyboardButton("✏️ Редактировать цену", callback_data=f'edit_field_price_{product_id}')],
        [InlineKeyboardButton("✏️ Редактировать описание", callback_data=f'edit_field_description_{product_id}')],
        [InlineKeyboardButton("⬅️ Назад к товарам", callback_data=f'edit_category_{category_id}')],
        [InlineKeyboardButton("🏠 В админ-меню", callback_data='admin_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message_text, reply_markup=reply_markup)
