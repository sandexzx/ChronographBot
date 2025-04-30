import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from openai import OpenAI
from config import REMINDER_INTERVAL, STATS_INTERVALS, PROMPTS
from data_manager import DataManager
from logger import logger

# Load environment variables
load_dotenv()

# Initialize bot and dispatcher
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize data manager
data_manager = DataManager()

# Store logs in memory (in production, use a database)
logs = []

# Keyboard buttons
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Заполнить отчет")],
        [KeyboardButton(text="📊 Статистика")],
    ],
    resize_keyboard=True
)

stats_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="30 минут"), KeyboardButton(text="1 час")],
        [KeyboardButton(text="4 часа"), KeyboardButton(text="10 часов")],
        [KeyboardButton(text="Сутки"), KeyboardButton(text="Неделя")],
        [KeyboardButton(text="🔙 Назад")],
    ],
    resize_keyboard=True
)

# Define states
class ReportStates(StatesGroup):
    waiting_for_report = State()

async def send_reminder():
    """Send reminder to admin every REMINDER_INTERVAL minutes if no report was submitted"""
    while True:
        last_report_time = data_manager.get_last_report_time()
        time_since_last_report = datetime.now() - last_report_time
        
        # Only send reminder if enough time has passed since the last report
        if time_since_last_report.total_seconds() >= REMINDER_INTERVAL * 60:
            admin_id = int(os.getenv('ADMIN_ID'))
            await bot.send_message(
                admin_id,
                "⏰ Время заполнить отчет!",
                reply_markup=main_keyboard
            )
        
        # Wait for the reminder interval before checking again
        await asyncio.sleep(REMINDER_INTERVAL * 60)

async def enhance_log_with_gpt(log_entry: str) -> str:
    """Enhance log entry using GPT"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": PROMPTS['log_enhancement']},
                {"role": "user", "content": log_entry}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error enhancing log: {e}")
        return log_entry

async def get_stats_summary(time_period: str, activities: list) -> str:
    """Get statistics summary using GPT"""
    try:
        prompt = PROMPTS['stats_summary_short' if time_period in ['30m', '1h', '4h', '10h'] else 'stats_summary_long']
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Time period: {time_period}\nActivities: {activities}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting stats summary: {e}")
        return "Ошибка при получении статистики"

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    if str(message.from_user.id) == os.getenv('ADMIN_ID'):
        await message.answer(
            f"👋 Привет! Я бот для ведения лога жизни.\n"
            f"Я буду напоминать тебе каждые {REMINDER_INTERVAL} минут заполнить отчет.",
            reply_markup=main_keyboard
        )
    else:
        logger.warning(f"Unauthorized access attempt from user {message.from_user.id}")
        await message.answer("Извините, этот бот доступен только для администратора.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📚 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n\n"
        "Основные функции:\n"
        "📝 Заполнить отчет - Добавить новую запись в лог\n"
        "📊 Статистика - Просмотреть статистику за выбранный период"
    )

@dp.message(lambda message: message.text == "📝 Заполнить отчет")
async def fill_report(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == os.getenv('ADMIN_ID'):
        await message.answer(
            "Пожалуйста, напишите ваш отчет. Я улучшу его с помощью ИИ и добавлю в лог."
        )
        # Set state to wait for report
        await state.set_state(ReportStates.waiting_for_report)
    else:
        await message.answer("Извините, эта функция доступна только для администратора.")

@dp.message(ReportStates.waiting_for_report)
async def process_report(message: types.Message, state: FSMContext):
    if str(message.from_user.id) == os.getenv('ADMIN_ID'):
        logger.info(f"Processing report from admin {message.from_user.id}")
        enhanced_log = await enhance_log_with_gpt(message.text)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "original": message.text,
            "enhanced": enhanced_log
        }
        data_manager.add_log(log_entry)
        logger.info("Report successfully processed and saved")
        await message.answer(
            f"✅ Отчет добавлен и улучшен:\n\n{enhanced_log}",
            reply_markup=main_keyboard
        )
        # Reset state
        await state.clear()

@dp.message(lambda message: message.text == "📊 Статистика")
async def show_stats_menu(message: types.Message):
    if str(message.from_user.id) == os.getenv('ADMIN_ID'):
        await message.answer(
            "Выберите период для просмотра статистики:",
            reply_markup=stats_keyboard
        )
    else:
        await message.answer("Извините, эта функция доступна только для администратора.")

@dp.message(lambda message: message.text in ["30 минут", "1 час", "4 часа", "10 часов", "Сутки", "Неделя"])
async def show_stats(message: types.Message):
    if str(message.from_user.id) == os.getenv('ADMIN_ID'):
        period_map = {
            "30 минут": "30m",
            "1 час": "1h",
            "4 часа": "4h",
            "10 часов": "10h",
            "Сутки": "1d",
            "Неделя": "7d"
        }
        
        period = period_map[message.text]
        time_delta = STATS_INTERVALS[period]
        
        relevant_logs = data_manager.get_logs_by_time_period(time_delta)
        relevant_logs_texts = [log['enhanced'] for log in relevant_logs]
        
        if not relevant_logs_texts:
            await message.answer(
                f"За последний период ({message.text}) нет записей.",
                reply_markup=main_keyboard
            )
            return
        
        summary = await get_stats_summary(period, relevant_logs_texts)
        await message.answer(
            f"📊 Статистика за {message.text}:\n\n{summary}",
            reply_markup=main_keyboard
        )

@dp.message(lambda message: message.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer(
        "Возвращаемся в главное меню",
        reply_markup=main_keyboard
    )

async def main():
    logger.info("Starting Chronograph Bot")
    # Start reminder task
    asyncio.create_task(send_reminder())
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bot crashed with error: {str(e)}", exc_info=True) 