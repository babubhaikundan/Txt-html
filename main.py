import os
import random
import txthtml  # Your updated txthtml.py file
from vars import API_ID, API_HASH, BOT_TOKEN, CREDIT, FORCE_SUB_CHANNEL
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

#=====================================================================================
#                        FORCE SUBSCRIBE CHECKER
#=====================================================================================
async def check_force_sub(client, message: Message):
    """
    Checks if a user is subscribed to the force subscription channel.
    Returns True if subscribed, False otherwise.
    """
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if user.status in ("left", "kicked"):
            raise UserNotParticipant
    except UserNotParticipant:
        # User is not a participant, send the force-subscribe message
        join_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
            [InlineKeyboardButton("✅ Retry", callback_data="checksub")]
        ])
        await message.reply_photo(
            photo=random.choice([
                "https://s.tfrbot.com/h/Vf6F3e", "https://s.tfrbot.com/h/g5lIWO",
                "https://s.tfrbot.com/h/sRMf7S", "https://s.tfrbot.com/h/xfeZKC",
                "https://s.tfrbot.com/h/QCvWqP"
            ]),
            caption=(
                f"**Hi {message.from_user.mention},**\n\n"
                f"**To use this bot, you must join our channel first.**\n\n"
                f"Click the button below to join, then click 'Retry'."
            ),
            reply_markup=join_button,
            quote=True
        )
        return False
    except Exception as e:
        await message.reply_text(f"🚫 An error occurred: `{e}`", quote=True)
        return False
    return True

#=====================================================================================
#                                COMMAND HANDLERS
#=====================================================================================

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    if not await check_force_sub(client, message):
        return

    await message.reply_photo(
        photo="https://s.tfrbot.com/h/QCvWqP",
        caption=(
            f"👋 **Hello {message.from_user.mention}!**\n\n"
            "Welcome to the **TXT → HTML Converter Bot** 🪄\n\n"
            "To get started, simply send me a `.txt` file containing your links.\n\n"
            "You can also use the /kundan command if you prefer."
        ),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]]
        )
    )

@bot.on_message(filters.command("kundan") & filters.private)
async def kundan_command(client, message: Message):
    if not await check_force_sub(client, message):
        return
        
    await message.reply_text(
        "**Ready to convert!** ✨\n\n"
        "Please send me the `.txt` file you want to process."
    )

#=====================================================================================
#                         MAIN LOGIC: DOCUMENT HANDLER
#=====================================================================================

@bot.on_message(filters.document & filters.private)
async def handle_document(client, message: Message):
    # 1. Check Force Subscribe
    if not await check_force_sub(client, message):
        return

    # 2. Check if it's a .txt file
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("⚠️ **Invalid File Type!**\n\nPlease send a `.txt` file.", quote=True)
        return

    doc = message.document
    file_name = doc.file_name
    
    # 3. Show a processing message to the user
    processing_msg = await message.reply_text("`Processing your file, please wait...` ⏳", quote=True)

    # 4. Process the file
    try:
        # Download the file
        downloaded_file_path = await message.download(file_name=f"./downloads/{message.id}/{file_name}")
        
        # Read the file content
        with open(downloaded_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # --- THIS IS THE FIXED LOGIC ---
        # A. Extract names and URLs
        urls = txthtml.extract_names_and_urls(file_content)
        
        # B. Categorize URLs using the new function (returns a dictionary)
        categorized_data = txthtml.categorize_urls(urls)
        
        # C. Generate HTML using the new function
        html_content = txthtml.generate_html(file_name, categorized_data)
        # --- END OF FIXED LOGIC ---

        # Save the generated HTML
        html_file_path = downloaded_file_path.rsplit('.', 1)[0] + ".html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Send the HTML file back to the user
        await message.reply_document(
            document=html_file_path,
            caption=(
                f"✅ **Conversion Successful!**\n\n"
                f"File: **`{file_name.replace('.txt', '.html')}`**\n\n"
                f"ⓘ *Open this file in a web browser (like Chrome) to view the content.*"
            )
        )
        
        # Delete the "Processing" message
        await processing_msg.delete()

    except Exception as e:
        # If any error occurs, inform the user
        await processing_msg.edit_text(
            f"**An error occurred!** 😢\n\n"
            f"**Error:** `{e}`\n\n"
            f"Please check your `.txt` file format. It should be `Name : URL` on each line."
        )
    finally:
        # Clean up downloaded and generated files
        try:
            os.remove(downloaded_file_path)
            os.remove(html_file_path)
        except Exception:
            pass

#=====================================================================================
#                                CALLBACK HANDLERS
#=====================================================================================

@bot.on_callback_query(filters.regex("^checksub$"))
async def recheck_sub_callback(client, callback_query: CallbackQuery):
    # Re-check if the user has joined the channel
    if await check_force_sub(client, callback_query.message):
        await callback_query.answer("✅ Thank you for joining!", show_alert=False)
        await callback_query.message.delete()  # Delete the "join channel" message
        await start_command(client, callback_query.message) # Show the welcome message again
    else:
        await callback_query.answer("You still haven't joined the channel. Please join and try again.", show_alert=True)

#=====================================================================================
#                                RUN THE BOT
#=====================================================================================
if __name__ == "__main__":
    # Create a downloads directory if it doesn't exist
    if not os.path.isdir("downloads"):
        os.makedirs("downloads")
    print("Bot is starting...")
    bot.run()
    print("Bot has stopped.")