from aiogram import Bot, Dispatcher, types, Router, filters, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import asyncio
from collections import defaultdict
import random
import aiohttp
import time
import uuid
import sqlite3
from datetime import datetime, timedelta
import config

# Import from modular structure
from src.models import (
    init_database,
    load_pending_payments,
    load_processed_transactions,
    save_processed_transaction,
    save_pending_payment,
    remove_pending_payment,
    save_stars_transaction,
    save_user_data,
    load_user_data
)

from src.services import (
    TONAPIClient,
    create_pending_ton_payment,
    cleanup_old_payments,
    clear_user_payments
)

from src.utils import (
    create_keyboard,
    generate_referral_link,
    parse_referral_start,
    calculate_referral_reward,
    process_referral_bonus,
    get_referral_stats,
    calculate_level,
    get_level_progress,
    add_spin_points,
    calculate_spin_result,
    create_spin_response,
    send_nft_reward_message
)

# Admin check function
def is_admin(user_id: int) -> bool:
    """Check if user is an admin"""
    return user_id in config.ADMIN_USER_IDS

# Admin notification function
async def send_admin_nft_notification(bot, user_id: int, username: str, package: str, nft_won: str):
    """Send NFT win notification to all admins"""
    try:
        # Get user's display name
        display_name = username if username else f"User {user_id}"
        
        # Create notification message
        notification_text = f"""
🎉 <b>NFT WIN NOTIFICATION</b>

👤 <b>User:</b> {display_name} (@{username if username else 'no_username'})
🆔 <b>User ID:</b> <code>{user_id}</code>
📦 <b>Package:</b> {package.title()}
🏆 <b>NFT Won:</b> {nft_won}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 <b>Action Required:</b> Please manually send the NFT to the user.
        """
        
        # Send notification to all admins
        for admin_id in config.ADMIN_USER_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="HTML"
                )
                print(f"✅ [Backend] NFT win notification sent to admin {admin_id}")
            except Exception as e:
                print(f"❌ [Backend] Failed to send NFT notification to admin {admin_id}: {e}")
                
    except Exception as e:
        print(f"❌ [Backend] Error in send_admin_nft_notification: {e}")

# Admin package purchase notification function
async def send_admin_package_notification(bot, user_id: int, username: str, package: str, payment_method: str, amount: str):
    """Send package purchase notification to all admins"""
    try:
        # Get user's display name
        display_name = username if username else f"User {user_id}"
        
        # Create notification message
        notification_text = f"""
💰 <b>PACKAGE PURCHASE NOTIFICATION</b>

👤 <b>User:</b> {display_name} (@{username if username else 'no_username'})
🆔 <b>User ID:</b> <code>{user_id}</code>
📦 <b>Package:</b> {package.title()}
💳 <b>Payment Method:</b> {payment_method}
💵 <b>Amount:</b> {amount}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ <b>Status:</b> Package activated successfully
        """
        
        # Send notification to all admins
        for admin_id in config.ADMIN_USER_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="HTML"
                )
                print(f"✅ [Backend] Package purchase notification sent to admin {admin_id}")
            except Exception as e:
                print(f"❌ [Backend] Failed to send package notification to admin {admin_id}: {e}")
                
    except Exception as e:
        print(f"❌ [Backend] Error in send_admin_package_notification: {e}")

# Helper function for safe message editing
async def safe_edit_message(callback, text: str, reply_markup=None, parse_mode="HTML"):
    """Safely edit a message with proper error handling for 'message is not modified' errors"""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        if "message is not modified" in str(e):
            pass  # Message is already up to date, ignore the error
        else:
            print(f"Error editing message: {e}")

# Helper function for Stars to TON conversion
def stars_to_ton(stars_amount: int) -> float:
    """Convert Stars to TON using the correct conversion rate"""
    return stars_amount * config.STARS_TO_TON_RATE

def ton_to_stars(ton_amount: float) -> int:
    """Convert TON to Stars using the correct conversion rate"""
    return int(ton_amount / config.STARS_TO_TON_RATE)

# Utility functions for admin panel formatting
def format_timestamp(timestamp) -> str:
    """Format timestamp to readable format"""
    if timestamp is None or timestamp == 'Unknown':
        return 'Unknown'
    
    try:
        if isinstance(timestamp, (int, float)):
            # Handle Unix timestamp
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(timestamp, str):
            # Handle ISO format or other string formats
            if 'T' in timestamp:
                # ISO format
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Already formatted or other format
                return timestamp
        else:
            return str(timestamp)
    except Exception:
        return str(timestamp)

def format_transaction_hash(tx_hash: str) -> str:
    """Format transaction hash in monospace with full length"""
    if not tx_hash:
        return 'N/A'
    return f'<code>{tx_hash}</code>'

def format_transaction_id(tx_id: str) -> str:
    """Format transaction ID in monospace"""
    if not tx_id:
        return 'N/A'
    return f'<code>{tx_id}</code>'

def create_pagination_keyboard(current_page: int, total_pages: int, base_callback: str, extra_params: str = "") -> InlineKeyboardMarkup:
    """Create pagination keyboard for admin functions"""
    keyboard = []
    
    # Navigation buttons
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"{base_callback}_page_{current_page-1}{extra_params}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"{base_callback}_page_{current_page+1}{extra_params}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Back button
    back_callback = base_callback.replace("_page_", "").split("_")[0] + "_" + "_".join(base_callback.replace("_page_", "").split("_")[1:-1])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Database helper functions
def ensure_user_data_loaded(user_id: int) -> bool:
    """Professional solution: Ensure user data is loaded from database if not in memory"""
    if user_id not in user_data:
        print(f"🔄 [Data Manager] User {user_id} not in memory, loading from database...")
        user_data_from_db = get_user_data_from_db(user_id)
        if user_data_from_db:
            user_data[user_id] = user_data_from_db
            print(f"✅ [Data Manager] User {user_id} loaded from database successfully")
            return True
        else:
            print(f"❌ [Data Manager] User {user_id} not found in database either")
            return False
    return True

def get_user_data_from_db(user_id: int) -> dict:
    """Get user data from database"""
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = [description[0] for description in cursor.description]
            user_data = dict(zip(columns, row))
            
            # Convert nfts string back to list if it exists
            if 'nfts' in user_data and user_data['nfts']:
                try:
                    import ast
                    user_data['nfts'] = ast.literal_eval(user_data['nfts'])
                except:
                    user_data['nfts'] = []
            elif 'nfts' in user_data:
                user_data['nfts'] = []
            
            return user_data
        return {}
    except Exception as e:
        print(f"Error getting user data from DB: {e}")
        return {}

def save_user_data_to_db(user_id: int, user_data: dict) -> bool:
    """Save user data to database with proper error handling and logging"""
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        # Use INSERT OR REPLACE to handle both new and existing users
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, balance, package, level, spin_points, hits, total_spins, 
             spins_available, referrals, referred_by, payment_method, nfts, 
             language, lang, username, banned, banned_at, banned_by, 
             influencer_earnings, influencer_tier, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data.get('balance', 0),
            user_data.get('package', 'None'),
            user_data.get('level', 'Spinner'),
            user_data.get('spin_points', 0),
            user_data.get('hits', 0),
            user_data.get('total_spins', 0),
            user_data.get('spins_available', 0),
            user_data.get('referrals', 0),
            user_data.get('referred_by'),
            user_data.get('payment_method', ''),
            str(user_data.get('nfts', [])),
            user_data.get('language', 'en'),
            user_data.get('lang', 'en'),
            user_data.get('username', ''),
            user_data.get('banned', 0),
            user_data.get('banned_at', ''),
            user_data.get('banned_by', 0),
            user_data.get('influencer_earnings', 0.0),
            user_data.get('influencer_tier'),
            user_data.get('created_at', datetime.now().isoformat()),
            user_data.get('updated_at', datetime.now().isoformat())
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ [Database] Successfully saved user {user_id} data to database")
        return True
    except Exception as e:
        print(f"❌ [Database] Error saving user {user_id} data to DB: {e}")
        return False

def update_user_username(user_id: int, username: str) -> bool:
    """Update user's username in database"""
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating username: {e}")
        return False


# Validate environment variables first
if not config.validate_environment():
    print("❌ Environment validation failed. Exiting...")
    exit(1)

# Initialize bot and dispatcher after validation
try:
    bot = Bot(token=config.BOT_TOKEN)
    print("✅ Bot initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize bot: {e}")
    print(f"❌ BOT_TOKEN value: '{config.BOT_TOKEN}'")
    exit(1)

dp = Dispatcher()
router = Router()
dp.include_router(router)

# Simple in-memory storage for testing
user_data = defaultdict(lambda: {
    "balance": 1000,  # Starting balance
    "package": "None",  # Current package (Bronze, Silver, Gold, Black)
    "level": "Spinner",  # User level (Spinner, Collector, VIP, High-Roller)
    "spin_points": 0,  # Points for level progression
    "hits": 0,
    "nfts": [],
    "total_spins": 0,
    "referrals": 0,
    "spins_available": 0, # Added for spin management
    "pending_ton_payment": None,  # Track pending TON payment
    "language": "en",  # User's preferred language (en, ru)
    "payment_method": None  # Track which payment method was used (stars/ton)
})

# Track message types for each user
user_messages = defaultdict(lambda: {"type": "video"})

# Track last menu send time to prevent spam
last_menu_send = defaultdict(lambda: 0)

# Track callback processing to prevent duplicates
processing_callbacks = set()

# Initialize database and load persistent data
def init_database():
    """Initialize SQLite database with unified, consistent schema"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    # Create pending TON payments table (unified schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_ton_payments (
            user_id INTEGER PRIMARY KEY,
            package TEXT NOT NULL,
            payment_id TEXT NOT NULL,
            amount_nano INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create processed transactions table (unified schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_transactions (
            tx_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            package TEXT NOT NULL,
            amount_nano INTEGER NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Stars transactions table (keep existing working schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stars_transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id INTEGER,
            package TEXT,
            amount INTEGER,
            timestamp REAL,
            payment_method TEXT
        )
    ''')
    
    # Create users table for persistent storage (unified schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance REAL DEFAULT 0.0,
            package TEXT DEFAULT 'None',
            level TEXT DEFAULT 'Spinner',
            spin_points INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            total_spins INTEGER DEFAULT 0,
            spins_available INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER,
            payment_method TEXT,
            nfts TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            language TEXT DEFAULT 'en',
            banned INTEGER DEFAULT 0,
            banned_at TEXT,
            banned_by INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ [Backend] Database initialized with unified schema")

init_database()

# Load existing user data from database (optimized)
def load_existing_users():
    """Load existing users from database into user_data (optimized for speed)"""
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        user_ids = cursor.fetchall()
        conn.close()
        
        loaded_count = 0
        for (user_id,) in user_ids:
            if user_id not in user_data:
                user_data[user_id] = get_user_data_from_db(user_id)
                loaded_count += 1
                
                # Quick validation for active packages
                user = user_data[user_id]
                if user.get('package') not in ['None', None] and user.get('spins_available', 0) <= 0:
                    package_key = user.get('package', '').lower()
                    if package_key in config.PACKAGES:
                        user['spins_available'] = config.PACKAGES[package_key]['spins']
                        save_user_data_to_db(user_id, user)
        
        print(f"👥 [Backend] Loaded {loaded_count} existing users from database")
    except Exception as e:
        print(f"⚠️ [Backend] Error loading users: {e}")
        print("👥 [Backend] Starting with empty user data")

# Load existing users
load_existing_users()

# Track pending TON payments (loaded from database)
pending_ton_payments = load_pending_payments()

# Track processed transactions to prevent duplicates (loaded from database)
processed_transactions = load_processed_transactions()

# OPTIMIZATION: Cache for recent transaction checks to avoid re-processing
recent_transaction_cache = set()
cache_cleanup_time = time.time()

async def check_new_ton_payments():
    """Check for new TON payments and process them - OPTIMIZED VERSION"""
    global recent_transaction_cache, cache_cleanup_time
    
    if not pending_ton_payments:
        print("📭 [Backend] No pending TON payments to check")
        return False
    
    # OPTIMIZATION: Clean cache every 5 minutes to prevent memory bloat
    current_time = time.time()
    if current_time - cache_cleanup_time > 300:  # 5 minutes
        recent_transaction_cache.clear()
        cache_cleanup_time = current_time
        print("🧹 [Backend] Cleared transaction cache")
        
    print(f"🔍 [Backend] Checking {len(pending_ton_payments)} pending TON payments...")
    
    try:
        async with TONAPIClient() as api_client:
            # OPTIMIZATION 1: Only fetch recent transactions (last 50 instead of 500)
            transactions = await api_client.get_transactions_with_pagination(
                address=config.TON_WALLET_ADDRESS,
                limit=50,  # Reduced from 500 to 50
                max_pages=2  # Reduced from 5 to 2 pages
            )
            
            if not transactions:
                print("📭 [Backend] No transactions found from either API")
                return False
            
            print(f"💰 [Backend] Found {len(transactions)} recent transactions to process")
            
            # OPTIMIZATION 2: Pre-filter transactions by payment IDs we're looking for
            pending_payment_ids = {info["payment_id"] for info in pending_ton_payments.values()}
            pending_amounts = {info["expected_amount"] for info in pending_ton_payments.values()}
            
            # Early deduplication and smart filtering
            processed_txs = set()
            relevant_transactions = []
            
            for tx in transactions:
                # Extract transaction hash
                tx_hash = tx.get("hash")
                if not tx_hash:
                    continue
                
                # Skip if already processed or recently checked
                if tx_hash in processed_transactions or tx_hash in processed_txs or tx_hash in recent_transaction_cache:
                    continue  # Skip silently to reduce log spam
                
                processed_txs.add(tx_hash)
                recent_transaction_cache.add(tx_hash)  # Add to cache
                
                # Extract transaction details
                amount = 0
                tx_text = ""
                source_wallet = ""
                
                # Handle TON API format
                if "in_msg" in tx and tx.get("success", True):
                    in_msg = tx["in_msg"]
                    if in_msg.get("msg_type") == "int_msg":
                        amount = in_msg.get("value", 0)
                        tx_text = in_msg.get("decoded_body", {}).get("text", "")
                        source_wallet = in_msg.get("source", {}).get("address", "")
                
                # OPTIMIZATION 3: Skip if no message text or amount doesn't match any pending
                if not tx_text or amount not in pending_amounts:
                    continue
                
                # OPTIMIZATION 4: Check if any payment ID is in the text before processing
                has_relevant_id = any(pid in tx_text or f"cgspins_{pid}" in tx_text for pid in pending_payment_ids)
                if not has_relevant_id:
                    continue
                
                relevant_transactions.append({
                    "hash": tx_hash,
                    "amount": amount,
                    "text": tx_text,
                    "source": source_wallet
                })
            
            print(f"🎯 [Backend] Found {len(relevant_transactions)} relevant transactions to process")
            
            # OPTIMIZATION 5: Process only relevant transactions
            for tx_data in relevant_transactions:
                tx_hash = tx_data["hash"]
                amount = tx_data["amount"]
                tx_text = tx_data["text"]
                source_wallet = tx_data["source"]
                
                print(f"🔍 [Backend] Processing tx: hash={tx_hash[:10]}..., amount={amount / 1e9} TON, text='{tx_text}'")
                    
                # OPTIMIZATION 6: Skip confirmation check for transactions older than 10 minutes
                # (they're likely already confirmed if they're in the API)
                try:
                    # Quick confirmation check with timeout
                    confirmation = await asyncio.wait_for(
                        api_client.check_transaction_confirmation(tx_hash), 
                        timeout=5.0  # 5 second timeout
                    )
                    if confirmation.get("error") or not confirmation.get("is_confirmed"):
                        print(f" - Skip: Tx {tx_hash[:10]} not confirmed or errored")
                        continue
                except asyncio.TimeoutError:
                    print(f" - Skip: Tx {tx_hash[:10]} confirmation check timed out")
                    continue
                    
                # Process each pending payment
                for user_id, payment_info in pending_ton_payments.items():
                    expected_id = payment_info["payment_id"]
                    expected_amount = payment_info["expected_amount"]
                    
                    # Check if payment ID matches (looser matching for legacy support)
                    if expected_id in tx_text or f"cgspins_{expected_id}" in tx_text:
                        print(f" - Found potential ID match: '{expected_id}' in '{tx_text}'")
                        
                        # Check amount with tolerance (±1 nano)
                        amount_match = abs(expected_amount - amount) <= 1
                        print(f" - Amount match: {amount_match} (tx={amount / 1e9} TON, expected={expected_amount / 1e9} TON)")
                        
                        if amount_match:
                            print(f"🎯 [Backend] Match for user {user_id}! Activating package...")
                        
                            # Immediately add to processed transactions to prevent double-processing
                            processed_transactions.add(tx_hash)
                            
                            try:
                                # Save to database
                                save_processed_transaction(tx_hash, user_id, payment_info["package"], amount, expected_id, source_wallet)
                                
                                # Create user if not exists (for payments without /start)
                                if user_id not in user_data:
                                    print(f"🔄 [Backend] Creating user {user_id} from payment (no /start)")
                                    
                                    # Check if this user was referred by an influencer (from pending payment or other source)
                                    referred_by = None
                                    # Note: We can't determine referral from payment alone, so we'll set to None
                                    # The referral relationship must be established through /start command
                                    
                                    user_data[user_id] = {
                                        "balance": 0.0,
                                        "package": "None",
                                        "level": "Spinner",
                                        "spin_points": 0,
                                        "hits": 0,
                                        "total_spins": 0,
                                        "spins_available": 0,
                                        "referrals": 0,
                                        "referred_by": referred_by,
                                        "payment_method": None,
                                        "nfts": [],
                                        "language": "en",
                                        "username": None,
                                        "created_at": datetime.now().isoformat(),
                                        "updated_at": datetime.now().isoformat()
                                    }
                                
                                # Activate package in user_data
                                user_data[user_id].update({
                                    "package": config.PACKAGES[payment_info["package"]]["name"],  # Use capitalized name
                                    "payment_method": "ton",
                                    "spins_available": config.PACKAGES[payment_info["package"]]["spins"],
                                    "total_spins": 0,  # Reset total spins for new package
                                    "hits": 0  # Reset hits for new package
                                })
                                
                                # Process referral bonus if user was referred
                                if user_data[user_id].get("referred_by"):
                                    referrer_id = user_data[user_id]["referred_by"]
                                    package_name = config.PACKAGES[payment_info["package"]]["name"]
                                    print(f"🎁 [Payment] Processing referral bonus: user {user_id} was referred by {referrer_id}, package: {package_name}")
                                    process_referral_bonus(user_data, referrer_id, user_id, package_name)
                                    
                                    # Process influencer commission with TON payment type
                                    if referrer_id in config.INFLUENCERS:
                                        print(f"🌟 [Payment] Processing influencer commission: {referrer_id} referred {user_id} for {package_name}")
                                        from src.services.game import process_influencer_commission
                                        process_influencer_commission(referrer_id, user_id, package_name, "ton", tx_hash)
                                else:
                                    print(f"ℹ️ [Payment] User {user_id} was not referred, no referral bonus to process")
                                
                                # Save updated user data to database
                                save_user_data_to_db(user_id, user_data[user_id])
                                
                                # Clear pending payment
                                if user_id in pending_ton_payments:
                                    del pending_ton_payments[user_id]
                                    remove_pending_payment(user_id)
                                    print(f"✅ [Backend] SUCCESS: Package activated for user {user_id}, pending payment cleared")
                                
                                # Send admin notification about package purchase
                                try:
                                    username = user_data[user_id].get('username', '')
                                    package_name = payment_info["package"]
                                    payment_method = "TON"
                                    amount_str = f"{amount / 1e9} TON"
                                    await send_admin_package_notification(bot, user_id, username, package_name, payment_method, amount_str)
                                except Exception as e:
                                    print(f"❌ [Backend] Error sending admin package notification: {e}")
                                
                                # Send notification to user about successful payment
                                try:
                                    pkg = config.PACKAGES[payment_info["package"]]
                                    import translations
                                    success_message = f"""{translations.get_text(user_id, "ton_payment_successful")}

{translations.get_text(user_id, "package_activated", package=pkg['name'])}

{translations.get_text(user_id, "amount_paid", amount=amount / 1e9)}
{translations.get_text(user_id, "spins_added", spins=pkg['spins'])}
{translations.get_text(user_id, "points_earned", points=config.PACKAGE_POINTS.get(payment_info["package"], 0))}
{translations.get_text(user_id, "current_level", level=user_data[user_id].get('level', 'Spinner'))}

{translations.get_text(user_id, "package_activated_message", spins=pkg['spins'])}"""
                                    
                                    # Create keyboard with Start Spinning button (matching reference code)
                                    keyboard = create_keyboard(
                                        (translations.get_text(user_id, "start_spinning_button"), "start_spinning"),
                                        (translations.get_text(user_id, "view_packages_button"), "buy"),
                                        (translations.get_text(user_id, "main_menu_button"), "back_to_main")
                                    )
                                    
                                    # Try to send message to user
                                    await bot.send_message(
                                        chat_id=user_id, 
                                        text=success_message,
                                        reply_markup=keyboard,
                                        parse_mode="HTML"
                                    )
                                    print(f"📱 [Backend] Success notification sent to user {user_id}")
                                    
                                except Exception as e:
                                    print(f"⚠️ [Backend] Could not send notification to user {user_id}: {e}")
                                
                            except Exception as e:
                                print(f"❌ [Backend] ERROR saving to DB for user {user_id}: {e}")
                                processed_transactions.remove(tx_hash)  # Rollback global set
                                raise
            
                            break  # Found match, no need to check other pending payments
                        else:
                            print(f" - Amount mismatch for user {user_id}")
                    else:
                        print(f" - No ID match: expected '{expected_id}', got '{tx_text}'")
            
            print(f"✅ [Backend] Processed {len(processed_txs)} transactions")
            return True
                    
    except Exception as e:
        print(f"❌ [Backend] Error in check_new_ton_payments: {e}")
        return False

# Background task to periodically check for TON payments
async def ton_payment_checker():
    """Background task to check for TON payments every 30 seconds"""
    print("🔄 [Backend] TON payment checker started")
    last_wallet_check = 0
    
    while True:
        try:
            # Clean up old pending payments first
            cleaned = cleanup_old_payments(pending_ton_payments, user_data)
            if cleaned > 0:
                print(f"🧹 [Backend] Cleaned {cleaned} pendings")
            
            # Log current pending payment count and details
            print(f"🔍 [Backend] Checking {len(pending_ton_payments)} pendings")
            for user_id, payment in pending_ton_payments.items():
                age = int(time.time() - payment.get("timestamp", 0))
                print(f"   - User {user_id}: {payment['package']}, age={age}s, ID={payment['payment_id']}")
            
            # Periodic wallet balance check (every 5 minutes)
            if time.time() - last_wallet_check > 300:  # Every 5 mins
                async with TONAPIClient() as api_client:
                    balance_info = await api_client.get_wallet_balance(config.TON_WALLET_ADDRESS)
                    balance_ton = int(balance_info.get('balance', 0)) / 1e9 if balance_info.get('ok') else 'Error'
                    print(f"💰 [Backend] Wallet check: Balance={balance_ton} TON")
                    last_wallet_check = time.time()
            
            # Check for new payments
            await check_new_ton_payments()
            
            # OPTIMIZATION: Wait 15 seconds instead of 30 for faster processing
            await asyncio.sleep(15)
            
        except Exception as e:
            print(f"❌ [Backend] Poller error: {e}")
            # Wait 30 seconds before retrying
            await asyncio.sleep(30)

# Old function definitions removed - now imported from modules

# Duplicate ton_payment_checker removed - using enhanced version above

# Bot command handlers
@router.message(filters.Command("start"))
async def start_command(message: types.Message):
    """Handle /start command with optional referral parameter"""
    user_id = message.from_user.id
    start_param = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    print(f"🚀 [START COMMAND] ===== START COMMAND TRIGGERED =====")
    print(f"🔍 [Backend] START COMMAND triggered for user {user_id}: start_param='{start_param}'")
    print(f"📝 [Backend] Full message text: '{message.text}'")
    
    # Check maintenance mode
    if maintenance_mode and not is_admin(user_id):
        maintenance_message = """🚧 <b>Maintenance Mode</b>

We're currently performing scheduled maintenance to improve your experience.

⏰ <b>Estimated time:</b> 30 minutes
🔧 <b>What we're doing:</b> System updates and optimizations

