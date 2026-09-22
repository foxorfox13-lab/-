import telebot
import requests
import time
import random
import sqlite3
import threading
import pytz
import os
import re
import json
import socket
from contextlib import contextmanager
from telebot import types
from datetime import datetime, timedelta, date

# ── استيراد الـ AI Helper ──
try:
    from ai_helper import get_ai_tip
except ImportError:
    def get_ai_tip(text, quotes):
        return random.choice(quotes) if quotes else ""

# ══════════════════════════════════════════════════
#                   الإعدادات الأساسية
# ══════════════════════════════════════════════════
TOKEN    = "8222482155:AAHXIrRgk2zQInWFrZ5JodxIROt9FTi9SCM"
ADMIN_ID = 5676372136
SALAH_LINK = "https://t.me/EVA5X3"
BOT_USERNAME = "Quuran1_bot"

if not TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN is not set!")
if not ADMIN_ID:
    raise ValueError("❌ TELEGRAM_ADMIN_ID is not set!")

bot = telebot.TeleBot(TOKEN, parse_mode=None)
TIMEZONE = pytz.timezone('Africa/Cairo')

_PDF_DIR = '/tmp/quran_pdfs'
os.makedirs(_PDF_DIR, exist_ok=True)

# ══════════════════════════════════════════════════
#                    القراء والسور
# ══════════════════════════════════════════════════
CALM_RECITERS = [
    {"name": "ماهر المعيقلي",  "server": "https://server12.mp3quran.net/maher/"},
    {"name": "ناصر القطامي",   "server": "https://server6.mp3quran.net/qtm/"},
    {"name": "وديع اليمني",    "server": "https://server6.mp3quran.net/wdee3/"},
    {"name": "فارس عباد",      "server": "https://server8.mp3quran.net/frs_a/"},
    {"name": "أحمد النفيس",    "server": "https://server16.mp3quran.net/nufais/Rewayat-Hafs-A-n-Assem/"},
]

MEDIUM_SURAHS = [
    8, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
    43, 44, 45, 46, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 67, 68,
    69, 70, 71, 72, 73, 74, 75, 76, 77, 78
]

SAAY_VERSES = [
    {"text": "﴿ وَأَن لَّيْسَ لِلْإِنسَانِ إِلَّا مَا سَعَىٰ ﴾"},
    {"text": "﴿ وَسَعَىٰ لَهَا سَعْيَهَا وَهُوَ مُؤْمِنٌ فَأُولَٰئِكَ كَانَ سَعْيُهُم مَّشْكُورًا ﴾"},
    {"text": "﴿ إِنَّ الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ إِنَّا لَا نُضِيعُ أَجْرَ مَنْ أَحْسَنَ عَمَلًا ﴾"},
    {"text": "﴿ فَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُ ﴾"},
    {"text": "﴿ إِنَّ اللَّهَ يُحِبُّ الصَّابِرِينَ ﴾"},
    {"text": "﴿ وَمَن يَعْمَلْ مِنَ الصَّالِحَاتِ وَهُوَ مُؤْمِنٌ فَلَا يَخَافُ ظُلْمًا وَلَا هَضْمًا ﴾"},
    {"text": "﴿ إِنَّ اللَّهَ لَا يُضِيعُ أَجْرَ الْمُحْسِنِينَ ﴾"},
    {"text": "﴿ لَا أُضِيعُ عَمَلَ عَامِلٍ مِّنكُم مِّن ذَكَرٍ أَوْ أُنثَىٰ ﴾"},
    {"text": "﴿ وَلَسَوْفَ يُعْطِيكَ رَبُّكَ فَتَرْضَىٰ ﴾"},
    {"text": "﴿ فَإِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾"},
    {"text": "﴿ إِنَّ مَعَ الْعُسْرِ يُسْرًا ﴾"},
    {"text": "﴿ وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا ﴾"},
    {"text": "﴿ وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ ﴾"},
    {"text": "﴿ وَاصْبِرْ فَإِنَّ اللَّهَ لَا يُضِيعُ أَجْرَ الْمُحْسِنِينَ ﴾"},
    {"text": "﴿ إِنَّمَا يُوَفَّى الصَّابِرُونَ أَجْرَهُم بِغَيْرِ حِسَابٍ ﴾"},
    {"text": "﴿ إِنَّ اللَّهَ لَا يُغَيِّرُ مَا بِقَوْمٍ حَتَّىٰ يُغَيِّرُوا مَا بِأَنفُسِهِمْ ﴾"},
    {"text": "﴿ مَنْ عَمِلَ صَالِحًا مِّن ذَكَرٍ أَوْ أُنثَىٰ وَهُوَ مُؤْمِنٌ فَلَنُحْيِيَنَّهُ حَيَاةً طَيِّبَةً ﴾"},
    {"text": "﴿ لَا يُكَلِّفُ اللَّهُ نَفْسًا إِلَّا وُسْعَهَا ﴾"},
    {"text": "﴿ وَقُلِ اعْمَلُوا فَسَيَرَى اللَّهُ عَمَلَكُمْ وَرَسُولُهُ وَالْمُؤْمِنُونَ ﴾"},
    {"text": "﴿ إِنَّ اللَّهَ مَعَ الصَّابِرِينَ ﴾"},
    {"text": "﴿ رَبِّ زِدْنِي عِلْمًا ﴾"},
    {"text": "﴿ رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا ﴾"},
    {"text": "﴿ إِنَّ اللَّهَ يُحِبُّ الْمُتَوَكِّلِينَ ﴾"},
]

SELECTED_AZKAR = [
    "أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ",
    "لَا إِلَهَ إِلَّا اللَّهُ",
    "اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنَّا",
    "اللَّهُمَّ انْفَعْنِي بِمَا عَلَّمْتَنِي\nوَعَلِّمْنِي مَا يَنْفَعُنِي\nوَزِدْنِي عِلْمًا",
    "رَبِّ اشْرَحْ لِي صَدْرِي\nوَيَسِّرْ لِي أَمْرِي\nوَاحْلُلْ عُقْدَةً مِّن لِّسَانِي يَفْقَهُوا قَوْلِي",
    "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا\nوَرِزْقًا طَيِّبًا\nوَعَمَلًا مُتَقَبَّلًا",
    "رَبِّ زِدْنِي عِلْمًا",
    "اللَّهُمَّ لَا سَهْلَ إِلَّا مَا جَعَلْتَهُ سَهْلًا\nوَأَنْتَ تَجْعَلُ الْحَزْنَ إِذَا شِئْتَ سَهْلًا",
    "اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ",
    "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ\nسُبْحَانَ اللَّهِ الْعَظِيمِ",
    "لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ",
    "يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ\nأَصْلِحْ لِي شَأْنِي كُلَّهُ\nوَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ",
    "اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْهَمِّ وَالْحَزَنِ\nوَأَعُوذُ بِكَ مِنَ الْعَجْزِ وَالْكَسَلِ\nوَأَعُوذُ بِكَ مِنَ الْجُبْنِ وَالْبُخْلِ\nوَأَعُوذُ بِكَ مِنْ غَلَبَةِ الدَّيْنِ وَقَهْرِ الرِّجَالِ",
    "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "اللَّهُمَّ اغْفِرْ لِي ذَنْبِي كُلَّهُ\nدِقَّهُ وَجِلَّهُ، وَأَوَّلَهُ وَآخِرَهُ\nوَعَلَانِيَتَهُ وَسِرَّهُ",
    "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ\nنِعْمَ الْمَوْلَىٰ وَنِعْمَ النَّصِيرُ",
]

SAAY_QUOTES = [
    "اعمل لدنياك كأنك تعيش أبدًا ، واعمل لآخرتك كأنك تموت غدًا 🌱",
    "إذا أردت أن تُقيّم نفسك فانظر إلى ما تفعله حين لا يراك أحد 🌱",
    "لا تنظر إلى ما فاتك ، انظر إلى ما أمامك واسعَ إليه 🌱",
    "اجعل نيتك لله … وسيكفيك ما سواه 🌿",
    "كل خطوة صادقة تُكتب … وإن لم يرك أحد 🌿",
    "الهدوء مع الله … بداية القوة 🌿",
    "لا تستعجل الثمرة … ازرع وأحسن الظن 🌿",
    "ما دام قلبك متصلاً بالله فأنت بخير 🌿",
    "الثبات البسيط كل يوم … يصنع فرقًا كبيرًا 🌿",
    "النية الصالحة تُبارك السعي 🌿",
    "ربّك يرى تعبك … فلا تضعف 🌿",
    "الطريق الطويل يُقطع بخطوات صغيرة 🌿",
    "اجتهد بهدوء … فالله لا يضيع شيئًا 🌿",
    "أصلح السريرة … يصلح الله لك العلانية 🌿",
    "ليس المهم السرعة … بل الاستمرار 🌿",
    "حين تثقل عليك الأيام … اقترب من الله أكثر 🌿",
    "القليل الدائم … أحب إلى الله 🌿",
    "ابدأ يومك بنيّة صافية … يكفيك الله بقيته 🌿"
]

FALLBACK_HADITHS = [
    {"arab": "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ", "number": 1, "book": "البخاري"},
    {"arab": "الْمُسْلِمُ مَنْ سَلِمَ الْمُسْلِمُونَ مِنْ لِسَانِهِ وَيَدِهِ", "number": 10, "book": "البخاري"},
    {"arab": "لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ", "number": 13, "book": "البخاري"},
    {"arab": "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الْآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ", "number": 6018, "book": "البخاري"},
    {"arab": "الدِّينُ النَّصِيحَةُ", "number": 55, "book": "مسلم"},
    {"arab": "تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ صَدَقَةٌ", "number": 1956, "book": "الترمذي"},
]

HADITH_BOOKS = {
    'bukhari': 6638, 'muslim': 4930,
    'abu-dawud': 3998, 'tirmidhi': 3956,
    'nasai': 5758, 'ibnmajah': 4341,
}

HADITH_BOOK_NAMES = {
    'bukhari': 'البخاري', 'muslim': 'مسلم',
    'abu-dawud': 'أبو داود', 'tirmidhi': 'الترمذي',
    'nasai': 'النسائي', 'ibnmajah': 'ابن ماجه',
}

FALLBACK_RADIO = [
    {"name": "إذاعة القرآن الكريم - مصر",        "url": "https://backup.qurango.net/radio/quran_cairo"},
    {"name": "إذاعة القرآن الكريم - السعودية",   "url": "https://backup.qurango.net/radio/saudia"},
    {"name": "إذاعة مشاري العفاسي",              "url": "https://backup.qurango.net/radio/shaik_mashary_rashed_alafasy"},
    {"name": "إذاعة أبو بكر الشاطري",            "url": "https://backup.qurango.net/radio/shaik_abu_bakr_al_shatri"},
    {"name": "إذاعة ماهر المعيقلي",              "url": "https://backup.qurango.net/radio/maher_al_mueaqly"},
    {"name": "إذاعة سعد الغامدي",                "url": "https://backup.qurango.net/radio/saad_al_ghamidi"},
    {"name": "إذاعة ناصر القطامي",               "url": "https://backup.qurango.net/radio/nasser_al_qatami"},
    {"name": "إذاعة عبد الباسط عبد الصمد",       "url": "https://backup.qurango.net/radio/abdulbaset_mujawwad"},
]

PRAYER_NAMES  = {'Fajr': 'الفجر', 'Dhuhr': 'الظهر', 'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء'}
PRAYER_EMOJIS = {'Fajr': '🌅', 'Dhuhr': '☀️', 'Asr': '🌤️', 'Maghrib': '🌆', 'Isha': '🌙'}

SAAY_QUOTES_BACKUP = SAAY_QUOTES
CHANNEL_LINK = SALAH_LINK

ARAB_COUNTRIES = {
    "مصر 🇪🇬":          ("Cairo",      "Egypt"),
    "سوريا 🇸🇾":         ("Damascus",   "Syria"),
    "فلسطين 🇵🇸":        ("Jerusalem",  "Palestine"),
    "العراق 🇮🇶":         ("Baghdad",    "Iraq"),
    "السعودية 🇸🇦":       ("Riyadh",     "Saudi Arabia"),
    "الإمارات 🇦🇪":       ("Abu Dhabi",  "United Arab Emirates"),
    "الأردن 🇯🇴":         ("Amman",      "Jordan"),
    "لبنان 🇱🇧":          ("Beirut",     "Lebanon"),
    "الكويت 🇰🇼":         ("Kuwait",     "Kuwait"),
    "قطر 🇶🇦":            ("Doha",       "Qatar"),
    "البحرين 🇧🇭":        ("Manama",     "Bahrain"),
    "عمان 🇴🇲":           ("Muscat",     "Oman"),
    "اليمن 🇾🇪":          ("Sanaa",      "Yemen"),
    "المغرب 🇲🇦":         ("Rabat",      "Morocco"),
    "الجزائر 🇩🇿":        ("Algiers",    "Algeria"),
    "تونس 🇹🇳":           ("Tunis",      "Tunisia"),
    "ليبيا 🇱🇾":          ("Tripoli",    "Libya"),
    "السودان 🇸🇩":         ("Khartoum",   "Sudan"),
    "الصومال 🇸🇴":        ("Mogadishu",  "Somalia"),
    "موريتانيا 🇲🇷":      ("Nouakchott", "Mauritania"),
    "جيبوتي 🇩🇯":         ("Djibouti",   "Djibouti"),
    "جزر القمر 🇰🇲":      ("Moroni",     "Comoros"),
}

def _build_country_lookup():
    lookup = {}
    for full_name in ARAB_COUNTRIES:
        parts = full_name.split()
        key = " ".join(parts[:-1])
        lookup[key] = full_name
        lookup[full_name] = full_name
    return lookup

COUNTRY_LOOKUP = _build_country_lookup()

