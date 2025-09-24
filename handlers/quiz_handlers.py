from telegram import Update
from telegram.ext import ContextTypes
import random
from database import update_quiz_stats, get_quiz_stats
from music_data import MUSIC_QUIZ_DATA
from .states import user_states

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