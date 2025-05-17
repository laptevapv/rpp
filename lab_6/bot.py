import os
from dotenv import load_dotenv
from aiogram import Bot,Dispatcher,types
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio

# Словарь для хранения валют и курса
currency = {}

# Список команд для меню
commands = [
    types.BotCommand(command="save_currency", description="Сохранить курс валюты"),
    types.BotCommand(command="convert", description="конвертировать валюту"),
    types.BotCommand(command="help", description="Помощь")
]

# Состояние для FSM
class currency_states(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()

class convert_states(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_amount = State()


load_dotenv()
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=bot_token)
dp = Dispatcher()

# Задание 1

# Обработчик команды strt
@dp.message(Command('start'))
async def start_command(messege: types.Message):
    await messege.reply("Привет, я ТГ-бот Конвертация Валют")

# Обработчик команды save_currency
@dp.message(Command('save_currency'))
async def cmd_save_currency(messege: types.Message, state: FSMContext):
    await messege.answer('Введите название валюты:(Например Доллар):')
    await state.set_state(currency_states.waiting_for_currency_name)

# Обработчик ввода названия валюты
@dp.message(currency_states.waiting_for_currency_name)
async def process_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper().strip() 
# Сохранение названия валюты во временное хранилище
    await state.update_data(currency_name=currency_name)

    await message.answer(f"Введите курс валюты {currency_name} к рублю (например: 90.5):")
    await state.set_state(currency_states.waiting_for_currency_rate)

# Обработчик ввода курса
@dp.message(currency_states.waiting_for_currency_rate)
async def process_currency_rate(messege: types.Message, state: FSMContext):
    try:
        rate = float(messege.text.replace(',','.'))

        # Сохранненое название валюты
        data = await state.get_data()
        currency_name = data['currency_name']

        # Сохраняем валюту в словарь
        currency[currency_name] = rate
        
        await messege.answer(f"Курс {currency_name} сохранен: {rate} RUB")
        await state.clear()

    except ValueError:
        await messege.answer("Введеные данные некортектны. Попробуйте еще раз:")

# Задание 2

# Обработчик команды convert
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    if not currency:
        await message.answer(" Нет сохранённых валют. Сначала используйте /save_currency")
        return
    
    await message.answer(
        "Введите название валюты для конвертации (доступные: " 
        + ", ".join(currency.keys()) + "):"
    )
    await state.set_state(convert_states.waiting_for_currency_name)

# Обработчик ввода названия валюты
@dp.message(convert_states.waiting_for_currency_name)
async def process_convert_currency(message: types.Message, state: FSMContext):
    currency = message.text.upper().strip()
    
    if currency not in currency:
        await message.answer(f" Валюта {currency} не найдена. Попробуйте ещё раз:")
        return
    
    await state.update_data(currency=currency)
    await message.answer(f"Введите сумму в {currency} для конвертации в RUB:")
    await state.set_state(convert_states.waiting_for_amount)

# Обработчик ввода суммы
@dp.message(convert_states.waiting_for_amount)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency = data['currency']
        rate = currency[currency]
        
        result = amount * rate
        await message.answer(
            f" Результат: {amount} {currency} = {round(result, 2)} RUB\n"
            f"Курс: 1 {currency} = {rate} RUB"
        )
        await state.clear()
    
    except ValueError:
        await message.answer(" Ошибка! Введите число (например: 150.5):")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())