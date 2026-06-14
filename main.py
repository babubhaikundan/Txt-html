"""
main.py — TXT → HTML Converter Bot
Features: Force-sub, user DB tracking, /stats, /history, /broadcast,
          encoding fallback, safe temp-file cleanup, file-size guard.
"""

import os
import asyncio
import shutil

import txthtml
from vars import API_ID, API_HASH, BOT_TOKEN, FORCE_SUB_CHANNEL, ADMINS, MONGO_URI
import db as database

from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import UserNotParticipant, FloodWait

# ── Bot client ────────────────────────────────────────────────────────────
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOADS_DIR   = "./downloads"
MAX_TXT_SIZE_MB = 10          # Reject .txt files larger than this
ENCODINGS       = ("utf-8", "utf-8-sig", "latin-1", "cp1252")


# ═══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _is_admin(user_id: int) -> bool:
    return user_id in ADMINS


def _read_file(path: str) -> str:
    """Try multiple encodings; raise ValueError if all fail."""
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(
        "File ko decode nahi kar saka. "
        "Please UTF-8 encoded `.txt` file bhejo."
    )


# ═══════════════════════════════════════════════════════════════════════════
#  FORCE SUBSCRIBE
# ═══════════════════════════════════════════════════════════════════════════

WELCOME_PHOTOS = [
    "https://s.tfrbot.com/h/Vf6F3e", "https://s.tfrbot.com/h/g5lIWO",
    "https://s.tfrbot.com/h/sRMf7S", "https://s.tfrbot.com/h/xfeZKC",
    "https://s.tfrbot.com/h/QCvWqP",
]

import random

async def check_force_sub(client: Client, message: Message) -> bool:
    """Returns True if user is subscribed (or FORCE_SUB_CHANNEL not set)."""
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if str(member.status) in ("ChatMemberStatus.LEFT", "ChatMemberStatus.BANNED",
                                   "left", "kicked", "banned"):
            raise UserNotParticipant
    except UserNotParticipant:
        await message.reply_photo(
            photo=random.choice(WELCOME_PHOTOS),
            caption=(
                f"**Hi {message.from_user.mention},**\n\n"
                "Bot use karne ke liye pehle hamara channel join karo! 👇\n\n"
                "Join karke **Retry** button dabao."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Channel Join Karo", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
                [InlineKeyboardButton("✅ Retry", callback_data="checksub")],
            ]),
            quote=True,
        )
        return False
    except Exception as e:
        await message.reply_text(f"🚫 Error: `{e}`", quote=True)
        return False
    return True


# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    if not await check_force_sub(client, message):
        return
    await database.upsert_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    await message.reply_photo(
        photo="https://s.tfrbot.com/h/QCvWqP",
        caption=(
            f"👋 **Hello {message.from_user.mention}!**\n\n"
            "Welcome to **TXT → HTML Converter Bot** 🪄\n\n"
            "📤 Bas ek `.txt` file bhejo jisme links hain:\n"
            "`Lecture Name : https://video-url.com`\n\n"
            "Use /help for more details."
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
            [InlineKeyboardButton("❓ Help", callback_data="show_help")],
        ]),
    )


@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    if not await check_force_sub(client, message):
        return
    await message.reply_text(
        "📖 **Bot Help**\n\n"
        "**Commands:**\n"
        "• /start — Welcome\n"
        "• /help — Yeh message\n"
        "• /history — Teri last 7 conversions\n\n"
        "**Supported .txt formats:**\n"
        "`Name : URL`\n"
        "`Subject || Topic #1 : URL`\n"
        "`(Subject) Topic #1 : URL`\n\n"
        "**Generated HTML features:**\n"
        "🌙 Dark mode toggle\n"
        "▶ Continue watching (resume where you left)\n"
        "✓ Progress tracking (auto-marks at 80%)\n"
        "🔍 Search with highlight\n"
        "📁 Topic-wise grouping\n"
        "⊞ Expand / Collapse all\n"
        "🔢 Part-wise buttons for multi-URL lectures\n\n"
        "**Keyboard Shortcuts (in HTML):**\n"
        "`Space` — Play/Pause\n"
        "`F` — Fullscreen\n"
        "`← / →` — Seek ±10s\n"
        "`↑ / ↓` — Volume\n"
        "`M` — Mute\n"
        "`Double tap` — Seek ±10s (mobile)",
        quote=True,
    )


