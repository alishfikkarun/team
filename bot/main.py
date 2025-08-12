import asyncio
import logging
import os
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config import Config
from database import Database
from s3_uploader import S3Uploader
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States for FSM
class GiftStates(StatesGroup):
    waiting_for_price = State()

class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.bot = Bot(token=self.config.BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = Database()
        self.s3_uploader = S3Uploader()
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        self.dp.message.register(self.start_command, Command("start"))
        self.dp.message.register(self.handle_unique_gift, lambda message: hasattr(message, 'unique_gift') and message.unique_gift is not None)
        self.dp.message.register(self.handle_price_input, GiftStates.waiting_for_price)
    
    async def start_command(self, message: types.Message):
        """Handle /start command"""
        if message.chat.type != 'private':
            await message.reply("Open the bot in private messages to continue")
            return
        
        await message.reply(
            "Welcome! Send me a Telegram gift to process it for sale."
        )
    
    async def handle_unique_gift(self, message: types.Message, state: FSMContext):
        """Handle messages containing unique_gift"""
        if message.chat.type != 'private':
            await message.reply("Open the bot in private messages to continue")
            return
        
        try:
            unique_gift = message.unique_gift
            if not unique_gift:
                return
            
            # Extract gift data safely
            gift_data = {
                "title": getattr(unique_gift, 'title', ''),
                "id": getattr(unique_gift, 'id', ''),
                "model_name": '',
                "model_rarity_per_mille": 0,
                "symbol_name": '',
                "symbol_rarity_per_mille": 0,
                "backdrop_color": '',
                "backdrop_rarity_per_mille": 0
            }
            
            # Extract model data if available
            if hasattr(unique_gift, 'model') and unique_gift.model:
                model = unique_gift.model
                gift_data["model_name"] = getattr(model, 'name', '')
                gift_data["model_rarity_per_mille"] = getattr(model, 'rarity_per_mille', 0)
            
            # Extract symbol data if available 
            if hasattr(unique_gift, 'symbol') and unique_gift.symbol:
                symbol = unique_gift.symbol
                gift_data["symbol_name"] = getattr(symbol, 'name', '')
                gift_data["symbol_rarity_per_mille"] = getattr(symbol, 'rarity_per_mille', 0)
            
            # Extract backdrop data if available
            if hasattr(unique_gift, 'backdrop') and unique_gift.backdrop:
                backdrop = unique_gift.backdrop
                gift_data["backdrop_color"] = getattr(backdrop, 'color', '')
                gift_data["backdrop_rarity_per_mille"] = getattr(backdrop, 'rarity_per_mille', 0)
            
            # Download and upload sticker if available
            image_url = ""
            if (hasattr(unique_gift, 'model') and unique_gift.model and 
                hasattr(unique_gift.model, 'sticker') and unique_gift.model.sticker and
                hasattr(unique_gift.model.sticker, 'file_id')):
                
                file_id = unique_gift.model.sticker.file_id
                
                # Download file from Telegram
                file = await self.bot.get_file(file_id)
                if file and file.file_path:
                    file_data = await self.bot.download_file(file.file_path)
                    if file_data:
                        # Upload to S3
                        filename = f"gifts/{uuid.uuid4()}.webp"
                        image_url = await self.s3_uploader.upload_file(file_data.read(), filename)
            
            # Store gift data temporarily in state
            await state.update_data(
                gift_data=gift_data,
                image_url=image_url
            )
            
            # Ask for price
            await message.reply("Enter the price at which this gift will be sold (e.g., '9.9 TON'):")
            await state.set_state(GiftStates.waiting_for_price)
            
        except Exception as e:
            logger.error(f"Error processing unique gift: {e}")
            await message.reply("Error processing the gift. Please try again.")
    
    async def handle_price_input(self, message: types.Message, state: FSMContext):
        """Handle price input from user"""
        try:
            if not message.text:
                await message.reply("Please provide a valid price.")
                return
                
            price = message.text.strip()
            state_data = await state.get_data()
            gift_data = state_data.get('gift_data', {})
            image_url = state_data.get('image_url', '')
            
            # Create complete payload
            payload = {
                **gift_data,
                "image_url": image_url,
                "price": price
            }
            
            # Generate slug and save to database
            slug = str(uuid.uuid4())[:8]
            self.db.save_gift(slug, json.dumps(payload))
            
            # Create WebApp button
            webapp_url = f"{self.config.WEBAPP_URL}/gift/{slug}"
            keyboard = ReplyKeyboardBuilder()
            keyboard.add(KeyboardButton(
                text="Open Gift Card",
                web_app=WebAppInfo(url=webapp_url)
            ))
            
            await message.reply(
                f"Gift processed successfully! Price set to {price}",
                reply_markup=keyboard.as_markup(resize_keyboard=True)
            )
            
            # Clear state
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error handling price input: {e}")
            await message.reply("Error processing the price. Please try again.")
    
    async def start_polling(self):
        """Start the bot"""
        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)

async def main():
    bot = TelegramBot()
    await bot.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
