# bot/app.py
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from bot.db import init_db, get_gift
from bot.bot_handlers import handle_message, price_handler, GiftStates
from aiogram.types import Update
from aiogram import F
from aiogram.client.session.aiohttp import AiohttpSession

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")

# init db
init_db()

# == FastAPI app (API to serve gift payloads) ==
api = FastAPI()

@api.get("/api/gifts/{slug}")
def api_get_gift(slug: str):
    payload = get_gift(slug)
    if not payload:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(payload)

# == aiogram bot (polling inside same process) ==
async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # register generic message handler to capture service messages (unique_gift)
    @dp.message()
    async def _any_msg_handler(message, state=dp.storage):
        # We cannot type annotate here easily; instead call our handler functions
        from aiogram.fsm.context import FSMContext
        # Use dispatcher.get_current() trick; simpler: use Dispatcher.middleware? For simplicity, reimport state via Dispatcher
        pass

    # Instead of using decorator above (complex), we will attach handlers via dispatcher.router
    from aiogram import Router
    router = Router()
    # Raw message handler:
    @router.message()
    async def raw_message_handler(message, state: FSMContext):
        # Try to process unique_gift
        await handle_message(bot, message, state)

    # Handler for waiting price state
    @router.message(lambda message: True, state=GiftStates.waiting_price)
    async def _price_msg(message, state: FSMContext):
        await price_handler(message, state)

    dp.include_router(router)

    # start polling
    await dp.start_polling(bot)

# Run both FastAPI (uvicorn) and aiogram polling concurrently
if __name__ == "__main__":
    async def main():
        # run uvicorn in background
        config = uvicorn.Config(api, host="0.0.0.0", port=int(os.getenv("API_PORT", 8000)), log_level="info")
        server = uvicorn.Server(config)
        task_uvicorn = asyncio.create_task(server.serve())
        task_bot = asyncio.create_task(start_bot())
        await asyncio.gather(task_uvicorn, task_bot)

    asyncio.run(main())
