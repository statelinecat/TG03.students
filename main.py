import asyncio
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from config import TOKEN, POGODA, URL, URL_FORECAST
import random
from datetime import datetime, timedelta
from gtts import gTTS
import os
from googletrans import Translator
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp
import logging

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
API_KEY = POGODA
WEATHER_URL = URL
WEATHER_URL_FORECAST = URL_FORECAST
translator = Translator()


class Form(StatesGroup):
    name = State()
    city = State()
    age = State()
    grade = State()

def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        age INTEGER NOT NULL,
        grade TEXT NOT NULL        
    )""")

    conn.commit()
    conn.close()

init_db()

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(f"Привет, как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def cmd_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Из какого ты города?")
    await state.set_state(Form.city)

@dp.message(Form.city)
async def cmd_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(f"Сколько тебе лет?")
    await state.set_state(Form.age)

@dp.message(Form.age)
async def cmd_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer(f"В какой группе ты учишься?")
    await state.set_state(Form.grade)

@dp.message(Form.grade)
async def cmd_grade(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)
    data = await state.get_data()
    await message.answer(f"Ваши данные: \n"
                         f"Имя: {data['name']}\n"
                         f"Город: {data['city']}\n"
                         f"Возраст: {data['age']}\n"
                         f"Группа: {data['grade']}")
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO users(name, city, age, grade) VALUES(?, ?, ?, ?)
    """, (data['name'], data['city'], data['age'], data['grade']))
    conn.commit()
    conn.close()

    async with aiohttp.ClientSession() as session:
        async with session.get(WEATHER_URL, params={'q': data['city'], 'appid': API_KEY, 'units': 'metric', 'lang': 'ru'}) as response:
            if response.status == 200:
                w_data = await response.json()
                temp = w_data['main']['temp']
                description = w_data['weather'][0]['description']
                await message.answer(f"Погода в {data['city']} сейчас: {temp}°C, {description}.")
            else:
                await message.answer("Не удалось получить данные о погоде.")
    await state.clear()



async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())