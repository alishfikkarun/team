import asyncio
import io
import logging
import mimetypes
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


def short_uuid() -> str:
    return uuid4().hex[:8]


async def download_file_bytes(bot: Bot, file_id: str) -> tuple[bytes, str]:
    """
    Returns (bytes, extension)
    """
    # aiogram v3: get_file + download
    file = await bot.get_file(file_id)
    file_path = file.file_path or ""
    ext = Path(file_path).suffix or ""
    buf = io.BytesIO()
    try:
        await bot.download_file(file_path, destination=buf)
    except Exception:
        # Fallback for aiogram v3: bot.download(file, destination)
        try:
            buf = io.BytesIO()
            await bot.download(file, destination=buf)
        except Exception as e:
            logger.exception("Failed to download file: %s", e)
            raise
    return buf.getvalue(), ext


def guess_content_type(ext: str) -> str:
    ctype, _ = mimetypes.guess_type("x" + ext)
    return ctype or "application/octet-stream"


def extract_unique_gift_fields(message: Any) -> Optional[Dict[str, Any]]:
    """
    Extracts required fields from a service message with gift/unique_gift.
    Tries to be resilient to schema changes.
    Expected fields:
      - title
      - unique_gift.id
      - model.name
      - model.rarity_per_mille
      - model.sticker.file_id
      - symbol.name
      - symbol.rarity_per_mille
      - backdrop.color
      - backdrop.rarity_per_mille
    """
    g = getattr(message, "gift", None)
    if g is None:
        # In case library exposes unique_gift directly
        ug = getattr(message, "unique_gift", None)
        if ug is None:
            return None
        title = getattr(ug, "title", None) or "Gift"
        unique = ug
    else:
        title = getattr(g, "title", None) or "Gift"
        unique = getattr(g, "unique_gift", None)

    if unique is None:
        return None

    model = getattr(unique, "model", None)
    symbol = getattr(unique, "symbol", None)
    backdrop = getattr(unique, "backdrop", None)

    # Sticker can be under model.sticker or unique.sticker
    sticker = None
    if model and hasattr(model, "sticker"):
        sticker = getattr(model, "sticker", None)
    if sticker is None and hasattr(unique, "sticker"):
        sticker = getattr(unique, "sticker", None)

    file_id = getattr(sticker, "file_id", None) if sticker else None
    if not file_id:
        logger.warning("No sticker.file_id found in unique_gift")
        return None

    payload = {
        "title": title,
        "id": getattr(unique, "id", None),
        "model_name": getattr(model, "name", None) if model else None,
        "model_rarity_per_mille": getattr(model, "rarity_per_mille", None) if model else None,
        "symbol_name": getattr(symbol, "name", None) if symbol else None,
        "symbol_rarity_per_mille": getattr(symbol, "rarity_per_mille", None) if symbol else None,
        "backdrop_color": getattr(backdrop, "color", None) if backdrop else None,
        "backdrop_rarity_per_mille": getattr(backdrop, "rarity_per_mille", None) if backdrop else None,
        "sticker_file_id": file_id,
    }
    return payload
