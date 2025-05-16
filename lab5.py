import asyncio
import aiogram
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from dotenv import load_dotenv
import os

# Подключение к базе данных
dsn = "dbname='lab5' user='postgres' password='postgres' host='localhost'"
conn = psycopg2.connect(dsn)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота
bot = Bot(os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher(bot, storage=MemoryStorage())

# Определение состояний FSM
class AddCurrencyStep(StatesGroup):
    name = State()
    rate = State()

class DeleteCurrencyStep(StatesGroup):
    name = State()

class ChangeRateStep(StatesGroup):
    name = State()
    rate = State()

class ConvertCurrencyStep(StatesGroup):
    name = State()
    amount = State()

# Обрабатывает команду /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Я бот для работы с валютами.")

# Обрабатывает команду /manage_currency — проверяет админа и предлагает действия
@dp.message_handler(commands=['manage_currency'])
async def manage_currency(message: types.Message):
    admin_chat_id = str(message.chat.id)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE chat_id = %s", (admin_chat_id,))
    admin = cursor.fetchone()
    if admin is None:
        await message.answer("Нет доступа к команде")
        return

    markup = types.ReplyKeyboardMarkup(row_width=3)
    btn1 = types.KeyboardButton("Добавить валюту")
    btn2 = types.KeyboardButton("Удалить валюту")
    btn3 = types.KeyboardButton("Изменить курс валюты")
    markup.add(btn1, btn2, btn3)

    await message.answer("Выберите действие:", reply_markup=markup)

# Обрабатывает добавление новой валюты
@dp.message_handler(lambda message: message.text == "Добавить валюту")
async def add_currency(message: types.Message):
    await message.answer("Введите название валюты:")
    await AddCurrencyStep.name.set()

@dp.message_handler(state=AddCurrencyStep.name)
async def add_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM currencies WHERE currency_name = %s", (currency_name,))
    if cursor.fetchone() is not None:
        await message.answer("Данная валюта уже существует")
        return

    await state.update_data(currency_name=currency_name)
    await message.answer("Введите курс к рублю:")
    await AddCurrencyStep.next()

@dp.message_handler(state=AddCurrencyStep.rate)
async def add_rate_step(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.strip())
        data = await state.get_data()
        currency_name = data.get('currency_name')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)", (currency_name, rate))
        conn.commit()
        await message.answer(f"Валюта {currency_name} успешно добавлена")
        await state.finish()
    except ValueError:
        await message.answer("Некорректный формат курса")

# Обрабатывает удаление валюты
@dp.message_handler(lambda message: message.text == "Удалить валюту")
async def delete_currency(message: types.Message):
    await message.answer("Введите название валюты для удаления:")
    await DeleteCurrencyStep.name.set()

@dp.message_handler(state=DeleteCurrencyStep.name)
async def delete_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM currencies WHERE currency_name = %s", (currency_name,))
    conn.commit()
    await message.answer(f"Валюта {currency_name} успешно удалена")
    await state.finish()

# Обрабатывает изменение курса валюты
@dp.message_handler(lambda message: message.text == "Изменить курс валюты")
async def change_rate(message: types.Message):
    await message.answer("Введите название валюты для изменения курса:")
    await ChangeRateStep.name.set()

@dp.message_handler(state=ChangeRateStep.name)
async def change_rate_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    await state.update_data(currency_name=currency_name)
    await message.answer("Введите новый курс к рублю:")
    await ChangeRateStep.rate.set()

@dp.message_handler(state=ChangeRateStep.rate)
async def change_rate_value(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.strip())
        data = await state.get_data()
        currency_name = data.get('currency_name')
        cursor = conn.cursor()
        cursor.execute("UPDATE currencies SET rate = %s WHERE currency_name = %s", (rate, currency_name))
        conn.commit()
        await message.answer(f"Курс валюты {currency_name} успешно изменен")
    except ValueError:
        await message.answer("Некорректный формат курса")
    await state.finish()

# Обрабатывает команду /get_currencies — показывает список валют
@dp.message_handler(commands=['get_currencies'])
async def get_currencies(message: types.Message):
    cursor = conn.cursor()
    cursor.execute("SELECT currency_name, rate FROM currencies")
    currencies = cursor.fetchall()
    if currencies:
        response = "Текущие курсы валют к рублю:\n"
        for currency in currencies:
            response += f"{currency[0]}: {currency[1]}\n"
    else:
        response = "В базе данных нет сохраненных валют"
    await message.answer(response)

# Обрабатывает команду /convert — запрашивает валюту и сумму, выполняет конвертацию
@dp.message_handler(commands=['convert'])
async def convert_currency(message: types.Message):
    await message.answer("Введите название валюты:")
    await ConvertCurrencyStep.name.set()

@dp.message_handler(state=ConvertCurrencyStep.name)
async def convert_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()
    cursor = conn.cursor()
    cursor.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
    currency = cursor.fetchone()
    if currency:
        await state.update_data(rate=currency[0], currency_name=currency_name)
        await message.answer("Введите сумму:")
        await ConvertCurrencyStep.next()
    else:
        await message.answer(f"Валюта {currency_name} не найдена")

@dp.message_handler(state=ConvertCurrencyStep.amount)
async def convert_amount_step(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        data = await state.get_data()
        currency_name = data.get('currency_name')
        rate = data.get('rate')
        if rate is None:
            await message.answer("Курс валюты не найден. Пожалуйста, проверьте правильность введенного названия валюты.")
            await state.finish()
            return
        converted_amount = amount * float(rate)
        await message.answer(f"{amount} {currency_name} = {converted_amount} рублей")
    except ValueError:
        await message.answer("Некорректный формат суммы")
    await state.finish()

# Обрабатывает команду /add_admin — добавляет пользователя в список администраторов
@dp.message_handler(commands=['add_admin'])
async def add_admin(message: types.Message):
    admin_chat_id = message.chat.id
    cursor = conn.cursor()
    cursor.execute("INSERT INTO admins (chat_id) VALUES (%s)", (admin_chat_id,))
    conn.commit()
    await message.answer("Вы добавлены в список администраторов")

# Обработка неизвестных команд
@dp.message_handler()
async def echo_all(message: types.Message):
    await message.answer("Я не понимаю вашего запроса. Воспользуйтесь командами.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
