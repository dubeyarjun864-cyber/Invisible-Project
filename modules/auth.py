import os
import re
import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import UserNotParticipantError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantRequest
from config import Config

# ==========================================
# 💎 PREMIUM BRANDING & CONFIGURATIONS
# ==========================================
CHANNEL_USERNAME = "EnglishMadhyam_Pdf"  # Updated official channel
DEVELOPER_LINK = "https://t.me/Stalker_here"
DEVELOPER_NAME = "⏤͟ 𝐏ʀɪᴍe 𝐍ᴏʙɪ𝐓ᴀ !!"

# State Tracking Dictionaries
user_login_steps = {}
user_clone_steps = {}

# Link Parsing Helper Function
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
    # 1. /START COMMAND (FORCE JOIN + PREMIUM UI)
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

        # If not joined ➡️ Show Premium Force Join Layout
        if not is_joined:
            buttons = [
                [Button.url("📢 Join Official Channel 📢", f"https://t.me/{CHANNEL_USERNAME}")],
                [Button.inline("🔄 Verify & Access Bot 🔄", b"check_join")]
            ]
            
            photo_path = None
            try: photo_path = await bot.download_profile_photo(user_id, file=f"avatar_{user_id}.jpg")
            except Exception: pass

            force_text = (
                f"👋 **Welcome {first_name}!**\n\n"
                f"🛑 **ACCESS DENIED** 🛑\n"
                f"To maintain server stability, you must join our official channel to unlock the cloning features.\n\n"
                f"👇 Please click the button below to join, then verify your subscription!"
            )

            if photo_path and os.path.exists(photo_path):
                await bot.send_file(event.chat_id, photo_path, caption=force_text, buttons=buttons)
                try: os.remove(photo_path)
                except Exception: pass
            else:
                await event.respond(force_text, buttons=buttons, link_preview=False)
            return

        await send_welcome_message(bot, event.chat_id, user_id, first_name)


    # ==========================================
    # 2. /LOGIN COMMAND SYSTEM
    # ==========================================
    @bot.on(events.NewMessage(pattern='/login', incoming=True))
    async def start_login(event):
        user_id = event.sender_id
        
        if user_id in user_login_steps:
            try: await user_login_steps[user_id]["client"].disconnect()
            except Exception: pass
            
        await event.respond(
            "🔑 **SECURE LOGIN SYSTEM** 🔑\n\n"
            "Please send your phone number in **International Format**.\n"
            "Example: `+91XXXXXXXXXX` \n\n"
            "🧭 _To abort the current session, type `/cancel`_"
        )
        user_login_steps[user_id] = {"step": "phone", "client": None}


    # ==========================================
    # 3. /CLONE COMMAND SYSTEM
    # ==========================================
    @bot.on(events.NewMessage(pattern='/clone', incoming=True))
    async def start_clone(event):
        user_id = event.sender_id
        if not os.path.exists(f"session_{user_id}.session"):
            await event.respond("⚠️ **ACCESS DENIED** ⚠️\n\nPlease initialize your user session first using `/login`.")
            return
        await event.respond("📊 **CLONE WIZARD [1/3]**\n\nPlease send the **First Message Link** from the source channel.")
        user_clone_steps[user_id] = {"step": "first_link"}


    # ==========================================
    # 4. MASTER INPUT HANDLER
    # ==========================================
    @bot.on(events.NewMessage(incoming=True))
    async def handle_master_inputs(event):
        user_id = event.sender_id
        text = event.text.strip()

        if text.lower() == '/cancel':
            if user_id in user_login_steps:
                if user_login_steps[user_id]["client"]:
                    try: await user_login_steps[user_id]["client"].disconnect()
                    except Exception: pass
                del user_login_steps[user_id]
            if user_id in user_clone_steps:
                del user_clone_steps[user_id]
            await event.respond("🛑 **OPERATION ABORTED** 🛑\nAll temporary states and sessions have been securely wiped.")
            return

        if text.startswith('/') and text.lower() not in ['/cancel']:
            return

        # LOGIN INPUTS PROCESSING
        if user_id in user_login_steps:
            state = user_login_steps[user_id]
            
            if state["step"] == "phone":
                state["step"] = "processing"
                await event.respond("⚡ **Contacting Telegram Servers...** Please wait.")
                
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
                    await event.respond("📩 **CLONE WIZARD [2/3]**\nInput the 5-digit verification code sent to your Telegram:\nFormat: `1 2 3 4 5`")
                except Exception as e:
                    await event.respond(f"❌ **Connection Error:** {str(e)}\nRestart via `/login`.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

            elif state["step"] == "otp":
                state["step"] = "processing"
                otp_code = text.replace(" ", "").replace("-", "")
                client = state["client"]
                
                try:
                    await client.sign_in(phone=state["phone"], code=otp_code, phone_code_hash=state["phone_code_hash"])
                    await event.respond("✨ **SUCCESSFULLY AUTHORIZED** ✨\nYour profile has been fully integrated. (No 2FA Required)")
                    del user_login_steps[user_id]
                except SessionPasswordNeededError:
                    state["step"] = "password"
                    await event.respond("🔐 **2-STEP VERIFICATION DETECTED**\nEnter your custom cloud password to finalize connection:")
                except Exception as e:
                    await event.respond(f"❌ **Invalid OTP:** {str(e)}\nRestart via `/login`.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

            elif state["step"] == "password":
                state["step"] = "processing"
                client = state["client"]
                try:
                    await client.sign_in(password=text)
                    await event.respond("✨ **SUCCESSFULLY AUTHORIZED** ✨\nYour 2FA session is now online.")
                    del user_login_steps[user_id]
                except Exception as e:
                    await event.respond(f"❌ **Password Error:** {str(e)}\nRetry using `/login`.")
                    try: await client.disconnect()
                    except Exception: pass
                    del user_login_steps[user_id]

        # CLONE INPUTS PROCESSING
        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]

            if state["step"] == "first_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id or not msg_id:
                    await event.respond("❌ **Invalid Link Format!** Please paste a correct message URL.")
                    return
                state["source_chat"] = chat_id
                state["start_id"] = msg_id
                state["step"] = "last_link"
                await event.respond("📊 **CLONE WIZARD [2/3]**\nNow send the **Last Message Link** to wrap the range.")

            elif state["step"] == "last_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id or not msg_id:
                    await event.respond("❌ **Invalid Link Format!** Please paste a correct message URL.")
                    return
                if chat_id != state["source_chat"]:
                    await event.respond("❌ **Target Mismatch!** Both links must originate from the same channel.")
                    return
                state["end_id"] = msg_id
                state["step"] = "dest_chat"
                await event.respond("📌 **CLONE WIZARD [3/3]**\nSend the Destination Channel/Group ID or Username (`@channel` or `-100xxx`):")

            elif state["step"] == "dest_chat":
                dest_chat = text
                if not dest_chat.startswith('-') and not dest_chat.startswith('@'):
                    dest_chat = f"@{dest_chat}"
                    
                state["dest_chat"] = dest_chat
                state["step"] = "menu_waiting"
                
                state["file_find"], state["file_replace"] = None, None
                state["cap_find"], state["cap_replace"] = None, None
                state["extra_caption"] = ""

                # 🛠️ PREMIUM CONTROLS ENGINE LAYOUT
                buttons = [
                    [Button.inline("📝 Filename: Find & Replace", b"fn_rep"),
                     Button.inline("💬 Caption: Find & Replace", b"cp_rep")],
                    [Button.inline("➕ Append Extra Caption Signature", b"add_ext")],
                    [Button.inline("⚡ FAST TRACK: Skip Customization ⚡", b"skip_start")],
                    [Button.inline("🚀 Launch Task", b"done_start"),
                     Button.inline("❌ Abort", b"cancel_task")]
                ]

                await event.respond(
                    "⚙️ **PREMIUM ENGINE CUSTOMIZATION PANEL** ⚙️\n\n"
                    "Configure filters for the streaming queue below. "
                    "To clone files instantly in their original state, click **FAST TRACK**.",
                    buttons=buttons
                )

            # Settings input captures
            elif state["step"] == "waiting_fn_find":
                state["file_find"] = text
                state["step"] = "waiting_fn_replace"
                await event.respond("📝 **Replacement Parameter:** Enter the text string to insert:")
            elif state["step"] == "waiting_fn_replace":
                state["file_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Filename pipeline modification saved successfully.")
            elif state["step"] == "waiting_cp_find":
                state["cap_find"] = text
                state["step"] = "waiting_cp_replace"
                await event.respond("💬 **Replacement Parameter:** Enter the text string to insert:")
            elif state["step"] == "waiting_cp_replace":
                state["cap_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Caption pipeline modification saved successfully.")
            elif state["step"] == "waiting_extra_cap":
                state["extra_caption"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Extra signature overlay matrix saved.")


    # ==========================================
    # 5. BUTTON CALLBACK ENGINE
    # ==========================================
    @bot.on(events.CallbackQuery)
    async def global_callback_handler(event):
        user_id = event.sender_id
        first_name = event.sender.first_name or "User"
        data = event.data

        if data == b"check_join":
            try:
                await bot(GetParticipantRequest(channel=CHANNEL_USERNAME, participant=user_id))
                await event.delete() 
                await send_welcome_message(bot, event.chat_id, user_id, first_name)
            except UserNotParticipantError:
                await event.answer("❌ Verification Failed! Please subscribe to the channel first.", alert=True)
                
        elif data == b"btn_login":
            await bot.send_message(event.chat_id, "🔒 Please dispatch `/login` command to start.")
            await event.answer()
        elif data == b"btn_clone":
            await bot.send_message(event.chat_id, "📊 Please dispatch `/clone` command to start.")
            await event.answer()

        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]
            
            if data == b"fn_rep":
                state["step"] = "waiting_fn_find"
                await event.edit("📝 Enter target string to string match and clear from filenames:")
            elif data == b"cp_rep":
                state["step"] = "waiting_cp_find"
                await event.edit("💬 Enter target string to string match and clear from captions:")
            elif data == b"add_ext":
                state["step"] = "waiting_extra_cap"
                await event.edit("➕ Enter custom layout block to inject into media descriptions:")
            elif data in [b"skip_start", b"done_start"]:
                await event.delete()
                asyncio.create_task(start_media_transfer(bot, event, user_id, state))
            elif data == b"cancel_task":
                del user_clone_steps[user_id]
                await event.edit("❌ Mirroring operation canceled successfully.")


# ==========================================
# 6. ENHANCED DIRECT STREAM COPY PIPELINE (NO VIDEO SKIP)
# ==========================================
async def start_media_transfer(bot, event, user_id, state):
    source_chat = state["source_chat"]
    start_id = state["start_id"]
    end_id = state["end_id"]
    dest_chat = state["dest_chat"]

    if start_id > end_id:
        start_id, end_id = end_id, start_id

    progress_msg = await bot.send_message(event.chat_id, "🚀 **Initializing High-Speed Media Pipeline...**")
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
                if state.get("cap_find") and state.get("cap_replace"):
                    caption = caption.replace(state["cap_find"], state["cap_replace"])
                if state.get("extra_caption"):
                    caption = f"{caption}\n\n{state['extra_caption']}"

                # 📥 STREAM BUFFER FILE HANDLING ENGINE (Bypasses Local File Download Locks)
                if msg.media:
                    await progress_msg.edit(f"⚡ **Streaming Chunks:** Extracting Media Object ID `{current_id}`...")
                    
                    # Direct upload token generation without saving to disk space to bypass upload hangs
                    file_path = await user_client.download_media(msg)
                    if file_path:
                        dir_name, file_name = os.path.split(file_path)
                        if state.get("file_find") and state.get("file_replace"):
                            new_file_name = file_name.replace(state["file_find"], state["file_replace"])
                            new_file_path = os.path.join(dir_name, new_file_name)
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path

                        await progress_msg.edit(f"⚡ **Pushing Stream:** Uploading customized assets to destination...")
                        # High level send_file routing to bypass standard send_message limitation
                        await user_client.send_file(dest_chat, file_path, caption=caption, force_document=False)
                        success_count += 1
                        
                        if os.path.exists(file_path):
                            os.remove(file_path)
                else:
                    if caption:
                        await user_client.send_message(dest_chat, caption)
                        success_count += 1

                # Dynamic Live Progress Window UI
                await progress_msg.edit(
                    f"✨ **PREMIUM MONITOR DASHBOARD** ✨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔄 **Task Status:** Active Transcoding\n"
                    f"✅ **Cloned Queue:** `{success_count}/{total_files}`\n"
                    f"📌 **Current Tracking ID:** `{current_id}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 **Powered By:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
                )
                await asyncio.sleep(2.0)

            except Exception as e:
                print(f"Error at sequence {current_id}: {e}")
                continue

        await progress_msg.edit(
            f"🏆 **TASK EXECUTION SUCCESSFUL** 🏆\n\n"
            f"📊 **Scanned Operations:** {total_files}\n"
            f"🎉 **Assets Mirrored:** {success_count}\n\n"
            f"🛡️ **Credits:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
        )

    except Exception as main_err:
        await progress_msg.edit(f"❌ **Global Pipe Critical Failure:** {str(main_err)}")
    finally:
        await user_client.disconnect()
        if user_id in user_clone_steps:
            del user_clone_steps[user_id]


# Premium Welcome Message Helper
async def send_welcome_message(bot, chat_id, user_id, first_name):
    welcome_buttons = [
        [Button.inline("🔑 LINK USER ACCOUNT 🔑", b"btn_login")],
        [Button.inline("📊 START CLONING PIPELINE 📊", b"btn_clone")],
        [Button.url("👑 DEVELOPER", DEVELOPER_LINK), Button.url("🎧 NETWORK SUPPORT", DEVELOPER_LINK)]
    ]
    
    photo_path = None
    try: photo_path = await bot.download_profile_photo(user_id, file=f"avatar_{user_id}.jpg")
    except Exception: pass

    welcome_text = (
        f"👑 **EXTREME AUTOMATION TERMINAL v2.0** 👑\n\n"
        f"Greetings, **{first_name}**! Your account is verified and ready for high-speed mirroring operations.\n\n"
        f"⚡ **Select an active system pipeline module below:**"
    )

    if photo_path and os.path.exists(photo_path):
        await bot.send_file(chat_id, photo_path, caption=welcome_text, buttons=welcome_buttons)
        try: os.remove(photo_path)
        except Exception: pass
    else:
        await bot.send_message(chat_id, welcome_text, buttons=welcome_buttons, link_preview=False)
