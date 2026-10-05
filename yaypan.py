import logging
import asyncio
import os
import json
import html
import re
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web
import aiohttp_cors
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, BotCommand, MenuButtonCommands, BufferedInputFile,
)

TOKEN = os.environ.get("BOT_TOKEN", "8941827736:AAE_9frRYe2r2FKhwcL9QK8eoOcXtmCf34w")
ADMIN_ID = 8488328091
WEBAPP_URL = "https://yaypanmuzqamoq.netlify.app"
USERS_FILE = "users.json"
DEBTS_FILE = "debts.json"  # Qarzlar bazasi
ORDERS_FILE = "orders.json" # Buyurtmalar bazasi

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Mahsulotlar ro'yxati
PRODUCTS = {
    "oilaviy": {"name": "1. Oilaviy (0.5 kg karobka)", "count_in_box": 12, "price": 15000, "photo": "https://t.me/YAYPAN_muzqaymoq/21?single"},
    "zuxro_shoko": {"name": "2. Zuxro shokolad", "count_in_box": 24, "price": 4000, "photo": "https://t.me/YAYPAN_muzqaymoq/19"},
    "flash": {"name": "3. Flash", "count_in_box": 50, "price": 800, "photo": "https://t.me/YAYPAN_muzqaymoq/16"},
    "moxitto": {"name": "4. Moxitto", "count_in_box": 50, "price": 800, "photo": "https://t.me/YAYPAN_muzqaymoq/13"},
    "sutli": {"name": "5. Sutli", "count_in_box": 54, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/10"},
    "ananas": {"name": "6. Ananas", "count_in_box": 50, "price": 800, "photo": "https://t.me/YAYPAN_muzqaymoq/7"},
    "anor": {"name": "7. Anor", "count_in_box": 50, "price": 800, "photo": "https://t.me/YAYPAN_muzqaymoq/6"},
    "jazzi": {"name": "8. Jazzi", "count_in_box": 50, "price": 2300, "photo": "https://t.me/YAYPAN_muzqaymoq/73"},
    "ferero": {"name": "9. Ferero", "count_in_box": 54, "price": 2200, "photo": "https://t.me/YAYPAN_muzqaymoq/74"},
    "anjan_qulupnay": {"name": "10. Anjan qulupnay", "count_in_box": 20, "price": 5000, "photo": "https://t.me/YAYPAN_muzqaymoq/75"},
    "shokoland": {"name": "11. Shokoland", "count_in_box": 60, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/76"},
    "ayron": {"name": "12. Ayron", "count_in_box": 70, "price": 800, "photo": "https://t.me/YAYPAN_muzqaymoq/56"},
    "pankie": {"name": "13. Pankie", "count_in_box": 24, "price": 6000, "photo": "https://t.me/YAYPAN_muzqaymoq/55"},
    "labubu": {"name": "14. Labubu", "count_in_box": 24, "price": 8000, "photo": "https://t.me/YAYPAN_muzqaymoq/53"},
    "gold": {"name": "15. Gold", "count_in_box": 28, "price": 5000, "photo": "https://t.me/YAYPAN_muzqaymoq/52"},
    "rojok": {"name": "16. Rojok", "count_in_box": 30, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/51"},
    "sendwich": {"name": "17. Sendwich", "count_in_box": 24, "price": 5000, "photo": "https://t.me/YAYPAN_muzqaymoq/50"},
    "gazeta": {"name": "18. Gazeta", "count_in_box": 20, "price": 3500, "photo": "https://t.me/YAYPAN_muzqaymoq/49"},
    "stakan": {"name": "19. Stakan", "count_in_box": 48, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/45"},
    "anjan": {"name": "20. Anjan", "count_in_box": 20, "price": 5000, "photo": "https://t.me/YAYPAN_muzqaymoq/44"},
    "banan": {"name": "21. Banan", "count_in_box": 48, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/34"},
}

class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_phone = State()
    waiting_for_save = State()
    shopping = State()
    waiting_for_custom_count = State()
    waiting_for_partial_pay = State()

user_carts = {}

# ---------- Saqlangan fayllar operatsiyalari ----------
def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if not filepath.endswith("list.json") else []

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"{filepath} yozishda xato: {e}")

saved_users = load_json(USERS_FILE)
debts_db = load_json(DEBTS_FILE)
orders_db = load_json(ORDERS_FILE)
if not isinstance(orders_db, list):
    orders_db = []

def get_saved_user(user_id):
    return saved_users.get(str(user_id))

def set_saved_user(user_id, name, location, phone):
    saved_users[str(user_id)] = {"name": name, "location": location, "phone": phone}
    save_json(USERS_FILE, saved_users)

def delete_saved_user(user_id):
    if str(user_id) in saved_users:
        del saved_users[str(user_id)]
        save_json(USERS_FILE, saved_users)

def add_user_debt(user_id, name, phone, added_amount):
    uid = str(user_id)
    # Agar foydalanuvchi ma'lumotlari bo'sh kelsa, baza orqali tekshirish
    if (not name or name == "-") and uid in saved_users:
        name = saved_users[uid].get("name", "Noma'lum")
    if (not phone or phone == "-") and uid in saved_users:
        phone = saved_users[uid].get("phone", "Noma'lum")

    if uid not in debts_db:
        debts_db[uid] = {"name": name or "Noma'lum", "phone": phone or "Noma'lum", "debt": 0}
    
    debts_db[uid]["debt"] += added_amount
    if name and name != "-":
        debts_db[uid]["name"] = name
    if phone and phone != "-":
        debts_db[uid]["phone"] = phone

    save_json(DEBTS_FILE, debts_db)
    return debts_db[uid]["debt"]

# ---------- Klaviaturalar ----------
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Savatni ko'rish"), KeyboardButton(text="✅ Buyurtmani yakunlash")],
        [KeyboardButton(text="🍦 Mini App", web_app=WebAppInfo(url=WEBAPP_URL)),
         KeyboardButton(text="✏️️ Ma'lumotlarni o'zgartirish")],
    ],
    resize_keyboard=True
)

save_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✅ Ha, saqlansin", callback_data="save_yes"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="save_no"),
    ]
])

