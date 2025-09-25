import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    is_admin, check_admin_password, get_all_users, block_user, unblock_user,
    get_support_questions, answer_support_question,
    update_product, add_product, delete_product, get_orders_by_status, update_order_status,
    get_categories, get_products_by_category, get_product, remove_from_cart_by_product
)
from .states import admin_states

# Настройка логирования для административных действий
admin_logger = logging.getLogger('admin_actions')
admin_logger.setLevel(logging.INFO)

# Константы для сообщений
MESSAGES = {
    'success_product_updated': '✅ Товар успешно обновлен!',
    'success_product_added': '✅ Товар успешно добавлен!',
    'success_product_deleted': '✅ Товар успешно удален!',
    'error_category_not_found': '❌ Ошибка: категория не найдена.',
    'error_product_not_found': '❌ Ошибка: товар не найден.',
    'error_invalid_price': '❌ Ошибка: цена должна быть положительным числом.',
    'error_empty_field': '❌ Ошибка: поле не может быть пустым.',
    'error_invalid_format': '❌ Ошибка формата ввода.',
    'confirm_deletion': '⚠️ Внимание! Это действие нельзя отменить.\n\n'
                       'Товар будет удален из базы данных и из корзин всех пользователей.\n'
                       'Для подтверждения введите: УДАЛИТЬ ТОВАР'
}