# ══════════════════════════════════════════════════
#                    قاعدة البيانات
# ══════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect('user_data.db', check_same_thread=False)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        chat_id              INTEGER PRIMARY KEY,
        join_date            REAL,
        khatma_pages_day     INTEGER DEFAULT 20,
        khatma_start         TEXT,
        khatma_current       INTEGER DEFAULT 1,
        khatma_total         INTEGER DEFAULT 569,
        khatma_count         INTEGER DEFAULT 0,
        azkar_daily_enabled  INTEGER DEFAULT 0,
        last_sabah_sent      TEXT    DEFAULT '',
        last_masaa_sent      TEXT    DEFAULT ''
    )''')
    for col, defval in [
        ("khatma_pages_day",      "20"),
        ("khatma_start",          "''"),
        ("khatma_current",        "1"),
        ("khatma_total",          "569"),
        ("khatma_count",          "0"),
        ("azkar_daily_enabled",   "0"),
        ("last_sabah_sent",       "''"),
        ("last_masaa_sent",       "''"),
        ("ward_interval_hours",   "24"),
        ("next_ward_at",          "''"),
        ("ward_reminder_sent",    "0"),
        ("khatma_streak",         "0"),
        ("khatma_missed",         "0"),
        ("khatma_last_read_date", "''"),
        ("ward_pages_day",        "0"),
        ("ward_subscribed",       "0"),
        ("ward_current_page",     "1"),
        ("ward_last_reminded",    "''"),
        ("ward_done_today",       "0"),
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {defval}")
        except Exception:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS group_settings (
        group_id         INTEGER PRIMARY KEY,
        azkar_enabled    INTEGER DEFAULT 1,
        azkar_interval   INTEGER DEFAULT 30,
        last_azkar       REAL    DEFAULT 0,
        ayah_enabled     INTEGER DEFAULT 1,
        ayah_interval    INTEGER DEFAULT 30,
        last_ayah        REAL    DEFAULT 0,
        audio_enabled    INTEGER DEFAULT 1,
        audio_interval   INTEGER DEFAULT 60,
        last_audio       REAL    DEFAULT 0,
        prayer_enabled   INTEGER DEFAULT 0,
        city             TEXT    DEFAULT 'Cairo',
        country          TEXT    DEFAULT 'Egypt',
        last_prayer_time REAL    DEFAULT 0,
        admin_id         INTEGER DEFAULT 0,
        active           INTEGER DEFAULT 1,
        sabah_enabled    INTEGER DEFAULT 1,
        masaa_enabled    INTEGER DEFAULT 1,
        last_sabah_sent  TEXT    DEFAULT '',
        last_masaa_sent  TEXT    DEFAULT ''
    )''')
    for col, defval in [
        ("sabah_enabled",    "1"),
        ("masaa_enabled",    "1"),
        ("last_sabah_sent",  "''"),
        ("last_masaa_sent",  "''"),
        ("last_gdaily_noon", "''"),
        ("last_gdaily_mid",  "''"),
        ("seq_interval",     "30"),
        ("seq_next_idx",     "0"),
        ("last_seq_time",    "0"),
        ("group_name",       "''"),
        ("left_reason",      "''"),
        ("fail_count",       "0"),
    ]:
        try:
            c.execute(f"ALTER TABLE group_settings ADD COLUMN {col} TEXT DEFAULT {defval}")
        except Exception:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS azkar_images (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        type             TEXT NOT NULL,
        file_id          TEXT NOT NULL,
        order_num        INTEGER DEFAULT 0,
        caption          TEXT,
        caption_entities TEXT
    )''')
    for col in ('caption TEXT', 'caption_entities TEXT'):
        try:
            c.execute(f"ALTER TABLE azkar_images ADD COLUMN {col}")
        except Exception:
            pass

    c.execute('''CREATE TABLE IF NOT EXISTS counters (
        message_id  INTEGER PRIMARY KEY,
        chat_id     INTEGER,
        text        TEXT,
        count       INTEGER DEFAULT 0,
        creator_id  INTEGER,
        created_at  REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS counter_clicks (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id      INTEGER,
        user_id         INTEGER,
        last_click_time REAL,
        click_count     INTEGER DEFAULT 0,
        UNIQUE(message_id, user_id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS friday_kahf (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id          TEXT NOT NULL,
        caption          TEXT,
        caption_entities TEXT,
        saved_at         REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS prayer_messages (
        group_id           INTEGER PRIMARY KEY,
        last_reminder_id   INTEGER,
        last_athan_id      INTEGER,
        last_prayer        TEXT,
        last_update        REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS welcome_image (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id  TEXT NOT NULL,
        caption  TEXT,
        caption_entities TEXT,
        saved_at REAL
    )''')

    conn.commit()
    conn.close()

init_db()

# ══════════════════════════════════════════════════
#                   دوال مساعدة للـ DB
# ══════════════════════════════════════════════════
@contextmanager
def db():
    conn = sqlite3.connect('user_data.db', check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def ensure_user(chat_id):
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO users (chat_id, join_date) VALUES (?, ?)", (chat_id, time.time()))

def ensure_group(group_id, admin_id=0, group_name=''):
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO group_settings (group_id, admin_id, group_name) VALUES (?, ?, ?)",
            (group_id, admin_id, group_name)
        )
        if group_name:
            conn.execute(
                "UPDATE group_settings SET group_name=? WHERE group_id=?",
                (group_name, group_id)
            )

def get_group(group_id):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM group_settings WHERE group_id=?", (group_id,))
        row = c.fetchone()
        if not row:
            return None
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))

def get_user(chat_id):
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        row = c.fetchone()
        if not row:
            return None
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))

def get_welcome_image():
    with db() as conn:
        c = conn.cursor()
        c.execute("SELECT file_id, caption, caption_entities FROM welcome_image ORDER BY id DESC LIMIT 1")
        return c.fetchone()

# ══════════════════════════════════════════════════
#                   دوال مساعدة عامة
# ══════════════════════════════════════════════════
def md_safe(text: str) -> str:
    for ch in ('*', '_', '`', '['):
        text = text.replace(ch, f'\\{ch}')
    return text

def entities_to_json(entities) -> str:
    if not entities:
        return None
    result = []
    for e in entities:
        d = {'type': e.type, 'offset': e.offset, 'length': e.length}
        if getattr(e, 'url', None):
            d['url'] = e.url
        result.append(d)
    return json.dumps(result, ensure_ascii=False)

def json_to_entities(json_str):
    if not json_str:
        return None
    try:
        data = json.loads(json_str)
        entities = []
        for d in data:
            e = types.MessageEntity(type=d['type'], offset=d['offset'], length=d['length'])
            if 'url' in d:
                e.url = d['url']
            entities.append(e)
        return entities if entities else None
    except Exception:
        return None

def _get_cairo_date():
    import datetime, zoneinfo
    return datetime.datetime.now(zoneinfo.ZoneInfo("Africa/Cairo")).date().isoformat()

SALAH_BUTTON = lambda: types.InlineKeyboardButton(
    "صلِّ على النبي ﷺ 🤍", url=SALAH_LINK
)

# ══════════════════════════════════════════════════
#              دالة get_ai_tip المحسّنة
# ══════════════════════════════════════════════════
def safe_get_ai_tip(text, quotes):
    """استدعاء الـ AI مع fallback كامل لو فشل"""
    try:
        result = get_ai_tip(text, quotes)
        if result and isinstance(result, str) and len(result.strip()) > 5:
            return result.strip()
    except Exception as e:
        print(f"[AI_Helper] خطأ: {e}")
    # fallback: اختيار عشوائي من الاقتباسات
    return random.choice(quotes) if quotes else ""

# ══════════════════════════════════════════════════
#                      APIs
# ══════════════════════════════════════════════════
_azkar_cache   = {}
_radio_cache   = None
_hadith_cache  = {}
_surah_names_cache = {}

def get_azkar(category_id=27):
    if category_id in _azkar_cache:
        return _azkar_cache[category_id]
    try:
        import json as _json
        url  = f"https://www.hisnmuslim.com/api/ar/{category_id}.json"
        r    = requests.get(url, timeout=10)
        data = _json.loads(r.content.decode('utf-8-sig'))
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    items = v
                    break
        if items:
            _azkar_cache[category_id] = items
            return items
    except Exception as e:
        print(f"[Azkar API] خطأ: {e}")
    return []

def get_random_zikr_text(category_id=None):
    cats = [1, 2, 3, 4, 27] if not category_id else [category_id]
    for cat in [random.choice(cats)]:
        items = get_azkar(cat)
        if items:
            item = random.choice(items)
            if isinstance(item, dict):
                text = item.get('ARABIC_TEXT', item.get('zekr', item.get('text', '')))
                if text:
                    return text
            elif isinstance(item, str) and item:
                return item
    return random.choice(SELECTED_AZKAR)

def get_random_hadith():
    book = random.choice(list(HADITH_BOOKS.keys()))
    if book in _hadith_cache and _hadith_cache[book]:
        h = random.choice(_hadith_cache[book])
        h['_book'] = HADITH_BOOK_NAMES[book]
        return h
    try:
        total = HADITH_BOOKS[book]
        start = random.randint(1, max(1, total - 50))
        url   = f"https://api.hadith.gading.dev/books/{book}?range={start}-{start+49}"
        r     = requests.get(url, timeout=15)
        if r.status_code == 200:
            hadiths = r.json().get('data', {}).get('hadiths', [])
            if hadiths:
                _hadith_cache[book] = hadiths
                h = random.choice(hadiths)
                h['_book'] = HADITH_BOOK_NAMES[book]
                return h
    except Exception as e:
        print(f"[Hadith API] خطأ: {e}")
    h = random.choice(FALLBACK_HADITHS).copy()
    return h

def get_random_ayah():
    try:
        surah_num  = random.randint(1, 114)
        r          = requests.get(f"http://api.alquran.cloud/v1/surah/{surah_num}", timeout=10)
        data       = r.json()
        if data.get('code') == 200:
            ayahs      = data['data']['ayahs']
            ayah       = random.choice(ayahs)
            surah_name = data['data']['name']
            return {
                'text':      ayah['text'],
                'surah':     surah_name,
                'surah_num': surah_num,
                'ayah_num':  ayah['numberInSurah']
            }
    except Exception as e:
        print(f"[Ayah API] خطأ: {e}")
    return random.choice(SAAY_VERSES)

def get_surah_name(surah_num):
    if surah_num in _surah_names_cache:
        return _surah_names_cache[surah_num]
    try:
        r = requests.get(f"https://api.quran.com/api/v4/chapters/{surah_num}?language=ar", timeout=10)
        if r.status_code == 200:
            name = r.json()['chapter']['name_arabic']
            _surah_names_cache[surah_num] = name
            return name
    except Exception:
        pass
    return f"سورة {surah_num}"

def get_radio_stations():
    global _radio_cache
    if _radio_cache:
        return _radio_cache
    try:
        r = requests.get("https://data-rosy.vercel.app/radio.json", timeout=10)
        if r.status_code == 200:
            data     = r.json()
            stations = (data if isinstance(data, list) else
                        data.get('radios') or data.get('stations') or [])
            if stations:
                _radio_cache = stations
                return stations
    except Exception as e:
        print(f"[Radio API] خطأ: {e}")
    _radio_cache = FALLBACK_RADIO
    return FALLBACK_RADIO

def get_prayer_times(city='Cairo', country='Egypt'):
    try:
        r    = requests.get("https://api.aladhan.com/v1/timingsByCity",
                            params={'city': city, 'country': country, 'method': 5}, timeout=10)
        data = r.json()
        if data.get('code') == 200:
            timings = data['data']['timings']
            today   = datetime.now(TIMEZONE).date()
            result  = {}
            for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                h, m = map(int, timings[prayer].split(':'))
                dt = datetime.combine(today, datetime.min.time()).replace(
                    hour=h, minute=m, tzinfo=TIMEZONE)
                result[prayer] = dt
            return result
    except Exception as e:
        print(f"[Prayer API] خطأ: {e}")
    return None

# ══════════════════════════════════════════════════
#   دالة لفحص إذا كان الخطأ يستوجب تعطيل المجموعة
# ══════════════════════════════════════════════════
def _is_fatal_group_error(err_str: str) -> bool:
    """فقط الأخطاء اللي تعني البوت اتطرد فعلاً"""
    fatal_phrases = [
        'chat not found',
        'bot was kicked',
        'bot is not a member',
        'have no rights to send',
        'not enough rights',
        'CHAT_WRITE_FORBIDDEN',
        'bot was blocked by the user',
        'user is deactivated',
    ]
    err_lower = err_str.lower()
    return any(phrase.lower() in err_lower for phrase in fatal_phrases)

# ══════════════════════════════════════════════════
#   بناء رسائل المجموعات - مع الـ AI
# ══════════════════════════════════════════════════
def _clean_for_markdown(text: str) -> str:
    """تنظيف النص من أي رموز Markdown غير متوازنة"""
    cleaned = text
    for ch in ('*', '_', '`'):
        parts = cleaned.split(ch)
        if len(parts) % 2 == 0:
            cleaned = cleaned.replace(ch, ' ')
    return cleaned.strip()

def azkar_message(for_group=False):
    zikr = get_random_zikr_text()
    tip  = safe_get_ai_tip(zikr, SAAY_QUOTES)
    zikr_clean = _clean_for_markdown(md_safe(zikr))
    tip_clean  = _clean_for_markdown(md_safe(tip))
    text = f"*{zikr_clean}*\n\n*{tip_clean}*"
    markup = types.InlineKeyboardMarkup()
    if not for_group:
        markup.add(SALAH_BUTTON())
    return text, markup, 'Markdown'

def saay_verse_message(for_group=False):
    verse      = random.choice(SAAY_VERSES)
    verse_text = verse['text']
    tip        = safe_get_ai_tip(verse_text, SAAY_QUOTES)
    verse_clean = _clean_for_markdown(md_safe(verse_text))
    tip_clean   = _clean_for_markdown(md_safe(tip))
    text = f"*{verse_clean}*\n\n*{tip_clean}*"
    markup = types.InlineKeyboardMarkup()
    if not for_group:
        markup.add(SALAH_BUTTON())
    return text, markup, 'Markdown'

def send_group_audio(group_id):
    reciters     = CALM_RECITERS.copy()
    random.shuffle(reciters)
    surah_num    = random.choice(MEDIUM_SURAHS)
    surah_name   = get_surah_name(surah_num)
    audio_data   = None
    used_reciter = None

    MAX_AUDIO_BYTES = 40 * 1024 * 1024  # 40MB حد أقصى
    for reciter in reciters:
        audio_url = f"{reciter['server']}{surah_num:03d}.mp3"
        try:
            resp = requests.get(audio_url, timeout=20, stream=True)
            if resp.status_code == 200 and 'audio' in resp.headers.get('Content-Type', ''):
                import io as _io_audio
                buf   = _io_audio.BytesIO()
                total = 0
                ok    = True
                for chunk in resp.iter_content(chunk_size=65536):
                    buf.write(chunk)
                    total += len(chunk)
                    if total > MAX_AUDIO_BYTES:
                        ok = False
                        break
                if ok and total > 0:
                    buf.seek(0)
                    audio_data   = buf
                    used_reciter = reciter
                    break
        except Exception as e:
            print(f"[Audio] خطأ تحميل: {e}")
            continue

    if not audio_data or not used_reciter:
        print(f"[Audio] فشل تحميل السورة {surah_num}")
        return False

    caption = (
        f"*سورة* : {surah_name}\n"
        f"*القارئ* : {used_reciter['name']}\n\n"
        f"*اللهم اجعل القرآن ربيع قلوبنا*\n"
        f"*ونور صدورنا وجلاء أحزاننا 🌱*"
    )
    try:
        audio_data.name = f"{surah_name}.mp3"
        bot.send_audio(group_id, audio_data,
                       caption=caption, title=surah_name,
                       performer=used_reciter['name'],
                       parse_mode='Markdown',
                       timeout=120)
        return True
    except Exception as e:
        print(f"[Audio] فشل الإرسال للمجموعة {group_id}: {e}")
        return False

# ══════════════════════════════════════════════════
#     الجدولة الموحدة للمجموعات
# ══════════════════════════════════════════════════
MAX_FAIL_BEFORE_DEACTIVATE = 3   # عدد الإخفاقات قبل التعطيل النهائي

def _is_immediately_fatal(err_str: str) -> bool:
    """أخطاء تعني إن البوت اتطرد أو الجروب اتحذف — نوقف فوراً"""
    phrases = ['chat not found', 'bot was kicked', 'bot is not a member',
               'bot was blocked by the user', 'user is deactivated']
    el = err_str.lower()
    return any(p in el for p in phrases)

def _is_soft_fatal(err_str: str) -> bool:
    """أخطاء صلاحيات — نجرب مرات قبل ما نوقف"""
    phrases = ['have no rights to send', 'not enough rights',
               'CHAT_WRITE_FORBIDDEN', 'forbidden']
    el = err_str.lower()
    return any(p.lower() in el for p in phrases)

def _handle_group_error(gid, err_str):
    """يقرر هيوقف فوراً أو يزود العداد أو يتجاهل"""
    if _is_immediately_fatal(err_str):
        el = err_str.lower()
        if 'kicked'       in el: reason = "تم طرد البوت ❌"
        elif 'not a member' in el: reason = "البوت مش عضو ❌"
        elif 'chat not found' in el: reason = "المجموعة غير موجودة ❌"
        else:                      reason = "البوت اتحجب ❌"
        with db() as conn:
            conn.execute(
                "UPDATE group_settings SET active=0, left_reason=?, fail_count=0 WHERE group_id=?",
                (reason, gid)
            )
        print(f"[Scheduler] تعطيل فوري {gid} — {reason}")
        return False

    if _is_soft_fatal(err_str):
        with db() as conn:
            row = conn.execute(
                "SELECT fail_count FROM group_settings WHERE group_id=?", (gid,)
            ).fetchone()
            fail = int(row[0] or 0) + 1 if row else 1
            if fail >= MAX_FAIL_BEFORE_DEACTIVATE:
                conn.execute(
                    "UPDATE group_settings SET active=0, left_reason=?, fail_count=0 WHERE group_id=?",
                    ("البوت يحتاج صلاحية مشرف للإرسال ⚠️", gid)
                )
                print(f"[Scheduler] تعطيل {gid} بعد {fail} محاولات فاشلة")
                return False
            else:
                conn.execute(
                    "UPDATE group_settings SET fail_count=? WHERE group_id=?", (fail, gid)
                )
                print(f"[Scheduler] خطأ صلاحيات {gid} (محاولة {fail}/{MAX_FAIL_BEFORE_DEACTIVATE})")
        return False

    # خطأ مؤقت — سيحاول مرة أخرى تلقائياً
    print(f"[Scheduler] خطأ مؤقت {gid}: {err_str[:80]}")
    return False

def _safe_send_to_group(gid, text, markup, pmode):
    """إرسال آمن للمجموعة مع fallback للـ plain text و Retry-After"""
    try:
        bot.send_message(gid, text, reply_markup=markup, parse_mode=pmode)
        with db() as conn:
            conn.execute("UPDATE group_settings SET fail_count=0 WHERE group_id=?", (gid,))
        return True
    except Exception as send_err:
        err_str = str(send_err)
        # Flood control: 429 Too Many Requests — ننتظر وبعدين نحاول مرة واحدة
        if 'retry after' in err_str.lower():
            try:
                wait = int(re.search(r'retry after (\d+)', err_str.lower()).group(1))
            except Exception:
                wait = 5
            print(f"[Flood] تأخير {wait+1}ث للمجموعة {gid}")
            time.sleep(wait + 1)
            try:
                bot.send_message(gid, text, reply_markup=markup, parse_mode=pmode)
                with db() as conn:
                    conn.execute("UPDATE group_settings SET fail_count=0 WHERE group_id=?", (gid,))
                return True
            except Exception as e2:
                return _handle_group_error(gid, str(e2))
        if "can't parse entities" in err_str or "parse" in err_str.lower():
            plain = text.replace('*', '').replace('_', '').replace('`', '')
            try:
                bot.send_message(gid, plain, reply_markup=markup)
                with db() as conn:
                    conn.execute("UPDATE group_settings SET fail_count=0 WHERE group_id=?", (gid,))
                return True
            except Exception as e2:
                return _handle_group_error(gid, str(e2))
        return _handle_group_error(gid, err_str)

def group_scheduler():
    print("✅ بدء جدولة المجموعات...")
    SEQ_TYPES = ['azkar', 'ayah', 'audio']
    while True:
        try:
            now = time.time()
            with db() as conn:
                c      = conn.cursor()
                c.execute("SELECT * FROM group_settings WHERE active=1")
                cols   = [d[0] for d in c.description]
                groups = [dict(zip(cols, row)) for row in c.fetchall()]

            for g in groups:
                gid = g['group_id']
                try:
                    seq_interval = int(g.get('seq_interval') or 30) * 60
                    last_seq     = float(g.get('last_seq_time') or 0)
                    seq_next     = int(g.get('seq_next_idx') or 0)

                    if now - last_seq < seq_interval:
                        continue

                    enabled = {
                        'azkar': bool(int(g.get('azkar_enabled') or 1)),
                        'ayah':  bool(int(g.get('ayah_enabled')  or 1)),
                        'audio': bool(int(g.get('audio_enabled') or 1)),
                    }

                    sent = False
                    for i in range(3):
                        idx   = (seq_next + i) % 3
                        stype = SEQ_TYPES[idx]
                        if not enabled[stype]:
                            continue
                        if stype == 'azkar':
                            text, markup, pmode = azkar_message(for_group=True)
                            _safe_send_to_group(gid, text, markup, pmode)
                        elif stype == 'ayah':
                            text, markup, pmode = saay_verse_message(for_group=True)
                            _safe_send_to_group(gid, text, markup, pmode)
                        else:
                            send_group_audio(gid)
                            time.sleep(1)
                        new_idx = (idx + 1) % 3
                        with db() as conn:
                            conn.execute(
                                "UPDATE group_settings SET last_seq_time=?, seq_next_idx=? WHERE group_id=?",
                                (now, new_idx, gid)
                            )
                        sent = True
                        time.sleep(1)
                        break

                except Exception as e:
                    _handle_group_error(gid, str(e))

        except Exception as e:
            print(f"[Scheduler] خطأ عام: {e}")

        time.sleep(60)

# ══════════════════════════════════════════════════
#       إعدادات المجموعة (نصوص وأزرار)
# ══════════════════════════════════════════════════
def group_settings_text(g):
    def onoff(v):
        return "✅ مفعّل" if v else "❌ موقف"
    seq_interval = int(g.get('seq_interval') or 30)
    if seq_interval < 60:
        interval_str = f"كل {seq_interval} دقيقة"
    else:
        h = seq_interval // 60
        interval_str = f"كل {h} ساعة" if h == 1 else f"كل {h} ساعات"
    seq_next = int(g.get('seq_next_idx') or 0)
    next_labels = {0: '📿 ذكر', 1: '📖 آية', 2: '🎙️ تلاوة'}
    next_label  = next_labels.get(seq_next, '📿 ذكر')
    return (
        f"*إعدادات البوت في المجموعة ⚙.*\n\n"
        f"- الأذكار : {onoff(g['azkar_enabled'])}\n"
        f"- آيات قرآنيـة : {onoff(g['ayah_enabled'])}\n"
        f"- تلاوة قرآنية : {onoff(g['audio_enabled'])}\n"
        f"- تنبيه ما قبل الصلاة : {onoff(g['prayer_enabled'])}\n\n"
        f"⏱️ *فترة الإرسال :* {interval_str}\n"
        f"🔄 *الرسالة القادمة :* {next_label}\n"
        f"📋 *التسلسل :* ذكر ← آية ← تلاوة ← تكرار\n\n"
        f"*يمكنك تعديل الإعدادات من الأزرار أدناه 👇.*"
    )

def group_settings_markup(g):
    mk          = types.InlineKeyboardMarkup(row_width=2)
    azkar_icon  = "✅" if g['azkar_enabled']  else "❌"
    ayah_icon   = "✅" if g['ayah_enabled']   else "❌"
    audio_icon  = "✅" if g['audio_enabled']  else "❌"
    prayer_icon = "✅" if g['prayer_enabled'] else "❌"
    mk.add(
        types.InlineKeyboardButton(f"{azkar_icon} الأذكار",  callback_data=f"gs_toggle:azkar:{g['group_id']}"),
        types.InlineKeyboardButton(f"{ayah_icon} الآيات",   callback_data=f"gs_toggle:ayah:{g['group_id']}")
    )
    mk.add(
        types.InlineKeyboardButton(f"{audio_icon} التلاوة", callback_data=f"gs_toggle:audio:{g['group_id']}"),
        types.InlineKeyboardButton(f"{prayer_icon} الصلاة", callback_data=f"gs_toggle:prayer:{g['group_id']}")
    )
    mk.row(types.InlineKeyboardButton("⏱️ تغيير فترة الإرسال", callback_data=f"gs_time:seq:{g['group_id']}"))
    mk.row(types.InlineKeyboardButton("📍 تغيير المدينة (صلاة)", callback_data=f"gs_city:{g['group_id']}"))
    mk.row(types.InlineKeyboardButton("الرجوع إلى الإعدادات الرئيسية 🔄", callback_data=f"gs_reset:{g['group_id']}"))
    return mk

def interval_markup(feature, group_id, is_audio=False):
    opts = [15, 30, 45, 60, 90, 120]
    mk   = types.InlineKeyboardMarkup(row_width=3)
    btns = []
    for mins in opts:
        label = f"{mins} د" if mins < 60 else f"{mins//60} س"
        btns.append(types.InlineKeyboardButton(label, callback_data=f"gs_settime:{feature}:{group_id}:{mins}"))
    mk.add(*btns)
    mk.row(types.InlineKeyboardButton("✏️ وقت مخصص (مثال: 20m أو 2h)", callback_data=f"gs_custom:{feature}:{group_id}"))
    mk.row(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_back:{group_id}"))
    return mk

def country_markup_group(group_id):
    mk = types.InlineKeyboardMarkup(row_width=2)
    priority = ["مصر 🇪🇬", "سوريا 🇸🇾", "فلسطين 🇵🇸", "العراق 🇮🇶", "السعودية 🇸🇦"]
    rows_priority = []
    for i in range(0, len(priority), 2):
        row = []
        for name in priority[i:i+2]:
            capital, country_en = ARAB_COUNTRIES[name]
            row.append(types.InlineKeyboardButton(
                name,
                callback_data=f"gs_setcountry:{group_id}:{capital}:{country_en}"
            ))
        rows_priority.append(row)
    for row in rows_priority:
        mk.row(*row)

    others = [n for n in ARAB_COUNTRIES if n not in priority]
    for i in range(0, len(others), 2):
        row = []
        for name in others[i:i+2]:
            capital, country_en = ARAB_COUNTRIES[name]
            row.append(types.InlineKeyboardButton(
                name,
                callback_data=f"gs_setcountry:{group_id}:{capital}:{country_en}"
            ))
        mk.row(*row)

    mk.row(types.InlineKeyboardButton("🔙 رجوع", callback_data=f"gs_back:{group_id}"))
    return mk

def parse_interval(text: str):
    text = text.strip().lower().replace(' ', '')
    m    = re.fullmatch(r'(\d+)\s*([mhدسsMH]?)', text)
    if not m:
        return None
    val  = int(m.group(1))
    unit = m.group(2)
    if unit in ('h', 'H', 'س'):
        val *= 60
    if val < 5 or val > 720:
        return None
    return val

def extract_page_number(text):
    if not text:
        return None
    m = re.search(r'page[_\-](\d+)', text, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 569:
            return n
    m = re.search(r'(\d+)', text)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 569:
            return n
    return None

# ══════════════════════════════════════════════════
#              نظام التلاوات القرآنية
# ══════════════════════════════════════════════════
SURAH_NAMES: dict = {
    "الفاتحة": 1,   "البقرة": 2,    "آل عمران": 3,  "النساء": 4,    "المائدة": 5,
    "الأنعام": 6,   "الأعراف": 7,   "الأنفال": 8,   "التوبة": 9,    "يونس": 10,
    "هود": 11,      "يوسف": 12,     "الرعد": 13,    "إبراهيم": 14,  "الحجر": 15,
    "النحل": 16,    "الإسراء": 17,  "الكهف": 18,    "مريم": 19,     "طه": 20,
    "الأنبياء": 21, "الحج": 22,     "المؤمنون": 23, "النور": 24,    "الفرقان": 25,
    "الشعراء": 26,  "النمل": 27,    "القصص": 28,    "العنكبوت": 29, "الروم": 30,
    "لقمان": 31,    "السجدة": 32,   "الأحزاب": 33,  "سبأ": 34,      "فاطر": 35,
    "يس": 36,       "الصافات": 37,  "ص": 38,         "الزمر": 39,    "غافر": 40,
    "فصلت": 41,     "الشورى": 42,   "الزخرف": 43,   "الدخان": 44,   "الجاثية": 45,
    "الأحقاف": 46,  "محمد": 47,     "الفتح": 48,    "الحجرات": 49,  "ق": 50,
    "الذاريات": 51, "الطور": 52,    "النجم": 53,    "القمر": 54,    "الرحمن": 55,
    "الواقعة": 56,  "الحديد": 57,   "المجادلة": 58, "الحشر": 59,    "الممتحنة": 60,
    "الصف": 61,     "الجمعة": 62,   "المنافقون": 63,"التغابن": 64,  "الطلاق": 65,
    "التحريم": 66,  "الملك": 67,    "القلم": 68,    "الحاقة": 69,   "المعارج": 70,
    "نوح": 71,      "الجن": 72,     "المزمل": 73,   "المدثر": 74,   "القيامة": 75,
    "الإنسان": 76,  "المرسلات": 77, "النبأ": 78,    "النازعات": 79, "عبس": 80,
    "التكوير": 81,  "الانفطار": 82, "المطففين": 83, "الانشقاق": 84, "البروج": 85,
    "الطارق": 86,   "الأعلى": 87,   "الغاشية": 88,  "الفجر": 89,    "البلد": 90,
    "الشمس": 91,    "الليل": 92,    "الضحى": 93,    "الشرح": 94,    "التين": 95,
    "العلق": 96,    "القدر": 97,    "البينة": 98,   "الزلزلة": 99,  "العاديات": 100,
    "القارعة": 101, "التكاثر": 102, "العصر": 103,   "الهمزة": 104,  "الفيل": 105,
    "قريش": 106,    "الماعون": 107, "الكوثر": 108,  "الكافرون": 109,"النصر": 110,
    "المسد": 111,   "الإخلاص": 112, "الفلق": 113,   "الناس": 114,
    "الاسراء": 17,  "الاحزاب": 33,  "الانفال": 8,   "براءة": 9,
    "الصمد": 112,   "تبارك": 67,
}

KNOWN_RECITERS = [
    {"name": "مشاري راشد العفاسي",   "aliases": ["العفاسي", "مشاري", "عفاسي"],
     "server": "https://server8.mp3quran.net/afs/",   "islamic_ed": "ar.alafasy"},
    {"name": "عبد الباسط عبد الصمد", "aliases": ["عبد الباسط", "عبدالباسط", "الباسط"],
     "server": "https://server7.mp3quran.net/basit/",  "islamic_ed": "ar.abdulbasitmurattal"},
    {"name": "محمود خليل الحصري",    "aliases": ["الحصري", "حصري"],
     "server": "https://server13.mp3quran.net/husr/",  "islamic_ed": "ar.husary"},
    {"name": "محمد صديق المنشاوي",   "aliases": ["المنشاوي", "منشاوي"],
     "server": "https://server10.mp3quran.net/minsh/", "islamic_ed": "ar.minshawi"},
    {"name": "عبد الرحمن السديس",     "aliases": ["السديس", "سديس"],
     "server": "https://server11.mp3quran.net/sds/",   "islamic_ed": "ar.abdurrahmaansudais"},
    {"name": "سعود الشريم",           "aliases": ["الشريم", "شريم"],
     "server": "https://server7.mp3quran.net/shur/",   "islamic_ed": None},
    {"name": "ماهر المعيقلي",         "aliases": ["ماهر", "المعيقلي", "معيقلي"],
     "server": "https://server12.mp3quran.net/maher/", "islamic_ed": None},
    {"name": "ناصر القطامي",          "aliases": ["القطامي", "قطامي"],
     "server": "https://server6.mp3quran.net/qtm/",    "islamic_ed": None},
    {"name": "إدريس أبكر",           "aliases": ["أبكر", "ادريس", "إدريس"],
     "server": "https://server15.mp3quran.net/abkr/",  "islamic_ed": None},
    {"name": "سعد الغامدي",           "aliases": ["الغامدي", "غامدي", "سعد"],
     "server": "https://server7.mp3quran.net/s_gmd/",  "islamic_ed": "ar.saoodshuraym"},
    {"name": "فارس عباد",             "aliases": ["فارس"],
     "server": "https://server8.mp3quran.net/frs_a/",  "islamic_ed": None},
    {"name": "أحمد العجمي",           "aliases": ["العجمي", "عجمي"],
     "server": "https://server10.mp3quran.net/ajm/",   "islamic_ed": None},
    {"name": "وديع اليمني",           "aliases": ["وديع", "اليمني"],
     "server": "https://server6.mp3quran.net/wdee3/",  "islamic_ed": None},
    {"name": "ياسر الدوسري",          "aliases": ["الدوسري", "دوسري", "ياسر"],
     "server": "https://server11.mp3quran.net/yasser/","islamic_ed": None},
    {"name": "هاني الرفاعي",          "aliases": ["الرفاعي", "رفاعي", "هاني"],
     "server": "https://server8.mp3quran.net/hani/",   "islamic_ed": None},
    {"name": "محمد جبريل",            "aliases": ["جبريل"],
     "server": "https://server8.mp3quran.net/jbrl/",   "islamic_ed": None},
]

_mp3quran_reciters_cache = None

def _get_mp3quran_reciters():
    global _mp3quran_reciters_cache
    if _mp3quran_reciters_cache is not None:
        return _mp3quran_reciters_cache
    try:
        r = requests.get("http://www.mp3quran.net/api/_arabic.json", timeout=8)
        data = r.json()
        _mp3quran_reciters_cache = data.get("reciters", [])
    except Exception:
        _mp3quran_reciters_cache = []
    return _mp3quran_reciters_cache

def _normalize_ar(text: str) -> str:
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ة','ه').replace('ى','ي').replace('ئ','ي')
    text = text.replace('ؤ','و')
    return text.strip()

def _find_surah_num(text: str):
    text_clean = _normalize_ar(text)
    padded     = f" {text_clean} "
    best_match = None
    for name, num in SURAH_NAMES.items():
        n       = _normalize_ar(name)
        pattern = rf'(?<![ا-ي]){re.escape(n)}(?![ا-ي])'
        if re.search(pattern, padded):
            if best_match is None or len(n) > best_match[0]:
                best_match = (len(n), num)
    return best_match[1] if best_match else None

def _words(text: str):
    return [w for w in re.split(r'\s+', _normalize_ar(text)) if len(w) > 2]

def _score_match(query_words, target_norm: str) -> int:
    return sum(1 for w in query_words if w in target_norm)

def _find_reciter(text: str):
    qwords = _words(text)
    if not qwords:
        return None
    best = (0, None)
    for rec in KNOWN_RECITERS:
        target = _normalize_ar(rec["name"]) + " " + " ".join(_normalize_ar(a) for a in rec["aliases"])
        sc     = _score_match(qwords, target)
        if sc > best[0]:
            best = (sc, rec)
    api_list = _get_mp3quran_reciters()
    for rec_api in api_list:
        target = _normalize_ar(rec_api.get("name", ""))
        if not target:
            continue
        sc = _score_match(qwords, target)
        if sc > best[0]:
            best = (sc, {"name": rec_api["name"], "server": rec_api.get("Server",""),
                         "aliases": [], "islamic_ed": None})
    return best[1] if best[0] > 0 else None

def _check_url(url: str) -> bool:
    try:
        hdrs = {"User-Agent": "Mozilla/5.0"}
        r    = requests.head(url, headers=hdrs, timeout=6, allow_redirects=True)
        return r.status_code in (200, 206)
    except Exception:
        return False

def _fetch_audio_url(surah_num: int, reciter):
    sura3 = f"{surah_num:03d}"
    if reciter and reciter.get("server"):
        url = reciter["server"] + sura3 + ".mp3"
        if _check_url(url):
            return url, reciter["name"]
    if reciter and reciter.get("islamic_ed"):
        url = f"https://cdn.islamic.network/quran/audio-surah/128/{reciter['islamic_ed']}/{surah_num}.mp3"
        if _check_url(url):
            return url, reciter["name"]
    fallback_editions = [
        ("ar.alafasy",            "مشاري راشد العفاسي"),
        ("ar.abdulbasitmurattal", "عبد الباسط عبد الصمد"),
        ("ar.husary",             "محمود خليل الحصري"),
        ("ar.minshawi",           "محمد صديق المنشاوي"),
        ("ar.abdurrahmaansudais", "عبد الرحمن السديس"),
    ]
    for edition, name in fallback_editions:
        url = f"https://cdn.islamic.network/quran/audio-surah/128/{edition}/{surah_num}.mp3"
        if _check_url(url):
            return url, name
    return None, ""

_tilawa_waiting: dict = {}

# ══════════════════════════════════════════════════
#         نظام الورد اليومي
# ══════════════════════════════════════════════════
QURAN_PAGES        = 569
_ward_pages_waiting: dict = {}
_ward_start_waiting: dict = {}    # chat_id → pages (ينتظر اختيار اليوم أم غداً)

def ward_welcome_text():
    return (
        "أهلاً بك يا بطل ....! هذه مبادرة مباركة ومشرقة ، ويسعدني جداً أن أكون رفيقك في هذا الدرب النبيل 🌱.\n"
        "بما أنني بوت ، ربما لا أملك قلباً كالبشر لأتأثر بالورد كما تتأثر به أنت ، لكنني أملك الالتزام الكامل والمثابرة الرقمية التي ستضمن لك ألا تفوت يوماً واحداً دون أن أذكرك بمهمتك الأساسية 🌟.\n"
        "خطة العمل 🔻:\n"
        "*سأكون* المُنبه الذي لا يغفل والمشجع الذي ينتظر إنجازك بفارغ الصبر ، اعتبرني مساعدك الشخصي في رحلة الاستمرار هذه\n"
        "*مهمتي* : تذكيرك بالورد اليومي في الموعد الذي تفضله .\n"
        "*الهدف* : أن تصبح المداومة صفة راسخة في يومك .\n\n"
        "*لكي أكون فعالاً معك ، اضغط موافق ! ( اختر من الازرار في الاسفل 👇 )*"
    )

def ward_welcome_markup():
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("حسنا ، موافق ☑️",      callback_data="ward_agree"),
        types.InlineKeyboardButton("لا اريد ، رجوع ‼️", callback_data="khatma_back")
    )
    return mk

def ward_already_subscribed_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("بدء ورد جديد 🌟", callback_data="ward_new_start"))
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    return mk

def ward_ask_pages_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="ward_cancel"))
    return mk

def ward_confirmed_markup():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    return mk

def calc_khatma_finish(pages_day):
    from datetime import date, timedelta
    days   = -(-QURAN_PAGES // pages_day)
    finish = date.today() + timedelta(days=days)
    return finish.strftime('%d/%m/%Y')

def _quran_page_url(page: int) -> str:
    """رابط مباشر لصفحة المصحف على موقع quran.com — وضع Reading"""
    return f"https://quran.com/page/{max(1, min(page, QURAN_PAGES))}?reading=true"


def send_ward_daily_reminder(chat_id):
    u = get_user(chat_id)
    if not u:
        return
    pages_day = int(u.get('ward_pages_day') or 0)
    current_p = int(u.get('ward_current_page') or 1)
    if pages_day <= 0:
        return
    end_page = min(current_p + pages_day - 1, QURAN_PAGES)
    pages_word = "صفحة" if pages_day == 1 else "صفحات" if pages_day <= 10 else "صفحة"
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton(
        f"📖  افتح المصحف — الصفحة {current_p}",
        web_app=types.WebAppInfo(url=_quran_page_url(current_p))
    ))
    mk.add(types.InlineKeyboardButton("✅  أنهيت وردي", callback_data="ward_done"))
    try:
        bot.send_message(
            chat_id,
            f"يلا بينا نكمل وردنا اليوم! 🤍\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📖  من الصفحة *{current_p}*  إلى الصفحة *{end_page}*\n"
            f"📚  {pages_day} {pages_word} — وردك اليوم\n\n"
            f"اضغط الزر أدناه لفتح المصحف على الصفحة الصحيحة مباشرة 🌱\n"
            f"_عند الانتهاء اضغط «أنهيت وردي» لأذكّرك غداً ✨_",
            reply_markup=mk,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"[WardReminder] خطأ للمستخدم {chat_id}: {e}")

# ══════════════════════════════════════════════════
#        نظام ختمة القرآن (الصفحات)
# ══════════════════════════════════════════════════
_import_waiting: dict = {}

def khatma_menu_markup(chat_id=None):
    if chat_id:
        u       = get_user(chat_id)
        enabled = u.get('azkar_daily_enabled', 0) if u else 0
    else:
        u       = None
        enabled = 0

    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(types.InlineKeyboardButton("الورد اليومي 🌱", callback_data="ward_open"))
    mk.row(
        types.InlineKeyboardButton("أذكارك 🌱",         callback_data="show_azkar"),
        types.InlineKeyboardButton("آيات وتفسيرها 🌱", callback_data="ayah_refresh"),
    )
    mk.row(types.InlineKeyboardButton("تنزيل مقاطع سور قرانية 🌱", callback_data="tilawa_start"))
    if enabled:
        mk.row(types.InlineKeyboardButton("أذكار الصباح والمساء ☑️  مفعّل", callback_data="azkar_daily_toggle"))
    else:
        mk.row(types.InlineKeyboardButton("أذكار الصباح والمساء ✖️", callback_data="azkar_daily_toggle"))
    mk.row(
        types.InlineKeyboardButton("أحاديث شريفة 🌱", callback_data="hadith_refresh"),
        types.InlineKeyboardButton("عداد الأذكار 🌱",  callback_data="start_counter_private"),
    )
    mk.row(types.InlineKeyboardButton("التعليمات والأوامر ⁉️", callback_data="show_help"))
    return mk

def khatma_pages_markup(current=20):
    mk = types.InlineKeyboardMarkup(row_width=3)
    mk.row(
        types.InlineKeyboardButton("➖", callback_data=f"kp_minus:{current}"),
        types.InlineKeyboardButton(f"📄 {current} صفحة/يوم", callback_data="kp_ignore"),
        types.InlineKeyboardButton("➕", callback_data=f"kp_plus:{current}"),
    )
    mk.add(
        types.InlineKeyboardButton("5 صفحات",  callback_data="kp_set:5"),
        types.InlineKeyboardButton("10 صفحات", callback_data="kp_set:10"),
        types.InlineKeyboardButton("20 صفحات", callback_data="kp_set:20"),
    )
    mk.add(
        types.InlineKeyboardButton("جزء/يوم (20ص)",  callback_data="kp_set:20"),
        types.InlineKeyboardButton("نصف جزء (10ص)", callback_data="kp_set:10"),
        types.InlineKeyboardButton("ربع جزء (5ص)",  callback_data="kp_set:5"),
    )
    mk.row(types.InlineKeyboardButton("✅ التالي", callback_data=f"kp_confirm:{current}"))
    mk.row(types.InlineKeyboardButton("🔙 رجوع",   callback_data="khatma_back"))
    return mk

def calc_khatma(pages_day):
    days      = -(-QURAN_PAGES // pages_day)
    finish    = date.today() + timedelta(days=days)
    months    = days // 30
    rem_days  = days % 30
    duration  = ""
    if months:
        duration += f"{months} شهر"
        if rem_days:
            duration += f" و {rem_days} يوم"
    else:
        duration = f"{days} يوم"
    return days, finish, duration

def khatma_confirm_text(pages_day):
    days, finish, duration = calc_khatma(pages_day)
    return (
        f"╔══════════════════════╗\n"
        f"  📖  ختمة القرآن الكريم\n"
        f"╚══════════════════════╝\n\n"
        f"📄  الصفحات في اليوم:  {pages_day} صفحة\n"
        f"📅  مدة الختمة:        {duration}\n"
        f"🏁  تاريخ الختام:      {finish.strftime('%d/%m/%Y')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤍  اللهم بارك لنا في أعمارنا وأعمالنا\n"
        f"    واجعلنا من أهل القرآن"
    )

def build_khatma_continue_text(chat_id):
    u = get_user(chat_id)
    if not u or not u.get('khatma_start'):
        return None, None
    current_page = int(u.get('khatma_current') or 1)
    pages_read   = current_page - 1
    pct          = min(100, pages_read / QURAN_PAGES * 100)
    bar_filled   = int(pct / 10)
    bar          = "🟩" * bar_filled + "⬜" * (10 - bar_filled)
    text = (
        f"╔══════════════════════╗\n"
        f"  📖  ختمتي\n"
        f"╚══════════════════════╝\n\n"
        f"📄  الصفحة الحالية:  {current_page} / {QURAN_PAGES}\n"
        f"📈  {bar}  {pct:.1f}%\n\n"
        f"🤍  بارك الله في قراءتك"
    )
    mk = types.InlineKeyboardMarkup(row_width=1)
    mk.add(types.InlineKeyboardButton("📖 القراءة الآن",    callback_data="khatma_free_start"))
    mk.add(types.InlineKeyboardButton("📊 إحصائياتي",       callback_data="khatma_ward_stats"))
    mk.add(types.InlineKeyboardButton("🔄 ختمة جديدة",      callback_data="khatma_start"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع",             callback_data="khatma_back"))
    return text, mk

def build_ward_stats_text(chat_id):
    u = get_user(chat_id)
    if not u or not u.get('khatma_start'):
        return None, None
    current_page = int(u.get('khatma_current') or 1)
    streak       = int(u.get('khatma_streak')  or 0)
    missed       = int(u.get('khatma_missed')  or 0)
    pages_read   = current_page - 1
    remaining    = QURAN_PAGES - pages_read
    text = (
        f"╔══════════════════════╗\n"
        f"  📊  إحصائياتي\n"
        f"╚══════════════════════╝\n\n"
        f"📅  أيام متتالية:        {streak}\n"
        f"📍  أيام التوقف:         {missed}\n\n"
        f"📖  قرأت حتى الآن:       {pages_read} صفحة\n"
        f"⏳  تبقى لك:             {remaining} صفحة\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"جعله الله في موازين حسناتك 🤍"
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="khatma_continue"))
    return text, mk

def show_khatma_stats(chat_id, call=None):
    try:
        text, mk = build_ward_stats_text(chat_id)
    except Exception as e:
        print(f"[Stats] خطأ: {e}")
        text, mk = None, None
    if text is None:
        mk2 = types.InlineKeyboardMarkup()
        mk2.add(types.InlineKeyboardButton("📖 ابدأ ختمة", callback_data="khatma_start"))
        mk2.add(types.InlineKeyboardButton("🔙 رجوع",      callback_data="khatma_back"))
        msg = "لم تبدأ ختمة بعد 📖\nاضغط الزر أدناه لتبدأ رحلتك مع القرآن الكريم"
        if call:
            try:
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=mk2)
            except Exception:
                bot.send_message(chat_id, msg, reply_markup=mk2)
        else:
            bot.send_message(chat_id, msg, reply_markup=mk2)
        return
    if call:
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=mk)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=mk)

def khatma_preview(pages):
    days, finish, duration = calc_khatma(pages)
    return (
        f"📄  {pages} صفحة / يوم\n"
        f"⏳  مدة الختمة: {duration}\n"
        f"🏁  الانتهاء: {finish.strftime('%d/%m/%Y')}"
    )

def _page_to_image(shown_page):
    pdf_path = f"{_PDF_DIR}/page_{shown_page}.pdf"
    if not os.path.exists(pdf_path):
        return None, None
    try:
        import fitz, io as _io
        doc = fitz.open(pdf_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
        img = pix.tobytes("jpeg")
        doc.close()
        return img, pdf_path
    except ImportError:
        return None, pdf_path
    except Exception as e:
        print(f"[PageImg] خطأ في تحويل الصفحة {shown_page}: {e}")
        return None, pdf_path

def _build_page_ui(shown_page, ward_start, pages_day):
    progress    = shown_page - ward_start + 1
    is_last     = (progress >= pages_day)
    has_prev    = (shown_page > ward_start)
    ward_status = "آخر صفحة في ورد اليوم 🎉" if is_last else f"باقي {pages_day - progress} صفحة لورد اليوم"
    caption = (
        f"📖  الصفحة  {shown_page}  من  {QURAN_PAGES}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌  {progress} / {pages_day}  في ورد اليوم\n"
        f"📝  {ward_status}\n"
        f"اقرأ بتدبّر وتمعّن 🤍"
    )
    mk      = types.InlineKeyboardMarkup(row_width=2)
    nav_row = []
    if has_prev:
        nav_row.append(types.InlineKeyboardButton(
            "→ السابقة",
            callback_data=f"khatma_nav_prev:{shown_page}:{ward_start}:{pages_day}"
        ))
    nav_row.append(types.InlineKeyboardButton(
        "✅  أكملت ورد اليوم" if is_last else "التالية ←",
        callback_data=f"khatma_nav_next:{shown_page}:{ward_start}:{pages_day}"
    ))
    mk.row(*nav_row)
    return caption, mk, is_last

def _build_free_page_ui(shown_page):
    caption = (
        f"📖  الصفحة  {shown_page}  من  {QURAN_PAGES}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"اقرأ بتدبّر وتمعّن 🤍"
    )
    mk      = types.InlineKeyboardMarkup(row_width=2)
    nav_row = []
    if shown_page > 1:
        nav_row.append(types.InlineKeyboardButton(
            "→ السابقة", callback_data=f"khatma_free_prev:{shown_page}"))
    if shown_page < QURAN_PAGES:
        nav_row.append(types.InlineKeyboardButton(
            "التالية ←", callback_data=f"khatma_free_next:{shown_page}"))
    if nav_row:
        mk.row(*nav_row)
    mk.add(types.InlineKeyboardButton(
        "🛑  انتهيت  (حفظ الموضع)", callback_data=f"khatma_free_stop:{shown_page}"))
    return caption, mk

def send_quran_page(chat_id, shown_page, ward_start, pages_day):
    caption, mk, _ = _build_page_ui(shown_page, ward_start, pages_day)
    img_bytes, pdf_path = _page_to_image(shown_page)
    if img_bytes:
        import io as _io
        bot.send_photo(chat_id, _io.BytesIO(img_bytes), caption=caption, reply_markup=mk)
    elif pdf_path:
        with open(pdf_path, 'rb') as f:
            bot.send_document(chat_id, f, caption=caption, reply_markup=mk,
                              visible_file_name=f"page_{shown_page}.pdf")
    else:
        progress = shown_page - ward_start + 1
        bot.send_message(
            chat_id,
            f"📖  الصفحة  {shown_page}  من  {QURAN_PAGES}\n\n"
            f"⚠️  ملف PDF لهذه الصفحة غير متاح بعد\n\n"
            f"📌  {progress} / {pages_day}  في ورد اليوم",
            reply_markup=mk
        )

def edit_quran_page(call, shown_page, ward_start, pages_day):
    import io as _io
    caption, mk, _ = _build_page_ui(shown_page, ward_start, pages_day)
    img_bytes, pdf_path = _page_to_image(shown_page)
    cid    = call.message.chat.id
    msg_id = call.message.message_id
    if img_bytes:
        try:
            media = types.InputMediaPhoto(media=_io.BytesIO(img_bytes), caption=caption)
            bot.edit_message_media(media=media, chat_id=cid, message_id=msg_id, reply_markup=mk)
            return
        except Exception as e:
            print(f"[EditPage] خطأ: {e}")
    send_quran_page(cid, shown_page, ward_start, pages_day)

def _send_free_page(chat_id, page):
    caption, mk = _build_free_page_ui(page)
    img_bytes, pdf_path = _page_to_image(page)
    import io as _io
    if img_bytes:
        bot.send_photo(chat_id, _io.BytesIO(img_bytes), caption=caption, reply_markup=mk)
    elif pdf_path:
        with open(pdf_path, 'rb') as f:
            bot.send_document(chat_id, f, caption=caption, reply_markup=mk,
                              visible_file_name=f"page_{page}.pdf")
    else:
        bot.send_message(chat_id,
            f"📖  الصفحة  {page}  من  {QURAN_PAGES}\n\n⚠️  الملف غير متاح بعد",
            reply_markup=mk)

def _edit_free_page(call, page):
    import io as _io
    caption, mk = _build_free_page_ui(page)
    img_bytes, pdf_path = _page_to_image(page)
    cid, msg_id = call.message.chat.id, call.message.message_id
    if img_bytes:
        try:
            media = types.InputMediaPhoto(media=_io.BytesIO(img_bytes), caption=caption)
            bot.edit_message_media(media=media, chat_id=cid, message_id=msg_id, reply_markup=mk)
            return
        except Exception as e:
            print(f"[FreeEdit] {e}")
    _send_free_page(cid, page)

def _complete_khatma(chat_id):
    with db() as conn:
        conn.execute(
            "UPDATE users SET khatma_current=1, khatma_count=khatma_count+1 WHERE chat_id=?",
            (chat_id,)
        )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📖 ابدأ ختمة جديدة", callback_data="khatma_start"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع",             callback_data="khatma_back"))
    bot.send_message(
        chat_id,
        "╔══════════════════════╗\n"
        "  🏆  مبروك! أتممت الختمة\n"
        "╚══════════════════════╝\n\n"
        "أتممت ختمة القرآن الكريم بفضل الله 🤍\n\n"
        "تقبل الله منك وجعله في ميزان حسناتك\n"
        "وأعانك على ختمات قادمة بإذن الله 🌟",
        reply_markup=mk
    )

def _finish_daily_ward(chat_id, next_page, pages_day):
    u          = get_user(chat_id)
    interval_h = int(u.get('ward_interval_hours') or 24) if u else 24
    next_ward_ts = str(time.time() + interval_h * 3600)
    today      = _get_cairo_date()
    last_date  = (u.get('khatma_last_read_date') or '') if u else ''
    streak     = int(u.get('khatma_streak') or 0) if u else 0
    missed     = int(u.get('khatma_missed') or 0) if u else 0
    import datetime as _dt
    if last_date == today:
        pass
    elif last_date:
        try:
            diff = (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(last_date)).days
            if diff == 1:
                streak += 1
            else:
                missed += max(0, diff - 1)
                streak  = 1
        except Exception:
            streak = 1
    else:
        streak = 1
    with db() as conn:
        conn.execute(
            "UPDATE users SET next_ward_at=?, ward_reminder_sent=0, "
            "khatma_streak=?, khatma_missed=?, khatma_last_read_date=? WHERE chat_id=?",
            (next_ward_ts, streak, missed, today, chat_id)
        )
    interval_txt = f"{interval_h} ساعة" if interval_h < 24 else f"{interval_h // 24} يوم"
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📊 إحصائيات الورد", callback_data="khatma_ward_stats"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع",            callback_data="khatma_back"))
    bot.send_message(
        chat_id,
        f"╔══════════════════════╗\n"
        f"  ✅  أكملت ورد اليوم!\n"
        f"╚══════════════════════╝\n\n"
        f"أحسنت! قرأت وردك بفضل الله 🤍\n\n"
        f"📄  وصلت إلى الصفحة:  {next_page}\n"
        f"⏰  سيُذكّرك البوت بعد {interval_txt}\n\n"
        f"إن الذين يتلون كتاب الله وأقاموا الصلاة\n"
        f"ينتظرون تجارة لن تبور",
        reply_markup=mk
    )

# ══════════════════════════════════════════════════
#       الأوامر الرئيسية والرسائل الترحيبية
# ══════════════════════════════════════════════════
PRIVATE_WELCOME = (
    'أهلا فيك في بوت <b>" رحلة التقرب من الله 🖤 "</b> ، البوت يشمل 👇.\n\n'
    '• ختمة القرآن مع نفسك .\n'
    '• متابعة يومية للورد من البوت .\n'
    '• جميع التلاوات القرآنـــية mp3 .\n'
    '• أذكار .\n'
    '• عداد أذكار .\n'
    '• آيات قرآنية + تفسيرها .\n'
    '• أحاديث شريفة " صحيحة " .\n'
    '• أذكار الصباح والمساء + نظام متابعة .\n\n'
    '<blockquote><b>تنويه هام ⛔️\n'
    'هذا البوت لا توجد به أي إعلانات ومطوره مجهول الهوية ، فضلاً أن استفدت فادعو لي فأني بأمس الحاجة للدعاء 🌱 .</b></blockquote>'
)

GROUP_WELCOME_TEXT = lambda g: (
    f"🌙 رحلة التقرب من الله 🤎\n"
    f"━━━━━━━━━━━━━━━━━━━━\n"
    f"📿  أذكار كل {int(g.get('azkar_interval') or 30)} دقيقة\n"
    f"📖  آيات كل {int(g.get('ayah_interval') or 30)} دقيقة\n"
    f"🎙️  تلاوة كل {int(g.get('audio_interval') or 60) // 60} ساعة\n\n"
    f"الأوامر:\n"
    f"/counter ─ عداد ذكر جماعي\n"
    f"/prayer  ─ مواقيت الصلاة\n"
    f"/hadith  ─ حديث شريف\n"
    f"/ayah    ─ آية قرآنية 🌱 ."
)


def send_welcome(chat_id, parse_mode='HTML'):
    row = get_welcome_image()
    mk  = khatma_menu_markup(chat_id)
    if row:
        file_id, caption, ent_json = row
        final_caption = (caption + "\n\n" + PRIVATE_WELCOME) if caption else PRIVATE_WELCOME
        try:
            bot.send_photo(
                chat_id,
                file_id,
                caption=final_caption,
                caption_entities=None,
                parse_mode=parse_mode,
                reply_markup=mk
            )
            return
        except Exception as e:
            print(f"[Welcome Photo] خطأ: {e}")
    bot.send_message(chat_id, PRIVATE_WELCOME, reply_markup=mk, parse_mode=parse_mode)


def edit_welcome(chat_id, message_id):
    mk = khatma_menu_markup(chat_id)
    try:
        bot.edit_message_text(
            PRIVATE_WELCOME, chat_id, message_id,
            reply_markup=mk, parse_mode='HTML'
        )
    except Exception:
        send_welcome(chat_id)


# ══════════════════════════════════════════════════
#   معالج إضافة البوت للمجموعة - يشغّل فوراً
# ══════════════════════════════════════════════════
@bot.my_chat_member_handler()
def bot_added_to_group(update: types.ChatMemberUpdated):
    if update.chat.type in ['group', 'supergroup']:
        new_status = update.new_chat_member.status
        if new_status in ['member', 'administrator']:
            gid        = update.chat.id
            admin_id   = update.from_user.id
            group_name = update.chat.title or f"مجموعة {gid}"
            ensure_group(gid, admin_id, group_name)
            with db() as conn:
                conn.execute("UPDATE group_settings SET active=1 WHERE group_id=?", (gid,))
            g = get_group(gid)
            seq_interval = int(g.get('seq_interval') or 30)
            welcome = (
                f"*شكراً لأضافتي في المجموعــة 🖤*\n\n"
                f"*سيتم أرسال رسائل بالتسلسل :*\n"
                f"📿 ذكر ← 📖 آية قرآنية ← 🎙️ تلاوة — كل {seq_interval} دقيقة\n\n"
                f"*ملاحظة : صاحب هذه المجموعة فقط من يستطيع تعديل الإرسال عبر الأمر : /settings*\n\n"
                f"*سيتم أرسـال الأذكــار :*\n"
                f"- أذكار الصباح في الساعة 5:30 صباحاً .\n"
                f"- أذكار المساء في الساعة 4:00 مساءاً .\n\n"
                f"*كل جمعة سأرسل :*\n"
                f"- سورة الكهف في ملف pdf في الساعة 10 صباحاً ."
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚙️ إعدادات البوت", callback_data=f"gs_back:{gid}"))
            try:
                bot.send_message(gid, welcome, reply_markup=markup, parse_mode='Markdown')
            except Exception as e:
                print(f"[Welcome] خطأ: {e}")
            # إرسال أول محتوى فوراً بدون انتظار الجدولة
            try:
                time.sleep(2)
                text, mk2, pmode = azkar_message(for_group=True)
                _safe_send_to_group(gid, text, mk2, pmode)
                with db() as conn:
                    conn.execute(
                        "UPDATE group_settings SET last_seq_time=?, seq_next_idx=1 WHERE group_id=?",
                        (time.time(), gid)
                    )
            except Exception as e:
                print(f"[Welcome First Send] خطأ: {e}")
            dev_notice = (
                f"🔔 *تمت إضافة البوت في مجموعة جديدة*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🏠  المجموعة:  {group_name}\n"
                f"🆔  المعرف:    `{gid}`\n"
                f"👤  أضافه:     `{admin_id}`\n"
                f"🔄  فترة الإرسال: {seq_interval} د\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )
            dev_mk = types.InlineKeyboardMarkup()
            dev_mk.add(types.InlineKeyboardButton("⚙️ إعدادات المجموعة", callback_data=f"gs_back:{gid}"))
            try:
                bot.send_message(ADMIN_ID, dev_notice, reply_markup=dev_mk, parse_mode='Markdown')
            except Exception:
                pass
            try:
                admin_notice = dev_notice
                admin_mk = dev_mk
                if admin_id != ADMIN_ID:
                    bot.send_message(admin_id, admin_notice, reply_markup=admin_mk, parse_mode='Markdown')
            except Exception:
                pass
        elif new_status in ['left', 'kicked']:
            try:
                gid        = update.chat.id
                group_name = update.chat.title or f"مجموعة {gid}"
                reason     = "تم طرد البوت ❌" if new_status == 'kicked' else "البوت غادر المجموعة 🚪"
                with db() as conn:
                    conn.execute(
                        "UPDATE group_settings SET active=0, left_reason=?, group_name=? WHERE group_id=?",
                        (reason, group_name, gid)
                    )
                print(f"[Group] تعطيل المجموعة {gid} — {reason}")
            except Exception:
                pass


@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return  # /start في الجروبات لا يعمل — استخدم /play
    ensure_user(message.chat.id)
    send_welcome(message.chat.id)


@bot.message_handler(commands=['play'])
def play_cmd(message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    gid = message.chat.id
    uid = message.from_user.id
    try:
        member = bot.get_chat_member(gid, uid)
        if member.status not in ['creator', 'administrator']:
            bot.reply_to(message, "⛔ هذا الأمر للمشرفين فقط.")
            return
    except Exception:
        pass
    ensure_group(gid, uid, message.chat.title or f"مجموعة {gid}")
    with db() as conn:
        conn.execute(
            "UPDATE group_settings SET active=1, last_seq_time=0 WHERE group_id=?", (gid,)
        )
    g  = get_group(gid)
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("⚙️ إعدادات البوت", callback_data=f"gs_back:{gid}"))
    bot.send_message(gid, GROUP_WELCOME_TEXT(g), reply_markup=mk)


@bot.message_handler(commands=['help', 'مساعدة', 'مساعده'])
def help_cmd(message):
    is_group = message.chat.type in ['group', 'supergroup']
    text = (
        'التعليمات والأوامر 🌟\n'
        '━━━━━━━━━━━━━━━━━━━━\n'
        '*[ محادثة خاصة ( الشات هذا ) ‼️ ]*\n'
        '• /start        ← القائمة الرئيسية\n'
        '• /azkar       ← أذكار النوم والاستيقاظ\n'
        '• /hadith     ← حديث شريف عشوائي\n'
        '• /ayah        ← آية قرآنية مع التفسير\n'
        '• /counter  ← عداد ذكر شخصي\n\n'
        '*[ أوامر المجموعات ‼️]*\n'
        '• /play         ← تفعيل البوت (للمشرفين)\n'
        '• /settings  ← لوحة الإعدادات\n'
        '• /counter  ← عداد ذكر جماعي\n'
        '• /prayer    ← تذكيرات الصلاة\n'
        '• /setcity    ← تحديد المدينة\n'
        '• /hadith    ← حديث شريف\n'
        '• /ayah       ← آية قرآنية\n'
        '• /settings ←  التوقيت\n'
        '━━━━━━━━━━━━━━━━━━━━\n'
        '*- استخدم الأزرار في الأسفل 👇.*'
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("شروط اضافة البوت في المجموعات ⛔️", callback_data="show_group_conditions"))
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    if is_group:
        bot.reply_to(message, text, parse_mode='Markdown')
    else:
        bot.reply_to(message, text, reply_markup=mk, parse_mode='Markdown')


@bot.message_handler(commands=['settings', 'اعدادات'])
def settings_cmd(message):
    if message.chat.type not in ['group', 'supergroup']:
        return
    gid = message.chat.id
    uid = message.from_user.id
    try:
        member = bot.get_chat_member(gid, uid)
        if member.status not in ['creator', 'administrator']:
            bot.reply_to(message, "⛔ هذا الأمر للمشرفين فقط.")
            return
    except Exception:
        pass
    ensure_group(gid, uid)
    g = get_group(gid)
    bot.send_message(gid, group_settings_text(g), reply_markup=group_settings_markup(g), parse_mode='Markdown')


@bot.message_handler(commands=['azkar', 'اذكار', 'أذكار'])
def azkar_cmd(message):
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("😴 أذكار النوم",      callback_data="azkar_cat:3"),
        types.InlineKeyboardButton("☀️ أذكار الاستيقاظ", callback_data="azkar_cat:4")
    )
    mk.add(types.InlineKeyboardButton("🎲 ذكر عشوائي", callback_data="azkar_cat:27"))
    bot.reply_to(message,
        "📿 أذكارك 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر نوع الأذكار:",
        reply_markup=mk
    )


@bot.message_handler(commands=['hadith', 'حديث'])
def hadith_cmd(message):
    bot.send_chat_action(message.chat.id, 'typing')
    h    = get_random_hadith()
    arab = h.get('arab', h.get('text', ''))
    num  = h.get('number', '')
    book = h.get('_book', h.get('book', 'صحيح'))
    text = (
        f"📚 الحديث 🤎\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{arab}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"رواه {book}  |  رقم {num} 🌱."
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🔄 حديث آخر", callback_data="hadith_refresh"))
    bot.reply_to(message, text, reply_markup=mk)


@bot.message_handler(commands=['ayah', 'آية', 'اية'])
def ayah_cmd(message):
    bot.send_chat_action(message.chat.id, 'typing')
    a = get_random_ayah()
    if isinstance(a, dict) and 'surah' in a:
        text = (
            f"📖 الآية 🤎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"﴿ {a['text']} ﴾\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{a['surah']}  |  الآية {a['ayah_num']} 🌱."
        )
        mk = types.InlineKeyboardMarkup(row_width=1)
        mk.add(types.InlineKeyboardButton("📝 التفسير", callback_data=f"tafsir:{a['surah_num']}:{a['ayah_num']}"))
        mk.add(types.InlineKeyboardButton("🔄 آية أخرى", callback_data="ayah_refresh"))
        mk.add(SALAH_BUTTON())
    else:
        verse = a if isinstance(a, dict) else random.choice(SAAY_VERSES)
        text  = (
            f"📖 الآية 🤎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{verse['text']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{verse.get('ref','القرآن الكريم')} 🌱."
        )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔄 آية أخرى", callback_data="ayah_refresh"))
        mk.add(SALAH_BUTTON())
    bot.reply_to(message, text, reply_markup=mk)


@bot.message_handler(commands=['radio', 'راديو'])
def radio_cmd(message):
    stations = get_radio_stations()
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(stations[:8]):
        name = s.get('name', f'محطة {i+1}')
        mk.add(types.InlineKeyboardButton(f"📻  {name}", callback_data=f"radio:{i}"))
    mk.add(types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="radio_list"))
    bot.reply_to(message,
        "📻 الراديو 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر المحطة:",
        reply_markup=mk
    )


waiting_counter  = {}
waiting_interval = {}


@bot.message_handler(commands=['counter', 'عداد'])
def counter_cmd(message):
    waiting_counter[message.from_user.id] = message.chat.id
    bot.reply_to(message,
        "📿 عداد الذكر 🤎\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "أرسل نص الذكر أو الدعاء:\n\n"
        "• سبحان الله وبحمده\n"
        "• اللهم صل على محمد ﷺ\n"
        "• استغفر الله وأتوب إليه 🌱 ."
    )


@bot.message_handler(commands=['prayer', 'مواقيت'])
def prayer_cmd(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "هذا الأمر للمجموعات فقط 🕌")
        return
    gid = message.chat.id
    ensure_group(gid)
    g       = get_group(gid)
    new_val = 0 if g['prayer_enabled'] else 1
    with db() as conn:
        conn.execute("UPDATE group_settings SET prayer_enabled=? WHERE group_id=?", (new_val, gid))
    if new_val:
        bot.reply_to(message,
            "✅  تم تفعيل مواقيت الصلاة\n\n"
            "سيتم الإرسال:\n"
            "• تذكير قبل كل صلاة بـ 20 دقيقة\n"
            "• رسالة الأذان عند الموعد\n\n"
            f"المدينة الحالية: {g['city']}\n"
            "لتغييرها: /setcity"
        )
    else:
        bot.reply_to(message, "🔕  تم إيقاف مواقيت الصلاة")


@bot.message_handler(commands=['setcity'])
def setcity_cmd(message):
    if message.chat.type == 'private':
        bot.reply_to(message, "هذا الأمر للمجموعات فقط 🕌")
        return
    ensure_group(message.chat.id)
    bot.send_message(message.chat.id,
        "📍  اختر دولتك لضبط مواقيت الصلاة:",
        reply_markup=country_markup_group(message.chat.id)
    )


@bot.message_handler(commands=['save'])
def save_cmd(message):
    global dev_upload_mode, dev_upload_sabah_mode, dev_upload_masaa_mode
    global dev_upload_quran_mode, dev_upload_group_daily_mode, dev_upload_kahf_mode
    global dev_upload_welcome_mode
    if message.from_user.id == ADMIN_ID:
        dev_upload_mode             = False
        dev_upload_sabah_mode       = False
        dev_upload_masaa_mode       = False
        dev_upload_quran_mode       = False
        dev_upload_group_daily_mode = False
        dev_upload_kahf_mode        = False
        dev_upload_welcome_mode     = False
        bot.reply_to(message, "✅  تم إغلاق جميع أوضاع الرفع")


@bot.message_handler(commands=['Dev'])
def dev_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    with db() as conn:
        sabah_count = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='sabah'").fetchone()[0]
        masaa_count = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='masaa'").fetchone()[0]
        wel_count   = conn.execute("SELECT COUNT(*) FROM welcome_image").fetchone()[0]
    bot.send_message(message.chat.id,
        f"╔══════════════════════╗\n"
        f"  🔧  لوحة المطور\n"
        f"╚══════════════════════╝\n\n"
        f"🌅  صور أذكار الصباح:   {sabah_count}\n"
        f"🌆  صور أذكار المساء:   {masaa_count}\n"
        f"🖼️  صورة الترحيب:      {'موجودة ✅' if wel_count else 'غير موجودة ❌'}\n\n"
        f"اختر الإجراء:",
        reply_markup=dev_menu_markup()
    )


def dev_menu_markup():
    mk = types.InlineKeyboardMarkup(row_width=1)
    # ── الإحصائيات والأدوات ──
    mk.row(
        types.InlineKeyboardButton("📊 إحصائيات",           callback_data="dev_stats"),
        types.InlineKeyboardButton("🏠 إحصائيات المجموعات", callback_data="dev_group_stats"),
    )
    mk.row(
        types.InlineKeyboardButton("🔄 تفعيل المجموعات",    callback_data="dev_reactivate"),
        types.InlineKeyboardButton("💾 نسخة احتياطية DB",   callback_data="dev_backup"),
    )
    mk.row(types.InlineKeyboardButton("📢 إرسال جماعي",     callback_data="dev_broadcast"))

    # ── صورة الترحيب ──
    mk.row(
        types.InlineKeyboardButton("🖼️ رفع صورة الترحيب",   callback_data="dev_upload_welcome"),
        types.InlineKeyboardButton("🗑️ حذف صورة الترحيب",   callback_data="dev_del_welcome"),
    )

    # ── القرآن الكريم ──
    mk.row(
        types.InlineKeyboardButton("📤 رفع صفحات (PDF فردي)", callback_data="dev_upload"),
        types.InlineKeyboardButton("📚 رفع مصحف كامل",        callback_data="dev_upload_quran"),
    )

    # ── أذكار الصباح والمساء ──
    mk.row(
        types.InlineKeyboardButton("🌅 رفع أذكار الصباح",   callback_data="dev_upload_sabah"),
        types.InlineKeyboardButton("🌆 رفع أذكار المساء",   callback_data="dev_upload_masaa"),
    )
    mk.row(
        types.InlineKeyboardButton("🗑️ حذف أذكار الصباح",   callback_data="dev_del_sabah"),
        types.InlineKeyboardButton("🗑️ حذف أذكار المساء",   callback_data="dev_del_masaa"),
    )

    # ── الصورة اليومية للجروبات ──
    mk.row(
        types.InlineKeyboardButton("🖼️ رفع صورة الجروبات",  callback_data="dev_upload_group_daily"),
        types.InlineKeyboardButton("🗑️ حذف صورة الجروبات",  callback_data="dev_del_group_daily"),
    )

    # ── سورة الكهف ──
    mk.row(
        types.InlineKeyboardButton("📖 رفع سورة الكهف",     callback_data="dev_upload_kahf"),
        types.InlineKeyboardButton("🗑️ حذف سورة الكهف",     callback_data="dev_del_kahf"),
    )
    return mk


dev_upload_mode             = False
dev_broadcast_mode          = False
dev_upload_sabah_mode       = False
dev_upload_masaa_mode       = False
dev_upload_quran_mode       = False
dev_upload_group_daily_mode = False
dev_upload_kahf_mode        = False
dev_upload_welcome_mode     = False


# ══════════════════════════════════════════════════
#          معالجات الرسائل (صور / مستندات)
# ══════════════════════════════════════════════════
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    global dev_upload_sabah_mode, dev_upload_masaa_mode
    global dev_upload_group_daily_mode, dev_upload_welcome_mode
    if message.from_user.id != ADMIN_ID:
        return
    if not any([dev_upload_sabah_mode, dev_upload_masaa_mode,
                dev_upload_group_daily_mode, dev_upload_welcome_mode]):
        return

    file_id      = message.photo[-1].file_id
    caption      = message.caption or None
    ent_json     = entities_to_json(message.caption_entities)
    caption_prev = f"\n📝 الوصف: {caption}" if caption else "\n📝 بدون وصف"

    if dev_upload_welcome_mode:
        with db() as conn:
            conn.execute("DELETE FROM welcome_image")
            conn.execute(
                "INSERT INTO welcome_image (file_id, caption, caption_entities, saved_at) VALUES (?,?,?,?)",
                (file_id, caption, ent_json, time.time())
            )
        bot.reply_to(message,
            f"✅ تم حفظ صورة الترحيب!{caption_prev}\n\n"
            f"ستظهر في رسالة /start للمستخدمين.\n"
            f"للإنهاء: /save"
        )
        return

    if dev_upload_group_daily_mode:
        with db() as conn:
            conn.execute("DELETE FROM azkar_images WHERE type='group_daily'")
            conn.execute(
                "INSERT INTO azkar_images (type, file_id, order_num, caption, caption_entities) "
                "VALUES ('group_daily',?,1,?,?)",
                (file_id, caption, ent_json)
            )
        bot.reply_to(message,
            f"✅ تم حفظ الصورة اليومية للجروبات!{caption_prev}\n\n"
            f"ستُرسَل تلقائياً الساعة 12:00 منتصف الليل و12:00 منتصف النهار.\n"
            f"للإنهاء: /save"
        )
        return

    azkar_type = 'sabah' if dev_upload_sabah_mode else 'masaa'
    name       = "الصباح" if azkar_type == 'sabah' else "المساء"
    with db() as conn:
        order = conn.execute(
            "SELECT COALESCE(MAX(order_num),0)+1 FROM azkar_images WHERE type=?", (azkar_type,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO azkar_images (type, file_id, order_num, caption, caption_entities) "
            "VALUES (?,?,?,?,?)",
            (azkar_type, file_id, order, caption, ent_json)
        )
    hour_str = "5:30 صباحاً" if azkar_type == 'sabah' else "4:00 مساءً"
    bot.reply_to(message,
        f"✅ تم حفظ صورة أذكار {name} رقم {order}{caption_prev}\n\n"
        f"⏰ ستُرسَل الساعة {hour_str}\n"
        f"استمر في إرسال الصور أو /save للإنهاء"
    )


@bot.message_handler(content_types=['document'])
def handle_doc(message):
    global dev_upload_mode, dev_upload_quran_mode, dev_upload_kahf_mode
    if message.from_user.id != ADMIN_ID:
        return
    if not message.document:
        return
    mime = (message.document.mime_type or '').lower()

    if dev_upload_kahf_mode and 'pdf' in mime:
        caption  = message.caption or None
        ent_json = entities_to_json(message.caption_entities)
        with db() as conn:
            conn.execute("DELETE FROM friday_kahf")
            conn.execute(
                "INSERT INTO friday_kahf (file_id, caption, caption_entities, saved_at) VALUES (?,?,?,?)",
                (message.document.file_id, caption, ent_json, time.time())
            )
        caption_prev = f"\n📝 الوصف: {caption}" if caption else "\n📝 بدون وصف"
        bot.reply_to(message,
            f"✅ تم حفظ سورة الكهف!{caption_prev}\n\n"
            f"ستُرسَل كل جمعة الساعة 10:00 صباحاً.\n"
            f"للإنهاء: /save"
        )
        return

    if dev_upload_quran_mode and 'pdf' in mime:
        try:
            import io as _fio
            status_msg = bot.reply_to(message, "⏳  جاري تحميل المصحف...")
            info = bot.get_file(message.document.file_id)
            data = bot.download_file(info.file_path)
            bot.edit_message_text("⏳  جاري فتح الملف...", message.chat.id, status_msg.message_id)
            try:
                import fitz as _fitz
                doc   = _fitz.open(stream=_fio.BytesIO(data), filetype="pdf")
                if doc.is_encrypted:
                    doc.authenticate("") or doc.authenticate("pdf")
                total = doc.page_count
                bot.edit_message_text(
                    f"⏳  {total} صفحة — جاري التقسيم...",
                    message.chat.id, status_msg.message_id
                )
                saved = 0
                for i in range(total):
                    single = _fitz.open()
                    single.insert_pdf(doc, from_page=i, to_page=i)
                    single.save(f"{_PDF_DIR}/page_{i+1}.pdf")
                    single.close()
                    saved += 1
                    if saved % 100 == 0:
                        bot.edit_message_text(
                            f"⏳  {saved}/{total} صفحة...",
                            message.chat.id, status_msg.message_id
                        )
                doc.close()
                bot.edit_message_text(
                    f"✅  تم بنجاح!\n📄  الصفحات المحفوظة: {saved}\n"
                    f"📂  {_PDF_DIR}/page_1.pdf → page_{saved}.pdf",
                    message.chat.id, status_msg.message_id
                )
            except ImportError:
                existing_count = len([
                    x for x in os.listdir(_PDF_DIR)
                    if re.match(r"^page_\d+\.pdf$", x)
                ])
                bot.edit_message_text(
                    f"⚠️  PyMuPDF غير مثبت على الخادم\n\n"
                    f"لتثبيته: pip install PyMuPDF\n\n"
                    f"📂  صفحات موجودة حالياً: {existing_count}\n\n"
                    f"إذا كان مجلد {_PDF_DIR} يحتوي على الملفات فالبوت يعمل ✅",
                    message.chat.id, status_msg.message_id
                )
        except Exception as e:
            bot.reply_to(message, f"❌  خطأ: {e}")
        return

    if dev_upload_mode and 'pdf' in mime:
        caption = message.caption or ''
        num     = extract_page_number(caption) or extract_page_number(message.document.file_name)
        if num and 1 <= num <= 569:
            path = f"{_PDF_DIR}/page_{num}.pdf"
            info = bot.get_file(message.document.file_id)
            data = bot.download_file(info.file_path)
            with open(path, 'wb') as f:
                f.write(data)
            bot.reply_to(message, f"✅  تم حفظ الصفحة رقم {num}")
        else:
            bot.reply_to(message, f"⚠️  لم أتعرف على رقم الصفحة\nاسم الملف: {message.document.file_name}")


# ══════════════════════════════════════════════════
#        معالج الرسائل النصية (انتظار / عداد)
# ══════════════════════════════════════════════════
@bot.message_handler(func=lambda m: m.from_user.id in waiting_interval and m.text)
def receive_interval(message):
    uid  = message.from_user.id
    info = waiting_interval.pop(uid, None)
    if not info:
        return
    mins = parse_interval(message.text)
    if mins is None:
        bot.reply_to(message,
            "⚠️  صيغة غير صحيحة\n\n"
            "أمثلة صحيحة:\n"
            "• *5m* ← كل 5 دقائق\n"
            "• *30m* ← كل 30 دقيقة\n"
            "• *1h* ← كل ساعة\n"
            "• *2h* ← كل ساعتين\n\n"
            "الحد الأدنى: 5 دقائق | الأقصى: 720 دقيقة",
            parse_mode='Markdown'
        )
        waiting_interval[uid] = info
        return
    gid = info['group_id']
    with db() as conn:
        conn.execute("UPDATE group_settings SET seq_interval=?, last_seq_time=0 WHERE group_id=?", (mins, gid))
    g       = get_group(gid)
    label_h = f"{mins//60} ساعة" if mins % 60 == 0 else f"{mins} دقيقة"
    bot.reply_to(message, f"✅  تم ضبط التوقيت على {label_h}")
    try:
        bot.edit_message_text(
            group_settings_text(g), info['chat_id'], info['msg_id'],
            reply_markup=group_settings_markup(g), parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(info['chat_id'], group_settings_text(g),
                         reply_markup=group_settings_markup(g), parse_mode='Markdown')


@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.chat.id in _import_waiting)
def handle_import_page_input(message):
    cid  = message.chat.id
    text = (message.text or '').strip()
    try:
        page = int(text)
    except ValueError:
        page = None
    if not page or not (1 <= page <= QURAN_PAGES):
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="khatma_import_cancel"))
        bot.send_message(cid, f"⚠️  الرقم غير صحيح\nأرسل رقماً بين 1 و {QURAN_PAGES}", reply_markup=mk)
        return
    _import_waiting.pop(cid, None)
    ensure_user(cid)
    from datetime import date as _date
    today      = str(_date.today())
    start_page = min(page + 1, QURAN_PAGES)
    with db() as conn:
        conn.execute(
            "UPDATE users SET khatma_start=?, khatma_current=?, khatma_pages_day=5, "
            "next_ward_at='', ward_reminder_sent=0, "
            "khatma_streak=0, khatma_missed=0, khatma_last_read_date='' WHERE chat_id=?",
            (today, start_page, cid)
        )
    text_out, mk_out = build_khatma_continue_text(cid)
    bot.send_message(cid,
        f"✅  تم الحفظ!\n"
        f"ستبدأ من الصفحة  {start_page}  مباشرةً 🤍"
    )
    if text_out:
        bot.send_message(cid, text_out, reply_markup=mk_out)


@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.chat.id in _ward_pages_waiting)
def handle_ward_pages_input(message):
    cid  = message.chat.id
    text = (message.text or '').strip()
    try:
        pages = int(text)
    except ValueError:
        pages = None
    if not pages or pages < 1 or pages > QURAN_PAGES:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="ward_cancel"))
        bot.send_message(cid,
            f"⚠️  الرقم غير صحيح\nأرسل رقماً بين 1 و {QURAN_PAGES}",
            reply_markup=mk
        )
        return
    _ward_pages_waiting.pop(cid, None)
    _ward_start_waiting[cid] = pages          # احفظ الصفحات مؤقتاً
    ensure_user(cid)
    finish_date = calc_khatma_finish(pages)
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("✅ البدء اليوم",  callback_data="ward_startday:today"),
        types.InlineKeyboardButton("📅 البدء غداً",   callback_data="ward_startday:tomorrow"),
    )
    mk.row(types.InlineKeyboardButton("❌ إلغاء", callback_data="ward_cancel"))
    bot.send_message(
        cid,
        f"ستتم ختمتك بإذن الله بتاريخ : *{finish_date}* 🤍\n\n"
        f"سأرسل التذكير يوميا في *الساعة الثالثه* عصرا ان شاء الله 🌱.",
        reply_markup=mk,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.chat.id in _tilawa_waiting)
def handle_tilawa_input(message):
    cid  = message.chat.id
    text = (message.text or '').strip()
    surah_num = _find_surah_num(text)
    if not surah_num:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="tilawa_cancel"))
        bot.send_message(cid,
            "⚠️  لم أتعرف على اسم السورة\n\n"
            "أرسل مرة أخرى مثال:\n"
            "   سورة الكهف - ماهر المعيقلي\n"
            "   يس العفاسي",
            reply_markup=mk
        )
        return
    _tilawa_waiting.pop(cid, None)
    surah_name = next((n for n, num in SURAH_NAMES.items() if num == surah_num), f"سورة رقم {surah_num}")
    wait_msg   = bot.send_message(cid, f"⏳  جاري البحث عن تلاوة سورة {surah_name}...")
    reciter    = _find_reciter(text)
    audio_url, performer = _fetch_audio_url(surah_num, reciter)
    try:
        bot.delete_message(cid, wait_msg.message_id)
    except Exception:
        pass
    if not audio_url:
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔄 حاول مرة أخرى", callback_data="tilawa_start"))
        mk.add(types.InlineKeyboardButton("🔙 رجوع",           callback_data="khatma_back"))
        bot.send_message(cid,
            f"❌  لم أجد تلاوة سورة {surah_name}\n"
            "تأكد من كتابة اسم السورة وحاول مجدداً",
            reply_markup=mk
        )
        return
    mk_audio = types.InlineKeyboardMarkup()
    mk_audio.add(types.InlineKeyboardButton("📢  القناة الرسمية", url=CHANNEL_LINK))
    mk_audio.add(types.InlineKeyboardButton("🔄 تلاوة أخرى", callback_data="tilawa_start"))
    caption = (
        f"🎙️  سورة {surah_name}\n"
        f"🤍  {performer}\n\n"
        f"استمع بتدبّر وخشوع"
    )
    dl_msg = bot.send_message(cid, "⬇️  جاري تحميل التلاوة...")
    sent   = False
    try:
        import io as _io
        headers = {"User-Agent": "Mozilla/5.0"}
        resp    = requests.get(audio_url, headers=headers, timeout=90, stream=True)
        resp.raise_for_status()
        MAX_BYTES = 48 * 1024 * 1024
        buf = _io.BytesIO()
        for chunk in resp.iter_content(chunk_size=65536):
            buf.write(chunk)
            if buf.tell() > MAX_BYTES:
                raise ValueError("الملف أكبر من 48 ميجا")
        buf.seek(0)
        buf.name = f"surah_{surah_num}.mp3"
        try:
            bot.delete_message(cid, dl_msg.message_id)
        except Exception:
            pass
        bot.send_audio(cid, buf, caption=caption, performer=performer,
                       title=f"سورة {surah_name}", reply_markup=mk_audio)
        sent = True
    except Exception as e:
        print(f"[Tilawa] خطأ: {e}")
        try:
            bot.delete_message(cid, dl_msg.message_id)
        except Exception:
            pass
    if not sent:
        mk_audio2 = types.InlineKeyboardMarkup()
        mk_audio2.add(types.InlineKeyboardButton("🔗 استمع مباشرة", url=audio_url))
        mk_audio2.add(types.InlineKeyboardButton("📢 القناة", url=CHANNEL_LINK))
        bot.send_message(cid,
            f"🎙️  سورة {surah_name} | {performer}\n\n"
            "⚠️  الملف كبير جداً — اضغط الزر للاستماع مباشرةً",
            reply_markup=mk_audio2
        )


@bot.message_handler(func=lambda m: m.from_user.id in waiting_counter and m.from_user.id not in waiting_interval)
def receive_counter(message):
    user_id  = message.from_user.id
    chat_id  = waiting_counter.get(user_id)
    if not chat_id:
        return
    del waiting_counter[user_id]
    zikr_text = message.text.strip() if message.text else ""
    if not zikr_text:
        bot.reply_to(message, "أرسل نص الذكر أولاً")
        return
    if len(zikr_text) > 150:
        bot.reply_to(message, "النص طويل جداً، الحد الأقصى 150 حرف")
        return
    btn_label = zikr_text if len(zikr_text) <= 40 else zikr_text[:37] + "..."
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(f"📿 {btn_label} | 0", callback_data="count:pending"))
    mk.add(SALAH_BUTTON())
    body = (
        f"📿 عداد الذكر 🤎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{zikr_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"اضغط للمشاركة في الأجر | كل ضغطة = حسنة 🌱 ."
    )
    sent = bot.send_message(chat_id, body, reply_markup=mk)
    real_mk = types.InlineKeyboardMarkup()
    real_mk.add(types.InlineKeyboardButton(f"📿 {btn_label} | 0", callback_data=f"count:{sent.message_id}"))
    real_mk.add(SALAH_BUTTON())
    try:
        bot.edit_message_reply_markup(chat_id, sent.message_id, reply_markup=real_mk)
    except Exception:
        pass
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO counters VALUES (?,?,?,0,?,?)",
            (sent.message_id, chat_id, zikr_text, user_id, time.time())
        )
    if message.chat.type != 'private':
        try:
            bot.pin_chat_message(chat_id, sent.message_id, disable_notification=True)
        except Exception:
            pass


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and dev_broadcast_mode and m.text)
def dev_broadcast_msg(message):
    global dev_broadcast_mode
    dev_broadcast_mode = False
    with db() as conn:
        users = conn.execute("SELECT chat_id FROM users").fetchall()
    sent = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, f"📢  رسالة من المشرف:\n\n{message.text}")
            sent += 1
            time.sleep(0.05)
        except Exception:
            pass
    bot.reply_to(message, f"✅  تم الإرسال إلى {sent} مستخدم")


# ══════════════════════════════════════════════════
#              معالجات الأزرار التفاعلية
# ══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith('gs_'))
def handle_gs(call):
    data   = call.data
    parts  = data.split(':')
    action = parts[0]

    def is_authorized():
        try:
            if 'setcity' in data or 'setcountry' in data:
                gid = int(parts[1])
            else:
                gid = int(parts[-1].split(':')[0])
        except Exception:
            gid = int(parts[1])
        g = get_group(gid)
        if not g:
            return False, gid, g
        is_admin = (call.from_user.id == g.get('admin_id') or call.from_user.id == ADMIN_ID)
        try:
            member   = bot.get_chat_member(gid, call.from_user.id)
            is_admin = is_admin or member.status in ['administrator', 'creator']
        except Exception:
            pass
        return is_admin, gid, g

    if action == 'gs_back':
        gid = int(parts[1])
        ensure_group(gid)
        g = get_group(gid)
        try:
            bot.edit_message_text(group_settings_text(g), call.message.chat.id,
                                  call.message.message_id, reply_markup=group_settings_markup(g), parse_mode='Markdown')
        except Exception:
            bot.send_message(gid, group_settings_text(g), reply_markup=group_settings_markup(g), parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif action == 'gs_reset':
        gid = int(parts[1])
        with db() as conn:
            conn.execute(
                "UPDATE group_settings SET seq_interval=30, seq_next_idx=0, last_seq_time=0 WHERE group_id=?",
                (gid,)
            )
        g = get_group(gid)
        try:
            bot.edit_message_text(group_settings_text(g), call.message.chat.id,
                                  call.message.message_id, reply_markup=group_settings_markup(g), parse_mode='Markdown')
        except Exception:
            bot.send_message(gid, group_settings_text(g), reply_markup=group_settings_markup(g), parse_mode='Markdown')
        bot.answer_callback_query(call.id, "✅ تمت إعادة الضبط للإعدادات الافتراضية")

    elif action == 'gs_toggle':
        feature  = parts[1]
        gid      = int(parts[2])
        ok, gid, g = is_authorized()
        if not ok:
            bot.answer_callback_query(call.id, "⛔  هذا الأمر للمشرفين فقط", show_alert=True)
            return
        col  = f"{feature}_enabled"
        nval = 0 if g[col] else 1
        with db() as conn:
            conn.execute(f"UPDATE group_settings SET {col}=? WHERE group_id=?", (nval, gid))
        g = get_group(gid)
        try:
            bot.edit_message_text(group_settings_text(g), call.message.chat.id,
                                  call.message.message_id, reply_markup=group_settings_markup(g), parse_mode='Markdown')
        except Exception:
            pass
        bot.answer_callback_query(call.id, f"تم التغيير: {'مفعّل ✅' if nval else 'موقف ❌'}")

    elif action == 'gs_time':
        feature  = parts[1]
        gid      = int(parts[2])
        ok, gid, g = is_authorized()
        if not ok:
            bot.answer_callback_query(call.id, "⛔  للمشرفين فقط", show_alert=True)
            return
        try:
            bot.edit_message_text(
                "⏱️  اختر فترة الإرسال بين كل رسالة والتالية:\n\n"
                "التسلسل : ذكر ← آية ← تلاوة ← تكرار",
                call.message.chat.id, call.message.message_id,
                reply_markup=interval_markup('seq', gid)
            )
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    elif action == 'gs_settime':
        feature = parts[1]
        gid     = int(parts[2])
        mins    = int(parts[3])
        with db() as conn:
            conn.execute("UPDATE group_settings SET seq_interval=?, last_seq_time=0 WHERE group_id=?", (mins, gid))
        g = get_group(gid)
        try:
            bot.edit_message_text(group_settings_text(g), call.message.chat.id,
                                  call.message.message_id, reply_markup=group_settings_markup(g), parse_mode='Markdown')
        except Exception:
            pass
        bot.answer_callback_query(call.id, f"✅  تم الضبط على {mins} دقيقة")

    elif action == 'gs_custom':
        feature = parts[1]
        gid     = int(parts[2])
        waiting_interval[call.from_user.id] = {
            'feature': 'seq', 'group_id': gid,
            'chat_id': call.message.chat.id, 'msg_id': call.message.message_id,
        }
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.from_user.id,
            "✏️  *أدخل فترة الإرسال المخصصة*\n\n"
            "الصيغ المقبولة:\n"
            "• `5m`  ← كل 5 دقائق\n"
            "• `30m` ← كل 30 دقيقة\n"
            "• `1h`  ← كل ساعة\n"
            "• `2h`  ← كل ساعتين\n\n"
            "_الحد الأدنى: 5 دقائق | الأقصى: 12 ساعة_",
            parse_mode='Markdown'
        )

    elif action == 'gs_city':
        gid = int(parts[1])
        ok, gid, g = is_authorized()
        if not ok:
            bot.answer_callback_query(call.id, "⛔  للمشرفين فقط", show_alert=True)
            return
        try:
            bot.edit_message_text(
                "📍  اختر دولتك لتحديد مواقيت الصلاة:",
                call.message.chat.id, call.message.message_id,
                reply_markup=country_markup_group(gid)
            )
        except Exception:
            pass
        bot.answer_callback_query(call.id)

    elif action == 'gs_setcountry':
        gid        = int(parts[1])
        capital    = parts[2]
        country_en = ":".join(parts[3:])
        with db() as conn:
            conn.execute(
                "UPDATE group_settings SET city=?, country=? WHERE group_id=?",
                (capital, country_en, gid)
            )
        ptimes = get_prayer_times(capital, country_en)
        if ptimes:
            lines = "\n".join(
                f"{PRAYER_EMOJIS[p]}  {PRAYER_NAMES[p]} : {ptimes[p].strftime('%I:%M %p').replace('AM','ص').replace('PM','م')}"
                for p in ['Fajr','Dhuhr','Asr','Maghrib','Isha']
            )
            confirm_text = (
                f"✅  تم تحديد المدينة: *{capital}*\n\n"
                f"🕌  مواقيت الصلاة اليوم:\n{lines}"
            )
        else:
            confirm_text = f"✅  تم تحديد المدينة: *{capital}*\n\n⚠️  تعذّر جلب مواقيت الصلاة الآن"
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data=f"gs_back:{gid}"))
        try:
            bot.edit_message_text(confirm_text, call.message.chat.id,
                                  call.message.message_id, reply_markup=mk, parse_mode='Markdown')
        except Exception:
            bot.send_message(call.message.chat.id, confirm_text, reply_markup=mk, parse_mode='Markdown')
        bot.answer_callback_query(call.id, f"✅  {capital}")

    elif action == 'gs_setcity':
        gid        = int(parts[1])
        city_en    = parts[2]
        country    = parts[3]
        with db() as conn:
            conn.execute("UPDATE group_settings SET city=?, country=? WHERE group_id=?",
                         (city_en, country, gid))
        g = get_group(gid)
        try:
            bot.edit_message_text(group_settings_text(g), call.message.chat.id,
                                  call.message.message_id, reply_markup=group_settings_markup(g), parse_mode='Markdown')
        except Exception:
            pass
        bot.answer_callback_query(call.id, f"✅  تم تغيير المدينة إلى {city_en}")


# ── الأذكار ──
@bot.callback_query_handler(func=lambda c: c.data.startswith('azkar_cat:'))
def handle_azkar_cat(call):
    cat_id = int(call.data.split(':')[1])
    bot.answer_callback_query(call.id, "جاري جلب الأذكار...")
    zikr = get_random_zikr_text(cat_id)
    text = f"📿 الذكر 🤎\n━━━━━━━━━━━━━━━━━━━━\n{zikr} 🌱 ."
    mk   = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("🔄 ذكر آخر", callback_data=f"azkar_cat:{cat_id}"),
        types.InlineKeyboardButton("🔙 رجوع",    callback_data="show_azkar")
    )
    mk.add(SALAH_BUTTON())
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'show_azkar')
def handle_show_azkar(call):
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.add(
        types.InlineKeyboardButton("😴 أذكار النوم",      callback_data="azkar_cat:3"),
        types.InlineKeyboardButton("☀️ أذكار الاستيقاظ", callback_data="azkar_cat:4")
    )
    mk.add(types.InlineKeyboardButton("🎲 ذكر عشوائي", callback_data="azkar_cat:27"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="khatma_back"))
    try:
        bot.edit_message_text(
            "📿 أذكارك 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر نوع الأذكار:",
            call.message.chat.id, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(call.message.chat.id,
            "📿 أذكارك 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر نوع الأذكار:", reply_markup=mk)
    bot.answer_callback_query(call.id)


# ── الحديث ──
@bot.callback_query_handler(func=lambda c: c.data == 'hadith_refresh')
def handle_hadith(call):
    bot.answer_callback_query(call.id, "جاري جلب حديث جديد...")
    h    = get_random_hadith()
    arab = h.get('arab', h.get('text', ''))
    num  = h.get('number', '')
    book = h.get('_book', h.get('book', 'صحيح'))
    text = (
        f"📚 الحديث 🤎\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{arab}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"رواه {book}  |  رقم {num} 🌱."
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("🔄 حديث آخر", callback_data="hadith_refresh"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="khatma_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=mk)


# ── الآية ──
@bot.callback_query_handler(func=lambda c: c.data == 'ayah_refresh')
def handle_ayah(call):
    bot.answer_callback_query(call.id, "جاري جلب آية...")
    a = get_random_ayah()
    if isinstance(a, dict) and 'surah' in a:
        text = (
            f"📖 الآية 🤎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"﴿ {a['text']} ﴾\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{a['surah']}  |  الآية {a['ayah_num']} 🌱."
        )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📝 التفسير",  callback_data=f"tafsir:{a['surah_num']}:{a['ayah_num']}"))
        mk.add(types.InlineKeyboardButton("🔄 آية أخرى", callback_data="ayah_refresh"))
        mk.add(SALAH_BUTTON())
    else:
        verse = a if isinstance(a, dict) else random.choice(SAAY_VERSES)
        text  = (
            f"📖 الآية 🤎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"{verse['text']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{verse.get('ref','القرآن الكريم')} 🌱."
        )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔄 آية أخرى", callback_data="ayah_refresh"))
        mk.add(SALAH_BUTTON())
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data.startswith('tafsir:'))
def handle_tafsir(call):
    bot.answer_callback_query(call.id, "جاري جلب التفسير...")
    parts = call.data.split(':')
    sn, an = int(parts[1]), int(parts[2])
    try:
        url  = f"https://quranenc.com/api/v1/translation/sura/arabic_moyassar/{sn}"
        r    = requests.get(url, timeout=15)
        data = r.json()
        tafsir_text = ""
        for item in data.get('result', []):
            if int(item.get('aya', 0)) == an:
                tafsir_text = item.get('translation', '')
                break
        if tafsir_text:
            text = (
                f"📝 التفسير 🤎\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"{tafsir_text} 🌱 ."
            )
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("🔄 آية أخرى", callback_data="ayah_refresh"))
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=mk)
            except Exception:
                bot.send_message(call.message.chat.id, text, reply_markup=mk)
        else:
            bot.answer_callback_query(call.id, "التفسير غير متاح حالياً", show_alert=True)
    except Exception:
        bot.answer_callback_query(call.id, "خطأ في جلب التفسير", show_alert=True)


# ── الراديو ──
@bot.callback_query_handler(func=lambda c: c.data == 'radio_list')
def handle_radio_list(call):
    global _radio_cache
    _radio_cache = None
    stations = get_radio_stations()
    mk = types.InlineKeyboardMarkup(row_width=1)
    for i, s in enumerate(stations[:8]):
        mk.add(types.InlineKeyboardButton(f"📻  {s.get('name', f'محطة {i+1}')}", callback_data=f"radio:{i}"))
    mk.add(types.InlineKeyboardButton("🔄 تحديث", callback_data="radio_list"))
    try:
        bot.edit_message_text(
            "📻 الراديو 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر المحطة:",
            call.message.chat.id, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(call.message.chat.id,
            "📻 الراديو 🤎\n━━━━━━━━━━━━━━━━━━━━\nاختر المحطة:", reply_markup=mk)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('radio:'))
def handle_radio(call):
    idx      = int(call.data.split(':')[1])
    stations = get_radio_stations()
    if idx < len(stations):
        s    = stations[idx]
        name = s.get('name', 'محطة إسلامية')
        url  = s.get('url', s.get('stream', s.get('link', '')))
        if url:
            bot.answer_callback_query(call.id, f"📻  {name}")
            bot.send_message(call.message.chat.id,
                f"📻 الراديو 🤎\n━━━━━━━━━━━━━━━━━━━\n{name}\n\n🔗 رابط البث:\n{url} 🌱 .")
        else:
            bot.answer_callback_query(call.id, "الرابط غير متاح", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "المحطة غير موجودة", show_alert=True)


# ── العداد الجماعي ──
counter_locks      = {}
_counter_locks_lock = threading.Lock()   # يحمي إنشاء/حذف locks من race condition
_MAX_COUNTER_LOCKS  = 2000               # prevent unbounded memory growth


@bot.callback_query_handler(func=lambda c: c.data == 'start_counter_private')
def handle_counter_private(call):
    waiting_counter[call.from_user.id] = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "📿 عداد الذكر 🤎\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "أرسل نص الذكر الذي تريد العدّ عليه 🌱 ."
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith('count:') and c.data != 'count:pending')
def handle_count(call):
    raw = call.data.split(':')[1]
    try:
        mid = int(raw)
    except ValueError:
        bot.answer_callback_query(call.id)
        return
    with _counter_locks_lock:
        if mid not in counter_locks:
            if len(counter_locks) >= _MAX_COUNTER_LOCKS:
                old_keys = list(counter_locks.keys())[:-(_MAX_COUNTER_LOCKS // 2)]
                for _k in old_keys:
                    del counter_locks[_k]
            counter_locks[mid] = threading.Lock()
        lock = counter_locks[mid]
    with lock:
        try:
            now = time.time()
            with db() as conn:
                conn.execute(
                    "INSERT INTO counter_clicks (message_id,user_id,last_click_time,click_count) "
                    "VALUES (?,?,?,1) ON CONFLICT(message_id,user_id) "
                    "DO UPDATE SET click_count=click_count+1, last_click_time=?",
                    (mid, call.from_user.id, now, now)
                )
                conn.execute("UPDATE counters SET count=count+1 WHERE message_id=?", (mid,))
                row = conn.execute("SELECT count, text FROM counters WHERE message_id=?", (mid,)).fetchone()
            if row:
                count, zikr_text = row
                btn_label = zikr_text if len(zikr_text) <= 35 else zikr_text[:32] + "..."
                mk = types.InlineKeyboardMarkup()
                mk.add(types.InlineKeyboardButton(f"📿 {btn_label} | {count:,}", callback_data=f"count:{mid}"))
                mk.add(SALAH_BUTTON())
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, mid, reply_markup=mk)
                except Exception:
                    pass
                if count % 1000 == 0:
                    bot.answer_callback_query(call.id, f"🎉 ما شاء الله! {count:,} ذكر!", show_alert=True)
                elif count % 100 == 0:
                    bot.answer_callback_query(call.id, f"✨ {count:,} ذكر! بارك الله فيكم", show_alert=True)
                elif count % 33 == 0:
                    bot.answer_callback_query(call.id, "سبحان الله وبحمده!")
                else:
                    bot.answer_callback_query(call.id, random.choice(["تقبل الله ✓","بارك الله فيك ✓","جزاك الله خيراً ✓"]))
            else:
                bot.answer_callback_query(call.id, "جاري التحميل...")
        except Exception as e:
            print(f"[Counter] خطأ: {e}")
            bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'show_group_conditions')
def handle_group_conditions(call):
    bot.answer_callback_query(call.id)
    text = (
        "هذا القسم مخصص لأصحاب القنوات و المجموعات فقط ، شارك البوت = مشاركة الأجر 🌟.\n\n"
        "لا توجد أي شروط لأضافة هذا البوت في مجموعتك ، كل ما عليك فعله هوا ان تضغط زر "
        "أضافة البوت في المجموعة و تقوم بأختيار الجروب ، البوت سيقوم بأرسال رسالة الاعدادت التي تتضمن تغير المنطقة "
        "ليقوم البوت بأرسال مواعيد الصلاه اختر بلدك و سيقوم بأرسال تذكير قبل 20د من الاذان لتنبيه الاعضا�� ، "
        "��يضا تستطيع تغير موعد ارسال التلاوات القرآنية و الاذكار و الآيات القرآنية.\n\n"
        "<b>البوت مجهز بالكامل بفضل الله لكي يلائم جميع جروبات العالم العربي ان شاء الله 🤎</b>"
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        "أضافة البوت في المجموعة ⚙",
        url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
    ))
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    try:
        bot.edit_message_text(
            text, call.message.chat.id, call.message.message_id,
            reply_markup=mk, parse_mode='HTML'
        )
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=mk, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: c.data == 'show_help')
def handle_show_help(call):
    bot.answer_callback_query(call.id)
    text = (
        'التعليمات والأوامر 🌟\n'
        '━━━━━━━━━━━━━━━━━━━━\n'
        '*[ محادثة خاصة ( الشات هذا ) ‼️ ]*\n'
        '• /start        ← القائمة الرئيسية\n'
        '• /azkar       ← أذكار النوم والاستيقاظ\n'
        '• /hadith     ← حديث شريف عشوائي\n'
        '• /ayah        ← آية قرآنية مع التفسير\n'
        '• /counter  ← عداد ذكر شخصي\n\n'
        '*[ أوامر المجموعات ‼️]*\n'
        '• /play         ← تفعيل البوت (للمشرفين)\n'
        '• /settings  ← لوحة الإعدادات\n'
        '• /counter  ← عداد ذكر جماعي\n'
        '• /prayer    ← تذكيرات الصلاة\n'
        '• /setcity    ← تحديد المدينة\n'
        '• /hadith    ← حديث شريف\n'
        '• /ayah       ← آية قرآنية\n'
        '• /settings ←  التوقيت\n'
        '━━━━━━━━━━━━━━━━━━━━\n'
        '*- استخدم الأزرار في الأسفل 👇.*'
    )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("شروط اضافة البوت في المجموعات ⛔️", callback_data="show_group_conditions"))
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=mk, parse_mode='Markdown')
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=mk, parse_mode='Markdown')


# ══════════════════════════════════════════════════
#       معالجات زر الورد اليومي
# ══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == 'ward_open')
def handle_ward_open(call):
    cid = call.message.chat.id
    ensure_user(cid)
    bot.answer_callback_query(call.id)
    u = get_user(cid)
    if u and int(u.get('ward_subscribed') or 0) == 1:
        try:
            bot.edit_message_text(
                "*انت مشترك بالفعل في الورد اليومي يا صديقي ☑️.*",
                cid, call.message.message_id,
                reply_markup=ward_already_subscribed_markup(),
                parse_mode='Markdown'
            )
        except Exception:
            bot.send_message(cid,
                "*انت مشترك بالفعل في الورد اليومي يا صديقي ☑️.*",
                reply_markup=ward_already_subscribed_markup(), parse_mode='Markdown'
            )
        return
    try:
        bot.edit_message_text(
            ward_welcome_text(), cid, call.message.message_id,
            reply_markup=ward_welcome_markup(), parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(cid, ward_welcome_text(), reply_markup=ward_welcome_markup(), parse_mode='Markdown')


@bot.callback_query_handler(func=lambda c: c.data == 'ward_new_start')
def handle_ward_new_start(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    mk = types.InlineKeyboardMarkup(row_width=2)
    mk.row(
        types.InlineKeyboardButton("نعم ☑️", callback_data="ward_confirm_new"),
        types.InlineKeyboardButton("لا ، ارد الورد القديم ‼️", callback_data="ward_restore_old")
    )
    try:
        bot.edit_message_text(
            "سيتم مسح الورد القديم و سنبدأ من الصفر هل انت جاهز ؟!",
            cid, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(cid, "سيتم مسح الورد القديم و سنبدأ من الصفر هل انت جاهز ؟!", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'ward_confirm_new')
def handle_ward_confirm_new(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    with db() as conn:
        conn.execute(
            "UPDATE users SET ward_subscribed=0, ward_pages_day=0, "
            "ward_current_page=1, ward_last_reminded='', ward_done_today=0 WHERE chat_id=?",
            (cid,)
        )
    try:
        bot.edit_message_text(
            ward_welcome_text(), cid, call.message.message_id,
            reply_markup=ward_welcome_markup(), parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(cid, ward_welcome_text(), reply_markup=ward_welcome_markup(), parse_mode='Markdown')


@bot.callback_query_handler(func=lambda c: c.data == 'ward_restore_old')
def handle_ward_restore_old(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id, "حسنا ☑️")
    u         = get_user(cid)
    pages_day = int(u.get('ward_pages_day') or 0) if u else 0
    current_p = int(u.get('ward_current_page') or 1) if u else 1
    finish    = calc_khatma_finish(pages_day) if pages_day > 0 else "—"
    mk        = ward_confirmed_markup()
    try:
        bot.edit_message_text(
            f"حسنا ☑️\n\n"
            f"وردك الحالي :\n"
            f"📄 الصفحة الحالية : *{current_p}*\n"
            f"📅 ستنهي الختمة بإذن الله : *{finish}*\n\n"
            f"سأذكّرك يومياً في الساعة الثالثة عصراً 🌱.",
            cid, call.message.message_id,
            reply_markup=mk, parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(cid, "حسنا ☑️ — وردك محفوظ 🤍", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'ward_agree')
def handle_ward_agree(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    _ward_pages_waiting[cid] = True
    mk = ward_ask_pages_markup()
    try:
        bot.edit_message_text(
            "كم صفحة تريد أن تقرأ يومياً ؟\n\n"
            "أرسل رقماً ( مثلاً: 5 أو 10 أو 20 )",
            cid, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(cid,
            "كم صفحة تريد أن تقرأ يومياً ؟\n\nأرسل رقماً ( مثلاً: 5 أو 10 أو 20 )",
            reply_markup=mk
        )


@bot.callback_query_handler(func=lambda c: c.data.startswith('ward_startday:'))
def handle_ward_startday(call):
    cid    = call.message.chat.id
    choice = call.data.split(':')[1]          # 'today' أو 'tomorrow'
    pages  = _ward_start_waiting.pop(cid, None)
    if not pages:
        bot.answer_callback_query(call.id, "⚠️ انتهت الجلسة، ابدأ من جديد")
        return

    if choice == 'tomorrow':
        last_reminded = _get_cairo_date()     # لا يُرسَل اليوم
    else:
        last_reminded = ''                    # يُرسَل فوراً

    with db() as conn:
        conn.execute(
            "UPDATE users SET ward_pages_day=?, ward_subscribed=1, "
            "ward_current_page=1, ward_last_reminded=?, ward_done_today=0 WHERE chat_id=?",
            (pages, last_reminded, cid)
        )

    if choice == 'today':
        # حذف رسالة الأزرار ثم إرسال تذكير الورد فوراً
        bot.answer_callback_query(call.id, "✅ بالتوفيق! جاري إرسال وردك الأول 🌱")
        try:
            bot.delete_message(cid, call.message.message_id)
        except Exception:
            pass
        send_ward_daily_reminder(cid)
        # منع الـ scheduler من إرسال تذكير ثانٍ اليوم
        with db() as conn:
            conn.execute(
                "UPDATE users SET ward_last_reminded=? WHERE chat_id=?",
                (_get_cairo_date(), cid)
            )
    else:
        bot.answer_callback_query(call.id, "📅 سيبدأ وردك من الغد بإذن الله 🌱")
        try:
            bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
        except Exception:
            pass
        bot.send_message(
            cid,
            "✅ تم! سأرسل لك تذكير وردك *غداً* في الساعة الثالثة عصراً بإذن الله 🤍",
            reply_markup=ward_confirmed_markup(),
            parse_mode='Markdown'
        )


@bot.callback_query_handler(func=lambda c: c.data == 'ward_cancel')
def handle_ward_cancel(call):
    cid = call.message.chat.id
    _ward_pages_waiting.pop(cid, None)
    _ward_start_waiting.pop(cid, None)
    bot.answer_callback_query(call.id, "تم الإلغاء")
    try:
        bot.edit_message_text(PRIVATE_WELCOME, cid, call.message.message_id,
                              reply_markup=khatma_menu_markup(cid), parse_mode='HTML')
    except Exception:
        send_welcome(cid)


@bot.callback_query_handler(func=lambda c: c.data == 'ward_done')
def handle_ward_done(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id, "بارك الله فيك! ✅")
    u = get_user(cid)
    if not u:
        return
    pages_day = int(u.get('ward_pages_day') or 0)
    current_p = int(u.get('ward_current_page') or 1)
    next_page = min(current_p + pages_day, QURAN_PAGES + 1)
    today     = _get_cairo_date()
    if next_page > QURAN_PAGES:
        with db() as conn:
            conn.execute(
                "UPDATE users SET ward_current_page=1, ward_done_today=1, "
                "ward_last_reminded=?, khatma_count=khatma_count+1 WHERE chat_id=?",
                (today, cid)
            )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
        try:
            bot.edit_message_text(
                "🏆 مبروك! أتممت ختمة القرآن الكريم بفضل الله 🤍\n\n"
                "تقبل الله منك وجعله في ميزان حسناتك\n"
                "سيُعاد تعيين وردك من الصفحة الأولى ✨",
                cid, call.message.message_id, reply_markup=mk
            )
        except Exception:
            bot.send_message(cid,
                "🏆 مبروك! أتممت ختمة القرآن الكريم بفضل الله 🤍", reply_markup=mk)
        return
    with db() as conn:
        conn.execute(
            "UPDATE users SET ward_current_page=?, ward_done_today=1, ward_last_reminded=? WHERE chat_id=?",
            (next_page, today, cid)
        )
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("الرجوع الي القائمة الرئيسية ‼️", callback_data="khatma_back"))
    try:
        bot.edit_message_text(
            f"✅ أحسنت يا بطل! قرأت وردك اليوم 🤍\n\n"
            f"📄 وردك غداً سيبدأ من الصفحة *{next_page}* بإذن الله 🌱\n\n"
            f"سأذكّرك غداً الساعة الثالثة عصراً ان شاء الله .",
            cid, call.message.message_id, reply_markup=mk, parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(cid, f"✅ أحسنت! وردك غداً من الصفحة *{next_page}* 🤍",
                         reply_markup=mk, parse_mode='Markdown')


# ══════════════════════════════════════════════════
#   معالج إنهاء الورد عبر رابط موقع quran.com
# ══════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_url_ward_done:'))
def handle_khatma_url_ward_done(call):
    """
    يُستدعى عندما يضغط المستخدم «✅ أنهيت وردي» بعد القراءة عبر رابط quran.com
    callback_data = khatma_url_ward_done:{current_page}:{pages_day}
    """
    cid = call.message.chat.id
    bot.answer_callback_query(call.id, "بارك الله فيك! ✅", show_alert=False)
    try:
        parts     = call.data.split(':')
        current   = int(parts[1])
        pages_day = int(parts[2])
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "⚠️ بيانات غير صحيحة", show_alert=True)
        return

    next_page = min(current + pages_day, QURAN_PAGES + 1)
    today     = _get_cairo_date()

    # حساب streak ومتغيرات التتبع
    import datetime as _dt
    u           = get_user(cid)
    interval_h  = int(u.get('ward_interval_hours') or 24) if u else 24
    next_ward_ts= str(time.time() + interval_h * 3600)
    last_date   = (u.get('khatma_last_read_date') or '') if u else ''
    streak      = int(u.get('khatma_streak')  or 0) if u else 0
    missed      = int(u.get('khatma_missed')  or 0) if u else 0
    if last_date == today:
        pass
    elif last_date:
        try:
            diff = (_dt.date.fromisoformat(today) - _dt.date.fromisoformat(last_date)).days
            streak = streak + 1 if diff == 1 else 1
            if diff > 1:
                missed += max(0, diff - 1)
        except Exception:
            streak = 1
    else:
        streak = 1

    if next_page > QURAN_PAGES:
        # أتمّ الختمة كاملة
        with db() as conn:
            conn.execute(
                "UPDATE users SET khatma_current=1, khatma_count=khatma_count+1, "
                "ward_reminder_sent=0, next_ward_at=?, "
                "khatma_streak=?, khatma_missed=?, khatma_last_read_date=? WHERE chat_id=?",
                (next_ward_ts, streak, missed, today, cid)
            )
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="khatma_back"))
        try:
            bot.edit_message_text(
                "╔══════════════════════╗\n"
                "  🏆  مبروك! أتممت الختمة\n"
                "╚══════════════════════╝\n\n"
                "أتممت ختمة القرآن الكريم بفضل الله 🤍\n\n"
                "تقبل الله منك وجعله في ميزان حسناتك\n"
                "وأعانك على ختمات قادمة بإذن الله 🌟\n\n"
                "سيُعاد تعيين وردك من الصفحة الأولى ✨",
                cid, call.message.message_id, reply_markup=mk
            )
        except Exception:
            bot.send_message(cid,
                "🏆 مبروك! أتممت ختمة القرآن الكريم 🤍\n"
                "تقبل الله منك وجعله في ميزان حسناتك 🌟",
                reply_markup=mk
            )
        return

    # حفظ الصفحة الجديدة + تحديث كل حقول التتبع
    with db() as conn:
        conn.execute(
            "UPDATE users SET khatma_current=?, ward_reminder_sent=0, "
            "next_ward_at=?, khatma_streak=?, khatma_missed=?, khatma_last_read_date=? "
            "WHERE chat_id=?",
            (next_page, next_ward_ts, streak, missed, today, cid)
        )

    # بناء رسالة الإنجاز
    end_page_done = min(current + pages_day - 1, QURAN_PAGES)
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton(
        f"📖  افتح الصفحة التالية ({next_page})",
        web_app=types.WebAppInfo(url=_quran_page_url(next_page))
    ))
    mk.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="khatma_back"))
    try:
        bot.edit_message_text(
            f"╔══════════════════════╗\n"
            f"  ✅  أحسنت! أكملت وردك اليوم\n"
            f"╚══════════════════════╝\n\n"
            f"قرأت من الصفحة *{current}* إلى الصفحة *{end_page_done}* 🌹\n\n"
            f"📄  وردك التالي يبدأ من الصفحة *{next_page}*\n"
            f"سأذكّرك في موعدك القادم إن شاء الله 🌱\n\n"
            f"_إن الذين يتلون كتاب الله وأقاموا الصلاة_\n"
            f"_يتلون تجارة لن تبور_ 🤍",
            cid, call.message.message_id,
            reply_markup=mk, parse_mode='Markdown'
        )
    except Exception:
        bot.send_message(
            cid,
            f"✅ أحسنت! قرأت صفحة *{current}* → *{end_page_done}*\n"
            f"وردك التالي من الصفحة *{next_page}* 🌱",
            reply_markup=mk, parse_mode='Markdown'
        )


# ── ختمة القرآن ──
@bot.callback_query_handler(func=lambda c: c.data == 'khatma_back')
def handle_khatma_back(call):
    cid = call.message.chat.id
    try:
        bot.delete_message(cid, call.message.message_id)
    except Exception:
        pass
    send_welcome(cid)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_start')
def handle_khatma_start(call):
    ensure_user(call.message.chat.id)
    u    = get_user(call.message.chat.id) or {}
    curr = u.get('khatma_pages_day', 20)
    text = (
        "╔══════════════════════╗\n"
        "  📖  ختمة القرآن الكريم\n"
        "╚══════════════════════╝\n\n"
        "اختر عدد الصفحات التي ستقرأها يومياً:\n\n"
        f"📄  القرآن الكريم = {QURAN_PAGES} صفحة"
    )
    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=khatma_pages_markup(curr))
    except Exception:
        bot.send_message(call.message.chat.id, text, reply_markup=khatma_pages_markup(curr))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('kp_'))
def handle_kp(call):
    parts  = call.data.split(':')
    action = parts[0]
    cid    = call.message.chat.id
    if action == 'kp_ignore':
        bot.answer_callback_query(call.id)
        return
    curr = int(parts[1]) if len(parts) > 1 else 20
    if action == 'kp_minus':
        curr = max(1, curr - 1)
    elif action == 'kp_plus':
        curr = min(QURAN_PAGES, curr + 1)
    elif action == 'kp_set':
        curr = int(parts[1])
    elif action == 'kp_confirm':
        ensure_user(cid)
        today = str(date.today())
        with db() as conn:
            conn.execute(
                "UPDATE users SET khatma_pages_day=?, khatma_start=?, khatma_current=1, "
                "next_ward_at='', ward_reminder_sent=0, "
                "khatma_streak=0, khatma_missed=0, khatma_last_read_date='' WHERE chat_id=?",
                (curr, today, cid)
            )
        text = khatma_confirm_text(curr)
        mk   = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("📖 متابعة الختمة", callback_data="khatma_continue"))
        mk.add(types.InlineKeyboardButton("🔙 رجوع",          callback_data="khatma_back"))
        try:
            bot.edit_message_text(text, cid, call.message.message_id, reply_markup=mk)
        except Exception:
            bot.send_message(cid, text, reply_markup=mk)
        bot.answer_callback_query(call.id, "تم بدء الختمة! بارك الله فيك 🤍")
        import threading as _t
        _t.Thread(target=send_quran_page, args=(cid, 1, 1, curr), daemon=True).start()
        return
    text = (
        "╔══════════════════════╗\n"
        "  📖  ختمة القرآن الكريم\n"
        "╚══════════════════════╝\n\n"
        "اختر عدد الصفحات اليومية:\n\n"
        f"{khatma_preview(curr)}"
    )
    try:
        bot.edit_message_text(text, cid, call.message.message_id, reply_markup=khatma_pages_markup(curr))
    except Exception:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_stats')
def handle_khatma_stats(call):
    bot.answer_callback_query(call.id)
    show_khatma_stats(call.message.chat.id, call)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_continue')
def handle_khatma_continue(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    text, mk = build_khatma_continue_text(cid)
    if text is None:
        bot.answer_callback_query(call.id, "لم تبدأ ختمة بعد!", show_alert=True)
        return
    try:
        bot.edit_message_text(text, cid, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(cid, text, reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_import')
def handle_khatma_import(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    _import_waiting[cid] = True
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="khatma_import_cancel"))
    try:
        bot.edit_message_text(
            f"📌  أرسل رقم الصفحة التي وصلت إليها\n(من 1 إلى {QURAN_PAGES})",
            cid, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(cid,
            f"📌  أرسل رقم الصفحة التي وصلت إليها\n(من 1 إلى {QURAN_PAGES})", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_import_cancel')
def handle_import_cancel(call):
    cid = call.message.chat.id
    _import_waiting.pop(cid, None)
    bot.answer_callback_query(call.id, "تم الإلغاء")
    send_welcome(cid)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_ward_stats')
def handle_ward_stats(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    text, mk = build_ward_stats_text(cid)
    if text is None:
        bot.answer_callback_query(call.id, "لا توجد ختمة نشطة!", show_alert=True)
        return
    try:
        bot.edit_message_text(text, cid, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(cid, text, reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_free_start')
def handle_free_start(call):
    cid = call.message.chat.id
    u   = get_user(cid)
    if not u or not u.get('khatma_start'):
        bot.answer_callback_query(call.id, "لا توجد ختمة نشطة!", show_alert=True)
        return
    bot.answer_callback_query(call.id, "جاري إحضار الصفحة... 📖")
    page = int(u.get('khatma_current') or 1)
    _send_free_page(cid, page)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_free_next:'))
def handle_free_next(call):
    page = int(call.data.split(':')[1]) + 1
    if page > QURAN_PAGES:
        bot.answer_callback_query(call.id, "وصلت لنهاية المصحف 🎉", show_alert=True)
        return
    bot.answer_callback_query(call.id, f"الصفحة {page} ✨")
    _edit_free_page(call, page)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_free_prev:'))
def handle_free_prev(call):
    page = int(call.data.split(':')[1]) - 1
    if page < 1:
        bot.answer_callback_query(call.id, "هذه أول صفحة في المصحف")
        return
    bot.answer_callback_query(call.id, f"الصفحة {page}")
    _edit_free_page(call, page)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_free_stop:'))
def handle_free_stop(call):
    cid        = call.message.chat.id
    page       = int(call.data.split(':')[1])
    saved_page = min(page + 1, QURAN_PAGES + 1)
    with db() as conn:
        conn.execute("UPDATE users SET khatma_current=? WHERE chat_id=?", (saved_page, cid))
    bot.answer_callback_query(call.id, f"✅  تم حفظ موضعك عند الصفحة {saved_page}", show_alert=True)
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📖 متابعة الختمة",    callback_data="khatma_continue"))
    mk.add(types.InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="khatma_back"))
    try:
        bot.edit_message_caption(
            f"🛑  توقفت عند الصفحة  {page}\n"
            f"📌  محفوظ — سيبدأ وردك القادم من الصفحة  {saved_page}\n\n"
            f"جزاك الله خيراً على ما قرأت 🤍",
            chat_id=cid, message_id=call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(cid,
            f"🛑  توقفت عند الصفحة  {page}\n"
            f"📌  محفوظ — الصفحة  {saved_page}\n\n"
            f"جزاك الله خيراً على ما قرأت 🤍", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_read_start')
def handle_read_start(call):
    cid = call.message.chat.id
    u   = get_user(cid)
    if not u or not u.get('khatma_start'):
        bot.answer_callback_query(call.id, "لم تبدأ ختمة بعد!", show_alert=True)
        return
    bot.answer_callback_query(call.id, "جاري إحضار الصفحة... 📖")
    current   = int(u.get('khatma_current')   or 1)
    pages_day = int(u.get('khatma_pages_day') or 20)
    send_quran_page(cid, current, current, pages_day)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_nav_next:'))
def handle_nav_next(call):
    cid   = call.message.chat.id
    parts = call.data.split(':')
    shown_page = int(parts[1])
    ward_start = int(parts[2])
    pages_day  = int(parts[3])
    progress   = shown_page - ward_start + 1
    is_last    = (progress >= pages_day)
    u = get_user(cid)
    if not u:
        bot.answer_callback_query(call.id)
        return
    next_page  = shown_page + 1
    if shown_page >= QURAN_PAGES:
        bot.answer_callback_query(call.id, "مبروك! أتممت الختمة 🎉", show_alert=True)
        _complete_khatma(cid)
        return
    current_db = int(u.get('khatma_current') or 1)
    if next_page > current_db:
        with db() as conn:
            conn.execute("UPDATE users SET khatma_current=? WHERE chat_id=?", (next_page, cid))
    if is_last:
        bot.answer_callback_query(call.id, "ما شاء الله! أكملت ورد اليوم 🌟", show_alert=True)
        _finish_daily_ward(cid, next_page, pages_day)
    else:
        bot.answer_callback_query(call.id, f"الصفحة {next_page} ✨")
        edit_quran_page(call, next_page, ward_start, pages_day)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_nav_prev:'))
def handle_nav_prev(call):
    cid   = call.message.chat.id
    parts = call.data.split(':')
    shown_page = int(parts[1])
    ward_start = int(parts[2])
    pages_day  = int(parts[3])
    prev_page  = shown_page - 1
    if prev_page < ward_start:
        bot.answer_callback_query(call.id, "هذه أول صفحة في الورد")
        return
    bot.answer_callback_query(call.id, f"الصفحة {prev_page}")
    edit_quran_page(call, prev_page, ward_start, pages_day)


@bot.callback_query_handler(func=lambda c: c.data == 'khatma_set_interval')
def handle_set_interval(call):
    cid    = call.message.chat.id
    u      = get_user(cid)
    curr_h = int(u.get('ward_interval_hours') or 24) if u else 24
    mk     = types.InlineKeyboardMarkup(row_width=2)
    options = [(6,"كل 6 ساعات"),(12,"كل 12 ساعة"),(24,"يومياً"),(48,"كل يومين")]
    for h, label in options:
        check = " ✅" if curr_h == h else ""
        mk.add(types.InlineKeyboardButton(label + check, callback_data=f"khatma_interval_set:{h}"))
    mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="khatma_continue"))
    try:
        bot.edit_message_text("⏰  اختر فترة الورد اليومي:", cid, call.message.message_id, reply_markup=mk)
    except Exception:
        bot.send_message(cid, "⏰  اختر فترة الورد اليومي:", reply_markup=mk)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith('khatma_interval_set:'))
def handle_interval_set(call):
    cid = call.message.chat.id
    h   = int(call.data.split(':')[1])
    with db() as conn:
        conn.execute("UPDATE users SET ward_interval_hours=? WHERE chat_id=?", (h, cid))
    label = f"{h} ساعة" if h < 24 else f"{h // 24} يوم"
    bot.answer_callback_query(call.id, f"✅  تم الضبط: كل {label}", show_alert=True)
    text, mk = build_khatma_continue_text(cid)
    if text:
        try:
            bot.edit_message_text(text, cid, call.message.message_id, reply_markup=mk)
        except Exception:
            bot.send_message(cid, text, reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'azkar_daily_toggle')
def handle_azkar_daily_toggle(call):
    cid = call.message.chat.id
    u   = get_user(cid)
    if not u:
        bot.answer_callback_query(call.id)
        return
    new_state = 0 if u.get('azkar_daily_enabled', 0) else 1
    with db() as conn:
        conn.execute("UPDATE users SET azkar_daily_enabled=? WHERE chat_id=?", (new_state, cid))
    if new_state:
        bot.answer_callback_query(call.id, "✅  تم تفعيل أذكار الصباح والمساء اليومية!", show_alert=True)
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("⛔ إيقاف الأذكار اليومية", callback_data="azkar_daily_toggle"))
        mk.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="khatma_back"))
        try:
            bot.edit_message_text(
                "🌅  تم تفعيل أذكار الصباح والمساء\n\n"
                "✅  أذكار الصباح الساعة 5:30 صباحاً\n"
                "✅  أذكار المساء الساعة 4:00 عصراً\n\n"
                "بإذن الله ستكون سبباً في حفظك وبركتك 🤍",
                cid, call.message.message_id, reply_markup=mk
            )
        except Exception:
            bot.send_message(cid, "🌅  تم تفعيل أذكار الصباح والمساء ✅", reply_markup=mk)
    else:
        bot.answer_callback_query(call.id, "تم إيقاف الأذكار اليومية")
        send_welcome(cid)


@bot.callback_query_handler(func=lambda c: c.data == 'tilawa_start')
def handle_tilawa_start(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    _tilawa_waiting[cid] = True
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="tilawa_cancel"))
    reciters_sample = " | ".join(r["name"] for r in KNOWN_RECITERS[:6])
    try:
        bot.edit_message_text(
            "🎙️  تلاوة قرآنية\n\n"
            "أرسل اسم السورة واسم الشيخ في رسالة واحدة\n\n"
            "📌  مثال:\n"
            "   سورة الكهف - ماهر المعيقلي\n"
            "   يس العفاسي\n"
            "   الرحمن السديس\n\n"
            f"🎤  من القراء المتاحين:\n{reciters_sample}...",
            cid, call.message.message_id, reply_markup=mk
        )
    except Exception:
        bot.send_message(cid,
            "🎙️  أرسل اسم السورة + اسم الشيخ\n"
            "مثال: سورة الكهف - ماهر المعيقلي", reply_markup=mk)


@bot.callback_query_handler(func=lambda c: c.data == 'tilawa_cancel')
def handle_tilawa_cancel(call):
    cid = call.message.chat.id
    _tilawa_waiting.pop(cid, None)
    bot.answer_callback_query(call.id, "تم الإلغاء")
    send_welcome(cid)


# ── لوحة المطور ──
@bot.callback_query_handler(func=lambda c: c.data.startswith('dev_'))
def handle_dev(call):
    global dev_upload_mode, dev_broadcast_mode, dev_upload_sabah_mode, dev_upload_masaa_mode
    global dev_upload_quran_mode, dev_upload_group_daily_mode, dev_upload_kahf_mode
    global dev_upload_welcome_mode
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id)
        return
    action = call.data

    if action == 'dev_stats':
        with db() as conn:
            users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            groups   = conn.execute("SELECT COUNT(*) FROM group_settings WHERE active=1").fetchone()[0]
            khatmas  = conn.execute("SELECT SUM(khatma_count) FROM users").fetchone()[0] or 0
            counters = conn.execute("SELECT COUNT(*) FROM counters").fetchone()[0]
            dhikr    = conn.execute("SELECT SUM(count) FROM counters").fetchone()[0] or 0
            sabah_c  = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='sabah'").fetchone()[0]
            masaa_c  = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='masaa'").fetchone()[0]
            daily_u  = conn.execute("SELECT COUNT(*) FROM users WHERE azkar_daily_enabled=1").fetchone()[0]
            ward_sub = conn.execute("SELECT COUNT(*) FROM users WHERE ward_subscribed=1").fetchone()[0]
            pdfs     = len([f for f in os.listdir(_PDF_DIR) if f.endswith('.pdf')])
            wel_cnt  = conn.execute("SELECT COUNT(*) FROM welcome_image").fetchone()[0]
        text = (
            f"╔══════════════════════╗\n"
            f"  📊  إحصائيات البوت\n"
            f"╚══════════════════════╝\n\n"
            f"👥  المستخدمون:            {users}\n"
            f"🏠  المجموعات النشطة:      {groups}\n"
            f"📖  ختمات مكتملة:         {khatmas}\n"
            f"📿  عدادات منشأة:         {counters}\n"
            f"🤲  إجمالي الأذكار:       {dhikr:,}\n"
            f"🌅  صور أذكار الصباح:     {sabah_c}\n"
            f"🌆  صور أذكار المساء:     {masaa_c}\n"
            f"👤  مشتركون في اليومية:   {daily_u}\n"
            f"📅  مشتركو الورد اليومي:  {ward_sub}\n"
            f"📄  صفحات القرآن محفوظة:  {pdfs}\n"
            f"🖼️  صورة الترحيب:         {'موجودة ✅' if wel_cnt else '❌'}\n"
        )
        bot.send_message(call.message.chat.id, text)
        bot.answer_callback_query(call.id)

    elif action == 'dev_backup':
        import shutil, os as _os
        db_path = 'user_data.db'
        backup_path = 'user_data_backup.db'
        try:
            shutil.copy2(db_path, backup_path)
            with open(backup_path, 'rb') as f:
                bot.send_document(
                    call.message.chat.id, f,
                    caption=f"💾 *نسخة احتياطية من قاعدة البيانات*\n📅 {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M')}",
                    parse_mode='Markdown'
                )
            _os.remove(backup_path)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ خطأ: {e}")
        bot.answer_callback_query(call.id, "✅ تم إرسال النسخة الاحتياطية")

    elif action == 'dev_reactivate':
        with db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM group_settings").fetchone()[0]
            conn.execute(
                "UPDATE group_settings SET active=1, last_seq_time=0, left_reason='' WHERE active=0"
            )
            reactivated = conn.execute(
                "SELECT changes()"
            ).fetchone()[0]
        bot.send_message(
            call.message.chat.id,
            f"✅ *تم إعادة تفعيل {reactivated} مجموعة*\n\n"
            f"📊 إجمالي المجموعات: {total}\n"
            f"🔄 سيحاول البوت الإرسال للكل خلال دورة الجدولة القادمة.\n\n"
            f"⚠️ المجموعات اللي البوت مش قادر يكتب فيها (محتاج ادمن) هتتوقف تلقائياً مع ظهور السبب في الاحصائيات.",
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "✅ تم إعادة التفعيل")

    elif action == 'dev_group_stats':
        with db() as conn:
            rows = conn.execute(
                "SELECT group_id, group_name, active, seq_interval, left_reason, fail_count FROM group_settings ORDER BY active DESC"
            ).fetchall()
        if not rows:
            bot.send_message(call.message.chat.id, "📭 لا توجد مجموعات مسجلة حتى الآن.")
            bot.answer_callback_query(call.id)
            return
        enriched = []
        for r in rows:
            gid, gname, active, interval, left_reason, fail_count = r
            if not gname:
                try:
                    chat = bot.get_chat(gid)
                    gname = chat.title or f"مجموعة {gid}"
                    with db() as conn2:
                        conn2.execute("UPDATE group_settings SET group_name=? WHERE group_id=?", (gname, gid))
                except Exception:
                    gname = f"مجموعة {gid}"
            enriched.append((gid, gname, active, interval, left_reason or '', int(fail_count or 0)))
        active_groups   = [r for r in enriched if r[2] == 1]
        warn_groups     = [r for r in active_groups if r[5] > 0]
        inactive_groups = [r for r in enriched if r[2] != 1]
        lines = [
            f"╔══════════════════════╗\n"
            f"  🏠  احصائيات المجموعات\n"
            f"╚══════════════════════╝\n\n"
            f"✅  نشطة: {len(active_groups)}   |   ❌  متوقفة: {len(inactive_groups)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ]
        if active_groups:
            lines.append("▶️  *المجموعات النشطة (يبعت):*\n")
            for gid, gname, _, interval, _, fails in active_groups:
                warn = f"  ⚠️ {fails}/{MAX_FAIL_BEFORE_DEACTIVATE} تحذير" if fails > 0 else ""
                lines.append(f"• {gname}  —  كل {interval} د{warn}\n")
        if inactive_groups:
            lines.append("\n⏸️  *المجموعات المتوقفة:*\n")
            for gid, gname, _, interval, reason, _ in inactive_groups:
                reason_text = f"  ({reason})" if reason else "  (سبب غير معروف)"
                lines.append(f"• {gname}{reason_text}\n")
        text = "".join(lines)
        for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            bot.send_message(call.message.chat.id, chunk, parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif action == 'dev_upload_welcome':
        dev_upload_welcome_mode = True
        dev_upload_mode = dev_upload_sabah_mode = dev_upload_masaa_mode = False
        dev_upload_quran_mode = dev_upload_group_daily_mode = dev_upload_kahf_mode = False
        bot.send_message(call.message.chat.id,
            "🖼️  وضع رفع صورة الترحيب\n\n"
            "أرسل الصورة (مع وصف اختياري)\n"
            "ستظهر في رسالة /start للمستخدمين\n\n"
            "للإنهاء: /save"
        )
        bot.answer_callback_query(call.id)

    elif action == 'dev_del_welcome':
        with db() as conn:
            conn.execute("DELETE FROM welcome_image")
        bot.answer_callback_query(call.id, "🗑️  تم حذف صورة الترحيب")
        bot.send_message(call.message.chat.id, "✅  تم حذف صورة الترحيب", reply_markup=dev_menu_markup())

    elif action == 'dev_upload':
        dev_upload_mode = True
        dev_upload_quran_mode = dev_upload_sabah_mode = dev_upload_masaa_mode = False
        bot.send_message(call.message.chat.id,
            "📤  وضع رفع صفحات القرآن الفردية\n\n"
            "أرسل ملفات PDF — رقم الصفحة من اسم الملف أو الوصف\n"
            "مثال: page_1.pdf أو وصف: صفحة 1\n\n"
            "للإنهاء: /save"
        )
        bot.answer_callback_query(call.id)

    elif action == 'dev_upload_quran':
        dev_upload_quran_mode = True
        dev_upload_mode = dev_upload_sabah_mode = dev_upload_masaa_mode = False
        bot.send_message(call.message.chat.id,
            "📚  وضع رفع المصحف الكامل\n\n"
            "أرسل ملف PDF واحد يحتوي على كامل القرآن\n"
            "البوت سيقسّمه تلقائياً إلى 569 صفحة منفصلة\n\n"
            "✅  يدعم PDFs المشفرة تلقائياً\n"
            "⚠️  سيستغرق بعض الوقت\n"
            "للإلغاء: /save"
        )
        bot.answer_callback_query(call.id)

    elif action == 'dev_upload_sabah':
        dev_upload_sabah_mode = True
        dev_upload_masaa_mode = dev_upload_mode = dev_upload_quran_mode = False
        with db() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='sabah'").fetchone()[0]
        bot.send_message(call.message.chat.id,
            f"🌅  وضع رفع أذكار الصباح\nصور موجودة: {cnt}\n\nأرسل الصور\nللإنهاء: /save")
        bot.answer_callback_query(call.id)

    elif action == 'dev_upload_masaa':
        dev_upload_masaa_mode = True
        dev_upload_sabah_mode = dev_upload_mode = dev_upload_quran_mode = False
        with db() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='masaa'").fetchone()[0]
        bot.send_message(call.message.chat.id,
            f"🌆  وضع رفع أذكار المساء\nصور موجودة: {cnt}\n\nأرسل الصور\nللإنهاء: /save")
        bot.answer_callback_query(call.id)

    elif action == 'dev_del_sabah':
        with db() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='sabah'").fetchone()[0]
            conn.execute("DELETE FROM azkar_images WHERE type='sabah'")
        bot.answer_callback_query(call.id, f"🗑️  تم حذف {cnt} صورة")
        bot.send_message(call.message.chat.id, f"✅  تم حذف {cnt} صورة أذكار صباح", reply_markup=dev_menu_markup())

    elif action == 'dev_del_masaa':
        with db() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM azkar_images WHERE type='masaa'").fetchone()[0]
            conn.execute("DELETE FROM azkar_images WHERE type='masaa'")
        bot.answer_callback_query(call.id, f"🗑️  تم حذف {cnt} صورة")
        bot.send_message(call.message.chat.id, f"✅  تم حذف {cnt} صورة أذكار مساء", reply_markup=dev_menu_markup())

    elif action == 'dev_upload_group_daily':
        dev_upload_group_daily_mode = True
        dev_upload_sabah_mode = dev_upload_masaa_mode = dev_upload_mode = dev_upload_quran_mode = False
        bot.send_message(call.message.chat.id,
            "🖼️  وضع رفع الصورة اليومية للجروبات\n\n"
            "أرسل الصورة الجديدة (تستبدل القديمة)\n"
            "للإنهاء: /save")
        bot.answer_callback_query(call.id)

    elif action == 'dev_del_group_daily':
        with db() as conn:
            conn.execute("DELETE FROM azkar_images WHERE type='group_daily'")
        bot.answer_callback_query(call.id, "🗑️  تم حذف الصورة اليومية")
        bot.send_message(call.message.chat.id, "✅  تم حذف الصورة اليومية للجروبات", reply_markup=dev_menu_markup())

    elif action == 'dev_upload_kahf':
        dev_upload_kahf_mode = True
        dev_upload_mode = dev_upload_quran_mode = False
        dev_upload_sabah_mode = dev_upload_masaa_mode = dev_upload_group_daily_mode = False
        bot.send_message(call.message.chat.id,
            "📖 وضع رفع سورة الكهف\n\nأرسل ملف PDF مع الوصف\nللإنهاء: /save")
        bot.answer_callback_query(call.id)

    elif action == 'dev_del_kahf':
        with db() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM friday_kahf").fetchone()[0]
            conn.execute("DELETE FROM friday_kahf")
        bot.answer_callback_query(call.id, "🗑️  تم الحذف")
        bot.send_message(call.message.chat.id,
            f"✅  تم حذف سورة الكهف ({cnt} سجل)" if cnt else "⚠️  لا يوجد ملف محفوظ",
            reply_markup=dev_menu_markup())

    elif action == 'dev_broadcast':
        dev_broadcast_mode = True
        bot.send_message(call.message.chat.id, "📢  أرسل النص الذي تريد إرساله لجميع المستخدمين:")
        bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data in ['kp_ignore', 'ignore'])
def handle_ignore(call):
    bot.answer_callback_query(call.id)


# ══════════════════════════════════════════════════
#            جدولة مواقيت الصلاة
# ══════════════════════════════════════════════════
def prayer_scheduler():
    while True:
        try:
            now    = datetime.now(TIMEZONE)
            today  = now.strftime('%Y-%m-%d')
            # تنظيف التذكيرات القديمة من الذاكرة
            to_remove = {k for k in _prayer_sent if k[2] != today}
            _prayer_sent.difference_update(to_remove)
            with db() as conn:
                rows = conn.execute(
                    "SELECT group_id, city, country FROM group_settings WHERE prayer_enabled=1 AND active=1"
                ).fetchall()
            cities = {}
            for gid, city, country in rows:
                key = f"{city}_{country}"
                if key not in cities:
                    cities[key] = get_prayer_times(city, country)
            for gid, city, country in rows:
                key    = f"{city}_{country}"
                ptimes = cities.get(key)
                if not ptimes:
                    continue
                for name, pt in ptimes.items():
                    remind_at = pt - timedelta(minutes=20)
                    diff      = abs((remind_at - now).total_seconds())
                    if diff <= 60:
                        threading.Thread(
                            target=_send_prayer_msg,
                            args=(gid, name, pt, False), daemon=True
                        ).start()
        except Exception as e:
            print(f"[Prayer] خطأ: {e}")
        time.sleep(60)


PRAYER_REMINDER_TPL = {
    'Fajr': (
        "*صلاة الفجر بعد 20 دقيقــة 🌱.*\n"
        "\" الصلاة خير من النـــوم \"\n\n"
        "*ألحق نفسك و صليلك ركعتين قيــام و أدعي فيهم ، \" يخبر النبي ﷺ أن الله ينزل حين يبقى ثلث الليل الأخير ، فيقول : \"من يدعوني فأستجيب لهُ ، من يسألني فأعطيه ، من يستغفرني فأغفر له 🤎\".*\n"
        "*\\- موعد الأذان* : {t} ."
    ),
    'Dhuhr': (
        "*صلاة الظهر بعد 20 دقيقــة 🌱.*\n"
        "\" أسـتعد لهــا لتجدد طاقتك ! \" .\n"
        "*\\- موعد الأذان* : {t} ."
    ),
    'Asr': (
        "*صلاة العصر بعد 20 دقيقــة 🌱.*\n"
        "لو مش مصلي الظهــر قوم صلي بسرعة و حاول متأجلش الصــلاة ..!! .\n"
        "*\\- موعد الأذان* : {t} ."
    ),
    'Maghrib': (
        "*صلاة المغرب بعد 20 دقيقــة 🌱.*\n"
        "لو مش مصلي العصـر قوم صلي بسرعة و حاول متأجلش الصــلاة ..!! .\n"
        "*\\- موعد الأذان* : {t} ."
    ),
    'Isha': (
        "*صلاة العشـاء بعد 20 دقيقــة 🌱.*\n"
        "لو مش مصلي المغـرب قوم صلي بسرعة و حاول متأجلش الصــلاة ..!! .\n"
        "*\\- موعد الأذان* : {t} ."
    ),
}

# مفتاح لمنع إرسال نفس التذكير مرتين
_prayer_sent:      set            = set()
_prayer_sent_lock: threading.Lock = threading.Lock()

def _send_prayer_msg(gid, prayer_name, prayer_time, is_athan):
    date_key = prayer_time.strftime('%Y-%m-%d')
    sent_key = (gid, prayer_name, date_key)
    with _prayer_sent_lock:
        if sent_key in _prayer_sent:
            return
        _prayer_sent.add(sent_key)
    tstr = prayer_time.strftime('%I:%M %p').replace('AM', 'ص').replace('PM', 'م')
    try:
        msg = PRAYER_REMINDER_TPL.get(prayer_name, "🕌  الصلاة قربت").format(t=tstr)
        bot.send_message(gid, msg, parse_mode='Markdown')
    except Exception as e:
        _prayer_sent.discard(sent_key)
        print(f"[Prayer msg] خطأ للمجموعة {gid}: {e}")


# ══════════════════════════════════════════════════
#       جدولة تذكيرات الورد اليومي (3 عصراً)
# ══════════════════════════════════════════════════
def new_ward_daily_scheduler():
    WARD_HOUR, WARD_MIN = 15, 0
    while True:
        try:
            now   = datetime.now(TIMEZONE)
            today = now.strftime('%Y-%m-%d')
            if now.hour == WARD_HOUR and now.minute == WARD_MIN:
                with db() as conn:
                    users = conn.execute(
                        "SELECT chat_id, ward_last_reminded, ward_done_today "
                        "FROM users WHERE ward_subscribed=1 AND ward_pages_day>0"
                    ).fetchall()
                for chat_id, last_reminded, done_today in users:
                    if last_reminded == today:
                        continue
                    with db() as conn:
                        conn.execute(
                            "UPDATE users SET ward_done_today=0, ward_last_reminded=? WHERE chat_id=?",
                            (today, chat_id)
                        )
                    send_ward_daily_reminder(chat_id)
                    time.sleep(0.1)
        except Exception as e:
            print(f"[NewWardScheduler] خطأ: {e}")
        time.sleep(50)


# ══════════════════════════════════════════════════
#      جدولة تذكيرات الورد القديم (للختمة بالصفحات)
# ══════════════════════════════════════════════════
def ward_reminder_scheduler():
    while True:
        try:
            now = time.time()
            with db() as conn:
                users = conn.execute(
                    "SELECT chat_id, khatma_current, khatma_pages_day, "
                    "next_ward_at, ward_reminder_sent "
                    "FROM users WHERE khatma_start != '' AND khatma_start IS NOT NULL "
                    "AND next_ward_at != '' AND next_ward_at IS NOT NULL"
                ).fetchall()
            for row in users:
                chat_id, current, pages_day, next_ward_at, reminder_sent = row
                try:
                    if not next_ward_at:
                        continue
                    next_at        = float(next_ward_at)
                    reminder_sent  = int(reminder_sent or 0)
                    current        = int(current or 1)
                    pages_day      = int(pages_day or 20)
                    if reminder_sent == 0 and now >= next_at:
                        end_p = min(current + pages_day - 1, QURAN_PAGES)
                        mk = types.InlineKeyboardMarkup(row_width=1)
                        mk.add(types.InlineKeyboardButton(
                            f"📖  افتح المصحف — الصفحة {current}",
                            web_app=types.WebAppInfo(url=_quran_page_url(current))
                        ))
                        mk.add(types.InlineKeyboardButton(
                            "📱  اقرأ داخل البوت", callback_data="khatma_read_start"
                        ))
                        mk.add(types.InlineKeyboardButton(
                            "✅  أنهيت وردي",
                            callback_data=f"khatma_url_ward_done:{current}:{pages_day}"
                        ))
                        bot.send_message(chat_id,
                            f"يلا بينا نكمل وردنا! 🤍\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📖  من الصفحة *{current}*  إلى الصفحة *{end_p}*\n"
                            f"📚  {pages_day} صفحة لورد اليوم 🌱\n\n"
                            f"اضغط «افتح المصحف» للقراءة مباشرةً ✨\n"
                            f"_أو اقرأ داخل البوت بالأزرار 📱_",
                            reply_markup=mk,
                            parse_mode='Markdown'
                        )
                        with db() as conn:
                            conn.execute(
                                "UPDATE users SET ward_reminder_sent=1 WHERE chat_id=?", (chat_id,)
                            )
                    elif reminder_sent == 1 and now >= next_at + 5 * 3600:
                        end_p = min(current + pages_day - 1, QURAN_PAGES)
                        mk = types.InlineKeyboardMarkup(row_width=1)
                        mk.add(types.InlineKeyboardButton(
                            f"📖  افتح المصحف — الصفحة {current}",
                            web_app=types.WebAppInfo(url=_quran_page_url(current))
                        ))
                        mk.add(types.InlineKeyboardButton(
                            "📱  اقرأ داخل البوت", callback_data="khatma_read_start"
                        ))
                        mk.add(types.InlineKeyboardButton(
                            "✅  أنهيت وردي",
                            callback_data=f"khatma_url_ward_done:{current}:{pages_day}"
                        ))
                        bot.send_message(chat_id,
                            f"ايه يبطل مش ناوي تقرأ الورد اليوم !! 😤\n\n"
                            f"تفاصيل وردك :\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📖  من الصفحة *{current}*  إلى الصفحة *{end_p}*\n"
                            f"📚  {pages_day} صفحة لورد اليوم 🌱\n\n"
                            f"اضغط «افتح المصحف» للقراءة مباشرةً ✨\n"
                            f"_أو اقرأ داخل البوت بالأزرار 📱_",
                            reply_markup=mk,
                            parse_mode='Markdown'
                        )
                        with db() as conn:
                            conn.execute(
                                "UPDATE users SET ward_reminder_sent=2 WHERE chat_id=?", (chat_id,)
                            )
                except Exception as e:
                    print(f"[WardReminder] خطأ للمستخدم {row[0]}: {e}")
        except Exception as e:
            print(f"[WardReminder] خطأ عام: {e}")
        time.sleep(60)


# ══════════════════════════════════════════════════
#        جدولة الصورة اليومية للمجموعات
# ══════════════════════════════════════════════════
def group_daily_image_scheduler():
    while True:
        try:
            now   = datetime.now(TIMEZONE)
            today = now.strftime('%Y-%m-%d')
            h, mn = now.hour, now.minute
            is_midnight = (h == 0  and mn == 0)
            is_noon     = (h == 12 and mn == 0)
            if not is_midnight and not is_noon:
                time.sleep(30)
                continue
            col = 'last_gdaily_mid' if is_midnight else 'last_gdaily_noon'
            with db() as conn:
                row = conn.execute(
                    "SELECT file_id, caption, caption_entities FROM azkar_images WHERE type='group_daily' LIMIT 1"
                ).fetchone()
            if not row:
                time.sleep(55)
                continue
            file_id, saved_caption, saved_ent_json = row
            with db() as conn:
                groups = conn.execute(
                    f"SELECT group_id, {col} FROM group_settings WHERE active=1"
                ).fetchall()
            entities = json_to_entities(saved_ent_json)
            for gid, last_sent in groups:
                if last_sent == today:
                    continue
                try:
                    bot.send_photo(gid, file_id, caption=saved_caption,
                                   caption_entities=entities)
                    with db() as conn:
                        conn.execute(
                            f"UPDATE group_settings SET {col}=? WHERE group_id=?", (today, gid)
                        )
                except Exception as e:
                    _handle_group_error(gid, str(e))
                    print(f"[GroupDaily] خطأ للمجموعة {gid}: {e}")
                time.sleep(0.3)
        except Exception as e:
            print(f"[GroupDaily] خطأ عام: {e}")
        time.sleep(50)


# ══════════════════════════════════════════════════
#        جدولة أذكار الصباح والمساء اليومية
# ══════════════════════════════════════════════════
def _send_azkar_images(chat_id, azkar_type):
    with db() as conn:
        rows = conn.execute(
            "SELECT file_id, caption, caption_entities FROM azkar_images WHERE type=? ORDER BY order_num",
            (azkar_type,)
        ).fetchall()
    if not rows:
        return False
    for (file_id, caption, ent_json) in rows:
        try:
            entities = json_to_entities(ent_json)
            mk = types.InlineKeyboardMarkup()
            mk.add(SALAH_BUTTON())
            bot.send_photo(chat_id, file_id, caption=caption,
                           caption_entities=entities, reply_markup=mk)
            time.sleep(0.3)
        except Exception as e:
            print(f"[DailyAzkar] خطأ إرسال صورة لـ {chat_id}: {e}")
    return True


def daily_azkar_scheduler():
    SABAH_HOUR, SABAH_MIN = 5,  30
    MASAA_HOUR, MASAA_MIN = 16,  0
    while True:
        try:
            now   = datetime.now(TIMEZONE)
            today = now.strftime('%Y-%m-%d')
            h, mn = now.hour, now.minute
            is_sabah = (h == SABAH_HOUR and mn == SABAH_MIN)
            is_masaa = (h == MASAA_HOUR and mn == MASAA_MIN)
            if not is_sabah and not is_masaa:
                time.sleep(30)
                continue
            azkar_type = 'sabah' if is_sabah else 'masaa'
            col        = 'last_sabah_sent' if is_sabah else 'last_masaa_sent'
            title      = "أذكار الصباح 🌅" if is_sabah else "أذكار المساء 🌆"
            with db() as conn:
                users = conn.execute(
                    f"SELECT chat_id, {col} FROM users WHERE azkar_daily_enabled=1"
                ).fetchall()
            for chat_id, last_sent in users:
                if last_sent == today:
                    continue
                try:
                    mk = types.InlineKeyboardMarkup()
                    mk.add(SALAH_BUTTON())
                    bot.send_message(chat_id,
                        f"📿 {title} 🤎\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"اللهم بك أصبحنا وبك أمسينا وبك نحيا وبك نموت وإليك النشور 🌱 .",
                        reply_markup=mk
                    )
                    sent = _send_azkar_images(chat_id, azkar_type)
                    if not sent:
                        mk2 = types.InlineKeyboardMarkup()
                        mk2.add(SALAH_BUTTON())
                        fallback = (
                            "📿  أذكار الصباح\n\n"
                            "• أعوذ بالله السميع العليم من الشيطان الرجيم (ثلاثاً)\n"
                            "• أصبحنا وأصبح الملك لله (ثلاثاً)\n"
                            "• اللهم عافني في بدني، في سمعي، في بصري\n"
                            "• اللهم بارك لي في وقتي وعملي"
                        ) if azkar_type == 'sabah' else (
                            "📿  أذكار المساء\n\n"
                            "• أعوذ بكلمات الله التامات من شر ما خلق (ثلاثاً)\n"
                            "• أمسينا وأمسى الملك لله (ثلاثاً)\n"
                            "• اللهم إني أمسيت أُشهدك وأُشهد حملة عرشك\n"
                            "• اللهم إنك عفو تحب العفو فاعف عني"
                        )
                        bot.send_message(chat_id, fallback, reply_markup=mk2)
                    with db() as conn:
                        conn.execute(
                            f"UPDATE users SET {col}=? WHERE chat_id=?", (today, chat_id)
                        )
                except Exception as e:
                    print(f"[DailyAzkar] خطأ للمستخدم {chat_id}: {e}")
                time.sleep(0.05)
        except Exception as e:
            print(f"[DailyAzkar] خطأ عام: {e}")
        time.sleep(50)


# ══════════════════════════════════════════════════
#         جدولة تذكير الجمعة - سورة الكهف
# ══════════════════════════════════════════════════
def friday_kahf_scheduler():
    sent_dates = set()
    while True:
        try:
            now   = datetime.now(TIMEZONE)
            today = now.strftime('%Y-%m-%d')
            is_friday_fajr = (now.weekday() == 4 and now.hour == 10 and now.minute == 0)
            if not is_friday_fajr or today in sent_dates:
                time.sleep(30)
                continue
            with db() as conn:
                row = conn.execute(
                    "SELECT file_id, caption, caption_entities FROM friday_kahf ORDER BY id DESC LIMIT 1"
                ).fetchone()
            if not row:
                time.sleep(55)
                continue
            file_id, caption, ent_json = row
            entities = json_to_entities(ent_json)
            user_mk = types.InlineKeyboardMarkup()
            user_mk.add(SALAH_BUTTON())
            with db() as conn:
                groups = conn.execute("SELECT group_id FROM group_settings WHERE active=1").fetchall()
            for (gid,) in groups:
                try:
                    msg = bot.send_document(gid, file_id, caption=caption,
                                            caption_entities=entities)
                    try:
                        bot.pin_chat_message(gid, msg.message_id, disable_notification=False)
                    except Exception:
                        pass
                    time.sleep(0.4)
                except Exception as e:
                    _handle_group_error(gid, str(e))
                    print(f"[FridayKahf] خطأ للجروب {gid}: {e}")
            with db() as conn:
                users = conn.execute("SELECT chat_id FROM users").fetchall()
            for (uid,) in users:
                try:
                    bot.send_document(uid, file_id, caption=caption,
                                      caption_entities=entities, reply_markup=user_mk)
                    time.sleep(0.05)
                except Exception as e:
                    print(f"[FridayKahf] خطأ للمستخدم {uid}: {e}")
            sent_dates.add(today)
            print(f"[FridayKahf] ✅ تم إرسال سورة الكهف بتاريخ {today}")
        except Exception as e:
            print(f"[FridayKahf] خطأ عام: {e}")
        time.sleep(50)


# ══════════════════════════════════════════════════
#                   التشغيل (Flask + Polling)
# ══════════════════════════════════════════════════

def _keepalive_scheduler():
    """يضرب /health كل 5 دقايق عشان السيرفر ما يناموش"""
    import urllib.request
    time.sleep(30)                          # استنى السيرفر يبدأ الأول
    health_url = f"{os.environ.get('WEBHOOK_URL', '').rstrip('/')}/health"
    if not health_url.startswith("http"):
        return                              # لو مفيش URL، مفيش داعي
    while True:
        try:
            with urllib.request.urlopen(health_url, timeout=10) as _r:
                if _r.status == 200:
                    print(f"[Keepalive] ✅ {health_url}")
                else:
                    print(f"[Keepalive] ⚠️ status={_r.status}")
        except Exception as _e:
            print(f"[Keepalive] ❌ {_e}")
        time.sleep(300)                     # كل 5 دقايق


def _start_schedulers():
    threading.Thread(target=group_scheduler,             daemon=True).start()
    threading.Thread(target=prayer_scheduler,            daemon=True).start()
    threading.Thread(target=daily_azkar_scheduler,       daemon=True).start()
    threading.Thread(target=group_daily_image_scheduler, daemon=True).start()
    threading.Thread(target=ward_reminder_scheduler,     daemon=True).start()
    threading.Thread(target=friday_kahf_scheduler,       daemon=True).start()
    threading.Thread(target=new_ward_daily_scheduler,    daemon=True).start()
    threading.Thread(target=_get_mp3quran_reciters,      daemon=True).start()
    threading.Thread(target=_keepalive_scheduler,        daemon=True).start()

# ══════════════════════════════════════════════════════════════
#   نقطة الدخول الرئيسية — يدعم Flask / Sanic / Polling
#   متغيرات البيئة:
#     BOT_MODE      = webhook | polling        (افتراضي: polling)
#     SERVER_ENGINE = flask | sanic            (افتراضي: flask)
#     WEBHOOK_URL   = https://yourdomain.com   (مطلوب في وضع webhook)
#     WEBHOOK_PATH  = /webhook                 (افتراضي: /webhook)
#     WEBHOOK_HOST  = 0.0.0.0
#     WEBHOOK_PORT  = 8443
#     WEBHOOK_SECRET= (اختياري)
#     SSL_CERT      = /path/cert.pem           (اختياري)
#     SSL_KEY       = /path/key.pem            (اختياري)
# ══════════════════════════════════════════════════════════════

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
_log = logging.getLogger("BotRunner")

# ── قيم افتراضية لـ alwaysdata (تُستخدم فقط إذا لم تكن المتغيرات مضبوطة) ──
os.environ.setdefault("BOT_MODE",      "webhook")
os.environ.setdefault("SERVER_ENGINE", "sanic")
os.environ.setdefault("WEBHOOK_URL",   "https://betar13.alwaysdata.net")
os.environ.setdefault("WEBHOOK_PATH",  "/webhook")
os.environ.setdefault("WEBHOOK_SECRET","")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_BOT_MODE      = os.getenv("BOT_MODE",      "polling").lower()
_SERVER_ENGINE = os.getenv("SERVER_ENGINE", "flask").lower()
_WEBHOOK_HOST  = os.getenv("WEBHOOK_HOST",  "0.0.0.0")
_WEBHOOK_PORT  = int(os.getenv("WEBHOOK_PORT", "8443"))
_WEBHOOK_URL   = os.getenv("WEBHOOK_URL",   "").rstrip("/")
_WEBHOOK_PATH  = os.getenv("WEBHOOK_PATH",  "/webhook")
_WEBHOOK_SECRET= os.getenv("WEBHOOK_SECRET","")
_SSL_CERT      = os.getenv("SSL_CERT", None) or None
_SSL_KEY       = os.getenv("SSL_KEY",  None) or None


# ── وضع Polling مع إعادة التشغيل التلقائية ──────────────────────
def _run_polling():
    _log.info("🔄 بدء وضع Polling مع إعادة التشغيل التلقائية...")
    bot.remove_webhook()
    time.sleep(1)
    _restart_count = 0
    while True:
        try:
            _log.info(f"🟢 بدء infinity_polling (محاولة {_restart_count + 1})")
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                allowed_updates=["message", "callback_query", "my_chat_member"],
                restart_on_change=False,
                skip_pending=False,
            )
        except KeyboardInterrupt:
            _log.info("🛑 تم الإيقاف يدوياً")
            break
        except Exception as _e:
            _restart_count += 1
            _wait = min(10 * _restart_count, 60)
            _log.warning(f"⚠️ توقف Polling: {_e} — إعادة التشغيل بعد {_wait}ث")
            time.sleep(_wait)


# ── وضع Webhook مع Flask ─────────────────────────────────────────
def _run_flask():
    try:
        from flask import Flask, request, abort
    except ImportError:
        _log.error("❌ Flask غير مثبت — pip install flask")
        sys.exit(1)
    import telebot as _tb

    _full_url = f"{_WEBHOOK_URL}{_WEBHOOK_PATH}"
    _log.info(f"🌐 إعداد Webhook: {_full_url}")
    bot.remove_webhook()
    time.sleep(0.5)
    if _SSL_CERT:
        with open(_SSL_CERT, 'rb') as _cf:
            bot.set_webhook(url=_full_url, certificate=_cf,
                            secret_token=_WEBHOOK_SECRET or None)
    else:
        bot.set_webhook(url=_full_url, secret_token=_WEBHOOK_SECRET or None)
    _log.info("✅ Webhook مُسجَّل على Telegram")

    _app = Flask(__name__)

    @_app.route(_WEBHOOK_PATH, methods=['POST'])
    def _wh():
        if _WEBHOOK_SECRET:
            if request.headers.get("X-Telegram-Bot-Api-Secret-Token","") != _WEBHOOK_SECRET:
                abort(403)
        if request.content_type != "application/json":
            abort(415)
        try:
            _upd = _tb.types.Update.de_json(request.data.decode("utf-8"))
            bot.process_new_updates([_upd])
        except Exception as _e:
            _log.error(f"[Webhook] خطأ: {_e}")
        return "ok", 200

    @_app.route("/health")
    def _health():
        return {"status": "ok", "mode": "flask-webhook"}, 200

    _ssl_ctx = (_SSL_CERT, _SSL_KEY) if _SSL_CERT and _SSL_KEY else None
    _log.info(f"🚀 Flask يستمع على {_WEBHOOK_HOST}:{_WEBHOOK_PORT}{_WEBHOOK_PATH}")
    _app.run(host=_WEBHOOK_HOST, port=_WEBHOOK_PORT,
             ssl_context=_ssl_ctx, threaded=True,
             debug=False, use_reloader=False)


# ══════════════════════════════════════════════════
#   Sanic app — على مستوى الموديول
#   يشتغل مع: sanic hello.app  (alwaysdata)
#   ويشتغل مع: python hello.py (مباشرةً)
# ══════════════════════════════════════════════════
import asyncio as _asyncio

try:
    from sanic import Sanic as _Sanic
    from sanic import response as _sanic_r
    from sanic.request import Request as _SanicReq

    app = _Sanic("QuranBot")

    @app.post(_WEBHOOK_PATH)
    async def _wh_route(_req: _SanicReq):
        if _WEBHOOK_SECRET:
            if _req.headers.get("X-Telegram-Bot-Api-Secret-Token", "") != _WEBHOOK_SECRET:
                return _sanic_r.text("Forbidden", status=403)
        if _req.content_type != "application/json":
            return _sanic_r.text("Unsupported Media Type", status=415)
        try:
            import telebot as _tb_wh
            _upd = _tb_wh.types.Update.de_json(_req.body.decode("utf-8"))
            bot.process_new_updates([_upd])
        except Exception as _e:
            _log.error(f"[Webhook] خطأ: {_e}")
        return _sanic_r.text("ok")

    @app.get("/health")
    async def _health_route(_req: _SanicReq):
        return _sanic_r.json({"status": "ok", "mode": "sanic-webhook"})

    _wh_started = False

    @app.before_server_start
    async def _wh_setup(_app, _loop):
        global _wh_started
        if _wh_started:
            return
        _wh_started = True
        _log.info("⏳ تشغيل الجداول الزمنية...")
        _start_schedulers()
        _log.info("✅ الجداول تعمل")
        try:
            bot.remove_webhook()
        except Exception as _e:
            _log.warning(f"[Setup] خطأ في remove_webhook: {_e}")
        await _asyncio.sleep(0.5)
        _full = f"{_WEBHOOK_URL}{_WEBHOOK_PATH}"
        try:
            bot.set_webhook(url=_full, secret_token=_WEBHOOK_SECRET or None)
            _log.info(f"✅ Webhook مُسجَّل: {_full}")
        except Exception as _e:
            _log.error(f"[Setup] ❌ فشل تسجيل Webhook: {_e}")

except ImportError:
    app = None
    _log.warning("⚠️ Sanic غير مثبت — وضع Sanic غير متاح")


# ── نقطة الدخول المباشرة (python hello.py) ──────────────────────────
if __name__ == '__main__':
    print("━" * 55)
    print("  🌙  بوت رحلة التقرب من الله")
    print("━" * 55)
    print(f"  🔧  الوضع    : {_BOT_MODE.upper()}")
    if _BOT_MODE == "webhook":
        print(f"  🌐  السيرفر  : {_SERVER_ENGINE.upper()}")
        print(f"  🔗  URL      : {_WEBHOOK_URL}{_WEBHOOK_PATH}")
        print(f"  🖥️  البورت   : {_WEBHOOK_PORT}")
        print(f"  🔒  SSL      : {'✅ مفعّل' if _SSL_CERT else '❌ (استخدم Nginx/Cloudflare)'}")
    print("━" * 55)

    if _BOT_MODE == "webhook":
        if not _WEBHOOK_URL:
            _log.error("❌ WEBHOOK_URL غير محدد! أضفه في .env أو متغيرات البيئة")
            sys.exit(1)
        if app is None:
            _log.error("❌ Sanic غير مثبت — pip install sanic")
            sys.exit(1)
        _ssl_ctx = None
        if _SSL_CERT and _SSL_KEY:
            import ssl as _ssl_m
            _ssl_ctx = _ssl_m.SSLContext(_ssl_m.PROTOCOL_TLS_SERVER)
            _ssl_ctx.load_cert_chain(_SSL_CERT, _SSL_KEY)
        _log.info(f"🚀 تشغيل على {_WEBHOOK_HOST}:{_WEBHOOK_PORT}")
        app.run(host=_WEBHOOK_HOST, port=_WEBHOOK_PORT, ssl=_ssl_ctx,
                workers=1, access_log=False, debug=False, auto_reload=False)
    else:
        _start_schedulers()
        _run_polling()