def info_text(name, location, phone):
    return (
        f"👤 <b>Ism:</b> {html.escape(str(name))}\n"
        f"📍 <b>Manzil:</b> {html.escape(str(location))}\n"
        f"📞 <b>Telefon:</b> {html.escape(str(phone))}"
    )

def admin_order_keyboard(user_id, total_price):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"deliv_{user_id}")],
        [InlineKeyboardButton(text="💵 Pulni oldim (Qarz yo'q)", callback_data=f"pay_full_{user_id}_{total_price}")],
        [InlineKeyboardButton(text="📝 To'liq qarzga berildi", callback_data=f"pay_debt_{user_id}_{total_price}")],
        [InlineKeyboardButton(text="⚡ Qisman to'landi", callback_data=f"pay_part_{user_id}_{total_price}")],
        [InlineKeyboardButton(text="🖨 Print qilish", callback_data="print_order")],
    ])

def fmt_money(n):
    return f"{int(n):,}".replace(",", " ")

def parse_order_text(text):
    name_match = re.search(r"Ism:\s*(.+)", text)
    phone_match = re.search(r"Telefon:\s*(.+)", text)
    total_match = re.search(r"Umumiy summa:\s*([\d\s]+)", text)
    
    items = []
    for m in re.finditer(r"•\s*(.+?):\s*(\d+)\s*ta\s*[×x]\s*(\d+)\s*=\s*(\d+)", text):
        title = re.sub(r"^\d+\.\s*", "", m.group(1).strip())
        items.append((title, int(m.group(2)), int(m.group(3)), int(m.group(4))))
        
    return {
        "name": name_match.group(1).strip() if name_match else "-",
        "phone": phone_match.group(1).strip() if phone_match else "-",
        "items": items,
        "total": int(re.sub(r"\s", "", total_match.group(1))) if total_match and total_match.group(1).strip() else sum(i[3] for i in items),
    }

# ---------- /start va oqimlar ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    await begin_flow(message, state, user_id)

