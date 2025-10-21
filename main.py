import os
import requests
import subprocess
import txthtml
from pyromod import listen
from vars import API_ID, API_HASH, BOT_TOKEN, CREDIT, FORCE_CHANNEL
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def is_subscribed(user_id: int, channel: str) -> bool:
    """
    Check if a user is a member of the specified channel.
    channel can be a username like @MyChannel or an invite URL.
    The bot must be a member of the channel for this to work.
    """
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ("creator", "administrator", "member", "restricted")
    except Exception:
        # get_chat_member may fail if bot is not in channel or channel invalid
        return False

@bot.on_callback_query(filters.regex(r"^check_sub$"))
async def check_subscription(client: Client, callback: CallbackQuery):
    """
    Handler for the 'I Joined' button after forced-subscribe message.
    If user is now subscribed, ask them to start again or upload file.
    """
    user_id = callback.from_user.id
    if await is_subscribed(user_id, FORCE_CHANNEL):
        await callback.message.edit_text(
            "✅ Thanks for joining the channel! Now please send /start again or upload your .txt file to continue."
        )
    else:
        await callback.answer("Aap abhi bhi channel ke member nahin hain. Pehle join karein.", show_alert=True)

@bot.on_message(filters.command(["start"]))
async def txt_handler(bot: Client, message: Message):
    # Force subscribe check
    if not await is_subscribed(message.from_user.id, FORCE_CHANNEL):
        # Build join URL: if FORCE_CHANNEL is a full link, use it; otherwise assume @username
        if FORCE_CHANNEL.startswith("http"):
            join_url = FORCE_CHANNEL
        else:
            join_url = f"https://t.me/{FORCE_CHANNEL.lstrip('@')}"
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Join Channel", url=join_url)],
                [InlineKeyboardButton("✅ I Joined", callback_data="check_sub")]
            ]
        )
        await message.reply_text(
            "Kripya pehle hamare channel ko join karein to bot ka istemal kar sakein.",
            reply_markup=keyboard
        )
        return

    # If subscribed, continue with existing flow
    editable = await message.reply_text("𝐖𝐞𝐥𝐜𝐨𝐦𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐮𝐩𝐥𝐨𝐚𝐝 𝐚 .txt 𝐟𝐢𝐥𝐞 𝐜𝐨𝐧𝐭𝐚𝐢𝐧𝐢𝐧𝐠 links (videos/pdf/others).")
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

    # Use txthtml utilities (assumes these functions exist in txthtml)
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
    caption=f"✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞!\n<blockquote><b>`{file_name}`</b></blockquote>\n❖** Open in Chrome.**❖\n\n📥𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲➤**<a href='https://t.me/kundan_yadav_bot'>{CREDIT}</a>**"
    )

    # Clean up
    try:
        os.remove(file_path)
    except Exception:
        pass
    try:
        os.remove(html_file_path)
    except Exception:
        pass

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
