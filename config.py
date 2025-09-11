import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TON_WALLET_ADDRESS = os.getenv("TON_WALLET_ADDRESS", "")

# Function to validate environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    print("🔍 [Config] Validating environment variables...")
    print(f"🔍 [Config] BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
    print(f"🔍 [Config] TON_WALLET_ADDRESS: {'SET' if TON_WALLET_ADDRESS else 'NOT SET'}")
    print(f"🔍 [Config] TON_API_KEY: {'SET' if os.getenv('TON_API_KEY') else 'NOT SET'}")
    print(f"🔍 [Config] ADMIN_USER_IDS: {os.getenv('ADMIN_USER_IDS', 'NOT SET')}")
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is not set!")
        print("Please set BOT_TOKEN in Railway environment variables")
        return False
    
    if not TON_WALLET_ADDRESS:
        print("❌ ERROR: TON_WALLET_ADDRESS environment variable is not set!")
        print("Please set TON_WALLET_ADDRESS in Railway environment variables")
        return False
    
    print("✅ Environment variables validated successfully")
    return True

# Admin Configuration
ADMIN_USER_IDS = [
    int(x) for x in os.getenv("ADMIN_USER_IDS", "8059922747").split(",")
]

# TON API Configuration
TON_API_URL = "https://tonapi.io/v2"
TON_API_KEY = os.getenv("TON_API_KEY", "")

# Alternative TON API (fallback)
TON_API_URL_ALT = "https://toncenter.com/api/v2"

# Game Configuration
HIT_POINTS = 10  # Points awarded for each 777 hit

# Payment Conversion Rates
STARS_TO_TON_RATE = 0.004836  # 1 Star = 0.004836 TON (100 Stars = 0.4836 TON)

PACKAGE_SPINS = {
    "bronze": 30,
    "silver": 60,
    "gold": 300,
    "black": 600
}

# Package Configuration
PACKAGES = {
    "bronze": {
        "name": "Bronze",
        "description": "Perfect for beginners!",
        "price_stars": 450,
        "price_ton": 2.0,
        "nano": 2000000000,   # 2 TON in nano (2.0 * 1e9)
        "spins": 30,
        "hits_required": 1,
        "nft_chance": 0.05  # 5% chance
    },
    "silver": {
        "name": "Silver", 
        "description": "Great value for regular players",
        "price_stars": 900,
        "price_ton": 4.0,
        "nano": 4000000000,   # 4 TON in nano (4.0 * 1e9)
        "spins": 60,
        "hits_required": 3,
        "nft_chance": 0.08  # 8% chance
    },
    "gold": {
        "name": "Gold",
        "description": "Premium package for serious players", 
        "price_stars": 5000,
        "price_ton": 24.0,
        "nano": 24000000000,   # 24 TON in nano (24.0 * 1e9)
        "spins": 300,
        "hits_required": 10,
        "nft_chance": 0.12  # 12% chance
    },
    "black": {
        "name": "Black",
        "description": "Elite package for high rollers",
        "price_stars": 10000,
        "price_ton": 49.0,
        "nano": 49000000000,   # 49 TON in nano (49.0 * 1e9)
        "spins": 600,
        "hits_required": 25,
        "nft_chance": 0.15  # 15% chance
    }
}

# Level System Configuration
LEVELS = {
    "Spinner": {"min_points": 0, "max_points": 19, "emoji": "🎰"},
    "Collector": {"min_points": 20, "max_points": 49, "emoji": "🎁"},
    "VIP": {"min_points": 50, "max_points": 99, "emoji": "👑"},
    "High-Roller": {"min_points": 100, "max_points": 999, "emoji": "💎"}
}

PACKAGE_POINTS = {
    "bronze": 5,
    "silver": 15,
    "gold": 50,
    "black": 100
}

# NFT Configuration
NFT_DROPS = {
    "Bronze": [
        "Bow Tie", "Bunny Muffin", "Candy Cane", "Crystal Ball", "Easter Egg",
        "Eternal Candle", "Evil Eye", "Ginger Cookie", "Hanging Star", "Hex Pot",
        "Jelly Bunny", "Jester Hat", "Jingle Bells", "Jolly Chimp", "Joyful Bundle",
        "Light Sword", "Love Candle", "Love Potion", "Lush Bouquet", "Pet Snake",
        "Restless Jar", "Sakura Flower", "Santa Hat", "Skull Flower", "Sleigh Bell",
        "Snoop Cigar", "Snoop Dogg", "Snow Globe", "Spiced Wine", "Spy Agaric",
        "Star Notepad", "Stellar Rocket", "Swag Bag", "Tama Gadget", "Top Hat",
        "Trapped Heart", "Valentine Box", "Winter Wreath"
    ],
    "Silver": [
        "Bonded Ring", "Diamond Ring", "Electric Skull", "Gem Signet", "Genie Lamp",
        "Kissed Frog", "Low Rider", "Magic Potion", "Neko Helmet", "Vintage Cigar",
        "Swiss Watch", "Sharp Tongue", "Signet Ring", "Toy Bear", "Westside Sign"
    ],
    "Gold": [
        "Heroic Helmet", "Precious Peach", "Durov's Cap"
    ],
    "Black": [
        "Heart Locket", "Plush Pepe"
    ]
}

# Welcome Message Configuration
WELCOME_MESSAGE = """👋 <b>Welcome to CG Spins!</b>

The only Telegram bot where every 🎰 spin can unlock exclusive NFT collectibles worth <b>$5 to $15K</b>. Join and win big – your first spin could change everything!

🕹️ <b>How It Works:</b>
<blockquote>➖ Send 🎰 to spin the slots.
➖ Land 777 for a hit. Collect hits in your chosen pack to claim NFTs.
➖ No apps – just spin directly in this chat!</blockquote>

⭐️ <b>Why CG Spins?</b>
Fair odds, instant action, and NFTs with real-world value – don't miss out!

🎰 <b>Start Winning Now!</b>"""

# Error Messages
ERROR_MESSAGES = {
    "user_not_found": "❌ User data not found!",
    "invalid_package": "❌ Invalid package selected!",
    "out_of_spins": "❌ Out of Spins!",
    "payment_failed": "❌ Payment failed!",
    "ton_api_error": "❌ TON API error occurred!"
}

# Success Messages
SUCCESS_MESSAGES = {
    "ton_payment": "✅ TON Payment Successful!",
    "stars_payment": "✅ Stars Payment Successful!",
    "package_activated": "Package Activated",
    "nft_earned": "🎉 NFT EARNED!"
}

# FAQ Content
FAQ_MESSAGE = """❓ <b>FREQUENTLY ASKED QUESTIONS</b>

🎰 <b>HOW TO PLAY</b>

<b>How do I start playing?</b>
Simply send 🎰 to this chat to spin the slots! You need to purchase a package first to get spins.

<b>What is a "777 hit"?</b>
A 777 hit occurs when the slot machine shows value 64 (the maximum). This is your winning combination!

<b>How do I get spins?</b>
Buy a package using 💰 Buy Spins button. Choose from <b>Bronze</b>, <b>Silver</b>, <b>Gold</b>, or <b>Black</b> packages.

🎁 <b>PACKAGES & PRICING</b>

<b>What packages are available?</b>
We have 4 packages:
🥉 <b>Bronze:</b> 30 spins, 1 hit needed for NFT
🥈 <b>Silver:</b> 60 spins, 3 hits needed for NFT  
🥇 <b>Gold:</b> 300 spins, 10 hits needed for NFT
⚫ <b>Black:</b> 600 spins, 25 hits needed for NFT

<b>How much do packages cost?</b>
🥉 <b>Bronze:</b> 450 Stars or 2 TON
🥈 <b>Silver:</b> 900 Stars or 4 TON
🥇 <b>Gold:</b> 5000 Stars or 24 TON
⚫ <b>Black:</b> 10000 Stars or 49 TON

<b>Can I pay with both Stars and TON?</b>
Yes! You can pay with Telegram Stars (in-app) or TON cryptocurrency (Tonkeeper wallet).

🏆 <b>NFT SYSTEM</b>

<b>How do I win NFTs?</b>
Collect the required number of 777 hits for your package:
🥉 <b>Bronze:</b> 1 hit = NFT
🥈 <b>Silver:</b> 3 hits = NFT
🥇 <b>Gold:</b> 10 hits = NFT
⚫ <b>Black:</b> 25 hits = NFT

<b>What NFTs can I win?</b>
Each package has exclusive NFTs:
🥉 <b>Bronze:</b> 38 NFTs (Bow Tie, Bunny Muffin, etc.) - up to $25
🥈 <b>Silver:</b> 15 NFTs (Bonded Ring, Diamond Ring, etc.) - $50-$200
🥇 <b>Gold:</b> 3 NFTs (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K
⚫ <b>Black:</b> 2 NFTs (Heart Locket, Plush Pepe) - up to $15K

<b>When do I get my NFT?</b>
NFTs are added to your profile within 15 minutes after winning.

<b>What happens after I win an NFT?</b>
Your package resets immediately - you can't continue spinning. Buy a new package to play again!

⭐ <b>POINTS & LEVELS</b>

<b>What are spin points?</b>
Points are earned by hitting 777. Each 777 hit gives you 10 points, plus bonus points from packages.

<b>What are the levels?</b>
🎰 <b>Spinner:</b> 0-19 points
🎁 <b>Collector:</b> 20-49 points  
👑 <b>VIP:</b> 50-99 points
💎 <b>High-Roller:</b> 100+ points

<b>Do levels give me any benefits?</b>
Your level determines the rarity of NFT models and backgrounds you receive! Each NFT has different models, backgrounds, and variations. Higher levels = rarer NFT appearances!

🎯 <b>REFERRAL PROGRAM</b>

<b>How does the referral system work?</b>
Share your referral link. When friends join and buy packages, you both get bonus points!

<b>What do I earn from referrals?</b>
You earn points based on your friend's package:
🥉 <b>Bronze:</b> +5 points
🥈 <b>Silver:</b> +10 points
🥇 <b>Gold:</b> +25 points
⚫ <b>Black:</b> +50 points

<b>What does my friend get?</b>
Your friend gets a welcome bonus of 2 points when they join through your link.

💡 <b>GAME RULES</b>

<b>Can I have multiple packages at once?</b>
No, you can only have one active package at a time.

<b>What happens if I run out of spins?</b>
You need to buy a new package to continue playing.

<b>Can I get a refund?</b>
All purchases are final. Make sure you understand the game before buying.

<b>Is the game fair?</b>
Yes! We use Telegram's built-in dice system (1-64 values) which is completely random and fair.

🔧 <b>TECHNICAL</b>

<b>Do I need to download anything?</b>
No! Everything works directly in Telegram - no apps needed.

<b>How do I contact support?</b>
Use the /start command to access the main menu and navigate to support options.

<b>What if I have technical issues?</b>
Try restarting the bot with /start. If problems persist, contact our support team.

🎉 <b>READY TO PLAY?</b>

Start your journey to NFT riches! Every spin could be your lucky one! 🍀"""
BOT_USERNAME = "CGSpinsBot"

# Admin Configuration (DEPRECATED - use ADMIN_USER_IDS instead)
ADMIN_IDS = [8059922747]  # Updated to match ADMIN_USER_IDS

# Payment Configuration  
TON_PAYMENT_EXPIRY = 3600  # 1 hour in seconds

# TON API Enhanced Configuration
TON_API_BASE = "https://tonapi.io"
TON_API_TIMEOUT = 30

# Influencer Configuration
INFLUENCERS = {
    # Tier 1: 15% commission
    1234567890: {"tier": 1, "commission_rate": 0.15, "name": "Influencer Name 1"},
    1234567891: {"tier": 1, "commission_rate": 0.15, "name": "Influencer Name 2"},
    
    # Tier 2: 25% commission  
    1234567892: {"tier": 2, "commission_rate": 0.25, "name": "Influencer Name 3"},
    1234567893: {"tier": 2, "commission_rate": 0.25, "name": "Influencer Name 4"},
    7911623970: {"tier": 2, "commission_rate": 0.25, "name": "Influencer 7911623970"},
}

# Influencer Commission Rates by Tier
INFLUENCER_COMMISSION_RATES = {
    1: 0.15,  # 15% commission
    2: 0.25,  # 25% commission
}
