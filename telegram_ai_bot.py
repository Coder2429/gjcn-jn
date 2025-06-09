import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import openai
import replicate
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Например, "@your_channel"

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния FSM (Finite State Machine)
class PostGeneration(StatesGroup):
    waiting_for_text_prompt = State()
    waiting_for_image_prompt = State()

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "🤖 Привет! Я бот для генерации постов с ИИ.\n"
        "Доступные команды:\n"
        "/generate_post - Создать новый пост\n"
        "/help - Помощь"
    )

# Команда /generate_post
@dp.message_handler(commands=['generate_post'])
async def cmd_generate_post(message: types.Message):
    await PostGeneration.waiting_for_text_prompt.set()
    await message.reply("📝 Введите текст для генерации (например, 'Напиши пост про ИИ'):")

# Генерация текста через OpenAI
@dp.message_handler(state=PostGeneration.waiting_for_text_prompt)
async def process_text_prompt(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text_prompt'] = message.text

    await PostGeneration.next()
    await message.reply("🎨 Теперь введите описание для изображения (например, 'Футуристический город'):")

# Генерация изображения и публикация
@dp.message_handler(state=PostGeneration.waiting_for_image_prompt)
async def process_image_prompt(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['image_prompt'] = message.text

    await message.reply("🔄 Генерирую пост...")

    try:
        # Генерация текста
        text = generate_text(data['text_prompt'])
        
        # Генерация изображения
        image_url = generate_image(data['image_prompt'])
        
        # Публикация в канал
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=image_url,
            caption=text
        )
        await message.reply("✅ Пост успешно опубликован в канал!")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")
    finally:
        await state.finish()

# Функция генерации текста (OpenAI)
def generate_text(prompt):
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content

# Функция генерации изображения (Replicate/Stable Diffusion)
def generate_image(prompt):
    output = replicate.run(
        "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        input={"prompt": prompt, "width": 512, "height": 512}
    )
    return output[0]

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)