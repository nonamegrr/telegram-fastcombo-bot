import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Получаем токен и ID администратора из переменных окружения
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Проверяем, что переменные установлены
if not TOKEN or not ADMIN_ID:
    raise ValueError("Переменные окружения TOKEN или ADMIN_ID не установлены!")

bot = Bot(TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей (в памяти)
users = {}

# Функция для главного меню
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🧾 Инструкция"),
        KeyboardButton("🛒 Заказать"),
        KeyboardButton("👤 ЛК"),
        KeyboardButton("❓ Задать вопрос")
    )
    return kb

# Кнопка "В меню"
def back_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 В меню"))
    return kb
def order_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Получил заказ"), KeyboardButton("🔙 В меню"))
    return kb

# Удаляем вебхук перед запуском polling
async def remove_webhook():
    await bot.delete_webhook()
    print("Webhook удалён!")
    
# Команда /start
@dp.message(CommandStart())
async def start(message: types.Message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {
            "i": message.from_user.first_name,
            "z1": " ",
            "z2": " ",
            "z3": " ",
            "state": None,
            "n": 0
        }
    await message.answer(
        "Привет! С чем тебе помочь?\nНе забудь прочитать инструкцию перед началом использования бота!",
        reply_markup=main_menu_kb()
    )

# Инструкция
@dp.message(lambda message: message.text == "🧾 Инструкция")
async def instruction(message: types.Message):
    text = "📌 Инструкция по использованию бота Fast Combo Clothes 📌\n(тут текст инструкции)"
    await message.answer(text, reply_markup=back_menu_kb())

# В меню
@dp.message(lambda message: message.text == "🔙 В меню")
async def back_to_menu(message: types.Message):
    await start(message)

# Обработка заказов
@dp.message(lambda message: message.text == "🛒 Заказать")
async def order(message: types.Message):
    uid = message.from_user.id
    u = users[uid]
    if u["z1"] == " ":
        u["state"] = "order_z1"
    elif u["z2"] == " ":
        u["state"] = "order_z2"
    elif u["z3"] == " ":
        u["state"] = "order_z3"
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("📦 Получил заказ"), KeyboardButton("🔙 В меню"))
        await message.answer("Вы достигли максимального числа заказов.", reply_markup=kb)
        u["state"] = "remove_order"
        return
    await message.answer("Введите номер сета и размер. Если собрали образ сами — напишите номера вещей.")

# Личный кабинет
@dp.message(lambda message: message.text == "👤 ЛК")
async def lk(message: types.Message):
    uid = message.from_user.id
    u = users[uid]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Получил заказ"), KeyboardButton("🔙 В меню"))
    text = f"💎 ЛИЧНЫЙ КАБИНЕТ 💎\nИмя: {u['i']}\n\n📦 Мои заказы:\n№1 {u['z1']}\n№2 {u['z2']}\n№3 {u['z3']}"
    await message.answer(text, reply_markup=kb)

# Задать вопрос администратору
@dp.message(lambda message: message.text == "❓ Задать вопрос")
async def ask(message: types.Message):
    uid = message.from_user.id
    users[uid]["state"] = "ask_admin"
    await message.answer("Напишите ваш вопрос:")

# Получил заказ
@dp.message(lambda message: message.text == "📦 Получил заказ")
async def got_order(message: types.Message):
    uid = message.from_user.id
    users[uid]["state"] = "remove_order_number"
    await message.answer("Напишите номер полученного заказа (1–3):")

# Обработка текста от пользователя
@dp.message()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    if uid not in users:
        await start(message)
        return
    u = users[uid]
    state = u["state"]

    if state == "order_z1":
        u["z1"] = message.text
        u["state"] = None
        await bot.send_message(ADMIN_ID, f"📦 Новый заказ от {u['i']}:\n{u['z1']}")
        await message.answer(f"Ваш заказ №1:\n{u['z1']}\n\n💌 Ожидайте ответа администратора!", reply_markup=main_menu_kb())

    elif state == "order_z2":
        u["z2"] = message.text
        u["state"] = None
        await bot.send_message(ADMIN_ID, f"📦 Новый заказ от {u['i']}:\n{u['z2']}")
        await message.answer(f"Ваш заказ №2:\n{u['z2']}", reply_markup=main_menu_kb())

    elif state == "order_z3":
        u["z3"] = message.text
        u["state"] = None
        await bot.send_message(ADMIN_ID, f"📦 Новый заказ от {u['i']}:\n{u['z3']}")
        await message.answer(f"Ваш заказ №3:\n{u['z3']}", reply_markup=main_menu_kb())

    elif state == "remove_order_number":
        if message.text in ["1","2","3"]:
            idx = int(message.text)
            u[f"z{idx}"] = " "
            u["state"] = None
            await message.answer("💌 Спасибо за покупку!", reply_markup=main_menu_kb())
        else:
            await message.answer("Введите число от 1 до 3.")

    elif state == "ask_admin":
        await bot.send_message(ADMIN_ID, f"❓ Вопрос от {u['i']}:\n{message.text}")
        u["state"] = None
        await message.answer("💌 Мы передали ваш вопрос администратору!", reply_markup=back_menu_kb())

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