def log_admin_action(user_id, action, details=""):
    """Логирование административных действий"""
    admin_logger.info(f"Admin {user_id}: {action} - {details}")

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["👥 Пользователи", "🚫 Заблокировать", "✅ Разблокировать"],
        ["🆘 Поддержка", "✉️ Ответить"],
        ["✏️ Редактировать товар", "➕ Добавить товар"],
        ["🗑️ Удалить товар", "📦 Заказы"],
        ["◀️ Выйти"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🔧 Панель администратора. Выберите действие:", reply_markup=reply_markup)

async def show_categories_for_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, action_type: str):
    """Показать категории для выбора с указанием типа действия"""
    categories = get_categories()
    if not categories:
        await update.message.reply_text("❌ В системе нет категорий товаров.")
        return False
    
    keyboard = [[cat[1]] for cat in categories] + [["🔙 Назад в админ-меню"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    action_messages = {
        "edit": "📝 Выберите категорию товара для редактирования:",
        "delete": "🗑️ Выберите категорию товара для удаления:",
        "add": "➕ Выберите категорию для добавления нового товара:"
    }
    
    await update.message.reply_text(action_messages.get(action_type, "Выберите категорию:"), reply_markup=reply_markup)
    return True

async def show_products_for_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, category_name: str, action_type: str):
    """Показать товары категории для выбора"""
    categories = get_categories()
    category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
    
    if not category_id:
        await update.message.reply_text(MESSAGES['error_category_not_found'])
        return False
    
    products = get_products_by_category(category_id)
    if not products:
        await update.message.reply_text(f"❌ В категории '{category_name}' нет товаров.")
        return False
    
    keyboard = []
    for product_id, product_name, price, description in products:
        keyboard.append([f"{product_name} - {price}₽"])
    keyboard.append(["🔙 Назад к категориям"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    action_messages = {
        "edit": f"📝 Выберите товар из категории '{category_name}' для редактирования:",
        "delete": f"🗑️ Выберите товар из категории '{category_name}' для удаления:"
    }
    
    await update.message.reply_text(action_messages.get(action_type, f"Товары в категории '{category_name}':"), reply_markup=reply_markup)
    return True

def validate_price(price_str: str) -> tuple[bool, float]:
    """Валидация цены"""
    try:
        price = float(price_str.replace(',', '.'))
        if price <= 0:
            return False, 0.0
        return True, price
    except ValueError:
        return False, 0.0

def validate_text_field(text: str, min_length: int = 1, max_length: int = 255) -> bool:
    """Валидация текстовых полей"""
    return min_length <= len(text.strip()) <= max_length

async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in admin_states:
        return

    # Логирование для отладки
    admin_logger.info(f"Admin {user_id}: state={admin_states[user_id].get('state')}, text='{text}'")

    # === РЕДАКТИРОВАНИЕ ТОВАРА ===
    if admin_states[user_id].get("state") == "edit_product_category":
        if text == "🔙 Назад в админ-меню":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
            
        # Проверяем существование категории
        categories = get_categories()
        category_exists = any(cat[1] == text for cat in categories)
        if not category_exists:
            await update.message.reply_text("❌ Такой категории не существует. Выберите категорию из предложенных.")
            return
            
        admin_states[user_id]["edit_category"] = text
        admin_states[user_id]["state"] = "edit_product_select"
        
        if not await show_products_for_selection(update, context, text, "edit"):
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
        return

    if admin_states[user_id].get("state") == "edit_product_select":
        if text == "🔙 Назад к категориям":
            admin_states[user_id]["state"] = "edit_product_category"
            await show_categories_for_selection(update, context, "edit")
            return
            
        category_name = admin_states[user_id]["edit_category"]
        
        # Извлекаем название товара из строки "Название - Цена₽"
        product_name = text.split(" - ")[0] if " - " in text else text
        
        # Проверяем существование товара
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        products = get_products_by_category(category_id) if category_id else []
        product_exists = any(prod[1] == product_name for prod in products)
        
        if not product_exists:
            await update.message.reply_text("❌ Такого товара не существует. Выберите товар из списка.")
            return
            
        admin_states[user_id]["edit_product"] = product_name
        admin_states[user_id]["state"] = "edit_product_field"
        
        keyboard = [["💰 Цена"], ["📝 Название"], ["📋 Описание"], ["🔙 Назад к товарам"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(f"📝 Редактирование товара: {product_name}\n\nВыберите параметр для изменения:", reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "edit_product_field":
        if text == "🔙 Назад к товарам":
            category_name = admin_states[user_id]["edit_category"]
            admin_states[user_id]["state"] = "edit_product_select"
            await show_products_for_selection(update, context, category_name, "edit")
            return
            
        field_mapping = {
            "💰 Цена": "price",
            "📝 Название": "name", 
            "📋 Описание": "description"
        }
        
        if text not in field_mapping:
            await update.message.reply_text("❌ Выберите параметр из предложенных вариантов.")
            return
            
        admin_states[user_id]["edit_field"] = field_mapping[text]
        admin_states[user_id]["state"] = "edit_product_value"
        
        field_prompts = {
            "price": "💰 Введите новую цену товара (только число):",
            "name": "📝 Введите новое название товара:",
            "description": "📋 Введите новое описание товара:"
        }
        
        field_name = field_mapping[text]
        keyboard = [["🔙 Отмена"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(field_prompts[field_name], reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "edit_product_value":
        if text == "🔙 Отмена":
            admin_states[user_id]["state"] = "edit_product_field"
            product_name = admin_states[user_id]["edit_product"]
            keyboard = [["💰 Цена"], ["📝 Название"], ["📋 Описание"], ["🔙 Назад к товарам"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(f"📝 Редактирование товара: {product_name}\n\nВыберите параметр для изменения:", reply_markup=reply_markup)
            return

        category_name = admin_states[user_id]["edit_category"]
        product_name = admin_states[user_id]["edit_product"]
        field = admin_states[user_id]["edit_field"]
        new_value = text.strip()

        # Валидация
        if field == "price":
            is_valid, validated_value = validate_price(new_value)
            if not is_valid:
                await update.message.reply_text(MESSAGES['error_invalid_price'])
                return
            new_value = validated_value
        elif field in ["name", "description"]:
            if not validate_text_field(new_value):
                await update.message.reply_text(MESSAGES['error_empty_field'])
                return

        # Обновление в базе данных
        try:
            categories = get_categories()
            category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
            
            if category_id:
                update_product(product_name, category_id, field, new_value)
                await update.message.reply_text(MESSAGES['success_product_updated'])
                log_admin_action(user_id, "PRODUCT_UPDATED", f"Product: {product_name}, Field: {field}, Value: {new_value}")
            else:
                await update.message.reply_text(MESSAGES['error_category_not_found'])
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при обновлении товара: {str(e)}")
            log_admin_action(user_id, "PRODUCT_UPDATE_ERROR", f"Product: {product_name}, Error: {str(e)}")

        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # === ДОБАВЛЕНИЕ ТОВАРА ===
    if admin_states[user_id].get("state") == "add_product_category":
        if text == "🔙 Назад в админ-меню":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
            
        categories = get_categories()
        category_exists = any(cat[1] == text for cat in categories)
        if not category_exists:
            await update.message.reply_text("❌ Такой категории не существует. Выберите категорию из предложенных.")
            return
            
        admin_states[user_id]["add_category"] = text
        admin_states[user_id]["state"] = "add_product_name"
        
        keyboard = [["🔙 Назад к категориям"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(f"➕ Добавление товара в категорию '{text}'\n\n📝 Введите название товара:", reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "add_product_name":
        if text == "🔙 Назад к категориям":
            admin_states[user_id]["state"] = "add_product_category"
            await show_categories_for_selection(update, context, "add")
            return
            
        if not validate_text_field(text):
            await update.message.reply_text(MESSAGES['error_empty_field'])
            return
            
        admin_states[user_id]["add_product_name"] = text.strip()
        admin_states[user_id]["state"] = "add_product_price"
        
        keyboard = [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("💰 Введите цену товара:", reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "add_product_price":
        if text == "🔙 Назад":
            admin_states[user_id]["state"] = "add_product_name"
            keyboard = [["🔙 Назад к категориям"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("📝 Введите название товара:", reply_markup=reply_markup)
            return
            
        is_valid, price = validate_price(text)
        if not is_valid:
            await update.message.reply_text(MESSAGES['error_invalid_price'])
            return
            
        admin_states[user_id]["add_product_price"] = price
        admin_states[user_id]["state"] = "add_product_description"
        
        keyboard = [["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("📋 Введите описание товара:", reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "add_product_description":
        if text == "🔙 Назад":
            admin_states[user_id]["state"] = "add_product_price"
            keyboard = [["🔙 Назад"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("💰 Введите цену товара:", reply_markup=reply_markup)
            return
            
        if not validate_text_field(text):
            await update.message.reply_text(MESSAGES['error_empty_field'])
            return

        # Добавление товара в базу данных
        try:
            category_name = admin_states[user_id]["add_category"]
            product_name = admin_states[user_id]["add_product_name"]
            product_price = admin_states[user_id]["add_product_price"]
            product_description = text.strip()
            
            categories = get_categories()
            category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
            
            if category_id:
                add_product(product_name, category_id, product_price, product_description)
                await update.message.reply_text(f"✅ Товар '{product_name}' успешно добавлен в категорию '{category_name}'!")
                log_admin_action(user_id, "PRODUCT_ADDED", f"Name: {product_name}, Category: {category_name}, Price: {product_price}")
            else:
                await update.message.reply_text(MESSAGES['error_category_not_found'])
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при добавлении товара: {str(e)}")
            log_admin_action(user_id, "PRODUCT_ADD_ERROR", f"Error: {str(e)}")

        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # === УДАЛЕНИЕ ТОВАРА ===
    if admin_states[user_id].get("state") == "delete_product_category":
        if text == "🔙 Назад в админ-меню":
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
            return
            
        categories = get_categories()
        category_exists = any(cat[1] == text for cat in categories)
        if not category_exists:
            await update.message.reply_text("❌ Такой категории не существует. Выберите категорию из предложенных.")
            return
            
        admin_states[user_id]["delete_category"] = text
        admin_states[user_id]["state"] = "delete_product_select"
        
        if not await show_products_for_selection(update, context, text, "delete"):
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
        return

    if admin_states[user_id].get("state") == "delete_product_select":
        if text == "🔙 Назад к категориям":
            admin_states[user_id]["state"] = "delete_product_category"
            await show_categories_for_selection(update, context, "delete")
            return
            
        category_name = admin_states[user_id]["delete_category"]
        product_name = text.split(" - ")[0] if " - " in text else text
        
        # Проверяем существование товара
        categories = get_categories()
        category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
        products = get_products_by_category(category_id) if category_id else []
        product_exists = any(prod[1] == product_name for prod in products)
        
        if not product_exists:
            await update.message.reply_text("❌ Такого товара не существует. Выберите товар из списка.")
            return
            
        admin_states[user_id]["delete_product"] = product_name
        admin_states[user_id]["state"] = "delete_product_confirm"
        
        keyboard = [["🔙 Отмена удаления"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(f"⚠️ Подтверждение удаления товара\n\nТовар: {product_name}\nКатегория: {category_name}\n\n{MESSAGES['confirm_deletion']}", reply_markup=reply_markup)
        return

    if admin_states[user_id].get("state") == "delete_product_confirm":
        if text == "🔙 Отмена удаления":
            category_name = admin_states[user_id]["delete_category"]
            admin_states[user_id]["state"] = "delete_product_select"
            await show_products_for_selection(update, context, category_name, "delete")
            return
            
        if text != "УДАЛИТЬ ТОВАР":
            await update.message.reply_text("❌ Для подтверждения удаления введите точно: УДАЛИТЬ ТОВАР")
            return

        # Удаление товара
        try:
            category_name = admin_states[user_id]["delete_category"]
            product_name = admin_states[user_id]["delete_product"]
            
            categories = get_categories()
            category_id = next((cat[0] for cat in categories if cat[1] == category_name), None)
            
            if category_id:
                # Каскадное удаление: сначала из корзин пользователей
                remove_from_cart_by_product(product_name, category_id)
                
                # Затем из базы данных товаров
                delete_product(product_name, category_id)
                
                await update.message.reply_text(f"✅ Товар '{product_name}' успешно удален!\n\n• Товар удален из базы данных\n• Товар удален из корзин всех пользователей")
                log_admin_action(user_id, "PRODUCT_DELETED", f"Product: {product_name}, Category: {category_name}")
            else:
                await update.message.reply_text(MESSAGES['error_category_not_found'])
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при удалении товара: {str(e)}")
            log_admin_action(user_id, "PRODUCT_DELETE_ERROR", f"Product: {product_name}, Error: {str(e)}")

        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # === ЗАКАЗЫ ===
    if admin_states[user_id].get("state") == "orders_status":
        status = text.strip().lower()
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
            await update.message.reply_text("📦 Нет заказов с этим статусом.")
        else:
            msg = f"📦 Заказы со статусом '{status}':\n\n"
            for order in orders:
                msg += f"🔹 Номер: {order[0]}\n   UserID: {order[1]}\n   Сумма: {order[4]}₽\n   Адрес: {order[2]}\n   Телефон: {order[3]}\n   Время: {order[5]}\n\n"
            await update.message.reply_text(msg)
            
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    # === ОСНОВНЫЕ КОМАНДЫ ===
    if text == "✏️ Редактировать товар":
        admin_states[user_id]["state"] = "edit_product_category"
        if not await show_categories_for_selection(update, context, "edit"):
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
        return

    if text == "➕ Добавить товар":
        admin_states[user_id]["state"] = "add_product_category"
        if not await show_categories_for_selection(update, context, "add"):
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
        return

    if text == "🗑️ Удалить товар":
        admin_states[user_id]["state"] = "delete_product_category"
        if not await show_categories_for_selection(update, context, "delete"):
            admin_states[user_id]["state"] = "admin_menu"
            await show_admin_menu(update, context)
        return

    if text == "📦 Заказы":
        admin_states[user_id]["state"] = "orders_status"
        keyboard = [["новые"], ["в работе"], ["выполненные"], ["🔙 Назад"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("📦 Выберите статус заказов:", reply_markup=reply_markup)
        return

    if text == "👥 Пользователи":
        users = get_all_users()
        if users:
            msg = "👥 Список пользователей:\n\n"
            for user in users:
                user_id_db, username, first_name, last_name, is_blocked = user
                status = "🔴 Заблокирован" if is_blocked else "🟢 Активен"
                msg += f"🔹 ID: {user_id_db}\n   Имя: {first_name} {last_name or ''}\n   Логин: @{username or 'не указан'}\n   Статус: {status}\n\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("👥 Пока нет зарегистрированных пользователей.")
            
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    if text == "🚫 Заблокировать":
        admin_states[user_id]["state"] = "block_waiting_user_id"
        await update.message.reply_text("🚫 Введите ID пользователя для блокировки:")
        return

    if text == "✅ Разблокировать":
        admin_states[user_id]["state"] = "unblock_waiting_user_id"
        await update.message.reply_text("✅ Введите ID пользователя для разблокировки:")
        return

    if text == "🆘 Поддержка":
        questions = get_support_questions()
        if questions:
            msg = "🆘 Новые вопросы в поддержке:\n\n"
            for q in questions:
                msg += f"🔹 ID: {q[0]}\n   UserID: {q[1]}\n   Вопрос: {q[2]}\n   Дата: {q[3]}\n\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("🆘 Нет новых вопросов в поддержке.")
            
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)
        return

    if text == "✉️ Ответить":
        admin_states[user_id]["state"] = "answer_waiting"
        await update.message.reply_text("✉️ Введите ID вопроса и ответ в формате 'ID:ответ':")
        return

    if text == "◀️ Выйти":
        if user_id in admin_states:
            del admin_states[user_id]
        keyboard = [
            ["🎵 Викторина", "📊 Статистика"],
            ["🎸 Ассортимент", "🛒 Корзина"],
            ["❓ Справка", "🛟 Поддержка"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Вы вышли из режима администратора.", reply_markup=reply_markup)
        log_admin_action(user_id, "ADMIN_LOGOUT")
        return

async def handle_answer_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states:
        return
        
    if admin_states[user_id].get("state") == "answer_waiting":
        try:
            text = update.message.text.strip()
            if ":" not in text:
                await update.message.reply_text("❌ Ошибка формата. Используйте формат: ID:ответ")
                return
                
            qid, answer = text.split(":", 1)
            qid = int(qid)
            answer_support_question(qid, answer.strip())
            await update.message.reply_text(f"✅ Ответ на вопрос {qid} отправлен.")
            log_admin_action(user_id, "SUPPORT_ANSWERED", f"Question ID: {qid}")
        except ValueError:
            await update.message.reply_text("❌ ID вопроса должен быть числом.")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
            
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)

async def handle_block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states:
        return
        
    if admin_states[user_id].get("state") == "block_waiting_user_id":
        try:
            block_id = int(update.message.text.strip())
            block_user(block_id)
            await update.message.reply_text(f"🚫 Пользователь {block_id} заблокирован.")
            log_admin_action(user_id, "USER_BLOCKED", f"Blocked user: {block_id}")
        except ValueError:
            await update.message.reply_text("❌ ID должен быть числом.")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка блокировки: {str(e)}")
            
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
            await update.message.reply_text(f"✅ Пользователь {unblock_id} разблокирован.")
            log_admin_action(user_id, "USER_UNBLOCKED", f"Unblocked user: {unblock_id}")
        except ValueError:
            await update.message.reply_text("❌ ID должен быть числом.")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка разблокировки: {str(e)}")
            
        admin_states[user_id]["state"] = "admin_menu"
        await show_admin_menu(update, context)