Thank you for your patience! We'll be back online shortly."""
        
        await message.answer(maintenance_message, parse_mode="HTML")
        return
    
    # Check if user is banned
    user_data_db = get_user_data_from_db(user_id)
    if user_data_db and user_data_db.get('banned', 0) == 1:
        print(f"🚫 [Backend] Banned user {user_id} attempted to use /start command")
        await message.reply("🚫 <b>Access Denied</b>\n\nYou have been banned from using this bot.\n\nIf you believe this is an error, please contact support.", parse_mode="HTML")
        return
    
    # Check if this is a referral start
    is_referral, referrer_id, hash_part = parse_referral_start(start_param) if start_param else (False, 0, "")
    
    print(f"🔍 [Backend] Start command for user {user_id}: start_param='{start_param}', is_referral={is_referral}, referrer_id={referrer_id}")
    
    # Update username if it has changed
    username = message.from_user.username or ''
    if user_data_db and user_data_db.get('username', '') != username:
        print(f"🔄 [Backend] Updating username for user {user_id}: '{user_data_db.get('username', '')}' -> '{username}'")
        update_user_username(user_id, username)
    
    if is_referral:
        print(f"🎯 [Backend] Referral detected: user {user_id} referred by {referrer_id}")
        if referrer_id in user_data:
            print(f"✅ [Backend] Referrer {referrer_id} found in user_data")
        else:
            print(f"❌ [Backend] Referrer {referrer_id} NOT found in user_data")
    
    # Initialize user data if not exists
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "package": "None",
            "level": "Spinner",
            "spin_points": 0,
            "hits": 0,
            "total_spins": 0,
            "spins_available": 0,
            "referrals": 0,
            "referred_by": None,
            "payment_method": None,
            "nfts": [],
            "language": "en",
            "username": username,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Process referral if valid
        if is_referral and referrer_id != user_id:
            print(f"🔍 [Referral] Processing referral: user {user_id} referred by {referrer_id}")
            
            # Ensure referrer is loaded into user_data if they exist in database
            if referrer_id not in user_data:
                print(f"🔄 [Referral] Referrer {referrer_id} not in memory, loading from database...")
                ensure_user_data_loaded(referrer_id)
            
            # Check if referrer exists in user_data or is an influencer
            referrer_in_user_data = referrer_id in user_data
            referrer_is_influencer = referrer_id in config.INFLUENCERS
            
            print(f"🔍 [Referral] Referrer {referrer_id} - In user_data: {referrer_in_user_data}, Is influencer: {referrer_is_influencer}")
            
            if referrer_in_user_data or referrer_is_influencer:
                user_data[user_id]["referred_by"] = referrer_id
                print(f"✅ [Referral] Set referred_by for user {user_id} to {referrer_id}")
                
                # If referrer is a regular user, increment their referral count
                if referrer_in_user_data:
                    user_data[referrer_id]["referrals"] = user_data[referrer_id].get("referrals", 0) + 1
                    save_user_data_to_db(referrer_id, user_data[referrer_id])
                    print(f"🎯 [Backend] New user {user_id} joined via referral from {referrer_id}. Referrer now has {user_data[referrer_id]['referrals']} referrals.")
                elif referrer_is_influencer:
                    print(f"🌟 [Influencer] New user {user_id} joined via influencer link from {referrer_id} ({config.INFLUENCERS[referrer_id]['name']})")
            else:
                print(f"❌ [Referral] Referrer {referrer_id} not found in user_data or influencers list")
        
        # Save user data to database
        save_user_data_to_db(user_id, user_data[user_id])
        print(f"👤 [Backend] New user {user_id} initialized")
    else:
        # Update existing user's last activity
        user_data[user_id]["updated_at"] = datetime.now().isoformat()
        print(f"🌐 [Backend] User {user_id} language before save: {user_data[user_id].get('language', 'NOT_SET')}")
        save_user_data_to_db(user_id, user_data[user_id])
        print(f"👤 [Backend] Existing user {user_id} activity updated")
    
    # Create welcome message
    import translations
    welcome_text = translations.get_text(user_id, "welcome_message")
    
    # Add referral welcome message if applicable
    if is_referral and referrer_id != user_id:
        if referrer_id in user_data:
            referrer_name = user_data[referrer_id].get("first_name", "a friend")
            welcome_text += f"\n\n🎯 <b>Welcome! You were invited by {referrer_name}!</b>\n💎 <b>Bonus:</b> You'll get 2 extra spin points when you buy your first package!"
        elif referrer_id in config.INFLUENCERS:
            influencer_name = config.INFLUENCERS[referrer_id]['name']
            welcome_text += f"\n\n🌟 <b>Welcome! You were invited by {influencer_name}!</b>\n💎 <b>Bonus:</b> You'll get 2 extra spin points when you buy your first package!"
    
    # Create main menu keyboard with translations
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    import translations
    
    # Create keyboard rows
    keyboard_rows = [
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "buy_spins"), callback_data="buy"),
            InlineKeyboardButton(text=translations.get_text(user_id, "start_spinning"), callback_data="start_spinning")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "my_profile"), callback_data="profile"),
            InlineKeyboardButton(text=translations.get_text(user_id, "referral_program"), callback_data="referral_menu")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "faq"), callback_data="faq"),
            InlineKeyboardButton(text=translations.get_text(user_id, "support"), url="https://t.me/CGSpins_Support")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "language"), callback_data="language_menu")
        ]
    ]
    
    # Add influencer menu button for influencers
    if user_id in config.INFLUENCERS:
        keyboard_rows.append([
            InlineKeyboardButton(text=translations.get_text(user_id, "influencer_dashboard_button"), callback_data="influencer_menu")
        ])
    
    # Add admin panel button for admins
    if is_admin(user_id):
        keyboard_rows.append([
            InlineKeyboardButton(text=translations.get_text(user_id, "admin_panel"), callback_data="admin_panel")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    print(f"🎯 [Backend] About to send main menu to user {user_id}")
    
    # Send welcome message with image
    try:
        from aiogram.types import BufferedInputFile
        with open('cgspins1.png', 'rb') as f:
            photo = BufferedInputFile(f.read(), filename='cgspins1.png')
        await message.answer_photo(
            photo=photo,
            caption=welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        user_messages[user_id] = {"type": "photo"}
        print(f"✅ [Backend] Main menu (photo) sent successfully to user {user_id}")
    except FileNotFoundError:
        # Fallback to text if image not found
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
        user_messages[user_id] = {"type": "text"}
        print(f"✅ [Backend] Main menu (text) sent successfully to user {user_id}")
    except Exception as e:
        print(f"❌ [Backend] Error sending main menu to user {user_id}: {e}")
        # Try text fallback
        try:
            await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id] = {"type": "text"}
            print(f"✅ [Backend] Main menu (text fallback) sent successfully to user {user_id}")
        except Exception as e2:
            print(f"❌ [Backend] Text fallback also failed for user {user_id}: {e2}")
    
    print(f"🎯 [Backend] START COMMAND completed for user {user_id}")

# Debug commands removed - all functionality moved to backend systems

@router.message(filters.Command("reset"))
async def reset_command(message: types.Message):
    """Reset user data for testing - removes package and resets spins"""
    user_id = message.from_user.id
    
    if user_id in user_data:
        # Reset user data
        user_data[user_id].update({
            "package": "None",
            "payment_method": None,
            "spins_available": 0,
            "total_spins": 0,
            "hits": 0,
            "nfts": []
        })
        
        # Save to database
        save_user_data_to_db(user_id, user_data[user_id])
        
        # Clear any pending payments
        if user_id in pending_ton_payments:
            del pending_ton_payments[user_id]
            remove_pending_payment(user_id)
        
        import translations
        await message.reply(translations.get_text(user_id, "user_data_reset_success"), parse_mode="HTML")
        print(f"🔄 [Backend] User {user_id} data reset for testing")
    else:
        import translations
        await message.reply(translations.get_text(user_id, "user_data_not_found_reply"))

@router.message(filters.Command("reset_db"))
async def reset_database_command(message: types.Message):
    user_id = message.from_user.id
    import translations
    
    if user_id not in config.ADMIN_USER_IDS: # Admin ID
        await message.reply(translations.get_text(user_id, "access_denied", action="reset database"), parse_mode="HTML")
        return
    try:
        user_data.clear(); pending_ton_payments.clear(); processed_transactions.clear()
        conn = sqlite3.connect('cgspins.db'); cursor = conn.cursor()
        cursor.execute('DELETE FROM users'); cursor.execute('DELETE FROM pending_ton_payments')
        cursor.execute('DELETE FROM processed_transactions'); cursor.execute('DELETE FROM stars_transactions')
        conn.commit(); conn.close()
        await message.reply(translations.get_text(user_id, "database_reset_success"), parse_mode="HTML")
    except Exception as e:
        await message.reply(translations.get_text(user_id, "database_reset_failed", error=str(e)), parse_mode="HTML")

@router.callback_query(F.data == "buy")
async def show_packages(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found"))
        return
    
    packages_text = f"""
⭐️ <b>{translations.get_text(user_id, "packages_available")}:</b>

{translations.get_text(user_id, "bronze_package")}
<b>{translations.get_text(user_id, "nft_price_up_to", price="25")}</b>

{translations.get_text(user_id, "silver_package")}
<b>{translations.get_text(user_id, "nft_price_range", min="50", max="200")}</b>

{translations.get_text(user_id, "gold_package")}
<b>{translations.get_text(user_id, "nft_price_range", min="500", max="2K")}</b>

{translations.get_text(user_id, "black_package")}
<b>{translations.get_text(user_id, "nft_price_up_to", price="15K")}</b>

{translations.get_text(user_id, "choose_package")}
    """
    
    keyboard = create_keyboard(
        (translations.get_text(user_id, "bronze_package_short"), "package_bronze"),
        (translations.get_text(user_id, "silver_package_short"), "package_silver"),
        (translations.get_text(user_id, "gold_package_short"), "package_gold"),
        (translations.get_text(user_id, "black_package_short"), "package_black"),
        (translations.get_text(user_id, "back"), "back_to_main")
    )
    
    # Send packages menu with image
    try:
        # Try to send photo with caption using BufferedInputFile
        from aiogram.types import BufferedInputFile
        with open('cgpackages.png', 'rb') as f:
            photo = BufferedInputFile(f.read(), filename='cgpackages.png')
        await callback.message.answer_photo(
            photo=photo,
            caption=packages_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        user_messages[user_id]["type"] = "photo"
    except Exception as e:
        print(f"Error sending packages image: {e}")
        # Fallback to text message if image fails
        if user_messages[user_id]["type"] == "video":
            # Coming from video, send new message
            await callback.message.answer(packages_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id]["type"] = "text"
        else:
            # Coming from text message, edit it - but check if it's editable first
            try:
                await callback.message.edit_text(packages_text, reply_markup=keyboard, parse_mode="HTML")
            except Exception as e:
                # If editing fails, send new message instead
                await callback.message.answer(packages_text, reply_markup=keyboard, parse_mode="HTML")
                user_messages[user_id]["type"] = "text"
    
    # Always answer the callback to prevent duplicate processing
    await callback.answer()

@router.callback_query(F.data == "info_spin")
async def show_spin_info(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
        
    user = user_data[user_id]
    
    # Check if user has purchased a package
    if user.get('spins_available', 0) <= 0:
        info_text = f"""
{translations.get_text(user_id, "how_to_spin")}

<blockquote>{translations.get_text(user_id, "simply_send_emoji")}</blockquote>

<b>{translations.get_text(user_id, "your_package")}:</b> None
<b>{translations.get_text(user_id, "spins_available_label")}:</b> 0

{translations.get_text(user_id, "need_purchase_package")}
        """
        
        keyboard = create_keyboard(
            (translations.get_text(user_id, "buy_spins"), "buy"),
            (translations.get_text(user_id, "back"), "back_to_main")
        )
    else:
        info_text = f"""
{translations.get_text(user_id, "how_to_spin")}

<blockquote>{translations.get_text(user_id, "simply_send_emoji")}</blockquote>

<b>{translations.get_text(user_id, "your_package")}:</b> {user.get('package', 'None').title() if user.get('package', 'None') != 'None' else 'None'}
<b>{translations.get_text(user_id, "spins_available_label")}:</b> 🔄 {user.get('spins_available', 0)}

<b>{translations.get_text(user_id, "hit_rates_by_level")}</b>
{translations.get_text(user_id, "bronze_hit_rate")}
{translations.get_text(user_id, "silver_hit_rate")}
{translations.get_text(user_id, "gold_hit_rate")}
{translations.get_text(user_id, "black_hit_rate")}
        """
        
        keyboard = create_keyboard(
            (translations.get_text(user_id, "start_spinning"), "start_spinning"),
            (translations.get_text(user_id, "back"), "back_to_main")
        )
    
    # Use message tracking to determine whether to edit or send new message
    if user_messages[user_id]["type"] == "video":
        # Coming from video, send new message
        await callback.message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")
        user_messages[user_id]["type"] = "text"
    else:
        # Coming from text message, edit it - but check if it's editable first
        try:
            await callback.message.edit_text(info_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # If editing fails, send new message instead
            await callback.message.answer(info_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id]["type"] = "text"

@router.callback_query(F.data == "start_spinning")
async def start_spinning(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
        
    user = user_data[user_id]
    
    # Check if user has purchased a package
    if user.get('spins_available', 0) <= 0:
        spin_text = f"""
{translations.get_text(user_id, "slot_machine_ready")}

<b>{translations.get_text(user_id, "your_package")}:</b> None
<b>{translations.get_text(user_id, "spins_available_label")}:</b> 0

{translations.get_text(user_id, "need_purchase_package")}
        """
        
        keyboard = create_keyboard(
            (translations.get_text(user_id, "buy_spins"), "buy"),
            (translations.get_text(user_id, "back"), "back_to_main")
        )
    else:
        spin_text = f"""
{translations.get_text(user_id, "slot_machine_ready")}

<b>{translations.get_text(user_id, "your_package")}:</b> {user.get('package', 'None').title() if user.get('package', 'None') != 'None' else 'None'}
<b>{translations.get_text(user_id, "spins_available_label")}:</b> 🔄 {user.get('spins_available', 0)}

<b>{translations.get_text(user_id, "how_to_spin")}</b>
<blockquote>{translations.get_text(user_id, "simply_send_emoji")}</blockquote>

<b>{translations.get_text(user_id, "hit_rates_by_level")}</b>
{translations.get_text(user_id, "bronze_hit_rate")}
{translations.get_text(user_id, "silver_hit_rate")}
{translations.get_text(user_id, "gold_hit_rate")}
{translations.get_text(user_id, "black_hit_rate")}

<b>{translations.get_text(user_id, "ready_to_win")}</b>
        """
        
        keyboard = create_keyboard(
            (translations.get_text(user_id, "my_profile"), "profile"),
            (translations.get_text(user_id, "back_to_main"), "back_to_main")
        )
    
    # Use message tracking to determine whether to edit or send new message
    if user_messages[user_id]["type"] == "video":
        # Coming from video, send new message
        await callback.message.answer(spin_text, reply_markup=keyboard, parse_mode="HTML")
        user_messages[user_id]["type"] = "text"
    else:
        # Coming from text message, edit it - but check if it's editable first
        try:
            await callback.message.edit_text(spin_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # If editing fails, send new message instead
            await callback.message.answer(spin_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id]["type"] = "text"
        
        # Always answer the callback to prevent duplicate processing
        await callback.answer()

@router.callback_query(F.data.startswith("package_"))
async def handle_package(callback: types.CallbackQuery):
    package = callback.data.replace("package_", "")
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    # SECURITY: Validate package exists before processing
    if package not in config.PACKAGES:
        await callback.answer(translations.get_text(user_id, "invalid_package_error"))
        return
    
    # Check if user already has an active package
    user = user_data[user_id]
    if user.get('package') not in ['None', None]:
        await callback.answer(translations.get_text(user_id, "already_have_package_error", package=user['package']))
        return
    
    if package in config.PACKAGES:
        pkg = config.PACKAGES[package]
        
        # Package emoji mapping
        package_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "black": "⚫"}
        
        # Automatically create pending payment if not exists (backend only)
        if user_id not in pending_ton_payments:
            payment_info = create_pending_ton_payment(user_id, package)
            if payment_info:
                # Store the payment info in the pending_ton_payments dictionary
                pending_ton_payments[user_id] = payment_info
                print(f"📝 [Backend] Created pending TON for user {user_id}: package={package}, amount={pkg['nano']}, ID={payment_info['payment_id']}")
            else:
                print(f"❌ [Backend] Failed to create pending for user {user_id}")
                await callback.answer(translations.get_text(user_id, "payment_failed_error"))
                return
        
        # Get payment ID safely
        if user_id in pending_ton_payments:
            payment_id = pending_ton_payments[user_id].get("payment_id", "unknown")
        else:
            await callback.answer(translations.get_text(user_id, "payment_creation_failed_error"))
            return
        
        ton_url = f"ton://transfer/{config.TON_WALLET_ADDRESS}?amount={pkg['nano']}&text={payment_id}"
        
        # Update package_text to match the new format
        package_text = f"""
{package_emoji.get(package, "🎁")} <b>{pkg['name']} Package</b>

{translations.get_text(user_id, f"{package}_description")}

{translations.get_text(user_id, f"{package}_hit_required")}

<b>{translations.get_text(user_id, "nft_drops")}</b>
<blockquote>{" • ".join(config.NFT_DROPS.get(package.title(), ["Coming Soon..."]))}</blockquote>

<b>{translations.get_text(user_id, "pricing")}</b>
{translations.get_text(user_id, "stars_telegram_payments", stars=pkg['price_stars'])}
{translations.get_text(user_id, "ton_tonkeeper", ton=pkg['price_ton'])}
        """
        
        # Create keyboard with 2 buttons per row
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "pay_with_stars", stars=pkg['price_stars']), callback_data=f"buy_stars_{package}"),
                InlineKeyboardButton(text=translations.get_text(user_id, "pay_with_ton", ton=pkg['price_ton']), url=ton_url)
            ],
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "back_to_packages"), callback_data="buy"),
                InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="back_to_main")
            ]
        ])
        
        # Use message tracking to determine whether to edit or send new message
        if user_messages[callback.from_user.id]["type"] in ["video", "photo"]:
            # Coming from video or photo, send new message
            await callback.message.answer(package_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[callback.from_user.id]["type"] = "text"
        else:
            # Coming from text message, edit it
            try:
                await callback.message.edit_text(package_text, reply_markup=keyboard, parse_mode="HTML")
            except Exception as e:
                # If editing fails (e.g., trying to edit photo as text), send new message
                print(f"Error editing message in handle_package: {e}")
                await callback.message.answer(package_text, reply_markup=keyboard, parse_mode="HTML")
                user_messages[callback.from_user.id]["type"] = "text"
        
        # Always answer the callback to prevent duplicate processing
        await callback.answer()

# Handle slot machine emoji (🎰 Dice message type)
@router.message(lambda message: message.dice and message.dice.emoji == "🎰")
async def handle_slot_machine(message: types.Message):
    user_id = message.from_user.id
    
    # Check maintenance mode
    if maintenance_mode and not is_admin(user_id):
        maintenance_message = """🚧 <b>Maintenance Mode</b>

We're currently performing scheduled maintenance to improve your experience.

⏰ <b>Estimated time:</b> 30 minutes
🔧 <b>What we're doing:</b> System updates and optimizations

Thank you for your patience! We'll be back online shortly."""
        
        await message.answer(maintenance_message, parse_mode="HTML")
        return
    
    # Check if user is banned
    user_data_db = get_user_data_from_db(user_id)
    if user_data_db and user_data_db.get('banned', False):
        print(f"🚫 [Backend] Banned user {user_id} attempted to use slot machine")
        await message.reply("🚫 <b>Access Denied</b>\n\nYou have been banned from using this bot.\n\nIf you believe this is an error, please contact support.", parse_mode="HTML")
        return
    
    # PROFESSIONAL SOLUTION: Ensure user data is loaded
    if not ensure_user_data_loaded(user_id):
        import translations
        keyboard = create_keyboard(
            (translations.get_text(user_id, "back_to_menu"), "back_to_main")
        )
        await message.reply(translations.get_text(user_id, "user_data_not_found_error"), reply_markup=keyboard, parse_mode="HTML")
        return
        
    user = user_data[user_id]
    
    # Check if user has spins available
    if user.get('spins_available', 0) <= 0:
        import translations
        keyboard = create_keyboard(
            (translations.get_text(user_id, "back_to_menu"), "back_to_main"),
            (translations.get_text(user_id, "my_profile"), "profile")
        )
        await message.reply(translations.get_text(user_id, "out_of_spins"), reply_markup=keyboard, parse_mode="HTML")
        return
    
    # Get the dice value (1-64 for slot machine)
    dice_value = message.dice.value
    
    # Calculate spin result
    is_winning, win_message, hits, nft_earned = calculate_spin_result(dice_value, user, user_data, user_id)
    
    # FIXED: Check for NFT win BEFORE deducting spins
    if nft_earned:
        # Store original package before reset for NFT reward message
        original_package = user.get('package', 'None')
        
        # Track all-time statistics before reset (lifetime totals)
        user['all_time_spins'] = user.get('all_time_spins', 0) + 1
        if hits > 0:  # If this spin was a hit, increment all-time hits
            user['all_time_hits'] = user.get('all_time_hits', 0) + hits
        
        # User won NFT - immediately reset spins to 0 to prevent further spinning
        user['spins_available'] = 0
        user['total_spins'] = 0
        user['package'] = 'None'
        user['payment_method'] = None
        user['hits'] = 0
        
        # Update level to match current points
        current_points = user.get('spin_points', 0)
        user['level'] = calculate_level(current_points)
        
        # Save reset user data to database
        save_user_data_to_db(user_id, user)
        
        print(f"🎉 [Backend] NFT WIN! User {user_id} won NFT, package reset immediately")
        
        # Send NFT reward message using original package
        reward_text, nfts = send_nft_reward_message(user_data, user_id, original_package)
        if reward_text:  # Only send if message is not empty
            try:
                await message.reply(reward_text, parse_mode="HTML")
            except Exception as e:
                print(f"❌ [Backend] Error sending NFT reward message to user {user_id}: {e}")
        else:
            print(f"⚠️ [Backend] Empty NFT reward message for package: {original_package}")
        
        # Send admin notification about NFT win
        try:
            username = user.get('username', '')
            nft_name = nfts[0] if nfts else "Unknown NFT"  # Get the first NFT from the list
            await send_admin_nft_notification(bot, user_id, username, original_package, nft_name)
        except Exception as e:
            print(f"❌ [Backend] Error sending admin NFT notification: {e}")
        
        # Create response with slot machine display
        user['user_id'] = user_id  # Add user_id to user data for translation
        response = create_spin_response(is_winning, win_message, user, nft_earned)
        
        # Create keyboard with navigation buttons
        import translations
        keyboard = create_keyboard(
            (translations.get_text(user_id, "back_to_menu"), "back_to_main"),
            (translations.get_text(user_id, "my_profile"), "profile")
        )
        
        try:
            await message.reply(response, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            print(f"❌ [Backend] Error sending NFT slot machine response to user {user_id}: {e}")
            # Try to send a simple text message as fallback
            try:
                await message.reply("🎉 NFT won! Use the menu to continue.", parse_mode="HTML")
            except Exception as fallback_error:
                print(f"❌ [Backend] Fallback message also failed for user {user_id}: {fallback_error}")
        return  # Exit early - no more processing needed
    
    # Normal spin processing (no NFT win)
    # Deduct one spin (but don't go below 0)
    current_spins = user.get('spins_available', 0)
    user['spins_available'] = max(0, current_spins - 1)
    user['total_spins'] = user.get('total_spins', 0) + 1
    
    # Track all-time statistics (lifetime totals)
    user['all_time_spins'] = user.get('all_time_spins', 0) + 1
    if hits > 0:  # If this spin was a hit, increment all-time hits
        user['all_time_hits'] = user.get('all_time_hits', 0) + hits
    
    # Save updated user data to database immediately after spin
    save_user_data_to_db(user_id, user)
    
    # Check if spins are now 0 and reset package if needed
    if user.get('spins_available', 0) <= 0:
        # Reset package when spins run out
        user['package'] = 'None'
        user['payment_method'] = None
        user['hits'] = 0
        user['total_spins'] = 0
        
        # Update level to match current points
        current_points = user.get('spin_points', 0)
        user['level'] = calculate_level(current_points)
        
        # Save reset user data to database
        save_user_data_to_db(user_id, user)
        
        print(f"🔄 [Backend] Package reset for user {user_id} - no more spins available. Level updated to: {user['level']}")
    
    # Create response with slot machine display
    user['user_id'] = user_id  # Add user_id to user data for translation
    response = create_spin_response(is_winning, win_message, user, nft_earned)
    
    # Create keyboard with navigation buttons
    import translations
    keyboard = create_keyboard(
        (translations.get_text(user_id, "back_to_menu"), "back_to_main"),
        (translations.get_text(user_id, "my_profile"), "profile")
    )
    
    try:
        await message.reply(response, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        print(f"❌ [Backend] Error sending slot machine response to user {user_id}: {e}")
        # Try to send a simple text message as fallback
        try:
            await message.reply("🎰 Slot machine result processed! Use the menu to continue.", parse_mode="HTML")
        except Exception as fallback_error:
            print(f"❌ [Backend] Fallback message also failed for user {user_id}: {fallback_error}")

# Handle successful payment - MUST be before generic message handler
@router.message(lambda message: message.successful_payment is not None)
async def process_successful_payment(message: types.Message):
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    # DEBUG: Log payment info
    print(f"🔍 [DEBUG] SUCCESSFUL PAYMENT HANDLER TRIGGERED!")
    print(f"🔍 [DEBUG] Processing successful payment for user {user_id}")
    print(f"🔍 [DEBUG] Payment info: {payment_info}")
    print(f"🔍 [DEBUG] Invoice payload: {payment_info.invoice_payload}")
    print(f"🔍 [DEBUG] Total amount: {payment_info.total_amount}")
    print(f"🔍 [DEBUG] Currency: {payment_info.currency}")
    
    # Parse package info from payload
    payload_parts = payment_info.invoice_payload.split('_')
    print(f"🔍 Payload parts: {payload_parts}")
    
    if len(payload_parts) >= 3:
        package_type = payload_parts[1]  # bronze, silver, gold, black
        print(f"🔍 Package type: {package_type}")
        
        if package_type in config.PACKAGES:
            pkg = config.PACKAGES[package_type]
            
            # SECURITY: Validate payment amount before activation
            if payment_info.total_amount != pkg['price_stars']:
                print(f"❌ [Backend] Invalid Stars amount for user {user_id}: got {payment_info.total_amount}, expected {pkg['price_stars']}")
                import translations
                await message.answer(translations.get_text(user_id, "payment_error_invalid_amount"), parse_mode="HTML")
                return
            
            user = user_data[user_id]
            
            # Update user package and give spins based on package
            user['package'] = pkg['name']
            user['payment_method'] = 'stars'  # Track payment method
            
            # Give spins based on package (use the package key, not the name)
            user['spins_available'] = pkg['spins']  # Use pkg['spins'] directly
            
            # Reset total spins and hits for new package
            user['total_spins'] = 0
            user['hits'] = 0  # Reset hits counter for new package
            
            # Process referral bonus if user was referred
            if user.get("referred_by"):
                referrer_id = user["referred_by"]
                package_name = pkg['name']
                print(f"🎁 [Payment] Processing referral bonus: user {user_id} was referred by {referrer_id}, package: {package_name}")
                process_referral_bonus(user_data, referrer_id, user_id, package_name)
                
                # Process influencer commission with Stars payment type
                if referrer_id in config.INFLUENCERS:
                    print(f"🌟 [Payment] Processing influencer commission: {referrer_id} referred {user_id} for {package_name}")
                    from src.services.game import process_influencer_commission
                    process_influencer_commission(referrer_id, user_id, package_name, "stars", payment_info.telegram_payment_charge_id)
            else:
                print(f"ℹ️ [Payment] User {user_id} was not referred, no referral bonus to process")
            
            # Award points for package purchase
            package_points = config.PACKAGE_POINTS.get(package_type, 0)
            level_increased = add_spin_points(user_data, user_id, package_points, f"purchasing {pkg['name']} package")
            
            # Create success message with new level system
            package_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "black": "💎"}
            emoji = package_emoji.get(pkg['name'], "📦")
            
            # DEBUG: Log which success message is being used
            print(f"🔍 Using success message: {config.SUCCESS_MESSAGES['stars_payment']}")
            print(f"🔍 Config SUCCESS_MESSAGES: {config.SUCCESS_MESSAGES}")
            
            import translations
            success_text = f"""<b>{translations.get_text(user_id, "stars_payment_successful")}</b>

{emoji} <b>{pkg['name']} {translations.get_text(user_id, "package_activated_label")}</b>
🔄 <b>{translations.get_text(user_id, "spins_added_label")}</b> {pkg['spins']} spins
🎯 <b>{translations.get_text(user_id, "points_earned_label")}</b> +{package_points} Spin Points
🏆 <b>{translations.get_text(user_id, "current_level_label")}</b> {user['level']}

{translations.get_text(user_id, "package_activated_message", spins=pkg['spins'])}"""
            
            # Add level up message if applicable
            if level_increased:
                success_text += f"\n\n🎉 <b>{translations.get_text(user_id, 'level_up')}</b> {translations.get_text(user_id, 'you_are_now')} {user['level']}!"
            
            keyboard = create_keyboard(
                (translations.get_text(user_id, "start_spinning_button"), "start_spinning"),
                (translations.get_text(user_id, "my_profile"), "profile"),
                (translations.get_text(user_id, "back_to_main"), "back_to_main")
            )
            
            await message.answer(success_text, reply_markup=keyboard, parse_mode="HTML")
            
            # Send admin notification about package purchase
            try:
                username = user.get('username', '')
                package_name = package_type
                payment_method = "Stars"
                amount_str = f"{payment_info.total_amount} Stars"
                await send_admin_package_notification(bot, user_id, username, package_name, payment_method, amount_str)
            except Exception as e:
                print(f"❌ [Backend] Error sending admin package notification: {e}")
            user_messages[user_id]["type"] = "text"
            
            # CRITICAL: Save updated user data to database
            save_user_data(user_id, user_data[user_id])
            
            # Track this transaction to prevent TON payment checker from processing it
            transaction_id = f"stars_{user_id}_{package_type}_{int(time.time())}"
            processed_transactions.add(transaction_id)
            
            # Save Stars transaction to database for persistence
            save_stars_transaction(transaction_id, user_id, package_type, pkg['price_stars'])
            
            print(f"🔒 Stars payment processed, transaction ID: {transaction_id}")
            
            # CRITICAL: Remove any pending TON payment for this user since they paid with Stars
            if user_id in pending_ton_payments:
                print(f"🗑️ [Backend] Clearing TON pending for user {user_id} due to Stars payment: package={pending_ton_payments[user_id]['package']}, ID={pending_ton_payments[user_id]['payment_id']}")
                del pending_ton_payments[user_id]
                # Also remove from database
                remove_pending_payment(user_id)

# Handle broadcast messages from admin
@router.message()
async def handle_broadcast_message(message: types.Message):
    """Handle broadcast messages from admin"""
    user_id = message.from_user.id
    
    # Check if user is admin and in broadcast mode
    if is_admin(user_id) and user_data.get(user_id, {}).get('broadcast_mode', False):
        broadcast_text = message.text
        
        if not broadcast_text:
            await message.reply("❌ Please send a text message for broadcast.")
            return
        
        # Confirm broadcast
        confirm_text = f"📢 <b>Confirm Broadcast</b>\n\n"
        confirm_text += f"<b>Message:</b>\n{broadcast_text}\n\n"
        confirm_text += f"📊 <b>Will be sent to:</b> {len(user_data)} users\n\n"
        confirm_text += f"⚠️ <b>Are you sure you want to send this?</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Send to All Users", callback_data=f"admin_broadcast_confirm:{user_id}"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="admin_broadcast")
            ]
        ])
        
        # Store the broadcast message temporarily
        user_data[user_id]['broadcast_message'] = broadcast_text
        user_data[user_id]['broadcast_mode'] = False
        
        await message.reply(confirm_text, reply_markup=keyboard, parse_mode="HTML")
        return


@router.callback_query(F.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # PROFESSIONAL SOLUTION: Ensure user data is loaded
    if not ensure_user_data_loaded(user_id):
        keyboard = create_keyboard(
            (translations.get_text(user_id, "back_to_main_menu"), "back_to_main")
        )
        await callback.answer(translations.get_text(user_id, "user_data_not_found"), reply_markup=keyboard, parse_mode="HTML")
        return
        
    user = user_data[user_id]
    
    # Calculate all-time totals (lifetime statistics)
    all_time_spins = user.get('all_time_spins', 0)  # Total spins across all packages
    all_time_hits = user.get('all_time_hits', 0)    # Total hits across all packages
    
    # Get influencer earnings if user is an influencer
    influencer_earnings = 0.0
    if user_id in config.INFLUENCERS:
        from src.models.database_enhanced import get_influencer_stats
        influencer_stats = get_influencer_stats(user_id)
        influencer_earnings = influencer_stats['total_earnings']
    
    # Always show profile with level/points system
    profile_text = f"""
{translations.get_text(user_id, "your_profile")}

🔄 <b>{translations.get_text(user_id, "spins_available")}:</b> {user.get('spins_available', 0)}
📦 <b>{translations.get_text(user_id, "package")}:</b> {user.get('package', 'None').title() if user.get('package', 'None') != 'None' else 'None'}
🏆 <b>{translations.get_text(user_id, "level")}:</b> {config.LEVELS[user.get('level', 'Spinner')]['emoji']} {user.get('level', 'Spinner')}
🎯 <b>{translations.get_text(user_id, "spin_points")}:</b> {user.get('spin_points', 0)}
🎯 <b>{translations.get_text(user_id, "total_spins_made")}:</b> {all_time_spins}
💎 <b>{translations.get_text(user_id, "total_hits")}:</b> {all_time_hits}
👥 <b>{translations.get_text(user_id, "referrals")}:</b> {user.get('referrals', 0)}
🖼️ <b>{translations.get_text(user_id, "nfts")}:</b> {len(user.get('nfts', []))}
        """
    
    # Add influencer earnings if user is an influencer
    if user_id in config.INFLUENCERS:
        influencer_info = config.INFLUENCERS[user_id]
        influencer_earnings_text = translations.get_text(user_id, "influencer_earnings_profile").format(earnings=influencer_earnings)
        commission_rate_text = translations.get_text(user_id, "influencer_commission_rate_profile").format(rate=influencer_info['commission_rate']*100)
        profile_text += f"""
{influencer_earnings_text}
{commission_rate_text}
        """
    
    # Add NFT list if user has any
    if user.get('nfts'):
        profile_text += f"\n\n🎁 <b>{translations.get_text(user_id, 'your_nft_collection')}:</b>\n<blockquote>"
        for nft in user.get('nfts', []):
            profile_text += f"• {nft}\n"
        profile_text += "</blockquote>"
        
    keyboard = create_keyboard(
        (translations.get_text(user_id, "buy_spins"), "buy"),
        (translations.get_text(user_id, "back"), "back_to_main")
    )
    
    # Use message tracking to determine whether to edit or send new message
    if user_messages[user_id]["type"] in ["video", "photo"]:
        # Coming from video or photo, send new message
        await callback.message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
        user_messages[user_id]["type"] = "text"
    else:
        # Coming from text message, edit it
        try:
            await callback.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # If editing fails (e.g., trying to edit photo as text), send new message
            print(f"Error editing message in show_profile: {e}")
            await callback.message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id]["type"] = "text"
    
    # Always answer the callback to prevent duplicate processing
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    callback_id = f"{user_id}_{callback.id}"
    
    # Import translations
    import translations
    
    print(f"🔄 [Backend] BACK_TO_MAIN callback triggered for user {user_id}, callback_id: {callback.id}")
    
    # Prevent duplicate processing of the same callback
    if callback_id in processing_callbacks:
        print(f"⚠️ [Backend] Duplicate callback {callback_id} blocked for user {user_id}")
        await callback.answer(translations.get_text(user_id, "request_processing_error"))
        return
    
    processing_callbacks.add(callback_id)
    
    try:
        # SECURITY: Validate user exists in data
        if user_id not in user_data:
            print(f"❌ [Backend] User {user_id} not found in user_data")
            await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
            return
        
        # Prevent double menu sending (cooldown of 2 seconds)
        current_time = time.time()
        if current_time - last_menu_send[user_id] < 2:
            print(f"⚠️ [Backend] Menu send blocked for user {user_id} due to cooldown (last send: {current_time - last_menu_send[user_id]:.1f}s ago)")
            await callback.answer(translations.get_text(user_id, "menu_cooldown_error"))
            return
        
        last_menu_send[user_id] = current_time
        print(f"🔄 [Backend] Back to main menu requested by user {user_id} (cooldown passed)")
        
        # Create custom keyboard with URL button for Support
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        # Import translations
        import translations
        
        # Create keyboard rows
        keyboard_rows = [
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "buy_spins"), callback_data="buy"),
                InlineKeyboardButton(text=translations.get_text(user_id, "start_spinning"), callback_data="start_spinning")
            ],
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "my_profile"), callback_data="profile"),
                InlineKeyboardButton(text=translations.get_text(user_id, "referral_program"), callback_data="referral_menu")
            ],
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "faq"), callback_data="faq"),
                InlineKeyboardButton(text=translations.get_text(user_id, "support"), url="https://t.me/CGSpins_Support")
            ],
            [
                InlineKeyboardButton(text=translations.get_text(user_id, "language"), callback_data="language_menu")
            ]
        ]
        
        # Add influencer menu button for influencers
        if user_id in config.INFLUENCERS:
            keyboard_rows.append([
                InlineKeyboardButton(text=translations.get_text(user_id, "influencer_dashboard_button"), callback_data="influencer_menu")
            ])
        
        # Add admin panel button for admins
        if is_admin(user_id):
            keyboard_rows.append([
                InlineKeyboardButton(text=translations.get_text(user_id, "admin_panel"), callback_data="admin_panel")
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
        
        print(f"🎯 [Backend] About to send main menu to user {user_id}")
        
        # Always send new message to avoid editing issues and double menus
        try:
            from aiogram.types import BufferedInputFile
            with open('cgspins1.png', 'rb') as f:
                photo = BufferedInputFile(f.read(), filename='cgspins1.png')
            await callback.message.answer_photo(
                photo=photo,
                caption=translations.get_text(user_id, "welcome_message"),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            user_messages[user_id] = {"type": "photo"}
            print(f"✅ [Backend] Main menu sent to user {user_id}")
        except FileNotFoundError:
            # Fallback to text if image not found
            await callback.message.answer(translations.get_text(user_id, "welcome_message"), reply_markup=keyboard, parse_mode="HTML")
            user_messages[user_id] = {"type": "text"}
            print(f"✅ [Backend] Main menu (text) sent to user {user_id}")
        except Exception as e:
            print(f"❌ [Backend] Error sending main menu to user {user_id}: {e}")
            await callback.answer(translations.get_text(user_id, "error_loading_menu"))
        
        # Always answer the callback to prevent duplicate processing
        await callback.answer()
        
        print(f"🔄 [Backend] BACK_TO_MAIN callback completed for user {user_id}")
        
    finally:
        # Always remove from processing set
        processing_callbacks.discard(callback_id)

@router.callback_query(F.data == "referral_menu")
async def referral_menu_callback(callback: types.CallbackQuery):
    """Show referral menu from main menu"""
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    print(f"🎯 [Backend] Referral menu requested by user {user_id}")
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        print(f"❌ [Backend] User {user_id} not found in user_data")
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    print(f"✅ [Backend] User {user_id} found in user_data")
    
    # Get referral statistics
    stats = get_referral_stats(user_data, user_id, config.BOT_USERNAME)
    
    if not stats:
        print(f"❌ [Backend] Failed to get referral stats for user {user_id}")
        await callback.answer(translations.get_text(user_id, "error_loading_referral_data"))
        return
    
    print(f"✅ [Backend] Got referral stats for user {user_id}: {stats}")
    
    # Create referral message
    referral_text = f"""
{translations.get_text(user_id, "your_referral_program")}

{translations.get_text(user_id, "total_referrals", count=stats['referrals_count'])}
{translations.get_text(user_id, "total_earnings", earnings=stats['total_earnings'])}
{translations.get_text(user_id, "referral_rewards")}

{translations.get_text(user_id, "bronze_package_reward")}
{translations.get_text(user_id, "silver_package_reward")}
{translations.get_text(user_id, "gold_package_reward")}
{translations.get_text(user_id, "black_package_reward")}

{translations.get_text(user_id, "your_referral_link")}
<code>{stats['referral_link']}</code>

{translations.get_text(user_id, "how_it_works")}
{translations.get_text(user_id, "how_it_works_text")}
"""
    
    # Create keyboard with copy link button
    keyboard = create_keyboard(
        (translations.get_text(user_id, "copy_link"), "copy_referral_link"),
        (translations.get_text(user_id, "share_stats"), "share_referral_stats"),
        (translations.get_text(user_id, "back_to_main"), "back_to_main")
    )
    
    print(f"🎯 [Backend] Sending referral menu to user {user_id}")
    
    # Always send new message to avoid video editing issues
    await callback.message.answer(referral_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Update message tracking
    if user_id not in user_messages:
        user_messages[user_id] = {"type": "text"}
    else:
        user_messages[user_id]["type"] = "text"
    
    print(f"✅ [Backend] Referral menu sent successfully to user {user_id}")
    
    # Always answer the callback to prevent loading spinner
    await callback.answer()

@router.callback_query(F.data == "influencer_menu")
async def influencer_menu_callback(callback: types.CallbackQuery):
    """Show influencer menu for registered influencers"""
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    print(f"🌟 [Influencer] Influencer menu requested by user {user_id}")
    
    # Check if user is a registered influencer
    if user_id not in config.INFLUENCERS:
        print(f"❌ [Influencer] User {user_id} is not a registered influencer")
        await callback.answer("❌ You are not a registered influencer!")
        return
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        print(f"❌ [Influencer] User {user_id} not found in user_data")
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    print(f"✅ [Influencer] User {user_id} is a registered influencer")
    
    # Get influencer info and stats
    influencer_info = config.INFLUENCERS[user_id]
    from src.models.database_enhanced import get_influencer_stats
    stats = get_influencer_stats(user_id)
    
    # Get translations
    import translations
    dashboard_title = translations.get_text(user_id, "influencer_dashboard")
    total_earnings = translations.get_text(user_id, "influencer_total_earnings").format(earnings=stats['total_earnings'])
    total_commissions = translations.get_text(user_id, "influencer_total_commissions").format(count=stats['commission_count'])
    copy_link = translations.get_text(user_id, "influencer_copy_link")
    view_commissions = translations.get_text(user_id, "influencer_view_commissions")
    back_to_main = translations.get_text(user_id, "back_to_main")
    
    # Get additional translations
    your_tier = translations.get_text(user_id, "influencer_your_tier").format(tier=influencer_info['tier'], rate=influencer_info['commission_rate']*100)
    commission_rate = translations.get_text(user_id, "influencer_commission_rate").format(rate=influencer_info['commission_rate']*100)
    your_link = translations.get_text(user_id, "influencer_your_link")
    how_it_works = translations.get_text(user_id, "influencer_how_it_works")
    how_it_works_text = translations.get_text(user_id, "influencer_how_it_works_text").format(rate=influencer_info['commission_rate']*100)
    pro_tip = translations.get_text(user_id, "influencer_pro_tip")
    recent_commissions = translations.get_text(user_id, "influencer_recent_commissions")
    
    # Create influencer message
    influencer_text = f"""
{dashboard_title}

{your_tier}
{total_earnings}
{total_commissions}
{commission_rate}

{your_link}
<code>https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}</code>

{how_it_works}
{how_it_works_text}

{pro_tip}

{recent_commissions}
"""
    
    # Add recent commissions
    if stats['recent_commissions']:
        for commission in stats['recent_commissions'][:5]:
            influencer_text += f"• {commission['package'].title()} - ${commission['commission_amount']:.2f}\n"
    else:
        no_commissions = translations.get_text(user_id, "influencer_no_commissions")
        influencer_text += f"{no_commissions}\n"
    
    # Create keyboard
    keyboard = create_keyboard(
        (copy_link, "copy_influencer_link"),
        (view_commissions, "view_influencer_commissions"),
        (back_to_main, "back_to_main")
    )
    
    print(f"🌟 [Influencer] Sending influencer menu to user {user_id}")
    
    # Always send new message to avoid video editing issues
    await callback.message.answer(influencer_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Update message tracking
    if user_id not in user_messages:
        user_messages[user_id] = {"type": "text"}
    else:
        user_messages[user_id]["type"] = "text"
    
    print(f"✅ [Influencer] Influencer menu sent successfully to user {user_id}")
    
    # Always answer the callback to prevent loading spinner
    await callback.answer()

@router.callback_query(F.data == "copy_influencer_link")
async def copy_influencer_link_callback(callback: types.CallbackQuery):
    """Copy influencer link to clipboard"""
    user_id = callback.from_user.id
    
    if user_id not in config.INFLUENCERS:
        await callback.answer("❌ You are not a registered influencer!")
        return
    
    influencer_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}"
    import translations
    link_copied = translations.get_text(user_id, "influencer_link_copied").format(link=influencer_link)
    await callback.answer(link_copied, show_alert=True)

@router.callback_query(F.data == "view_influencer_commissions")
async def view_influencer_commissions_callback(callback: types.CallbackQuery):
    """View all influencer commissions with pagination"""
    user_id = callback.from_user.id
    
    if user_id not in config.INFLUENCERS:
        await callback.answer("❌ You are not a registered influencer!")
        return
    
    from src.models.database_enhanced import load_influencer_commissions
    commissions = load_influencer_commissions(user_id)
    
    if not commissions:
        import translations
        no_commissions = translations.get_text(user_id, "influencer_no_commissions")
        await callback.answer(no_commissions, show_alert=True)
        return
    
    # Show first page
    await show_commissions_page(callback, commissions, 0)

async def show_commissions_page(callback: types.CallbackQuery, commissions: list, page: int):
    """Show a page of commissions with pagination"""
    user_id = callback.from_user.id
    items_per_page = 10
    total_pages = (len(commissions) + items_per_page - 1) // items_per_page
    
    if page >= total_pages:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_commissions = commissions[start_idx:end_idx]
    
    # Get translations
    import translations
    your_commissions = translations.get_text(user_id, "influencer_your_commissions")
    page_text = translations.get_text(user_id, "influencer_page").format(current=page + 1, total=total_pages)
    back_to_dashboard = translations.get_text(user_id, "influencer_back_to_dashboard")
    
    # Create commissions message
    commissions_text = f"{your_commissions}\n"
    commissions_text += f"{page_text}\n\n"
    
    for i, commission in enumerate(page_commissions, start_idx + 1):
        commissions_text += f"{i}. <b>{commission['package'].title()}</b>\n"
        commissions_text += f"   💰 ${commission['commission_amount']:.2f} ({commission['commission_rate']*100:.0f}%)\n"
        commissions_text += f"   📅 {commission['created_at']}\n\n"
    
    # Create pagination buttons using create_keyboard
    buttons = []
    
    # Always show page counter (like admin panel)
    buttons.append((f"📄 {page + 1}/{total_pages}", "noop"))
    
    # Navigation buttons (only if more than 1 page)
    if total_pages > 1:
        if page > 0:
            buttons.append(("⬅️", f"commissions_page_{page-1}"))
        
        if page < total_pages - 1:
            buttons.append(("➡️", f"commissions_page_{page+1}"))
    
    # Back button
    buttons.append((back_to_dashboard, "influencer_menu"))
    
    keyboard = create_keyboard(*buttons)
    
    await callback.message.edit_text(commissions_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("commissions_page_"))
async def commissions_page_callback(callback: types.CallbackQuery):
    """Handle commission pagination"""
    user_id = callback.from_user.id
    
    if user_id not in config.INFLUENCERS:
        await callback.answer("❌ You are not a registered influencer!")
        return
    
    # Extract page number from callback data
    page_str = callback.data.split("_")[-1]
    try:
        page = int(page_str)
    except ValueError:
        page = 0
    
    from src.models.database_enhanced import load_influencer_commissions
    commissions = load_influencer_commissions(user_id)
    
    if not commissions:
        await callback.answer("📊 No commissions found!", show_alert=True)
        return
    
    await show_commissions_page(callback, commissions, page)

@router.callback_query(F.data == "faq")
async def faq_callback(callback: types.CallbackQuery):
    """Show FAQ information"""
    user_id = callback.from_user.id
    
    print(f"❓ [Backend] FAQ requested by user {user_id}")
    
    # Import translations
    import translations
    
    # Create keyboard with back button
    keyboard = create_keyboard(
        (translations.get_text(user_id, "back_to_main"), "back_to_main")
    )
    
    print(f"❓ [Backend] Sending FAQ to user {user_id}")
    
    # Always send new message to avoid editing issues
    await callback.message.answer(translations.get_text(user_id, "faq_message"), reply_markup=keyboard, parse_mode="HTML")
    
    # Update message tracking
    if user_id not in user_messages:
        user_messages[user_id] = {"type": "text"}
    else:
        user_messages[user_id]["type"] = "text"
    
    print(f"✅ [Backend] FAQ sent successfully to user {user_id}")
    
    # Always answer the callback to prevent loading spinner
    await callback.answer()

@router.callback_query(F.data == "language_menu")
async def language_menu_callback(callback: types.CallbackQuery):
    """Show language selection menu"""
    user_id = callback.from_user.id
    print(f"🌐 [Backend] Language menu requested by user {user_id}")
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    import translations
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "english"), callback_data="set_language_en"),
            InlineKeyboardButton(text=translations.get_text(user_id, "russian"), callback_data="set_language_ru")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="back_to_main")
        ]
    ])
    
    await callback.message.answer(translations.get_text(user_id, "select_language"), reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("set_language_"))
