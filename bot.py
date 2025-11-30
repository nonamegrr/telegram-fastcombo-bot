import asyncio
import os 
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(TOKEN)
dp = Dispatcher()

users = {}  # user_id: {"i": name, "z1": " ", "z2": " ", "z3": " ", "state": None, "n":0}


def menu_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="Инструкция", callback_data="instr")
    kb.button(text="Заказать", callback_data="order")
    kb.button(text="ЛК", callback_data="lk")
    kb.button(text="Задать вопрос", callback_data="ask")
    kb.adjust(1)
    return kb.as_markup()


def back_to_menu_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="В меню", callback_data="menu")
    return kb.as_markup()


def got_order_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="Получил заказ", callback_data="got_order")
    kb.button(text="В меню", callback_data="menu")
    kb.adjust(1)
    return kb.as_markup()


def init_user(user_id, name):
    users[user_id] = {
        "i": name,
        "z1": " ",
        "z2": " ",
        "z3": " ",
        "state": None,
        "n": 0
    }


def orders_text(u):
    return (f"№1 {u['z1']}
"
            f"№2 {u['z2']}
"
            f"№3 {u['z3']}")


@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        init_user(user_id, message.from_user.first_name)

    await message.answer(
        "Привет! С чем тебе помочь?\n"
        "Не забудь прочитать инструкцию перед началом использования бота!",
        reply_markup=menu_kb()
    )


@dp.callback_query(F.data == "instr")
async def instruction(call: types.CallbackQuery):
    text = """📌 Инструкция по использованию бота Fast Combo Clothes📌  

Добро пожаловать в наш бот! 🛍✨  
Здесь вы можете легко оформить заказ, задать вопрос администратору или проверить статус покупки.

🔹 Главное меню  
При запуске бота вы увидите три основные кнопки:  
✅ «Заказать» – Оформление заказа.  
✅ «Задать вопрос» – Связь с администратором.  
✅ «Личный кабинет (ЛК)» – Ваши данные и заказы.

📦 Как сделать заказ?  
1. Нажмите кнопку «Заказать»  
2. Укажите номер комплекта или вещей и размер.

📌 Пример оформления:  
"1M"  
"17XL"  
"4S 41XS"

❓ Как задать вопрос?  
Нажмите «Задать вопрос» и напишите ваш запрос.

👤 Личный кабинет  
Здесь можно посмотреть историю заказов.

🔙 Вернуться в меню — кнопка «В меню».
"""
    await call.message.edit_text(text, reply_markup=back_to_menu_kb())


@dp.callback_query(F.data == "menu")
async def to_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "Привет! С чем тебе помочь?\n"
        "Не забудь прочитать инструкцию перед началом использования бота!",
        reply_markup=menu_kb()
    )


@dp.callback_query(F.data == "order")
async def start_order(call: types.CallbackQuery):
    u = users[call.from_user.id]

    if u["z1"] == " ":
        u["state"] = "wait_z1"
    elif u["z2"] == " ":
        u["state"] = "wait_z2"
    elif u["z3"] == " ":
        u["state"] = "wait_z3"
    else:
        await call.message.edit_text(
            "Вы достигли максимального количества заказов.\n"
            "Если один из заказов уже доставлен, выберите «Получил заказ».",
            reply_markup=got_order_kb()
        )
        return

    await call.message.edit_text(
        "Введите номер сета и размер. Если сами собрали образ — напишите номера всех вещей."
    )


@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        return

    u = users[user_id]

    if u["state"] == "ask":
        await bot.send_message(ADMIN_ID, f"❓ Вопрос от @{message.from_user.username}: {message.text}")
        u["state"] = None
        await message.answer("💌Мы передали ваш вопрос, ожидайте ответ.", reply_markup=back_to_menu_kb())
        return

    state = u["state"]
    if state in ["wait_z1", "wait_z2", "wait_z3"]:
        slot = state[-2:]
        u[slot] = message.text
        u["state"] = None

        await bot.send_message(ADMIN_ID, f"🛍 Новый заказ от @{message.from_user.username}:\n{message.text}")

        num = slot[-1]
        await message.answer(
            f"Ваш заказ:\n№{num} {message.text}\n\n"
            "💌Ожидайте! В ближайшее время вам напишет админ.",
            reply_markup=back_to_menu_kb()
        )
        return

    if u["state"] == "got_order":
        if message.text not in ["1", "2", "3"]:
            await message.answer("Выберите цифру от 1 до 3:")
            return

        n = int(message.text)
        u[f"z{n}"] = " "
        u["state"] = None

        await message.answer("💌Спасибо за покупку!", reply_markup=back_to_menu_kb())
        return


@dp.callback_query(F.data == "got_order")
async def got_order(call: types.CallbackQuery):
    u = users[call.from_user.id]
    u["state"] = "got_order"
    await call.message.edit_text("Напишите номер полученного заказа (1–3):")


@dp.callback_query(F.data == "lk")
async def lk(call: types.CallbackQuery):
    u = users[call.from_user.id]
    text = f"""💎ЛИЧНЫЙ КАБИНЕТ💎
Имя: {u['i']}

📦Мои заказы:
{orders_text(u)}
"""
    await call.message.edit_text(text, reply_markup=got_order_kb())


@dp.callback_query(F.data == "ask")
async def ask(call: types.CallbackQuery):
    u = users[call.from_user.id]
    u["state"] = "ask"
    await call.message.edit_text("Задайте нужный вопрос:")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
