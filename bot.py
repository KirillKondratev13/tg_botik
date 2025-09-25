from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from database import init_db, is_user_blocked, is_admin
from handlers import (
    start_quiz, check_answer, show_stats,
    start_support, handle_support_question,
    start_reference, handle_reference_band,
    show_assortment, show_cart,
    show_category_products, show_product_details, add_product_to_cart,
    handle_cart_actions, clear_user_cart, back_to_main_menu, back_to_categories,
    start_checkout, handle_address_input, handle_phone_input, handle_checkout_button,
    admin_command, handle_admin_password, show_admin_menu, handle_answer_support, handle_block_user, handle_unblock_user, handle_admin_menu,
    show_edit_product_categories, show_edit_product_list, show_edit_product_form, start_edit_field, finish_edit_field,
    user_states, admin_states
)

# Инициализация базы данных
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Регистрируем пользователя, если его нет в таблице users
    from database import register_user
    register_user(user.id, user.username, user.first_name, user.last_name)
    welcome_text = (
        f"Привет, {user.first_name}! Я музыкальный бот. 🎵\n"
        "Выбери опцию из меню ниже:"
    )
    keyboard = [
        ["🎵 Викторина", "📊 Статистика"],
        ["🎸 Ассортимент", "🛒 Корзина"],
        ["❓ Справка", "🛟 Поддержка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text

    # Регистрируем пользователя, если его нет в таблице users
    from database import register_user
    register_user(user.id, user.username, user.first_name, user.last_name)

    # Проверяем блокировку пользователя (админы не блокируются)
    if is_user_blocked(user_id) and not is_admin(user_id):
        if text == "🛟 Поддержка" or (user_id in user_states and user_states[user_id].get('state') == 'support_waiting_question'):
            pass  # Разрешить поддержку
        else:
            await update.message.reply_text("Вы заблокированы. Доступ только к поддержке.")
            return

    # Проверяем состояния оформления заказа
    if user_id in user_states:
        state = user_states[user_id].get('state')
        if state == 'checkout_waiting_address':
            await handle_address_input(update, context)
            return
        elif state == 'checkout_waiting_phone':
            await handle_phone_input(update, context)
            return

    # Проверяем состояния администратора
    if user_id in admin_states:
        admin_state = admin_states[user_id].get('state')
        # Все состояния админ-панели обрабатываются одним обработчиком
        if admin_state in [
            'waiting_password', 'admin_menu', 'edit_product_category', 'edit_product_select', 'edit_product_field', 'edit_product_value',
            'add_product_category', 'add_product_name', 'add_product_price', 'add_product_description', 'delete_product_category', 'delete_product_select', 'delete_product_confirm',
            'orders_status', 'block_waiting_user_id', 'unblock_waiting_user_id', 'answer_waiting'
        ]:
            if admin_state == 'waiting_password':
                await handle_admin_password(update, context)
            elif admin_state in ['admin_menu', 'edit_product_category', 'edit_product_select', 'edit_product_field', 'edit_product_value',
                                 'add_product_category', 'add_product_name', 'add_product_price', 'add_product_description', 'delete_product_category', 'delete_product_select', 'delete_product_confirm',
                                 'orders_status']:
                print(f"DEBUG bot.py: Handling admin state '{admin_state}' for user {user_id} with text '{text}'")
                await handle_admin_menu(update, context)
            elif admin_state == 'block_waiting_user_id':
                await handle_block_user(update, context)
            elif admin_state == 'unblock_waiting_user_id':
                await handle_unblock_user(update, context)
            elif admin_state == 'answer_waiting':
                await handle_answer_support(update, context)
            return
        # Обработка состояния редактирования поля товара
        elif admin_state == 'editing_field':
            # finish_edit_field теперь импортируется в заголовке файла
            await finish_edit_field(update, context)
            return
    
    # Обработка основных команд
    if text == "🎵 Викторина":
        await start_quiz(update, context)
    elif text == "📊 Статистика":
        await show_stats(update, context)
    elif text == "❓ Справка":
        await start_reference(update, context)
    elif text == "🛟 Поддержка":
        await start_support(update, context)
    elif text == "🎸 Ассортимент":
        await show_assortment(update, context)
    elif text == "🛒 Корзина":
        await show_cart(update, context)
    else:
        if user_id in user_states:
            state = user_states[user_id].get('state')
            if state == 'quiz_waiting_answer':
                await check_answer(update, context)
            elif state == 'support_waiting_question':
                await handle_support_question(update, context)
            elif state == 'reference_waiting_band':
                await handle_reference_band(update, context)
        else:
            await update.message.reply_text("Не понимаю ваше сообщение. Выберите опцию из меню.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.CONTACT, handle_phone_input))

    # Обработчики callback-запросов (inline кнопки)
    application.add_handler(CallbackQueryHandler(show_category_products, pattern='^category_'))
    application.add_handler(CallbackQueryHandler(show_product_details, pattern='^product_'))
    application.add_handler(CallbackQueryHandler(add_product_to_cart, pattern='^add_to_cart_'))
    application.add_handler(CallbackQueryHandler(handle_cart_actions, pattern='^(increase|decrease|remove)_'))
    application.add_handler(CallbackQueryHandler(clear_user_cart, pattern='^clear_cart$'))
    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(back_to_categories, pattern='^back_to_categories$'))
    application.add_handler(CallbackQueryHandler(handle_checkout_button, pattern='^checkout$'))
    
    # Обработчики callback-запросов для редактирования товаров
    application.add_handler(CallbackQueryHandler(show_edit_product_categories, pattern='^edit_categories$'))
    application.add_handler(CallbackQueryHandler(show_edit_product_list, pattern='^edit_category_'))
    application.add_handler(CallbackQueryHandler(show_edit_product_form, pattern='^edit_product_'))
    application.add_handler(CallbackQueryHandler(start_edit_field, pattern='^edit_field_'))

    # Обработчик ошибок
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Произошла ошибка: {context.error}")

    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
