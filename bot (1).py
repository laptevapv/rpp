import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio

# Словарь для хранения валют и курса
currency_rates = {} 

# Список команд для меню
commands = [
    types.BotCommand(command="save_currency", description="Сохранить курс валюты"),
    types.BotCommand(command="convert", description="Конвертировать валюту"),
    types.BotCommand(command="help", description="Помощь")
]

# Состояние для FSM
class CurrencyStates(StatesGroup):  
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()

class ConvertStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_amount = State()

load_dotenv()
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=bot_token)
dp = Dispatcher()

# Обработчик команды start
@dp.message(Command('start'))
async def start_command(message: types.Message):  
    await message.reply("Привет, я ТГ-бот Конвертация Валют")

# Обработчик команды save_currency
@dp.message(Command('save_currency'))
async def cmd_save_currency(message: types.Message, state: FSMContext):
    await message.answer('Введите название валюты (например, Доллар):')
    await state.set_state(CurrencyStates.waiting_for_currency_name)

# Обработчик ввода названия валюты
@dp.message(CurrencyStates.waiting_for_currency_name)
async def process_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper().strip()
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите курс валюты {currency_name} к рублю (например: 90.5):")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)

# Обработчик ввода курса
@dp.message(CurrencyStates.waiting_for_currency_rate)
async def process_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data['currency_name']
        currency_rates[currency_name] = rate
        await message.answer(f"Курс {currency_name} сохранен: {rate} RUB")
        await state.clear()
    except ValueError:
        await message.answer("Введенные данные некорректны. Попробуйте еще раз:")

# Обработчик команды convert
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    if not currency_rates:
        await message.answer("Нет сохранённых валют. Сначала используйте /save_currency")
        return
    
    await message.answer(
        "Введите название валюты для конвертации (доступные: " 
        + ", ".join(currency_rates.keys()) + "):"
    )
    await state.set_state(ConvertStates.waiting_for_currency_name)

# Обработчик ввода названия валюты
@dp.message(ConvertStates.waiting_for_currency_name)
async def process_convert_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.upper().strip()
    
    if currency_name not in currency_rates:
        await message.answer(f"Валюта {currency_name} не найдена. Попробуйте ещё раз:")
        return
    
    await state.update_data(currency_name=currency_name)  
    await message.answer(f"Введите сумму в {currency_name} для конвертации в RUB:")
    await state.set_state(ConvertStates.waiting_for_amount)

# Обработчик ввода суммы
@dp.message(ConvertStates.waiting_for_amount)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data['currency_name']  
        rate = currency_rates[currency_name]  
        
        result = amount * rate
        await message.answer(
            f"Результат: {amount} {currency_name} = {round(result, 2)} RUB\n"
            f"Курс: 1 {currency_name} = {rate} RUB"
        )
        await state.clear()
    
    except ValueError:
        await message.answer("Ошибка! Введите число (например: 150.5):")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())