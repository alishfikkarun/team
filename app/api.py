import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import cfg
from .db import db
from .handlers import router as bot_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


bot: Bot | None = None
dp: Dispatcher | None = None
bot_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, bot_task
    await db.init()
    bot = Bot(token=cfg.BOT_TOKEN, parse_mode="HTML")
    me = await bot.get_me()
    cfg.BOT_USERNAME = me.username

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(bot_router)

    logger.info("Starting bot polling as @%s", cfg.BOT_USERNAME)
    bot_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

    yield

    if bot_task:
        bot_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await bot_task
    if dp:
        await dp.storage.close()
        await dp.storage.wait_closed()
    if bot:
        await bot.session.close()


app = FastAPI(title="Gifts Backend API", version="1.0.0", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/gifts/{slug}")
async def get_gift(slug: str):
    data = await db.get_gift_by_slug(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Gift not found")
    return JSONResponse(content=data)