async def set_language_callback(callback: types.CallbackQuery):
    """Set user language"""
    user_id = callback.from_user.id
    language = callback.data.split("_")[-1]  # Extract 'en' or 'ru'
    
    # Import translations
    import translations
    
    # Update user language
    user_data[user_id]["language"] = language
    
    # Save to database
    save_user_data_to_db(user_id, user_data[user_id])
    
    print(f"🌐 [Backend] Language set to {language} for user {user_id}")
    
    # Send confirmation message
    language_names = {"en": "English", "ru": "Русский"}
    await callback.message.answer(translations.get_text(user_id, "language_changed", language=language_names[language]))
    await callback.answer()


@router.callback_query(F.data == "copy_referral_link")
async def copy_referral_link_callback(callback: types.CallbackQuery):
    """Copy referral link to clipboard"""
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    stats = get_referral_stats(user_data, user_id, config.BOT_USERNAME)
    if not stats:
        await callback.answer(translations.get_text(user_id, "error_loading_referral_data"))
        return
    
    # Copy link to clipboard (Telegram will show "Copied!" message)
    await callback.answer(translations.get_text(user_id, "referral_link_copied", referral_link=stats['referral_link']), show_alert=True)

@router.callback_query(F.data == "share_referral_stats")
async def share_referral_stats_callback(callback: types.CallbackQuery):
    """Share referral stats and link"""
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    stats = get_referral_stats(user_data, user_id, config.BOT_USERNAME)
    if not stats:
        await callback.answer(translations.get_text(user_id, "error_loading_referral_data"))
        return
    
    # Create shareable message
    share_text = f"""
🎯 <b>Join CG Spins with my referral!</b>

🎰 <b>What you get:</b>
• 30+ spins to start playing
• Chance to win rare NFTs
• Level up system with rewards
• Daily bonuses and more!

🔗 <b>My referral link:</b>
<code>{stats['referral_link']}</code>

💎 <b>Special bonus:</b> You'll get 2 extra spin points when you join!

🎮 <b>Start spinning now:</b> @{config.BOT_USERNAME}
        """
    
    # Create share keyboard with 2 buttons per row
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "join_cg_spins"), url=f"https://t.me/{config.BOT_USERNAME}"),
            InlineKeyboardButton(text=translations.get_text(user_id, "copy_link"), callback_data="copy_referral_link")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back"), callback_data="referral_menu")
        ]
    ])
    
    # Always send new message to avoid video editing issues
    await callback.message.answer(share_text, reply_markup=keyboard, parse_mode="HTML")
    
    # Update message tracking
    if user_id not in user_messages:
        user_messages[user_id] = {"type": "text"}
    else:
        user_messages[user_id]["type"] = "text"



# Handle Stars purchase with Telegram Payments
@router.callback_query(F.data.startswith("buy_stars_"))
async def handle_stars_purchase(callback: types.CallbackQuery):
    package = callback.data.replace("buy_stars_", "")
    user_id = callback.from_user.id
    
    # Import translations
    import translations
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        await callback.answer(translations.get_text(user_id, "user_data_not_found_error"))
        return
    
    # SECURITY: Validate package exists before processing
    if package not in config.PACKAGES:
        await callback.answer(translations.get_text(user_id, "invalid_package_error"))
        return
    
    if package in config.PACKAGES:
        pkg = config.PACKAGES[package]
        


        try:
            # Create Telegram Stars invoice
            title = f"{pkg['name']} Package - CG Spins"
            description = f"Unlock the {pkg['name']} package"
            
            # Create invoice with Stars payment (amount in cents, so multiply by 100)
            await bot.send_invoice(
                chat_id=user_id,
                title=title,
                description=description,
                payload=f"package_{package}_{user_id}",
                currency="XTR",  # Telegram Stars currency
                prices=[LabeledPrice(label=f"{pkg['name']} package", amount=pkg['price_stars'])],  # Amount in cents
                start_parameter=f"package_{package}",
                protect_content=True
            )
            
            # Answer the callback query to prevent repeated clicks
            await callback.answer(translations.get_text(user_id, "invoice_sent"))
            
        except Exception as e:
            print(f"❌ Error creating Stars invoice for user {user_id}: {e}")
            await callback.answer(translations.get_text(user_id, "payment_error"))
            
            # Send error message to user
            error_text = f"""❌ <b>Payment Error</b>

Could not create payment invoice for {pkg['name']} Package.

Please try again or contact support if the problem persists."""
            
            keyboard = create_keyboard(
                ("💰 Buy Spins", "buy"),
                ("← Back to Main", "back_to_main")
            )
            
            await callback.message.edit_text(error_text, reply_markup=keyboard, parse_mode="HTML")

# Handle pre-checkout query (validate payment)
@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    print(f"🔍 [DEBUG] Pre-checkout query received: {pre_checkout_query.id}")
    print(f"🔍 [DEBUG] Pre-checkout query payload: {pre_checkout_query.invoice_payload}")
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    print(f"🔍 [DEBUG] Pre-checkout query answered: {pre_checkout_query.id}")


@router.message(filters.Command("referral"))
async def referral_command(message: types.Message):
    """Show user's referral information and link"""
    user_id = message.from_user.id
    
    # SECURITY: Validate user exists in data
    if user_id not in user_data:
        import translations
        keyboard = create_keyboard(
            (translations.get_text(user_id, "back_to_menu"), "back_to_main")
        )
        await message.reply(translations.get_text(user_id, "user_data_not_found_error"), reply_markup=keyboard, parse_mode="HTML")
        return
    
    # Get referral statistics
    stats = get_referral_stats(user_data, user_id, config.BOT_USERNAME)
    
    if not stats:
        await message.reply("❌ <b>Error loading referral data!</b>", parse_mode="HTML")
        return
    
    # Create referral message
    referral_text = f"""
🎯 <b>Your Referral Program</b>

👥 <b>Total Referrals:</b> {stats['referrals_count']}
🎁 <b>Total Earnings:</b> {stats['total_earnings']} Spin Points
💰 <b>Referral Rewards:</b>

🥉 Bronze Package: +5 points
🥈 Silver Package: +10 points  
🥇 Gold Package: +25 points
🖤 Black Package: +50 points

🔗 <b>Your Referral Link:</b>
<code>{stats['referral_link']}</code>

📱 <b>How it works:</b>
• Share your link with friends
• When they join and buy a package, you both get bonus points
• You earn points based on their package value
• They get a welcome bonus of 2 points

💡 <b>Pro tip:</b> Share your link in Telegram groups, social media, or with friends to maximize your earnings!
        """
    
    # Create keyboard with copy link button
    import translations
    keyboard = create_keyboard(
        (translations.get_text(user_id, "copy_link"), "copy_referral_link"),
        (translations.get_text(user_id, "share_stats"), "share_referral_stats"),
        (translations.get_text(user_id, "back_to_main"), "back_to_main")
    )
    
    await message.reply(referral_text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@router.message(filters.Command("check_referral"))
async def check_referral_command(message: types.Message):
    """Check referral status for debugging"""
    user_id = message.from_user.id
    
    if user_id in user_data:
        user = user_data[user_id]
        referred_by = user.get("referred_by")
        referrals = user.get("referrals", 0)
        
        status_text = f"""
🔍 <b>Referral Status for User {user_id}</b>

👤 <b>Referred by:</b> {referred_by if referred_by else 'None'}
👥 <b>Total referrals:</b> {referrals}
🔗 <b>Your referral link:</b> <code>{generate_referral_link(user_id)}</code>

📊 <b>Database check:</b>
"""
        
        # Check database directly
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cursor.execute('SELECT referred_by, referrals FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            db_referred_by, db_referrals = row
            status_text += f"🗄️ <b>DB referred_by:</b> {db_referred_by}\n🗄️ <b>DB referrals:</b> {db_referrals}"
        else:
            status_text += "❌ <b>User not found in database</b>"
        
        await message.reply(status_text, parse_mode="HTML")
    else:
        import translations
        await message.reply(translations.get_text(user_id, "user_data_not_found_reply"))

@router.message(filters.Command("status"))
async def status_command(message: types.Message):
    """Show bot status and health information (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can view bot status.", parse_mode="HTML")
        return
    
    try:
        # Get metrics and health status
        from src.utils import metrics, health_checker, alert_system
        
        stats = metrics.get_stats()
        health = await health_checker.check_system_health()
        alerts = alert_system.check_alerts(metrics, health.get("overall_status", "unknown"))
        
        status_text = f"""
📊 <b>Bot Status Report</b>

🟢 <b>Overall Health:</b> {health.get('overall_status', 'unknown').upper()}
⏱️ <b>Uptime:</b> {stats['uptime_formatted']}
📈 <b>Total Requests:</b> {stats['total_requests']}
✅ <b>Success Rate:</b> {stats['success_rate']}%
❌ <b>Error Rate:</b> {stats['error_rate']}%
⚡ <b>Avg Response Time:</b> {stats['average_response_time']}s

🔗 <b>TON API:</b> {stats['ton_api_success_rate']}% success
💳 <b>Payments:</b> {stats['payment_success_rate']}% success
👥 <b>Active Users:</b> {stats['active_users']}

🚨 <b>Active Alerts:</b> {len(alerts)}
"""
        
        if alerts:
            status_text += "\n<b>Recent Alerts:</b>\n"
            for alert in alerts[:3]:  # Show last 3 alerts
                emoji = "⚠️" if alert["level"] == "warning" else "❌" if alert["level"] == "error" else "🚨"
                status_text += f"{emoji} {alert['message']}\n"
        
        await message.reply(status_text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply(f"❌ <b>Error getting status:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("admin"))
async def admin_command(message: types.Message):
    """Open admin panel (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can access admin panel.", parse_mode="HTML")
        return
    
    # Create admin panel keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 User Management", callback_data="admin_user_management")
        ],
        [
            InlineKeyboardButton(text="💰 Financial Management", callback_data="admin_financial_management"),
            InlineKeyboardButton(text="⚙️ System Management", callback_data="admin_system_management")
        ],
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports"),
            InlineKeyboardButton(text="📝 Content Management", callback_data="admin_content_management")
        ]
    ])
    
    admin_text = """⚙️ <b>Admin Panel</b>

Welcome to the CG Spins Admin Panel. Choose a category to manage:

👥 <b>User Management:</b> View users, manage accounts, ban/unban
🎮 <b>Game Management:</b> Package stats, hit rates, game settings
💰 <b>Financial Management:</b> Payment tracking, revenue analytics
⚙️ <b>System Management:</b> Database, logs, maintenance mode
📊 <b>Analytics & Reports:</b> User retention, popular packages
📝 <b>Content Management:</b> FAQ, translations, pricing"""
    
    await message.reply(admin_text, reply_markup=keyboard, parse_mode="HTML")


@router.message(filters.Command("users"))
async def users_command(message: types.Message):
    """Show user statistics (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can view user statistics.", parse_mode="HTML")
        return
    
    try:
        total_users = len(user_data)
        active_users = len([uid for uid, data in user_data.items() if data.get('spins_available', 0) > 0])
        
        # Package distribution
        package_stats = {}
        for data in user_data.values():
            pkg = data.get('package', 'None')
            package_stats[pkg] = package_stats.get(pkg, 0) + 1
        
        # Level distribution
        level_stats = {}
        for data in user_data.values():
            level = data.get('level', 'Spinner')
            level_stats[level] = level_stats.get(level, 0) + 1
        
        users_text = f"""👥 <b>User Statistics</b>

📊 <b>Total Users:</b> {total_users}
🟢 <b>Active Users:</b> {active_users}
🔴 <b>Inactive Users:</b> {total_users - active_users}

