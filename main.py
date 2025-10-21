import os
import random
import requests
import subprocess
import txthtml
from pyromod import listen
from vars import API_ID, API_HASH, BOT_TOKEN, CREDIT, FORCE_SUB_CHANNEL
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant  # ✅ Added missing import

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


#=====================================================================================
#                        FORCE SUBSCRIBE CHECKER (Fixed indentation)
#=====================================================================================
async def is_subscribed(user_id: int, channel: str) -> bool:
    try:
        user = await bot.get_chat_member(channel, user_id)
        return user.status not in ("left", "kicked")
    except Exception:
        return False


def get_force_sub_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data="checksub")]
    ])


async def check_force_sub(client, message):
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if user.status in ("left", "kicked"):
            raise UserNotParticipant
    except UserNotParticipant:
        await message.reply_photo(
            photo=random.choice([
                "https://s.tfrbot.com/h/Vf6F3e", "https://s.tfrbot.com/h/g5lIWO",
                "https://s.tfrbot.com/h/sRMf7S", "https://s.tfrbot.com/h/xfeZKC",
                "https://s.tfrbot.com/h/QCvWqP"
            ]),
            caption=f"<b>Hi {message.from_user.mention},\n\nTo use this bot, you must join our channel first.</b>",
            reply_markup=get_force_sub_buttons()
        )
        return False
    except Exception as e:
        await message.reply(f"🚫 An error occurred: `{e}`", quote=True)
        return False
    return True


#=====================================================================================
#                                CALLBACK HANDLERS
#=====================================================================================
#=====================================================================================
#                                START COMMAND HANDLER
#=====================================================================================
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    # Check if user joined the required channel
    if not await check_force_sub(client, message):
        return

    # If subscribed, show welcome message
    await message.reply_photo(
        photo="https://s.tfrbot.com/h/QCvWqP",
        caption=(
            f"👋 Hello {message.from_user.mention}!\n\n"
            "Welcome to the **TXT → HTML Extractor Bot** 🪄\n"
            "Just upload a `.txt` file containing links (videos, pdfs, etc.) and I'll convert it into a neat HTML file.\n\n"
            "✨ Let's get started!"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Updates", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
            [InlineKeyboardButton("🚀 Start Conversion", callback_data="close_data")]
        ])
    )

@bot.on_callback_query(filters.regex("^checksub$"))
async def recheck_sub(client, callback_query: CallbackQuery):
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, callback_query.from_user.id)
        if user.status in ("left", "kicked"):
            await callback_query.answer("💀Abbey yaar channel join kar lo...", show_alert=True)
            return
    except UserNotParticipant:
        await callback_query.answer("💀Abbey yaar channel join kar lo...", show_alert=True)
        return
    except Exception as e:
        await callback_query.answer(f"🚫 Error: {e}", show_alert=True)
        return

    await callback_query.answer("✅ Thank you for joining!", show_alert=False)
    await callback_query.message.delete()
    await client.send_message(callback_query.from_user.id, "Welcome! 🎉\nSend me a file to get started.")


@bot.on_callback_query(filters.regex("^close_data$"))
async def close_handler(client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer()

    message = callback_query.message  # ✅ Fixed undefined variable

    # Ask for txt file
    editable = await message.reply_text(
        "𝐖𝐞𝐥𝐜𝐨𝐦𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐮𝐩𝐥𝐨𝐚𝐝 𝐚 .txt 𝐟𝐢𝐥𝐞 𝐜𝐨𝐧𝐭𝐚𝐢𝐧𝐢𝐧𝐠 links (videos/pdf/others)."
    )

    # Listen for the next message (file upload)
    input_msg: Message = await bot.listen(editable.chat.id)

    if input_msg.document and input_msg.document.file_name.endswith('.txt'):
        file_path = await input_msg.download()
        file_name, ext = os.path.splitext(os.path.basename(file_path))
    else:
        await message.reply_text("**• Invalid file input. Please upload a .txt file.**")
        return

    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Use txthtml utilities
    urls = txthtml.extract_names_and_urls(file_content)
    videos, pdfs, others = txthtml.categorize_urls(urls)
    html_content = txthtml.generate_html(file_name, videos, pdfs, others)

    # Save HTML
    html_file_path = file_path.replace(".txt", ".html")
    with open(html_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Send HTML back
    await message.reply_document(
        document=html_file_path,
        caption=(
            f"✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞!\n"
            f"<blockquote><b>`{file_name}`</b></blockquote>\n"
            f"❖** Open in Chrome.**❖\n\n"
            f"📥𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲➤**<a href='https://t.me/kundan_yadav_bot'>{CREDIT}</a>**"
        )
    )

    # Clean up
    try:
        os.remove(file_path)
        os.remove(html_file_path)
    except Exception:
        pass


#=====================================================================================
#                                RUN THE BOT
#=====================================================================================
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
