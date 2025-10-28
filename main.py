hereimport os
import asyncio
import random
from datetime import date, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils import executor
from keep_alive import keep_alive
from database import (
    init_db, add_user, get_user_count, get_kino_by_code,
    get_all_codes, delete_kino_code, get_code_stat,
    increment_stat, get_all_user_ids, get_today_users,
    add_anime, get_all_admins, add_admin, remove_admin,
    search_anime_by_name, get_conn, update_anime_code, update_anime_poster,
    add_channel_to_db, get_channels_by_type, delete_channel_from_db,
    set_bot_active, get_bot_active, ban_user, unban_user,
    is_user_banned, get_all_banned_users, add_multiple_users,
    add_part_to_anime, delete_part_from_anime,
    get_user_profile, update_user_balance, set_user_balance,
    give_vip, remove_vip, is_user_vip, get_all_vip_users,
    get_vip_prices, update_vip_price, get_card_number, set_card_number,
    add_payment_request, get_pending_payment_requests, approve_payment_request,
    reject_payment_request, get_all_genres, get_anime_by_genre, get_random_anime,
    get_top_anime, update_anime_genre, set_anime_forward_status, get_anime_forward_status,
    update_user_activity, get_active_today_users, get_weekly_new_users,
        get_all_vip_user_ids, get_all_regular_user_ids,  # Yangi funksiyalar
    add_pending_request, is_request_pending, remove_all_pending_requests # ZAYAVKA UCHUN
)
    
load_dotenv()
keep_alive()

API_TOKEN = os.getenv("API_TOKEN")
CHANNELS = []
LINKS = []
CHANNEL_USERNAMES = []
MAIN_CHANNELS = []
MAIN_LINKS = []
MAIN_USERNAMES = []
BOT_USERNAME = os.getenv("BOT_USERNAME")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

START_ADMINS = [7483732504, 5959511392]
ADMINS = set(START_ADMINS)

user_data = {}


async def load_channels():
    global CHANNELS, LINKS, CHANNEL_USERNAMES, MAIN_CHANNELS, MAIN_LINKS, MAIN_USERNAMES
    sub_channels = await get_channels_by_type('sub')
    CHANNELS = [ch[0] for ch in sub_channels]
    LINKS = [ch[1] for ch in sub_channels]
    CHANNEL_USERNAMES = [ch[2] if len(ch) > 2 else "" for ch in sub_channels]
    
    main_channels = await get_channels_by_type('main')
    MAIN_CHANNELS = [ch[0] for ch in main_channels]
    MAIN_LINKS = [ch[1] for ch in main_channels]
    MAIN_USERNAMES = [ch[2] if len(ch) > 2 else "" for ch in main_channels]

# --- KEYBOARDS (O'ZGARTIRILGAN) ---

