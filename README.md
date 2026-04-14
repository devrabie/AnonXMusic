# Anony Music Bot

A powerful Telegram Music Bot designed for groups and channels.

## Features
- High-quality audio/video streaming.
- Support for Telegram media links.
- Persistent playlist and queue management.
- Multi-language support.
- Dashboard for private control (especially useful for channels).

## Installation

### Traditional Deployment
1. **Install Dependencies:**
   - Python 3.10 or higher.
   - [FFmpeg](https://ffmpeg.org/download.html).
   - [Deno](https://deno.land/#installation) (Required for some core components).
2. **Clone the repository:**
   ```bash
   git clone https://github.com/YourUsername/AnonyMusic
   cd AnonyMusic
   ```
3. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment:**
   Copy `sample.env` to `.env` and fill in your credentials:
   ```bash
   cp sample.env .env
   ```
5. **Start the Bot:**
   ```bash
   bash start
   ```

### Docker Deployment (Recommended)
You can easily run the bot using Docker and Docker Compose.

1. **Install Docker and Docker Compose.**
2. **Configure Environment:**
   Ensure you have a `.env` file with the required variables (see `sample.env`).
3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

To stop the bot:
```bash
docker-compose down
```

## Environment Variables
- `API_ID`: Your Telegram API ID.
- `API_HASH`: Your Telegram API Hash.
- `BOT_TOKEN`: Your Telegram Bot Token.
- `LOGGER_ID`: ID of the group/channel for logs.
- `OWNER_ID`: Your Telegram User ID.
- `SESSION`: Pyrogram string session for the assistant account.
- `API_SERVER` (Optional): URL of a local Telegram Bot API server for 2GB file support.

## License
Distributed under the MIT License. See `LICENSE` for more information.
