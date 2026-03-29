#!/usr/bin/env python3
"""
🎵 Advanced Telegram Music Bot
Features: Search, Download, Stream, Lyrics, Song Recognition, Voice Search
Developer: @Modder_TZP
"""

import logging
import os
import tempfile
import time
from pathlib import Path

import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────────────────────
BOT_TOKEN = "8388734758:AAERzPdonoypB-tUoQ-FswsZuZF1sEVzrOE"
SHAZAM_API_KEY = ""  # rapidapi.com မှာ free key ယူပါ (optional)

DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "music_bot"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

SAAVN_API = "https://saavn.dev/api"

user_data: dict = {}  # uid -> {songs, lang, history}

# ── Language Strings ──────────────────────────
LANG = {
    "en": {
        "welcome": (
            "🎵 *Music Bot* by @Modder\\_TZP\n\n"
            "Send me:\n"
            "🎵 Song name or artist\n"
            "📝 abc Lyrics from the song\n"
            "🎤 Voice message with music\n"
            "🎵 Audio recording\n"
            "🔗 YouTube/Instagram/TikTok link\n\n"
            "🇲🇲 Myanmar songs supported!\n\n"
            "Use /lang to change language"
        ),
        "searching": "🔍 Searching...",
        "not_found": "❌ Not found. Try another name.",
        "pick_song": "🎶 Pick a song:",
        "how_listen": "How do you want to listen?",
        "downloading": "⬇️ Downloading...",
        "uploading": "📤 Uploading...",
        "dl_failed": "❌ Download failed. Try again.",
        "fetching_lyrics": "📝 Fetching lyrics...",
        "no_lyrics": "❌ Lyrics not found.",
        "recognizing": "🎵 Recognizing song...",
        "rec_failed": "❌ Could not recognize. Try clearer audio.",
        "history_empty": "📋 No history yet.",
        "history_title": "📋 *Recent searches:*\n\n",
        "pick_lang": "🌍 Pick your language:",
        "lang_set": "✅ Language set to English!",
    },
    "my": {
        "welcome": (
            "🎵 *Music Bot* by @Modder\\_TZP\n\n"
            "ဒါတွေ ပို့နိုင်တယ်:\n"
            "🎵 သီချင်းအမည် သို့မဟုတ် သရုပ်ဆောင်\n"
            "📝 သီချင်း lyrics\n"
            "🎤 Voice message\n"
            "🎵 Audio recording\n"
            "🔗 YouTube/Instagram/TikTok link\n\n"
            "🇲🇲 မြန်မာ သီချင်းများ ပါဝင်တယ်!\n\n"
            "/lang - ဘာသာစကား ပြောင်းရန်"
        ),
        "searching": "🔍 ရှာနေတယ်...",
        "not_found": "❌ မတွေ့ပါ။ ထပ်ကြိုးစားပါ။",
        "pick_song": "🎶 Song ရွေးပါ:",
        "how_listen": "ဘယ်လို နားထောင်မလဲ?",
        "downloading": "⬇️ Download လုပ်နေတယ်...",
        "uploading": "📤 Upload လုပ်နေတယ်...",
        "dl_failed": "❌ Download မအောင်မြင်ပါ။ ထပ်ကြိုးစားပါ။",
        "fetching_lyrics": "📝 Lyrics ရှာနေတယ်...",
        "no_lyrics": "❌ Lyrics မတွေ့ပါ။",
        "recognizing": "🎵 သီချင်း ရှာဖွေနေတယ်...",
        "rec_failed": "❌ မသိနိုင်ပါ။ ပိုပြတ်သားတဲ့ audio ထပ်ကြိုးစားပါ။",
        "history_empty": "📋 မှတ်တမ်း မရှိသေးပါ။",
        "history_title": "📋 *မကြာခင် ရှာထားသောများ:*\n\n",
        "pick_lang": "🌍 ဘာသာစကား ရွေးပါ:",
        "lang_set": "✅ မြန်မာဘာသာ သတ်မှတ်ပြီးပြီ!",
    },
}


def t(uid: int, key: str) -> str:
    lang = user_data.get(uid, {}).get("lang", "my")
    return LANG.get(lang, LANG["my"]).get(key, key)


# ── API Helpers ───────────────────────────────

