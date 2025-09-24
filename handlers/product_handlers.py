from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_categories

async def show_assortment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    keyboard = []
    
    for category_id, category_name in categories:
        keyboard.append([InlineKeyboardButton(category_name, callback_data=f'category_{category_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎸 Выберите категорию товаров:", reply_markup=reply_markup)