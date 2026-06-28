import os
import re
import asyncio
from telethon import TelegramClient, events, Button
from telethon.errors import UserNotParticipantError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import MessageReplyHeader
from config import Config

# ==========================================
# 💎 PREMIUM BRANDING & CONFIGURATIONS
# ==========================================
CHANNEL_USERNAME = "EnglishMadhyam_Pdf"
DEVELOPER_LINK = "https://t.me/Stalker_here"
DEVELOPER_NAME = "⏤͟ 𝐏ʀɪᴍe 𝐍ᴏʙɪ𝐓ᴀ !!"

user_login_steps = {}
user_clone_steps = {}

def parse_telegram_link(link_text):
    priv_match = re.search(r't\.me\/c\/(\d+)\/(\d+)', link_text)
    if priv_match:
        return int(f"-100{priv_match.group(1)}"), int(priv_match.group(2))
        
    pub_match = re.search(r't\.me\/([a-zA-Z0-9_]+)\/(\d+)', link_text)
    if pub_match:
        chat_identifier = pub_match.group(1)
        msg_id = int(pub_match.group(2))
        if chat_identifier.isdigit():
            return int(f"-100{chat_identifier}"), msg_id
        return f"@{chat_identifier}", msg_id
        
    return None, None


async def auth_handler(bot: TelegramClient):

    # ==========================================
    # 🆕 0. DYNAMIC /ID COMMAND SYSTEM (FOR CHAT ID)
    # ==========================================
    @bot.on(events.NewMessage(pattern='/id', incoming=True))
    async def get_chat_id(event):
        chat_id = event.chat_id
        chat_title = "This Chat"
        if event.is_channel or event.is_group:
            chat = await event.get_chat()
            chat_title = chat.title
        
        id_text = (
            "📊 **📌 CHAT IDENTIFIER INFO** 📊\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 **Chat Name:** `{chat_title}`\n"
            f"🔹 **Numeric ID:** `{chat_id}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Tip:* Use this exact Numeric ID as your destination during `/clone` setup!"
        )
        await event.respond(id_text)
        raise events.StopPropagation

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
        except Exception:
            is_joined = True 

        if not is_joined:
            buttons = [
                [Button.url("📢 Join Official Channel 📢", f"https://t.me/{CHANNEL_USERNAME}")],
                [Button.inline("🔄 Verify & Access Bot 🔄", b"check_join")]
            ]
            force_text = f"👋 **Welcome {first_name}!**\n\n🛑 **ACCESS DENIED** 🛑\nPlease join our official channel to unlock features."
            
            photo_path = None
            try: 
                photo_path = await bot.download_profile_photo(user_id, file=f"avatar_{user_id}.jpg")
            except Exception: 
                pass

            if photo_path and os.path.exists(photo_path):
                await bot.send_file(event.chat_id, photo_path, caption=force_text, buttons=buttons)
                try: os.remove(photo_path)
                except Exception: pass
            else:
                await event.respond(force_text, buttons=buttons)
            raise events.StopPropagation
            return

        await send_welcome_message(bot, event.chat_id, user_id, first_name)
        raise events.StopPropagation

    # ==========================================
    # 2. /LOGIN COMMAND SYSTEM
    # ==========================================
    @bot.on(events.NewMessage(pattern='/login', incoming=True))
    async def start_login(event):
        user_id = event.sender_id
        if user_id in user_login_steps:
            try: await user_login_steps[user_id]["client"].disconnect()
            except Exception: pass
            
        await event.respond("🔑 **SECURE LOGIN SYSTEM**\nEnter phone number with country code (e.g., `+91XXXXXXXXXX`):\n\n_(Type `/cancel` to abort)_")
        user_login_steps[user_id] = {"step": "phone", "client": None}
        raise events.StopPropagation

    # ==========================================
    # 3. /CLONE COMMAND SYSTEM
    # ==========================================
    @bot.on(events.NewMessage(pattern='/clone', incoming=True))
    async def start_clone(event):
        user_id = event.sender_id
        if not os.path.exists(f"session_{user_id}.session"):
            await event.respond("⚠️ Please login first using `/login`.")
            return
        await event.respond("📊 **CLONE WIZARD [1/3]**\nSend the **First Message Link** (Public or Private):")
        user_clone_steps[user_id] = {"step": "first_link"}
        raise events.StopPropagation

    # ==========================================
    # 4. MASTER INPUT HANDLER
    # ==========================================
    @bot.on(events.NewMessage(incoming=True))
    async def handle_master_inputs(event):
        user_id = event.sender_id
        text = event.text.strip()

        if text.lower() == '/cancel':
            if user_id in user_login_steps:
                try: await user_login_steps[user_id]["client"].disconnect()
                except Exception: pass
                del user_login_steps[user_id]
            if user_id in user_clone_steps:
                del user_clone_steps[user_id]
            await event.respond("🛑 Operation Aborted.")
            raise events.StopPropagation
            return

        if text.startswith('/'):
            return

        # LOGIN INPUT FLOW
        if user_id in user_login_steps:
            state = user_login_steps[user_id]
            if state["step"] == "phone":
                state["step"] = "processing"
                client = TelegramClient(f"session_{user_id}", Config.API_ID, Config.API_HASH)
                try:
                    await client.connect()
                    send_code = await client.send_code_request(text)
                    user_login_steps[user_id] = {"step": "otp", "phone": text, "phone_code_hash": send_code.phone_code_hash, "client": client}
                    await event.respond("📩 Enter OTP Format: `1 2 3 4 5`")
                except Exception as e:
                    await event.respond(f"❌ Error: {e}")
                    del user_login_steps[user_id]
            elif state["step"] == "otp":
                state["step"] = "processing"
                client = state["client"]
                try:
                    await client.sign_in(phone=state["phone"], code=text.replace(" ", ""), phone_code_hash=state["phone_code_hash"])
                    await event.respond("✅ Authorized successfully.")
                    del user_login_steps[user_id]
                except SessionPasswordNeededError:
                    state["step"] = "password"
                    await event.respond("🔐 Enter 2FA Password:")
                except Exception as e:
                    await event.respond(f"❌ Error: {e}")
                    del user_login_steps[user_id]
            elif state["step"] == "password":
                state["step"] = "processing"
                client = state["client"]
                try:
                    await client.sign_in(password=text)
                    await event.respond("✅ 2FA Authorized successfully.")
                    del user_login_steps[user_id]
                except Exception as e:
                    await event.respond(f"❌ Error: {e}")
                    del user_login_steps[user_id]
            raise events.StopPropagation
            return

        # CLONE INPUT FLOW
        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]
            if state["step"] == "first_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id: 
                    await event.respond("❌ Invalid link structure.")
                    raise events.StopPropagation
                    return
                state["source_chat"] = chat_id
                state["start_id"] = msg_id
                state["step"] = "last_link"
                await event.respond("📊 **CLONE WIZARD [2/3]**\nSend the **Last Message Link**:")
            elif state["step"] == "last_link":
                chat_id, msg_id = parse_telegram_link(text)
                if not chat_id: 
                    await event.respond("❌ Invalid link structure.")
                    raise events.StopPropagation
                    return
                state["end_id"] = msg_id
                state["step"] = "dest_chat"
                await event.respond("📌 **CLONE WIZARD [3/3]**\nSend Destination Group/Channel ID or Username:")
            elif state["step"] == "dest_chat":
                if text.isdigit() or text.startswith('-'):
                    state["dest_chat"] = int(text)
                else:
                    state["dest_chat"] = text if text.startswith('@') else f"@{text}"
                
                state["step"] = "menu_waiting"
                state["file_find"], state["file_replace"] = None, None
                state["cap_find"], state["cap_replace"] = None, None
                state["cap_remove"] = None
                state["extra_caption"] = ""
                state["dest_topic"] = None

                buttons = [
                    [Button.inline("📝 Filename: Find & Replace", b"fn_rep")],
                    [Button.inline("💬 Caption: Find & Replace", b"cp_rep")],
                    [Button.inline("✂️ Caption: Remove Text", b"cp_rem")],
                    [Button.inline("➕ Add Extra Caption", b"add_ext")],
                    [Button.inline("🧵 Set Destination Topic ID", b"set_top")],
                    [Button.inline("✅ Done - Start Transfer", b"done_start"),
                     Button.inline("❌ Cancel", b"cancel_task")]
                ]

                await event.respond(
                    f"✅ **Clone Setup Complete**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📥 **Source Chat:** `{state['source_chat']}`\n"
                    f"📤 **Destination Chat:** `{state['dest_chat']}`\n"
                    f"🔢 **Message Range:** `{state['start_id']} - {state['end_id']}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Configure settings below or click Start Transfer:",
                    buttons=buttons
                )

            elif state["step"] == "waiting_fn_find":
                state["file_find"] = text
                state["step"] = "waiting_fn_replace"
                await event.respond("📝 Enter new replacement string:")
            elif state["step"] == "waiting_fn_replace":
                state["file_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Filename pipeline filter saved.")
            elif state["step"] == "waiting_cp_find":
                state["cap_find"] = text
                state["step"] = "waiting_cp_replace"
                await event.respond("💬 Enter new replacement string:")
            elif state["step"] == "waiting_cp_replace":
                state["cap_replace"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Caption pipeline filter saved.")
            elif state["step"] == "waiting_cp_rem":
                state["cap_remove"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Text removal rule saved.")
            elif state["step"] == "waiting_extra_cap":
                state["extra_caption"] = text
                state["step"] = "menu_waiting"
                await event.respond("✅ Extra caption footer text injected.")
            elif state["step"] == "waiting_topic_id":
                try:
                    state["dest_topic"] = int(text)
                    await event.respond(f"✅ Target Topic Thread ID bound to `{text}`.")
                except ValueError:
                    await event.respond("❌ Topic ID must be a numeric integer.")
                state["step"] = "menu_waiting"
            raise events.StopPropagation
            return

    # ==========================================
    # 5. BUTTON CALLBACK ENGINE
    # ==========================================
    @bot.on(events.CallbackQuery)
    async def global_callback_handler(event):
        user_id = event.sender_id
        data = event.data

        if data == b"check_join":
            try:
                await bot(GetParticipantRequest(channel=CHANNEL_USERNAME, participant=user_id))
                await event.delete()
                await send_welcome_message(bot, event.chat_id, user_id, event.sender.first_name)
            except Exception:
                await event.answer("❌ Join channel first!", alert=True)
            raise events.StopPropagation
        elif data == b"btn_login":
            await bot.send_message(event.chat_id, "🔒 Type `/login` to connect.")
            raise events.StopPropagation
        elif data == b"btn_clone":
            await bot.send_message(event.chat_id, "📊 Type `/clone` to start cloning.")
            raise events.StopPropagation

        elif user_id in user_clone_steps:
            state = user_clone_steps[user_id]
            if data == b"fn_rep":
                state["step"] = "waiting_fn_find"
                await event.respond("📝 Enter text to find in filename:")
            elif data == b"cp_rep":
                state["step"] = "waiting_cp_find"
                await event.respond("💬 Enter text to find in caption:")
            elif data == b"cp_rem":
                state["step"] = "waiting_cp_rem"
                await event.respond("✂️ Enter text block to completely remove from caption:")
            elif data == b"add_ext":
                state["step"] = "waiting_extra_cap"
                await event.respond("➕ Enter text to append at bottom:")
            elif data == b"set_top":
                state["step"] = "waiting_topic_id"
                await event.respond("🧵 Enter the numeric Topic/Thread ID:")
            elif data == b"done_start":
                await event.delete()
                asyncio.create_task(start_media_transfer(bot, event, user_id, state))
            elif data == b"cancel_task":
                del user_clone_steps[user_id]
                await event.edit("❌ Canceled.")
            raise events.StopPropagation

# ==========================================
# 6. FORCE ITERATOR + TOPIC-WISE PIPELINE (100% REAL DOWNLOAD & UPLOAD)
# ==========================================
async def start_media_transfer(bot, event, user_id, state):
    source_chat = state["source_chat"]
    start_id = state["start_id"]
    end_id = state["end_id"]
    dest_chat = state["dest_chat"]
    topic_id = state.get("dest_topic")

    if start_id > end_id:
        start_id, end_id = end_id, start_id

    progress_msg = await bot.send_message(event.chat_id, "🚀 **Initializing Protected Media Pipeline...**")
    user_client = TelegramClient(f"session_{user_id}", Config.API_ID, Config.API_HASH)
    
    try:
        await user_client.connect()
        
        try:
            source_entity = await user_client.get_input_entity(source_chat)
        except Exception:
            source_entity = source_chat

        success_count = 0
        total_files = (end_id - start_id) + 1

        reply_header = None
        if topic_id:
            reply_header = MessageReplyHeader(reply_to_msg_id=topic_id)

        async for msg in user_client.iter_messages(source_entity, min_id=start_id-1, max_id=end_id+1, reverse=True):
            if msg.id < start_id or msg.id > end_id:
                continue
                
            try:
                if not msg or msg.action:
                    continue

                caption = msg.text or ""
                if state.get("cap_find") and state.get("cap_replace"):
                    caption = caption.replace(state["cap_find"], state["cap_replace"])
                if state.get("cap_remove"):
                    caption = caption.replace(state["cap_remove"], "")
                if state.get("extra_caption"):
                    caption = f"{caption}\n\n{state['extra_caption']}"

                if msg.media:
                    await progress_msg.edit(f"📥 **Downloading Media ID:** `{msg.id}`...")
                    
                    temp_dir = "downloads"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                        
                    file_path = await user_client.download_media(msg, file=temp_dir)
                    
                    if file_path and os.path.exists(file_path):
                        dir_name, file_name = os.path.split(file_path)
                        if state.get("file_find") and state.get("file_replace"):
                            new_file_name = file_name.replace(state["file_find"], state["file_replace"])
                            new_file_path = os.path.join(dir_name, new_file_name)
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path

                        await progress_msg.edit(f"📤 **Uploading Media ID:** `{msg.id}`...")
                        
                        await user_client.send_file(
                            dest_chat, 
                            file_path, 
                            caption=caption, 
                            reply_to=reply_header, 
                            force_document=False
                        )
                        success_count += 1
                        os.remove(file_path)
                else:
                    if caption:
                        await user_client.send_message(dest_chat, caption, reply_to=reply_header)
                        success_count += 1

                await progress_msg.edit(
                    f"✨ **PREMIUM MONITOR DASHBOARD** ✨\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔄 **Task Status:** Active Transcoding\n"
                    f"✅ **Cloned Queue:** `{success_count}/{total_files}`\n"
                    f"📌 **Current Tracking ID:** `{msg.id}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👑 **Powered By:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
                )
                await asyncio.sleep(2.5)

            except Exception as loop_err:
                print(f"Loop error for message {msg.id}: {loop_err}")
                continue

        await progress_msg.edit(
            f"🏆 **TASK EXECUTION SUCCESSFUL** 🏆\n\n"
            f"📊 **Scanned Operations:** {total_files}\n"
            f"🎉 **Assets Mirrored:** {success_count}\n\n"
            f"🛡️ **Credits:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
        )

    except Exception as main_err:
        await progress_msg.edit(f"❌ **Pipe Failure:** {str(main_err)}")
    finally:
        await user_client.disconnect()
        if user_id in user_clone_steps:
            del user_clone_steps[user_id]


async def send_welcome_message(bot, chat_id, user_id, first_name):
    welcome_buttons = [
        [Button.inline("🔑 LINK USER ACCOUNT 🔑", b"btn_login")],
        [Button.inline("📊 START CLONING PIPELINE 📊", b"btn_clone")]
    ]
    await bot.send_message(chat_id, f"👑 Welcome **{first_name}** to Extreme Terminal v2.0!", buttons=welcome_buttons)