def user_panel_keyboard(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🔍 Anime izlash"), KeyboardButton("🎞 Barcha animelar"))
    kb.add(KeyboardButton("💳 Pul kiritish"), KeyboardButton("💎 VIP olish"))
    kb.add(KeyboardButton("📦 Buyurtma berish"), KeyboardButton("👤 Profil"))
    kb.add(KeyboardButton("✉️ Admin bilan bog'lanish"))
    if is_admin:
        # Foydalanuvchi panelidan Admin paneliga o'tish
        kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def admin_panel_keyboard():
    # '📄 Kodlar ro'yxati' shu yerga qo'shildi
    # '📢 Habar yuborish' -> '✉️ Xabar yuborish' ga o'zgartirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("📋 Kodlar paneli"), KeyboardButton("🤖 Bot paneli"))
    kb.add(KeyboardButton("📡 Kanal boshqaruvi"), KeyboardButton("➕ Anime qo'shish"))
    kb.add(KeyboardButton("📊 Statistika"), KeyboardButton("👥 Adminlar"))
    kb.add(KeyboardButton("📄 Kodlar ro'yxati")) # <<< YANGI JOY
    kb.add(KeyboardButton("✉️ Xabar yuborish"), KeyboardButton("📤 Post qilish"))
    kb.add(KeyboardButton("👤 Foydalanuvchi paneli"))
    return kb


def kodlar_panel_keyboard():
    # '📄 Kodlar ro'yxati' olib tashlandi
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("❌ Kodni o'chirish"), KeyboardButton("🔄 Kodni tahrirlash"))
    kb.add(KeyboardButton("📈 Kod statistikasi"), KeyboardButton("✏️ Postni tahrirlash"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def bot_panel_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🤖 Bot holati"), KeyboardButton("👥 User qo'shish"))
    kb.add(KeyboardButton("💎 VIP boshqaruvi"), KeyboardButton("🎬 Anime statusi"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def anime_search_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("📝 Nomi bilan izlash"), KeyboardButton("🔢 Kodi bilan izlash"))
    kb.add(KeyboardButton("🎭 Janr orqali izlash"), KeyboardButton("🎲 Tasodifiy animelar"))
    kb.add(KeyboardButton("🏆 10 TOP animelar"))
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb


def vip_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("💎 VIP ga nima kiradi?"), KeyboardButton("💰 VIP sotib olish"))
    kb.add(KeyboardButton("🔙 Orqaga"))
    return kb


def vip_management_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("➕ VIP berish"), KeyboardButton("❌ VIP olish"))
    kb.add(KeyboardButton("💳 Karta boshqaruvi"), KeyboardButton("💵 Pul qo'shish"))
    kb.add(KeyboardButton("💸 Pul olish"), KeyboardButton("💰 VIP narxini belgilash"))
    kb.add(KeyboardButton("📋 VIP userlar ro'yxati"), KeyboardButton("💳 To'lov so'rovlari"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def back_keyboard():
    # Bu faqat foydalanuvchi menyulari uchun
    return ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Orqaga")

def admin_back_keyboard():
    # Bu faqat admin menyulari uchun
    return ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 Admin paneli")


def admin_menu_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Admin qo'shish")
    kb.add("➖ Admin o'chirish")
    kb.add("👥 Adminlar ro'yxati")
    kb.add("🔙 Admin paneli")
    return kb


def bot_status_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("✅ Botni yoqish"), KeyboardButton("⛔️ Botni o'chirish"))
    kb.add(KeyboardButton("🚫 User ban qilish"), KeyboardButton("✅ User ban dan chiqarish"))
    kb.add(KeyboardButton("📋 Banlangan userlar"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb


def edit_code_menu_keyboard():
    # Faqat '🔙 Admin paneli' qoldirildi
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("🔄 Nomini o'zgartirish"))
    kb.add(KeyboardButton("➕ Qisim qo'shish"), KeyboardButton("➖ Qisim o'chirish"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb

# YANGI KEYBOARD (Xabar yuborish uchun)
def admin_broadcast_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("👤 Bitta foydalanuvchiga"))
    kb.add(KeyboardButton("👥 Barcha foydalanuvchilarga"))
    kb.add(KeyboardButton("💎 VIP foydalanuvchilarga"))
    kb.add(KeyboardButton("⭐️ Oddiy foydalanuvchilarga"))
    kb.add(KeyboardButton("🔙 Admin paneli"))
    return kb

# --- END KEYBOARDS ---

# YANGI FUNKSIYA (Post qilish uchun kanal tanlash menyusi)
async def generate_channel_selection_keyboard(user_id):
    """
    Foydalanuvchi uchun kanal tanlash menyusini yaratadi.
    user_data da 'selected_channels' (set) bo'lishi kerak.
    """
    data = user_data.get(user_id, {})
    selected_channels = data.get('selected_channels', set())
    
    kb = InlineKeyboardMarkup(row_width=1)
    
    # Barcha asosiy kanallarni tugma sifatida qo'shamiz
    for idx, channel_id in enumerate(MAIN_CHANNELS):
        # Kanal nomini (username) olamiz, agar yo'q bo'lsa ID sini ko'rsatamiz
        name = MAIN_USERNAMES[idx]
        display_name = f"@{name}" if name else f"ID: {channel_id}"
        
        if channel_id in selected_channels:
            button_text = f"✅ {display_name}"
        else:
            button_text = f"☑️ {display_name}"
        
        kb.add(InlineKeyboardButton(button_text, callback_data=f"post_toggle_ch:{channel_id}"))
    
    # Boshqaruv tugmalari
    kb.add(InlineKeyboardButton("✅ Barchasiga jo'natish", callback_data="post_send_all"))
    
    selected_count = len(selected_channels)
    kb.add(InlineKeyboardButton(f"🚀 Jo'natish ({selected_count} ta tanlangan)", callback_data="post_send_selected"))
    
    kb.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="post_cancel"))
    
    return kb

# --- END (Yangi funksiya) ---


async def get_unsubscribed_channels(user_id):
    # ... POST KANALLAR TUGADI
    
async def get_unsubscribed_channels(user_id):
    is_vip = await is_user_vip(user_id)
    if is_vip or user_id in ADMINS:
        return []
    
    unsubscribed = []
    for idx, channel_id in enumerate(CHANNELS):
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            
            # 1. Егер пайдаланушы канал мүшесі БОЛМАСА
            if member.status not in ["member", "administrator", "creator"]:
                # 2. Базадан "сұраныс" (заявка) бар-жоғын тексереміз
                is_pending = await is_request_pending(user_id, channel_id)
                
                # 3. Егер мүше болмаса ЖӘНЕ сұранысы да жоқ болса, тізімге қосамыз
                if not is_pending:
                    unsubscribed.append((channel_id, LINKS[idx]))
        except:
            # Каналда қате болса да (мысалы, бот бан алса), базаны тексереміз
            is_pending = await is_request_pending(user_id, channel_id)
            if not is_pending:
                unsubscribed.append((channel_id, LINKS[idx]))
    return unsubscribed

async def make_unsubscribed_markup(user_id, code):
    unsubscribed = await get_unsubscribed_channels(user_id)
    markup = InlineKeyboardMarkup(row_width=1)
    for channel_id, channel_link in unsubscribed:
        try:
            chat = await bot.get_chat(channel_id)
            markup.add(InlineKeyboardButton(f"➕ {chat.title}", url=channel_link))
        except:
            pass
    markup.add(InlineKeyboardButton("✅ Tekshirish", callback_data=f"checksub:{code}"))
    return markup


# --- POST FORMAT (O'ZGARTIRILGAN) ---
#--- CHANEL POSTI BOSHLANDI---
#--- SEND CHANEL POST.---

async def send_channel_post(channel_id, kino, code):
    title = kino.get('title', 'Noma\'lum')
    parts_count = kino.get('post_count', 0)
    genre = kino.get('genre', 'Anime')
    ovoz_berdi = kino.get('ovoz_berdi', '')  # Ovoz berdi maydoni
    channel_username = MAIN_USERNAMES[0] if MAIN_USERNAMES else "@animelar_serveri"

    caption = "✽ ──...──:•°⛩°•:──...──╮\n"
    caption += f"    ✨ {title} ✨\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    caption += f"🎞 Qismlar soni : {parts_count}\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🖋 Janri : {genre}\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    
    if ovoz_berdi:
        caption += f"🎙 Ovoz berdi : {ovoz_berdi}\n"
        caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    
    caption += "💭 Tili : O'zbek\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🔍 Kod : {code}\n"  # Qidirish soni орнына Kod қосылды
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🌐 Manzil: @{channel_username}"

    button_text = kino.get('button_text') or "💎 Tomosha qilish 💎"
    button_url = kino.get('button_url') or f"https://t.me/{BOT_USERNAME}?start={code}"
    
    download_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton(button_text, url=button_url)
    )
    
    try:
        media_type = kino.get('media_type', 'photo')
        if media_type == "photo":
            await bot.send_photo(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        elif media_type == "video":
            await bot.send_video(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        else:
            await bot.send_document(channel_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
    except Exception as e:
        print(f"Xatolik kanalga post yuborishda: {e}")
        raise

#--- END CHANEL POST 
#--- REKLAMA POSTI BOSHLANDI---
#--- SEND REKLAMA POST---

async def send_reklama_post(user_id, code):
    kino = await get_kino_by_code(code)
    if not kino:
        await bot.send_message(user_id, "❌ Kod topilmadi.")
        return

    title = kino.get('title', 'Noma\'lum')
    parts_count = kino.get('post_count', 0)
    genre = kino.get('genre', 'Anime')
    ovoz_berdi = kino.get('ovoz_berdi', '')  # Ovoz berdi maydoni
    channel_username = MAIN_USERNAMES[0] if MAIN_USERNAMES else "@animelar_serveri"

    caption = "✽ ──...──:•°⛩°•:──...──╮\n"
    caption += f"    ✨ {title} ✨\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    caption += f"🎞 Qismlar soni : {parts_count}\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🖋 Janri : {genre}\n"
    caption += ". . . . . . . . . . . . . . . . . . . . . . . ──\n"
    
    if ovoz_berdi:
        caption += f"🎙 Ovoz berdi : {ovoz_berdi}\n"
        caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    
    caption += "💭 Tili : O'zbek\n"
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🔍 Kod : {code}\n"  # Qidirish soni орнына Kod қосылды
    caption += ". . . ── . . . . . . . . . . . . . . . . . . . .\n"
    caption += f"🌐 Manzil: @{channel_username}"

    button_text = kino.get('button_text') or "💎 Tomosha qilish 💎"
    
    download_btn = InlineKeyboardMarkup().add(
        InlineKeyboardButton(button_text, callback_data=f"download_anime:{code}")
    )

    try:
        media_type = kino.get('media_type', 'photo')
        if media_type == "photo":
            await bot.send_photo(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        elif media_type == "video":
            await bot.send_video(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")
        else:
            await bot.send_document(user_id, kino['poster_file_id'], caption=caption, reply_markup=download_btn, parse_mode="Markdown")

        await increment_stat(code, "viewed")  # Viewed санын жаңарту
    except Exception as e:
        await bot.send_message(user_id, f"❌ Xatolik yuz berdi: {e}")

# --- END POST FORMAT ---
#SEND ANIME PARTS 

async def send_anime_parts(user_id, code):
    kino = await get_kino_by_code(code)
    if not kino:
        return
    
    title = kino.get('title', 'Noma\'lum')
    parts = kino.get('parts_file_ids', [])
    
    # --- ТҮЗЕТУ БАСТАЛДЫ ---
    # 1. Анименің "forward" статусын аламыз (по умолчанию "ruxsat etilgan" - True)
    forward_is_enabled = kino.get('forward_enabled', True)
    
    # 2. Мазмұнды қорғау статусын анықтаймыз:
    # Егер forward_is_enabled = True болса, protect_status = False (қорғау КЕРЕК ЕМЕС)
    # Егер forward_is_enabled = False болса, protect_status = True (қорғау КЕРЕК)
    protect_status = not forward_is_enabled
    # --- ТҮЗЕТУ АЯҚТАЛДЫ ---

    for idx, file_id in enumerate(parts, 1):
        try:
            await bot.send_document(
                user_id, 
                file_id, 
                caption=f"📂 {title} - {idx}-qism",
                protect_content=protect_status  # <-- ОСЫ ЖЕР ҚОСЫЛДЫ
            )
        except:
            try:
                await bot.send_video(
                    user_id, 
                    file_id, 
                    caption=f"📂 {title} - {idx}-qism",
                    protect_content=protect_status  # <-- ОСЫ ЖЕР ҚОСЫЛДЫ
                )
            except Exception as e:
                print(f"Xatolik qism yuborishda: {e}")

#SEND ANIME PARTS TUGADI

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.\n\n✉️ Admin bilan bog'lanish uchun /contact buyrug'ini yuboring.")
        return
    
    bot_active = await get_bot_active()
    if not bot_active and message.from_user.id not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan. Keyinroq urinib ko'ring.")
        return
    
    await add_user(message.from_user.id)
    await update_user_activity(message.from_user.id)
    args = message.get_args()

    if args and args.isdigit():
        code = args
        await increment_stat(code, "init")
        await increment_stat(code, "searched")

        unsubscribed = await get_unsubscribed_channels(message.from_user.id)
        if unsubscribed:
            markup = await make_unsubscribed_markup(message.from_user.id, code)
            await message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
        else:
            await send_reklama_post(message.from_user.id, code)
        return

    is_vip = await is_user_vip(message.from_user.id)
    
    if is_vip:
        welcome_text = (
            "💎 Assalomu alaykum!\n\n"
            f"⭐ {message.from_user.first_name}, VIP foydalanuvchi!\n\n"
            "🎬 Bu yerda minglab anime seriallarini topishingiz mumkin!\n"
            "✨ VIP sifatida siz barcha imkoniyatlardan foydalana olasiz!\n\n"
            "🔥 Qiziqarli anime dunyosiga xush kelibsiz!"
        )
    else:
        welcome_text = (
            "🎭 Assalomu alaykum!\n\n"
            f"👤 {message.from_user.first_name}, botimizga xush kelibsiz!\n\n"
            "🎬 Bu yerda minglab anime seriallarini topishingiz mumkin!\n"
            "🔍 Qidirish orqali o'zingizga yoqqan animeni toping!\n\n"
            "✨ Qiziqarli anime dunyosiga xush kelibsiz!"
        )

    if message.from_user.id in ADMINS:
        await message.answer(welcome_text, reply_markup=admin_panel_keyboard())
    else:
        await message.answer(welcome_text, reply_markup=user_panel_keyboard())


@dp.message_handler(commands=['contact'])
async def contact_command(message: types.Message):
    if await is_user_banned(message.from_user.id):
        user_data[message.from_user.id] = {'action': 'contact_admin'}
        await message.answer("✍️ Adminlarga yubormoqchi bo'lgan xabaringizni yozing.")
    else:
        await message.answer("✉️ Admin bilan bog'lanish uchun menyudan foydalaning.")

# --- ZAYAVKA KANALLARNI AVTO-TASDIQLASH ---

@dp.chat_join_request_handler()
async def handle_join_request(update: types.ChatJoinRequest):
    global CHANNELS  # Global majburiy obuna kanallari ro'yxati
    
    chat_id = update.chat.id
    user_id = update.from_user.id

    # Bot faqat bizning majburiy obuna (sub) kanallarimiz ro'yxatidagi
    # kanallar uchun so'rovlarni bazaga saqlashi kerak.
    
    if chat_id in CHANNELS:
        try:
            # Foydalanuvchi so'rovini bazaga saqlaymiz
            await add_pending_request(user_id, chat_id)
            print(f"[ZAYAVKA] Foydalanuvchi {user_id} uchun {chat_id} kanaliga so'rov bazaga saqlandi.")
            
            # (Ixtiyoriy) Foydalanuvchiga bu haqida xabar berish
            try:
                await bot.send_message(user_id, 
                    f"✅ \"{update.chat.title}\" zayafka saqlandi.\n\n"
                    "«✅ Yana tekshirish» tugmasni bosin."
                )
            except Exception as e:
                print(f"Xatolik (zayavka xabari yuborish): {e}")
                
        except Exception as e:
            print(f"Xatolik (zayavka saqlash): {e}")

# --- END ZAYAVKA HANDLER ---

# --- NAVIGATION HANDLERS (O'ZGARTIRILGAN) ---

@dp.message_handler(lambda m: m.text == "👤 Foydalanuvchi paneli")
async def switch_to_user_panel(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    # Admin uchun maxsus '🔙 Admin paneli' tugmasi bilan ko'rsatish
    await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard(is_admin=True))


@dp.message_handler(lambda m: m.text == "🔙 Orqaga")
async def back_to_main(message: types.Message):
    user_data.pop(message.from_user.id, None)
    
    # Bu tugma faqat foydalanuvchi menyularidan (masalan, izlash) qaytish uchun
    if message.from_user.id in ADMINS:
        # Adminni 'Foydalanuvchi paneli'ga qaytaramiz (admin versiyasiga)
        await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard(is_admin=True))
    else:
        await message.answer("👤 Foydalanuvchi paneli:", reply_markup=user_panel_keyboard())


@dp.message_handler(lambda m: m.text == "🔙 Admin paneli")
async def back_to_admin_panel(message: types.Message):
    # Bu tugma BARCHA admin sub-panellaridan qaytish uchun
    if message.from_user.id not in ADMINS:
        return
    user_data.pop(message.from_user.id, None)
    await message.answer("👮‍♂️ Admin panel:", reply_markup=admin_panel_keyboard())

# --- END NAVIGATION HANDLERS ---
#  CHEK SUBSCRIBTION 

@dp.callback_query_handler(lambda c: c.data.startswith("checksub:"))
async def check_subscription_callback(call: types.CallbackQuery):
    if await is_user_banned(call.from_user.id):
        await call.answer("⛔️ Siz ban qilingan foydalanuvchisiz.", show_alert=True)
        return
    
    bot_active = await get_bot_active()
    if not bot_active and call.from_user.id not in ADMINS:
        await call.answer("🚫 Bot vaqtincha to'xtatilgan.", show_alert=True)
        return
    
    code = call.data.split(":")[1]
    
    # 1. Жазылмаған НЕМЕСЕ сұраныс жібермеген каналдарды аламыз
    # (Біз бұл функцияны өзгерттік, ол енді базаны да тексереді)
    unsubscribed_channels = await get_unsubscribed_channels(call.from_user.id)
    
    # 2. Нәтижені тексереміз
    if unsubscribed_channels:
        # Егер әлі де сұраныс жіберілмеген каналдар болса
        markup = InlineKeyboardMarkup(row_width=1)
        for channel_id, channel_link in unsubscribed_channels:
            try:
                chat = await bot.get_chat(channel_id)
                markup.add(InlineKeyboardButton(f"➕ {chat.title}", url=channel_link))
            except:
                pass
        markup.add(InlineKeyboardButton("✅ Yana tekshirish", callback_data=f"checksub:{code}"))
        
        try:
            await call.message.edit_text("❗ Hali ham obuna bo'lmagan yoki сұраныс жіберілмеген kanal(lar):", reply_markup=markup)
        except: # Егер мәтін өзгермеген болса
            pass
        
        await call.answer(
            "🔄 Tekshirildi. Ro'yxatdagi kanallarga сұраныс (zayavka) yuboring va qaytadan tekshiring.",
            show_alert=True,
            cache_time=1
        )
    else:
        # Барлық каналдарға не жазылған, не сұраныс жіберілген
        await call.message.delete()
        await send_reklama_post(call.from_user.id, code)
        await increment_stat(code, "searched")
        
        # await remove_all_pending_requests(call.from_user.id) # <-- МАҢЫЗДЫ! БІЗ БҰЛ ҚАТАРДЫ АЛЫП ТАСТАДЫҚ!
        
        await call.answer("✅ Obuna tasdiqlandi! Anime yuborilmoqda...")

#  --- END CHEK SUB
@dp.callback_query_handler(lambda c: c.data.startswith("download_anime:"))
async def download_anime_callback(call: types.CallbackQuery):
    code = call.data.split(":")[1]
    await send_anime_parts(call.from_user.id, code)
    await call.answer("✅ Qismlar yuborilmoqda...", show_alert=False)


@dp.message_handler(lambda m: m.text == "🔍 Anime izlash")
async def anime_search_menu(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    bot_active = await get_bot_active()
    if not bot_active and message.from_user.id not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan.")
        return
    
    await update_user_activity(message.from_user.id)
    await message.answer("🔍 Anime izlash menyusi:", reply_markup=anime_search_menu_keyboard())


@dp.message_handler(lambda m: m.text == "📝 Nomi bilan izlash")
async def anime_search_by_name(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    user_data[message.from_user.id] = {'action': 'search_by_name'}
    await message.answer("📝 Anime nomini kiriting:\n\nMisol: 'Naruto'", reply_markup=back_keyboard())


@dp.message_handler(lambda m: m.text == "🔢 Kodi bilan izlash")
async def anime_search_by_code(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    user_data[message.from_user.id] = {'action': 'search_by_code'}
    await message.answer("🔢 Anime kodini kiriting:\n\nMisol: '147'", reply_markup=back_keyboard())

@dp.message_handler(lambda m: m.text == "🎭 Janr orqali izlash")
async def genre_search_menu(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    # VIP-тексеру осы жерден алып тасталды (бұл дұрыс)
    
    genres = await get_all_genres()
    if not genres:
        await message.answer("❌ Hozircha janrlar yo'q.")
        return
    
    kb = InlineKeyboardMarkup(row_width=2)
    for genre in genres[:20]:
        kb.add(InlineKeyboardButton(f"🎭 {genre}", callback_data=f"genre:{genre}"))
    
    await message.answer("🎭 Janrni tanlang:", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("genre:"))
async def show_genre_animes(call: types.CallbackQuery):
    genre = call.data.split(":", 1)[1]
    animes = await get_anime_by_genre(genre, 20)
    
    if not animes:
        await call.message.answer(f"❌ '{genre}' janrida anime topilmadi.")
        await call.answer()
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    for anime in animes:
        title = anime.get('title', 'Noma\'lum')
        code = anime.get('code', '')
        kb.add(InlineKeyboardButton(f"📺 {title}", callback_data=f"select_anime:{code}"))
    
    await call.message.answer(f"🎭 {genre} janridagi animelar:", reply_markup=kb)
    await call.answer()


@dp.message_handler(lambda m: m.text == "🎲 Tasodifiy animelar")
async def random_anime_start(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    # VIP-тексеру осы жерден алып тасталды
    
    random_anime = await get_random_anime(1)
    if not random_anime:
        await message.answer("❌ Hozircha animelar yo'q.")
        return
    
    anime = random_anime[0]
    code = anime['code']
    user_data[message.from_user.id] = {'random_current_code': code}
    
    await show_random_anime(message.from_user.id, code)


async def show_random_anime(user_id, code):
    kino = await get_kino_by_code(code)
    if not kino:
        await bot.send_message(user_id, "❌ Anime topilmadi.")
        return
    
    title = kino.get('title', 'Noma\'lum')
    genre = kino.get('genre', 'Anime')
    parts_count = kino.get('post_count', 0)
    
    caption = (
        f"🎲 TASODIFIY ANIME\n\n"
        f"📺 {title}\n"
        f"🎭 Janr: {genre}\n"
        f"📦 Qismlar: {parts_count} ta\n"
        f"🔢 Kod: {code}"
    )
    
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("◀️ Orqaga", callback_data=f"random_prev:{code}"),
        InlineKeyboardButton("📥 Yuklab olish", callback_data=f"download_anime:{code}"),
        InlineKeyboardButton("Oldinga ▶️", callback_data=f"random_next:{code}")
    )
    
    try:
        media_type = kino.get('media_type', 'photo')
        if media_type == "photo":
            await bot.send_photo(user_id, kino['poster_file_id'], caption=caption, reply_markup=kb)
        elif media_type == "video":
            await bot.send_video(user_id, kino['poster_file_id'], caption=caption, reply_markup=kb)
        else:
            await bot.send_document(user_id, kino['poster_file_id'], caption=caption, reply_markup=kb)
    except Exception as e:
        await bot.send_message(user_id, f"❌ Xatolik: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("random_"))
async def random_navigation(call: types.CallbackQuery):
    action = call.data.split(":")[0]
    
    if action in ["random_next", "random_prev"]:
        random_anime = await get_random_anime(1)
        if random_anime:
            code = random_anime[0]['code']
            user_data[call.from_user.id] = {'random_current_code': code}
            await call.message.delete()
            await show_random_anime(call.from_user.id, code)
        else:
            await call.answer("❌ Anime topilmadi")
    
    await call.answer()

@dp.message_handler(lambda m: m.text == "🏆 10 TOP animelar")
async def top_10_animes(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    # VIP-тексеру осы жерден алып тасталды
    
    top_animes = await get_top_anime(10)
    if not top_animes:
        await message.answer("❌ Hozircha animelar yo'q.")
        return
    
    text = "🏆 TOP 10 ANIMELAR:\n\n"
    kb = InlineKeyboardMarkup(row_width=1)
    
    for idx, anime in enumerate(top_animes, 1):
        title = anime.get('title', 'Noma\'lum')
        viewed = anime.get('viewed', 0)
        code = anime.get('code', '')
        text += f"{idx}. 📺 {title} - 👁 {viewed} ko\'rilgan\n"
        kb.add(InlineKeyboardButton(f"{idx}. {title}", callback_data=f"select_anime:{code}"))
    
    await message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("select_anime:"))
async def select_anime_callback(call: types.CallbackQuery):
    code = call.data.split(":")[1]
    await call.message.delete()
    
    unsubscribed = await get_unsubscribed_channels(call.from_user.id)
    if unsubscribed:
        markup = await make_unsubscribed_markup(call.from_user.id, code)
        await call.message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
    else:
        await send_reklama_post(call.from_user.id, code)
    
    await call.answer()


@dp.message_handler(lambda m: m.text == "🎞 Barcha animelar")
async def show_all_animes(message: types.Message):
    if await is_user_banned(message.from_user.id):
        await message.answer("⛔️ Siz ban qilingan foydalanuvchisiz.")
        return
    
    bot_active = await get_bot_active()
    if not bot_active and message.from_user.id not in ADMINS:
        await message.answer("🚫 Bot hozirda vaqtincha to'xtatilgan.")
        return
    
    kodlar = await get_all_codes()
    if not kodlar:
        await message.answer("⛔️ Hozircha animelar yo'q.")
        return

    kodlar = sorted(kodlar, key=lambda x: int(x["code"]) if x["code"].isdigit() else float('inf'))
    chunk_size = 100
    for i in range(0, len(kodlar), chunk_size):
        chunk = kodlar[i:i + chunk_size]
        text = "📄 *Barcha animelar:*\n\n"
        for row in chunk:
            text += f"`{row['code']}` – *{row['title']}*\n"
        await message.answer(text, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text == "💳 Pul kiritish")
async def payment_menu(message: types.Message):
    card = await get_card_number()
    user_data[message.from_user.id] = {'action': 'payment_upload'}
    await message.answer(
        f"💳 KARTA RAQAMI:\n\n<code>{card}</code>\n\n"
        "📸 To'lov chekini yuboring:\n\n"
        "⚠️ Iltimos, to'lovni amalga oshiring va chek rasmini yuboring.",
        parse_mode="HTML",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.message_handler(lambda m: m.text == "💎 VIP olish")
async def vip_menu(message: types.Message):
    await message.answer("💎 VIP menyusi:", reply_markup=vip_menu_keyboard())


@dp.message_handler(lambda m: m.text == "💎 VIP ga nima kiradi?")
async def vip_info(message: types.Message):
    await message.answer(
        "💎 VIP IMKONIYATLARI:\n\n"
        "✅ Reklama yo'q\n"
        "✅ Kanal obunasiz yuklab olish\n"
        "✅ Janr bo'yicha qidirish\n"
        "✅ Tasodifiy anime tanlash\n"
        "✅ TOP animelarni ko'rish\n"
        "✅ Yangi animelar haqida xabardor bo'lish\n\n"
        "🔥 VIP bo'ling va barcha imkoniyatlardan bahramand bo'ling!"
    )


@dp.message_handler(lambda m: m.text == "💰 VIP sotib olish")
async def buy_vip_menu(message: types.Message):
    prices = await get_vip_prices()
    
    kb = InlineKeyboardMarkup(row_width=1)
    for tariff, info in prices.items():
        price = info['price']
        days = info['days']
        tariff_name = {
            '1month': '1 oylik',
            '3month': '3 oylik',
            '6month': '6 oylik'
        }.get(tariff, tariff)
        kb.add(InlineKeyboardButton(f"💎 {tariff_name} - {price:,} so'm", callback_data=f"buy_vip:{tariff}"))
    
    await message.answer(
        "💎 VIP TARIFLAR:\n\n"
        "Kerakli tarifni tanlang:",
        reply_markup=kb
    )


@dp.callback_query_handler(lambda c: c.data.startswith("buy_vip:"))
async def buy_vip_callback(call: types.CallbackQuery):
    tariff = call.data.split(":")[1]
    prices = await get_vip_prices()
    
    if tariff not in prices:
        await call.answer("❌ Xatolik!", show_alert=True)
        return
    
    price = prices[tariff]['price']
    days = prices[tariff]['days']
    
    card = await get_card_number()
    
    await call.message.answer(
        f"💎 VIP SOTIB OLISH\n\n"
        f"📦 Tarif: {days} kun\n"
        f"💰 Narx: {price:,} so'm\n\n"
        f"💳 Karta raqami:\n<code>{card}</code>\n\n"
        f"📸 To'lov chekini yuboring va admin tasdiqlashi bilan VIP beriladi!",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message_handler(lambda m: m.text == "📦 Buyurtma berish")
async def order_service(message: types.Message):
    user_data[message.from_user.id] = {'action': 'order_service'}
    await message.answer(
        "📦 BUYURTMA BERISH\n\n"
        "Qanday anime yoki xizmat kerakligini yozing.\n"
        "Admin siz bilan bog'lanadi!",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.message_handler(lambda m: m.text == "👤 Profil")
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    profile = await get_user_profile(user_id)
    
    balance = profile.get('balance', 0)
    is_vip = profile.get('is_vip', False)
    vip_until = profile.get('vip_until')
    vip_count = profile.get('vip_count', 0)
    
    vip_status = "💎 VIP" if is_vip else "⭐ Oddiy"
    vip_info = ""
    
    if is_vip and vip_until:
        vip_info = f"\n⏳ VIP tugaydi: {vip_until.strftime('%d.%m.%Y')}"
    
    await message.answer(
        f"👤 PROFIL\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👨‍💼 Ism: {message.from_user.full_name}\n"
        f"📊 Status: {vip_status}{vip_info}\n"
        f"💰 Balans: {balance:,} so'm\n"
        f"🔢 VIP xaridlar: {vip_count} marta",
        parse_mode="HTML"
    )


@dp.message_handler(lambda m: m.text == "✉️ Admin bilan bog'lanish")
async def contact_admin(message: types.Message):
    user_data[message.from_user.id] = {'action': 'contact_admin'}
    await message.answer(
        "✉️ ADMIN BILAN BOG'LANISH\n\n"
        "Xabaringizni yozing, admin javob beradi:",
        reply_markup=back_keyboard() # User menyusi
    )


@dp.callback_query_handler(lambda c: c.data.startswith("reply_user:"))
async def reply_user_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    
    target_user = int(call.data.split(":")[1])
    user_data[call.from_user.id] = {'action': 'reply_to_user', 'target_user': target_user}
    
    await call.message.answer(
        f"✍️ Foydalanuvchiga javob yozish: {target_user}\n\n"
        "Xabaringizni yozing:",
        reply_markup=admin_back_keyboard() # Admin menyusi
    )
    await call.answer()

# --- ADMIN HANDLERS (O'ZGARTIRILGAN) ---

@dp.message_handler(lambda m: m.text == "📋 Kodlar paneli")
async def kodlar_panel_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("📋 Kodlar paneli:", reply_markup=kodlar_panel_keyboard())


@dp.message_handler(lambda m: m.text == "🤖 Bot paneli")
async def bot_panel_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("🤖 Bot paneli:", reply_markup=bot_panel_keyboard())


@dp.message_handler(lambda m: m.text == "📡 Kanal boshqaruvi")
async def channel_management(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📢 Majburiy obuna", callback_data="channel_type:sub"),
        InlineKeyboardButton("📌 Asosiy kanallar", callback_data="channel_type:main")
    )
    
    await message.answer("📡 Kanal boshqaruvi:", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("channel_type:"))
async def select_channel_type(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ctype = callback.data.split(":")[1]
    user_data[callback.from_user.id] = {'channel_type': ctype}
    
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="action:add"),
        InlineKeyboardButton("📋 Kanal ro'yxati", callback_data="action:list")
    )
    kb.add(
        InlineKeyboardButton("❌ Kanal o'chirish", callback_data="action:delete"),
        InlineKeyboardButton("🔙 Orqaga (Admin)", callback_data="action:back_admin")
    )
    
    text = "📡 Majburiy obuna kanallari menyusi:" if ctype == "sub" else "📌 Asosiy kanallar menyusi:"
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("action:"))
async def channel_actions(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    action = callback.data.split(":")[1]
    data = user_data.get(callback.from_user.id, {})
    ctype = data.get("channel_type")

    if not ctype and action != "back_admin":
        await callback.answer("❗ Avval kanal turini tanlang.")
        return

    if action == "add":
        user_data[callback.from_user.id] = {'action': 'add_channel', 'channel_type': ctype, 'step': 'id'}
        await callback.message.answer("🆔 Kanal ID yuboring (masalan: -1001234567890):", reply_markup=admin_back_keyboard())

    elif action == "list":
        await load_channels()
        if ctype == "sub":
            channels = list(zip(CHANNELS, LINKS, CHANNEL_USERNAMES))
            title = "📋 Majburiy obuna kanallari:\n\n"
        else:
            channels = list(zip(MAIN_CHANNELS, MAIN_LINKS, MAIN_USERNAMES))
            title = "📌 Asosiy kanallar:\n\n"

        if not channels:
            await callback.message.answer("📭 Hali kanal yo'q.")
        else:
            text = title
            for i, (cid, link, username) in enumerate(channels, 1):
                text += f"{i}. 🆔 {cid}\n   🔗 {link}\n"
                if username:
                    text += f"   👤 @{username}\n"
                text += "\n"
            await callback.message.answer(text)

    elif action == "delete":
        await load_channels()
        if ctype == "sub":
            channels = list(zip(CHANNELS, LINKS))
            prefix = "del_sub"
        else:
            channels = list(zip(MAIN_CHANNELS, MAIN_LINKS))
            prefix = "del_main"

        if not channels:
            await callback.message.answer("📭 Hali kanal yo'q.")
            return

        kb = InlineKeyboardMarkup()
        for cid, link in channels:
            kb.add(InlineKeyboardButton(f"O'chirish: {cid}", callback_data=f"{prefix}:{cid}"))
        await callback.message.answer("❌ Qaysi kanalni o'chirmoqchisiz?", reply_markup=kb)

    elif action == "back_admin":
        # Inline menyudan Admin paneliga qaytish
        user_data.pop(callback.from_user.id, None)
        await callback.message.delete()
        await callback.message.answer("👮‍♂️ Admin panel:", reply_markup=admin_panel_keyboard())

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("del_sub:") or c.data.startswith("del_main:"))
async def delete_channel_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    
    parts = callback.data.split(":")
    prefix = parts[0]
    channel_id = int(parts[1])
    
    if prefix == "del_sub":
        await delete_channel_from_db(channel_id, 'sub')
        await load_channels()
        await callback.message.answer("✅ Majburiy obuna kanali o'chirildi!")
    else:
        await delete_channel_from_db(channel_id, 'main')
        await load_channels()
        await callback.message.answer("✅ Asosiy kanal o'chirildi!")
    
    await callback.answer()


@dp.message_handler(lambda m: m.text == "❌ Kodni o'chirish")
async def ask_delete_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'delete_code'}
    await message.answer("🗑 Qaysi kodni o'chirmoqchisiz? Kodni yuboring.", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➕ Anime qo'shish")
async def start_add_anime(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_anime', 'step': 'code'}
    await message.answer("📝 Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "🔄 Kodni tahrirlash")
async def start_edit_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'edit_code_select'}
    await message.answer("📝 Qaysi kodni tahrirlamoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "✏️ Postni tahrirlash")
async def start_edit_post(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'edit_post', 'step': 'code'}
    await message.answer("📝 Qaysi anime postini tahrirlamoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "📄 Kodlar ro'yxati")
async def show_all_codes_admin(message: types.Message):
    # Bu endi asosiy admin panelidan chaqiriladi
    if message.from_user.id not in ADMINS:
        return
    kodlar = await get_all_codes()
    if not kodlar:
        await message.answer("⛔️ Hozircha kodlar yo'q.")
        return

    kodlar = sorted(kodlar, key=lambda x: int(x["code"]) if x["code"].isdigit() else float('inf'))
    
    chunk_size = 100
    for i in range(0, len(kodlar), chunk_size):
        chunk = kodlar[i:i + chunk_size]
        text = "📄 *Kodlar ro'yxati:*\n\n"
        for row in chunk:
            text += f"`{row['code']}` – {row['title']}\n"
        await message.answer(text, parse_mode="Markdown")


@dp.message_handler(lambda m: m.text == "📈 Kod statistikasi")
async def ask_stat_code(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'view_stat'}
    await message.answer("📝 Qaysi kod statistikasini ko'rmoqchisiz? Kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    total_users = await get_user_count()
    today_users = await get_today_users()
    active_today = await get_active_today_users()
    weekly_new = await get_weekly_new_users()
    total_codes = len(await get_all_codes())
    vip_users = len(await get_all_vip_users())

    await message.answer(
        f"📊 <b>BOT STATISTIKASI</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"🆕 Bugungi yangi foydalanuvchilar: <b>{today_users}</b>\n"
        f"🟢 Bugun aktiv foydalanuvchilar: <b>{active_today}</b>\n"
        f"📈 1 haftalik yangi foydalanuvchilar: <b>{weekly_new}</b>\n\n"
        f"🎬 Jami anime kodlari: <b>{total_codes}</b>\n"
        f"💎 VIP foydalanuvchilar: <b>{vip_users}</b>\n\n"
        f"🤖 Bot to'liq ishlayapti!",
        parse_mode="HTML"
    )


@dp.message_handler(lambda m: m.text == "👥 Adminlar")
async def admin_management(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("👥 Admin boshqaruvi:", reply_markup=admin_menu_keyboard())


@dp.message_handler(lambda m: m.text == "➕ Admin qo'shish")
async def ask_add_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_admin'}
    await message.answer("👤 Yangi admin ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➖ Admin o'chirish")
async def ask_remove_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'remove_admin'}
    await message.answer("👤 O'chirish kerak bo'lgan admin ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "👥 Adminlar ro'yxati")
async def list_admins(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    admins = await get_all_admins()
    text = "👥 <b>Adminlar ro'yxati:</b>\n\n"
    for admin_id in admins:
        text += f"• <code>{admin_id}</code>\n"
    await message.answer(text, parse_mode="HTML")

# --- BROADCAST (O'ZGARTIRILGAN) ---

async def broadcast_message(admin_message: types.Message, user_ids: list, text: str, group_name: str = "Barcha"):
    if not user_ids:
        await admin_message.answer(f"❌ {group_name} foydalanuvchilar topilmadi.", reply_markup=admin_panel_keyboard())
        return

    success = 0
    failed = 0
    await admin_message.answer(f"📤 Xabar yuborilmoqda... Jami: {len(user_ids)} ta ({group_name}) foydalanuvchi")
    
    for uid in user_ids:
        try:
            # Xabarni HTML yoki Markdown sifatida yuborish o'rniga oddiy matn
            # Yoki message.text o'rniga message.html_text ishlatish kerak
            # Xavfsizlik uchun oddiy matn
            await bot.send_message(uid, f"📢 <b>Xabar:</b>\n\n{text}", parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.05) # 20 msg/sec
        except:
            failed += 1
    
    await admin_message.answer(
        f"✅ Xabar yuborish tugadi! ({group_name})\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}",
        reply_markup=admin_panel_keyboard()
    )

@dp.message_handler(lambda m: m.text == "✉️ Xabar yuborish")
async def start_broadcast_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("Kimga xabar yubormoqchisiz?", reply_markup=admin_broadcast_menu_keyboard())


@dp.message_handler(lambda m: m.text == "👤 Bitta foydalanuvchiga")
async def broadcast_single_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'broadcast_single_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())

@dp.message_handler(lambda m: m.text == "👥 Barcha foydalanuvchilarga")
async def broadcast_all_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'broadcast_all'}
    await message.answer("📝 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:", reply_markup=admin_back_keyboard())

@dp.message_handler(lambda m: m.text == "💎 VIP foydalanuvchilarga")
async def broadcast_vip_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'broadcast_vip'}
    await message.answer("📝 VIP foydalanuvchilarga yuboriladigan xabarni yozing:", reply_markup=admin_back_keyboard())

@dp.message_handler(lambda m: m.text == "⭐️ Oddiy foydalanuvchilarga")
async def broadcast_regular_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'broadcast_regular'}
    await message.answer("📝 Oddiy foydalanuvchilarga yuboriladigan xabarni yozing:", reply_markup=admin_back_keyboard())

# --- END BROADCAST ---

@dp.message_handler(lambda m: m.text == "📤 Post qilish")
async def start_post_process(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'post_to_channel'}
    await message.answer("🔢 Qaysi anime KODini kanalga yubormoqchisiz?\nMasalan: `147`", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "🤖 Bot holati")
async def bot_status_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    bot_active = await get_bot_active()
    status = "✅ Yoqilgan" if bot_active else "⛔️ O'chirilgan"
    await message.answer(f"🤖 Bot holati: {status}\n\nKerakli amalni tanlang:", reply_markup=bot_status_keyboard())


@dp.message_handler(lambda m: m.text == "✅ Botni yoqish")
async def turn_bot_on(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await set_bot_active(True)
    await message.answer("✅ Bot yoqildi! Barcha foydalanuvchilar botdan foydalanishi mumkin.", reply_markup=admin_panel_keyboard())


@dp.message_handler(lambda m: m.text == "⛔️ Botni o'chirish")
async def turn_bot_off(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await set_bot_active(False)
    await message.answer("⛔️ Bot o'chirildi! Faqat adminlar botdan foydalanishi mumkin.", reply_markup=admin_panel_keyboard())


@dp.message_handler(lambda m: m.text == "🚫 User ban qilish")
async def ask_ban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'ban_user'}
    await message.answer("👤 Ban qilish kerak bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "✅ User ban dan chiqarish")
async def ask_unban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'unban_user'}
    await message.answer("👤 Ban dan chiqarish kerak bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "📋 Banlangan userlar")
async def show_banned_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    banned = await get_all_banned_users()
    if not banned:
        await message.answer("✅ Hozircha banlangan foydalanuvchilar yo'q.")
        return
    
    text = "📋 <b>Banlangan foydalanuvchilar:</b>\n\n"
    for user in banned:
        reason = user['reason'] or "Sabab ko'rsatilmagan"
        text += f"👤 ID: <code>{user['user_id']}</code>\n📝 Sabab: {reason}\n\n"
    await message.answer(text, parse_mode="HTML")


@dp.message_handler(lambda m: m.text == "👥 User qo'shish")
async def ask_add_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'add_users'}
    await message.answer(
        "👥 Foydalanuvchi ID larini yuboring.\n\n"
        "📝 Har bir ID ni yangi qatorda yuboring.\n"
        "⚠️ Maksimal 2500 ta ID qo'shishingiz mumkin.\n\n"
        "Misol:\n123456789\n987654321\n555666777",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "💎 VIP boshqaruvi")
async def vip_management_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    await message.answer("💎 VIP boshqaruvi:", reply_markup=vip_management_keyboard())


@dp.message_handler(lambda m: m.text == "➕ VIP berish")
async def ask_give_vip(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_give_vip', 'step': 'user_id'}
    await message.answer("👤 VIP bermoqchi bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "❌ VIP olish")
async def ask_remove_vip_admin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_remove_vip'}
    await message.answer("👤 VIP ni olib tashlamoqchi bo'lgan foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💳 Karta boshqaruvi")
async def ask_card_number(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'update_card'}
    current_card = await get_card_number()
    await message.answer(
        f"💳 Joriy karta raqami:\n<code>{current_card}</code>\n\n"
        "📝 Yangi karta raqamini kiriting:",
        parse_mode="HTML",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "💵 Pul qo'shish")
async def ask_add_balance(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_add_balance', 'step': 'user_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💸 Pul olish")
async def ask_remove_balance(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'admin_remove_balance', 'step': 'user_id'}
    await message.answer("👤 Foydalanuvchi ID sini kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "💰 VIP narxini belgilash")
async def ask_vip_price(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1 oylik", callback_data="set_price:1month"),
        InlineKeyboardButton("3 oylik", callback_data="set_price:3month"),
        InlineKeyboardButton("6 oylik", callback_data="set_price:6month")
    )
    
    await message.answer("💰 Qaysi tarif narxini o'zgartirmoqchisiz?", reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data.startswith("set_price:"))
async def set_vip_price_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    
    tariff = call.data.split(":")[1]
    user_data[call.from_user.id] = {'action': 'update_vip_price', 'tariff': tariff}
    
    tariff_names = {'1month': '1 oylik', '3month': '3 oylik', '6month': '6 oylik'}
    await call.message.answer(
        f"💰 {tariff_names.get(tariff, tariff)} tarifi uchun yangi narxni kiriting (so'mda):",
        reply_markup=admin_back_keyboard()
    )
    await call.answer()


@dp.message_handler(lambda m: m.text == "📋 VIP userlar ro'yxati")
async def list_vip_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    vip_users = await get_all_vip_users()
    if not vip_users:
        await message.answer("❌ Hozircha VIP foydalanuvchilar yo'q.")
        return
    
    text = "💎 <b>VIP FOYDALANUVCHILAR:</b>\n\n"
    for user in vip_users:
        vip_until = user['vip_until'].strftime('%d.%m.%Y')
        text += f"👤 ID: <code>{user['user_id']}</code>\n⏳ Tugaydi: {vip_until}\n\n"
    
    await message.answer(text, parse_mode="HTML")


@dp.message_handler(lambda m: m.text == "💳 To'lov so'rovlari")
async def show_payment_requests(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    
    requests = await get_pending_payment_requests()
    if not requests:
        await message.answer("✅ Hozircha to'lov so'rovlari yo'q.")
        return
    
    await message.answer(f"💳 {len(requests)} ta to'lov so'rovi mavjud:")
    
    for req in requests:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_pay:{req['id']}:{req['user_id']}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_pay:{req['id']}")
        )
        
        await bot.send_photo(
            message.chat.id,
            req['photo_file_id'],
            caption=f"👤 User ID: <code>{req['user_id']}</code>\n📅 Sana: {req['created_at'].strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML",
            reply_markup=kb
        )


@dp.callback_query_handler(lambda c: c.data.startswith("approve_pay:"))
async def approve_payment_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    
    parts = call.data.split(":")
    request_id = int(parts[1])
    user_id = int(parts[2])
    
    user_data[call.from_user.id] = {
        'action': 'approve_payment_amount',
        'request_id': request_id,
        'user_id': user_id
    }
    
    await call.message.answer(
        f"💰 Qancha pul qo'shmoqchisiz? (so'mda)\n\n"
        f"👤 User ID: {user_id}",
        reply_markup=admin_back_keyboard()
    )
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("reject_pay:"))
async def reject_payment_callback(call: types.CallbackQuery):
    if call.from_user.id not in ADMINS:
        return
    
    request_id = int(call.data.split(":")[1])
    await reject_payment_request(request_id)
    
    await call.message.edit_caption(
        caption=call.message.caption + "\n\n❌ RAD ETILDI",
        parse_mode="HTML"
    )
    await call.answer("❌ To'lov rad etildi!")


@dp.message_handler(lambda m: m.text == "🎬 Anime statusi")
async def anime_status_menu(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    user_data[message.from_user.id] = {'action': 'anime_status_code'}
    await message.answer(
        "🎬 ANIME FORWARD STATUSINI BOSHQARISH\n\n"
        "📝 Anime kodini kiriting:",
        reply_markup=admin_back_keyboard()
    )


@dp.message_handler(lambda m: m.text == "🔄 Nomini o'zgartirish")
async def edit_code_name(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    user_data[message.from_user.id] = {'action': 'edit_code_name', 'code': data.get('code'), 'step': 'new_code'}
    await message.answer("📝 Yangi kodni kiriting:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➕ Qisim qo'shish")
async def add_part_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    user_data[message.from_user.id] = {'action': 'add_part', 'code': data.get('code')}
    await message.answer("📂 Qo'shmoqchi bo'lgan qism (video/fayl) ni yuboring:", reply_markup=admin_back_keyboard())


@dp.message_handler(lambda m: m.text == "➖ Qisim o'chirish")
async def delete_part_start(message: types.Message):
    if message.from_user.id not in ADMINS:
        return
    data = user_data.get(message.from_user.id, {})
    if data.get('action') != 'edit_code_menu':
        return
    code = data.get('code')
    kino = await get_kino_by_code(code)
    if not kino:
        await message.answer("❌ Kod topilmadi.")
        return
    
    parts_count = kino.get('post_count', 0)
    if parts_count == 0:
        await message.answer("❌ Bu kodda qismlar yo'q.")
        return
    
    user_data[message.from_user.id] = {'action': 'delete_part', 'code': code}
    await message.answer(
        f"📂 Jami {parts_count} ta qism mavjud.\n\n"
        "🔢 O'chirmoqchi bo'lgan qism raqamini kiriting (masalan: 1, 2, 3...):",
        reply_markup=admin_back_keyboard()
    )

# --- BOSHQA XABARLAR UCHUN HANDLER (O'ZGARTIRILGAN) ---

@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    data = user_data.get(user_id, {})
    action = data.get('action')

    if action == 'search_by_name':
        query = message.text.strip()
        results = await search_anime_by_name(query, limit=20)
        if not results:
            await message.answer("❌ Hech narsa topilmadi. Boshqa nom bilan qidirib ko'ring.")
            return

        user_data.pop(user_id, None)
        kb = InlineKeyboardMarkup(row_width=1)
        for anime in results:
            parts_count = anime.get('post_count', 0)
            kb.add(InlineKeyboardButton(f"{anime['title']} ({parts_count} qisim)", callback_data=f"select_anime:{anime['code']}"))
        
        await message.answer(f"🔎 {len(results)} ta natija topildi. Kerakligini tanlang:", reply_markup=kb)

    elif action == 'search_by_code':
        query = message.text.strip()
        
        if query.isdigit():
            kino = await get_kino_by_code(query)
            if kino:
                user_data.pop(user_id, None)
                unsubscribed = await get_unsubscribed_channels(user_id)
                if unsubscribed:
                    markup = await make_unsubscribed_markup(user_id, query)
                    await message.answer("❗ Animeni olishdan oldin quyidagi kanal(lar)ga obuna bo'ling:", reply_markup=markup)
                else:
                    await increment_stat(query, "init")
                    await increment_stat(query, "searched")
                    await send_reklama_post(user_id, query)
            else:
                await message.answer("❌ Bu kod topilmadi.")
        else:
            await message.answer("❌ Iltimos, faqat raqam kiriting!")

    elif action == 'payment_upload':
        if message.photo:
            photo_file_id = message.photo[-1].file_id
            await add_payment_request(user_id, photo_file_id)
            user_data.pop(user_id, None)
            
            for admin_id in ADMINS:
                try:
                    await bot.send_photo(
                        admin_id,
                        photo_file_id,
                        caption=f"💵 YANGI TO'LOV!\n\n👤 User: @{message.from_user.username or 'no_username'} (ID: {user_id})\n📸 Chek yuborildi\n\nTasdiqlash uchun: 💳 To'lov so'rovlari"
                    )
                except:
                    pass
            
            is_admin = user_id in ADMINS
            await message.answer("✅ To'lov cheki yuborildi! Admin tasdiqlashi bilan balansingizga qo'shiladi.", reply_markup=user_panel_keyboard(is_admin=is_admin))
        else:
            await message.answer("❌ Iltimos, to'lov cheki rasmini yuboring!")

    elif action == 'order_service':
        user_data.pop(user_id, None)
        for admin_id in ADMINS:
            try:
                await bot.send_message(
                    admin_id,
                    f"📦 YANGI BUYURTMA!\n\n👤 User: @{message.from_user.username or 'no_username'} (ID: {user_id})\n💬 Xabar:\n{message.text}"
                )
            except:
                pass
        is_admin = user_id in ADMINS
        await message.answer("✅ Buyurtmangiz yuborildi! Admin siz bilan tez orada bog'lanadi.", reply_markup=user_panel_keyboard(is_admin=is_admin))

    elif action == 'contact_admin':
        user_data.pop(user_id, None)
        for admin_id in ADMINS:
            try:
                keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✉️ Javob yozish", callback_data=f"reply_user:{user_id}"))
                await bot.send_message(
                    admin_id,
                    f"📩 <b>Yangi xabar:</b>\n\n<b>👤 Foydalanuvchi:</b> {message.from_user.full_name} | <code>{user_id}</code>\n<b>💬 Xabar:</b> {message.text}",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except:
                pass
        
        is_admin = user_id in ADMINS
        await message.answer("✅ Xabaringiz yuborildi. Tez orada admin siz bilan bog'lanadi.", 
                           reply_markup=user_panel_keyboard(is_admin=is_admin))

    elif action == 'reply_to_user':
        target = data.get('target_user')
        user_data.pop(user_id, None)
        try:
            await bot.send_message(target, f"✉️ Admindan javob:\n\n{message.text}")
            await message.answer("✅ Javob foydalanuvchiga yuborildi.", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}", reply_markup=admin_panel_keyboard())

    elif action == 'admin_give_vip':
        step = data.get('step')
        if step == 'user_id':
            try:
                vip_user_id = int(message.text.strip())
                user_data[user_id]['vip_user_id'] = vip_user_id
                user_data[user_id]['step'] = 'days'
                await message.answer("⏱ Necha kun VIP bermoqchisiz?", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'days':
            try:
                days = int(message.text.strip())
                vip_user_id = data['vip_user_id']
                await give_vip(vip_user_id, days)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {vip_user_id}\n💎 VIP berildi: {days} kun", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'admin_remove_vip':
        try:
            vip_user_id = int(message.text.strip())
            await remove_vip(vip_user_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ VIP muvaffaqiyatli olindi!\n\n👤 User ID: {vip_user_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'update_card':
        card_number = message.text.strip()
        await set_card_number(card_number)
        user_data.pop(user_id, None)
        await message.answer(f"✅ Yangi karta saqlandi: {card_number}", reply_markup=admin_panel_keyboard())

    elif action == 'admin_add_balance':
        step = data.get('step')
        if step == 'user_id':
            try:
                balance_user_id = int(message.text.strip())
                user_data[user_id]['balance_user_id'] = balance_user_id
                user_data[user_id]['step'] = 'amount'
                await message.answer("💰 Qancha pul qo'shasiz? (so'mda)", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'amount':
            try:
                amount = int(message.text.strip())
                balance_user_id = data['balance_user_id']
                await update_user_balance(balance_user_id, amount)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {balance_user_id}\n💰 Qo'shildi: {amount:,} so'm", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'admin_remove_balance':
        step = data.get('step')
        if step == 'user_id':
            try:
                balance_user_id = int(message.text.strip())
                user_data[user_id]['balance_user_id'] = balance_user_id
                user_data[user_id]['step'] = 'amount'
                await message.answer("💰 Qancha pul olasiz? (so'mda)", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri ID format!")
        elif step == 'amount':
            try:
                amount = int(message.text.strip())
                balance_user_id = data['balance_user_id']
                await update_user_balance(balance_user_id, -amount)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Muvaffaqiyatli!\n\n👤 User ID: {balance_user_id}\n💸 Olindi: {amount:,} so'm", reply_markup=admin_panel_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format!")

    elif action == 'approve_payment_amount':
        try:
            amount = int(message.text.strip())
            request_id = data['request_id']
            target_user = data['user_id']
            
            approved_user = await approve_payment_request(request_id, amount)
            user_data.pop(user_id, None)
            
            if approved_user:
                try:
                    await bot.send_message(
                        target_user,
                        f"✅ To'lovingiz tasdiqlandi!\n\n💰 Balansingizga {amount:,} so'm qo'shildi!"
                    )
                except:
                    pass
                
                await message.answer(
                    f"✅ To'lov tasdiqlandi!\n\n👤 User ID: {target_user}\n💰 Qo'shildi: {amount:,} so'm",
                    reply_markup=admin_panel_keyboard()
                )
            else:
                await message.answer("❌ Xatolik yuz berdi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri format! Raqam kiriting.")
    
    elif action == 'update_vip_price':
        try:
            price = int(message.text.strip())
            tariff = data['tariff']
            await update_vip_price(tariff, price)
            user_data.pop(user_id, None)
            tariff_names = {'1month': '1 oylik', '3month': '3 oylik', '6month': '6 oylik'}
            await message.answer(f"✅ Yangi narx saqlandi!\n\n{tariff_names.get(tariff, tariff)} - {price:,} so'm", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri format! Raqam kiriting.")

    # KANAL QO'SHISH (O'ZGARTIRILGAN)
    elif action == 'add_channel':
        step = data.get('step')
        ctype = data.get('channel_type')
        
        if step == 'id':
            try:
                channel_id = int(message.text.strip())
                user_data[user_id]['channel_id'] = channel_id
                user_data[user_id]['step'] = 'link'
                await message.answer("🔗 Endi kanal HTTPS linkini yuboring (masalan: https://t.me/kanalingiz):", reply_markup=admin_back_keyboard())
            except:
                await message.answer("❌ Noto'g'ri format. Raqam kiriting!")
        
        elif step == 'link':
            channel_link = message.text.strip()
            if not channel_link.startswith('http'):
                await message.answer("❌ Iltimos HTTPS link yuboring! (https://t.me/...)")
                return
            
            user_data[user_id]['channel_link'] = channel_link
            channel_id = data.get('channel_id')
            
            if ctype == 'main':
                # Asosiy kanal uchun username so'raymiz
                user_data[user_id]['step'] = 'username'
                await message.answer("👤 Endi kanal username kiriting (@kanal yoki kanal):", reply_markup=admin_back_keyboard())
            else:
                # Majburiy obuna (sub) uchun username kerak emas, tekshirib saqlaymiz
                try:
                    member = await bot.get_chat_member(channel_id, message.from_user.id)
                    if member.status not in ['administrator', 'creator']:
                        await message.answer("❌ Siz bu kanalda admin emassiz! Kanal qo'shish uchun admin bo'lishingiz kerak.")
                        user_data.pop(user_id, None)
                        return
                    
                    await add_channel_to_db(channel_id, channel_link, ctype, "") # Username bo'sh
                    await load_channels()
                    user_data.pop(user_id, None)
                    await message.answer(f"✅ Majburiy obuna kanali muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())
                except Exception as e:
                    await message.answer(f"❌ Xatolik: {e}\n\nKanal ID to'g'ri va siz admin ekanligingizni tekshiring!")
                    user_data.pop(user_id, None)

        elif step == 'username':
            # Bu qadam faqat ctype == 'main' bo'lganda ishlaydi
            if ctype != 'main':
                user_data.pop(user_id, None) # Xatolik holati
                return 
                
            username = message.text.strip().replace('@', '')
            channel_id = data.get('channel_id')
            channel_link = data.get('channel_link')
            
            try:
                member = await bot.get_chat_member(channel_id, message.from_user.id)
                if member.status not in ['administrator', 'creator']:
                    await message.answer("❌ Siz bu kanalda admin emassiz! Kanal qo'shish uchun admin bo'lishingiz kerak.")
                    user_data.pop(user_id, None)
                    return
                
                await add_channel_to_db(channel_id, channel_link, ctype, username)
                await load_channels()
                user_data.pop(user_id, None)
                await message.answer(f"✅ Asosiy kanal muvaffaqiyatli qo'shildi!\n📌 Username: @{username}", reply_markup=admin_panel_keyboard())
            except Exception as e:
                await message.answer(f"❌ Xatolik: {e}\n\nKanal ID to'g'ri va siz admin ekanligingizni tekshiring!")
                user_data.pop(user_id, None)

    elif action == 'delete_code':
        code = message.text.strip()
        if await delete_kino_code(code):
            user_data.pop(user_id, None)
            await message.answer(f"✅ Kod {code} o'chirildi!", reply_markup=admin_panel_keyboard())
        else:
            await message.answer("❌ Kod topilmadi yoki o'chirishda xatolik.")

    # ANIME QO'SHISH (O'ZGARTIRILGAN - OVOZ BERDI + /SKIP)
    elif action == 'add_anime':
        step = data.get('step')
        
        if step == 'code':
            user_data[user_id]['code'] = message.text.strip()
            user_data[user_id]['step'] = 'title'
            await message.answer("📝 Anime nomini kiriting:", reply_markup=admin_back_keyboard())
        
        elif step == 'title':
            user_data[user_id]['title'] = message.text.strip()
            user_data[user_id]['step'] = 'genre'
            await message.answer("?? Anime janrini kiriting (masalan: Action, Comedy, Drama):", reply_markup=admin_back_keyboard())
        
        elif step == 'genre':
            user_data[user_id]['genre'] = message.text.strip()
            user_data[user_id]['step'] = 'ovoz_berdi'
            await message.answer("🎙 Ovoz bergan studiya/jamoa nomini kiriting (masalan: 'AniLibria')\n\nE'tiborsiz qoldirish uchun /skip yuboring:", reply_markup=admin_back_keyboard())

        elif step == 'ovoz_berdi':
            if message.text == '/skip':
                user_data[user_id]['ovoz_berdi'] = ""
            else:
                user_data[user_id]['ovoz_berdi'] = message.text.strip()
            user_data[user_id]['step'] = 'poster'
            await message.answer("🖼 Poster (rasm yoki video) yuboring:", reply_markup=admin_back_keyboard())

        elif step == 'poster':
            if message.photo:
                user_data[user_id]['poster_file_id'] = message.photo[-1].file_id
                user_data[user_id]['media_type'] = 'photo'
            elif message.video:
                user_data[user_id]['poster_file_id'] = message.video.file_id
                user_data[user_id]['media_type'] = 'video'
            elif message.document:
                user_data[user_id]['poster_file_id'] = message.document.file_id
                user_data[user_id]['media_type'] = 'document'
            else:
                await message.answer("❌ Iltimos rasm, video yoki fayl yuboring!")
                return
            
            user_data[user_id]['step'] = 'parts'
            user_data[user_id]['parts'] = []
            await message.answer("📂 Anime qismlarini yuboring (video yoki fayl). Tugagach /done yuboring:", reply_markup=admin_back_keyboard())
        
        elif step == 'parts':
            if message.text == '/done':
                code = data['code']
                title = data['title']
                poster_file_id = data['poster_file_id']
                parts = data.get('parts', [])
                media_type = data.get('media_type', 'photo')
                genre = data.get('genre', 'Anime')
                ovoz_berdi = data.get('ovoz_berdi', '') # Yangi maydon
                
                channel_username = ""
                if MAIN_USERNAMES and MAIN_USERNAMES[0]:
                    channel_username = MAIN_USERNAMES[0]
                
                await add_anime(code, title, poster_file_id, parts, "", media_type, genre, True, channel_username, ovoz_berdi)
                user_data.pop(user_id, None)
                await message.answer(f"✅ Anime muvaffaqiyatli qo'shildi!\n🎭 Janr: {genre}\n📦 Jami {len(parts)} qisim yuklandi.", reply_markup=admin_panel_keyboard())
            else:
                if message.video:
                    user_data[user_id]['parts'].append(message.video.file_id)
                    await message.answer(f"✅ {len(user_data[user_id]['parts'])}-qism qo'shildi. Davom eting yoki /done yuboring.")
                elif message.document:
                    user_data[user_id]['parts'].append(message.document.file_id)
                    await message.answer(f"✅ {len(user_data[user_id]['parts'])}-qism qo'shildi. Davom eting yoki /done yuboring.")
                else:
                    await message.answer("❌ Iltimos video yoki fayl yuboring!")

    elif action == 'edit_code_select':
        code = message.text.strip()
        kino = await get_kino_by_code(code)
        if not kino:
            await message.answer("❌ Kod topilmadi.")
            return
        
        user_data[user_id] = {'action': 'edit_code_menu', 'code': code}
        await message.answer(
            f"📝 Kod: {code}\n📺 Nomi: {kino['title']}\n\n"
            "Qaysi amalni bajarmoqchisiz?",
            reply_markup=edit_code_menu_keyboard()
        )

    elif action == 'edit_code_name':
        step = data.get('step')
        code = data.get('code')
        
        if step == 'new_code':
            user_data[user_id]['new_code'] = message.text.strip()
            user_data[user_id]['step'] = 'new_title'
            await message.answer("📝 Yangi nomini kiriting:", reply_markup=admin_back_keyboard())
        
        elif step == 'new_title':
            new_code = data['new_code']
            new_title = message.text.strip()
            await update_anime_code(code, new_code, new_title)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Kod va nom muvaffaqiyatli o'zgartirildi!\n\n📝 Yangi kod: {new_code}\n📺 Yangi nom: {new_title}", reply_markup=admin_panel_keyboard())

    elif action == 'add_part':
        code = data.get('code')
        if message.video:
            file_id = message.video.file_id
        elif message.document:
            file_id = message.document.file_id
        else:
            await message.answer("❌ Iltimos video yoki fayl yuboring!")
            return
        
        await add_part_to_anime(code, file_id)
        user_data.pop(user_id, None)
        await message.answer("✅ Qism muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())

    elif action == 'delete_part':
        code = data.get('code')
        try:
            part_number = int(message.text.strip())
            success = await delete_part_from_anime(code, part_number)
            user_data.pop(user_id, None)
            if success:
                await message.answer(f"✅ {part_number}-qism o'chirildi!", reply_markup=admin_panel_keyboard())
            else:
                await message.answer("❌ Noto'g'ri qism raqami.", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Iltimos raqam kiriting!", reply_markup=admin_panel_keyboard())

    elif action == 'edit_post':
        step = data.get('step')
        
        if step == 'code':
            code = message.text.strip()
            kino = await get_kino_by_code(code)
            if not kino:
                await message.answer("❌ Kod topilmadi.")
                return
            
            user_data[user_id]['code'] = code
            user_data[user_id]['step'] = 'new_poster'
            await message.answer("🖼 Yangi poster (rasm yoki video) yuboring yoki /skip:", reply_markup=admin_back_keyboard())
        
        elif step == 'new_poster':
            if message.text == '/skip':
                user_data[user_id]['new_poster'] = None
                user_data[user_id]['new_media_type'] = None
            else:
                if message.photo:
                    user_data[user_id]['new_poster'] = message.photo[-1].file_id
                    user_data[user_id]['new_media_type'] = 'photo'
                elif message.video:
                    user_data[user_id]['new_poster'] = message.video.file_id
                    user_data[user_id]['new_media_type'] = 'video'
                elif message.document:
                    user_data[user_id]['new_poster'] = message.document.file_id
                    user_data[user_id]['new_media_type'] = 'document'
                else:
                    await message.answer("❌ Iltimos rasm, video yoki fayl yuboring!")
                    return
            
            user_data[user_id]['step'] = 'button_text'
            await message.answer("🔘 Tugma matni yuboring (masalan: 'Tomosha qilish') yoki /skip:", reply_markup=admin_back_keyboard())
        
        elif step == 'button_text':
            if message.text == '/skip':
                code = data['code']
                kino = await get_kino_by_code(code)
                poster = data.get('new_poster') or kino['poster_file_id']
                media_type = data.get('new_media_type') or kino['media_type']
                
                await update_anime_poster(code, poster, "", media_type, None, None)
                user_data.pop(user_id, None)
                await message.answer("✅ Post muvaffaqiyatli tahrirlandi!", reply_markup=admin_panel_keyboard())
            else:
                button_text = message.text.strip()
                code = data['code']
                kino = await get_kino_by_code(code)
                
                poster = data.get('new_poster') or kino['poster_file_id']
                media_type = data.get('new_media_type') or kino['media_type']
                button_url = f"https.t.me/{BOT_USERNAME}?start={code}"
                
                await update_anime_poster(code, poster, "", media_type, button_text, button_url)
                user_data.pop(user_id, None)
                await message.answer("✅ Post va tugma muvaffaqiyatli tahrirlandi!", reply_markup=admin_panel_keyboard())

    elif action == 'view_stat':
        code = message.text.strip()
        stat = await get_code_stat(code)
        if stat:
            user_data.pop(user_id, None)
            await message.answer(
                f"📈 Kod {code} statistikasi:\n\n"
                f"🔍 Qidirildi: {stat['searched']} marta\n"
                f"👀 Ko'rildi: {stat['viewed']} marta",
                reply_markup=admin_panel_keyboard()
            )
        else:
            await message.answer("❌ Bu kod uchun statistika topilmadi.")

    elif action == 'add_admin':
        try:
            admin_id = int(message.text.strip())
            await add_admin(admin_id)
            ADMINS.add(admin_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Admin qo'shildi: {admin_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'remove_admin':
        try:
            admin_id = int(message.text.strip())
            if admin_id in START_ADMINS:
                await message.answer("❌ Asosiy adminlarni o'chirib bo'lmaydi!")
                return
            await remove_admin(admin_id)
            ADMINS.discard(admin_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Admin o'chirildi: {admin_id}", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    # YANGI BROADCAST ACTIONLARI
    elif action == 'broadcast_single_id':
        try:
            target_id = int(message.text.strip())
            user_data[user_id] = {'action': 'broadcast_single_message', 'target_id': target_id}
            await message.answer(f"📝 {target_id} ga yuboriladigan xabarni yozing:", reply_markup=admin_back_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")
    
    elif action == 'broadcast_single_message':
        target_id = data.get('target_id')
        user_data.pop(user_id, None)
        try:
            await bot.send_message(target_id, f"📢 <b>Xabar:</b>\n\n{message.text}", parse_mode="HTML")
            await message.answer(f"✅ Xabar {target_id} ga yuborildi.", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xabar yuborilmadi: {e}", reply_markup=admin_panel_keyboard())

    elif action == 'broadcast_all':
        text = message.text
        user_data.pop(user_id, None)
        users = await get_all_user_ids()
        await broadcast_message(message, users, text, "Barcha")

    elif action == 'broadcast_vip':
        text = message.text
        user_data.pop(user_id, None)
        users = await get_all_vip_user_ids()
        await broadcast_message(message, users, text, "VIP")

    elif action == 'broadcast_regular':
        text = message.text
        user_data.pop(user_id, None)
        users = await get_all_regular_user_ids()
        await broadcast_message(message, users, text, "Oddiy")
    
    # ESKI 'broadcast' O'CHIRILDI

        elif action == 'post_to_channel':
        code = message.text.strip()
        kino = await get_kino_by_code(code)
        if not kino:
            await message.answer("❌ Kod topilmadi.")
            return
        
        if not MAIN_CHANNELS:
            await message.answer("❌ Asosiy kanal belgilanmagan! (📡 Kanal boshqaruvi -> 📌 Asosiy kanallar)", reply_markup=admin_panel_keyboard())
            user_data.pop(user_id, None) # Holatni tozalash
            return
        
        # Foydalanuvchi holatini saqlaymiz
        user_data[user_id] = {
            'action': 'post_channel_select', # Bu yangi holat
            'code': code,
            'selected_channels': set() # Boshlang'ich tanlovlar (bo'sh)
        }
        
        # Tanlash menyusini yaratamiz
        keyboard = await generate_channel_selection_keyboard(user_id)
        
        await message.answer(
            f"🎬 Anime: *{kino.get('title', 'Noma\'lum')}*\n\n"
            f"📡 Qaysi asosiy kanal(lar)ga post qilmoqchisiz? Tanlang:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    #HOZ
    elif action == 'ban_user':
        try:
            ban_id = int(message.text.strip())
            if ban_id in ADMINS:
                await message.answer("❌ Adminlarni ban qilib bo'lmaydi!")
                return
            await ban_user(ban_id, "Admin tomonidan ban qilindi")
            user_data.pop(user_id, None)
            await message.answer(f"✅ Foydalanuvchi {ban_id} ban qilindi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'unban_user':
        try:
            unban_id = int(message.text.strip())
            await unban_user(unban_id)
            user_data.pop(user_id, None)
            await message.answer(f"✅ Foydalanuvchi {unban_id} ban dan chiqarildi!", reply_markup=admin_panel_keyboard())
        except:
            await message.answer("❌ Noto'g'ri ID format!")

    elif action == 'add_users':
        try:
            lines = message.text.strip().split('\n')
            user_ids = []
            for line in lines:
                try:
                    user_ids.append(int(line.strip()))
                except:
                    continue
            
            if len(user_ids) > 2500:
                await message.answer(f"❌ Maksimal 2500 ta ID qo'shish mumkin! Siz {len(user_ids)} ta yubordingiz.")
                return
            
            if not user_ids:
                await message.answer("❌ Hech qanday to'g'ri ID topilmadi!")
                return
            
            await add_multiple_users(user_ids)
            user_data.pop(user_id, None)
            await message.answer(f"✅ {len(user_ids)} ta foydalanuvchi muvaffaqiyatli qo'shildi!", reply_markup=admin_panel_keyboard())
        except Exception as e:
            await message.answer(f"❌ Xatolik: {e}")

    elif action == 'anime_status_code':
        if message.text == "🔙 Orqaga":
            return
        
        code = message.text.strip()
        anime = await get_kino_by_code(code)
        
        if not anime:
            await message.answer("❌ Bu kod bilan anime topilmadi!")
            return
        
        forward_enabled = await get_anime_forward_status(code)
        status_text = "✅ ON (Forward ruxsat etilgan)" if forward_enabled else "❌ OFF (Forward taqiqlangan)"
        
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ ON qilish", callback_data=f"anime_fwd_on:{code}"),
            InlineKeyboardButton("❌ OFF qilish", callback_data=f"anime_fwd_off:{code}")
        )
        
        await message.answer(
            f"🎬 Anime: {anime['title']}\n"
            f"🔢 Kod: {code}\n"
            f"📊 Status: {status_text}\n\n"
            f"Forward statusini o\'zgartiring:",
            reply_markup=kb
        )
        user_data.pop(message.from_user.id, None)


@dp.callback_query_handler(lambda c: c.data.startswith("anime_fwd_"))
async def anime_forward_toggle_callback(call: types.CallbackQuery):
    parts = call.data.split(":")
    action = parts[0]
    code = parts[1]
    
    if action == "anime_fwd_on":
        await set_anime_forward_status(code, True)
        await call.message.edit_text("✅ Anime forward statusi ON qilindi!")
    elif action == "anime_fwd_off":
        await set_anime_forward_status(code, False)
        await call.message.edit_text("❌ Anime forward statusi OFF qilindi!")
    
    await call.answer()


async def on_startup(dp):
    await init_db()
    await load_channels()
    admins = await get_all_admins()
    ADMINS.update(admins)
    print("Bot ishga tushdi!")


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
