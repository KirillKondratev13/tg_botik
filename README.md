# Music Telegram Bot

## Project Description
A Telegram bot for a music store featuring user management, quiz, product catalog, orders, support, and an admin panel.

## Prerequisites
- Python 3.6 or higher
- BOT_TOKEN from @BotFather
- SQLite (built-in with Python)

## Installation
1. `sudo apt update && sudo apt upgrade -y`
2. `sudo apt install git python3 python3-pip -y`
3. `git clone https://github.com/KirillKondratev13/tg_botik.git && cd tg_botik`
4. `python3 -m venv venv && source venv/bin/activate`
5. `pip install python-telegram-bot`

## Configuration
Edit `config.py` to set your BOT_TOKEN.

## Running
`python3 bot.py`

## Adding an Administrator
To add an administrator to the bot's database, use the following SQL command after the bot has been run at least once (to create the database):

```
sqlite3 music_bot.db "INSERT INTO administrators (user_id, password) VALUES (558525097, 'admin');"
```

Replace `558525097` with the actual Telegram user ID and `'admin'` with a secure password.

## Troubleshooting
- **Version conflicts:** Ensure Python 3.6+ is installed.
- **Permissions:** Run commands with appropriate privileges.
- **Token issues:** Verify BOT_TOKEN is correctly set in config.py.

## Security Best Practices
- Never commit sensitive data like bot tokens to the repository. Use environment variables instead.
- Ensure `config.py` is added to `.gitignore`.
- Consider using `python-dotenv` to load environment variables from a `.env` file (not committed).
- Regularly rotate tokens and monitor bot usage for unauthorized access.