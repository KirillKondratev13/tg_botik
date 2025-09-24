from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_categories, get_products_by_category, get_product, add_to_cart,
    get_cart, update_cart_item, remove_from_cart, clear_cart,
    create_order, get_user_orders, generate_order_number,
    get_band_country
)
from .states import admin_states

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
    # admin_states уже импортирован из .states
    admin_states[user_id] = {"state": "edit_product_category_selection"}
    
    categories = get_categories()
    keyboard = []
    
    for category_id, category_name in categories:
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'edit_category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎸 Выберите категорию товара для редактирования:", reply_markup=reply_markup)

async def show_edit_product_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список товаров в выбранной категории для редактирования"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли это callback_query или обычным сообщением
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        category_id = int(query.data.split('_')[2])
        
        # Устанавливаем состояние администратора
        # admin_states уже импортирован из .states
        admin_states[user_id] = {"state": "edit_product_selection", "edit_category_id": category_id}
    else:
        # Если это обычное сообщение, предполагаем, что категория уже сохранена в состоянии
        # admin_states уже импортирован из .states
        if user_id in admin_states and "edit_category_id" in admin_states[user_id]:
            category_id = admin_states[user_id]["edit_category_id"]
        else:
            await update.message.reply_text("Ошибка: категория не найдена.")
            return
    
    from database import get_products_by_category, get_categories
    products = get_products_by_category(category_id)
    
    if not products:
        if update.callback_query:
            await query.edit_message_text("В этой категории пока нет товаров для редактирования.")
        else:
            await update.message.reply_text("В этой категории пока нет товаров для редактирования.")
        return
    
    keyboard = []
    for product_id, product_name, price, description in products:
        keyboard.append([InlineKeyboardButton(f"{product_name} - {price}₽", callback_data=f'edit_product_{product_id}')])
    
    # Добавляем кнопку "Назад к категориям"
    keyboard.append([InlineKeyboardButton("⬅️ Назад к категориям", callback_data='edit_categories')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    category_name = next((cat[1] for cat in get_categories() if cat[0] == category_id), "Неизвестная категория")
    
    message_text = f"📦 Товары в категории '{category_name}' (для редактирования):"
    
    if update.callback_query:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def show_edit_product_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать форму редактирования товара"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли это callback_query или обычным сообщением
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        product_id = int(query.data.split('_')[2])
    else:
        # Если это обычное сообщение, получаем product_id из состояния администратора
        from .states import admin_states
        if user_id in admin_states and "edit_product_id" in admin_states[user_id]:
            product_id = admin_states[user_id]["edit_product_id"]
        else:
            await update.message.reply_text("Ошибка: ID товара не найден.")
            return
    
    from database import get_product
    product = get_product(product_id)
    
    if not product:
        if update.callback_query:
            await query.edit_message_text("Товар не найден.")
        else:
            await update.message.reply_text("Товар не найден.")
        return
    
    product_id, product_name, price, description, category_name = product
    
    # Устанавливаем состояние администратора
    # admin_states уже импортирован из .states
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
    
    if update.callback_query:
        await query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)

async def start_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать редактирование конкретного поля товара"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data_parts = query.data.split('_')
    field = data_parts[2]  # name, price, or description
    product_id = int(data_parts[3])
    
    # Устанавливаем состояние администратора
    # admin_states уже импортирован из .states
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
        pass # new_value уже содержит правильное значение
    
    # Обновляем товар
    update_product(update_product_name, category_id, field, new_value)
    
    await update.message.reply_text(f"✅ Поле '{field}' успешно обновлено!")
    
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

# show_admin_menu удалена - функция уже определена в admin_handlers.py