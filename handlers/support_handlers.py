from telegram import Update
from telegram.ext import ContextTypes
from database import add_support_question, get_band_country
from .states import user_states

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