def search_songs(query: str, limit: int = 6) -> list:
    try:
        r = requests.get(
            f"{SAAVN_API}/search/songs",
            params={"query": query, "limit": limit},
            timeout=15,
        )
        data = r.json()
        results = data.get("data", {}).get("results", [])
        songs = []
        for s in results:
            dl_urls = s.get("downloadUrl", [])
            best_url = ""
            for q in ["320kbps", "160kbps", "96kbps", "48kbps"]:
                for u in dl_urls:
                    if u.get("quality") == q and u.get("url"):
                        best_url = u["url"]
                        break
                if best_url:
                    break
            artists = ", ".join([a["name"] for a in s.get("artists", {}).get("primary", [])])
            imgs = s.get("image", [])
            image = imgs[-1].get("url", "") if imgs else ""
            songs.append({
                "id": s.get("id", ""),
                "title": s.get("name", "Unknown"),
                "artist": artists,
                "duration": int(s.get("duration", 0)),
                "image": image,
                "url": best_url,
                "album": s.get("album", {}).get("name", ""),
            })
        return songs
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def get_lyrics(song_name: str, artist: str = "") -> str:
    try:
        # Try lyrics.ovh
        query = f"{song_name} {artist}".strip()
        r = requests.get(
            f"https://api.lyrics.ovh/v1/{artist or song_name}/{song_name}",
            timeout=10,
        )
        if r.status_code == 200:
            lyrics = r.json().get("lyrics", "")
            if lyrics:
                return lyrics[:3500]  # Telegram message limit

        # Fallback: search via JioSaavn
        songs = search_songs(query, limit=1)
        if songs:
            sid = songs[0]["id"]
            r2 = requests.get(f"{SAAVN_API}/songs/{sid}", timeout=10)
            data = r2.json().get("data", [])
            if data:
                return data[0].get("lyrics", "") or ""
        return ""
    except Exception as e:
        logger.error(f"Lyrics error: {e}")
        return ""


def recognize_song_shazam(audio_path: str) -> dict | None:
    """Recognize song using Shazam via RapidAPI."""
    if not SHAZAM_API_KEY:
        return None
    try:
        with open(audio_path, "rb") as f:
            r = requests.post(
                "https://shazam.p.rapidapi.com/songs/detect",
                headers={
                    "x-rapidapi-key": SHAZAM_API_KEY,
                    "x-rapidapi-host": "shazam.p.rapidapi.com",
                    "content-type": "text/plain",
                },
                data=f.read(),
                timeout=20,
            )
        data = r.json()
        track = data.get("track", {})
        if track:
            return {
                "title": track.get("title", ""),
                "artist": track.get("subtitle", ""),
                "image": track.get("images", {}).get("coverart", ""),
            }
        return None
    except Exception as e:
        logger.error(f"Shazam error: {e}")
        return None


def download_song(url: str, song_id: str) -> Path | None:
    out = DOWNLOAD_DIR / f"{song_id}.mp4"
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return out if out.stat().st_size > 0 else None
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None


def fmt(sec) -> str:
    m, s = divmod(int(sec or 0), 60)
    return f"{m}:{s:02d}"


def add_history(uid: int, title: str, artist: str):
    if uid not in user_data:
        user_data[uid] = {}
    hist = user_data[uid].get("history", [])
    entry = f"🎵 {title} — {artist}"
    if entry not in hist:
        hist.insert(0, entry)
    user_data[uid]["history"] = hist[:10]


# ── Keyboards ─────────────────────────────────

def results_keyboard(songs: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for s in songs:
        label = f"🎵 {s['title']}"
        if s["artist"]:
            label += f" — {s['artist']}"
        label = label[:52] + f" ({fmt(s['duration'])})"
        kb.add(InlineKeyboardButton(label, callback_data=f"pick|{s['id']}"))
    return kb


def song_action_keyboard(song_id: str, has_lyrics: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("⬇️ Download", callback_data=f"dl|{song_id}"),
        InlineKeyboardButton("▶️ Stream", callback_data=f"st|{song_id}"),
    )
    if has_lyrics:
        kb.add(InlineKeyboardButton("📝 Lyrics", callback_data=f"ly|{song_id}"))
    kb.add(InlineKeyboardButton("🔍 ထပ်ရှာမယ်", callback_data="back_search"))
    return kb


def lang_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="lang|my"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang|en"),
    )
    return kb


# ── Commands ──────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    if uid not in user_data:
        user_data[uid] = {"lang": "my", "history": []}
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🇲🇲 မြန်မာ", callback_data="lang|my"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang|en"),
    )
    bot.send_message(msg.chat.id, "🌍 ဘာသာစကား ရွေးပါ / Pick language:", reply_markup=kb)