@bot.on_message(filters.command("history") & filters.private)
async def history_command(client: Client, message: Message):
    if not await check_force_sub(client, message):
        return
    history = await database.get_user_history(message.from_user.id, limit=7)
    if not history:
        await message.reply_text(
            "📭 Koi history nahi mili.\n\n"
            "Pehle ek `.txt` file bhejo — convert hogi toh yahan dikhegi!",
            quote=True,
        )
        return
    lines = [f"📋 **Teri Last {len(history)} Conversions:**\n"]
    for i, item in enumerate(history, 1):
        fname   = item.get("file_name", "Unknown")
        at      = item.get("at")
        date_s  = at.strftime("%d %b %Y, %H:%M UTC") if at else "?"
        lcount  = item.get("lecture_count", 0)
        lines.append(f"{i}. `{fname}`\n   📚 {lcount} lectures  🕒 {date_s}")
    await message.reply_text("\n".join(lines), quote=True)


# ── Admin commands ─────────────────────────────────────────────────────────

@bot.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    if not _is_admin(message.from_user.id):
        await message.reply_text("⛔ Yeh command sirf admins ke liye hai.", quote=True)
        return
    total_users = await database.count_users()
    total_conv  = await database.count_conversions_total()
    today_conv  = await database.count_conversions_today()
    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users:         `{total_users}`\n"
        f"🔄 Total Conversions:   `{total_conv}`\n"
        f"📅 Today's Conversions: `{today_conv}`",
        quote=True,
    )


@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client: Client, message: Message):
    if not _is_admin(message.from_user.id):
        await message.reply_text("⛔ Yeh command sirf admins ke liye hai.", quote=True)
        return
    if not message.reply_to_message:
        await message.reply_text(
            "ℹ️ **Broadcast kaise karein:**\n"
            "Jis message ko bhejni ho usse reply karke `/broadcast` likho.",
            quote=True,
        )
        return

    all_users = await database.get_all_user_ids()
    if not all_users:
        await message.reply_text("❌ Database mein koi user nahi hai.", quote=True)
        return

    prog_msg = await message.reply_text(
        f"📡 Broadcast shuru... **{len(all_users)}** users ko bhej raha hoon."
    )
    success, failed = 0, 0

    for i, uid in enumerate(all_users):
        try:
            await message.reply_to_message.copy(chat_id=uid)
            success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
            try:
                await message.reply_to_message.copy(chat_id=uid)
                success += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1

        if (i + 1) % 25 == 0:
            try:
                await prog_msg.edit_text(
                    f"📡 Broadcasting... {i + 1}/{len(all_users)}\n"
                    f"✅ Sent: {success}  ❌ Failed: {failed}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.07)   # ~14 msg/s — safe under Telegram limits

    await prog_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"📊 Total: {len(all_users)}\n"
        f"✅ Sent:   {success}\n"
        f"❌ Failed: {failed}"
    )


# ── kundan alias ───────────────────────────────────────────────────────────

