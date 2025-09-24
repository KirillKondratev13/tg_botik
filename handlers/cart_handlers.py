from telegram import Update, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_cart, create_order, add_to_cart,
    update_cart_item, remove_from_cart, clear_cart
)
from .states import user_states

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