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

## Troubleshooting
- **Version conflicts:** Ensure Python 3.6+ is installed.
- **Permissions:** Run commands with appropriate privileges.
- **Token issues:** Verify BOT_TOKEN is correctly set in config.py.