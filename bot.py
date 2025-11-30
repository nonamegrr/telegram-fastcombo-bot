import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.filters.text import Text  # <-- исправлено

# Получаем токен и ID админа из переменных окружения Railway
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not TOKEN or not ADMIN_ID:
    raise ValueError("TOKEN или ADMIN_ID не установлены!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для хранения данных пользователей
users = {}

# Функции для клавиатур
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🧾 Инструкция"),
        KeyboardButton("🛒 Заказать"),
        KeyboardButton("👤 ЛК"),
        KeyboardButton("❓ Задать вопрос")
    )
    return kb

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

# Обработчик /start
@dp.message(CommandStart())
async def start(message: types.Message):
    uid = message.from_user.id
    if uid not in users:
        users[uid] = {"i": message.from_user.first_name, "z1":" ","z2":" ","z3":" ","state":None,"n":0}
    await message.answer(
        "Привет! С чем тебе помочь?\nНе забудь прочитать инструкцию перед началом использования бота!",
        reply_markup=main_menu_kb()
    )

# Обработка кнопок меню
@dp.message(Text(text="🧾 Инструкция"))
async def instruction(message: types.Message):
    text = """
📌 Инструкция по использованию бота Fast Combo Clothes 📌

Добро пожаловать! 🛍✨
1️⃣ Для заказа нажмите "Заказать"
2️⃣ Администратор проверит наличие и свяжется с вами
3️⃣ Оплатите и получите заказ

🔙 В меню
"""
    await message.answer(text, reply_markup=back_menu_kb())

@dp.message(Text(text="🔙 В меню"))
async def back_menu(message: types.Message):
    await start(message)

@dp.message(Text(text="🛒 Заказать"))
async def order(message: types.Message):
    uid = message.from_user.id
    user = users[uid]

    # Проверяем, куда сохранить заказ
    if user["z1"] == " ":
        user["state"] = "z1"
    elif user["z2"] == " ":
        user["state"] = "z2"
    elif user["z3"] == " ":
        user["state"] = "z3"
    else:
        await message.answer(
            "Вы достигли максимального количества заказов.\nЕсли один из заказов уже доставлен, выберите «Получил заказ»",
            reply_markup=order_menu_kb()
        )
        return

    await message.answer(
        "Введите номер сета и размер. Если вы сами собрали образ, напишите номера каждой вещи."
    )

# Получение текста заказа
@dp.message()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    if uid not in users:
        return
    user = users[uid]

    # Если пользователь находится в процессе заказа
    if user["state"] in ["z1", "z2", "z3"]:
        user[user["state"]] = message.text
        order_num = user["state"][-1]  # 'z1' → '1'
        await bot.send_message(ADMIN_ID, f"Новый заказ от {user['i']}:\n№{order_num} {message.text}")
        await message.answer(
            f"Ваш заказ:\n№{order_num} {message.text}\n\n💌 Ожидайте! В ближайшее время вам напишет админ.",
            reply_markup=main_menu_kb()
        )
        user["state"] = None
        return

    # Получение номера полученного заказа
    if user["state"] == "received":
        if message.text in ["1","2","3"]:
            z_key = f"z{message.text}"
            user[z_key] = " "
            await message.answer("💌 Спасибо за покупку!", reply_markup=main_menu_kb())
            user["state"] = None
        else:
            await message.answer("Выберете цифру от 1 до 3")
        return

    # Задать вопрос
    if user.get("state") == "ask":
        await bot.send_message(ADMIN_ID, f"Вопрос от {user['i']}:\n{message.text}")
        await message.answer("💌 Мы передали ваш вопрос, ожидайте ответ", reply_markup=main_menu_kb())
        user["state"] = None

# Личный кабинет
@dp.message(Text(text="👤 ЛК"))
async def my_orders(message: types.Message):
    uid = message.from_user.id
    user = users[uid]
    text = f"""
💎 ЛИЧНЫЙ КАБИНЕТ 💎
Имя: {user['i']}

📦 Мои заказы:
№1 {user['z1']}
№2 {user['z2']}
№3 {user['z3']}
"""
    await message.answer(text, reply_markup=order_menu_kb())

# Кнопка "Получил заказ"
@dp.message(Text(text="Получил заказ"))
async def received_order(message: types.Message):
    uid = message.from_user.id
    users[uid]["state"] = "received"
    await message.answer("Напишите номер полученного заказа (1-3)")

# Кнопка "Задать вопрос"
@dp.message(Text(text="❓ Задать вопрос"))
async def ask_question(message: types.Message):
    uid = message.from_user.id
    users[uid]["state"] = "ask"
    await message.answer("Задайте ваш вопрос")

# Запуск бота
async def main():
    await remove_webhook()  # удаляем старый вебхук
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