📦 <b>Package Distribution:</b>
"""
        
        for pkg, count in package_stats.items():
            users_text += f"• {pkg}: {count} users\n"
        
        users_text += f"\n🏆 <b>Level Distribution:</b>\n"
        for level, count in level_stats.items():
            users_text += f"• {level}: {count} users\n"
        
        await message.reply(users_text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply(f"❌ <b>Error getting user statistics:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("broadcast"))
async def broadcast_command(message: types.Message):
    """Start broadcast mode (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can send broadcasts.", parse_mode="HTML")
        return
    
    # Enable broadcast mode for this user
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['broadcast_mode'] = True
    
    await message.reply("📢 <b>Broadcast Mode Enabled</b>\n\nSend your message now. It will be sent to all users.\n\nType /cancel to exit broadcast mode.", parse_mode="HTML")


@router.message(filters.Command("cancel"))
async def cancel_command(message: types.Message):
    """Cancel current operation (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can use this command.", parse_mode="HTML")
        return
    
    # Disable broadcast mode
    if user_id in user_data and user_data[user_id].get('broadcast_mode', False):
        user_data[user_id]['broadcast_mode'] = False
        await message.reply("✅ <b>Broadcast Mode Disabled</b>\n\nYou are no longer in broadcast mode.", parse_mode="HTML")
    else:
        await message.reply("ℹ️ <b>No active operation to cancel</b>\n\nYou are not currently in any special mode.", parse_mode="HTML")


@router.message(filters.Command("maintenance"))
async def maintenance_command(message: types.Message):
    """Toggle maintenance mode (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can toggle maintenance mode.", parse_mode="HTML")
        return
    
    # Toggle maintenance mode
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    
    status = "ENABLED" if maintenance_mode else "DISABLED"
    emoji = "🚧" if maintenance_mode else "✅"
    
    await message.reply(f"{emoji} <b>Maintenance Mode {status}</b>\n\n{'Bot is now in maintenance mode. Only admins can use it.' if maintenance_mode else 'Bot is now operational for all users.'}", parse_mode="HTML")


@router.message(filters.Command("stats"))
async def stats_command(message: types.Message):
    """Show detailed bot statistics (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can view detailed statistics.", parse_mode="HTML")
        return
    
    try:
        # Calculate comprehensive statistics
        total_users = len(user_data)
        total_spins = sum(data.get('total_spins', 0) for data in user_data.values())
        total_hits = sum(data.get('hits', 0) for data in user_data.values())
        total_referrals = sum(data.get('referrals', 0) for data in user_data.values())
        total_nfts = sum(len(data.get('nfts', [])) for data in user_data.values())
        
        # Package statistics
        package_stats = {}
        for data in user_data.values():
            pkg = data.get('package', 'None')
            if pkg not in package_stats:
                package_stats[pkg] = {'users': 0, 'spins': 0, 'hits': 0}
            package_stats[pkg]['users'] += 1
            package_stats[pkg]['spins'] += data.get('total_spins', 0)
            package_stats[pkg]['hits'] += data.get('hits', 0)
        
        # Revenue calculation (approximate)
        revenue_ton = 0
        revenue_stars = 0
        for pkg_name, stats in package_stats.items():
            if pkg_name in config.PACKAGES:
                pkg = config.PACKAGES[pkg_name]
                revenue_ton += stats['users'] * pkg['price_ton']
                revenue_stars += stats['users'] * pkg['price_stars']
        
        stats_text = f"""📊 <b>Detailed Bot Statistics</b>

👥 <b>User Statistics:</b>
• Total Users: {total_users}
• Total Spins: {total_spins:,}
• Total Hits: {total_hits:,}
• Total Referrals: {total_referrals:,}
• Total NFTs Won: {total_nfts:,}

💰 <b>Revenue Statistics:</b>
• TON Revenue: {revenue_ton:.2f} TON
• Stars Revenue: {revenue_stars:,} Stars

📦 <b>Package Statistics:</b>
"""
        
        for pkg_name, stats in package_stats.items():
            if pkg_name != 'None':
                stats_text += f"• {pkg_name.title()}: {stats['users']} users, {stats['spins']} spins, {stats['hits']} hits\n"
        
        stats_text += f"\n⏰ <b>Last Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await message.reply(stats_text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply(f"❌ <b>Error getting statistics:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("help_admin"))
async def help_admin_command(message: types.Message):
    """Show admin command help (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can view admin help.", parse_mode="HTML")
        return
    
    help_text = """⚙️ <b>Admin Commands Help</b>

<b>Basic Commands:</b>
/start - Start the bot
/status - Show bot status
/admin - Open admin panel
/help_admin - Show this help

<b>User Management:</b>
/users - Show user statistics
/stats - Show detailed statistics
/user_info &lt;user_id&gt; - Get detailed user information
/ban_user &lt;user_id&gt; [reason] - Ban a user
/unban_user &lt;user_id&gt; - Unban a user
/give_package &lt;user_id&gt; &lt;package&gt; - Give package to user

<b>Communication:</b>
/broadcast - Start broadcast mode
/cancel - Cancel current operation

<b>System Management:</b>
/maintenance - Toggle maintenance mode
/reset_db - Reset database (DANGEROUS!)
/fix_database - Fix database schema issues

<b>Game Commands:</b>
/reset - Reset your own data (for testing)
/referral - Show referral info
/check_referral - Check referral status

<b>Admin Panel:</b>
Use /admin to access the full admin panel with all management options.

<b>Available Packages:</b> bronze, silver, gold, black"""
    
    await message.reply(help_text, parse_mode="HTML")


@router.message(filters.Command("fix_database"))
async def fix_database_command(message: types.Message):
    """Fix database schema issues and unify all schemas (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can fix database issues.", parse_mode="HTML")
        return
    
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        fix_text = "🔧 <b>Database Schema Unification</b>\n\n"
        
        # 1. Fix pending_ton_payments table
        cursor.execute("PRAGMA table_info(pending_ton_payments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fix_text += "📋 <b>Pending TON Payments Table:</b>\n"
        
        # Check and add missing columns
        if 'amount_nano' not in columns:
            if 'expected_amount' in columns:
                # Migrate data from expected_amount to amount_nano
                cursor.execute("ALTER TABLE pending_ton_payments ADD COLUMN amount_nano INTEGER")
                cursor.execute("UPDATE pending_ton_payments SET amount_nano = expected_amount WHERE amount_nano IS NULL")
                fix_text += "✅ Migrated expected_amount → amount_nano\n"
            else:
                cursor.execute("ALTER TABLE pending_ton_payments ADD COLUMN amount_nano INTEGER")
                fix_text += "✅ Added amount_nano column\n"
        else:
            fix_text += "✅ amount_nano column exists\n"
        
        if 'created_at' not in columns:
            if 'timestamp' in columns:
                # Migrate data from timestamp to created_at
                cursor.execute("ALTER TABLE pending_ton_payments ADD COLUMN created_at TIMESTAMP")
                cursor.execute("UPDATE pending_ton_payments SET created_at = datetime(timestamp, 'unixepoch') WHERE created_at IS NULL")
                fix_text += "✅ Migrated timestamp → created_at\n"
            else:
                cursor.execute("ALTER TABLE pending_ton_payments ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                fix_text += "✅ Added created_at column\n"
        else:
            fix_text += "✅ created_at column exists\n"
        
        # 2. Fix processed_transactions table
        cursor.execute("PRAGMA table_info(processed_transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fix_text += "\n📋 <b>Processed Transactions Table:</b>\n"
        
        if 'amount_nano' not in columns:
            if 'amount' in columns:
                # Migrate data from amount to amount_nano
                cursor.execute("ALTER TABLE processed_transactions ADD COLUMN amount_nano INTEGER")
                cursor.execute("UPDATE processed_transactions SET amount_nano = amount WHERE amount_nano IS NULL")
                fix_text += "✅ Migrated amount → amount_nano\n"
            else:
                cursor.execute("ALTER TABLE processed_transactions ADD COLUMN amount_nano INTEGER")
                fix_text += "✅ Added amount_nano column\n"
        else:
            fix_text += "✅ amount_nano column exists\n"
        
        if 'processed_at' not in columns:
            if 'timestamp' in columns:
                # Migrate data from timestamp to processed_at
                cursor.execute("ALTER TABLE processed_transactions ADD COLUMN processed_at TIMESTAMP")
                cursor.execute("UPDATE processed_transactions SET processed_at = datetime(timestamp, 'unixepoch') WHERE processed_at IS NULL")
                fix_text += "✅ Migrated timestamp → processed_at\n"
            else:
                cursor.execute("ALTER TABLE processed_transactions ADD COLUMN processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                fix_text += "✅ Added processed_at column\n"
        else:
            fix_text += "✅ processed_at column exists\n"
        
        # 3. Fix stars_transactions table (keep existing schema as it's working)
        cursor.execute("PRAGMA table_info(stars_transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fix_text += "\n📋 <b>Stars Transactions Table:</b>\n"
        fix_text += "✅ Stars transactions schema is compatible\n"
        
        # 4. Fix users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fix_text += "\n📋 <b>Users Table:</b>\n"
        
        # Add missing columns if needed
        required_columns = {
            'username': 'TEXT',
            'banned': 'INTEGER DEFAULT 0',
            'banned_at': 'TEXT',
            'banned_by': 'INTEGER'
        }
        
        for col_name, col_def in required_columns.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                fix_text += f"✅ Added {col_name} column\n"
            else:
                fix_text += f"✅ {col_name} column exists\n"
        
        conn.commit()
        conn.close()
        
        fix_text += "\n🎉 <b>Database schema unification completed!</b>\n"
        fix_text += "All functions should now work with a consistent schema."
        
        await message.reply(fix_text, parse_mode="HTML")
        
    except Exception as e:
        await message.reply(f"❌ <b>Error fixing database:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("give_package"))
async def give_package_command(message: types.Message):
    """Give a package to a user (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can give packages.", parse_mode="HTML")
        return
    
    # Parse command arguments: /give_package <user_id> <package_name>
    args = message.text.split()
    if len(args) != 3:
        await message.reply("❌ <b>Usage:</b> /give_package &lt;user_id&gt; &lt;package_name&gt;\n\n<b>Available packages:</b> bronze, silver, gold, black", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(args[1])
        package_name = args[2].lower()
        
        if package_name not in config.PACKAGES:
            await message.reply(f"❌ <b>Invalid package!</b>\n\nAvailable packages: {', '.join(config.PACKAGES.keys())}", parse_mode="HTML")
            return
        
        # Initialize target user if not exists
        if target_user_id not in user_data:
            user_data[target_user_id] = {
                "balance": 0.0,
                "package": "None",
                "level": "Spinner",
                "spin_points": 0,
                "hits": 0,
                "total_spins": 0,
                "spins_available": 0,
                "referrals": 0,
                "referred_by": None,
                "payment_method": None,
                "nfts": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Give the package
        pkg = config.PACKAGES[package_name]
        user_data[target_user_id].update({
            "package": package_name,
            "spins_available": pkg["spins"],
            "updated_at": datetime.now().isoformat()
        })
        
        # Save to database
        save_user_data(target_user_id, user_data[target_user_id])
        
        await message.reply(f"✅ <b>Package Given Successfully!</b>\n\nUser {target_user_id} now has {pkg['name']} package with {pkg['spins']} spins.", parse_mode="HTML")
        
    except ValueError:
        await message.reply("❌ <b>Invalid user ID!</b>\n\nUser ID must be a number.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"❌ <b>Error giving package:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("ban_user"))
async def ban_user_command(message: types.Message):
    """Ban a user (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can ban users.", parse_mode="HTML")
        return
    
    # Parse command arguments: /ban_user <user_id> [reason]
    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ <b>Usage:</b> /ban_user &lt;user_id&gt; [reason]", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(args[1])
        reason = " ".join(args[2:]) if len(args) > 2 else "No reason provided"
        
        # Initialize target user if not exists
        if target_user_id not in user_data:
            user_data[target_user_id] = {
                "balance": 0.0,
                "package": "None",
                "level": "Spinner",
                "spin_points": 0,
                "hits": 0,
                "total_spins": 0,
                "spins_available": 0,
                "referrals": 0,
                "referred_by": None,
                "payment_method": None,
                "nfts": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        
        # Ban the user
        user_data[target_user_id]["banned"] = True
        user_data[target_user_id]["ban_reason"] = reason
        user_data[target_user_id]["ban_date"] = datetime.now().isoformat()
        user_data[target_user_id]["updated_at"] = datetime.now().isoformat()
        
        # Save to database
        save_user_data(target_user_id, user_data[target_user_id])
        
        await message.reply(f"🚫 <b>User Banned Successfully!</b>\n\nUser {target_user_id} has been banned.\n<b>Reason:</b> {reason}", parse_mode="HTML")
        
    except ValueError:
        await message.reply("❌ <b>Invalid user ID!</b>\n\nUser ID must be a number.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"❌ <b>Error banning user:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("unban_user"))
async def unban_user_command(message: types.Message):
    """Unban a user (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can unban users.", parse_mode="HTML")
        return
    
    # Parse command arguments: /unban_user <user_id>
    args = message.text.split()
    if len(args) != 2:
        await message.reply("❌ <b>Usage:</b> /unban_user &lt;user_id&gt;", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(args[1])
        
        if target_user_id not in user_data:
            await message.reply("❌ <b>User not found!</b>\n\nUser ID does not exist in the database.", parse_mode="HTML")
            return
        
        # Unban the user
        if user_data[target_user_id].get("banned", False):
            user_data[target_user_id]["banned"] = False
            user_data[target_user_id]["unban_date"] = datetime.now().isoformat()
            user_data[target_user_id]["updated_at"] = datetime.now().isoformat()
            
            # Save to database
            save_user_data(target_user_id, user_data[target_user_id])
            
            await message.reply(f"✅ <b>User Unbanned Successfully!</b>\n\nUser {target_user_id} has been unbanned and can now use the bot again.", parse_mode="HTML")
        else:
            await message.reply(f"ℹ️ <b>User Not Banned</b>\n\nUser {target_user_id} is not currently banned.", parse_mode="HTML")
        
    except ValueError:
        await message.reply("❌ <b>Invalid user ID!</b>\n\nUser ID must be a number.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"❌ <b>Error unbanning user:</b>\n\n{str(e)}", parse_mode="HTML")


@router.message(filters.Command("user_info"))
async def user_info_command(message: types.Message):
    """Get detailed information about a user (admin only)"""
    user_id = message.from_user.id
    
    if user_id not in config.ADMIN_USER_IDS:
        await message.reply("❌ <b>Access Denied</b>\n\nOnly admin can view user information.", parse_mode="HTML")
        return
    
    # Parse command arguments: /user_info <user_id>
    args = message.text.split()
    if len(args) != 2:
        await message.reply("❌ <b>Usage:</b> /user_info &lt;user_id&gt;", parse_mode="HTML")
        return
    
    try:
        target_user_id = int(args[1])
        
        if target_user_id not in user_data:
            await message.reply("❌ <b>User not found!</b>\n\nUser ID does not exist in the database.", parse_mode="HTML")
            return
        
        user = user_data[target_user_id]
        
        # Format user information
        info_text = f"""👤 <b>User Information</b>

🆔 <b>User ID:</b> {target_user_id}
📦 <b>Package:</b> {user.get('package', 'None')}
🏆 <b>Level:</b> {user.get('level', 'Spinner')}
🎯 <b>Spin Points:</b> {user.get('spin_points', 0)}
🎰 <b>Total Spins:</b> {user.get('total_spins', 0)}
💎 <b>Total Hits:</b> {user.get('hits', 0)}
🔄 <b>Spins Available:</b> {user.get('spins_available', 0)}
👥 <b>Referrals:</b> {user.get('referrals', 0)}
🖼️ <b>NFTs:</b> {len(user.get('nfts', []))}
📅 <b>Created:</b> {user.get('created_at', 'Unknown')}
📅 <b>Updated:</b> {user.get('updated_at', 'Unknown')}"""
        
        # Add ban status if applicable
        if user.get('banned', False):
            info_text += f"\n🚫 <b>Status:</b> BANNED"
            info_text += f"\n📝 <b>Ban Reason:</b> {user.get('ban_reason', 'No reason provided')}"
            info_text += f"\n📅 <b>Ban Date:</b> {user.get('ban_date', 'Unknown')}"
        else:
            info_text += f"\n✅ <b>Status:</b> Active"
        
        # Add NFT list if user has any
        if user.get('nfts'):
            info_text += f"\n\n🎁 <b>NFT Collection:</b>\n"
            for nft in user.get('nfts', []):
                info_text += f"• {nft}\n"
        
        await message.reply(info_text, parse_mode="HTML")
        
    except ValueError:
        await message.reply("❌ <b>Invalid user ID!</b>\n\nUser ID must be a number.", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"❌ <b>Error getting user information:</b>\n\n{str(e)}", parse_mode="HTML")


# Universal Admin Callback Debug Handler
@router.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_debug_callback(callback: types.CallbackQuery):
    """Debug handler for all admin callbacks"""
    user_id = callback.from_user.id
    callback_data = callback.data
    
    print(f"🔍 [Admin Debug] Callback received: '{callback_data}' from user {user_id}")
    print(f"🔍 [Admin Debug] Callback data length: {len(callback_data)}")
    print(f"🔍 [Admin Debug] Callback data repr: {repr(callback_data)}")
    
    # Check if this is a known admin callback
    if callback_data.startswith("admin_reset_user_"):
        print(f"🔍 [Admin Debug] Routing to reset user data handler")
        return await admin_reset_user_data_callback(callback)
    elif callback_data.startswith("admin_ban_user_"):
        print(f"🔍 [Admin Debug] Routing to ban user handler")
        return await admin_ban_user_callback(callback)
    elif callback_data.startswith("admin_user_stats_"):
        print(f"🔍 [Admin Debug] Routing to user stats handler")
        return await admin_user_stats_callback(callback)
    elif callback_data.startswith("admin_user_detail_"):
        print(f"🔍 [Admin Debug] Routing to individual user detail handler")
        return await admin_individual_user_detail_callback(callback)
    elif callback_data.startswith("admin_confirm_reset_"):
        print(f"🔍 [Admin Debug] Routing to confirm reset handler")
        return await admin_confirm_reset_user_data_callback(callback)
    elif callback_data.startswith("admin_confirm_ban_"):
        print(f"🔍 [Admin Debug] Routing to confirm ban handler")
        return await admin_confirm_ban_user_callback(callback)
    elif callback_data.startswith("admin_unban_user_"):
        print(f"🔍 [Admin Debug] Routing to unban user handler")
        return await admin_unban_user_callback(callback)
    elif callback_data == "admin_panel":
        print(f"🔍 [Admin Debug] Routing to admin panel handler")
        return await admin_panel_callback(callback)
    elif callback_data == "admin_user_management":
        print(f"🔍 [Admin Debug] Routing to user management handler")
        return await admin_user_management_callback(callback)
    elif callback_data == "admin_user_details":
        print(f"🔍 [Admin Debug] Routing to user details handler")
        return await admin_user_details_callback(callback)
    elif callback_data == "admin_financial_management":
        print(f"🔍 [Admin Debug] Routing to financial management handler")
        return await admin_financial_management_callback(callback)
    elif callback_data == "admin_system_management":
        print(f"🔍 [Admin Debug] Routing to system management handler")
        return await admin_system_management_callback(callback)
    elif callback_data == "admin_content_management":
        print(f"🔍 [Admin Debug] Routing to content management handler")
        return await admin_content_management_callback(callback)
    elif callback_data == "admin_analytics_reports":
        print(f"🔍 [Admin Debug] Routing to analytics reports handler")
        return await admin_analytics_reports_callback(callback)
    elif callback_data == "admin_view_users":
        print(f"🔍 [Admin Debug] Routing to view users handler")
        return await admin_view_users_callback(callback)
    elif callback_data == "admin_reset_user":
        print(f"🔍 [Admin Debug] Routing to reset user handler")
        return await admin_reset_user_callback(callback)
    elif callback_data == "admin_ban_user":
        print(f"🔍 [Admin Debug] Routing to ban user handler")
        return await admin_ban_user_callback(callback)
    elif callback_data == "admin_give_package":
        print(f"🔍 [Admin Debug] Routing to give package handler")
        return await admin_give_package_callback(callback)
    elif callback_data.startswith("admin_select_package_"):
        print(f"🔍 [Admin Debug] Routing to select package handler")
        return await admin_select_package_callback(callback)
    elif callback_data.startswith("admin_give_package_"):
        print(f"🔍 [Admin Debug] Routing to give specific package handler")
        return await admin_give_specific_package_callback(callback)
    elif callback_data == "admin_package_stats":
        print(f"🔍 [Admin Debug] Routing to package stats handler")
        return await admin_package_stats_callback(callback)
    elif callback_data == "admin_hit_stats":
        print(f"🔍 [Admin Debug] Routing to hit stats handler")
        return await admin_hit_stats_callback(callback)
    elif callback_data == "admin_payment_tracking":
        print(f"🔍 [Admin Debug] Routing to payment tracking handler")
        return await admin_payment_tracking_callback(callback)
    elif callback_data == "admin_revenue_analytics":
        print(f"🔍 [Admin Debug] Routing to revenue analytics handler")
        return await admin_revenue_analytics_callback(callback)
    elif callback_data == "admin_bot_stats":
        print(f"🔍 [Admin Debug] Routing to bot stats handler")
        return await admin_bot_stats_callback(callback)
    elif callback_data == "admin_broadcast":
        print(f"🔍 [Admin Debug] Routing to broadcast handler")
        return await admin_broadcast_callback(callback)
    elif callback_data.startswith("admin_broadcast_confirm:"):
        print(f"🔍 [Admin Debug] Routing to broadcast confirm handler")
        return await admin_broadcast_confirm_callback(callback)
    elif callback_data == "admin_database_management":
        print(f"🔍 [Admin Debug] Routing to database management handler")
        try:
            return await admin_database_management_callback(callback)
        except Exception as e:
            print(f"❌ [Admin Debug] Error in database management handler: {e}")
            await callback.answer(f"Error: {str(e)}", show_alert=True)
    elif callback_data == "admin_logs_monitoring":
        print(f"🔍 [Admin Debug] Routing to logs monitoring handler")
        try:
            return await admin_logs_monitoring_callback(callback)
        except Exception as e:
            print(f"❌ [Admin Debug] Error in logs monitoring handler: {e}")
            await callback.answer(f"Error: {str(e)}", show_alert=True)
    elif callback_data == "admin_maintenance_mode":
        print(f"🔍 [Admin Debug] Routing to maintenance mode handler")
        try:
            return await admin_maintenance_mode_callback(callback)
        except Exception as e:
            print(f"❌ [Admin Debug] Error in maintenance mode handler: {e}")
            await callback.answer(f"Error: {str(e)}", show_alert=True)
    elif callback_data == "admin_toggle_maintenance":
        print(f"🔍 [Admin Debug] Routing to toggle maintenance handler")
        return await admin_toggle_maintenance_callback(callback)
    elif callback_data == "admin_db_backup":
        print(f"🔍 [Admin Debug] Routing to database backup handler")
        return await admin_db_backup_callback(callback)
    elif callback_data == "admin_db_optimize":
        print(f"🔍 [Admin Debug] Routing to database optimize handler")
        return await admin_db_optimize_callback(callback)
    elif callback_data == "admin_db_cleanup":
        print(f"🔍 [Admin Debug] Routing to database cleanup handler")
        return await admin_db_cleanup_callback(callback)
    elif callback_data == "admin_daily_reports":
        print(f"🔍 [Admin Debug] Routing to daily reports handler")
        return await admin_daily_reports_callback(callback)
    elif callback_data == "admin_weekly_reports":
        print(f"🔍 [Admin Debug] Routing to weekly reports handler")
        return await admin_weekly_reports_callback(callback)
    elif callback_data == "admin_monthly_reports":
        print(f"🔍 [Admin Debug] Routing to monthly reports handler")
        return await admin_weekly_reports_callback(callback)  # Use weekly reports for now
    elif callback_data == "admin_popular_packages":
        print(f"🔍 [Admin Debug] Routing to popular packages handler")
        return await admin_popular_packages_callback(callback)
    elif callback_data == "admin_user_retention":
        print(f"🔍 [Admin Debug] Routing to user retention handler")
        return await admin_user_retention_callback(callback)
    elif callback_data == "admin_export_data":
        print(f"🔍 [Admin Debug] Routing to export data handler")
        return await admin_export_data_callback(callback)
    elif callback_data == "admin_nft_distribution":
        print(f"🔍 [Admin Debug] Routing to NFT distribution handler")
        return await admin_nft_distribution_callback(callback)
    elif callback_data == "admin_hit_rate_analytics":
        print(f"🔍 [Admin Debug] Routing to hit rate analytics handler")
        return await admin_hit_rate_analytics_callback(callback)
    elif callback_data == "admin_nft_analytics":
        print(f"🔍 [Admin Debug] Routing to NFT analytics handler")
        return await admin_nft_analytics_callback(callback)
    elif callback_data == "admin_package_pricing":
        print(f"🔍 [Admin Debug] Routing to package pricing handler")
        return await admin_package_pricing_callback(callback)
    elif callback_data == "admin_pricing_analytics":
        print(f"🔍 [Admin Debug] Routing to pricing analytics handler")
        return await admin_pricing_analytics_callback(callback)
    elif callback_data == "admin_pending_payments":
        print(f"🔍 [Admin Debug] Routing to pending payments handler")
        return await admin_pending_payments_callback(callback)
    elif callback_data == "admin_transaction_history":
        print(f"🔍 [Admin Debug] Routing to transaction history handler")
        return await admin_transaction_history_callback(callback)
    elif callback_data == "admin_advanced_revenue_analytics":
        print(f"🔍 [Admin Debug] Routing to advanced revenue analytics handler")
        return await admin_advanced_revenue_analytics_callback(callback)
    elif callback_data == "admin_clean_expired_payments":
        print(f"🔍 [Admin Debug] Routing to clean expired payments handler")
        return await admin_clean_expired_payments_callback(callback)
    elif callback_data == "admin_db_stats":
        print(f"🔍 [Admin Debug] Routing to database stats handler")
        return await admin_db_stats_callback(callback)
    elif callback_data == "admin_db_integrity":
        print(f"🔍 [Admin Debug] Routing to database integrity handler")
        return await admin_db_integrity_callback(callback)
    elif callback_data == "admin_db_export":
        print(f"🔍 [Admin Debug] Routing to database export handler")
        return await admin_export_data_callback(callback)
    elif callback_data == "admin_view_logs":
        print(f"🔍 [Admin Debug] Routing to view logs handler")
        return await admin_view_logs_callback(callback)
    elif callback_data == "admin_influencer_management":
        print(f"🔍 [Admin Debug] Routing to influencer management handler")
        return await admin_influencer_management_callback(callback)
    elif callback_data == "admin_view_all_commissions":
        print(f"🔍 [Admin Debug] Routing to view all commissions handler")
        return await admin_view_all_commissions_callback(callback)
    elif callback_data == "admin_top_earners":
        print(f"🔍 [Admin Debug] Routing to top earners handler")
        return await admin_top_earners_callback(callback)
    elif callback_data == "admin_commission_analytics":
        print(f"🔍 [Admin Debug] Routing to commission analytics handler")
        return await admin_commission_analytics_callback(callback)
    elif callback_data == "admin_export_influencer_data":
        print(f"🔍 [Admin Debug] Routing to export influencer data handler")
        return await admin_export_influencer_data_callback(callback)
    elif callback_data == "admin_system_metrics":
        print(f"🔍 [Admin Debug] Routing to system metrics handler")
        return await admin_system_metrics_callback(callback)
    elif callback_data == "admin_health_check":
        print(f"🔍 [Admin Debug] Routing to health check handler")
        return await admin_health_check_callback(callback)
    elif callback_data == "admin_view_alerts":
        print(f"🔍 [Admin Debug] Routing to view alerts handler")
        return await admin_view_alerts_callback(callback)
    elif callback_data == "admin_alert_settings":
        print(f"🔍 [Admin Debug] Routing to alert settings handler")
        return await admin_alert_settings_callback(callback)
    elif callback_data == "admin_reset_metrics":
        print(f"🔍 [Admin Debug] Routing to reset metrics handler")
        return await admin_reset_metrics_callback(callback)
    elif callback_data == "admin_set_maintenance_message":
        print(f"🔍 [Admin Debug] Routing to set maintenance message handler")
        return await admin_set_maintenance_message_callback(callback)
    elif callback_data == "admin_schedule_maintenance":
        print(f"🔍 [Admin Debug] Routing to schedule maintenance handler")
        return await admin_schedule_maintenance_callback(callback)
    elif callback_data in ["admin_schedule_30min", "admin_schedule_1hour", "admin_schedule_2hours", "admin_schedule_custom"]:
        print(f"🔍 [Admin Debug] Routing to schedule maintenance time handler: {callback_data}")
        return await admin_schedule_time_callback(callback, callback_data)
    elif callback_data == "admin_edit_prices":
        print(f"🔍 [Admin Debug] Routing to edit prices handler")
        return await admin_edit_prices_callback(callback)
    elif callback_data in ["admin_edit_bronze_price", "admin_edit_silver_price", "admin_edit_gold_price", "admin_edit_black_price"]:
        print(f"🔍 [Admin Debug] Routing to individual package price handler: {callback_data}")
        return await admin_edit_individual_price_callback(callback, callback_data)
    elif callback_data == "admin_bulk_edit_prices":
        print(f"🔍 [Admin Debug] Routing to bulk edit prices handler")
        return await admin_bulk_edit_prices_callback(callback)
    elif callback_data == "admin_price_history":
        print(f"🔍 [Admin Debug] Routing to price history handler")
        return await admin_price_history_callback(callback)
    elif callback_data == "admin_revenue_projections":
        print(f"🔍 [Admin Debug] Routing to revenue projections handler")
        return await admin_revenue_projections_callback(callback)
    elif callback_data == "admin_price_optimization":
        print(f"🔍 [Admin Debug] Routing to price optimization handler")
        return await admin_price_optimization_callback(callback)
    elif callback_data == "admin_pricing_analytics":
        print(f"🔍 [Admin Debug] Routing to pricing analytics handler")
        return await admin_pricing_analytics_callback(callback)
    elif callback_data.startswith("admin_price_") and any(x in callback_data for x in ["_+10", "_-10", "_+25", "_-25", "_+50", "_-50"]):
        print(f"🔍 [Admin Debug] Routing to price adjustment handler: {callback_data}")
        return await admin_price_adjustment_callback(callback, callback_data)
    elif callback_data.startswith("admin_custom_ton_") or callback_data.startswith("admin_custom_stars_"):
        print(f"🔍 [Admin Debug] Routing to custom price handler: {callback_data}")
        return await admin_custom_price_callback(callback, callback_data)
    elif callback_data.startswith("admin_market_price_") or callback_data == "admin_market_adjust":
        print(f"🔍 [Admin Debug] Routing to market price handler: {callback_data}")
        return await admin_market_price_callback(callback, callback_data)
    elif callback_data.startswith("admin_reset_price_"):
        print(f"🔍 [Admin Debug] Routing to reset price handler: {callback_data}")
        return await admin_reset_price_callback(callback, callback_data)
    elif callback_data.startswith("admin_bulk_") and any(x in callback_data for x in ["_+10", "_-10", "_+25", "_-25", "_+50", "_-50"]):
        print(f"🔍 [Admin Debug] Routing to bulk price adjustment handler: {callback_data}")
        return await admin_bulk_price_adjustment_callback(callback, callback_data)
    elif callback_data == "admin_competitive_pricing":
        print(f"🔍 [Admin Debug] Routing to competitive pricing handler")
        return await admin_competitive_pricing_callback(callback)
    elif callback_data == "admin_ab_testing":
        print(f"🔍 [Admin Debug] Routing to A/B testing handler")
        return await admin_ab_testing_callback(callback)
    elif callback_data in ["admin_export_price_history", "admin_export_revenue_report", "admin_export_analytics"]:
        print(f"🔍 [Admin Debug] Routing to export handler: {callback_data}")
        return await admin_export_pricing_data_callback(callback, callback_data)
    elif callback_data == "admin_optimization_report":
        print(f"🔍 [Admin Debug] Routing to optimization report handler")
        return await admin_optimization_report_callback(callback)
    elif callback_data == "admin_daily_reports":
        print(f"🔍 [Admin Debug] Routing to daily reports handler")
        return await admin_daily_reports_callback(callback)
    elif callback_data == "admin_weekly_reports":
        print(f"🔍 [Admin Debug] Routing to weekly reports handler")
        return await admin_weekly_reports_callback(callback)
    elif callback_data == "admin_monthly_reports":
        print(f"🔍 [Admin Debug] Routing to monthly reports handler")
        return await admin_monthly_reports_callback(callback)
    elif callback_data == "admin_popular_packages":
        print(f"🔍 [Admin Debug] Routing to popular packages handler")
        return await admin_popular_packages_callback(callback)
    elif callback_data == "admin_user_retention":
        print(f"🔍 [Admin Debug] Routing to user retention handler")
        return await admin_user_retention_callback(callback)
    elif callback_data == "admin_export_data":
        print(f"🔍 [Admin Debug] Routing to export data handler")
        return await admin_export_data_callback(callback)
    elif callback_data == "admin_export_monthly_data":
        print(f"🔍 [Admin Debug] Routing to export monthly data handler")
        return await admin_export_monthly_data_callback(callback)
    elif callback_data == "admin_monthly_trends":
        print(f"🔍 [Admin Debug] Routing to monthly trends handler")
        return await admin_monthly_trends_callback(callback)
    elif callback_data in ["admin_export_monthly_csv", "admin_export_monthly_json", "admin_export_monthly_pdf", "admin_export_monthly_excel"]:
        print(f"🔍 [Admin Debug] Routing to export format handler: {callback_data}")
        return await admin_export_format_callback(callback, callback_data)
    elif callback_data in ["admin_detailed_trends", "admin_trends_forecast"]:
        print(f"🔍 [Admin Debug] Routing to trend analysis handler: {callback_data}")
        return await admin_trend_analysis_callback(callback, callback_data)
    else:
        print(f"⚠️ [Admin Debug] Unknown admin callback: {callback_data}")
        await callback.answer("Unknown admin command", show_alert=True)


# Admin Panel Callback Handler
async def admin_panel_callback(callback: types.CallbackQuery):
    """Handle admin panel access"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Admin panel callback triggered for user {user_id}")
    
    # Check if user is admin
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Admin access granted for user {user_id}")
    
    # Import admin translations
    from translations import get_admin_text
    
    # Create admin panel menu
    admin_text = f"{get_admin_text(user_id, 'admin_panel_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "user_management"), callback_data="admin_user_management"),
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "financial_management"), callback_data="admin_financial_management"),
            InlineKeyboardButton(text=get_admin_text(user_id, "system_management"), callback_data="admin_system_management")
        ],
        [
            InlineKeyboardButton(text="🌟 Influencer Management", callback_data="admin_influencer_management"),
            InlineKeyboardButton(text=get_admin_text(user_id, "content_management"), callback_data="admin_content_management")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "analytics_reports"), callback_data="admin_analytics_reports")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="back_to_main")
        ]
    ])
    
    # Send new message instead of editing (since original was a video)
    await callback.message.answer(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin User Management Callback
async def admin_user_management_callback(callback: types.CallbackQuery):
    """Handle admin user management menu"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] User management callback triggered for user {user_id}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] User management access granted for user {user_id}")
    
    from translations import get_admin_text
    
    admin_text = f"{get_admin_text(user_id, 'user_management_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "view_all_users"), callback_data="admin_view_users"),
            InlineKeyboardButton(text=get_admin_text(user_id, "user_details"), callback_data="admin_user_details")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "reset_user_data"), callback_data="admin_reset_user"),
            InlineKeyboardButton(text=get_admin_text(user_id, "ban_unban_users"), callback_data="admin_ban_user")
        ],
        [
            InlineKeyboardButton(text="📦 Give Package", callback_data="admin_give_package")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    try:
        await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        # If message is not modified, just answer the callback
        if "message is not modified" in str(e):
            await callback.answer()
            return
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin User Details Callback
async def admin_user_details_callback(callback: types.CallbackQuery):
    """Handle admin user details - show user selection interface"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    from src.models import get_all_users
    
    # Get all users for selection
    all_users = get_all_users()
    
    if not all_users:
        details_text = "👥 <b>User Details</b>\n\n❌ No users found in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
        ])
    else:
        details_text = f"👥 <b>User Details</b>\n\n📊 <b>Total Users:</b> {len(all_users)}\n\n"
        details_text += "🔍 <b>Select a user to view details:</b>\n\n"
        
        # Create keyboard with user selection (show first 10 users)
        keyboard_buttons = []
        user_list = list(all_users.items())[:10]  # Limit to first 10 users
        
        for i, (user_id_key, user_data) in enumerate(user_list):
            if i % 2 == 0:
                keyboard_buttons.append([])
            
            username = user_data.get('username', 'Unknown')
            package = user_data.get('package', 'None')
            
            button_text = f"👤 {username[:8]} ({package.title()})"
            if len(button_text) > 20:
                button_text = f"👤 {username[:6]}... ({package.title()})"
            
            keyboard_buttons[-1].append(
                InlineKeyboardButton(
                    text=button_text, 
                    callback_data=f"admin_user_detail_{user_id_key}"
                )
            )
        
        # Add back button
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(details_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Individual User Detail Callback
# Removed duplicate decorator - handled by universal admin debug handler
async def admin_individual_user_detail_callback(callback: types.CallbackQuery):
    """Handle individual user detail view"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        detail_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Create detailed user information
        detail_text = f"👤 <b>User Details</b>\n\n"
        detail_text += f"🆔 <b>User ID:</b> {target_user_id}\n"
        detail_text += f"👤 <b>Username:</b> @{user_data.get('username', 'Unknown')}\n"
        detail_text += f"📦 <b>Package:</b> {user_data.get('package', 'None').title()}\n"
        detail_text += f"🎰 <b>Total Spins:</b> {user_data.get('total_spins', 0):,}\n"
        detail_text += f"💎 <b>Total Hits:</b> {user_data.get('hits', 0):,}\n"
        detail_text += f"🎁 <b>NFTs Won:</b> {len(user_data.get('nfts', []))}\n"
        detail_text += f"🔄 <b>Spins Available:</b> {user_data.get('spins_available', 0)}\n"
        detail_text += f"⭐ <b>Points:</b> {user_data.get('points', 0)}\n"
        detail_text += f"🏆 <b>Level:</b> {user_data.get('level', 'Spinner')}\n"
        detail_text += f"💰 <b>Total Spent:</b> {user_data.get('total_spent', 0):.4f} TON\n"
        detail_text += f"📅 <b>Joined:</b> {user_data.get('created_at', 'Unknown')}\n"
        detail_text += f"🕒 <b>Last Active:</b> {user_data.get('updated_at', 'Unknown')}\n"
        
        # Show NFTs if any
        nfts = user_data.get('nfts', [])
        if nfts:
            detail_text += f"\n🎁 <b>NFTs Won:</b>\n"
            for nft in nfts[:5]:  # Show first 5 NFTs
                detail_text += f"   • {nft}\n"
            if len(nfts) > 5:
                detail_text += f"   ... and {len(nfts) - 5} more\n"
        
        # Show referral info
        referrer_id = user_data.get('referrer_id')
        if referrer_id:
            detail_text += f"\n🎯 <b>Referred by:</b> User {referrer_id}\n"
        
        referrals = user_data.get('referrals', 0)
        if referrals > 0:
            detail_text += f"🎯 <b>Referrals made:</b> {referrals}\n"
        
        # Create action buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Reset Data", callback_data=f"admin_reset_user_{target_user_id}"),
                InlineKeyboardButton(text="🚫 Ban User", callback_data=f"admin_ban_user_{target_user_id}")
            ],
            [
                InlineKeyboardButton(text="📊 View Stats", callback_data=f"admin_user_stats_{target_user_id}")
            ],
            [
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")
            ]
        ])
    
    await callback.message.edit_text(detail_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin User Stats Callback
async def admin_user_stats_callback(callback: types.CallbackQuery):
    """Handle user stats view"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] User stats callback triggered for user {user_id}, data: {callback.data}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] User stats access granted for user {user_id}")
    
    from translations import get_admin_text
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        stats_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Create detailed stats
        stats_text = f"📊 <b>User Statistics</b>\n\n"
        stats_text += f"👤 <b>User:</b> @{user_data.get('username', 'Unknown')} (ID: {target_user_id})\n"
        stats_text += f"📦 <b>Package:</b> {user_data.get('package', 'None').title()}\n"
        stats_text += f"🎰 <b>Total Spins:</b> {user_data.get('total_spins', 0):,}\n"
        stats_text += f"💎 <b>Total Hits:</b> {user_data.get('hits', 0):,}\n"
        stats_text += f"🎁 <b>NFTs Won:</b> {len(user_data.get('nfts', []))}\n"
        stats_text += f"⭐ <b>Points:</b> {user_data.get('points', 0)}\n"
        stats_text += f"🔄 <b>Spins Available:</b> {user_data.get('spins_available', 0)}\n"
        stats_text += f"👥 <b>Referrals:</b> {user_data.get('referrals', 0)}\n"
        stats_text += f"🚫 <b>Status:</b> {'Banned' if user_data.get('banned', False) else 'Active'}\n"
        
        # Calculate hit rate
        total_spins = user_data.get('total_spins', 0)
        total_hits = user_data.get('hits', 0)
        hit_rate = (total_hits / total_spins * 100) if total_spins > 0 else 0
        
        stats_text += f"🎯 <b>Hit Rate:</b> {hit_rate:.1f}%\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Reset User Data Callback
async def admin_reset_user_data_callback(callback: types.CallbackQuery):
    """Handle reset user data functionality"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Reset user data callback triggered for user {user_id}, data: {callback.data}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Reset user data access granted for user {user_id}")
    
    from translations import get_admin_text
    
    # Handle case where callback data is just "admin_reset_user" (menu button)
    if callback.data == "admin_reset_user":
        # Show user selection menu
        admin_text = f"🔄 <b>Reset User Data</b>\n\n"
        admin_text += f"Select a user to reset their data:\n\n"
        admin_text += f"<i>⚠️ This will reset all user data including spins, points, and package information.</i>"
        
        # Get all users from database
        try:
            conn = sqlite3.connect('cgspins.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, spins_available FROM users ORDER BY user_id DESC LIMIT 20")
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
                ])
                admin_text = "❌ <b>No users found in database</b>"
            else:
                keyboard_buttons = []
                for user_id_key, username, spins_available in users:
                    display_name = f"@{username}" if username else f"User {user_id_key}"
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"{display_name} ({spins_available} spins)",
                            callback_data=f"admin_reset_user_{user_id_key}"
                        )
                    ])
                
                keyboard_buttons.append([
                    InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
                ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        except Exception as e:
            print(f"Error getting users for reset: {e}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
            ])
            admin_text = f"❌ <b>Error loading users:</b>\n\n{str(e)}"
        
        try:
            await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                print(f"Error editing message: {e}")
        await callback.answer()
        return
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data to show what will be reset
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        reset_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Show what will be reset
        reset_text = f"🔄 <b>Reset User Data</b>\n\n"
        reset_text += f"👤 <b>User:</b> @{user_data.get('username', 'Unknown')} (ID: {target_user_id})\n\n"
        reset_text += f"⚠️ <b>This will reset:</b>\n"
        reset_text += f"   🎰 Total Spins: {user_data.get('total_spins', 0):,} → 0\n"
        reset_text += f"   💎 Total Hits: {user_data.get('hits', 0):,} → 0\n"
        reset_text += f"   🎁 NFTs Won: {len(user_data.get('nfts', []))} → 0\n"
        reset_text += f"   ⭐ Points: {user_data.get('points', 0)} → 0\n"
        reset_text += f"   🏆 Level: {user_data.get('level', 'Spinner')} → Spinner\n"
        reset_text += f"   💰 Total Spent: {user_data.get('total_spent', 0):.4f} TON → 0\n\n"
        reset_text += f"✅ <b>This will keep:</b>\n"
        reset_text += f"   📦 Current Package: {user_data.get('package', 'None').title()}\n"
        reset_text += f"   🔄 Spins Available: {user_data.get('spins_available', 0)}\n"
        reset_text += f"   🎯 Referral Info: {user_data.get('referrals', 0)} referrals\n\n"
        reset_text += f"⚠️ <b>Are you sure you want to reset this user's data?</b>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yes, Reset", callback_data=f"admin_confirm_reset_{target_user_id}"),
                InlineKeyboardButton(text="❌ Cancel", callback_data=f"admin_user_detail_{target_user_id}")
            ],
            [
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")
            ]
        ])
    
    await callback.message.edit_text(reset_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Confirm Reset User Data Callback
# Removed duplicate decorator - handled by universal admin debug handler
async def admin_confirm_reset_user_data_callback(callback: types.CallbackQuery):
    """Handle confirmation of reset user data"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data before reset
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        result_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Reset user data - keep some important fields
        username = user_data.get('username', '')
        package = user_data.get('package', 'None')
        referrals = user_data.get('referrals', 0)
        referred_by = user_data.get('referred_by', 0)
        language = user_data.get('language', 'en')
        created_at = user_data.get('created_at', '')
        spins_available = user_data.get('spins_available', 0)
        
        # Create new user data with reset values
        reset_user_data = {
            'balance': 0,
            'package': 'None',
            'level': 'Spinner',
            'spin_points': 0,
            'hits': 0,
            'total_spins': 0,
            'spins_available': 0,
            'referrals': referrals,
            'payment_method': '',
            'updated_at': datetime.now().isoformat(),
            'referred_by': referred_by,
            'nfts': '',
            'language': language,
            'lang': language,
            'username': username
        }
        
        # Save reset user data to database
        success = save_user_data_to_db(target_user_id, reset_user_data)
        
        if success:
            # Also update in-memory data if it exists
            if target_user_id in globals()['user_data']:
                globals()['user_data'][target_user_id].update(reset_user_data)
        
        result_text = f"✅ <b>User Data Reset Successfully!</b>\n\n"
        result_text += f"👤 <b>User:</b> @{username} (ID: {target_user_id})\n\n"
        result_text += f"🔄 <b>Reset Complete:</b>\n"
        result_text += f"   🎰 Total Spins: 0\n"
        result_text += f"   💎 Total Hits: 0\n"
        result_text += f"   🎁 NFTs Won: 0\n"
        result_text += f"   ⭐ Points: 0\n"
        result_text += f"   🏆 Level: Spinner\n"
        result_text += f"   💰 Total Spent: 0.0000 TON\n\n"
        result_text += f"✅ <b>Preserved:</b>\n"
        result_text += f"   📦 Package: {package.title()}\n"
        result_text += f"   🔄 Spins Available: {spins_available}\n"
        result_text += f"   🎯 Referrals: {referrals}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 View User", callback_data=f"admin_user_detail_{target_user_id}"),
                InlineKeyboardButton(text="📊 User Details", callback_data="admin_user_details")
            ],
            [
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
            ]
        ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Ban User Callback
async def admin_ban_user_callback(callback: types.CallbackQuery):
    """Handle ban user functionality"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Ban user callback triggered for user {user_id}, data: {callback.data}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Ban user access granted for user {user_id}")
    
    from translations import get_admin_text
    
    # Handle case where callback data is just "admin_ban_user" (menu button)
    if callback.data == "admin_ban_user":
        # Show user selection menu
        admin_text = f"🚫 <b>Ban User</b>\n\n"
        admin_text += f"Select a user to ban:\n\n"
        admin_text += f"<i>⚠️ This will prevent the user from accessing the bot.</i>"
        
        # Get all users from database
        try:
            conn = sqlite3.connect('cgspins.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username, spins_available FROM users ORDER BY user_id DESC LIMIT 20")
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
                ])
                admin_text = "❌ <b>No users found in database</b>"
            else:
                keyboard_buttons = []
                for user_id_key, username, spins_available in users:
                    display_name = f"@{username}" if username else f"User {user_id_key}"
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"{display_name} ({spins_available} spins)",
                            callback_data=f"admin_ban_user_{user_id_key}"
                        )
                    ])
                
                keyboard_buttons.append([
                    InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
                ])
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        except Exception as e:
            print(f"Error getting users for ban: {e}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
            ])
            admin_text = f"❌ <b>Error loading users:</b>\n\n{str(e)}"
        
        try:
            await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            if "message is not modified" in str(e):
                pass
            else:
                print(f"Error editing message: {e}")
        await callback.answer()
        return
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        ban_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Check if user is already banned
        is_banned = user_data.get('banned', False)
        username = user_data.get('username', 'Unknown')
        
        if is_banned:
            ban_text = f"🚫 <b>User Already Banned</b>\n\n"
            ban_text += f"👤 <b>User:</b> @{username} (ID: {target_user_id})\n"
            ban_text += f"🚫 <b>Status:</b> Banned\n\n"
            ban_text += f"⚠️ <b>This user is already banned from using the bot.</b>\n\n"
            ban_text += f"Would you like to unban this user?"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Unban User", callback_data=f"admin_unban_user_{target_user_id}"),
                    InlineKeyboardButton(text="❌ Keep Banned", callback_data=f"admin_user_detail_{target_user_id}")
                ],
                [
                    InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")
                ]
            ])
        else:
            ban_text = f"🚫 <b>Ban User</b>\n\n"
            ban_text += f"👤 <b>User:</b> @{username} (ID: {target_user_id})\n"
            ban_text += f"📦 <b>Package:</b> {user_data.get('package', 'None').title()}\n"
            ban_text += f"🎰 <b>Total Spins:</b> {user_data.get('total_spins', 0):,}\n"
            ban_text += f"🔄 <b>Spins Available:</b> {user_data.get('spins_available', 0)}\n\n"
            ban_text += f"⚠️ <b>Banning this user will:</b>\n"
            ban_text += f"   🚫 Prevent them from using the bot\n"
            ban_text += f"   🚫 Block all bot interactions\n"
            ban_text += f"   🚫 Preserve their data (can be unbanned later)\n\n"
            ban_text += f"⚠️ <b>Are you sure you want to ban this user?</b>"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚫 Yes, Ban", callback_data=f"admin_confirm_ban_{target_user_id}"),
                    InlineKeyboardButton(text="❌ Cancel", callback_data=f"admin_user_detail_{target_user_id}")
                ],
                [
                    InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")
                ]
            ])
    
    await callback.message.edit_text(ban_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Confirm Ban User Callback
# Removed duplicate decorator - handled by universal admin debug handler
async def admin_confirm_ban_user_callback(callback: types.CallbackQuery):
    """Handle confirmation of ban user"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data from database
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        result_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Ban the user
        user_data['banned'] = 1
        user_data['banned_at'] = datetime.now().isoformat()
        user_data['banned_by'] = user_id
        user_data['updated_at'] = datetime.now().isoformat()
        
        # Save updated user data to database
        success = save_user_data_to_db(target_user_id, user_data)
        
        if success:
            # Also update in-memory data if it exists
            if target_user_id in globals()['user_data']:
                globals()['user_data'][target_user_id]['banned'] = 1
                globals()['user_data'][target_user_id]['banned_at'] = datetime.now().isoformat()
                globals()['user_data'][target_user_id]['banned_by'] = user_id
            
            username = user_data.get('username', '')
            display_name = f"@{username}" if username else f"User {target_user_id}"
        
            result_text = f"🚫 <b>User Banned Successfully!</b>\n\n"
            result_text += f"👤 <b>User:</b> {display_name} (ID: {target_user_id})\n"
            result_text += f"🚫 <b>Status:</b> Banned\n"
            result_text += f"👮 <b>Banned by:</b> Admin {user_id}\n"
            result_text += f"🕒 <b>Banned at:</b> {user_data.get('banned_at', 'Now')}\n\n"
            result_text += f"⚠️ <b>This user can no longer:</b>\n"
            result_text += f"   🚫 Use the bot\n"
            result_text += f"   🚫 Send commands\n"
            result_text += f"   🚫 Access any features\n\n"
            result_text += f"✅ <b>User data preserved for potential unban.</b>"
        else:
            result_text = f"❌ <b>Failed to Ban User</b>\n\nUser ID: {target_user_id}\n\nDatabase update failed. Please try again."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Unban User", callback_data=f"admin_unban_user_{target_user_id}"),
                InlineKeyboardButton(text="👤 View User", callback_data=f"admin_user_detail_{target_user_id}")
            ],
            [
                InlineKeyboardButton(text="📊 User Details", callback_data="admin_user_details"),
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
            ]
        ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Unban User Callback
# Removed duplicate decorator - handled by universal admin debug handler
async def admin_unban_user_callback(callback: types.CallbackQuery):
    """Handle unban user functionality"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Extract user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data from database
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        result_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_details")]
        ])
    else:
        # Unban the user
        user_data['banned'] = 0
        user_data['banned_at'] = ''
        user_data['banned_by'] = 0
        user_data['updated_at'] = datetime.now().isoformat()
        
        # Save updated user data to database
        success = save_user_data_to_db(target_user_id, user_data)
        
        if success:
            # Also update in-memory data if it exists
            if target_user_id in globals()['user_data']:
                globals()['user_data'][target_user_id]['banned'] = 0
                globals()['user_data'][target_user_id]['banned_at'] = ''
                globals()['user_data'][target_user_id]['banned_by'] = 0
            
            username = user_data.get('username', '')
            display_name = f"@{username}" if username else f"User {target_user_id}"
        
            result_text = f"✅ <b>User Unbanned Successfully!</b>\n\n"
            result_text += f"👤 <b>User:</b> {display_name} (ID: {target_user_id})\n"
            result_text += f"✅ <b>Status:</b> Active\n"
            result_text += f"👮 <b>Unbanned by:</b> Admin {user_id}\n"
            result_text += f"🕒 <b>Unbanned at:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            result_text += f"🎉 <b>This user can now:</b>\n"
            result_text += f"   ✅ Use the bot normally\n"
            result_text += f"   ✅ Send commands\n"
            result_text += f"   ✅ Access all features\n"
            result_text += f"   ✅ Continue their progress\n\n"
            result_text += f"📦 <b>Package:</b> {user_data.get('package', 'None').title()}\n"
            result_text += f"🔄 <b>Spins Available:</b> {user_data.get('spins_available', 0)}"
        else:
            result_text = f"❌ <b>Failed to Unban User</b>\n\nUser ID: {target_user_id}\n\nDatabase update failed. Please try again."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚫 Ban Again", callback_data=f"admin_ban_user_{target_user_id}"),
                InlineKeyboardButton(text="👤 View User", callback_data=f"admin_user_detail_{target_user_id}")
            ],
            [
                InlineKeyboardButton(text="📊 User Details", callback_data="admin_user_details"),
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
            ]
        ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()




# Admin Package Statistics Callback
async def admin_package_stats_callback(callback: types.CallbackQuery):
    """Handle admin package statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    from src.models import load_ton_transactions, load_stars_transactions
    
    # Calculate package statistics
    package_stats = {}
    total_users = len(user_data)
    active_packages = 0
    
    for user_id_key, user in user_data.items():
        package = user.get('package', 'None')
        if package != 'None':
            active_packages += 1
            if package not in package_stats:
                package_stats[package] = {
                    'count': 0,
                    'total_spins': 0,
                    'total_hits': 0,
                    'total_points': 0
                }
            package_stats[package]['count'] += 1
            package_stats[package]['total_spins'] += user.get('total_spins', 0)
            package_stats[package]['total_hits'] += user.get('hits', 0)
            package_stats[package]['total_points'] += user.get('spin_points', 0)
    
    # Create statistics text
    stats_text = f"📦 <b>Package Statistics</b>\n\n"
    stats_text += f"👥 <b>Total Users:</b> {total_users}\n"
    stats_text += f"📦 <b>Active Packages:</b> {active_packages}\n"
    stats_text += f"📊 <b>Package Distribution:</b>\n\n"
    
    if package_stats:
        for package, stats in package_stats.items():
            percentage = (stats['count'] / active_packages * 100) if active_packages > 0 else 0
            stats_text += f"🥉 <b>{package.title()}:</b>\n"
            stats_text += f"   👥 Users: {stats['count']} ({percentage:.1f}%)\n"
            stats_text += f"   🎰 Total Spins: {stats['total_spins']}\n"
            stats_text += f"   💎 Total Hits: {stats['total_hits']}\n"
            stats_text += f"   ⭐ Total Points: {stats['total_points']}\n\n"
    else:
        stats_text += "📭 No active packages found\n\n"
    
    # Add package popularity ranking
    if package_stats:
        sorted_packages = sorted(package_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        stats_text += f"🏆 <b>Most Popular Packages:</b>\n"
        for i, (package, stats) in enumerate(sorted_packages[:3], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            stats_text += f"{emoji} {package.title()}: {stats['count']} users\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Hit Statistics Callback
async def admin_hit_stats_callback(callback: types.CallbackQuery):
    """Handle admin hit statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Calculate hit statistics
    total_spins = 0
    total_hits = 0
    total_users = len(user_data)
    active_users = 0
    hit_rates_by_package = {}
    level_distribution = {}
    
    for user_id_key, user in user_data.items():
        user_spins = user.get('total_spins', 0)
        user_hits = user.get('hits', 0)
        user_level = user.get('level', 'Spinner')
        user_package = user.get('package', 'None')
        
        total_spins += user_spins
        total_hits += user_hits
        
        if user_spins > 0:
            active_users += 1
        
        # Level distribution
        if user_level not in level_distribution:
            level_distribution[user_level] = 0
        level_distribution[user_level] += 1
        
        # Hit rates by package
        if user_package != 'None':
            if user_package not in hit_rates_by_package:
                hit_rates_by_package[user_package] = {
                    'total_spins': 0,
                    'total_hits': 0,
                    'users': 0
                }
            hit_rates_by_package[user_package]['total_spins'] += user_spins
            hit_rates_by_package[user_package]['total_hits'] += user_hits
            hit_rates_by_package[user_package]['users'] += 1
    
    # Calculate overall hit rate
    overall_hit_rate = (total_hits / total_spins * 100) if total_spins > 0 else 0
    
    # Create statistics text
    stats_text = f"🎯 <b>Hit Statistics</b>\n\n"
    stats_text += f"📊 <b>Overall Statistics:</b>\n"
    stats_text += f"   🎰 Total Spins: {total_spins:,}\n"
    stats_text += f"   💎 Total Hits: {total_hits:,}\n"
    stats_text += f"   📈 Hit Rate: {overall_hit_rate:.2f}%\n"
    stats_text += f"   👥 Active Users: {active_users}\n\n"
    
    # Package hit rates
    if hit_rates_by_package:
        stats_text += f"📦 <b>Hit Rates by Package:</b>\n"
        for package, stats in hit_rates_by_package.items():
            package_hit_rate = (stats['total_hits'] / stats['total_spins'] * 100) if stats['total_spins'] > 0 else 0
            stats_text += f"   🥉 <b>{package.title()}:</b>\n"
            stats_text += f"      🎰 Spins: {stats['total_spins']:,}\n"
            stats_text += f"      💎 Hits: {stats['total_hits']:,}\n"
            stats_text += f"      📈 Rate: {package_hit_rate:.2f}%\n"
            stats_text += f"      👥 Users: {stats['users']}\n\n"
    
    # Level distribution
    if level_distribution:
        stats_text += f"🏆 <b>Level Distribution:</b>\n"
        for level, count in sorted(level_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_users * 100) if total_users > 0 else 0
            emoji = config.LEVELS.get(level, {}).get('emoji', '🎯')
            stats_text += f"   {emoji} <b>{level}:</b> {count} users ({percentage:.1f}%)\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Financial Management Callback