@bot.message_handler(commands=["help"])
def cmd_help(msg):
    uid = msg.from_user.id
    bot.send_message(msg.chat.id, t(uid, "welcome"), parse_mode="Markdown")


@bot.message_handler(commands=["lang"])
def cmd_lang(msg):
    uid = msg.from_user.id
    bot.send_message(msg.chat.id, t(uid, "pick_lang"), reply_markup=lang_keyboard())


@bot.message_handler(commands=["history"])
def cmd_history(msg):
    uid = msg.from_user.id
    hist = user_data.get(uid, {}).get("history", [])
    if not hist:
        bot.send_message(msg.chat.id, t(uid, "history_empty"))
        return
    text = t(uid, "history_title") + "\n".join(hist)
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")


# ── Text Handler ──────────────────────────────

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(msg):
    uid = msg.from_user.id
    if uid not in user_data:
        user_data[uid] = {"lang": "my", "history": []}
    query = msg.text.strip()

    # Lyrics request detection
    if query.lower().startswith("lyrics ") or query.startswith("📝"):
        query = query.replace("lyrics ", "").replace("📝", "").strip()
        wait = bot.send_message(msg.chat.id, t(uid, "fetching_lyrics"))
        lyrics = get_lyrics(query)
        if not lyrics:
            bot.edit_message_text(t(uid, "no_lyrics"), msg.chat.id, wait.message_id)
            return
        bot.edit_message_text(f"📝 *{query}*\n\n{lyrics[:3800]}", msg.chat.id, wait.message_id, parse_mode="Markdown")
        return

    wait = bot.send_message(msg.chat.id, t(uid, "searching"))
    songs = search_songs(query, limit=6)
    if not songs:
        bot.edit_message_text(t(uid, "not_found"), msg.chat.id, wait.message_id)
        return

    user_data[uid]["songs"] = {s["id"]: s for s in songs}
    user_data[uid]["last_query"] = query
    bot.edit_message_text(
        t(uid, "pick_song"),
        msg.chat.id,
        wait.message_id,
        reply_markup=results_keyboard(songs),
    )


# ── Voice / Audio Handler ─────────────────────

@bot.message_handler(content_types=["voice", "audio"])
def handle_voice(msg):
    uid = msg.from_user.id
    if uid not in user_data:
        user_data[uid] = {"lang": "my", "history": []}

    wait = bot.send_message(msg.chat.id, t(uid, "recognizing"))

    # Download the voice/audio
    if msg.voice:
        file_info = bot.get_file(msg.voice.file_id)
    else:
        file_info = bot.get_file(msg.audio.file_id)

    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    tmp_path = DOWNLOAD_DIR / f"voice_{uid}_{int(time.time())}.ogg"

    try:
        r = requests.get(file_url, timeout=30)
        tmp_path.write_bytes(r.content)
    except Exception as e:
        bot.edit_message_text(t(uid, "rec_failed"), msg.chat.id, wait.message_id)
        return

    # Try Shazam recognition
    result = recognize_song_shazam(str(tmp_path))
    tmp_path.unlink(missing_ok=True)

    if result and result.get("title"):
        title = result["title"]
        artist = result["artist"]
        text = f"🎵 *{title}*\n👤 {artist}\n\nသီချင်း ရှာမလား?"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔍 ဒီသီချင်း ရှာမယ်", callback_data=f"search_q|{title} {artist}"))
        bot.edit_message_text(text, msg.chat.id, wait.message_id, parse_mode="Markdown", reply_markup=kb)
    else:
        # Fallback: ask user to type the name
        bot.edit_message_text(
            "🎤 Voice/Audio ရရှိပြီ!\n\n"
            "Shazam API key မပါတာကြောင့် auto-recognize မလုပ်နိုင်ပါ။\n"
            "သီချင်းအမည် ရိုက်ပြီး ရှာပါ။\n\n"
            "💡 RapidAPI မှာ Shazam key ထည့်ရင် auto-recognize အလုပ်လုပ်မယ်။",
            msg.chat.id,
            wait.message_id,
        )


