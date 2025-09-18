from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import random
from database import update_quiz_stats, get_quiz_stats, add_support_question, get_band_country
from music_data import MUSIC_QUIZ_DATA

# Переменная для хранения состояния пользователей
user_states = {}

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

# Заглушки для корзины (будут реализованы позже)
async def show_assortment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функционал ассортимента в разработке.")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Функционал корзины в разработке.")
