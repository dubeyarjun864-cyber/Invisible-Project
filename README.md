# 🚀 Extreme Transfer Bot 

<p align="center">
  <img src="https://img.shields.io/github/license/ArjunBotz/ExtremeTransferBot?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/github/stars/ArjunBotz/ExtremeTransferBot?style=for-the-badge" alt="Stars">
  <img src="https://img.shields.io/github/forks/ArjunBotz/ExtremeTransferBot?style=for-the-badge" alt="Forks">
</p>

**Extreme Transfer Bot** is a premium and advanced Telegram cloning bot designed to seamlessly mirror and transfer content between Telegram channels and groups. It features a powerful media bypass engine that downloads restricted files (from public or private channels with *Content Copy Protection / Restrict Saving Content* enabled) straight to the backend server and re-uploads them fresh to your destination, effortlessly bypassing Telegram copy limitations.

---

## ✨ Premium Features

*   **🛡️ Force Join System:** Automatically restricts access and presents users with a personalized verification screen displaying their Telegram avatar until they join your channel.
*   **🎯 Avatar Personalization Welcome:** Welcomes verified members with a beautiful embedded message featuring their own profile photo and dynamic inline control layout.
*   **🔒 Secure Dual Login (2FA Supported):** Robust login handler capable of connecting standard sessions as well as two-step verification (2FA) accounts smoothly without system crashes.
*   **⏩ One-Click Skip & Start:** Gives users the freedom to instantly execute a completely original mirror task without applying any modifications.
*   **⚙️ Advanced Customization Engine:**
    *   **📝 Filename Editing:** Instantly apply *Find & Replace* text rules to media file names during transfer.
    *   **💬 Caption Editing:** Effortlessly filter, replace, or strip unwanted advertisements and text from message captions.
    *   **➕ Extra Caption Strings:** Automatically append customized text, promotional links, or branding signatures at the bottom of every mirrored file.
*   **📊 Live Progress Window:** Tracks progress in real-time with an active live chat layout dashboard updating after every successful file copy.
*   **🐳 Dockerized Deployment:** Optimized with a stable Debian Bookworm base and pre-packaged with FFMPEG for cross-platform VPS or cloud deployments (Render, Railway, etc.).

---

## 📂 Project Architecture

```text
ExtremeTransferBot/
│
├── main.py             # Active web ping listener + Core initialization handler
├── config.py           # Environment variables configuration & secure credentials loading
├── Dockerfile          # Debian Bookworm base deployment blueprint with FFMPEG support
├── requirements.txt    # Frozen Python library dependencies
├── .env                # Local environmental variables configuration (Hidden/Ignored)
└── modules/
    ├── __init__.py     # Empty Python package initializer 
    └── auth.py         # All-in-One master script containing login, force join, and copy engines