@bot.on_message(filters.command("kundan") & filters.private)
async def kundan_command(client: Client, message: Message):
    if not await check_force_sub(client, message):
        return
    await message.reply_text(
        "✨ **Ready!**\n\nApna `.txt` file bhejo — main HTML bana dunga!",
        quote=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN DOCUMENT HANDLER
# ═══════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.document & filters.private)
async def handle_document(client: Client, message: Message):
    # 1. Force sub check
    if not await check_force_sub(client, message):
        return

    doc = message.document

    # 2. File type check
    safe_name = os.path.basename(doc.file_name or "")
    if not safe_name.lower().endswith(".txt"):
        await message.reply_text(
            "⚠️ **Invalid File!**\n\nSirf `.txt` files accept hoti hain.",
            quote=True,
        )
        return

    # 3. File size guard
    if doc.file_size and doc.file_size > MAX_TXT_SIZE_MB * 1024 * 1024:
        await message.reply_text(
            f"⚠️ File bahut badi hai! Max allowed: **{MAX_TXT_SIZE_MB} MB**",
            quote=True,
        )
        return

    file_name_only = os.path.splitext(safe_name)[0]
    user_dir       = os.path.join(DOWNLOADS_DIR, str(message.id))
    downloaded_path = None

    prog = await message.reply_text("`⏳ Downloading...`", quote=True)

    try:
        # 4. Download
        os.makedirs(user_dir, exist_ok=True)
        downloaded_path = await message.download(
            file_name=os.path.join(user_dir, safe_name)
        )

        await prog.edit_text("`⚙️ Processing aur HTML generate ho raha hai...`")

        # 5. Read with encoding fallback
        file_content = _read_file(downloaded_path)

        # 6. Convert
        urls            = txthtml.extract_names_and_urls(file_content)
        structured_list = txthtml.structure_data_in_order(urls)
        html_content    = txthtml.generate_html(file_name_only, structured_list)
        lec_count       = txthtml.count_total_lectures(structured_list)

        # 7. Save HTML
        html_path = os.path.join(user_dir, file_name_only + ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 8. Upload
        await prog.edit_text("`📤 File upload ho rahi hai...`")
        await message.reply_document(
            document=html_path,
            caption=(
                f"✅ **Conversion Successful!**\n\n"
                f"📄 File: `{file_name_only}.html`\n"
                f"📚 Lectures: `{lec_count}`\n\n"
                f"ℹ️ Browser mein open karo (Chrome recommended)."
            ),
            quote=True,
        )
        await prog.delete()

        # 9. Log to DB
        await database.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
        await database.log_conversion(message.from_user.id, file_name_only, lec_count)

    except Exception as e:
        await prog.edit_text(
            f"❌ **Error!**\n\n`{e}`\n\n"
            f"Format check karo: `Name : URL` (har line mein)"
        )

    finally:
        # Clean up the entire per-message download folder
        shutil.rmtree(user_dir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@bot.on_callback_query(filters.regex("^checksub$"))
async def recheck_sub_callback(client: Client, callback_query: CallbackQuery):
    user = callback_query.from_user
    joined = False
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user.id)
        status = str(member.status)
        if status not in ("ChatMemberStatus.LEFT", "ChatMemberStatus.BANNED",
                          "left", "kicked", "banned"):
            joined = True
    except UserNotParticipant:
        pass
    except Exception:
        pass

    if not joined:
        await callback_query.answer(
            "❌ Abhi bhi join nahi kiya! Pehle join karo.", show_alert=True
        )
        return

    await callback_query.answer("✅ Verified! Welcome!", show_alert=False)
    await callback_query.message.delete()

    await database.upsert_user(user.id, user.username, user.full_name)

    await client.send_photo(
        chat_id=user.id,
        photo="https://s.tfrbot.com/h/QCvWqP",
        caption=(
            f"👋 **Hello {user.mention}!**\n\n"
            "Welcome to **TXT → HTML Converter Bot** 🪄\n\n"
            "📤 Apna `.txt` file bhejo — main HTML bana dunga!\n"
            "Use /help for full guide."
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
        ]),
    )


@bot.on_callback_query(filters.regex("^show_help$"))
async def show_help_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply_text(
        "📖 **Quick Guide:**\n\n"
        "Send a `.txt` file with this format:\n"
        "`Lecture Name : https://link`\n\n"
        "Use /help for full details.",
    )


# ═══════════════════════════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    database.init_db(MONGO_URI)
    print("🤖 Bot starting...")
    bot.run()
    print("🛑 Bot stopped.")
