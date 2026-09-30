import logging
import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8941827736:AAFBeYE_MJ6HlVXJHGoVFeRslYWY2XzggYo"
ADMIN_ID = 8488328091

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
    "jazzi": {"name": "8. Jazzi", "count_in_box": 50, "price": 2300, "photo": "https://t.me/YAYPAN_muzqaymoq/67"},
    "ferero": {"name": "9. Ferero", "count_in_box": 54, "price": 2200, "photo": "https://t.me/YAYPAN_muzqaymoq/68"},
    "anjan_qulupnay": {"name": "10. Anjan qulupnay", "count_in_box": 20, "price": 5000, "photo": "https://t.me/YAYPAN_muzqaymoq/69"},
    "shokoland": {"name": "11. Shokoland", "count_in_box": 60, "price": 1600, "photo": "https://t.me/YAYPAN_muzqaymoq/70?single"},
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
    shopping = State()
    waiting_for_custom_count = State()

user_carts = {}

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Savatni ko'rish"), KeyboardButton(text="✅ Buyurtmani yakunlash")]
    ],
    resize_keyboard=True
)

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    user_carts[message.from_user.id] = {}
    await message.answer("Assalomu alaykum! Muzqaymoq buyurtma berish botiga xush kelibsiz.\nIltimos, Ism va Familiyangizni kiriting:")
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
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(OrderState.waiting_for_phone)

@dp.message(OrderState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    
    await message.answer("Rahmat! Quyidagi mahsulotlar ro'yxatidan tanlang:", reply_markup=main_menu_keyboard)
    await show_catalog(message)
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
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Karobkada olish", callback_data=f"box_{key}"),
                InlineKeyboardButton(text="🔢 Dona tanlash", callback_data=f"dona_{key}")
            ]
        ])
        
        try:
            await message.answer_photo(
                photo=prod['photo'],
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith('box_'), OrderState.shopping)
async def add_box_to_cart(callback_query: types.CallbackQuery):
    product_key = callback_query.data.split('_', 1)[1]
    user_id = callback_query.from_user.id
    
    if user_id not in user_carts:
        user_carts[user_id] = {}
        
    prod = PRODUCTS[product_key]
    add_count = prod['count_in_box']
    
    if product_key in user_carts[user_id]:
        user_carts[user_id][product_key] += add_count
    else:
        user_carts[user_id][product_key] = add_count
        
    await callback_query.answer(f"1 karobka ({add_count} ta) savatga qo'shildi! ✅")

@dp.callback_query(F.data.startswith('dona_'), OrderState.shopping)
async def ask_custom_dona(callback_query: types.CallbackQuery, state: FSMContext):
    product_key = callback_query.data.split('_', 1)[1]
    prod = PRODUCTS[product_key]
    
    await state.update_data(selected_product=product_key)
    await callback_query.message.answer(f"<b>{prod['name']}</b> uchun nechta dona olishni xohlaysiz? Raqamni kiriting (masalan: 70):", parse_mode="HTML")
    await state.set_state(OrderState.waiting_for_custom_count)
    await callback_query.answer()

