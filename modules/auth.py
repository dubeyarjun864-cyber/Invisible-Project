import os
import re
import asyncio
import traceback  # 🆕 Debugging के लिए ज़रूरी
from telethon import TelegramClient, events, Button
from telethon.errors import UserNotParticipantError, SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import MessageReplyHeader
from config import Config

# (बाकी का ऊपर का पूरा कोड सेम रहेगा...)

# ==========================================
# 6. FORCE ITERATOR + TOPIC-WISE PIPELINE (FULLY DEBUGGED VERSION)
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
        print(f"\n[DEBUG] Connected to User Client for ID: {user_id}")
        
        try:
            source_entity = await user_client.get_input_entity(source_chat)
            print(f"[DEBUG] Source Entity Found: {source_entity}")
        except Exception as entity_err:
            print(f"[DEBUG] Input Entity failed, trying get_entity: {entity_err}")
            try:
                source_entity = await user_client.get_entity(source_chat)
                print(f"[DEBUG] Source Entity Found via get_entity: {source_entity}")
            except Exception as final_ent_err:
                print("[DEBUG] CRITICAL: Channel access denied or not a member!")
                traceback.print_exc()
                await progress_msg.edit("❌ **Pipe Failure:** Logged-in account is NOT a member of the source channel or link is invalid.")
                return

        success_count = 0
        total_files = (end_id - start_id) + 1

        reply_header = None
        if topic_id:
            reply_header = MessageReplyHeader(reply_to_msg_id=topic_id)

        print(f"[DEBUG] Starting Loop from ID {start_id} to {end_id}")
        
        async for msg in user_client.iter_messages(source_entity, min_id=start_id-1, max_id=end_id+1, reverse=True):
            if msg.id < start_id or msg.id > end_id:
                continue
                
            try:
                # 1. Check karo source message mil raha hai ya nahi
                if not msg:
                    print(f"[DEBUG] Message ID {msg.id if msg else 'None'} is Empty or Action Message.")
                    continue
                
                if msg.action:
                    print(f"[DEBUG] Skipping action message ID: {msg.id}")
                    continue

                print(f"\n[DEBUG] Processing Message ID: {msg.id}")
                print(f"[DEBUG] Message Media State: {msg.media}")

                caption = msg.text or ""
                if state.get("cap_find") and state.get("cap_replace"):
                    caption = caption.replace(state["cap_find"], state["cap_replace"])
                if state.get("cap_remove"):
                    caption = caption.replace(state["cap_remove"], "")
                if state.get("extra_caption"):
                    caption = f"{caption}\n\n{state['extra_caption']}"

                # 2. Check karo ki message me media hai ya nahi
                if msg.media:
                    await progress_msg.edit(f"📥 **Downloading Media ID:** `{msg.id}`...")
                    
                    temp_dir = "downloads"
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                        
                    # 3. Check karo download_media() kya return kar raha hai
                    print(f"[DEBUG] Attempting download for ID: {msg.id}")
                    file_path = await user_client.download_media(msg, file=temp_dir)
                    print(f"[DEBUG] download_media() returned file_path: {file_path}")
                    
                    # 5. Check if file actually exists on server
                    if file_path and os.path.exists(file_path):
                        print(f"[DEBUG] File successfully exists on disk: {os.path.exists(file_path)}")
                        
                        dir_name, file_name = os.path.split(file_path)
                        if state.get("file_find") and state.get("file_replace"):
                            new_file_name = file_name.replace(state["file_find"], state["file_replace"])
                            new_file_path = os.path.join(dir_name, new_file_name)
                            os.rename(file_path, new_file_path)
                            file_path = new_file_path
                            print(f"[DEBUG] Renamed file path to: {file_path}")

                        await progress_msg.edit(f"📤 **Uploading Media ID:** `{msg.id}`...")
                        
                        print(f"[DEBUG] Uploading file to destination: {dest_chat} with Topic ID: {topic_id}")
                        await user_client.send_file(
                            dest_chat, 
                            file_path, 
                            caption=caption, 
                            reply_to=reply_header, 
                            force_document=False
                        )
                        success_count += 1
                        print(f"[DEBUG] Upload Success for ID: {msg.id}. Removing local file.")
                        os.remove(file_path)
                    else:
                        print(f"[DEBUG] WARNING: download_media returned None or file missing for ID: {msg.id}")
                        # Agar content protected channel hai to forward_messages try karega bypass ke roop me
                        print("[DEBUG] Content might be strictly restricted. Trying fallback forward channel...")
                        try:
                            await user_client.forward_messages(dest_chat, msg.id, source_chat, reply_to=topic_id)
                            success_count += 1
                            print(f"[DEBUG] Fallback forward success for ID: {msg.id}")
                        except Exception as fwd_err:
                            print(f"[DEBUG] Fallback forward also failed: {fwd_err}")
                else:
                    # Text message processing
                    if caption:
                        print(f"[DEBUG] Sending text only message for ID: {msg.id}")
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
                # 4. Exception ko hide nahi kiya, exact traceback print hoga terminal par
                print(f"\n[DEBUG] CRITICAL LOOP ERROR for Message ID {msg.id if msg else 'Unknown'}:")
                traceback.print_exc()
                continue

        await progress_msg.edit(
            f"🏆 **TASK EXECUTION SUCCESSFUL** 🏆\n\n"
            f"📊 **Scanned Operations:** {total_files}\n"
            f"🎉 **Assets Mirrored:** {success_count}\n\n"
            f"🛡️ **Credits:** [{DEVELOPER_NAME}]({DEVELOPER_LINK})"
        )

    except Exception as main_err:
        print("\n[DEBUG] CRITICAL MAIN TRANSFER FAILURE:")
        traceback.print_exc()
        await progress_msg.edit(f"❌ **Pipe Failure:** {str(main_err)}")
    finally:
        await user_client.disconnect()
        if user_id in user_clone_steps:
            del user_clone_steps[user_id]
            
