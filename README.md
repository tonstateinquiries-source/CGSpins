# CGSPINS Telegram Bot

A Telegram bot built with aiogram, MongoDB, and TON Connect for managing spin mechanics and NFT interactions.

## Setup

### Prerequisites
- Python 3.13+
- MongoDB Atlas account (or local MongoDB)
- Telegram Bot Token from @BotFather
- TON Wallet address

### Installation

1. **Clone the repository and navigate to the project directory:**
   ```bash
   cd CGSPINS
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Get your Telegram Bot Token:**
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Copy the token

2. **Set up MongoDB:**
   - Create a MongoDB Atlas account or use local MongoDB
   - Get your connection string

3. **Configure the bot:**
   - Edit `main.py`
   - Replace the placeholder values:
     - `BOT_TOKEN = "YOUR_BOT_TOKEN"` → Your actual bot token
     - `MONGODB_URI = "YOUR_MONGODB_URI"` → Your MongoDB connection string
     - `TON_WALLET = "YOUR_TON_WALLET"` → Your TON wallet address

### Running the Bot

```bash
source venv/bin/activate
python main.py
```

## Project Structure

- `main.py` - Main bot file with imports and setup
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Dependencies

- **aiogram 3.22.0** - Telegram Bot API framework
- **pymongo 4.8.0** - MongoDB driver
- **tonconnect 0.2.1** - TON Connect integration

## Features (To be implemented)

- Spin mechanics with cooldowns
- Leaderboard system
- NFT management
- TON wallet integration
- User management with MongoDB

## Notes

- The bot uses aiogram 3.x which has a different API structure than 2.x
- MongoDB connection is established only when valid URI is provided
- TON Connect integration is initialized only when valid wallet address is provided
- All placeholder values are safely handled to prevent initialization errors 