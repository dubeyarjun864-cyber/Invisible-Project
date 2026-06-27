import asyncio
import sys
import os
from telethon import TelegramClient
from config import Config
from modules.auth import auth_handler
from aiohttp import web

bot = TelegramClient('extreme_bot', Config.API_ID, Config.API_HASH)

async def handle_ping(request):
    return web.Response(text="Bot is running smoothly on Render!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Dummy Web Server started on port {port}")

async def start_bot():
    print("⚡ Extreme Transfer Bot Starting...")
    await start_dummy_server()
    await bot.start(bot_token=Config.BOT_TOKEN)
    print("✅ Bot Connected Successfully!")
    
    # Load Master Handler
    await auth_handler(bot)
    
    print("🚀 Bot is now running 24/7 in background...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(start_bot())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot stopped manually by user.")
