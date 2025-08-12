import asyncio
import logging
from typing import Any, Dict

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from .config import cfg
from .db import db
from .s3 import upload_bytes_public
from .utils import short_uuid, download_file_bytes, guess_content_type, extract_unique_gift_fields

logger = logging.getLogger(__name__)
router = Router()


class GiftStates(StatesGroup):
    waiting_for_price = State()


@router.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        "Привет! Отправьте мне сервисное сообщение подарка (unique_gift), и я подготовлю карточку для WebApp."
    )


@router.message(lambda m: getattr(m, "gift", None) is not None or getattr(m, "unique_gift", None) is not None)
async def on_unique_gift(message: Message, state: FSMContext, bot: Bot):
    # If not a private chat
    if message.chat.type != "private":
        text = "Откройте бота в личных сообщениях, чтобы продолжить."
        if cfg.BOT_USERNAME:
            text += f"\nhttps://t.me/{cfg.BOT_USERNAME}"
        await message.answer(text)
        return

    fields = extract_unique_gift_fields(message)
    if not fields:
        await message.answer("Не удалось извлечь данные подарка. Убедитесь, что это сервисное сообщение с уникальным подарком.")
        return

    # Download sticker and upload to S3
    try:
        file_bytes, ext = await download_file_bytes(bot, fields["sticker_file_id"])
        ctype = guess_content_type(ext)
        slug = short_uuid()
        s3_key = f"gifts/{slug}{ext or '.webp'}"
        image_url = await asyncio.to_thread(upload_bytes_public, file_bytes, s3_key, ctype)
        fields["image_url"] = image_url
        fields.pop("sticker_file_id", None)
        fields["slug"] = slug
    except Exception as e:
        logger.exception("Failed to process file upload: %s", e)
        await message.answer("Ошибка при загрузке изображения подарка.")
        return

    # Save interim data in FSM to wait for price
    await state.update_data(gift_fields=fields)
    await state.set_state(GiftStates.waiting_for_price)
    await message.answer("Укажите цену, по которой будет продаваться подарок (например: 9.9 TON):")


@router.message(GiftStates.waiting_for_price)
async def on_price(message: Message, state: FSMContext):
    price = (message.text or "").strip()
    if not price:
        await message.answer("Пожалуйста, введите корректную цену.")
        return

    data = await state.get_data()
    fields: Dict[str, Any] = data.get("gift_fields", {})
    if not fields:
        await message.answer("Сессия истекла. Отправьте подарок ещё раз.")
        await state.clear()
        return

    payload = {
        "title": fields.get("title"),
        "id": fields.get("id"),
        "model_name": fields.get("model_name"),
        "model_rarity_per_mille": fields.get("model_rarity_per_mille"),
        "symbol_name": fields.get("symbol_name"),
        "symbol_rarity_per_mille": fields.get("symbol_rarity_per_mille"),
        "backdrop_color": fields.get("backdrop_color"),
        "backdrop_rarity_per_mille": fields.get("backdrop_rarity_per_mille"),
        "image_url": fields.get("image_url"),
        "price": price,
    }
    slug = fields.get("slug")

    try:
        await db.save_gift(slug, payload)
    except Exception as e:
        logger.exception("DB save failed: %s", e)
        await message.answer("Ошибка при сохранении данных.")
        await state.clear()
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Открыть WebApp", web_app=WebAppInfo(url=f"{cfg.WEBAPP_URL}/gift/{slug}"))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Готово! Откройте карточку в WebApp:", reply_markup=kb)
    await state.clear()
