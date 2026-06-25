import os
import re
import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import UserNotParticipantError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantRequest
from config import Config

# ==========================================
# 💎 GLOBAL BRANDING & CONFIGURATIONS
# ==========================================
CHANNEL_USERNAME = "English_Madhyam_2026" 
DEVELOPER_LINK = "https://t.me/Stalker_here"
DEVELOPER_NAME = "⏤͟ 𝐏ʀɪᴍe 𝐍ᴏʙɪ𝐓ᴀ !!"

# State Tracking Dictionaries
user_login_steps = {}
user_clone_steps = {}

# Link Parsing Helper
def parse_telegram_link(link_text):
    match = re.search(r'(?:t\.me\/c\/|t\.me\/)([a-zA-Z0-9_]+|\d+)\/(\d+)', link_text)
    if match:
        chat_identifier = match.group(1)
        msg_id = int(match.group(2))
        if chat_identifier.isdigit():
            chat_identifier = int(f"-100{chat_identifier}")
        return chat_identifier, msg_id
    return None, None


async def auth_handler(bot: TelegramClient):

    # ==========================================
    # 1. /START COMMAND (FORCE JOIN + WELCOME)
    # ==========================================
    @bot.on(events.NewMessage(pattern='/start', incoming=True))
    async def welcome_and_force_join(event):
        user_id = event.sender_id
        first_name = event.sender.first_name or "User"
        
        try:
            await bot(GetParticipantRequest(channel=CHANNEL_USERNAME, participant=user_id))
            is_joined = True
        except UserNotParticipantError:
            is_joined = False
        except Exception as e:
            print(f"Force Join Check Error: {e}")
            is_joined = True 

        # If not joined ➡️ Show Force Join Interface
        if not is_joined:
            buttons = [
                [Button.url("📢 Join Channel", f"https://t.me/{CHANNEL_USERNAME}")],
                [Button.inline("🔄 Check Again", b"check_join")]
            ]
            
            photo_path = None
            try: photo_path = await bot.download_profile_photo(user_id, file=f"avatar_{user_id}.jpg")
            except Exception: pass

            force_text = (
                f"👋 **Hey {first_name}!**\n\n"
                f"⚠️ **Access Denied!**\n"
                f"Is bot ko use karne ke liye aapko hamare official channel ko join karna zaroori hai.\n\n"
                f"Neeche diye gaye button par click karke join karein aur fir **Check Again** par click karein.\n\n"
                f"🛠 *Dev:* [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
                f"🎧 *Support:* [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
            )

            if photo_path and os.path.exists(photo_path):
                await bot.send_file(event.chat_id, photo_path, caption=force_text, buttons=buttons)
                try: os.remove(photo_path)
                except Exception: pass
            else:
                await event.respond(force_text, buttons=buttons, link_preview=False)
            return

        # If joined ➡️ Direct Welcome Flow
        await send_welcome_message(bot, event.chat_id, user_id, first_name)


    # ==========================================
    # 2. /LOGIN COMMAND SYSTEM (WITH CANCEL & 2FA DETECTION)
    # ==========================================
    @bot.on(events.NewMessage(pattern='/login', incoming=True))
    async def start_login(event):
        user_id = event.sender_id
        
        if user_id in user_login_steps:
            try: await user_login_steps[user_id]["client"].disconnect()
            except Exception: pass
            
        await event.respond(
            "🔒 **Login Step 1/3:** Kripya apna phone number International Format me bhejen.\n"
            "Udaharand: `+91XXXXXXXXXX` \n\n"
            "_(Process cancel karne ke liye `/cancel` bhejen)_"
        )
        user_login_steps[user_id] = {"step": "phone", "client": None}


    # ==========================================
    # 3. /CLONE COMMAND SYSTEM (INITIALIZATION)
    # ==========================================
    @bot.on(events.NewMessage(pattern='/clone', incoming=True))
    async def start_clone(event):
        user_id = event.sender_id
        if not os.path.exists(f"session_{user_id}.session"):
            await event.respond("❌ **Access Denied!** Pehle `/login` karke apna account connect karein.")
            return
        await event.respond("📊 **Clone Step 1/3:** Source channel ke **First Message** ka link bhejen.")
        user_clone_steps[user_id] = {"step": "first_link"}


    # ==========================================
    # 4. MASTER DYNAMIC INPUT HANDLER (LOGIN & CLONE INPUTS)
    # ==========================================
    @bot.on(events.NewMessage(incoming=True))
    async def handle_master_inputs(event):
        user_id = event.sender_id
        text = event.text.strip()

        # Global Cancel Hook
        if text.lower() == '/cancel':
            # Clear Login States
            if user_id in user_login_steps:
                if user_login_steps[user_id]["client"]:
                    try: await user_login_steps[user_id]["client"].disconnect()
                    except Exception: pass
                del user_login_steps[user_id]
            # Clear Clone States
            if user_id in user_clone_steps:
                del user_clone_steps[user_id]
                
            await event.respond("🛑 **Process Cancelled!** Aapka active session aur inputs clear kar diye gaye hain.")
            return

        if text.startswith('/') and text.lower() not in ['/cancel']:
            return

        # 🛑 PART A: HANDLING LOGIN INPUTS
        if user_id in user_login_steps:
            state = user_login_steps[user_id]
            
            if state["step"] == "phone":
                state["step"] = "processing"
                await event.respond("⏳ Number verify karke OTP bheja ja raha hai, kripya wait karein...")
                
                client = TelegramClient(f"session_{user_id}", Config.API_ID, Config.API_HASH)
                try:
                    await client.connect()
                    send_code = await client.send_code_request(text)
                    user_login_steps[user_id] = {
                        "step": "otp",
                        "phone": text,
                        "phone_code_hash": send_code.phone_code_hash,
                        "client": client
                    }
                    await event.respond("📩 **Login Step 2/3:** Aapke Telegram par aaya 5-digits ka OTP bhejen.\nFormat: `1 2 3 4 5`")
                except Exception as e:
                    await event.respond(f"❌ Error: {str(e)}\nKripya `/login` karke dubara try karein.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

            elif state["step"] == "otp":
                state["step"] = "processing"
                otp_code = text.replace(" ", "").replace("-", "")
                client = state["client"]
                
                try:
                    await client.sign_in(phone=state["phone"], code=otp_code, phone_code_hash=state["phone_code_hash"])
                    await event.respond("✅ **Login Successful!** Aapka account bot se successfully jud chuka hai. (No 2FA)")
                    del user_login_steps[user_id]
                except SessionPasswordNeededError:
                    state["step"] = "password"
                    await event.respond("🔐 **Login Step 3/3:** Aapke account par 2FA enabled hai. Kripya apna Two-Step Verification password dalen.")
                except Exception as e:
                    await event.respond(f"❌ Galat OTP: {str(e)}\nKripya `/login` se dubara shuru karein.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

            elif state["step"] == "password":
                state["step"] = "processing"
                client = state["client"]
                try:
                    await client.sign_in(password=text)
                    await event.respond("✅ **Login Successful!** Aapka 2FA account bot se successfully jud chuka hai.")
                    del user_login_steps[user_id]
                except Exception as e:
                    await event.respond(f"❌ Galat Password: {str(e)}\nKripya `/login` se dubara try karein.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

        # 🛑 PART B: HANDLING CLONE INPUTS
        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]

            if state["step"] == "first_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id or not msg_id:
                    await event.respond("❌ **Invalid Link!** Sahi message link bhejen.")
                    return
                state["source_chat"] = chat_id
                state["start_id"] = msg_id
                state["step"] = "last_link"
                await event.respond("📊 **Clone Step 2/3:** Ab **Last Message** ka link bhejen.")

            elif state["step"] == "last_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id or not msg_id:
                    await event.respond("❌ **Invalid Link!** Sahi message link bhejen.")
                    return
                if chat_id != state["source_chat"]:
                    await event.respond("❌ **Error:** Links ek hi channel ke hone chahiye!")
                    return
                state["end_id"] = msg_id
                state["step"] = "dest_chat"
                await event.respond("📌 **Clone Step 3/3:** Destination Channel/Group ka Username ya ID bhejen (`@channel` ya `-100xxx`).")

            elif state["step"] == "dest_chat":
                dest_chat = text
                if not dest_chat.startswith('-') and not dest_chat.startswith('@'):
                    dest_chat = f"@{dest_chat}"
                    
                state["dest_chat"] = dest_chat
                state["step"] = "menu_waiting"
                
                # Default Customization Structs
                state["file_find"], state["file_replace"] = None, None
                state["cap_find"], state["cap_replace"] = None, None
                state["extra_caption"] = ""

                # 🛠️ PREMIUM VIDEO CUSTOMIZATION MENU BUTTONS
                buttons = [
                    [Button.inline("📝 Filename: Find & Replace", b"fn_rep"),
                     Button.inline("💬 Caption: Find & Replace", b"cp_rep")],
                    [Button.inline("➕ Add Extra Caption", b"add_ext")],
                    [Button.inline("⏩ Skip & Start Transfer", b"skip_start")],
                    [Button.inline("✅ Done - Start", b"done_start"),
                     Button.inline("❌ Cancel", b"cancel_task")]
                ]

                await event.respond(
                    "⚙️ **File k कस्टमाइजेशन का मेन्यू:**\n\n"
                    "Agar aap Filename ya Caption me kuch badalna chahte hain, toh neeche diye gaye buttons use karein.\n"
                    "Agar koi badlav nahi chahiye, toh direct **Skip & Start Transfer** par click karein!",
                    buttons=buttons
                )

            # Text captures for replacements
            elif state["step"] == "waiting_fn_find":
                state["file_find"] = text
                state["step"] = "waiting_fn_replace"
                await event.respond("📝 **Filename Text:** Ab wo text likhen jisse replace karna hai:")
                
            elif state["step"] == "waiting_fn_replace":
                state["file_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond(f"✅ Filename change set!\nAb aap task start kar sakte hain.")

            elif state["step"] == "waiting_cp_find":
                state["cap_find"] = text
                state["step"] = "waiting_cp_replace"
                await event.respond("💬 **Caption Text:** Ab wo text likhen jisse replace karna hai:")

            elif state["step"] == "waiting_cp_replace":
                state["cap_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond(f"✅ Caption change set!\nAb aap task start kar sakte hain.")

            elif state["step"] == "waiting_extra_cap":
                state["extra_caption"] = text
                state["step"] = "menu_waiting"
                await event.respond(f"✅ Extra Caption set!\nAb aap task start kar sakte hain.")


    # ==========================================
    # 5. ALL INLINE KEYBOARD CALLBACK QUERIES
    # ==========================================
    @bot.on(events.CallbackQuery)
    async def global_callback_handler(event):
        user_id = event.sender_id
        first_name = event.sender.first_name or "User"
        data = event.data

        # Force Join Button Actions
        if data == b"check_join":
            try:
                await bot(GetParticipantRequest(channel=CHANNEL_USERNAME, participant=user_id))
                await event.delete() 
                await send_welcome_message(bot, event.chat_id, user_id, first_name)
            except UserNotParticipantError:
                await event.answer("❌ Aapne abhi tak channel join nahi kiya hai! Kripya pehle join karein.", alert=True)
                
        elif data == b"btn_login":
            await bot.send_message(event.chat_id, "🔒 Please type `/login` to start the connection process.")
            await event.answer()
            
        elif data == b"btn_clone":
            await bot.send_message(event.chat_id, "📊 Please type `/clone` to configure your cloning task.")
            await event.answer()

        # Clone Menu Button Actions
        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]
            
            if data == b"fn_rep":
                state["step"] = "waiting_fn_find"
                await event.edit("📝 **Filename کस्टमाइजेशन:** Wo text type karke bhejen jise aap file ke naam me se **Hataana/Find** chahte hain:")
            elif data == b"cp_rep":
                state["step"] = "waiting_cp_find"
                await event.edit("💬 **Caption कस्टमाइजेशन:** Wo text type karke bhejen jise aap video caption me se **Hataana/Find** chahte hain:")
            elif data == b"add_ext":
                state["step"] = "waiting_extra_cap"
                await event.edit("➕ **Add Extra Caption:** Jo text aap har video ke niche extra jodhna chahte hain, wo type karke bhejen:")
            elif data in [b"skip_start", b"done_start"]:
                await event.delete()
                asyncio.create_task(start_media_transfer(bot, event, user_id, state))
            elif data == b"cancel_task":
                del user_clone_steps[user_id]
                await event.edit("❌ **Task Cancelled!** Aapka clone process rok diya gaya hai.")


# ==========================================
# 6. CORE CUSTOM MEDIA BYPASS TRANSFER LOGIC
# ==========================================
async def start_media_transfer(bot, event, user_id, state):
    source_chat = state["source_chat"]
    start_id = state["start_id"]
    end_id = state["end_id"]
    dest_chat = state["dest_chat"]

    if start_id > end_id:
        start_id, end_id = end_id, start_id

    progress_msg = await bot.send_message(event.chat_id, "⏳ **Initializing Transfer & Customizations...**")
    user_client = TelegramClient(f"session_{user_id}", Config.API_ID, Config.API_HASH)
    
    try:
        await user_client.connect()
        success_count = 0
        total_files = (end_id - start_id) + 1

        for current_id in range(start_id, end_id + 1):
            try:
                msg = await user_client.get_messages(source_chat, ids=current_id)
                if not msg or msg.action:
                    continue

                caption = msg.text or ""
                
                # Apply Caption Find & Replace
                if state.get("cap_find") and state.get("cap_replace"):
                    caption = caption.replace(state["cap_find"], state["cap_replace"])
                
                # Apply Extra Caption Addition
                if state.get("extra_caption"):
                    caption = f"{caption}\n\n{state['extra_caption']}"

                # 📥 MEDIA DOWNLOADING & UPLOADING CORE BYPASS ENGINE
                if msg.media:
                    await progress_msg.edit(f"📥 Downloading Media (ID: `{current_id}`)...")
                    file_path = await user_client.download_media(msg)
                    
                    if file_path:
                        # Apply Filename Find & Replace
                        dir_name, file_name = os.path.split(file_path)
                        if state.get("file_find") and state.get("file_replace"):
                            new_file_name = file_name.replace(state["file_find"], state["file_replace"])
                            new_file_path = os.path.join(dir_name, new_file_name)
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path

                        await progress_msg.edit(f"📤 Uploading Customized Media to Destination...")
                        await user_client.send_file(dest_chat, file_path, caption=caption)
                        success_count += 1
                        
                        if os.path.exists(file_path):
                            os.remove(file_path)
                else:
                    # Pure Text Messages
                    if caption:
                        await user_client.send_message(dest_chat, caption)
                        success_count += 1

                # 🤖 LIVE TASK PROCESS SYSTEM WINDOW
                await progress_msg.edit(
                    f"🤖 **Live Progress Counter:**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔄 Status: Copying Files...\n"
                    f"✅ Successfully Cloned: `{success_count}/{total_files}`\n"
                    f"📌 Current Message ID: `{current_id}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛠️ **Dev:** [{DEVELOPER_NAME}](https://t.me/Stalker_here)"
                )
                await asyncio.sleep(2.0)

            except Exception as e:
                print(f"Error at Message {current_id}: {e}")
                continue

        await progress_msg.edit(
            f"✅ **Task Completed Successfully!**\n\n"
            f"📊 Total Scanned: {total_files}\n"
            f"🎉 Successfully Cloned: {success_count}\n\n"
            f"💳 **Credits:** [{DEVELOPER_NAME}](https://t.me/Stalker_here)"
        )

    except Exception as main_err:
        await progress_msg.edit(f"❌ **Transfer Error:** {str(main_err)}")
    finally:
        await user_client.disconnect()
        if user_id in user_clone_steps:
            del user_clone_steps[user_id]


# Welcome Message Reusable Helper
async def send_welcome_message(bot, chat_id, user_id, first_name):
    welcome_buttons = [
        [Button.inline("🔑 Connect Account (/login)", b"btn_login")],
        [Button.inline("📊 Clone Content (/clone)", b"btn_clone")],
        [Button.url("👨‍💻 Developer", DEVELOPER_LINK), Button.url("🎧 Support", DEVELOPER_LINK)]
    ]
    
    photo_path = None
    try: photo_path = await bot.download_profile_photo(user_id, file=f"avatar_{user_id}.jpg")
    except Exception: pass

    welcome_text = (
        f"🎉 **Welcome {first_name} to Extreme Transfer Bot!**\n\n"
        f"Main aapke kisi bhi Telegram channel ka content clone karke aapke destination topic ya group me bhej sakta hoon.\n\n"
        f"⚡ **Aage badhne ke liye neeche diye gaye options select karein:**\n\n"
        f"💳 **Credits:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})\n"
        f"📢 **Channel:** [English Madhyam](https://t.me/{CHANNEL_USERNAME})\n"
        f"🎧 **Support:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
    )

    if photo_path and os.path.exists(photo_path):
        await bot.send_file(chat_id, photo_path, caption=welcome_text, buttons=welcome_buttons)
        try: os.remove(photo_path)
        except Exception: pass
    else:
        await bot.send_message(chat_id, welcome_text, buttons=welcome_buttons, link_preview=False)
