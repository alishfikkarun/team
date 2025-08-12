# bot/bot_handlers.py
import os
import io
import uuid
import json
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from .db import save_gift
from .s3uploader import upload_fileobj

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com")

class GiftStates(StatesGroup):
    waiting_price = State()

# helper to safely extract nested keys from message.dict()
def extract_unique_gift_from_message(message: Message):
    d = message.to_python()  # dict representation
    # service messages: check keys 'service' or 'new_chat' depending on Telegram schema
    # We will search for 'unique_gift' anywhere in dict
    def find_key(obj, key):
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                res = find_key(v, key)
                if res is not None:
                    return res
        elif isinstance(obj, list):
            for item in obj:
                res = find_key(item, key)
                if res is not None:
                    return res
        return None
    return find_key(d, "unique_gift")

async def handle_message(bot: Bot, message: Message, state: FSMContext):
    unique_gift = extract_unique_gift_from_message(message)
    if not unique_gift:
        return  # ignore non-gift messages

    # If chat not private -> instruct to open bot in private
    if message.chat.type != "private":
        await message.reply("Откройте бота в личных сообщениях, чтобы продолжить")
        return

    # Extract required fields defensively
    title = unique_gift.get("title")
    uid = unique_gift.get("id")
    model = unique_gift.get("model", {})
    symbol = unique_gift.get("symbol", {})
    backdrop = unique_gift.get("backdrop", {})

    model_name = model.get("name")
    model_rarity = model.get("rarity_per_mille")
    sticker = model.get("sticker") or {}
    sticker_file_id = sticker.get("file_id")
    symbol_name = symbol.get("name")
    symbol_rarity = symbol.get("rarity_per_mille")
    backdrop_color = backdrop.get("color")
    backdrop_rarity = backdrop.get("rarity_per_mille")

    # download file via file_id
    if not sticker_file_id:
        await message.reply("Подарок пришёл без стикера — не могу обработать.")
        return

    # get file info
    file = await bot.get_file(sticker_file_id)
    file_path = file.file_path  # remote path
    # download into memory
    bio = io.BytesIO()
    await bot.download_file(file_path, bio)
    bio.seek(0)

    # upload to S3
    key = f"gifts/{uid}_{uuid.uuid4().hex}.webp"  # extension guessed; you could parse from file_path
    try:
        image_url = upload_fileobj(bio, key, content_type="image/webp")
    except Exception as e:
        await message.reply("Ошибка при загрузке изображения. Попробуйте позже.")
        return

    # save temp data in FSM context
    await state.update_data(
        temp_gift = {
            "title": title,
            "id": uid,
            "model_name": model_name,
            "model_rarity_per_mille": model_rarity,
            "symbol_name": symbol_name,
            "symbol_rarity_per_mille": symbol_rarity,
            "backdrop_color": backdrop_color,
            "backdrop_rarity_per_mille": backdrop_rarity,
            "image_url": image_url
        }
    )

    await message.answer("Укажите цену, по которой будет продаваться подарок (например: 9.9 TON)")
    await state.set_state(GiftStates.waiting_price)

async def price_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    temp = data.get("temp_gift")
    if not temp:
        await message.reply("Нет данных о подарке — начните сначала.")
        await state.clear()
        return
    price = message.text.strip()
    # Build payload
    payload = {
        "title": temp.get("title"),
        "id": temp.get("id"),
        "model_name": temp.get("model_name"),
        "model_rarity_per_mille": temp.get("model_rarity_per_mille"),
        "symbol_name": temp.get("symbol_name"),
        "symbol_rarity_per_mille": temp.get("symbol_rarity_per_mille"),
        "backdrop_color": temp.get("backdrop_color"),
        "backdrop_rarity_per_mille": temp.get("backdrop_rarity_per_mille"),
        "image_url": temp.get("image_url"),
        "price": price
    }

    # slug
    slug = uuid.uuid4().hex[:8]
    save_gift(slug, payload)

    # prepare WebApp button
    web_button = KeyboardButton(text="Open in Web", web_app=WebAppInfo(url=f"{WEBAPP_URL}/gift/{slug}"))
    markup = ReplyKeyboardMarkup(keyboard=[[web_button]], resize_keyboard=True, one_time_keyboard=True)

    await message.answer("Готово — нажмите кнопку, чтобы открыть веб-страницу товара:", reply_markup=markup)
    await state.clear()
