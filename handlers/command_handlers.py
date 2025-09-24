from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import register_user
from .states import user_states, admin_states

ADMIN_PASSWORD_PROMPT = "Введите пароль администратора:"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Регистрируем пользователя, если его нет в таблице users
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

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_states[user_id] = {"state": "waiting_password"}
    await update.message.reply_text(ADMIN_PASSWORD_PROMPT)

async def handle_admin_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in admin_states or admin_states[user_id].get("state") != "waiting_password":
        return
    password = update.message.text.strip()
    from database import check_admin_password
    if check_admin_password(user_id, password):
        admin_states[user_id] = {"state": "admin_menu"}
        from .admin_handlers import show_admin_menu
        await show_admin_menu(update, context)
    else:
        await update.message.reply_text("Неверный пароль или недостаточно прав.")
        del admin_states[user_id]