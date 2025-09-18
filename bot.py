from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start_quiz, check_answer, show_stats, 
    start_support, handle_support_question,
    start_reference, handle_reference_band,
    show_assortment, show_cart
)

# Инициализация базы данных
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
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
    user_id = update.effective_user.id
    text = update.message.text
    
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
        # Проверяем, не находится ли пользователь в каком-либо состоянии
        from handlers import user_states
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
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик ошибок
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Произошла ошибка: {context.error}")
    
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
