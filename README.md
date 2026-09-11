# AURA FFX — Telegram Managed PHP Website

This project is based on the supplied AURA FFX HTML design/content and turns the main site into a dynamic PHP + SQLite site controlled by a Telegram admin bot.

## Features
- Dynamic logo URL
- Site name and description
- Primary / secondary / background colors
- Main download URL
- Version management
- Version enable/disable and password field
- Resource management
- Review Projects
- Social links
- Telegram user tracking
- Broadcast to bot users
- SQLite database
- One Render Docker service runs Apache/PHP and the Python Telegram bot together

## Render
1. Create a GitHub repository and upload this entire folder.
2. In Render choose **New > Blueprint** and select the repo, or create a Docker Web Service.
3. Add secrets:
   - `BOT_TOKEN` = your Telegram bot token
   - `ADMIN_IDS` = your Telegram numeric ID (comma-separated for multiple admins)
4. Deploy.
5. Open the Render URL. Send `/admin` to your bot.

## Important
The included default logo and social links are from the supplied `aura.html`. The site content can be changed from the Telegram admin panel.

Render free services have ephemeral storage. SQLite changes can be lost when the service is recreated/redeployed. For permanent production data, use a persistent disk/database later.