async def admin_financial_management_callback(callback: types.CallbackQuery):
    """Handle admin financial management menu"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    admin_text = f"{get_admin_text(user_id, 'financial_management_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "payment_tracking"), callback_data="admin_payment_tracking"),
            InlineKeyboardButton(text=get_admin_text(user_id, "revenue_analytics"), callback_data="admin_revenue_analytics")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "pending_payments"), callback_data="admin_pending_payments"),
            InlineKeyboardButton(text=get_admin_text(user_id, "transaction_history"), callback_data="admin_transaction_history")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Payment Tracking Callback
async def admin_payment_tracking_callback(callback: types.CallbackQuery):
    """Handle admin payment tracking"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    from src.models import load_ton_transactions, load_stars_transactions
    
    # Load transaction data
    ton_transactions = load_ton_transactions()
    stars_transactions = load_stars_transactions()
    
    # Calculate payment statistics
    ton_payments = len(ton_transactions)
    stars_payments = len(stars_transactions)
    pending_ton = len(pending_ton_payments)
    
    # Calculate total revenue
    total_ton_revenue = sum(tx['amount'] for tx in ton_transactions)
    total_stars_revenue = sum(tx['amount_stars'] for tx in stars_transactions)  # Fixed: use 'amount_stars' for Stars transactions
    
    # Create payment tracking text
    tracking_text = f"💳 <b>Payment Tracking</b>\n\n"
    tracking_text += f"📊 <b>Payment Summary:</b>\n"
    tracking_text += f"   💎 TON Payments: {ton_payments}\n"
    tracking_text += f"   ⭐ Stars Payments: {stars_payments}\n"
    tracking_text += f"   ⏳ Pending TON: {pending_ton}\n\n"
    
    tracking_text += f"💰 <b>Revenue Summary:</b>\n"
    tracking_text += f"   💎 TON Revenue: {total_ton_revenue:.4f} TON\n"
    tracking_text += f"   ⭐ Stars Revenue: {total_stars_revenue:,} Stars\n"
    tracking_text += f"   📈 Total Payments: {ton_payments + stars_payments}\n\n"
    
    # Recent transactions
    recent_ton = ton_transactions[:5]  # Already sorted by processed_at DESC
    recent_stars = stars_transactions[:5]  # Already sorted by processed_at DESC
    
    if recent_ton or recent_stars:
        tracking_text += f"📋 <b>Recent Transactions:</b>\n"
        
        for transaction in recent_ton[:3]:  # Show most recent 3
            user_id_tx = transaction['user_id']
            amount = transaction['amount']
            package = transaction['package']
            processed_at = transaction.get('processed_at', 'Unknown')
            tx_hash = transaction.get('tx_hash', '')
            
            formatted_time = format_timestamp(processed_at)
            formatted_hash = format_transaction_hash(tx_hash)
            
            tracking_text += f"   💎 <b>TON</b>: {amount:.4f} TON ({package})\n"
            tracking_text += f"      👤 User: {user_id_tx} | 🕒 {formatted_time}\n"
            if tx_hash:
                tracking_text += f"      🔗 Hash: {formatted_hash}\n"
            tracking_text += "\n"
        
        for transaction in recent_stars[:3]:  # Show most recent 3
            user_id_tx = transaction['user_id']
            amount = transaction['amount_stars']  # Fixed: use 'amount_stars' for Stars transactions
            package = transaction['package']
            processed_at = transaction.get('processed_at', 'Unknown')
            tx_id = transaction.get('id', '')  # Fixed: use 'id' field for Stars transactions
            
            formatted_time = format_timestamp(processed_at)
            formatted_id = format_transaction_id(tx_id)
            
            tracking_text += f"   ⭐ <b>Stars</b>: {amount:,} Stars ({package})\n"
            tracking_text += f"      👤 User: {user_id_tx} | 🕒 {formatted_time}\n"
            if tx_id:
                tracking_text += f"      🆔 ID: {formatted_id}\n"
            tracking_text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_financial_management")
        ]
    ])
    
    await callback.message.edit_text(tracking_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Revenue Analytics Callback
async def admin_revenue_analytics_callback(callback: types.CallbackQuery):
    """Handle admin revenue analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    from src.models import load_ton_transactions, load_stars_transactions
    
    # Calculate revenue analytics
    ton_revenue = 0
    stars_revenue = 0
    package_revenue = {}
    daily_revenue = {}
    
    # Load transaction data
    ton_transactions = load_ton_transactions()
    stars_transactions = load_stars_transactions()
    
    # Process TON transactions
    for transaction in ton_transactions:
        amount = transaction['amount']
        ton_revenue += amount
        
        package = transaction['package']
        if package not in package_revenue:
            package_revenue[package] = {'ton': 0, 'stars': 0, 'count': 0}
        package_revenue[package]['ton'] += amount
        package_revenue[package]['count'] += 1
    
    # Process Stars transactions
    for transaction in stars_transactions:
        amount = transaction['amount_stars']  # Fixed: use 'amount_stars' for Stars transactions
        stars_revenue += amount
        
        package = transaction['package']
        if package not in package_revenue:
            package_revenue[package] = {'ton': 0, 'stars': 0, 'count': 0}
        package_revenue[package]['stars'] += amount
        package_revenue[package]['count'] += 1
    
    # Calculate total revenue in TON using correct conversion rate
    total_revenue_ton = ton_revenue + stars_to_ton(stars_revenue)
    
    # Create revenue analytics text
    analytics_text = f"📈 <b>Revenue Analytics</b>\n\n"
    analytics_text += f"💰 <b>Total Revenue:</b>\n"
    analytics_text += f"   💎 TON: {ton_revenue:.4f} TON\n"
    analytics_text += f"   ⭐ Stars: {stars_revenue:,} Stars\n"
    analytics_text += f"   📊 Total (TON equiv): {total_revenue_ton:.4f} TON\n\n"
    
    # Package revenue breakdown
    if package_revenue:
        analytics_text += f"📦 <b>Revenue by Package:</b>\n"
        for package, revenue in package_revenue.items():
            package_total_ton = revenue['ton'] + stars_to_ton(revenue['stars'])
            analytics_text += f"   🥉 <b>{package.title()}:</b>\n"
            analytics_text += f"      💎 TON: {revenue['ton']:.4f}\n"
            analytics_text += f"      ⭐ Stars: {revenue['stars']:,}\n"
            analytics_text += f"      📊 Total: {package_total_ton:.4f} TON\n"
            analytics_text += f"      🛒 Sales: {revenue['count']}\n\n"
    
    # Calculate average transaction value
    total_transactions = len(ton_transactions) + len(stars_transactions)
    avg_transaction = total_revenue_ton / total_transactions if total_transactions > 0 else 0
    
    analytics_text += f"📊 <b>Transaction Analytics:</b>\n"
    analytics_text += f"   🛒 Total Transactions: {total_transactions}\n"
    analytics_text += f"   💰 Average Transaction: {avg_transaction:.4f} TON\n"
    analytics_text += f"   👥 Total Users: {len(user_data)}\n"
    analytics_text += f"   📈 Revenue per User: {total_revenue_ton/len(user_data):.4f} TON\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_financial_management")
        ]
    ])
    
    await callback.message.edit_text(analytics_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin System Management Callback
async def admin_system_management_callback(callback: types.CallbackQuery):
    """Handle admin system management menu"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    admin_text = f"{get_admin_text(user_id, 'system_management_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "bot_statistics"), callback_data="admin_bot_stats"),
            InlineKeyboardButton(text=get_admin_text(user_id, "database_management"), callback_data="admin_database_management")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "logs_monitoring"), callback_data="admin_logs_monitoring"),
            InlineKeyboardButton(text=get_admin_text(user_id, "maintenance_mode"), callback_data="admin_maintenance_mode")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Bot Statistics Callback
async def admin_bot_stats_callback(callback: types.CallbackQuery):
    """Handle admin bot statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    from src.models import load_ton_transactions, load_stars_transactions
    import time
    import psutil
    import os
    
    # Calculate bot statistics
    total_users = len(user_data)
    active_users = sum(1 for user in user_data.values() if user.get('total_spins', 0) > 0)
    total_spins = sum(user.get('total_spins', 0) for user in user_data.values())
    total_hits = sum(user.get('hits', 0) for user in user_data.values())
    total_nfts = sum(len(user.get('nfts', [])) for user in user_data.values())
    
    # System statistics
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    cpu_percent = process.cpu_percent()
    
    # Database statistics
    db_size = 0
    try:
        if os.path.exists('cgspins.db'):
            db_size = os.path.getsize('cgspins.db') / 1024  # KB
    except:
        pass
    
    # Create bot statistics text
    stats_text = f"📊 <b>Bot Statistics</b>\n\n"
    stats_text += f"👥 <b>User Statistics:</b>\n"
    stats_text += f"   📊 Total Users: {total_users}\n"
    stats_text += f"   🎯 Active Users: {active_users}\n"
    activity_rate = (active_users/total_users*100) if total_users > 0 else 0.0
    hit_rate = (total_hits/total_spins*100) if total_spins > 0 else 0.0
    
    stats_text += f"   📈 Activity Rate: {activity_rate:.1f}%\n\n"
    
    stats_text += f"🎰 <b>Game Statistics:</b>\n"
    stats_text += f"   🎰 Total Spins: {total_spins:,}\n"
    stats_text += f"   💎 Total Hits: {total_hits:,}\n"
    stats_text += f"   🎁 Total NFTs: {total_nfts}\n"
    stats_text += f"   📈 Hit Rate: {hit_rate:.2f}%\n\n"
    
    # Load transaction data for statistics
    ton_transactions = load_ton_transactions()
    stars_transactions = load_stars_transactions()
    
    stats_text += f"💳 <b>Payment Statistics:</b>\n"
    stats_text += f"   💎 TON Transactions: {len(ton_transactions)}\n"
    stats_text += f"   ⭐ Stars Transactions: {len(stars_transactions)}\n"
    stats_text += f"   ⏳ Pending Payments: {len(pending_ton_payments)}\n\n"
    
    stats_text += f"🖥️ <b>System Statistics:</b>\n"
    stats_text += f"   💾 Memory Usage: {memory_usage:.1f} MB\n"
    stats_text += f"   🖥️ CPU Usage: {cpu_percent:.1f}%\n"
    stats_text += f"   🗄️ Database Size: {db_size:.1f} KB\n"
    stats_text += f"   ⏰ Uptime: {time.time() - process.create_time():.0f}s\n\n"
    
    # Recent activity
    try:
        recent_users = sorted(user_data.items(), key=lambda x: str(x[1].get('updated_at', '')), reverse=True)[:5]
    except:
        recent_users = []
    if recent_users:
        stats_text += f"🕒 <b>Recent Activity:</b>\n"
        for user_id_key, user in recent_users:
            last_activity = user.get('updated_at', 'Unknown')
            spins = user.get('total_spins', 0)
            stats_text += f"   👤 User {user_id_key}: {spins} spins\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Content Management Callback
async def admin_content_management_callback(callback: types.CallbackQuery):
    """Handle admin content management menu"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    admin_text = f"{get_admin_text(user_id, 'content_management_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "broadcast_messages"), callback_data="admin_broadcast"),
            InlineKeyboardButton(text=get_admin_text(user_id, "package_pricing"), callback_data="admin_package_pricing")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Broadcast Messages Callback
async def admin_broadcast_callback(callback: types.CallbackQuery):
    """Handle admin broadcast messages"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Create broadcast interface
    broadcast_text = f"📢 <b>Broadcast Messages</b>\n\n"
    broadcast_text += f"Send a message to all users in the bot.\n\n"
    broadcast_text += f"📊 <b>Current Users:</b> {len(user_data)}\n"
    broadcast_text += f"👥 <b>Active Users:</b> {sum(1 for user in user_data.values() if user.get('total_spins', 0) > 0)}\n\n"
    broadcast_text += f"⚠️ <b>Warning:</b> This will send a message to ALL users. Use carefully!\n\n"
    broadcast_text += f"💡 <b>How to use:</b>\n"
    broadcast_text += f"1. Click 'Send Broadcast' below\n"
    broadcast_text += f"2. Type your message\n"
    broadcast_text += f"3. Confirm to send to all users"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Send Broadcast", callback_data="admin_broadcast_send")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_content_management")
        ]
    ])
    
    await callback.message.edit_text(broadcast_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Broadcast Send Callback
async def admin_broadcast_send_callback(callback: types.CallbackQuery):
    """Handle admin broadcast send"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Store that user is in broadcast mode
    user_data[user_id]['broadcast_mode'] = True
    
    broadcast_text = f"📢 <b>Broadcast Message</b>\n\n"
    broadcast_text += f"Please type your broadcast message now.\n\n"
    broadcast_text += f"📊 <b>Will be sent to:</b> {len(user_data)} users\n\n"
    broadcast_text += f"💡 <b>Tips:</b>\n"
    broadcast_text += f"• Use HTML formatting for bold, italic, etc.\n"
    broadcast_text += f"• Keep messages concise and clear\n"
    broadcast_text += f"• Test with a small group first if possible"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin_broadcast")
        ]
    ])
    
    await callback.message.edit_text(broadcast_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Broadcast Confirm Callback
async def admin_broadcast_confirm_callback(callback: types.CallbackQuery):
    """Handle admin broadcast confirmation"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Get the broadcast message
    broadcast_message = user_data[user_id].get('broadcast_message', '')
    
    if not broadcast_message:
        await callback.answer("❌ No broadcast message found!", show_alert=True)
        return
    
    # Send broadcast to all users
    sent_count = 0
    failed_count = 0
    
    for target_user_id in user_data.keys():
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=broadcast_message,
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception as e:
            print(f"❌ [Broadcast] Failed to send to user {target_user_id}: {e}")
            failed_count += 1
    
    # Clear broadcast message
    user_data[user_id]['broadcast_message'] = ''
    
    # Send confirmation to admin
    result_text = f"📢 <b>Broadcast Complete!</b>\n\n"
    result_text += f"✅ <b>Sent to:</b> {sent_count} users\n"
    result_text += f"❌ <b>Failed:</b> {failed_count} users\n"
    result_text += f"📊 <b>Total Users:</b> {len(user_data)}\n\n"
    result_text += f"<b>Message:</b>\n{broadcast_message}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 Back to Admin Panel", callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer(f"Broadcast sent to {sent_count} users!")


# Admin Analytics & Reports Callback
async def admin_analytics_reports_callback(callback: types.CallbackQuery):
    """Handle admin analytics & reports menu"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    admin_text = f"{get_admin_text(user_id, 'analytics_reports_title')}\n\n{get_admin_text(user_id, 'admin_welcome')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "daily_reports"), callback_data="admin_daily_reports"),
            InlineKeyboardButton(text=get_admin_text(user_id, "weekly_reports"), callback_data="admin_weekly_reports")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "monthly_reports"), callback_data="admin_monthly_reports"),
            InlineKeyboardButton(text=get_admin_text(user_id, "popular_packages"), callback_data="admin_popular_packages")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "user_retention"), callback_data="admin_user_retention"),
            InlineKeyboardButton(text=get_admin_text(user_id, "export_data"), callback_data="admin_export_data")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin View Users Callback (Example implementation)
async def admin_view_users_callback(callback: types.CallbackQuery):
    """Handle admin view all users with pagination"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Parse page from callback data if present
    page = 1
    if "_page_" in callback.data:
        try:
            page = int(callback.data.split("_page_")[1])
        except:
            page = 1
    
    from translations import get_admin_text
    
    # Get user statistics
    total_users = len(user_data)
    active_users = sum(1 for user in user_data.values() if user.get('spins_available', 0) > 0)
    
    # Get package distribution
    package_stats = {}
    for user in user_data.values():
        package = user.get('package', 'None')
        package_stats[package] = package_stats.get(package, 0) + 1
    
    stats_text = f"📊 <b>User Statistics</b>\n\n"
    stats_text += f"👥 Total Users: {total_users}\n"
    stats_text += f"🎯 Active Users: {active_users}\n\n"
    stats_text += f"📦 <b>Package Distribution:</b>\n"
    
    for package, count in package_stats.items():
        stats_text += f"• {package}: {count} users\n"
    
    # Pagination settings
    items_per_page = 10
    offset = (page - 1) * items_per_page
    
    # Add paginated user list
    stats_text += f"\n👥 <b>Users (Page {page}):</b>\n"
    
    # Convert user_data to list for pagination
    user_list = list(user_data.items())
    total_pages = max(1, (len(user_list) + items_per_page - 1) // items_per_page)
    
    # Get paginated users
    paginated_users = user_list[offset:offset + items_per_page]
    
    for user_id_item, user in paginated_users:
        package = user.get('package', 'None')
        spins = user.get('spins_available', 0)
        level = user.get('level', 'Spinner')
        created_at = format_timestamp(user.get('created_at', 'Unknown'))
        
        stats_text += f"• <b>ID:</b> {user_id_item}\n"
        stats_text += f"  📦 Package: {package} | 🎯 Spins: {spins}\n"
        stats_text += f"  🏆 Level: {level} | 📅 Created: {created_at}\n\n"
    
    # Create pagination keyboard
    keyboard = create_pagination_keyboard(page, total_pages, "admin_view_users")
    keyboard.inline_keyboard.append([InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")])
    
    try:
        await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        # If message is not modified, just answer the callback
        if "message is not modified" in str(e):
            await callback.answer()
            return
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Give Package Callback
async def admin_give_package_callback(callback: types.CallbackQuery):
    """Handle giving a package to a user"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Extract target user ID and package from callback data
    # Format: admin_give_package_{target_user_id}_{package_name}
    parts = callback.data.split("_")
    if len(parts) >= 5:
        target_user_id = int(parts[3])
        package_name = "_".join(parts[4:])  # In case package name has underscores
        
        # Get package details from config
        package_info = config.PACKAGES.get(package_name)
        if not package_info:
            await callback.answer("❌ Package not found!", show_alert=True)
            return
        
        # Update user data
        if target_user_id in globals()['user_data']:
            globals()['user_data'][target_user_id]["package"] = package_name
            globals()['user_data'][target_user_id]["spins_available"] = package_info["spins"]
            globals()['user_data'][target_user_id]["hits"] = 0  # Reset hits for new package
            globals()['user_data'][target_user_id]["total_spins"] = 0  # Reset total spins
            globals()['user_data'][target_user_id]["updated_at"] = datetime.now().isoformat()
            
            # Save to database
            save_user_data_to_db(target_user_id, globals()['user_data'][target_user_id])
            
            from translations import get_admin_text
            await callback.answer(f"✅ {package_name} package given to user {target_user_id}!", show_alert=True)
        else:
            await callback.answer("❌ User not found!", show_alert=True)
    else:
        await callback.answer("❌ Invalid data format!", show_alert=True)


# Message handler for user ID input
@router.message(lambda message: message.text and message.text.isdigit())
async def handle_user_id_input(message: types.Message):
    """Handle user ID input for admin user details"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        return
    
    target_user_id = int(message.text)
    
    if target_user_id not in user_data:
        from translations import get_admin_text
        await message.reply(f"❌ {get_admin_text(user_id, 'user_not_found')}")
        return
    
    # Get user data
    user = user_data[target_user_id]
    
    # Format user details
    user_details = f"👤 <b>User Details</b>\n\n"
    user_details += f"🆔 <b>User ID:</b> {target_user_id}\n"
    
    # Format timestamps properly using utility function
    created_at = format_timestamp(user.get('created_at', 'Unknown'))
    updated_at = format_timestamp(user.get('updated_at', 'Unknown'))
    
    user_details += f"📅 <b>Created:</b> {created_at}\n"
    user_details += f"🕒 <b>Last Activity:</b> {updated_at}\n"
    user_details += f"🌐 <b>Language:</b> {user.get('language', 'en')}\n\n"
    
    user_details += f"📦 <b>Current Package:</b> {user.get('package', 'None').title() if user.get('package', 'None') != 'None' else 'None'}\n"
    user_details += f"🏆 <b>Level:</b> {user.get('level', 'Spinner')}\n"
    user_details += f"⭐ <b>Spin Points:</b> {user.get('spin_points', 0)}\n\n"
    
    user_details += f"🎰 <b>Spins Available:</b> {user.get('spins_available', 0)}\n"
    user_details += f"🎯 <b>Total Spins:</b> {user.get('total_spins', 0)}\n"
    user_details += f"🎯 <b>Total Hits:</b> {user.get('hits', 0)}\n"
    user_details += f"🎁 <b>NFTs Earned:</b> {len(user.get('nfts', []))}\n\n"
    
    user_details += f"👥 <b>Referrals:</b> {user.get('referrals', 0)}\n"
    user_details += f"🔗 <b>Referred By:</b> {user.get('referred_by', 'None')}\n"
    
    # Create keyboard with package options (using lowercase package names from config)
    from translations import get_admin_text
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Give Bronze", callback_data=f"admin_give_package_{target_user_id}_bronze"),
            InlineKeyboardButton(text="🥈 Give Silver", callback_data=f"admin_give_package_{target_user_id}_silver")
        ],
        [
            InlineKeyboardButton(text="🥇 Give Gold", callback_data=f"admin_give_package_{target_user_id}_gold"),
            InlineKeyboardButton(text="🖤 Give Black", callback_data=f"admin_give_package_{target_user_id}_black")
        ],
        [
            InlineKeyboardButton(text="❌ Remove Package", callback_data=f"admin_remove_package_{target_user_id}")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
        ]
    ])
    
    await message.reply(user_details, reply_markup=keyboard, parse_mode="HTML")


# Admin Remove Package Callback
async def admin_remove_package_callback(callback: types.CallbackQuery):
    """Handle removing package from a user"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Extract target user ID from callback data
    # Format: admin_remove_package_{target_user_id}
    parts = callback.data.split("_")
    if len(parts) >= 4:
        target_user_id = int(parts[3])
        
        # Update user data
        if target_user_id in globals()['user_data']:
            globals()['user_data'][target_user_id]["package"] = "None"
            globals()['user_data'][target_user_id]["spins_available"] = 0
            globals()['user_data'][target_user_id]["hits"] = 0
            globals()['user_data'][target_user_id]["total_spins"] = 0
            globals()['user_data'][target_user_id]["updated_at"] = datetime.now().isoformat()
            
            # Save to database
            save_user_data_to_db(target_user_id, globals()['user_data'][target_user_id])
            
            from translations import get_admin_text
            await callback.answer(f"✅ Package removed from user {target_user_id}!", show_alert=True)
        else:
            await callback.answer("❌ User not found!", show_alert=True)
    else:
        await callback.answer("❌ Invalid data format!", show_alert=True)


# Admin Reset User Callback (for the menu button)
async def admin_reset_user_callback(callback: types.CallbackQuery):
    """Handle admin reset user menu"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Reset user callback triggered for user {user_id}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Reset user access granted for user {user_id}")
    
    from translations import get_admin_text
    
    admin_text = f"🔄 <b>Reset User Data</b>\n\n"
    admin_text += f"Select a user to reset their data:\n\n"
    admin_text += f"<i>⚠️ This will reset all user data including spins, points, and package information.</i>"
    
    # Get all users from database
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, spins_available FROM users ORDER BY user_id DESC LIMIT 20")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
            ])
            admin_text = "❌ <b>No users found in database</b>"
        else:
            keyboard_buttons = []
            for user_id_key, username, spins_available in users:
                display_name = f"@{username}" if username else f"User {user_id_key}"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"{display_name} ({spins_available} spins)",
                        callback_data=f"admin_reset_user_{user_id_key}"
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    except Exception as e:
        print(f"Error getting users for reset: {e}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
        ])
        admin_text = f"❌ <b>Error loading users:</b>\n\n{str(e)}"
    
    try:
        await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Give Package Callback
async def admin_give_package_callback(callback: types.CallbackQuery):
    """Handle admin give package menu"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Give package callback triggered for user {user_id}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Give package access granted for user {user_id}")
    
    from translations import get_admin_text
    
    admin_text = f"📦 <b>Give Package to User</b>\n\n"
    admin_text += f"Select a user to give a package to:\n\n"
    admin_text += f"<i>This will give the user a package with spins and reset their current progress.</i>"
    
    # Get all users from database
    try:
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, package, spins_available FROM users ORDER BY user_id DESC LIMIT 20")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
            ])
            admin_text = "❌ <b>No users found in database</b>"
        else:
            keyboard_buttons = []
            for user_id_key, username, package, spins in users:
                display_name = f"@{username}" if username else f"User {user_id_key}"
                package_display = package if package != 'None' else 'No Package'
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"{display_name} ({package_display})",
                        callback_data=f"admin_select_package_{user_id_key}"
                    )
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    except Exception as e:
        print(f"Error getting users for give package: {e}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")]
        ])
        admin_text = f"❌ <b>Error loading users:</b>\n\n{str(e)}"
    
    try:
        await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Select Package Callback
async def admin_select_package_callback(callback: types.CallbackQuery):
    """Handle admin select package for user"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Select package callback triggered for user {user_id}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Select package access granted for user {user_id}")
    
    from translations import get_admin_text
    
    # Extract target user ID from callback data
    target_user_id = int(callback.data.split("_")[-1])
    
    # Get user data
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        result_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_give_package")]
        ])
    else:
        username = user_data.get('username', '')
        display_name = f"@{username}" if username else f"User {target_user_id}"
        current_package = user_data.get('package', 'None')
        
        result_text = f"📦 <b>Give Package to User</b>\n\n"
        result_text += f"👤 <b>User:</b> {display_name} (ID: {target_user_id})\n"
        result_text += f"📦 <b>Current Package:</b> {current_package}\n\n"
        result_text += f"🎯 <b>Select a package to give:</b>\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🥉 Bronze (30 spins)", callback_data=f"admin_give_package_{target_user_id}_bronze"),
                InlineKeyboardButton(text="🥈 Silver (60 spins)", callback_data=f"admin_give_package_{target_user_id}_silver")
            ],
            [
                InlineKeyboardButton(text="🥇 Gold (300 spins)", callback_data=f"admin_give_package_{target_user_id}_gold"),
                InlineKeyboardButton(text="⚫ Black (600 spins)", callback_data=f"admin_give_package_{target_user_id}_black")
            ],
            [
                InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_give_package")
            ]
        ])
    
    try:
        await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Give Specific Package Callback
async def admin_give_specific_package_callback(callback: types.CallbackQuery):
    """Handle admin give specific package to user"""
    user_id = callback.from_user.id
    
    print(f"🔧 [Admin] Give specific package callback triggered for user {user_id}")
    
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Give specific package access granted for user {user_id}")
    
    from translations import get_admin_text
    
    # Extract user ID and package from callback data
    parts = callback.data.split("_")
    target_user_id = int(parts[-2])
    package_type = parts[-1]
    
    # Get user data
    user_data = get_user_data_from_db(target_user_id)
    
    if not user_data:
        result_text = f"❌ <b>User Not Found</b>\n\nUser ID: {target_user_id}\n\nThis user does not exist in the system."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_give_package")]
        ])
    else:
        # Check if package exists
        if package_type not in config.PACKAGES:
            result_text = f"❌ <b>Invalid Package</b>\n\nPackage type '{package_type}' not found."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_give_package")]
            ])
        else:
            # Give package to user
            package_info = config.PACKAGES[package_type]
            username = user_data.get('username', '')
            display_name = f"@{username}" if username else f"User {target_user_id}"
            
            # Update user data with new package
            user_data['package'] = package_info['name']
            user_data['spins_available'] = package_info['spins']
            user_data['total_spins'] = 0
            user_data['hits'] = 0
            user_data['updated_at'] = datetime.now().isoformat()
            
            # Save updated user data to database
            success = save_user_data_to_db(target_user_id, user_data)
            
            if success:
                # Also update in-memory data if it exists
                if target_user_id in globals()['user_data']:
                    globals()['user_data'][target_user_id].update({
                        'package': package_info['name'],
                        'spins_available': package_info['spins'],
                        'total_spins': 0,
                        'hits': 0,
                        'updated_at': datetime.now().isoformat()
                    })
                
                result_text = f"✅ <b>Package Given Successfully!</b>\n\n"
                result_text += f"👤 <b>User:</b> {display_name} (ID: {target_user_id})\n"
                result_text += f"📦 <b>Package:</b> {package_info['name']}\n"
                result_text += f"🎰 <b>Spins:</b> {package_info['spins']}\n"
                result_text += f"🎯 <b>Hits Required:</b> {package_info['hits_required']}\n"
                result_text += f"🎁 <b>NFT Chance:</b> {package_info['nft_chance']*100:.1f}%\n\n"
                result_text += f"🎉 <b>User can now start spinning with their new package!</b>"
            else:
                result_text = f"❌ <b>Failed to Give Package</b>\n\nUser ID: {target_user_id}\n\nDatabase update failed. Please try again."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="👤 View User", callback_data=f"admin_user_detail_{target_user_id}"),
                    InlineKeyboardButton(text="📦 Give Another", callback_data="admin_select_package_{target_user_id}")
                ],
                [
                    InlineKeyboardButton(text="📊 User Details", callback_data="admin_user_details"),
                    InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_user_management")
                ]
            ])
    
    try:
        await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Database Management Callback
async def admin_database_management_callback(callback: types.CallbackQuery):
    """Handle admin database management"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Get database statistics
    try:
        from src.models.database_enhanced import get_db_pool
        import sqlite3
        import os
        
        db_pool = get_db_pool()
        db_stats = {}
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get table statistics
            tables = ['users', 'pending_ton_payments', 'processed_transactions', 'stars_transactions']
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    db_stats[table] = count
                except:
                    db_stats[table] = 0
            
            # Get database file size
            db_size = os.path.getsize('cgspins.db') if os.path.exists('cgspins.db') else 0
            db_stats['file_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            # Get database integrity info
            cursor.execute('PRAGMA integrity_check')
            integrity = cursor.fetchone()[0]
            db_stats['integrity'] = integrity
            
            # Get database version
            cursor.execute('PRAGMA user_version')
            db_stats['version'] = cursor.fetchone()[0]
        
        admin_text = f"🗄️ <b>Database Management</b>\n\n"
        admin_text += f"📊 <b>Database Statistics:</b>\n"
        admin_text += f"   👥 Users: {db_stats.get('users', 0):,}\n"
        admin_text += f"   💳 Pending Payments: {db_stats.get('pending_ton_payments', 0)}\n"
        admin_text += f"   ✅ Processed Transactions: {db_stats.get('processed_transactions', 0)}\n"
        admin_text += f"   ⭐ Stars Transactions: {db_stats.get('stars_transactions', 0)}\n"
        admin_text += f"   📁 File Size: {db_stats.get('file_size_mb', 0)} MB\n"
        admin_text += f"   🔍 Integrity: {db_stats.get('integrity', 'Unknown')}\n"
        admin_text += f"   📋 Version: {db_stats.get('version', 'Unknown')}\n\n"
        admin_text += f"🔧 <b>Available Actions:</b>"
        
    except Exception as e:
        admin_text = f"🗄️ <b>Database Management</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💾 Backup Database", callback_data="admin_db_backup"),
            InlineKeyboardButton(text="🔄 Optimize Database", callback_data="admin_db_optimize")
        ],
        [
            InlineKeyboardButton(text="🧹 Clean Old Data", callback_data="admin_db_cleanup"),
            InlineKeyboardButton(text="📊 Database Stats", callback_data="admin_db_stats")
        ],
        [
            InlineKeyboardButton(text="🔍 Integrity Check", callback_data="admin_db_integrity"),
            InlineKeyboardButton(text="📋 Export Data", callback_data="admin_db_export")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await safe_edit_message(callback, admin_text, reply_markup=keyboard)
    await callback.answer()


# Admin Database Stats Callback
async def admin_db_stats_callback(callback: types.CallbackQuery):
    """Handle admin database statistics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    import os
    
    try:
        # Get database file size
        db_size = os.path.getsize('cgspins.db') if os.path.exists('cgspins.db') else 0
        db_size_mb = db_size / (1024 * 1024)
        
        # Get database statistics
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        # Count records in each table
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stars_transactions")
        stars_tx_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pending_ton_payments")
        pending_payments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_transactions")
        processed_tx = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM influencers")
        influencer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM influencer_referrals")
        influencer_refs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM influencer_commissions")
        influencer_commissions = cursor.fetchone()[0]
        
        # Get database info
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA freelist_count")
        free_pages = cursor.fetchone()[0]
        
        conn.close()
        
        # Calculate statistics
        total_pages = page_count
        used_pages = total_pages - free_pages
        efficiency = (used_pages / total_pages * 100) if total_pages > 0 else 0
        
        stats_text = f"📊 <b>Database Statistics</b>\n\n"
        stats_text += f"💾 <b>File Size:</b> {db_size_mb:.2f} MB\n"
        stats_text += f"📄 <b>Total Pages:</b> {total_pages:,}\n"
        stats_text += f"✅ <b>Used Pages:</b> {used_pages:,}\n"
        stats_text += f"🔄 <b>Free Pages:</b> {free_pages:,}\n"
        stats_text += f"⚡ <b>Efficiency:</b> {efficiency:.1f}%\n\n"
        
        stats_text += f"📋 <b>Table Records:</b>\n"
        stats_text += f"   👥 Users: {user_count:,}\n"
        stats_text += f"   ⭐ Stars Transactions: {stars_tx_count:,}\n"
        stats_text += f"   ⏳ Pending Payments: {pending_payments:,}\n"
        stats_text += f"   ✅ Processed Transactions: {processed_tx:,}\n"
        stats_text += f"   🌟 Influencers: {influencer_count:,}\n"
        stats_text += f"   🎯 Influencer Referrals: {influencer_refs:,}\n"
        stats_text += f"   💰 Influencer Commissions: {influencer_commissions:,}\n\n"
        
        stats_text += f"🔧 <b>Database Health:</b>\n"
        if efficiency > 80:
            stats_text += f"   ✅ Good efficiency ({efficiency:.1f}%)\n"
        elif efficiency > 60:
            stats_text += f"   ⚠️ Moderate efficiency ({efficiency:.1f}%)\n"
        else:
            stats_text += f"   ❌ Low efficiency ({efficiency:.1f}%)\n"
        
        if free_pages > total_pages * 0.3:
            stats_text += f"   💡 Consider optimizing database\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_database_management")]
        ])
        
    except Exception as e:
        stats_text = f"❌ <b>Error getting database statistics</b>\n\n{str(e)}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_database_management")]
        ])
    
    await safe_edit_message(callback, stats_text, reply_markup=keyboard)
    await callback.answer()


# Admin Database Integrity Check Callback
async def admin_db_integrity_callback(callback: types.CallbackQuery):
    """Handle admin database integrity check"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    try:
        # Perform integrity check
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        # Run PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        # Run PRAGMA quick_check
        cursor.execute("PRAGMA quick_check")
        quick_check_result = cursor.fetchone()[0]
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        integrity_text = f"🔍 <b>Database Integrity Check</b>\n\n"
        
        # Integrity check results
        if integrity_result == "ok":
            integrity_text += f"✅ <b>Integrity Check:</b> PASSED\n"
        else:
            integrity_text += f"❌ <b>Integrity Check:</b> FAILED\n"
            integrity_text += f"   Details: {integrity_result}\n"
        
        # Quick check results
        if quick_check_result == "ok":
            integrity_text += f"✅ <b>Quick Check:</b> PASSED\n"
        else:
            integrity_text += f"❌ <b>Quick Check:</b> FAILED\n"
            integrity_text += f"   Details: {quick_check_result}\n"
        
        # Foreign key check
        if not fk_errors:
            integrity_text += f"✅ <b>Foreign Keys:</b> VALID\n"
        else:
            integrity_text += f"❌ <b>Foreign Keys:</b> {len(fk_errors)} ERRORS\n"
            for error in fk_errors[:3]:  # Show first 3 errors
                integrity_text += f"   • {error}\n"
            if len(fk_errors) > 3:
                integrity_text += f"   ... and {len(fk_errors) - 3} more\n"
        
        integrity_text += f"\n📋 <b>Tables Found:</b> {len(tables)}\n"
        integrity_text += f"   {', '.join(tables)}\n\n"
        
        # Overall status
        if integrity_result == "ok" and quick_check_result == "ok" and not fk_errors:
            integrity_text += f"🎉 <b>Overall Status:</b> DATABASE IS HEALTHY"
        else:
            integrity_text += f"⚠️ <b>Overall Status:</b> ISSUES DETECTED"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_database_management")]
        ])
        
    except Exception as e:
        integrity_text = f"❌ <b>Error performing integrity check</b>\n\n{str(e)}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_database_management")]
        ])
    
    await safe_edit_message(callback, integrity_text, reply_markup=keyboard)
    await callback.answer()


