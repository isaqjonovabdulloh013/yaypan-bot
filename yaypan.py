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
DEBTS_FILE = "debts.json"    # База долгов
ORDERS_FILE = "orders.json"  # База заказов
CHANNEL = "@YAYPAN_muzqaymoq"
CHANNEL_URL = "https://t.me/YAYPAN_muzqaymoq"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Список продуктов
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
    admin_waiting_for_debt_amount = State()

user_carts = {}

# ---------- Operations with JSON files ----------
def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return [] if filepath.endswith("orders.json") else {}

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error writing to {filepath}: {e}")

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

def add_user_debt(user_id, name, phone, added_amount, items_text=""):
    uid = str(user_id)
    if (not name or name == "-") and uid in saved_users:
        name = saved_users[uid].get("name", "Noma'lum")
    if (not phone or phone == "-") and uid in saved_users:
        phone = saved_users[uid].get("phone", "Noma'lum")

    if uid not in debts_db:
        debts_db[uid] = {
            "name": name or "Noma'lum", 
            "phone": phone or "Noma'lum", 
            "debt": 0,
            "history": []
        }
    
    if "history" not in debts_db[uid]:
        debts_db[uid]["history"] = []

    debts_db[uid]["debt"] += added_amount
    if name and name != "-":
        debts_db[uid]["name"] = name
    if phone and phone != "-":
        debts_db[uid]["phone"] = phone

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    debts_db[uid]["history"].append({
        "date": now_str,
        "amount": added_amount,
        "items": items_text or ("Qarz qo'shildi" if added_amount > 0 else "Qarz to'landi")
    })

    save_json(DEBTS_FILE, debts_db)
    return debts_db[uid]["debt"]