# ── Callback Handler ──────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data

    if uid not in user_data:
        user_data[uid] = {"lang": "my", "history": []}

    bot.answer_callback_query(call.id)

    # Language selection
    if data.startswith("lang|"):
        lang = data[5:]
        user_data[uid]["lang"] = lang
        bot.edit_message_text(t(uid, "lang_set"), cid, mid)
        time.sleep(0.5)
        bot.send_message(cid, t(uid, "welcome"), parse_mode="Markdown")

    # Search by query (from voice recognition)
    elif data.startswith("search_q|"):
        query = data[9:]
        bot.edit_message_text(t(uid, "searching"), cid, mid)
        songs = search_songs(query, limit=6)
        if not songs:
            bot.edit_message_text(t(uid, "not_found"), cid, mid)
            return
        user_data[uid]["songs"] = {s["id"]: s for s in songs}
        bot.edit_message_text(t(uid, "pick_song"), cid, mid, reply_markup=results_keyboard(songs))

    # Song picked
    elif data.startswith("pick|"):
        song_id = data[5:]
        song = user_data.get(uid, {}).get("songs", {}).get(song_id)
        if not song:
            bot.edit_message_text(t(uid, "not_found"), cid, mid)
            return
        add_history(uid, song["title"], song["artist"])
        text = (
            f"🎵 *{song['title']}*\n"
            f"👤 {song['artist']}\n"
            f"💿 {song['album']}\n"
            f"⏱ {fmt(song['duration'])}\n\n"
            f"{t(uid, 'how_listen')}"
        )
        bot.edit_message_text(text, cid, mid, parse_mode="Markdown", reply_markup=song_action_keyboard(song_id))

    # Download
    elif data.startswith("dl|"):
        song_id = data[3:]
        song = user_data.get(uid, {}).get("songs", {}).get(song_id)
        if not song or not song.get("url"):
            bot.edit_message_text(t(uid, "dl_failed"), cid, mid)
            return
        bot.edit_message_text(f"{t(uid, 'downloading')}\n*{song['title']}*", cid, mid, parse_mode="Markdown")
        file_path = download_song(song["url"], song_id)
        if not file_path:
            bot.edit_message_text(t(uid, "dl_failed"), cid, mid)
            return
        bot.edit_message_text(t(uid, "uploading"), cid, mid)
        try:
            with open(file_path, "rb") as f:
                caption = f"🎵 {song['title']}\n👤 {song['artist']}\n💿 {song['album']}"
                bot.send_audio(cid, f, title=song["title"], performer=song["artist"], caption=caption)
            bot.delete_message(cid, mid)
        except Exception as e:
            bot.edit_message_text(f"❌ Upload failed: {e}", cid, mid)
        finally:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

    # Stream
    elif data.startswith("st|"):
        song_id = data[3:]
        song = user_data.get(uid, {}).get("songs", {}).get(song_id)
        if not song or not song.get("url"):
            bot.edit_message_text("❌ Stream URL မတွေ့ပါ။", cid, mid)
            return
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎵 Stream နားထောင်မယ်", url=song["url"]))
        kb.add(InlineKeyboardButton("⬅️ Back", callback_data=f"pick|{song_id}"))
        text = (
            f"▶️ *{song['title']}*\n"
            f"👤 {song['artist']}\n"
            f"⏱ {fmt(song['duration'])}\n\n"
            f"🎧 Link နှိပ်ပြီး နားထောင်ပါ:"
        )
        bot.edit_message_text(text, cid, mid, parse_mode="Markdown", reply_markup=kb)

    # Lyrics
    elif data.startswith("ly|"):
        song_id = data[3:]
        song = user_data.get(uid, {}).get("songs", {}).get(song_id)
        if not song:
            bot.edit_message_text(t(uid, "no_lyrics"), cid, mid)
            return
        bot.edit_message_text(t(uid, "fetching_lyrics"), cid, mid)
        lyrics = get_lyrics(song["title"], song["artist"])
        if not lyrics:
            bot.edit_message_text(t(uid, "no_lyrics"), cid, mid,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"pick|{song_id}")]]))
            return
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⬅️ Back", callback_data=f"pick|{song_id}"))
        text = f"📝 *{song['title']}*\n👤 {song['artist']}\n\n{lyrics[:3800]}"
        bot.edit_message_text(text, cid, mid, parse_mode="Markdown", reply_markup=kb)

    # Back to search
    elif data == "back_search":
        query = user_data.get(uid, {}).get("last_query", "")
        if not query:
            bot.edit_message_text("ထပ်ရှာချင်တဲ့ song name ရိုက်ပါ။", cid, mid)
            return
        songs = search_songs(query, limit=6)
        if not songs:
            bot.edit_message_text(t(uid, "not_found"), cid, mid)
            return
        user_data[uid]["songs"] = {s["id"]: s for s in songs}
        bot.edit_message_text(t(uid, "pick_song"), cid, mid, reply_markup=results_keyboard(songs))


# ── Main ──────────────────────────────────────

if __name__ == "__main__":
    logger.info("🎵 Music Bot started...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