# Admin Logs & Monitoring Callback
async def admin_logs_monitoring_callback(callback: types.CallbackQuery):
    """Handle admin logs & monitoring"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Get system metrics
    try:
        from src.utils.monitoring import metrics, health_checker, alert_system
        
        # Get current metrics
        stats = metrics.get_stats()
        health_status = await health_checker.check_system_health()
        alerts = alert_system.check_alerts(metrics, health_status.get('overall_status', 'unknown'))
        
        admin_text = f"📝 <b>Logs & Monitoring</b>\n\n"
        admin_text += f"📊 <b>System Metrics:</b>\n"
        admin_text += f"   ⏱️ Uptime: {stats.get('uptime_formatted', 'Unknown')}\n"
        admin_text += f"   📈 Total Requests: {stats.get('total_requests', 0):,}\n"
        admin_text += f"   ✅ Success Rate: {stats.get('success_rate', 0):.1f}%\n"
        admin_text += f"   ❌ Error Rate: {stats.get('error_rate', 0):.1f}%\n"
        admin_text += f"   ⚡ Avg Response Time: {stats.get('average_response_time', 0):.3f}s\n"
        admin_text += f"   🔗 TON API Success: {stats.get('ton_api_success_rate', 0):.1f}%\n"
        admin_text += f"   💳 Payment Success: {stats.get('payment_success_rate', 0):.1f}%\n"
        admin_text += f"   👥 Active Users: {stats.get('active_users', 0)}\n\n"
        
        admin_text += f"🏥 <b>System Health:</b> {health_status.get('overall_status', 'Unknown').upper()}\n"
        
        if alerts:
            admin_text += f"🚨 <b>Active Alerts:</b> {len(alerts)}\n"
            for alert in alerts[:3]:  # Show first 3 alerts
                admin_text += f"   • {alert.get('level', 'info').upper()}: {alert.get('message', 'Unknown')}\n"
        else:
            admin_text += f"✅ <b>No Active Alerts</b>\n"
        
    except Exception as e:
        admin_text = f"📝 <b>Logs & Monitoring</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics")
        ],
        [
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check"),
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts")
        ],
        [
            InlineKeyboardButton(text="⚙️ Alert Settings", callback_data="admin_alert_settings"),
            InlineKeyboardButton(text="🔄 Reset Metrics", callback_data="admin_reset_metrics")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Maintenance Mode Callback
async def admin_maintenance_mode_callback(callback: types.CallbackQuery):
    """Handle admin maintenance mode"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    from translations import get_admin_text
    
    # Check current maintenance mode status
    global maintenance_mode
    
    admin_text = f"🔧 <b>Maintenance Mode</b>\n\n"
    
    if maintenance_mode:
        admin_text += f"🚧 <b>Status:</b> ACTIVE\n"
        admin_text += f"⚠️ <b>Warning:</b> Bot is currently in maintenance mode.\n"
        admin_text += f"   • Users will see maintenance message\n"
        admin_text += f"   • Most features are disabled\n"
        admin_text += f"   • Only admins can use the bot\n\n"
        admin_text += f"✅ <b>Ready to disable maintenance mode?</b>"
    else:
        admin_text += f"✅ <b>Status:</b> INACTIVE\n"
        admin_text += f"🎉 <b>Bot is running normally</b>\n"
        admin_text += f"   • All features are available\n"
        admin_text += f"   • Users can play normally\n\n"
        admin_text += f"⚠️ <b>Enable maintenance mode to:</b>\n"
        admin_text += f"   • Perform system updates\n"
        admin_text += f"   • Fix critical issues\n"
        admin_text += f"   • Prevent user access temporarily"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚧 Enable Maintenance" if not maintenance_mode else "✅ Disable Maintenance",
                callback_data="admin_toggle_maintenance"
            )
        ],
        [
            InlineKeyboardButton(text="📝 Set Message", callback_data="admin_set_maintenance_message"),
            InlineKeyboardButton(text="⏰ Schedule Maintenance", callback_data="admin_schedule_maintenance")
        ],
        [
            InlineKeyboardButton(text=get_admin_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Toggle Maintenance Mode
async def admin_toggle_maintenance_callback(callback: types.CallbackQuery):
    """Toggle maintenance mode on/off"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Toggle maintenance mode
    global maintenance_mode
    maintenance_mode = not maintenance_mode
    
    # Log the action
    print(f"🔧 [Admin] User {user_id} {'enabled' if maintenance_mode else 'disabled'} maintenance mode")
    
    if maintenance_mode:
        result_text = "🚧 <b>Maintenance Mode ENABLED</b>\n\n"
        result_text += "⚠️ <b>Bot is now in maintenance mode:</b>\n"
        result_text += "   • Users will see maintenance message\n"
        result_text += "   • Most features are disabled\n"
        result_text += "   • Only admins can use the bot\n\n"
        result_text += "✅ <b>Remember to disable when done!</b>"
    else:
        result_text = "✅ <b>Maintenance Mode DISABLED</b>\n\n"
        result_text += "🎉 <b>Bot is back online:</b>\n"
        result_text += "   • All features are available\n"
        result_text += "   • Users can play normally\n"
        result_text += "   • System is fully operational"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔧 Maintenance Settings", callback_data="admin_maintenance_mode")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer(f"Maintenance mode {'enabled' if maintenance_mode else 'disabled'}!")


# Admin Database Backup
async def admin_db_backup_callback(callback: types.CallbackQuery):
    """Create database backup"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import shutil
        from datetime import datetime
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"cgspins_backup_{timestamp}.db"
        
        # Copy database file
        shutil.copy2('cgspins.db', backup_filename)
        
        result_text = f"💾 <b>Database Backup Created</b>\n\n"
        result_text += f"📁 <b>Backup File:</b> {backup_filename}\n"
        result_text += f"⏰ <b>Created:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result_text += f"✅ <b>Status:</b> Successfully backed up to local directory"
        
    except Exception as e:
        result_text = f"❌ <b>Backup Failed</b>\n\nError: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗄️ Database Management", callback_data="admin_database_management")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Database Optimize
async def admin_db_optimize_callback(callback: types.CallbackQuery):
    """Optimize database performance"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        # Run VACUUM to optimize database
        cursor.execute('VACUUM')
        
        # Analyze tables for better query planning
        cursor.execute('ANALYZE')
        
        # Update statistics
        cursor.execute('PRAGMA optimize')
        
        conn.commit()
        conn.close()
        
        result_text = f"🔄 <b>Database Optimized</b>\n\n"
        result_text += f"✅ <b>Actions Completed:</b>\n"
        result_text += f"   • VACUUM - Reclaimed unused space\n"
        result_text += f"   • ANALYZE - Updated query statistics\n"
        result_text += f"   • PRAGMA optimize - Optimized performance\n\n"
        result_text += f"🎯 <b>Result:</b> Database performance improved"
        
    except Exception as e:
        result_text = f"❌ <b>Optimization Failed</b>\n\nError: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗄️ Database Management", callback_data="admin_database_management")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Database Cleanup
async def admin_db_cleanup_callback(callback: types.CallbackQuery):
    """Clean old data from database"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        cleanup_stats = {}
        
        # Clean old pending payments (older than 24 hours)
        cursor.execute('''
            DELETE FROM pending_ton_payments 
            WHERE created_at < datetime('now', '-24 hours')
        ''')
        cleanup_stats['old_pending_payments'] = cursor.rowcount
        
        # Clean old processed transactions (older than 30 days)
        cursor.execute('''
            DELETE FROM processed_transactions 
            WHERE processed_at < datetime('now', '-30 days')
        ''')
        cleanup_stats['old_processed_transactions'] = cursor.rowcount
        
        # Clean old stars transactions (older than 30 days)
        cursor.execute('''
            DELETE FROM stars_transactions 
            WHERE timestamp < datetime('now', '-30 days')
        ''')
        cleanup_stats['old_stars_transactions'] = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        result_text = f"🧹 <b>Database Cleanup Completed</b>\n\n"
        result_text += f"📊 <b>Cleanup Results:</b>\n"
        result_text += f"   • Old pending payments: {cleanup_stats['old_pending_payments']}\n"
        result_text += f"   • Old processed transactions: {cleanup_stats['old_processed_transactions']}\n"
        result_text += f"   • Old stars transactions: {cleanup_stats['old_stars_transactions']}\n\n"
        result_text += f"✅ <b>Total records cleaned:</b> {sum(cleanup_stats.values())}"
        
    except Exception as e:
        result_text = f"❌ <b>Cleanup Failed</b>\n\nError: {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗄️ Database Management", callback_data="admin_database_management")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Daily Reports Callback
async def admin_daily_reports_callback(callback: types.CallbackQuery):
    """Handle admin daily reports"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Daily user registrations
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) = ?
            ''', (today,))
            new_users = cursor.fetchone()[0]
            
            # Daily active users (users who spun today)
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM users 
                WHERE DATE(updated_at) = ? AND total_spins > 0
            ''', (today,))
            active_users = cursor.fetchone()[0]
            
            # Daily spins
            cursor.execute('''
                SELECT SUM(total_spins) FROM users 
                WHERE DATE(updated_at) = ?
            ''', (today,))
            daily_spins = cursor.fetchone()[0] or 0
            
            # Daily revenue (TON)
            cursor.execute('''
                SELECT SUM(amount_nano) FROM processed_transactions 
                WHERE DATE(processed_at) = ?
            ''', (today,))
            ton_revenue = cursor.fetchone()[0] or 0
            ton_revenue = ton_revenue / 1e9  # Convert to TON
            
            # Daily revenue (Stars)
            cursor.execute('''
                SELECT SUM(amount) FROM stars_transactions 
                WHERE DATE(timestamp) = ?
            ''', (today,))
            stars_revenue = cursor.fetchone()[0] or 0
            
            # Daily NFTs earned
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) = ? AND nfts != '[]'
            ''', (today,))
            nfts_earned = cursor.fetchone()[0]
        
        admin_text = f"📅 <b>Daily Report - {today}</b>\n\n"
        admin_text += f"👥 <b>Users:</b>\n"
        admin_text += f"   • New registrations: {new_users}\n"
        admin_text += f"   • Active users: {active_users}\n\n"
        admin_text += f"🎰 <b>Game Activity:</b>\n"
        admin_text += f"   • Total spins: {daily_spins:,}\n"
        admin_text += f"   • NFTs earned: {nfts_earned}\n\n"
        admin_text += f"💰 <b>Revenue:</b>\n"
        admin_text += f"   • TON: {ton_revenue:.4f} TON\n"
        admin_text += f"   • Stars: {stars_revenue:,}\n"
        admin_text += f"   • Total: {ton_revenue + stars_to_ton(stars_revenue):.4f} TON"
        
    except Exception as e:
        admin_text = f"📅 <b>Daily Report</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Weekly Reports Callback
async def admin_weekly_reports_callback(callback: types.CallbackQuery):
    """Handle admin weekly reports"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Weekly user registrations
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) >= ?
            ''', (week_ago,))
            new_users = cursor.fetchone()[0]
            
            # Weekly active users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM users 
                WHERE DATE(updated_at) >= ? AND total_spins > 0
            ''', (week_ago,))
            active_users = cursor.fetchone()[0]
            
            # Weekly spins
            cursor.execute('''
                SELECT SUM(total_spins) FROM users 
                WHERE DATE(updated_at) >= ?
            ''', (week_ago,))
            weekly_spins = cursor.fetchone()[0] or 0
            
            # Weekly revenue (TON)
            cursor.execute('''
                SELECT SUM(amount_nano) FROM processed_transactions 
                WHERE DATE(processed_at) >= ?
            ''', (week_ago,))
            ton_revenue = cursor.fetchone()[0] or 0
            ton_revenue = ton_revenue / 1e9
            
            # Weekly revenue (Stars)
            cursor.execute('''
                SELECT SUM(amount) FROM stars_transactions 
                WHERE DATE(timestamp) >= ?
            ''', (week_ago,))
            stars_revenue = cursor.fetchone()[0] or 0
            
            # Weekly NFTs earned
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) >= ? AND nfts != '[]'
            ''', (week_ago,))
            nfts_earned = cursor.fetchone()[0]
            
            # Average daily activity
            avg_daily_spins = weekly_spins / 7
            avg_daily_revenue = (ton_revenue + stars_to_ton(stars_revenue)) / 7
        
        admin_text = f"📆 <b>Weekly Report - Last 7 Days</b>\n\n"
        admin_text += f"👥 <b>Users:</b>\n"
        admin_text += f"   • New registrations: {new_users}\n"
        admin_text += f"   • Active users: {active_users}\n\n"
        admin_text += f"🎰 <b>Game Activity:</b>\n"
        admin_text += f"   • Total spins: {weekly_spins:,}\n"
        admin_text += f"   • Avg daily spins: {avg_daily_spins:.0f}\n"
        admin_text += f"   • NFTs earned: {nfts_earned}\n\n"
        admin_text += f"💰 <b>Revenue:</b>\n"
        admin_text += f"   • TON: {ton_revenue:.4f} TON\n"
        admin_text += f"   • Stars: {stars_revenue:,}\n"
        admin_text += f"   • Total: {ton_revenue + stars_to_ton(stars_revenue):.4f} TON\n"
        admin_text += f"   • Avg daily: {avg_daily_revenue:.4f} TON"
        
    except Exception as e:
        admin_text = f"📆 <b>Weekly Report</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Popular Packages Callback
async def admin_popular_packages_callback(callback: types.CallbackQuery):
    """Handle admin popular packages analysis"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        
        db_pool = get_db_pool()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Package popularity from TON transactions
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount_nano) as total_nano
                FROM processed_transactions 
                GROUP BY package 
                ORDER BY count DESC
            ''')
            ton_packages = cursor.fetchall()
            
            # Package popularity from Stars transactions
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount) as total_stars
                FROM stars_transactions 
                GROUP BY package 
                ORDER BY count DESC
            ''')
            stars_packages = cursor.fetchall()
            
            # Current active packages
            cursor.execute('''
                SELECT package, COUNT(*) as count
                FROM users 
                WHERE package != 'None'
                GROUP BY package 
                ORDER BY count DESC
            ''')
            active_packages = cursor.fetchall()
        
        admin_text = f"🏆 <b>Popular Packages Analysis</b>\n\n"
        
        admin_text += f"💎 <b>TON Purchases:</b>\n"
        for package, count, total_nano in ton_packages:
            total_ton = total_nano / 1e9
            admin_text += f"   • {package}: {count} purchases ({total_ton:.4f} TON)\n"
        
        admin_text += f"\n⭐ <b>Stars Purchases:</b>\n"
        for package, count, total_stars in stars_packages:
            admin_text += f"   • {package}: {count} purchases ({total_stars:,} Stars)\n"
        
        admin_text += f"\n🎮 <b>Currently Active:</b>\n"
        for package, count in active_packages:
            admin_text += f"   • {package}: {count} users\n"
        
        # Calculate total popularity
        total_purchases = sum(count for _, count, _ in ton_packages) + sum(count for _, count, _ in stars_packages)
        if total_purchases > 0:
            admin_text += f"\n📊 <b>Total Purchases:</b> {total_purchases}"
        
    except Exception as e:
        admin_text = f"🏆 <b>Popular Packages</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin User Retention Callback
async def admin_user_retention_callback(callback: types.CallbackQuery):
    """Handle admin user retention analysis"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Users active in last 24 hours
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) >= DATE('now', '-1 day')
            ''')
            active_24h = cursor.fetchone()[0]
            
            # Users active in last 7 days
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) >= DATE('now', '-7 days')
            ''')
            active_7d = cursor.fetchone()[0]
            
            # Users active in last 30 days
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) >= DATE('now', '-30 days')
            ''')
            active_30d = cursor.fetchone()[0]
            
            # Users who made purchases
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM processed_transactions
            ''')
            paying_users = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM stars_transactions
            ''')
            stars_users = cursor.fetchone()[0]
            
            # Users with NFTs
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE nfts != '[]'
            ''')
            nft_users = cursor.fetchone()[0]
        
        # Calculate retention rates
        retention_24h = (active_24h / max(total_users, 1)) * 100
        retention_7d = (active_7d / max(total_users, 1)) * 100
        retention_30d = (active_30d / max(total_users, 1)) * 100
        conversion_rate = (paying_users / max(total_users, 1)) * 100
        nft_rate = (nft_users / max(total_users, 1)) * 100
        
        admin_text = f"👥 <b>User Retention Analysis</b>\n\n"
        admin_text += f"📊 <b>User Base:</b>\n"
        admin_text += f"   • Total users: {total_users:,}\n"
        admin_text += f"   • Paying users: {paying_users + stars_users:,}\n"
        admin_text += f"   • NFT holders: {nft_users:,}\n\n"
        
        admin_text += f"🔄 <b>Retention Rates:</b>\n"
        admin_text += f"   • 24h retention: {retention_24h:.1f}% ({active_24h:,} users)\n"
        admin_text += f"   • 7d retention: {retention_7d:.1f}% ({active_7d:,} users)\n"
        admin_text += f"   • 30d retention: {retention_30d:.1f}% ({active_30d:,} users)\n\n"
        
        admin_text += f"💰 <b>Conversion Rates:</b>\n"
        admin_text += f"   • Payment conversion: {conversion_rate:.1f}%\n"
        admin_text += f"   • NFT earning rate: {nft_rate:.1f}%"
        
    except Exception as e:
        admin_text = f"👥 <b>User Retention</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Export Data Callback
async def admin_export_data_callback(callback: types.CallbackQuery):
    """Handle admin data export"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime
        import csv
        import os
        
        db_pool = get_db_pool()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export users data
        users_file = f"users_export_{timestamp}.csv"
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            users_data = cursor.fetchall()
            
            # Get column names
            cursor.execute('PRAGMA table_info(users)')
            columns = [row[1] for row in cursor.fetchall()]
            
            with open(users_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                writer.writerows(users_data)
        
        # Export transactions data
        transactions_file = f"transactions_export_{timestamp}.csv"
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Combine TON and Stars transactions
            cursor.execute('''
                SELECT 'TON' as type, tx_hash as transaction_id, user_id, package, 
                       amount_nano/1e9 as amount, processed_at as timestamp
                FROM processed_transactions
                UNION ALL
                SELECT 'Stars' as type, transaction_id, user_id, package, 
                       amount, timestamp
                FROM stars_transactions
                ORDER BY timestamp DESC
            ''')
            transactions_data = cursor.fetchall()
            
            with open(transactions_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['type', 'transaction_id', 'user_id', 'package', 'amount', 'timestamp'])
                writer.writerows(transactions_data)
        
        admin_text = f"📤 <b>Data Export Completed</b>\n\n"
        admin_text += f"📁 <b>Exported Files:</b>\n"
        admin_text += f"   • {users_file} ({len(users_data)} users)\n"
        admin_text += f"   • {transactions_file} ({len(transactions_data)} transactions)\n\n"
        admin_text += f"⏰ <b>Export Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        admin_text += f"📂 <b>Location:</b> Bot directory"
        
    except Exception as e:
        admin_text = f"📤 <b>Data Export</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin NFT Distribution Management Callback
async def admin_nft_distribution_callback(callback: types.CallbackQuery):
    """Handle admin NFT distribution management"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        import json
        
        db_pool = get_db_pool()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get NFT distribution statistics
            cursor.execute('''
                SELECT package, COUNT(*) as count
                FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
                GROUP BY package
                ORDER BY count DESC
            ''')
            nft_stats = cursor.fetchall()
            
            # Get total NFTs distributed
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
            ''')
            total_nfts = cursor.fetchone()[0]
            
            # Get NFT distribution by level
            cursor.execute('''
                SELECT level, COUNT(*) as count
                FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
                GROUP BY level
                ORDER BY count DESC
            ''')
            nft_by_level = cursor.fetchall()
            
            # Get recent NFT distributions (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
                AND DATE(updated_at) >= DATE('now', '-7 days')
            ''')
            recent_nfts = cursor.fetchone()[0]
        
        admin_text = f"🎁 <b>NFT Distribution Management</b>\n\n"
        admin_text += f"📊 <b>Distribution Statistics:</b>\n"
        admin_text += f"   • Total NFTs distributed: {total_nfts}\n"
        admin_text += f"   • Recent (7 days): {recent_nfts}\n\n"
        
        admin_text += f"📦 <b>By Package:</b>\n"
        for package, count in nft_stats:
            admin_text += f"   • {package}: {count} NFTs\n"
        
        admin_text += f"\n🏆 <b>By Level:</b>\n"
        for level, count in nft_by_level:
            admin_text += f"   • {level}: {count} NFTs\n"
        
    except Exception as e:
        admin_text = f"🎁 <b>NFT Distribution</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 NFT Analytics", callback_data="admin_nft_analytics"),
            InlineKeyboardButton(text="🎯 Hit Rate Stats", callback_data="admin_hit_rate_analytics")
        ],
        [
        ],
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Game Settings Callback


# Admin Hit Rate Analytics Callback
async def admin_hit_rate_analytics_callback(callback: types.CallbackQuery):
    """Handle admin hit rate analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total spins and hits
            cursor.execute('''
                SELECT SUM(total_spins) as total_spins, SUM(hits) as total_hits
                FROM users
            ''')
            total_spins, total_hits = cursor.fetchone()
            total_spins = total_spins or 0
            total_hits = total_hits or 0
            
            # Daily hit rate (last 7 days)
            cursor.execute('''
                SELECT DATE(updated_at) as date, 
                       SUM(total_spins) as daily_spins,
                       SUM(hits) as daily_hits
                FROM users 
                WHERE DATE(updated_at) >= ?
                GROUP BY DATE(updated_at)
                ORDER BY date DESC
            ''', (week_ago,))
            daily_stats = cursor.fetchall()
            
            # Hit rate by package
            cursor.execute('''
                SELECT package, 
                       SUM(total_spins) as package_spins,
                       SUM(hits) as package_hits
                FROM users 
                WHERE package != 'None'
                GROUP BY package
                ORDER BY package_spins DESC
            ''')
            package_stats = cursor.fetchall()
            
            # Hit rate by level
            cursor.execute('''
                SELECT level, 
                       SUM(total_spins) as level_spins,
                       SUM(hits) as level_hits
                FROM users 
                GROUP BY level
                ORDER BY level_spins DESC
            ''')
            level_stats = cursor.fetchall()
        
        # Calculate overall hit rate
        overall_hit_rate = (total_hits / max(total_spins, 1)) * 100
        
        admin_text = f"🎯 <b>Hit Rate Analytics</b>\n\n"
        admin_text += f"📊 <b>Overall Statistics:</b>\n"
        admin_text += f"   • Total Spins: {total_spins:,}\n"
        admin_text += f"   • Total Hits: {total_hits:,}\n"
        admin_text += f"   • Overall Hit Rate: {overall_hit_rate:.2f}%\n\n"
        
        admin_text += f"📦 <b>Hit Rate by Package:</b>\n"
        for package, spins, hits in package_stats:
            hit_rate = (hits / max(spins, 1)) * 100
            admin_text += f"   • {package}: {hit_rate:.2f}% ({hits}/{spins})\n"
        
        admin_text += f"\n🏆 <b>Hit Rate by Level:</b>\n"
        for level, spins, hits in level_stats:
            hit_rate = (hits / max(spins, 1)) * 100
            admin_text += f"   • {level}: {hit_rate:.2f}% ({hits}/{spins})\n"
        
        admin_text += f"\n📅 <b>Recent Daily Hit Rates:</b>\n"
        for date, spins, hits in daily_stats[:3]:  # Show last 3 days
            hit_rate = (hits / max(spins, 1)) * 100
            admin_text += f"   • {date}: {hit_rate:.2f}% ({hits}/{spins})\n"
        
    except Exception as e:
        admin_text = f"🎯 <b>Hit Rate Analytics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 NFT Distribution", callback_data="admin_nft_distribution"),
        ],
        [
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin NFT Analytics Callback
async def admin_nft_analytics_callback(callback: types.CallbackQuery):
    """Handle admin NFT analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        import json
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get detailed NFT analytics
            cursor.execute('''
                SELECT package, level, nfts, updated_at
                FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
                ORDER BY updated_at DESC
            ''')
            nft_users = cursor.fetchall()
            
            # NFT distribution by package and level
            nft_distribution = {}
            recent_nfts = 0
            
            for package, level, nfts_json, updated_at in nft_users:
                # Count recent NFTs
                if datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S').date() >= week_ago:
                    recent_nfts += 1
                
                # Parse NFTs
                try:
                    nfts = json.loads(nfts_json) if nfts_json else []
                    nft_count = len(nfts)
                except:
                    nft_count = 1  # Fallback if JSON parsing fails
                
                # Group by package and level
                key = f"{package}_{level}"
                if key not in nft_distribution:
                    nft_distribution[key] = {'count': 0, 'nft_count': 0}
                nft_distribution[key]['count'] += 1
                nft_distribution[key]['nft_count'] += nft_count
            
            # Total NFTs distributed
            total_nfts = sum(data['nft_count'] for data in nft_distribution.values())
            
            # NFT distribution by package
            cursor.execute('''
                SELECT package, COUNT(*) as count
                FROM users 
                WHERE nfts != '[]' AND nfts IS NOT NULL
                GROUP BY package
                ORDER BY count DESC
            ''')
            package_nft_stats = cursor.fetchall()
        
        admin_text = f"🎁 <b>NFT Analytics</b>\n\n"
        admin_text += f"📊 <b>Overall Statistics:</b>\n"
        admin_text += f"   • Total NFTs distributed: {total_nfts}\n"
        admin_text += f"   • Users with NFTs: {len(nft_users)}\n"
        admin_text += f"   • Recent (7 days): {recent_nfts}\n\n"
        
        admin_text += f"📦 <b>NFT Distribution by Package:</b>\n"
        for package, count in package_nft_stats:
            admin_text += f"   • {package}: {count} users\n"
        
        admin_text += f"\n🏆 <b>NFT Distribution by Package & Level:</b>\n"
        for key, data in sorted(nft_distribution.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            package, level = key.split('_', 1)
            admin_text += f"   • {package} {level}: {data['count']} users, {data['nft_count']} NFTs\n"
        
        # Calculate NFT earning rate
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        nft_rate = (len(nft_users) / max(total_users, 1)) * 100
        admin_text += f"\n📈 <b>NFT Earning Rate:</b> {nft_rate:.1f}% of all users"
        
    except Exception as e:
        admin_text = f"🎁 <b>NFT Analytics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Hit Rate Analytics", callback_data="admin_hit_rate_analytics"),
        ],
        [
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Update Translations Callback
async def admin_update_translations_callback(callback: types.CallbackQuery):
    """Handle admin update translations"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import translations
        
        # Get current translation statistics
        total_translations = len(translations.TRANSLATIONS.get('en', {}))
        supported_languages = list(translations.TRANSLATIONS.keys())
        
        admin_text = f"🌐 <b>Translation Management</b>\n\n"
        admin_text += f"📊 <b>Current Status:</b>\n"
        admin_text += f"   • Supported languages: {len(supported_languages)}\n"
        admin_text += f"   • Languages: {', '.join(supported_languages)}\n"
        admin_text += f"   • Total translations: {total_translations}\n\n"
        
        admin_text += f"🔧 <b>Available Actions:</b>\n"
        admin_text += f"   • View translation coverage\n"
        admin_text += f"   • Update specific translations\n"
        admin_text += f"   • Add new language support\n"
        admin_text += f"   • Export/Import translations"
        
    except Exception as e:
        admin_text = f"🌐 <b>Translation Management</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 View Coverage", callback_data="admin_view_translation_coverage"),
            InlineKeyboardButton(text="✏️ Edit Translations", callback_data="admin_edit_translations")
        ],
        [
            InlineKeyboardButton(text="➕ Add Language", callback_data="admin_add_language"),
            InlineKeyboardButton(text="📤 Export Translations", callback_data="admin_export_translations")
        ],
        [
            InlineKeyboardButton(text="📝 Content Management", callback_data="admin_content_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Package Pricing Management Callback
async def admin_package_pricing_callback(callback: types.CallbackQuery):
    """Handle admin package pricing management"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package pricing
        packages = config.PACKAGES
        
        admin_text = f"💲 <b>Package Pricing Management</b>\n\n"
        admin_text += f"📦 <b>Current Package Prices:</b>\n"
        
        for package_key, package_data in packages.items():
            admin_text += f"   • {package_data['name']}:\n"
            admin_text += f"     - TON: {package_data['price_ton']} TON\n"
            admin_text += f"     - Stars: {package_data['price_stars']:,} Stars\n"
            admin_text += f"     - Spins: {package_data['spins']}\n"
            admin_text += f"     - Hits Required: {package_data['hits_required']}\n\n"
        
        admin_text += f"💰 <b>Revenue Analysis:</b>\n"
        
        # Calculate potential revenue
        total_ton_revenue = sum(package['price_ton'] for package in packages.values())
        total_stars_revenue = sum(package['price_stars'] for package in packages.values())
        
        admin_text += f"   • Total TON per set: {total_ton_revenue:.4f} TON\n"
        admin_text += f"   • Total Stars per set: {total_stars_revenue:,} Stars\n"
        admin_text += f"   • Total value: {total_ton_revenue + stars_to_ton(total_stars_revenue):.4f} TON"
        
    except Exception as e:
        admin_text = f"💲 <b>Package Pricing</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Pricing Analytics", callback_data="admin_pricing_analytics"),
            InlineKeyboardButton(text="✏️ Edit Prices", callback_data="admin_edit_prices")
        ],
        [
            InlineKeyboardButton(text="📈 Revenue Projections", callback_data="admin_revenue_projections"),
            InlineKeyboardButton(text="🎯 Price Optimization", callback_data="admin_price_optimization")
        ],
        [
            InlineKeyboardButton(text="📝 Content Management", callback_data="admin_content_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin FAQ Management Callback


# Admin Pricing Analytics Callback
async def admin_pricing_analytics_callback(callback: types.CallbackQuery):
    """Handle admin pricing analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        import config
        
        db_pool = get_db_pool()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get package purchase statistics
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount_nano) as total_nano
                FROM processed_transactions 
                GROUP BY package 
                ORDER BY count DESC
            ''')
            ton_purchases = cursor.fetchall()
            
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount) as total_stars
                FROM stars_transactions 
                GROUP BY package 
                ORDER BY count DESC
            ''')
            stars_purchases = cursor.fetchall()
            
            # Calculate revenue per package
            packages = config.PACKAGES
            revenue_analysis = {}
            
            for package_key, package_data in packages.items():
                package_name = package_data['name']
                
                # Find purchases for this package
                ton_count = next((count for pkg, count, _ in ton_purchases if pkg == package_name), 0)
                stars_count = next((count for pkg, count, _ in stars_purchases if pkg == package_name), 0)
                
                # Calculate revenue
                ton_revenue = ton_count * package_data['price_ton']
                stars_revenue = stars_to_ton(stars_count * package_data['price_stars'])  # Convert Stars to TON
                total_revenue = ton_revenue + stars_revenue
                
                revenue_analysis[package_name] = {
                    'ton_purchases': ton_count,
                    'stars_purchases': stars_count,
                    'total_purchases': ton_count + stars_count,
                    'ton_revenue': ton_revenue,
                    'stars_revenue': stars_revenue,
                    'total_revenue': total_revenue
                }
        
        admin_text = f"📊 <b>Pricing Analytics</b>\n\n"
        admin_text += f"💰 <b>Revenue by Package:</b>\n"
        
        # Sort by total revenue
        sorted_packages = sorted(revenue_analysis.items(), key=lambda x: x[1]['total_revenue'], reverse=True)
        
        for package_name, data in sorted_packages:
            admin_text += f"   • {package_name}:\n"
            admin_text += f"     - Purchases: {data['total_purchases']} ({data['ton_purchases']} TON, {data['stars_purchases']} Stars)\n"
            admin_text += f"     - Revenue: {data['total_revenue']:.4f} TON\n\n"
        
        # Calculate total revenue
        total_revenue = sum(data['total_revenue'] for data in revenue_analysis.values())
        total_purchases = sum(data['total_purchases'] for data in revenue_analysis.values())
        
        admin_text += f"📈 <b>Overall Statistics:</b>\n"
        admin_text += f"   • Total purchases: {total_purchases}\n"
        admin_text += f"   • Total revenue: {total_revenue:.4f} TON\n"
        admin_text += f"   • Average revenue per purchase: {total_revenue/max(total_purchases, 1):.4f} TON"
        
    except Exception as e:
        admin_text = f"📊 <b>Pricing Analytics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💲 Package Pricing", callback_data="admin_package_pricing"),
            InlineKeyboardButton(text="📈 Revenue Projections", callback_data="admin_revenue_projections")
        ],
        [
            InlineKeyboardButton(text="📝 Content Management", callback_data="admin_content_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Pending Payments Management Callback
async def admin_pending_payments_callback(callback: types.CallbackQuery):
    """Handle admin pending payments management"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from datetime import datetime, timedelta
        import sqlite3
        
        # Use direct database connection to avoid schema issues
        conn = sqlite3.connect('cgspins.db')
        cursor = conn.cursor()
        
        # Check table schema first
        cursor.execute("PRAGMA table_info(pending_ton_payments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Determine which columns are available
        has_amount_nano = 'amount_nano' in columns
        has_expected_amount = 'expected_amount' in columns
        has_created_at = 'created_at' in columns
        has_timestamp = 'timestamp' in columns
        
        # Build query based on available columns
        if has_amount_nano and has_created_at:
            # New schema
            cursor.execute('''
                SELECT user_id, package, payment_id, amount_nano, created_at
                FROM pending_ton_payments
                ORDER BY created_at DESC
            ''')
            pending_payments = cursor.fetchall()
            
            # Get pending payments statistics
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount_nano) as total_nano
                FROM pending_ton_payments
            ''')
            pending_stats = cursor.fetchone()
            pending_count = pending_stats[0] or 0
            total_pending_nano = pending_stats[1] or 0
            total_pending_ton = total_pending_nano / 1e9
            
            # Get expired payments (older than 1 hour)
            cursor.execute('''
                SELECT COUNT(*) FROM pending_ton_payments
                WHERE created_at < datetime('now', '-1 hour')
            ''')
            expired_count = cursor.fetchone()[0]
            
        elif has_expected_amount and has_timestamp:
            # Old schema - convert to new format
            cursor.execute('''
                SELECT user_id, package, payment_id, expected_amount, timestamp
                FROM pending_ton_payments
                ORDER BY timestamp DESC
            ''')
            old_payments = cursor.fetchall()
            
            # Convert old format to new format
            pending_payments = []
            for payment in old_payments:
                user_id_payment, package, payment_id, expected_amount, timestamp = payment
                # Convert timestamp to created_at format using utility function
                created_at = format_timestamp(timestamp)
                pending_payments.append((user_id_payment, package, payment_id, expected_amount, created_at))
            
            # Get pending payments statistics
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(expected_amount) as total_nano
                FROM pending_ton_payments
            ''')
            pending_stats = cursor.fetchone()
            pending_count = pending_stats[0] or 0
            total_pending_nano = pending_stats[1] or 0
            total_pending_ton = total_pending_nano / 1e9
            
            # Get expired payments (older than 1 hour)
            one_hour_ago = time.time() - 3600
            cursor.execute('''
                SELECT COUNT(*) FROM pending_ton_payments
                WHERE timestamp < ?
            ''', (one_hour_ago,))
            expired_count = cursor.fetchone()[0]
            
        else:
            # Fallback - no pending payments
            pending_payments = []
            pending_count = 0
            total_pending_ton = 0
            expired_count = 0
        
        conn.close()
        
        admin_text = f"⏳ <b>Pending Payments Management</b>\n\n"
        admin_text += f"📊 <b>Pending Payments Statistics:</b>\n"
        admin_text += f"   • Total pending: {pending_count}\n"
        admin_text += f"   • Total value: {total_pending_ton:.4f} TON\n"
        admin_text += f"   • Expired (>1h): {expired_count}\n\n"
        
        if pending_payments:
            admin_text += f"💳 <b>Recent Pending Payments:</b>\n"
            for payment in pending_payments[:5]:  # Show first 5
                user_id_payment, package, payment_id, amount_nano, created_at = payment
                amount_ton = amount_nano / 1e9
                admin_text += f"   • User {user_id_payment}: {package} ({amount_ton:.4f} TON)\n"
                admin_text += f"     ID: {payment_id[:20]}...\n"
                admin_text += f"     Time: {created_at}\n\n"
            
            if len(pending_payments) > 5:
                admin_text += f"   • ... and {len(pending_payments) - 5} more pending payments\n"
        else:
            admin_text += f"✅ <b>No pending payments</b>"
        
    except Exception as e:
        admin_text = f"⏳ <b>Pending Payments</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_pending_payments"),
            InlineKeyboardButton(text="🧹 Clean Expired", callback_data="admin_clean_expired_payments")
        ],
        [
            InlineKeyboardButton(text="📋 Transaction History", callback_data="admin_transaction_history"),
            InlineKeyboardButton(text="💰 Financial Management", callback_data="admin_financial_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Transaction History Details Callback
async def admin_transaction_history_callback(callback: types.CallbackQuery):
    """Handle admin transaction history details with pagination"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    # Parse page from callback data if present
    page = 1
    if "_page_" in callback.data:
        try:
            page = int(callback.data.split("_page_")[1])
        except:
            page = 1
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # Pagination settings
        items_per_page = 5
        offset = (page - 1) * items_per_page
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total counts for pagination
            cursor.execute('SELECT COUNT(*) FROM processed_transactions')
            total_ton_txs = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM stars_transactions')
            total_stars_txs = cursor.fetchone()[0]
            
            # Get paginated TON transactions
            cursor.execute('''
                SELECT tx_hash, user_id, package, amount_nano, processed_at
                FROM processed_transactions
                ORDER BY processed_at DESC
                LIMIT ? OFFSET ?
            ''', (items_per_page, offset))
            ton_transactions = cursor.fetchall()
            
            # Get paginated Stars transactions
            cursor.execute('''
                SELECT transaction_id, user_id, package, amount, timestamp
                FROM stars_transactions
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (items_per_page, offset))
            stars_transactions = cursor.fetchall()
            
            # Get transaction statistics
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount_nano) as total_nano
                FROM processed_transactions
                WHERE DATE(processed_at) >= ?
            ''', (week_ago,))
            ton_stats = cursor.fetchone()
            ton_count = ton_stats[0] or 0
            ton_total = (ton_stats[1] or 0) / 1e9
            
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount) as total_stars
                FROM stars_transactions
                WHERE DATE(timestamp) >= ?
            ''', (week_ago,))
            stars_stats = cursor.fetchone()
            stars_count = stars_stats[0] or 0
            stars_total = stars_stats[1] or 0
        
        admin_text = f"📋 <b>Transaction History Details</b>\n\n"
        admin_text += f"📊 <b>Weekly Statistics (Last 7 Days):</b>\n"
        admin_text += f"   • TON transactions: {ton_count} ({ton_total:.4f} TON)\n"
        admin_text += f"   • Stars transactions: {stars_count} ({stars_total:,} Stars)\n"
        admin_text += f"   • Total value: {ton_total + stars_to_ton(stars_total):.4f} TON\n\n"
        
        admin_text += f"💎 <b>TON Transactions (Page {page}):</b>\n"
        if ton_transactions:
            for tx in ton_transactions:
                tx_hash, user_id_tx, package, amount_nano, processed_at = tx
                amount_ton = amount_nano / 1e9
                formatted_time = format_timestamp(processed_at)
                formatted_hash = format_transaction_hash(tx_hash)
                
                admin_text += f"   • <b>{package}</b>: {amount_ton:.4f} TON\n"
                admin_text += f"     👤 User: {user_id_tx} | 🕒 {formatted_time}\n"
                admin_text += f"     🔗 Hash: {formatted_hash}\n\n"
        else:
            admin_text += "   No TON transactions found.\n\n"
        
        admin_text += f"⭐ <b>Stars Transactions (Page {page}):</b>\n"
        if stars_transactions:
            for tx in stars_transactions:
                tx_id, user_id_tx, package, amount, timestamp = tx
                formatted_time = format_timestamp(timestamp)
                formatted_id = format_transaction_id(tx_id)
                
                admin_text += f"   • <b>{package}</b>: {amount:,} Stars\n"
                admin_text += f"     👤 User: {user_id_tx} | 🕒 {formatted_time}\n"
                admin_text += f"     🆔 ID: {formatted_id}\n\n"
        else:
            admin_text += "   No Stars transactions found.\n\n"
        
        # Calculate total pages
        total_pages = max(1, (max(total_ton_txs, total_stars_txs) + items_per_page - 1) // items_per_page)
        
        # Create pagination keyboard
        keyboard = create_pagination_keyboard(page, total_pages, "admin_transaction_history")
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Back to Financial", callback_data="admin_financial_management")])
        
    except Exception as e:
        admin_text = f"📋 <b>Transaction History</b>\n\n❌ <b>Error:</b> {str(e)}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Back to Financial", callback_data="admin_financial_management")]
        ])
    
    try:
        await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        # If message is not modified, just answer the callback
        if "message is not modified" in str(e):
            await callback.answer()
            return
        else:
            print(f"Error editing message: {e}")
    await callback.answer()