# ---------- Keyboards ----------
def get_main_keyboard(user_id):
    kb = [
        [KeyboardButton(text="🛒 Savatni ko'rish"), KeyboardButton(text="✅ Buyurtmani yakunlash")],
        [KeyboardButton(text="📜 Mening qarzlarim"), KeyboardButton(text="🍦 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton(text="✏️ Ma'lumotlarni o'zgartirish")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="👥 Mijozlar va Qarzlar")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

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
    items_raw = []
    for m in re.finditer(r"•\s*(.+?):\s*(\d+)\s*ta\s*[×x]\s*(\d+)\s*=\s*(\d+)", text):
        title = re.sub(r"^\d+\.\s*", "", m.group(1).strip())
        items.append((title, int(m.group(2)), int(m.group(3)), int(m.group(4))))
        items_raw.append(f"{title} ({m.group(2)}ta)")
        
    return {
        "name": name_match.group(1).strip() if name_match else "-",
        "phone": phone_match.group(1).strip() if phone_match else "-",
        "items": items,
        "items_str": ", ".join(items_raw),
        "total": int(re.sub(r"\s", "", total_match.group(1))) if total_match and total_match.group(1).strip() else sum(i[3] for i in items),
    }

# ---------- Receipt Generation ----------
def _load_font(size, bold=False):
    names = (
        ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"] if bold
        else ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"]
    )
    dirs = ["", "/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/",
            "/usr/share/fonts/truetype/liberation/", "/usr/share/fonts/liberation/",
            "C:/Windows/Fonts/"]
    for d in dirs:
        for n in names:
            try:
                return ImageFont.truetype(d + n, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def build_receipt_image(order):
    W, M = 800, 40
    f_title, f_b, f_n, f_s = _load_font(44, True), _load_font(30, True), _load_font(28), _load_font(24)
    x_qty, x_price, x_sum = 420, 580, W - M

    rows = order["items"]
    H = 330 + len(rows) * 52 + 140
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    def center(text, y, font):
        w = d.textlength(text, font=font)
        d.text(((W - w) / 2, y), text, font=font, fill="black")

    def right(text, xr, y, font):
        w = d.textlength(text, font=font)
        d.text((xr - w, y), text, font=font, fill="black")

    def fit(text, font, maxw):
        while d.textlength(text, font=font) > maxw and len(text) > 1:
            text = text[:-2] + "…"
        return text

    y = 25
    center("YAYPAN MUZQAYMOQ", y, f_title); y += 62
    center(datetime.now().strftime("%d.%m.%Y %H:%M"), y, f_s); y += 50
    d.text((M, y), "Ism:", font=f_b, fill="black")
    d.text((M + 90, y), fit(order["name"], f_n, W - 2 * M - 90), font=f_n, fill="black"); y += 46
    d.text((M, y), "Telefon:", font=f_b, fill="black")
    d.text((M + 150, y), fit(order["phone"], f_n, W - 2 * M - 150), font=f_n, fill="black"); y += 60

    d.line((M, y, W - M, y), fill="black", width=3); y += 10
    d.text((M, y), "Mahsulot", font=f_b, fill="black")
    right("Soni", x_qty, y, f_b)
    right("Narxi", x_price, y, f_b)
    right("Summa", x_sum, y, f_b); y += 48
    d.line((M, y, W - M, y), fill="black", width=3); y += 10

    for title, qty, price, cost in rows:
        d.text((M, y), fit(title, f_n, 285), font=f_n, fill="black")
        right(str(qty), x_qty, y, f_n)
        right(fmt_money(price), x_price, y, f_n)
        right(fmt_money(cost), x_sum, y, f_n)
        y += 46
        d.line((M, y, W - M, y), fill="gray", width=1); y += 6

    y += 14
    d.line((M, y, W - M, y), fill="black", width=3); y += 16
    d.text((M, y), "JAMI:", font=f_title, fill="black")
    right(f"{fmt_money(order['total'])} so'm", W - M, y, f_title)

    buf = io.BytesIO()
    img.crop((0, 0, W, y + 80)).save(buf, format="PNG")
    return buf.getvalue()

@dp.callback_query(F.data == "print_order")
async def print_order(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("Bu tugma faqat admin uchun!", show_alert=True)
        return
    order = parse_order_text(callback_query.message.text or callback_query.message.caption or "")
    if not order["items"]:
        await callback_query.answer("Buyurtma tarkibini o'qib bo'lmadi.", show_alert=True)
        return
    png = build_receipt_image(order)
    await callback_query.message.answer_photo(BufferedInputFile(png, filename="chek.png"))
    await callback_query.answer("Chek yuborildi ✅")

# ---------- Subscription ----------
verified_users = set()
_admin_warned = False

async def is_subscribed(user_id):
    global _admin_warned
    try:
        m = await bot.get_chat_member(CHANNEL, user_id)
        return m.status in ("member", "administrator", "creator") or (
            m.status == "restricted" and getattr(m, "is_member", False)
        )
    except Exception as e:
        logging.warning(f"Obunani tekshirib bo'lmadi: {e}")
        if not _admin_warned:
            _admin_warned = True
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"⚠️ Obunani tekshirib bo'lmadi. Botni {CHANNEL} kanaliga ADMIN qilib qo'shing.\nXato: {e}"
                )
            except Exception:
                pass
        return True

def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")],
    ])

async def send_subscribe_prompt(message: types.Message):
    await send_sticker_safe(message.chat.id, "📢", "👋", "🙏")
    await message.answer(
        "Assalomu alaykum! 🍦\n\n"
        f"Botdan foydalanish uchun avval rasmiy kanalimizga obuna bo'ling:\n👉 {CHANNEL}\n\n"
        "Obuna bo'lgach, «✅ Obuna bo'ldim» tugmasini bosing.",
        reply_markup=subscribe_keyboard()
    )

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is None or user.id == ADMIN_ID or user.id in verified_users:
            return await handler(event, data)
        if isinstance(event, types.Message) and (event.text or "").startswith("/start"):
            return await handler(event, data)
        if isinstance(event, types.CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)
        if await is_subscribed(user.id):
            verified_users.add(user.id)
            return await handler(event, data)
        if isinstance(event, types.CallbackQuery):
            await event.answer("Avval kanalga obuna bo'ling!", show_alert=True)
            if event.message:
                await send_subscribe_prompt(event.message)
        elif isinstance(event, types.Message):
            await send_subscribe_prompt(event)
        return

dp.message.middleware(SubscriptionMiddleware())
dp.callback_query.middleware(SubscriptionMiddleware())

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if not await is_subscribed(user_id):
        await callback_query.answer("❌ Siz hali obuna bo'lmagansiz. Avval kanalga obuna bo'ling.", show_alert=True)
        return
    verified_users.add(user_id)
    await callback_query.answer("✅ Obuna tasdiqlandi!")
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await send_sticker_safe(callback_query.message.chat.id, "🎉", "🥳", "👏")
    await begin_flow(callback_query.message, state, user_id)

# ---------- Animated Stickers ----------
STICKER_SETS = ["AnimatedEmojies", "animatedemoji", "HotCherry", "TheFoods", "BananaFun"]
_sticker_cache = {}

def _norm(e):
    return (e or "").replace("\ufe0f", "")

async def pick_sticker(*emojis):
    for set_name in STICKER_SETS:
        if set_name not in _sticker_cache:
            try:
                st = await bot.get_sticker_set(set_name)
                _sticker_cache[set_name] = [(_norm(x.emoji), x.file_id) for x in st.stickers]
            except Exception:
                _sticker_cache[set_name] = []
        for e in emojis:
            for emo, fid in _sticker_cache[set_name]:
                if emo == _norm(e):
                    return fid
    return None

async def send_sticker_safe(chat_id, *emojis):
    try:
        fid = await pick_sticker(*emojis)
        if fid:
            await bot.send_sticker(chat_id, fid)
    except Exception as e:
        logging.info(f"Stiker yuborilmadi: {e}")

# ---------- Start and Flow ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    if user_id != ADMIN_ID and user_id not in verified_users:
        if not await is_subscribed(user_id):
            await message.answer("👋", reply_markup=types.ReplyKeyboardRemove())
            await send_subscribe_prompt(message)
            return
        verified_users.add(user_id)
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
            reply_markup=get_main_keyboard(user_id)
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
    await message.answer("Endi manzilingizni (qaysi joyda ekaningizni) yozib yuboring:")
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
        f"💾 Shu ma'lumotlar saqlansinmi?\n"
        f"Saqlansa, keyingi safar qayta so'ralmaydi va buyurtmalar doim shu nomdan boradi.",
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
        result = "💾 Ma'lumotlaringiz saqlandi!"
    else:
        result = "Ma'lumotlar saqlanmadi (faqat shu buyurtma uchun ishlatiladi)."

    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer()
    await callback_query.message.answer(
        f"{result}\n\nQuyidagi mahsulotlar ro'yxatidan tanlang:",
        reply_markup=get_main_keyboard(user_id)
    )
    await show_catalog(callback_query.message)
    await state.set_state(OrderState.shopping)

# ---------- FOYDALANUVCHI QARZ TARIHI ----------
@dp.message(F.text == "📜 Mening qarzlarim")
async def show_user_debt_history(message: types.Message):
    user_id = str(message.from_user.id)
    user_debt_info = debts_db.get(user_id)

    if not user_debt_info:
        await message.answer("Sizda hech qanday qarz yoki operatsiyalar tarixi yo'q.\n\n💰 **Umumiy qarzingiz:** 0 so'm", parse_mode="Markdown")
        return

    history = user_debt_info.get("history", [])
    total_debt = user_debt_info.get("debt", 0)

    if not history:
        await message.answer(f"Sizda operatsiyalar tarixi yo'q.\n\n💰 **Umumiy qarzingiz:** {fmt_money(total_debt)} so'm", parse_mode="Markdown")
        return

    text = "📋 **Sizning qarz va xaridlaringiz tarixi:**\n\n"
    for item in reversed(history):
        dt = item.get("date", "-")
        amt = item.get("amount", 0)
        prod = item.get("items", "Mahsulot")
        
        if amt > 0:
            text += f"📅 {dt}\n🍦 **Mahsulot:** {prod}\n➕ **Qarz:** {fmt_money(amt)} so'm\n──────────────────\n"
        else:
            text += f"📅 {dt}\n💳 **Qarz to'lovi:** {fmt_money(abs(amt))} so'm\n──────────────────\n"

    text += f"\n💰 **Jami qarzingiz:** {fmt_money(total_debt)} so'm"
    await message.answer(text, parse_mode="Markdown")

# ---------- ADMIN PANEL: MIJOZLAR RO'YXATI VA QARZNI BOSHQARISH ----------
@dp.message(F.text == "👥 Mijozlar va Qarzlar")
async def admin_users_list(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not debts_db and not saved_users:
        await message.answer("Hozircha mijozlar ro'yxati bo'sh.")
        return

    inline_kb = []
    # Barcha foydalanuvchilarni jamlash
    all_uids = set(list(debts_db.keys()) + list(saved_users.keys()))

    for uid in all_uids:
        u_info = debts_db.get(uid) or saved_users.get(uid) or {}
        name = u_info.get("name", "Noma'lum")
        debt = debts_db.get(uid, {}).get("debt", 0)
        inline_kb.append([InlineKeyboardButton(
            text=f"👤 {name} | Qarz: {fmt_money(debt)} so'm", 
            callback_data=f"adm_user:{uid}"
        )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer("👥 **Mijozlar va ularning qarzlari ro'yxati:**\nBoshqarish uchun mijozni tanlang:", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("adm_user:"))
async def process_adm_user_select(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    uid = callback.data.split(":")[1]
    u_info = debts_db.get(uid) or saved_users.get(uid) or {}
    name = u_info.get("name", "Noma'lum")
    phone = u_info.get("phone", "-")
    debt = debts_db.get(uid, {}).get("debt", 0)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Qarz qo'shish", callback_data=f"adm_add:{uid}"),
            InlineKeyboardButton(text="➖ Qarzni kamaytirish", callback_data=f"adm_sub:{uid}")
        ],
        [InlineKeyboardButton(text="📜 Qarzlar tarixini ko'rish", callback_data=f"adm_hist:{uid}")]
    ])

    await callback.message.edit_text(
        f"👤 **Mijoz:** {name}\n"
        f"📞 **Telefon:** {phone}\n"
        f"🆔 **ID:** `{uid}`\n"
        f"💰 **Hozirgi qarzi:** {fmt_money(debt)} so'm\n\n"
        f"Amalni tanlang:",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("adm_hist:"))
async def view_user_hist_admin(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    uid = callback.data.split(":")[1]
    u_info = debts_db.get(uid, {})
    history = u_info.get("history", [])
    debt = u_info.get("debt", 0)

    if not history:
        await callback.answer("Ushbu mijozda tarix yo'q.", show_alert=True)
        return

    text = f"📋 **Mijoz ({u_info.get('name', 'Noma'lum')}) qarz tarixi:**\n\n"
    for item in reversed(history):
        text += f"📅 {item.get('date')}\n📝 {item.get('items')}\n💵 Summa: {fmt_money(item.get('amount'))} so'm\n──────────────────\n"

    text += f"\n💰 **Jami qarz:** {fmt_money(debt)} so'm"
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith(("adm_add:", "adm_sub:")))
async def prompt_adm_debt_amount(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    action, uid = callback.data.split(":")
    await state.update_data(target_uid=uid, action=action)
    await state.set_state(OrderState.admin_waiting_for_debt_amount)

    action_title = "qo'shiladigan" if action == "adm_add" else "kamaytiriladigan (ayriladigan)"
    await callback.message.answer(f"Summani kiriting ({action_title}):\n*Masalan:* 25000", parse_mode="Markdown")
    await callback.answer()

@dp.message(OrderState.admin_waiting_for_debt_amount)
async def process_adm_debt_change(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    amount = int(message.text)
    data = await state.get_data()
    uid = data["target_uid"]
    action = data["action"]
    await state.clear()

    u_info = debts_db.get(uid) or saved_users.get(uid) or {}
    name = u_info.get("name", "Noma'lum")
    phone = u_info.get("phone", "-")

    if action == "adm_add":
        added_val = amount
        item_note = "Admin tomonidan qarz qo'shildi"
    else:
        added_val = -amount
        item_note = "Qarz to'landi (Admin)"

    new_total = add_user_debt(uid, name, phone, added_val, item_note)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    await message.answer(f"✅ Qarz yangilandi!\nMijoz: {name}\nYangi umumiy qarz: {fmt_money(new_total)} so'm")

    # Mijozga avtomati xabar yuborish
    try:
        if added_val > 0:
            msg = f"🔔 **Qarzingizga yangi summa qo'shildi:**\n📅 Vaqt: {now_str}\n➕ Summa: {fmt_money(amount)} so'm\n\n💰 **Umumiy qarzingiz:** {fmt_money(new_total)} so'm"
        else:
            msg = f"✅ **Qarz to'lovingiz qabul qilindi:**\n📅 Vaqt: {now_str}\n➖ Ayrildi: {fmt_money(amount)} so'm\n\n💰 **Qolgan qarzingiz:** {fmt_money(new_total)} so'm"
        
        await bot.send_message(chat_id=int(uid), text=msg, parse_mode="Markdown")
    except Exception:
        pass

# ---------- Catalog ----------
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
        f"<b>{prod['name']}</b> uchun nechta dona olishni xohlaysiz? Raqamni kiriting (masalan: 70):",
        parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_for_custom_count)
    await callback_query.answer()

@dp.message(OrderState.waiting_for_custom_count)
async def process_custom_dona(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 50):")
        return
    count = int(message.text)
    data = await state.get_data()
    product_key = data.get('selected_product')
    user_id = message.from_user.id
    user_carts.setdefault(user_id, {})
    user_carts[user_id][product_key] = user_carts[user_id].get(product_key, 0) + count
    await message.answer(f"Savatga {count} dona qo'shildi! ✅", reply_markup=get_main_keyboard(user_id))
    await state.set_state(OrderState.shopping)

# ---------- Cart ----------
def build_cart(cart):
    text = "🛒 <b>Sizning savatingiz:</b>\n\n"
    total_price = 0
    inline_kb = []
    for prod_key, total_items in cart.items():
        if prod_key in PRODUCTS:
            prod = PRODUCTS[prod_key]
            cost = total_items * prod['price']
            total_price += cost
            text += f"• {prod['name']}: {total_items} ta dona - {cost} so'm\n"
            inline_kb.append([InlineKeyboardButton(text=f"❌ O'chirish: {prod['name']}", callback_data=f"remove_{prod_key}")])
    text += f"\n💳 <b>Umumiy summa:</b> {total_price} so'm"
    return text, InlineKeyboardMarkup(inline_keyboard=inline_kb)

@dp.message(F.text == "🛒 Savatni ko'rish", OrderState.shopping)
async def show_cart(message: types.Message):
    cart = user_carts.get(message.from_user.id, {})
    if not cart:
        await message.answer("Savatingiz hozircha bo'sh. 📭", reply_markup=get_main_keyboard(message.from_user.id))
        return
    text, kb = build_cart(cart)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data.startswith('remove_'), OrderState.shopping)
async def remove_from_cart(callback_query: types.CallbackQuery):
    product_key = callback_query.data.split('_', 1)[1]
    user_id = callback_query.from_user.id
    if user_id in user_carts and product_key in user_carts[user_id]:
        del user_carts[user_id][product_key]
        await callback_query.answer("Savatdan olib tashlandi! 🗑")
        cart = user_carts[user_id]
        if not cart:
            await callback_query.message.edit_text("Savatingiz bo'shadi. 📭")
        else:
            text, kb = build_cart(cart)
            await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

# ---------- Finish Order ----------
@dp.message(F.text == "✅ Buyurtmani yakunlash", OrderState.shopping)
async def finish_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, {})
    if not cart:
        await message.answer("Savatingiz bo'sh! Avval mahsulot tanlang.", reply_markup=get_main_keyboard(user_id))
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

    user_saved_info = saved_users.get(str(user_id)) or {}
    user_name = data.get('name') or user_saved_info.get('name') or "Noma'lum"
    user_phone = data.get('phone') or user_saved_info.get('phone') or "-"

    # Save order
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
        "Buyurtmangiz muvaffaqiyatli yuborildi! ✅ Tez orada siz bilan bog'lanishadi.\n\n"
        "Yangi buyurtma berish uchun /start buyrug'ini bosing.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await send_sticker_safe(message.chat.id, "🍦", "❤", "👍", "✅")
    await state.clear()

# ---------- Admin Payment Processing ----------
@dp.callback_query(F.data.startswith('pay_full_'))
async def process_pay_full(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, total_price = callback_query.data.split('_')
    
    try:
        await bot.send_message(int(target_user_id), f"Buyurtmangiz uchun to'lov qabul qilindi. Rahmat! ✅")
    except Exception:
        pass

    await callback_query.message.reply(f"To'lov to'liq qabul qilindi. Mijozga qarz yozilmadi. ✅")
    await callback_query.answer()

@dp.callback_query(F.data.startswith('pay_debt_'))
async def process_pay_debt(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, total_price = callback_query.data.split('_')
    
    order_info = parse_order_text(callback_query.message.text or callback_query.message.caption or "")
    total_debt = add_user_debt(target_user_id, order_info['name'], order_info['phone'], int(total_price), order_info.get('items_str', ''))

    try:
        await bot.send_message(
            int(target_user_id), 
            f"Buyurtmangiz qarzga rasmiylashtirildi.\n"
            f"Ushbu buyurtma: {fmt_money(total_price)} so'm.\n"
            f"Umumiy qarzingiz: {fmt_money(total_debt)} so'm."
        )
    except Exception:
        pass

    await callback_query.message.reply(f"Mijoz qarziga {fmt_money(total_price)} so'm qo'shildi. Umumiy qarzi: {fmt_money(total_debt)} so'm.")
    await callback_query.answer()

@dp.callback_query(F.data.startswith('pay_part_'))
async def process_pay_part(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        return
    _, _, target_user_id, total_price = callback_query.data.split('_')
    
    await state.update_data(
        target_user_id=target_user_id, 
        total_price=int(total_price), 
        msg_text=callback_query.message.text or callback_query.message.caption or ""
    )
    await callback_query.message.reply("Olingan summani kiriting (masalan 20000):")
    await state.set_state(OrderState.waiting_for_partial_pay)
    await callback_query.answer()

@dp.message(OrderState.waiting_for_partial_pay)
async def process_partial_pay_input(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting:")
        return

    paid = int(message.text)
    data = await state.get_data()
    target_user_id = data['target_user_id']
    total_price = data['total_price']
    
    debt_to_add = total_price - paid
    order_info = parse_order_text(data.get('msg_text', ''))
    
    if debt_to_add > 0:
        total_debt = add_user_debt(target_user_id, order_info['name'], order_info['phone'], debt_to_add, order_info.get('items_str', ''))
        msg_text = f"Qolgan {fmt_money(debt_to_add)} so'm qarzga yozildi. Umumiy qarzi: {fmt_money(total_debt)} so'm."
        try:
            await bot.send_message(
                int(target_user_id), 
                f"Siz {fmt_money(paid)} so'm to'ladingiz.\n"
                f"Qolgan {fmt_money(debt_to_add)} so'm qarzga yozildi.\n"
                f"Umumiy qarzingiz: {fmt_money(total_debt)} so'm."
            )
        except Exception:
            pass
    else:
        msg_text = "To'lov to'liq qoplandi, qarz yozilmadi."

    await message.answer(msg_text)
    await state.clear()

# ---------- API ----------
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
    
    app.router.add_get("/", handle_ping)
    app.router.add_get("/api/orders", get_orders_api)
    app.router.add_get("/api/debts", get_debts_api)

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