@dp.message(OrderState.waiting_for_custom_count)
async def process_custom_dona(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting (masalan: 50):")
        return
        
    count = int(message.text)
    data = await state.get_data()
    product_key = data.get('selected_product')
    user_id = message.from_user.id
    
    if user_id not in user_carts:
        user_carts[user_id] = {}
        
    if product_key in user_carts[user_id]:
        user_carts[user_id][product_key] += count
    else:
        user_carts[user_id][product_key] = count
        
    await message.answer(f"Savatga {count} dona qo'shildi! ✅", reply_markup=main_menu_keyboard)
    await state.set_state(OrderState.shopping)

@dp.message(F.text == "🛒 Savatni ko'rish", OrderState.shopping)
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, {})
    
    if not cart:
        await message.answer("Savatingiz hozircha bo'sh. 📭", reply_markup=main_menu_keyboard)
        return

    text = "🛒 **Sizning savatingiz:**\n\n"
    total_price = 0
    
    inline_kb = []
    for prod_key, total_items in cart.items():
        if prod_key in PRODUCTS:
            prod = PRODUCTS[prod_key]
            cost = total_items * prod['price']
            total_price += cost
            text += f"• {prod['name']}: {total_items} ta dona - {cost} so'm\n"
            inline_kb.append([InlineKeyboardButton(text=f"❌ O'chirish: {prod['name']}", callback_data=f"remove_{prod_key}")])

    text += f"\n💳 **Umumiy summa:** {total_price} so'm"
    
    await message.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))

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
            text = "🛒 **Sizning savatingiz:**\n\n"
            total_price = 0
            inline_kb = []
            for p_key, total_items in cart.items():
                if p_key in PRODUCTS:
                    prod = PRODUCTS[p_key]
                    cost = total_items * prod['price']
                    total_price += cost
                    text += f"• {prod['name']}: {total_items} ta dona - {cost} so'm\n"
                    inline_kb.append([InlineKeyboardButton(text=f"❌ O'chirish: {prod['name']}", callback_data=f"remove_{p_key}")])
            text += f"\n💳 **Umumiy summa:** {total_price} so'm"
            await callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_kb))
    else:
        await callback_query.answer("Bu mahsulot savatda yo'q!")

@dp.message(F.text == "✅ Buyurtmani yakunlash", OrderState.shopping)
async def finish_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, {})
    
    if not cart:
        await message.answer("Savatingiz bo'sh! Avval mahsulot tanlang.", reply_markup=main_menu_keyboard)
        return

    data = await state.get_data()
    name = data.get('name')
    location = data.get('location')
    phone = data.get('phone')
    
    total_price = 0
    order_details = ""
    
    for prod_key, total_items in cart.items():
        if prod_key in PRODUCTS:
            prod = PRODUCTS[prod_key]
            cost = total_items * prod['price']
            total_price += cost
            order_details += f"• {prod['name']}: {total_items} ta × {prod['price']} = {cost} so'm\n"
        
    admin_message = (
        f"📥 **Yangi buyurtma keldi!**\n\n"
        f"👤 **Ism:** {name}\n"
        f"📍 **Manzil:** {location}\n"
        f"📞 **Telefon:** {phone}\n\n"
        f"🛍 **Buyurtma tarkibi:**\n{order_details}\n"
        f"💳 **Umumiy summa:** {total_price} so'm"
    )
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Yetkazilmoqda", callback_data=f"deliv_{user_id}")]
    ])
    
    await bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown", reply_markup=admin_kb)
    
    user_carts[user_id] = {}
    await message.answer(
        "Buyurtmangiz muvaffaqiyatli yuborildi! ✅ Tez orada siz bilan bog'lanishadi.\n\nYangi buyurtma berish uchun /start buyrug'ini bosing.", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()

@dp.callback_query(F.data.startswith('deliv_'))
async def process_delivery_status(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("Bu tugma faqat admin uchun!", show_alert=True)
        return

    target_user_id = int(callback_query.data.split('_', 1)[1])
    
    try:
        await bot.send_message(target_user_id, "Muzqaymoq 30 minutda yetib boradi 🧊")
        await callback_query.answer("Xaridorga xabar yuborildi! ✅")
        
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Yetkazilmoqda (Yuborildi)", callback_data="none")]
            ])
        )
    except Exception as e:
        await callback_query.answer(f"Xatolik yuz berdi: xaridor botni bloklagan bo'lishi mumkin.", show_alert=True)

# Render serverini hushyor ushlab turish uchun HTTP sahifa
async def handle_ping(request):
    return web.Response(text="Bot ishlamoqda!")

async def main():
    # Web server yaratish
    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    # Telegram pollingni boshlash
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