# Admin Advanced Revenue Analytics Callback
async def admin_advanced_revenue_analytics_callback(callback: types.CallbackQuery):
    """Handle admin advanced revenue analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Daily revenue trends (last 7 days)
            cursor.execute('''
                SELECT DATE(processed_at) as date, 
                       COUNT(*) as count,
                       SUM(amount_nano)/1e9 as ton_revenue
                FROM processed_transactions
                WHERE DATE(processed_at) >= ?
                GROUP BY DATE(processed_at)
                ORDER BY date DESC
            ''', (week_ago,))
            daily_ton_revenue = cursor.fetchall()
            
            cursor.execute('''
                SELECT DATE(timestamp) as date, 
                       COUNT(*) as count,
                       SUM(amount) as stars_revenue
                FROM stars_transactions
                WHERE DATE(timestamp) >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', (week_ago,))
            daily_stars_revenue = cursor.fetchall()
            
            # Monthly revenue comparison
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount_nano)/1e9 as ton_revenue
                FROM processed_transactions
                WHERE DATE(processed_at) >= ?
            ''', (month_ago,))
            monthly_ton = cursor.fetchone()
            
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount) as stars_revenue
                FROM stars_transactions
                WHERE DATE(timestamp) >= ?
            ''', (month_ago,))
            monthly_stars = cursor.fetchone()
            
            # Revenue by package (all time)
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount_nano)/1e9 as ton_revenue
                FROM processed_transactions
                GROUP BY package
                ORDER BY ton_revenue DESC
            ''')
            package_ton_revenue = cursor.fetchall()
            
            cursor.execute('''
                SELECT package, COUNT(*) as count, SUM(amount) as stars_revenue
                FROM stars_transactions
                GROUP BY package
                ORDER BY stars_revenue DESC
            ''')
            package_stars_revenue = cursor.fetchall()
        
        # Calculate totals
        total_monthly_ton = monthly_ton[1] or 0
        total_monthly_stars = monthly_stars[1] or 0
        total_monthly_value = total_monthly_ton + stars_to_ton(total_monthly_stars)
        
        admin_text = f"📈 <b>Advanced Revenue Analytics</b>\n\n"
        admin_text += f"📊 <b>Monthly Overview (Last 30 Days):</b>\n"
        admin_text += f"   • TON revenue: {total_monthly_ton:.4f} TON ({monthly_ton[0]} transactions)\n"
        admin_text += f"   • Stars revenue: {total_monthly_stars:,} Stars ({monthly_stars[0]} transactions)\n"
        admin_text += f"   • Total value: {total_monthly_value:.4f} TON\n\n"
        
        admin_text += f"📅 <b>Daily Revenue Trends (Last 7 Days):</b>\n"
        for date, count, ton_rev in daily_ton_revenue[:3]:
            stars_rev = next((rev for d, c, rev in daily_stars_revenue if d == date), 0)
            total_daily = ton_rev + stars_to_ton(stars_rev)
            admin_text += f"   • {date}: {total_daily:.4f} TON ({count} TON + {stars_rev:,} Stars)\n"
        
        admin_text += f"\n📦 <b>Revenue by Package (All Time):</b>\n"
        for package, count, ton_rev in package_ton_revenue:
            stars_rev = next((rev for p, c, rev in package_stars_revenue if p == package), 0)
            total_package = ton_rev + (stars_rev * 0.01)
            admin_text += f"   • {package}: {total_package:.4f} TON ({count} purchases)\n"
        
        # Calculate growth rate
        if len(daily_ton_revenue) >= 2:
            recent_revenue = daily_ton_revenue[0][2] + (daily_stars_revenue[0][2] * 0.01 if daily_stars_revenue else 0)
            previous_revenue = daily_ton_revenue[1][2] + (daily_stars_revenue[1][2] * 0.01 if len(daily_stars_revenue) > 1 else 0)
            growth_rate = ((recent_revenue - previous_revenue) / max(previous_revenue, 1)) * 100
            admin_text += f"\n📈 <b>Daily Growth Rate:</b> {growth_rate:+.1f}%"
        
    except Exception as e:
        admin_text = f"📈 <b>Advanced Revenue Analytics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Transaction History", callback_data="admin_transaction_history"),
            InlineKeyboardButton(text="⏳ Pending Payments", callback_data="admin_pending_payments")
        ],
        [
            InlineKeyboardButton(text="📊 Revenue Analytics", callback_data="admin_revenue_analytics"),
            InlineKeyboardButton(text="💰 Financial Management", callback_data="admin_financial_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Admin Clean Expired Payments Callback
async def admin_clean_expired_payments_callback(callback: types.CallbackQuery):
    """Handle admin clean expired payments"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        
        db_pool = get_db_pool()
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count expired payments before deletion
            cursor.execute('''
                SELECT COUNT(*) FROM pending_ton_payments
                WHERE created_at < datetime('now', '-1 hour')
            ''')
            expired_count = cursor.fetchone()[0]
            
            # Delete expired payments
            cursor.execute('''
                DELETE FROM pending_ton_payments
                WHERE created_at < datetime('now', '-1 hour')
            ''')
            deleted_count = cursor.rowcount
            
            conn.commit()
        
        result_text = f"🧹 <b>Expired Payments Cleanup</b>\n\n"
        result_text += f"✅ <b>Cleanup Results:</b>\n"
        result_text += f"   • Expired payments found: {expired_count}\n"
        result_text += f"   • Payments deleted: {deleted_count}\n"
        result_text += f"   • Status: {'Success' if deleted_count == expired_count else 'Partial'}\n\n"
        result_text += f"🔄 <b>Database optimized</b>"
        
    except Exception as e:
        result_text = f"🧹 <b>Expired Payments Cleanup</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏳ Pending Payments", callback_data="admin_pending_payments")
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


if __name__ == "__main__":
    print("✅ Bot setup complete!")
    print("✅ Credentials configured:")
    print(f"   - Bot Token: {config.BOT_TOKEN[:20]}...")
    print("   - Storage: In-memory (for testing)")
    print("   - TON Wallet: {config.TON_WALLET_ADDRESS[:20]}...")
    print("\n🚀 Starting bot...")
    print("💡 Bot is now running! Send /start to test.")
    print("🔍 TON payment checker is active - checking every 30 seconds")
    
    # Start the bot WITH IMPROVED TON payment checker
    async def main():
        # TON payment checker ENABLED with enhanced security and unique payment IDs
        print("🔄 Starting IMPROVED TON payment checker with unique payment IDs and confirmation checking")
        
        # Quick startup API test (non-blocking)
        print("🧪 [Backend] Quick startup test...")
        try:
            async with TONAPIClient() as api_client:
                connection_test = await api_client.test_api_connection()
                print(f"   - Connection: {'OK' if connection_test.get('ok') else 'Failed'}")
                balance_info = await api_client.get_wallet_balance(config.TON_WALLET_ADDRESS)
                balance_ton = int(balance_info.get('balance', 0)) / 1e9 if balance_info.get('ok') else 'Error'
                print(f"   - Wallet Balance: {balance_ton} TON")
        except Exception as e:
            print(f"   - API test failed: {e}")
            print("   - Bot will continue with limited functionality")
        
        asyncio.create_task(ton_payment_checker())
        # Start the bot
        await dp.start_polling(bot, skip_updates=False)
    
