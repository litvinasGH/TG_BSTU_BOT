import asyncio
import json
import os
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import emoji


# ----------------- LOGGING -----------------
logging.basicConfig(level=logging.INFO)

# ----------------- CONFIG -----------------

TOKEN = os.getenv("8485267029:AAF6bkEQpqPXdzm34nBngZhHzUzYYtdnSbg")


STORAGE_FILE = "storage.json"

EMOJI_POOL = list(emoji.EMOJI_DATA.keys())

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ----------------- STORAGE -----------------

def load_storage():
    if not os.path.exists(STORAGE_FILE):
        return {"users": {}, "blacklist": [], "batch_size": 5}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_storage(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


storage = load_storage()

# ----------------- UTILS -----------------

def get_random_emoji():
    return random.choice(EMOJI_POOL)


def ensure_user(user: types.User):
    if not user or user.is_bot:
        return

    uid = str(user.id)

    if uid in storage["blacklist"]:
        return

    if uid not in storage["users"]:
        storage["users"][uid] = {
            "emoji": get_random_emoji()
        }
        save_storage(storage)


def get_user_emoji(user_id: int):
    uid = str(user_id)
    user = storage["users"].get(uid)
    if not user:
        return None
    return user.get("emoji")


async def send_tag_batches(chat_id: int, extra_text: str = ""):
    users = storage.get("users", {})

    if not users:
        await bot.send_message(chat_id, "Хранилище пустое.")
        return

    user_ids = list(users.keys())
    batch_size = storage.get("batch_size", 5)
    batches = [user_ids[i:i + batch_size] for i in range(0, len(user_ids), batch_size)]

    for batch in batches:
        mentions = []
        for uid in batch:
            emoji = storage["users"][uid]["emoji"]
            mentions.append(f"{emoji} <a href='tg://user?id={uid}'>‎</a>")

        text = " ".join(mentions)
        if extra_text:
            text += f"\n{extra_text}"

        await bot.send_message(chat_id, text)
        await asyncio.sleep(1)

# ----------------- COMMANDS -----------------

@dp.message(Command("all"))
async def tag_all(message: types.Message):
    extra_text = ""
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        extra_text = parts[1]

    await send_tag_batches(message.chat.id, extra_text)


@dp.message(Command("set_emoji"))
async def set_emoji(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /set_emoji 😎")
        return

    emoji = parts[1].strip()
    uid = str(message.from_user.id)

    ensure_user(message.from_user)
    storage["users"][uid]["emoji"] = emoji
    save_storage(storage)

    await message.answer(f"Твой эмоджи установлен: {emoji}")


@dp.message(Command("random_emoji"))
async def random_emoji(message: types.Message):
    uid = str(message.from_user.id)
    ensure_user(message.from_user)

    new_emoji = get_random_emoji()
    storage["users"][uid]["emoji"] = new_emoji
    save_storage(storage)

    await message.answer(f"Тебе выпал новый эмоджи: {new_emoji}")


@dp.message(Command("my_emoji"))
async def my_emoji(message: types.Message):
    ensure_user(message.from_user)
    emoji = get_user_emoji(message.from_user.id)

    if emoji:
        await message.answer(f"Твой текущий эмоджи: {emoji}")
    else:
        await message.answer("У тебя ещё нет эмоджи (что странно 😅)")


@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer(
        "PONG 🏓\n"
        f"Users: {len(storage['users'])}\n"
        f"Blacklisted: {len(storage['blacklist'])}\n"
        f"Batch size: {storage['batch_size']}\n"
        f"Your ID: {message.from_user.id}\n"
        f"Your emoji: {get_user_emoji(message.from_user.id)}"
    )

# ----------------- MAIN MESSAGE HANDLER (ВСЁ ЗДЕСЬ) -----------------

@dp.message()
async def main_message_handler(message: types.Message):
    if message.chat.type not in ("group", "supergroup"):
        return

    if not message.from_user:
        return

    text = (message.text or "").lower()

    # всегда добавляем пользователя
    ensure_user(message.from_user)

    # ---- КАЛЛ ----
    if "калл" in text:
        idx = text.find("калл")
        extra_text = message.text[idx + 4:].strip()
        await send_tag_batches(message.chat.id, extra_text)
        return

    # ---- КОРОВКИ ----
    if "коровка" in text or "коровки" in text:
        jokes = [
            "Коровки сегодня на техобслуживании 🛠️",
            "Коровки в отпуске. Все. Сразу. 🏖️",
            "Коровки не выйдут, у них собрание профсоюза 🐄",
            "Коровки были, но убежали, испугались калла 😅",
            "Коровки закончились, остались только быки 💪"
        ]
        await message.reply(random.choice(jokes))
        return

# ----------------- MAIN -----------------

async def main():
    print(">>> BOT STARTED <<<")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
