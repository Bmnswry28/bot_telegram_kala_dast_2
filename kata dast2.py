from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
#کد های وصل شدن به بات
api_id = '#'
api_hash = '#'
app = Client("my_bot", api_id, api_hash)

# وصل شدن به دیتابیس
conn = sqlite3.connect('items.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS items
             (id INTEGER PRIMARY KEY AUTOINCREMENT, photo BLOB, description TEXT, category TEXT)''')

# دکمه های اول
main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton('افزودن آیتم')], [KeyboardButton('جستجوی آیتم‌ها')]],
    resize_keyboard=True
)
#دکمه های دسته بندی
category_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton('لوازم دیجیتال')], [KeyboardButton('لوازم خانگی')], [KeyboardButton('لوازم ورزشی')]],
    resize_keyboard=True
)

# ساخت دیکشنیری برای ذخیره برای سرعت لود بیشتر
storage = {}

# دستور استارت
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("سلام! به ربات فروش آیتم خوش آمدید. لطفا از دکمه‌های زیر استفاده کنید.", reply_markup=main_keyboard)

# بخش اضافه کردن ایتم
@app.on_message(filters.regex("^افزودن آیتم$"))
async def add_item(client, message):
    storage[message.chat.id] = {"adding_item": True}
    await message.reply("لطفا دسته‌بندی آیتم را انتخاب کنید:", reply_markup=category_keyboard)

@app.on_message(filters.regex("^(لوازم دیجیتال|لوازم خانگی|لوازم ورزشی)$"))
async def handle_category(client, message):
    category = message.text
    storage[message.chat.id]["category"] = category
    await message.reply("لطفا عکس و توضیحات آیتم را ارسال کنید.")

@app.on_message(filters.photo)
async def save_item(client, message):
    chat_data = storage.get(message.chat.id)
    if chat_data and chat_data.get("adding_item"):
        category = chat_data.get("category")
        photo = message.photo.file_id
        description = message.caption
        c.execute("INSERT INTO items (photo, description, category) VALUES (?, ?, ?)", (photo, description, category))
        conn.commit()
        await message.reply(f"آیتم در دسته‌بندی {category} با موفقیت ذخیره شد!", reply_markup=main_keyboard)
        storage[message.chat.id]["adding_item"] = False
    else:
        await message.reply("لطفا ابتدا دسته‌بندی آیتم را انتخاب کنید.")
@app.on_message(filters.regex("^جستجوی آیتم‌ها$"))
async def search_items(client, message):
    category_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("لوازم دیجیتال", callback_data="لوازم دیجیتال")],
        [InlineKeyboardButton("لوازم خانگی", callback_data="لوازم خانگی")],
        [InlineKeyboardButton("لوازم ورزشی", callback_data="لوازم ورزشی")],
        [InlineKeyboardButton("همه", callback_data="all")]
    ])
    await message.reply("لطفا دسته‌بندی مورد نظر را انتخاب کنید:", reply_markup=category_keyboard)

@app.on_callback_query()
async def display_items(client, callback_query):
    category = callback_query.data
    if category == "all":
        c.execute("SELECT * FROM items")
    else:
        c.execute(f"SELECT * FROM items WHERE category = ?", (category,))
    items = c.fetchall()

    if not items:
        await callback_query.answer("هیچ ایتمی پیدا نشد", show_alert=True)
    else:
        for item in items:
            photo_id = item[1]
            description = item[2]
            category = item[3]
            await client.send_photo(chat_id=callback_query.message.chat.id, photo=photo_id, caption=f"دسته‌بندی: {category}\n{description}")
        await callback_query.answer("آیتم‌ها نمایش داده شد.", show_alert=True)

# استارت کلاینت
app.run()