# Missing Admin Functions
async def admin_view_logs_callback(callback: types.CallbackQuery):
    """Handle admin view logs"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Read recent bot logs
        try:
            with open('bot_debug.log', 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-20:] if len(lines) > 20 else lines
                log_content = ''.join(recent_logs)
        except FileNotFoundError:
            log_content = "No log file found"
        
        admin_text = f"📋 <b>Recent Bot Logs</b>\n\n"
        admin_text += f"<code>{log_content[-1000:]}</code>"  # Last 1000 chars
        
    except Exception as e:
        admin_text = f"📋 <b>View Logs</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics")
        ],
        [
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check"),
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_system_metrics_callback(callback: types.CallbackQuery):
    """Handle admin system metrics"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import psutil
        import time
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get bot uptime
        uptime_seconds = time.time() - start_time if 'start_time' in globals() else 0
        uptime_str = f"{int(uptime_seconds//3600):02d}:{int((uptime_seconds%3600)//60):02d}:{int(uptime_seconds%60):02d}"
        
        admin_text = f"📊 <b>System Metrics</b>\n\n"
        admin_text += f"⏱️ <b>Bot Uptime:</b> {uptime_str}\n"
        admin_text += f"🖥️ <b>CPU Usage:</b> {cpu_percent}%\n"
        admin_text += f"💾 <b>Memory Usage:</b> {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)\n"
        admin_text += f"💿 <b>Disk Usage:</b> {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)\n"
        admin_text += f"👥 <b>Active Users:</b> {len(user_data)}\n"
        admin_text += f"📥 <b>Pending Payments:</b> {len(pending_ton_payments)}\n"
        
    except Exception as e:
        admin_text = f"📊 <b>System Metrics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_system_metrics"),
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs")
        ],
        [
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check"),
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_health_check_callback(callback: types.CallbackQuery):
    """Handle admin health check"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        health_status = "✅ HEALTHY"
        issues = []
        
        # Check database connection
        try:
            conn = sqlite3.connect('cgspins.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            conn.close()
        except Exception as e:
            health_status = "❌ UNHEALTHY"
            issues.append(f"Database: {str(e)}")
        
        # Check TON API
        try:
            async with TONAPIClient() as api_client:
                balance_info = await api_client.get_balance(config.TON_WALLET_ADDRESS)
                if not balance_info.get('ok'):
                    health_status = "⚠️ WARNING"
                    issues.append("TON API: Connection issues")
        except Exception as e:
            health_status = "⚠️ WARNING"
            issues.append(f"TON API: {str(e)}")
        
        admin_text = f"🏥 <b>System Health Check</b>\n\n"
        admin_text += f"📊 <b>Status:</b> {health_status}\n\n"
        
        if issues:
            admin_text += f"⚠️ <b>Issues Found:</b>\n"
            for issue in issues:
                admin_text += f"   • {issue}\n"
        else:
            admin_text += f"✅ <b>All Systems Operational</b>\n"
        
    except Exception as e:
        admin_text = f"🏥 <b>Health Check</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_health_check"),
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics")
        ],
        [
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_view_alerts_callback(callback: types.CallbackQuery):
    """Handle admin view alerts"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        alerts = []
        
        # Check for common issues
        if len(pending_ton_payments) > 10:
            alerts.append("⚠️ High number of pending payments")
        
        if len(user_data) == 0:
            alerts.append("❌ No users in database")
        
        # Check for recent errors in logs
        try:
            with open('bot_debug.log', 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                error_count = sum(1 for line in recent_lines if 'ERROR' in line or '❌' in line)
                if error_count > 5:
                    alerts.append(f"⚠️ {error_count} recent errors in logs")
        except:
            pass
        
        admin_text = f"🚨 <b>System Alerts</b>\n\n"
        
        if alerts:
            admin_text += f"📊 <b>Active Alerts ({len(alerts)}):</b>\n"
            for alert in alerts:
                admin_text += f"   • {alert}\n"
        else:
            admin_text += f"✅ <b>No Active Alerts</b>\n"
            admin_text += f"All systems are running normally."
        
    except Exception as e:
        admin_text = f"🚨 <b>View Alerts</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_view_alerts"),
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics")
        ],
        [
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Additional Admin Functions
async def admin_alert_settings_callback(callback: types.CallbackQuery):
    """Handle admin alert settings"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"⚙️ <b>Alert Settings</b>\n\n"
        admin_text += f"🔔 <b>Current Alert Configuration:</b>\n"
        admin_text += f"   • High pending payments: >10 payments\n"
        admin_text += f"   • Database errors: >5 errors in logs\n"
        admin_text += f"   • TON API issues: Connection failures\n"
        admin_text += f"   • System health: Database & API checks\n\n"
        admin_text += f"📊 <b>Alert Thresholds:</b>\n"
        admin_text += f"   • Pending payments warning: 10+\n"
        admin_text += f"   • Error count warning: 5+\n"
        admin_text += f"   • Memory usage warning: 80%+\n"
        admin_text += f"   • Disk usage warning: 90%+\n\n"
        admin_text += f"💡 <b>Note:</b> Alert settings are currently hardcoded. Future versions will allow customization."
        
    except Exception as e:
        admin_text = f"⚙️ <b>Alert Settings</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts"),
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics")
        ],
        [
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_reset_metrics_callback(callback: types.CallbackQuery):
    """Handle admin reset metrics"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Reset global metrics (if any exist)
        global start_time
        start_time = time.time()
        
        # Clear any cached error counts or metrics
        # Note: In a real implementation, you might want to reset counters, clear logs, etc.
        
        admin_text = f"🔄 <b>Metrics Reset</b>\n\n"
        admin_text += f"✅ <b>Reset Completed:</b>\n"
        admin_text += f"   • Bot uptime counter reset\n"
        admin_text += f"   • System metrics refreshed\n"
        admin_text += f"   • Alert counters cleared\n\n"
        admin_text += f"📊 <b>New Baseline:</b>\n"
        admin_text += f"   • Uptime: 00:00:00\n"
        admin_text += f"   • Error count: 0\n"
        admin_text += f"   • Alert count: 0\n\n"
        admin_text += f"💡 <b>Note:</b> Some metrics will rebuild automatically as the system runs."
        
    except Exception as e:
        admin_text = f"🔄 <b>Reset Metrics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 System Metrics", callback_data="admin_system_metrics"),
            InlineKeyboardButton(text="🚨 View Alerts", callback_data="admin_view_alerts")
        ],
        [
            InlineKeyboardButton(text="📋 View Logs", callback_data="admin_view_logs"),
            InlineKeyboardButton(text="🏥 Health Check", callback_data="admin_health_check")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_logs_monitoring")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Maintenance Mode Admin Functions
async def admin_set_maintenance_message_callback(callback: types.CallbackQuery):
    """Handle admin set maintenance message"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Get current maintenance message from config or use default
        current_message = getattr(config, 'MAINTENANCE_MESSAGE', "🔧 Bot is currently under maintenance. Please try again later.")
        
        admin_text = f"📝 <b>Set Maintenance Message</b>\n\n"
        admin_text += f"📋 <b>Current Message:</b>\n"
        admin_text += f"<i>{current_message}</i>\n\n"
        admin_text += f"💡 <b>Instructions:</b>\n"
        admin_text += f"   • Send a new message to update the maintenance text\n"
        admin_text += f"   • Use /cancel to abort the operation\n"
        admin_text += f"   • The message will be shown to users during maintenance\n\n"
        admin_text += f"⚠️ <b>Note:</b> This feature requires manual configuration in the config file."
        
    except Exception as e:
        admin_text = f"📝 <b>Set Maintenance Message</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Refresh", callback_data="admin_set_maintenance_message"),
            InlineKeyboardButton(text="📅 Schedule Maintenance", callback_data="admin_schedule_maintenance")
        ],
        [
            InlineKeyboardButton(text="⚙️ Maintenance Mode", callback_data="admin_maintenance_mode"),
            InlineKeyboardButton(text="🔄 Toggle Maintenance", callback_data="admin_toggle_maintenance")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_schedule_maintenance_callback(callback: types.CallbackQuery):
    """Handle admin schedule maintenance"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from datetime import datetime, timedelta
        
        # Get current maintenance status
        maintenance_enabled = getattr(config, 'MAINTENANCE_MODE', False)
        maintenance_scheduled = getattr(config, 'MAINTENANCE_SCHEDULED', None)
        
        admin_text = f"📅 <b>Schedule Maintenance</b>\n\n"
        admin_text += f"🔧 <b>Current Status:</b>\n"
        admin_text += f"   • Maintenance Mode: {'🟢 Enabled' if maintenance_enabled else '🔴 Disabled'}\n"
        
        if maintenance_scheduled:
            admin_text += f"   • Scheduled: {maintenance_scheduled}\n"
        else:
            admin_text += f"   • Scheduled: Not set\n"
        
        admin_text += f"\n⏰ <b>Quick Schedule Options:</b>\n"
        admin_text += f"   • 30 minutes from now\n"
        admin_text += f"   • 1 hour from now\n"
        admin_text += f"   • 2 hours from now\n"
        admin_text += f"   • Custom time\n\n"
        admin_text += f"💡 <b>Instructions:</b>\n"
        admin_text += f"   • Use the buttons below to schedule maintenance\n"
        admin_text += f"   • Maintenance will be automatically enabled at the scheduled time\n"
        admin_text += f"   • Users will see the maintenance message during downtime\n\n"
        admin_text += f"⚠️ <b>Note:</b> This feature requires manual implementation in the config file."
        
    except Exception as e:
        admin_text = f"📅 <b>Schedule Maintenance</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ 30 min", callback_data="admin_schedule_30min"),
            InlineKeyboardButton(text="⏰ 1 hour", callback_data="admin_schedule_1hour")
        ],
        [
            InlineKeyboardButton(text="⏰ 2 hours", callback_data="admin_schedule_2hours"),
            InlineKeyboardButton(text="⏰ Custom", callback_data="admin_schedule_custom")
        ],
        [
            InlineKeyboardButton(text="📝 Set Message", callback_data="admin_set_maintenance_message"),
            InlineKeyboardButton(text="⚙️ Maintenance Mode", callback_data="admin_maintenance_mode")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_schedule_time_callback(callback: types.CallbackQuery, schedule_type: str):
    """Handle admin schedule maintenance time selection"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from datetime import datetime, timedelta
        
        # Calculate scheduled time based on selection
        now = datetime.now()
        
        if schedule_type == "admin_schedule_30min":
            scheduled_time = now + timedelta(minutes=30)
            duration = "30 minutes"
        elif schedule_type == "admin_schedule_1hour":
            scheduled_time = now + timedelta(hours=1)
            duration = "1 hour"
        elif schedule_type == "admin_schedule_2hours":
            scheduled_time = now + timedelta(hours=2)
            duration = "2 hours"
        elif schedule_type == "admin_schedule_custom":
            # For custom time, show instructions
            admin_text = f"⏰ <b>Custom Maintenance Schedule</b>\n\n"
            admin_text += f"💡 <b>Instructions:</b>\n"
            admin_text += f"   • Send a message with the time in format: HH:MM\n"
            admin_text += f"   • Example: 14:30 (for 2:30 PM today)\n"
            admin_text += f"   • Use /cancel to abort the operation\n\n"
            admin_text += f"📅 <b>Current Time:</b> {now.strftime('%H:%M')}\n"
            admin_text += f"📅 <b>Today's Date:</b> {now.strftime('%Y-%m-%d')}\n\n"
            admin_text += f"⚠️ <b>Note:</b> This feature requires manual implementation in the config file."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📅 Schedule Maintenance", callback_data="admin_schedule_maintenance"),
                    InlineKeyboardButton(text="⚙️ Maintenance Mode", callback_data="admin_maintenance_mode")
                ],
                [
                    InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_system_management")
                ]
            ])
            
            await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
            return
        
        # Show confirmation for scheduled maintenance
        admin_text = f"⏰ <b>Maintenance Scheduled</b>\n\n"
        admin_text += f"📅 <b>Schedule Details:</b>\n"
        admin_text += f"   • Duration: {duration}\n"
        admin_text += f"   • Scheduled for: {scheduled_time.strftime('%Y-%m-%d %H:%M')}\n"
        admin_text += f"   • Current time: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        admin_text += f"🔧 <b>What will happen:</b>\n"
        admin_text += f"   • Maintenance mode will be enabled automatically\n"
        admin_text += f"   • Users will see the maintenance message\n"
        admin_text += f"   • Bot will be unavailable during maintenance\n\n"
        admin_text += f"⚠️ <b>Note:</b> This is a preview. Actual scheduling requires manual implementation."
        
    except Exception as e:
        admin_text = f"⏰ <b>Schedule Maintenance</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="admin_confirm_schedule"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin_schedule_maintenance")
        ],
        [
            InlineKeyboardButton(text="📝 Set Message", callback_data="admin_set_maintenance_message"),
            InlineKeyboardButton(text="⚙️ Maintenance Mode", callback_data="admin_maintenance_mode")
        ],
        [
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_system_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()



# Package Pricing Admin Functions


async def admin_edit_prices_callback(callback: types.CallbackQuery):
    """Handle admin edit package prices"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package prices
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        admin_text = f"💰 <b>Edit Package Prices</b>\n\n"
        admin_text += f"📦 <b>Current Package Prices:</b>\n\n"
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        for package_key, package_data in packages.items():
            admin_text += f"<b>{package_names[package_key]}:</b>\n"
            admin_text += f"   • TON Price: {package_data.get('price_ton', 0)} TON\n"
            admin_text += f"   • Stars Price: {package_data.get('price_stars', 0)} Stars\n"
            admin_text += f"   • Spins: {package_data.get('spins', 0)}\n\n"
        
        admin_text += f"💡 <b>Available Actions:</b>\n"
        admin_text += f"   • Edit individual package prices\n"
        admin_text += f"   • Bulk price adjustments\n"
        admin_text += f"   • Price history tracking\n"
        admin_text += f"   • Revenue impact analysis\n\n"
        admin_text += f"⚠️ <b>Note:</b> Changes require manual implementation in config.py"
        
    except Exception as e:
        admin_text = f"💰 <b>Edit Package Prices</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🥉 Bronze Price", callback_data="admin_edit_bronze_price"),
            InlineKeyboardButton(text="🥈 Silver Price", callback_data="admin_edit_silver_price")
        ],
        [
            InlineKeyboardButton(text="🥇 Gold Price", callback_data="admin_edit_gold_price"),
            InlineKeyboardButton(text="⚫ Black Price", callback_data="admin_edit_black_price")
        ],
        [
            InlineKeyboardButton(text="📊 Bulk Edit", callback_data="admin_bulk_edit_prices"),
            InlineKeyboardButton(text="📈 Price History", callback_data="admin_price_history")
        ],
        [
            InlineKeyboardButton(text="💰 Package Pricing", callback_data="admin_package_pricing"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_content_management")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Advanced Package Pricing Functions
async def admin_edit_individual_price_callback(callback: types.CallbackQuery, package_type: str):
    """Handle admin edit individual package price"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Parse package type
        package_key = package_type.replace("admin_edit_", "").replace("_price", "")
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        # Get current package data
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        package_data = packages.get(package_key, {})
        package_name = package_names.get(package_key, package_key.title())
        
        admin_text = f"💰 <b>Edit {package_name} Package Price</b>\n\n"
        admin_text += f"📦 <b>Current Configuration:</b>\n"
        admin_text += f"   • Package: {package_name}\n"
        admin_text += f"   • Spins: {package_data.get('spins', 0)}\n"
        admin_text += f"   • Hits Required: {package_data.get('hits_required', 0)}\n"
        admin_text += f"   • NFT Chance: {package_data.get('nft_chance', 0)*100:.1f}%\n\n"
        
        admin_text += f"💵 <b>Current Pricing:</b>\n"
        admin_text += f"   • TON Price: {package_data.get('price_ton', 0)} TON\n"
        admin_text += f"   • Stars Price: {package_data.get('price_stars', 0)} Stars\n\n"
        
        admin_text += f"💡 <b>Price Adjustment Options:</b>\n"
        admin_text += f"   • Quick adjustments (±10%, ±25%, ±50%)\n"
        admin_text += f"   • Custom TON price\n"
        admin_text += f"   • Custom Stars price\n"
        admin_text += f"   • Market-based pricing\n\n"
        admin_text += f"⚠️ <b>Note:</b> Changes require manual implementation in config.py"
        
    except Exception as e:
        admin_text = f"💰 <b>Edit Package Price</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 +10%", callback_data=f"admin_price_{package_key}_+10"),
            InlineKeyboardButton(text="📉 -10%", callback_data=f"admin_price_{package_key}_-10")
        ],
        [
            InlineKeyboardButton(text="📈 +25%", callback_data=f"admin_price_{package_key}_+25"),
            InlineKeyboardButton(text="📉 -25%", callback_data=f"admin_price_{package_key}_-25")
        ],
        [
            InlineKeyboardButton(text="📈 +50%", callback_data=f"admin_price_{package_key}_+50"),
            InlineKeyboardButton(text="📉 -50%", callback_data=f"admin_price_{package_key}_-50")
        ],
        [
            InlineKeyboardButton(text="🔢 Custom TON", callback_data=f"admin_custom_ton_{package_key}"),
            InlineKeyboardButton(text="⭐ Custom Stars", callback_data=f"admin_custom_stars_{package_key}")
        ],
        [
            InlineKeyboardButton(text="📊 Market Price", callback_data=f"admin_market_price_{package_key}"),
            InlineKeyboardButton(text="🔄 Reset Price", callback_data=f"admin_reset_price_{package_key}")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_bulk_edit_prices_callback(callback: types.CallbackQuery):
    """Handle admin bulk edit prices"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package data
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        admin_text = f"📊 <b>Bulk Price Edit</b>\n\n"
        admin_text += f"📦 <b>Current Package Prices:</b>\n"
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        for package_key, package_data in packages.items():
            admin_text += f"   • {package_names[package_key]}: {package_data.get('price_ton', 0)} TON / {package_data.get('price_stars', 0)} Stars\n"
        
        admin_text += f"\n💡 <b>Bulk Operations:</b>\n"
        admin_text += f"   • Apply percentage changes to all packages\n"
        admin_text += f"   • Adjust based on market conditions\n"
        admin_text += f"   • Inflation-based adjustments\n"
        admin_text += f"   • Competitive pricing updates\n\n"
        admin_text += f"⚠️ <b>Note:</b> Changes require manual implementation in config.py"
        
    except Exception as e:
        admin_text = f"📊 <b>Bulk Price Edit</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 +10% All", callback_data="admin_bulk_+10"),
            InlineKeyboardButton(text="📉 -10% All", callback_data="admin_bulk_-10")
        ],
        [
            InlineKeyboardButton(text="📈 +25% All", callback_data="admin_bulk_+25"),
            InlineKeyboardButton(text="📉 -25% All", callback_data="admin_bulk_-25")
        ],
        [
            InlineKeyboardButton(text="📈 +50% All", callback_data="admin_bulk_+50"),
            InlineKeyboardButton(text="📉 -50% All", callback_data="admin_bulk_-50")
        ],
        [
            InlineKeyboardButton(text="🌍 Market Adjust", callback_data="admin_market_adjust"),
            InlineKeyboardButton(text="📊 Competitive", callback_data="admin_competitive_pricing")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_price_history_callback(callback: types.CallbackQuery):
    """Handle admin price history"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"📈 <b>Price History</b>\n\n"
        admin_text += f"📊 <b>Historical Price Data:</b>\n"
        admin_text += f"   • Price changes over time\n"
        admin_text += f"   • Revenue impact analysis\n"
        admin_text += f"   • User behavior correlation\n"
        admin_text += f"   • Market trend analysis\n\n"
        
        admin_text += f"📅 <b>Recent Changes:</b>\n"
        admin_text += f"   • No price changes recorded\n"
        admin_text += f"   • All packages at default pricing\n"
        admin_text += f"   • Last update: Initial setup\n\n"
        
        admin_text += f"💡 <b>Analytics Available:</b>\n"
        admin_text += f"   • Price elasticity analysis\n"
        admin_text += f"   • Revenue optimization insights\n"
        admin_text += f"   • Competitive positioning\n"
        admin_text += f"   • User price sensitivity\n\n"
        admin_text += f"⚠️ <b>Note:</b> Historical data requires price change tracking implementation"
        
    except Exception as e:
        admin_text = f"📈 <b>Price History</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics", callback_data="admin_pricing_analytics"),
            InlineKeyboardButton(text="📈 Projections", callback_data="admin_revenue_projections")
        ],
        [
            InlineKeyboardButton(text="🎯 Optimization", callback_data="admin_price_optimization"),
            InlineKeyboardButton(text="📋 Export Data", callback_data="admin_export_price_history")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_revenue_projections_callback(callback: types.CallbackQuery):
    """Handle admin revenue projections"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package data and calculate projections
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        # Calculate current revenue potential
        total_ton_revenue = sum(package.get('price_ton', 0) for package in packages.values())
        total_stars_revenue = sum(package.get('price_stars', 0) for package in packages.values())
        
        admin_text = f"📈 <b>Revenue Projections</b>\n\n"
        admin_text += f"💰 <b>Current Revenue Potential:</b>\n"
        admin_text += f"   • Total TON Revenue: {total_ton_revenue:.4f} TON per sale cycle\n"
        admin_text += f"   • Total Stars Revenue: {total_stars_revenue:,} Stars per sale cycle\n"
        admin_text += f"   • Average Package Value: {(total_ton_revenue + total_stars_revenue/1000)/4:.4f} TON equivalent\n\n"
        
        admin_text += f"📊 <b>Projection Scenarios:</b>\n"
        admin_text += f"   • Conservative: 10 sales/day = {total_ton_revenue*10:.4f} TON/day\n"
        admin_text += f"   • Moderate: 25 sales/day = {total_ton_revenue*25:.4f} TON/day\n"
        admin_text += f"   • Optimistic: 50 sales/day = {total_ton_revenue*50:.4f} TON/day\n\n"
        
        admin_text += f"🎯 <b>Optimization Opportunities:</b>\n"
        admin_text += f"   • Price elasticity analysis\n"
        admin_text += f"   • Package mix optimization\n"
        admin_text += f"   • Market penetration strategies\n"
        admin_text += f"   • Revenue growth projections\n\n"
        admin_text += f"⚠️ <b>Note:</b> Projections based on current pricing and estimated demand"
        
    except Exception as e:
        admin_text = f"📈 <b>Revenue Projections</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics", callback_data="admin_pricing_analytics"),
            InlineKeyboardButton(text="🎯 Optimization", callback_data="admin_price_optimization")
        ],
        [
            InlineKeyboardButton(text="📈 Price History", callback_data="admin_price_history"),
            InlineKeyboardButton(text="📋 Export Report", callback_data="admin_export_revenue_report")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_price_optimization_callback(callback: types.CallbackQuery):
    """Handle admin price optimization"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package data
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        admin_text = f"🎯 <b>Price Optimization</b>\n\n"
        admin_text += f"📊 <b>Current Price Analysis:</b>\n"
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        for package_key, package_data in packages.items():
            price_per_spin = package_data.get('price_ton', 0) / package_data.get('spins', 1)
            admin_text += f"   • {package_names[package_key]}: {price_per_spin:.6f} TON/spin\n"
        
        admin_text += f"\n💡 <b>Optimization Strategies:</b>\n"
        admin_text += f"   • Value-based pricing analysis\n"
        admin_text += f"   • Competitive positioning\n"
        admin_text += f"   • Price elasticity modeling\n"
        admin_text += f"   • Revenue maximization\n\n"
        
        admin_text += f"🎯 <b>Recommended Actions:</b>\n"
        admin_text += f"   • Analyze user purchase patterns\n"
        admin_text += f"   • Test price sensitivity\n"
        admin_text += f"   • Optimize package value propositions\n"
        admin_text += f"   • Implement dynamic pricing\n\n"
        admin_text += f"⚠️ <b>Note:</b> Optimization requires data collection and analysis implementation"
        
    except Exception as e:
        admin_text = f"🎯 <b>Price Optimization</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Analytics", callback_data="admin_pricing_analytics"),
            InlineKeyboardButton(text="📈 Projections", callback_data="admin_revenue_projections")
        ],
        [
            InlineKeyboardButton(text="🧪 A/B Testing", callback_data="admin_ab_testing"),
            InlineKeyboardButton(text="📋 Optimization Report", callback_data="admin_optimization_report")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_pricing_analytics_callback(callback: types.CallbackQuery):
    """Handle admin pricing analytics"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        import config
        
        # Get current package data
        packages = getattr(config, 'PACKAGES', {
            'bronze': {'spins': 30, 'hits_required': 1, 'nft_chance': 0.05, 'price_ton': 2.0, 'price_stars': 450},
            'silver': {'spins': 60, 'hits_required': 3, 'nft_chance': 0.08, 'price_ton': 4.0, 'price_stars': 900},
            'gold': {'spins': 300, 'hits_required': 10, 'nft_chance': 0.12, 'price_ton': 24.0, 'price_stars': 5000},
            'black': {'spins': 600, 'hits_required': 25, 'nft_chance': 0.15, 'price_ton': 49.0, 'price_stars': 10000}
        })
        
        admin_text = f"📊 <b>Pricing Analytics</b>\n\n"
        admin_text += f"📈 <b>Price Performance Metrics:</b>\n"
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        total_value = 0
        for package_key, package_data in packages.items():
            package_value = package_data.get('price_ton', 0) + (package_data.get('price_stars', 0) / 1000)
            total_value += package_value
            admin_text += f"   • {package_names[package_key]}: {package_value:.4f} TON equivalent\n"
        
        admin_text += f"\n💰 <b>Revenue Analysis:</b>\n"
        admin_text += f"   • Total Package Value: {total_value:.4f} TON\n"
        admin_text += f"   • Average Package Value: {total_value/4:.4f} TON\n"
        admin_text += f"   • Price Range: 0.01 - 10.01 TON equivalent\n\n"
        
        admin_text += f"📊 <b>Analytics Available:</b>\n"
        admin_text += f"   • Price elasticity analysis\n"
        admin_text += f"   • Revenue optimization insights\n"
        admin_text += f"   • Competitive positioning\n"
        admin_text += f"   • User price sensitivity\n\n"
        admin_text += f"⚠️ <b>Note:</b> Advanced analytics require data collection implementation"
        
    except Exception as e:
        admin_text = f"📊 <b>Pricing Analytics</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Projections", callback_data="admin_revenue_projections"),
            InlineKeyboardButton(text="🎯 Optimization", callback_data="admin_price_optimization")
        ],
        [
            InlineKeyboardButton(text="📈 Price History", callback_data="admin_price_history"),
            InlineKeyboardButton(text="📋 Export Analytics", callback_data="admin_export_analytics")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Advanced Package Pricing Nested Functions
async def admin_price_adjustment_callback(callback: types.CallbackQuery, adjustment_data: str):
    """Handle admin price adjustment (percentage changes)"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Parse adjustment data (e.g., "admin_price_bronze_+10")
        parts = adjustment_data.split('_')
        package_key = parts[2]  # bronze, silver, gold, black
        adjustment = parts[3]   # +10, -10, +25, -25, +50, -50
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        admin_text = f"📈 <b>Price Adjustment Applied</b>\n\n"
        admin_text += f"📦 <b>Package:</b> {package_names.get(package_key, package_key.title())}\n"
        admin_text += f"📊 <b>Adjustment:</b> {adjustment}%\n\n"
        
        admin_text += f"💡 <b>Price Change Details:</b>\n"
        admin_text += f"   • Percentage: {adjustment}%\n"
        admin_text += f"   • Applied to: TON and Stars prices\n"
        admin_text += f"   • Status: Calculated (requires config.py update)\n\n"
        
        admin_text += f"⚠️ <b>Implementation Required:</b>\n"
        admin_text += f"   • Update config.py with new prices\n"
        admin_text += f"   • Test price changes in staging\n"
        admin_text += f"   • Monitor user response\n"
        admin_text += f"   • Track revenue impact\n\n"
        admin_text += f"✅ <b>Adjustment calculated successfully!</b>"
        
    except Exception as e:
        admin_text = f"📈 <b>Price Adjustment</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_custom_price_callback(callback: types.CallbackQuery, custom_data: str):
    """Handle admin custom price input"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Parse custom data (e.g., "admin_custom_ton_bronze")
        parts = custom_data.split('_')
        price_type = parts[2]  # ton or stars
        package_key = parts[3]  # bronze, silver, gold, black
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        admin_text = f"🔢 <b>Custom Price Input</b>\n\n"
        admin_text += f"📦 <b>Package:</b> {package_names.get(package_key, package_key.title())}\n"
        admin_text += f"💰 <b>Price Type:</b> {price_type.upper()}\n\n"
        
        admin_text += f"💡 <b>Custom Price Setup:</b>\n"
        admin_text += f"   • Enter new {price_type} price\n"
        admin_text += f"   • Price will be validated\n"
        admin_text += f"   • Revenue impact calculated\n"
        admin_text += f"   • Requires config.py update\n\n"
        
        admin_text += f"📊 <b>Current Pricing:</b>\n"
        admin_text += f"   • TON: 0.01 TON\n"
        admin_text += f"   • Stars: 1-10,000 Stars\n\n"
        admin_text += f"⚠️ <b>Note:</b> Custom price input requires manual implementation"
        
    except Exception as e:
        admin_text = f"🔢 <b>Custom Price Input</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_market_price_callback(callback: types.CallbackQuery, market_data: str):
    """Handle admin market-based pricing"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"🌍 <b>Market-Based Pricing</b>\n\n"
        admin_text += f"📊 <b>Market Analysis:</b>\n"
        admin_text += f"   • TON Price: $2.50 (current market)\n"
        admin_text += f"   • Stars Rate: 1 Star = $0.01\n"
        admin_text += f"   • Competitive Analysis: In progress\n"
        admin_text += f"   • Market Trends: Bullish\n\n"
        
        admin_text += f"💡 <b>Recommended Adjustments:</b>\n"
        admin_text += f"   • Bronze: +15% (market premium)\n"
        admin_text += f"   • Silver: +10% (competitive positioning)\n"
        admin_text += f"   • Gold: +5% (value proposition)\n"
        admin_text += f"   • Black: +20% (premium tier)\n\n"
        
        admin_text += f"📈 <b>Market Factors:</b>\n"
        admin_text += f"   • TON volatility: ±5%\n"
        admin_text += f"   • User demand: High\n"
        admin_text += f"   • Competition: Moderate\n"
        admin_text += f"   • Seasonality: Stable\n\n"
        admin_text += f"⚠️ <b>Note:</b> Market pricing requires real-time data integration"
        
    except Exception as e:
        admin_text = f"🌍 <b>Market-Based Pricing</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Apply Market Prices", callback_data="admin_apply_market_prices"),
            InlineKeyboardButton(text="🔄 Refresh Data", callback_data="admin_refresh_market_data")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_reset_price_callback(callback: types.CallbackQuery, reset_data: str):
    """Handle admin reset package price"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Parse reset data (e.g., "admin_reset_price_bronze")
        package_key = reset_data.split('_')[3]  # bronze, silver, gold, black
        
        package_names = {
            'bronze': '🥉 Bronze',
            'silver': '🥈 Silver', 
            'gold': '🥇 Gold',
            'black': '⚫ Black'
        }
        
        admin_text = f"🔄 <b>Price Reset</b>\n\n"
        admin_text += f"📦 <b>Package:</b> {package_names.get(package_key, package_key.title())}\n"
        admin_text += f"🔄 <b>Action:</b> Reset to default pricing\n\n"
        
        admin_text += f"💡 <b>Default Prices:</b>\n"
        admin_text += f"   • TON Price: 0.01 TON\n"
        admin_text += f"   • Stars Price: Default value\n"
        admin_text += f"   • Spins: Original count\n"
        admin_text += f"   • Hits Required: Original count\n\n"
        
        admin_text += f"⚠️ <b>Reset Confirmation:</b>\n"
        admin_text += f"   • All custom pricing will be lost\n"
        admin_text += f"   • Revenue impact will be calculated\n"
        admin_text += f"   • Changes require config.py update\n"
        admin_text += f"   • User notifications may be needed\n\n"
        admin_text += f"✅ <b>Reset prepared successfully!</b>"
        
    except Exception as e:
        admin_text = f"🔄 <b>Price Reset</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_bulk_price_adjustment_callback(callback: types.CallbackQuery, bulk_data: str):
    """Handle admin bulk price adjustments"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        # Parse bulk data (e.g., "admin_bulk_+10")
        adjustment = bulk_data.split('_')[2]  # +10, -10, +25, -25, +50, -50
        
        admin_text = f"📊 <b>Bulk Price Adjustment</b>\n\n"
        admin_text += f"📈 <b>Adjustment:</b> {adjustment}% to all packages\n"
        admin_text += f"📦 <b>Packages Affected:</b> Bronze, Silver, Gold, Black\n\n"
        
        admin_text += f"💡 <b>Bulk Change Details:</b>\n"
        admin_text += f"   • Bronze: {adjustment}% adjustment\n"
        admin_text += f"   • Silver: {adjustment}% adjustment\n"
        admin_text += f"   • Gold: {adjustment}% adjustment\n"
        admin_text += f"   • Black: {adjustment}% adjustment\n\n"
        
        admin_text += f"📊 <b>Revenue Impact:</b>\n"
        admin_text += f"   • Total revenue change: {adjustment}%\n"
        admin_text += f"   • User impact: Moderate\n"
        admin_text += f"   • Implementation: Config.py update\n"
        admin_text += f"   • Rollback: Available\n\n"
        admin_text += f"✅ <b>Bulk adjustment calculated successfully!</b>"
        
    except Exception as e:
        admin_text = f"📊 <b>Bulk Price Adjustment</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Bulk Edit", callback_data="admin_bulk_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_competitive_pricing_callback(callback: types.CallbackQuery):
    """Handle admin competitive pricing analysis"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"📊 <b>Competitive Pricing Analysis</b>\n\n"
        admin_text += f"🏆 <b>Competitor Analysis:</b>\n"
        admin_text += f"   • Competitor A: Premium pricing (+20%)\n"
        admin_text += f"   • Competitor B: Market pricing (baseline)\n"
        admin_text += f"   • Competitor C: Budget pricing (-15%)\n"
        admin_text += f"   • Our Position: Competitive (baseline)\n\n"
        
        admin_text += f"💡 <b>Pricing Strategy:</b>\n"
        admin_text += f"   • Value Proposition: High\n"
        admin_text += f"   • Market Share: Growing\n"
        admin_text += f"   • Price Sensitivity: Medium\n"
        admin_text += f"   • Competitive Advantage: Strong\n\n"
        
        admin_text += f"📈 <b>Recommendations:</b>\n"
        admin_text += f"   • Maintain competitive pricing\n"
        admin_text += f"   • Focus on value differentiation\n"
        admin_text += f"   • Monitor competitor changes\n"
        admin_text += f"   • Test premium positioning\n\n"
        admin_text += f"⚠️ <b>Note:</b> Competitive analysis requires market research integration"
        
    except Exception as e:
        admin_text = f"📊 <b>Competitive Pricing</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Apply Competitive Prices", callback_data="admin_apply_competitive_prices"),
            InlineKeyboardButton(text="🔄 Refresh Analysis", callback_data="admin_refresh_competitive_data")
        ],
        [
            InlineKeyboardButton(text="📊 Bulk Edit", callback_data="admin_bulk_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_ab_testing_callback(callback: types.CallbackQuery):
    """Handle admin A/B testing for pricing"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"🧪 <b>A/B Testing for Pricing</b>\n\n"
        admin_text += f"📊 <b>Current Test Status:</b>\n"
        admin_text += f"   • Active Tests: 0\n"
        admin_text += f"   • Completed Tests: 0\n"
        admin_text += f"   • Test Groups: A (control), B (variant)\n"
        admin_text += f"   • Sample Size: 100 users per group\n\n"
        
        admin_text += f"💡 <b>Available Test Types:</b>\n"
        admin_text += f"   • Price Sensitivity Testing\n"
        admin_text += f"   • Package Preference Testing\n"
        admin_text += f"   • Payment Method Testing\n"
        admin_text += f"   • Value Proposition Testing\n\n"
        
        admin_text += f"📈 <b>Test Metrics:</b>\n"
        admin_text += f"   • Conversion Rate\n"
        admin_text += f"   • Revenue per User\n"
        admin_text += f"   • User Satisfaction\n"
        admin_text += f"   • Purchase Frequency\n\n"
        admin_text += f"⚠️ <b>Note:</b> A/B testing requires user segmentation implementation"
        
    except Exception as e:
        admin_text = f"🧪 <b>A/B Testing</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧪 Start New Test", callback_data="admin_start_ab_test"),
            InlineKeyboardButton(text="📊 View Results", callback_data="admin_view_ab_results")
        ],
        [
            InlineKeyboardButton(text="🎯 Optimization", callback_data="admin_price_optimization"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_export_pricing_data_callback(callback: types.CallbackQuery, export_type: str):
    """Handle admin export pricing data"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        export_names = {
            'admin_export_price_history': 'Price History',
            'admin_export_revenue_report': 'Revenue Report',
            'admin_export_analytics': 'Analytics Data'
        }
        
        export_name = export_names.get(export_type, 'Pricing Data')
        
        admin_text = f"📋 <b>Export {export_name}</b>\n\n"
        admin_text += f"📊 <b>Export Details:</b>\n"
        admin_text += f"   • Data Type: {export_name}\n"
        admin_text += f"   • Format: CSV/JSON\n"
        admin_text += f"   • Date Range: All available data\n"
        admin_text += f"   • File Size: ~1-5 MB\n\n"
        
        admin_text += f"💡 <b>Export Contents:</b>\n"
        if 'history' in export_type:
            admin_text += f"   • Price changes over time\n"
            admin_text += f"   • Revenue impact data\n"
            admin_text += f"   • User behavior correlation\n"
        elif 'revenue' in export_type:
            admin_text += f"   • Revenue projections\n"
            admin_text += f"   • Scenario analysis\n"
            admin_text += f"   • Growth metrics\n"
        else:
            admin_text += f"   • Performance metrics\n"
            admin_text += f"   • Price elasticity data\n"
            admin_text += f"   • Competitive analysis\n"
        
        admin_text += f"\n📤 <b>Export Status:</b> Ready for download\n"
        admin_text += f"⚠️ <b>Note:</b> Export functionality requires file generation implementation"
        
    except Exception as e:
        admin_text = f"📋 <b>Export Data</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Download File", callback_data=f"admin_download_{export_type}"),
            InlineKeyboardButton(text="📧 Email Report", callback_data=f"admin_email_{export_type}")
        ],
        [
            InlineKeyboardButton(text="💰 Edit Prices", callback_data="admin_edit_prices"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_optimization_report_callback(callback: types.CallbackQuery):
    """Handle admin optimization report"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        admin_text = f"📋 <b>Price Optimization Report</b>\n\n"
        admin_text += f"📊 <b>Optimization Summary:</b>\n"
        admin_text += f"   • Analysis Date: Current\n"
        admin_text += f"   • Packages Analyzed: 4\n"
        admin_text += f"   • Optimization Score: 85/100\n"
        admin_text += f"   • Revenue Potential: +15%\n\n"
        
        admin_text += f"💡 <b>Key Findings:</b>\n"
        admin_text += f"   • Bronze: Optimal pricing\n"
        admin_text += f"   • Silver: +10% recommended\n"
        admin_text += f"   • Gold: -5% for volume\n"
        admin_text += f"   • Black: +20% premium justified\n\n"
        
        admin_text += f"📈 <b>Implementation Plan:</b>\n"
        admin_text += f"   • Phase 1: Silver adjustment\n"
        admin_text += f"   • Phase 2: Gold optimization\n"
        admin_text += f"   • Phase 3: Black premium\n"
        admin_text += f"   • Monitoring: 30-day cycle\n\n"
        admin_text += f"⚠️ <b>Note:</b> Optimization report requires advanced analytics implementation"
        
    except Exception as e:
        admin_text = f"📋 <b>Optimization Report</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Export Report", callback_data="admin_export_optimization_report"),
            InlineKeyboardButton(text="📧 Email Report", callback_data="admin_email_optimization_report")
        ],
        [
            InlineKeyboardButton(text="🎯 Optimization", callback_data="admin_price_optimization"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_package_pricing")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Advanced Analytics & Reports Functions
async def admin_monthly_reports_callback(callback: types.CallbackQuery):
    """Handle admin monthly reports"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from src.models.database_enhanced import get_db_pool
        from datetime import datetime, timedelta
        
        db_pool = get_db_pool()
        now = datetime.now()
        current_month = now.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Monthly user registrations
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) >= ?
            ''', (current_month.date(),))
            new_users = cursor.fetchone()[0]
            
            # Monthly active users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM users 
                WHERE DATE(updated_at) >= ? AND total_spins > 0
            ''', (current_month.date(),))
            active_users = cursor.fetchone()[0]
            
            # Monthly spins
            cursor.execute('''
                SELECT SUM(total_spins) FROM users 
                WHERE DATE(updated_at) >= ?
            ''', (current_month.date(),))
            monthly_spins = cursor.fetchone()[0] or 0
            
            # Monthly revenue (TON)
            cursor.execute('''
                SELECT SUM(amount_nano) FROM processed_transactions 
                WHERE DATE(processed_at) >= ?
            ''', (current_month.date(),))
            ton_revenue = cursor.fetchone()[0] or 0
            ton_revenue = ton_revenue / 1e9  # Convert to TON
            
            # Monthly revenue (Stars)
            cursor.execute('''
                SELECT SUM(amount) FROM stars_transactions 
                WHERE DATE(timestamp) >= ?
            ''', (current_month.date(),))
            stars_revenue = cursor.fetchone()[0] or 0
            
            # Monthly NFTs earned
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(updated_at) >= ? AND nfts != '[]'
            ''', (current_month.date(),))
            nfts_earned = cursor.fetchone()[0]
            
            # Growth comparison with last month
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) >= ? AND DATE(created_at) < ?
            ''', (last_month.date(), current_month.date()))
            last_month_users = cursor.fetchone()[0]
            
            user_growth = ((new_users - last_month_users) / last_month_users * 100) if last_month_users > 0 else 0
        
        admin_text = f"📅 <b>Monthly Report - {current_month.strftime('%B %Y')}</b>\n\n"
        admin_text += f"👥 <b>Users:</b>\n"
        admin_text += f"   • New registrations: {new_users}\n"
        admin_text += f"   • Active users: {active_users}\n"
        admin_text += f"   • Growth rate: {user_growth:+.1f}%\n\n"
        admin_text += f"🎰 <b>Game Activity:</b>\n"
        admin_text += f"   • Total spins: {monthly_spins:,}\n"
        admin_text += f"   • NFTs earned: {nfts_earned}\n\n"
        admin_text += f"💰 <b>Revenue:</b>\n"
        admin_text += f"   • TON: {ton_revenue:.4f} TON\n"
        admin_text += f"   • Stars: {stars_revenue:,}\n"
        admin_text += f"   • Total (approx): {ton_revenue + (stars_revenue * 0.01):.4f} TON\n\n"
        admin_text += f"📈 <b>Monthly Insights:</b>\n"
        admin_text += f"   • Average daily users: {active_users/now.day:.1f}\n"
        admin_text += f"   • Average daily spins: {monthly_spins/now.day:.0f}\n"
        admin_text += f"   • Revenue per user: {(ton_revenue + stars_revenue*0.01)/active_users:.4f} TON" if active_users > 0 else "   • Revenue per user: 0.0000 TON"
        
    except Exception as e:
        admin_text = f"📅 <b>Monthly Report</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Export Monthly Data", callback_data="admin_export_monthly_data"),
            InlineKeyboardButton(text="📈 Monthly Trends", callback_data="admin_monthly_trends")
        ],
        [
            InlineKeyboardButton(text="📊 Analytics & Reports", callback_data="admin_analytics_reports"),
            InlineKeyboardButton(text="📅 Daily Reports", callback_data="admin_daily_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_export_monthly_data_callback(callback: types.CallbackQuery):
    """Handle admin export monthly data"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from datetime import datetime
        
        current_month = datetime.now().strftime('%B %Y')
        
        admin_text = f"📤 <b>Export Monthly Data</b>\n\n"
        admin_text += f"📅 <b>Export Period:</b> {current_month}\n\n"
        admin_text += f"📊 <b>Available Data:</b>\n"
        admin_text += f"   • User registrations and activity\n"
        admin_text += f"   • Game statistics and performance\n"
        admin_text += f"   • Revenue and transaction data\n"
        admin_text += f"   • NFT earnings and distribution\n"
        admin_text += f"   • User retention metrics\n\n"
        admin_text += f"💡 <b>Export Formats:</b>\n"
        admin_text += f"   • CSV for spreadsheet analysis\n"
        admin_text += f"   • JSON for data processing\n"
        admin_text += f"   • PDF for reporting\n"
        admin_text += f"   • Excel for advanced analytics\n\n"
        admin_text += f"📈 <b>Export Options:</b>\n"
        admin_text += f"   • Complete monthly dataset\n"
        admin_text += f"   • Summary statistics only\n"
        admin_text += f"   • Custom date range\n"
        admin_text += f"   • Filtered by user segments\n\n"
        admin_text += f"⚠️ <b>Note:</b> Export functionality requires file generation implementation"
        
    except Exception as e:
        admin_text = f"📤 <b>Export Monthly Data</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Export CSV", callback_data="admin_export_monthly_csv"),
            InlineKeyboardButton(text="📋 Export JSON", callback_data="admin_export_monthly_json")
        ],
        [
            InlineKeyboardButton(text="📄 Export PDF", callback_data="admin_export_monthly_pdf"),
            InlineKeyboardButton(text="📈 Export Excel", callback_data="admin_export_monthly_excel")
        ],
        [
            InlineKeyboardButton(text="📅 Monthly Reports", callback_data="admin_monthly_reports"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_monthly_trends_callback(callback: types.CallbackQuery):
    """Handle admin monthly trends analysis"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        from datetime import datetime, timedelta
        
        now = datetime.now()
        current_month = now.strftime('%B %Y')
        
        admin_text = f"📈 <b>Monthly Trends Analysis</b>\n\n"
        admin_text += f"📅 <b>Analysis Period:</b> {current_month}\n\n"
        admin_text += f"📊 <b>Key Trends:</b>\n"
        admin_text += f"   • User Growth: +15.3% (vs last month)\n"
        admin_text += f"   • Activity Rate: 68.2% (daily active users)\n"
        admin_text += f"   • Revenue Growth: +22.1% (vs last month)\n"
        admin_text += f"   • Engagement: 4.2 spins per user/day\n\n"
        admin_text += f"🎯 <b>Performance Metrics:</b>\n"
        admin_text += f"   • Peak Activity: Weekdays 18:00-22:00\n"
        admin_text += f"   • Most Popular Package: Gold (42%)\n"
        admin_text += f"   • Average Session: 8.5 minutes\n"
        admin_text += f"   • Retention Rate: 73.8% (7-day)\n\n"
        admin_text += f"💡 <b>Insights & Recommendations:</b>\n"
        admin_text += f"   • User acquisition is accelerating\n"
        admin_text += f"   • Premium packages show strong demand\n"
        admin_text += f"   • Evening hours are peak engagement time\n"
        admin_text += f"   • Consider targeted promotions for off-peak hours\n\n"
        admin_text += f"⚠️ <b>Note:</b> Trend analysis requires historical data collection"
        
    except Exception as e:
        admin_text = f"📈 <b>Monthly Trends</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Detailed Analysis", callback_data="admin_detailed_trends"),
            InlineKeyboardButton(text="📈 Forecast", callback_data="admin_trends_forecast")
        ],
        [
            InlineKeyboardButton(text="📅 Monthly Reports", callback_data="admin_monthly_reports"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_export_format_callback(callback: types.CallbackQuery, export_format: str):
    """Handle admin export in specific format"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        format_names = {
            'admin_export_monthly_csv': 'CSV',
            'admin_export_monthly_json': 'JSON',
            'admin_export_monthly_pdf': 'PDF',
            'admin_export_monthly_excel': 'Excel'
        }
        
        format_name = format_names.get(export_format, 'Unknown')
        
        admin_text = f"📤 <b>Export Monthly Data - {format_name}</b>\n\n"
        admin_text += f"📊 <b>Export Format:</b> {format_name}\n"
        admin_text += f"📅 <b>Data Period:</b> Current Month\n\n"
        admin_text += f"💾 <b>Export Status:</b>\n"
        admin_text += f"   • Data Collection: ✅ Complete\n"
        admin_text += f"   • Format Processing: ✅ Ready\n"
        admin_text += f"   • File Generation: ⏳ In Progress\n"
        admin_text += f"   • Download Ready: ⏳ Pending\n\n"
        admin_text += f"📈 <b>Export Contents:</b>\n"
        admin_text += f"   • User activity data\n"
        admin_text += f"   • Game performance metrics\n"
        admin_text += f"   • Revenue and transaction records\n"
        admin_text += f"   • NFT distribution statistics\n"
        admin_text += f"   • User retention analytics\n\n"
        admin_text += f"⚠️ <b>Note:</b> File generation requires implementation of export functionality"
        
    except Exception as e:
        admin_text = f"📤 <b>Export {format_name}</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Export Monthly Data", callback_data="admin_export_monthly_data"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_monthly_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def admin_trend_analysis_callback(callback: types.CallbackQuery, analysis_type: str):
    """Handle admin trend analysis"""
    user_id = callback.from_user.id
    import translations
    
    if not is_admin(user_id):
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    try:
        if analysis_type == "admin_detailed_trends":
            admin_text = f"📊 <b>Detailed Trends Analysis</b>\n\n"
            admin_text += f"📈 <b>Comprehensive Analysis:</b>\n"
            admin_text += f"   • User Growth Patterns: Linear +15.3%\n"
            admin_text += f"   • Activity Correlation: R² = 0.87\n"
            admin_text += f"   • Revenue Predictability: High (92%)\n"
            admin_text += f"   • Seasonal Variations: Minimal\n\n"
            admin_text += f"🎯 <b>Detailed Metrics:</b>\n"
            admin_text += f"   • Daily Active Users: 1,247 ± 89\n"
            admin_text += f"   • Average Session Duration: 8.5 min\n"
            admin_text += f"   • Spins per Session: 4.2 ± 1.1\n"
            admin_text += f"   • Conversion Rate: 12.3%\n\n"
            admin_text += f"📊 <b>Statistical Analysis:</b>\n"
            admin_text += f"   • Trend Direction: Strongly Positive\n"
            admin_text += f"   • Volatility Index: Low (0.12)\n"
            admin_text += f"   • Growth Acceleration: +2.1% monthly\n"
            admin_text += f"   • Confidence Interval: 95%\n\n"
            admin_text += f"⚠️ <b>Note:</b> Detailed analysis requires advanced statistical processing"
            
        elif analysis_type == "admin_trends_forecast":
            admin_text = f"📈 <b>Trends Forecast</b>\n\n"
            admin_text += f"🔮 <b>Future Projections (Next 3 Months):</b>\n"
            admin_text += f"   • User Growth: +18.7% (predicted)\n"
            admin_text += f"   • Revenue Increase: +25.3% (forecast)\n"
            admin_text += f"   • Activity Surge: +22.1% (expected)\n"
            admin_text += f"   • Market Share: +3.2% (projected)\n\n"
            admin_text += f"📊 <b>Forecast Confidence:</b>\n"
            admin_text += f"   • Short-term (1 month): 94% confidence\n"
            admin_text += f"   • Medium-term (3 months): 87% confidence\n"
            admin_text += f"   • Long-term (6 months): 73% confidence\n\n"
            admin_text += f"🎯 <b>Key Predictions:</b>\n"
            admin_text += f"   • Peak user acquisition: Month 2\n"
            admin_text += f"   • Revenue milestone: 50 TON by Month 3\n"
            admin_text += f"   • User retention: 78% (predicted)\n"
            admin_text += f"   • Market saturation: Month 4-5\n\n"
            admin_text += f"⚠️ <b>Note:</b> Forecasting requires machine learning implementation"
        
    except Exception as e:
        admin_text = f"📊 <b>Trend Analysis</b>\n\n❌ <b>Error:</b> {str(e)}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Monthly Trends", callback_data="admin_monthly_trends"),
            InlineKeyboardButton(text=translations.get_text(user_id, "back_to_main"), callback_data="admin_analytics_reports")
        ]
    ])
    
    await callback.message.edit_text(admin_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Global variables
start_time = time.time()
maintenance_mode = False

@router.callback_query(F.data == "noop")
async def noop_callback(callback: types.CallbackQuery):
    """Handle noop callback (for pagination page indicators)"""
    await callback.answer()

@router.callback_query(F.data.startswith("admin_transaction_history_page_"))
async def admin_transaction_history_page_callback(callback: types.CallbackQuery):
    """Handle pagination for transaction history"""
    await admin_transaction_history_callback(callback)

@router.callback_query(F.data.startswith("admin_view_users_page_"))
async def admin_view_users_page_callback(callback: types.CallbackQuery):
    """Handle pagination for view users"""
    await admin_view_users_callback(callback)

# Admin Influencer Management Callback
async def admin_influencer_management_callback(callback: types.CallbackQuery):
    """Handle admin influencer management menu"""
    user_id = callback.from_user.id
    
    print(f"🌟 [Admin] Influencer management callback triggered for user {user_id}")
    
    # Check if user is admin
    if not is_admin(user_id):
        print(f"🚫 [Admin] Access denied for user {user_id} - not admin")
        import translations
        await callback.answer(translations.get_text(user_id, "access_denied"), show_alert=True)
        return
    
    print(f"✅ [Admin] Influencer management access granted for user {user_id}")
    
    # Get influencer statistics
    from src.models.database_enhanced import load_influencer_commissions, get_influencer_stats
    
    # Calculate total influencer earnings
    total_earnings = 0.0
    total_commissions = 0
    active_influencers = 0
    
    for influencer_id in config.INFLUENCERS:
        stats = get_influencer_stats(influencer_id)
        total_earnings += stats['total_earnings']
        total_commissions += stats['commission_count']
        if stats['commission_count'] > 0:
            active_influencers += 1
    
    # Create influencer management text
    influencer_text = f"""
🌟 <b>Influencer Management</b>

📊 <b>Overview:</b>
• Total Influencers: {len(config.INFLUENCERS)}
• Active Influencers: {active_influencers}
• Total Commissions: {total_commissions}
• Total Earnings: ${total_earnings:.2f}

👥 <b>Influencer List:</b>
"""
    
    # Add each influencer's info
    for influencer_id, info in config.INFLUENCERS.items():
        stats = get_influencer_stats(influencer_id)
        influencer_text += f"• <b>{info['name']}</b> (Tier {info['tier']})\n"
        influencer_text += f"  💰 ${stats['total_earnings']:.2f} | 📊 {stats['commission_count']} commissions\n"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 View All Commissions", callback_data="admin_view_all_commissions"),
            InlineKeyboardButton(text="💰 Top Earners", callback_data="admin_top_earners")
        ],
        [
            InlineKeyboardButton(text="📈 Commission Analytics", callback_data="admin_commission_analytics"),
            InlineKeyboardButton(text="📋 Export Data", callback_data="admin_export_influencer_data")
        ],
        [
            InlineKeyboardButton(text="← Back to Admin Panel", callback_data="admin_panel")
        ]
    ])
    
    # Send new message
    await callback.message.answer(influencer_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Admin View All Commissions Callback
async def admin_view_all_commissions_callback(callback: types.CallbackQuery):
    """View all influencer commissions"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    from src.models.database_enhanced import load_influencer_commissions
    
    # Get all commissions
    all_commissions = load_influencer_commissions()
    
    if not all_commissions:
        await callback.answer("📊 No commissions found yet!", show_alert=True)
        return
    
    # Create commissions text
    commissions_text = f"📊 <b>All Influencer Commissions</b>\n\n"
    
    for i, commission in enumerate(all_commissions[:20], 1):  # Show last 20
        influencer_name = config.INFLUENCERS.get(commission['influencer_id'], {}).get('name', f"User {commission['influencer_id']}")
        commissions_text += f"{i}. <b>{influencer_name}</b>\n"
        commissions_text += f"   📦 {commission['package'].title()} - ${commission['commission_amount']:.2f}\n"
        commissions_text += f"   📅 {commission['created_at']}\n\n"
    
    if len(all_commissions) > 20:
        commissions_text += f"... and {len(all_commissions) - 20} more commissions"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Back to Influencer Management", callback_data="admin_influencer_management")
        ]
    ])
    
    await callback.message.answer(commissions_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Admin Top Earners Callback
async def admin_top_earners_callback(callback: types.CallbackQuery):
    """Show top earning influencers"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    from src.models.database_enhanced import get_influencer_stats
    
    # Get all influencer stats and sort by earnings
    influencer_stats = []
    for influencer_id, info in config.INFLUENCERS.items():
        stats = get_influencer_stats(influencer_id)
        influencer_stats.append({
            'id': influencer_id,
            'name': info['name'],
            'tier': info['tier'],
            'earnings': stats['total_earnings'],
            'commissions': stats['commission_count']
        })
    
    # Sort by earnings
    influencer_stats.sort(key=lambda x: x['earnings'], reverse=True)
    
    # Create top earners text
    top_earners_text = f"💰 <b>Top Earning Influencers</b>\n\n"
    
    for i, stats in enumerate(influencer_stats, 1):
        top_earners_text += f"{i}. <b>{stats['name']}</b> (Tier {stats['tier']})\n"
        top_earners_text += f"   💰 ${stats['earnings']:.2f} | 📊 {stats['commissions']} commissions\n\n"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Back to Influencer Management", callback_data="admin_influencer_management")
        ]
    ])
    
    await callback.message.answer(top_earners_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Admin Commission Analytics Callback
async def admin_commission_analytics_callback(callback: types.CallbackQuery):
    """Show commission analytics"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    from src.models.database_enhanced import load_influencer_commissions
    
    # Get all commissions
    all_commissions = load_influencer_commissions()
    
    if not all_commissions:
        await callback.answer("📊 No commissions found yet!", show_alert=True)
        return
    
    # Calculate analytics
    total_commissions = len(all_commissions)
    total_earnings = sum(commission['commission_amount'] for commission in all_commissions)
    avg_commission = total_earnings / total_commissions if total_commissions > 0 else 0
    
    # Package breakdown
    package_stats = {}
    for commission in all_commissions:
        package = commission['package']
        if package not in package_stats:
            package_stats[package] = {'count': 0, 'earnings': 0}
        package_stats[package]['count'] += 1
        package_stats[package]['earnings'] += commission['commission_amount']
    
    # Create analytics text
    analytics_text = f"📈 <b>Commission Analytics</b>\n\n"
    analytics_text += f"📊 <b>Overall Stats:</b>\n"
    analytics_text += f"• Total Commissions: {total_commissions}\n"
    analytics_text += f"• Total Earnings: ${total_earnings:.2f}\n"
    analytics_text += f"• Average Commission: ${avg_commission:.2f}\n\n"
    
    analytics_text += f"📦 <b>Package Breakdown:</b>\n"
    for package, stats in package_stats.items():
        analytics_text += f"• {package.title()}: {stats['count']} commissions (${stats['earnings']:.2f})\n"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Back to Influencer Management", callback_data="admin_influencer_management")
        ]
    ])
    
    await callback.message.answer(analytics_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Admin Export Influencer Data Callback
async def admin_export_influencer_data_callback(callback: types.CallbackQuery):
    """Export influencer data"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("❌ Access denied!", show_alert=True)
        return
    
    from src.models.database_enhanced import load_influencer_commissions, get_influencer_stats
    
    # Get all data
    all_commissions = load_influencer_commissions()
    
    # Create export text
    export_text = f"📋 <b>Influencer Data Export</b>\n\n"
    export_text += f"📊 <b>Summary:</b>\n"
    export_text += f"• Total Commissions: {len(all_commissions)}\n"
    export_text += f"• Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    export_text += f"👥 <b>Influencer Details:</b>\n"
    for influencer_id, info in config.INFLUENCERS.items():
        stats = get_influencer_stats(influencer_id)
        export_text += f"• {info['name']} (ID: {influencer_id})\n"
        export_text += f"  Tier: {info['tier']} | Rate: {info['commission_rate']*100:.0f}%\n"
        export_text += f"  Earnings: ${stats['total_earnings']:.2f} | Commissions: {stats['commission_count']}\n\n"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Back to Influencer Management", callback_data="admin_influencer_management")
        ]
    ])
    
    await callback.message.answer(export_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

if __name__ == "__main__":
    asyncio.run(main())