async def begin_flow(message: types.Message, state: FSMContext, user_id: int):
    user_carts[user_id] = {}
    await state.clear()

    saved = get_saved_user(user_id)
    if saved:
        await state.update_data(name=saved["name"], location=saved["location"], phone=saved["phone"])
        await message.answer(
            f"Assalomu alaykum, <b>{html.escape(saved['name'])}</b>! 🍦\n"
            f"Buyurtma shu ma'lumotlar bilan yuboriladi:\n\n"
            f"{info_text(saved['name'], saved['location'], saved['phone'])}\n\n"
            f"O'zgartirish uchun «✏️ Ma'lumotlarni o'zgartirish» tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard
        )
        await show_catalog(message)
        await state.set_state(OrderState.shopping)
        return

    await message.answer(
        "Assalomu alaykum! Muzqaymoq buyurtma berish botiga xush kelibsiz.\n"
        "Iltimos, Ism va Familiyangizni kiriting:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(OrderState.waiting_for_name)

@dp.message(F.text == "✏️ Ma'lumotlarni o'zgartirish")
async def change_info(message: types.Message, state: FSMContext):
    delete_saved_user(message.from_user.id)
    await state.clear()
    user_carts.setdefault(message.from_user.id, {})
    await message.answer("Yangi Ism va Familiyangizni kiriting:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(OrderState.waiting_for_name)

@dp.message(OrderState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Endi manzilingizni yozib yuboring:")
    await state.set_state(OrderState.waiting_for_location)

@dp.message(OrderState.waiting_for_location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(OrderState.waiting_for_phone)

@dp.message(OrderState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    data = await state.get_data()

    await message.answer("Rahmat! ✅", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(
        f"{info_text(data.get('name'), data.get('location'), phone)}\n\n"
        f"💾 Shu ma'lumotlar saqlansinmi?",
        parse_mode="HTML",
        reply_markup=save_keyboard
    )
    await state.set_state(OrderState.waiting_for_save)

@dp.callback_query(F.data.in_({"save_yes", "save_no"}), OrderState.waiting_for_save)
async def process_save(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback_query.from_user.id

    if callback_query.data == "save_yes":
        set_saved_user(user_id, data.get("name"), data.get("location"), data.get("phone"))

    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer()
    await callback_query.message.answer(
        "Quyidagi mahsulotlar ro'yxatidan tanlang:",
        reply_markup=main_menu_keyboard
    )
    await show_catalog(callback_query.message)
    await state.set_state(OrderState.shopping)

async def show_catalog(message: types.Message):
    for key, prod in PRODUCTS.items():
        box_total = prod['count_in_box'] * prod['price']
        text = (
            f"<b>{prod['name']}</b>\n"
            f"📦 Qutida: {prod['count_in_box']} ta\n"
            f"💰 Dona narxi: {prod['price']} so'm\n"
            f"💵 Jami quti narxi: {box_total} so'm"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📦 Karobkada olish", callback_data=f"box_{key}"),
            InlineKeyboardButton(text="🔢 Dona tanlash", callback_data=f"dona_{key}")
        ]])
        try:
            await message.answer_photo(photo=prod['photo'], caption=text, parse_mode="HTML", reply_markup=keyboard)
        except Exception:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith('box_'), OrderState.shopping)
async def add_box_to_cart(callback_query: types.CallbackQuery):
    product_key = callback_query.data.split('_', 1)[1]
    user_id = callback_query.from_user.id
    user_carts.setdefault(user_id, {})
    add_count = PRODUCTS[product_key]['count_in_box']
    user_carts[user_id][product_key] = user_carts[user_id].get(product_key, 0) + add_count
    await callback_query.answer(f"1 karobka ({add_count} ta) savatga qo'shildi! ✅")

@dp.callback_query(F.data.startswith('dona_'), OrderState.shopping)
async def ask_custom_dona(callback_query: types.CallbackQuery, state: FSMContext):
    product_key = callback_query.data.split('_', 1)[1]
    prod = PRODUCTS[product_key]
    await state.update_data(selected_product=product_key)
    await callback_query.message.answer(
        f"<b>{prod['name']}</b> uchun nechta dona olishni xohlaysiz? Raqamni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_for_custom_count)
    await callback_query.answer()

@dp.message(OrderState.waiting_for_custom_count)
async def process_custom_dona(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Iltimos, faqat raqam kiriting:")
        return
    count = int(message.text)
    data = await state.get_data()
    product_key = data.get('selected_product')
    user_id = message.from_user.id
    user_carts.setdefault(user_id, {})
    user_carts[user_id][product_key] = user_carts[user_id].get(product_key, 0) + count
    await message.answer(f"Savatga {count} dona qo'shildi! ✅", reply_markup=main_menu_keyboard)
    await state.set_state(OrderState.shopping)

@dp.message(F.text == "✅ Buyurtmani yakunlash", OrderState.shopping)
async def finish_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, {})
    if not cart:
        await message.answer("Savatingiz bo'sh! Avval mahsulot tanlang.", reply_markup=main_menu_keyboard)
        return

    data = await state.get_data()
    total_price = 0
    order_details = ""
    items_summary = []
    
    for prod_key, total_items in cart.items():
        if prod_key in PRODUCTS:
            prod = PRODUCTS[prod_key]
            cost = total_items * prod['price']
            total_price += cost
            order_details += f"• {prod['name']}: {total_items} ta × {prod['price']} = {cost} so'm\n"
            items_summary.append(f"{prod['name']} ({total_items}ta)")

    user_name = data.get('name') or (saved_users.get(str(user_id)), {}).get('name', 'Noma'lum')
    user_phone = data.get('phone') or (saved_users.get(str(user_id)), {}).get('phone', '-')

    # Yangi buyurtmani xotiraga saqlash
    new_order = {
        "id": len(orders_db) + 1,
        "clientName": user_name,
        "phone": user_phone,
        "items": ", ".join(items_summary),
        "totalPrice": total_price,
        "status": "Yangi"
    }
    orders_db.append(new_order)
    save_json(ORDERS_FILE, orders_db)

    admin_message = (
        f"📥 <b>Yangi buyurtma keldi! (bot)</b>\n\n"
        f"{info_text(user_name, data.get('location', '-'), user_phone)}\n\n"
        f"🛍 <b>Buyurtma tarkibi:</b>\n{order_details}\n"
        f"💳 <b>Umumiy summa:</b> {total_price} so'm"
    )
    await bot.send_message(ADMIN_ID, admin_message, parse_mode="HTML", reply_markup=admin_order_keyboard(user_id, total_price))

    user_carts[user_id] = {}
    await message.answer(
        "Buyurtmangiz muvaffaqiyatli yuborildi! ✅\n\nYangi buyurtma uchun /start bosing.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()

# ---------- Admin qarz to'lovlari ----------
@dp.callback_query(F.data.startswith('pay_full_'))
async def process_pay_full(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, _ = callback_query.data.split('_')
    try:
        await bot.send_message(int(target_user_id), f"Buyurtmangiz uchun to'lov qabul qilindi. Rahmat! ✅")
    except Exception:
        pass
    await callback_query.message.reply(f"To'lov to'liq qabul qilindi. ✅")
    await callback_query.answer()

@dp.callback_query(F.data.startswith('pay_debt_'))
async def process_pay_debt(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, total_price = callback_query.data.split('_')
    order_info = parse_order_text(callback_query.message.text or "")
    
    total_debt = add_user_debt(target_user_id, order_info['name'], order_info['phone'], int(total_price))
    
    try:
        await bot.send_message(
            int(target_user_id), 
            f"Buyurtmangiz qarzga rasmiylashtirildi.\n"
            f"Ushbu buyurtma: {total_price} so'm.\n"
            f"Umumiy qarzingiz: {total_debt} so'm."
        )
    except Exception:
        pass

    await callback_query.message.reply(f"Mijoz qarziga {total_price} so'm qo'shildi. Umumiy qarzi: {total_debt} so'm.")
    await callback_query.answer()

@dp.callback_query(F.data.startswith('pay_part_'))
async def process_pay_part(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, total_price = callback_query.data.split('_')
    await state.update_data(target_user_id=target_user_id, total_price=int(total_price), msg_text=callback_query.message.text)
    await callback_query.message.reply("Olingan summani kiriting (masalan 20000):")
    await state.set_state(OrderState.waiting_for_partial_pay)
    await callback_query.answer()

@dp.message(OrderState.waiting_for_partial_pay)
async def process_partial_pay_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID or not message.text or not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting:")
        return

    paid = int(message.text)
    data = await state.get_data()
    target_user_id = data['target_user_id']
    total_price = data['total_price']
    
    debt_to_add = total_price - paid
    order_info = parse_order_text(data.get('msg_text', ''))
    
    if debt_to_add > 0:
        total_debt = add_user_debt(target_user_id, order_info['name'], order_info['phone'], debt_to_add)
        msg_text = f"Qolgan {debt_to_add} so'm qarzga yozildi. Umumiy qarzi: {total_debt} so'm."
    else:
        msg_text = "To'lov to'liq qoplandi, qarz yozilmadi."

    await message.answer(msg_text)
    await state.clear()

# ---------- API endpoints (Mobil ilova uchun) ----------
async def get_orders_api(request):
    return web.json_response(orders_db)

async def get_debts_api(request):
    return web.json_response(debts_db)

async def handle_ping(request):
    return web.Response(text="Bot va API ishlamoqda!")

async def setup_bot_menu():
    await bot.set_my_commands([
        BotCommand(command="start", description="🍦 Buyurtma berishni boshlash"),
    ])
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

async def main():
    app = web.Application()
    
    # HTTP marshrutlari
    app.router.add_get("/", handle_ping)
    app.router.add_get("/api/orders", get_orders_api)
    app.router.add_get("/api/debts", get_debts_api)

    # CORS sozlashi (Mobil ilova va Brauzerlar uchun)
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await setup_bot_menu()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
