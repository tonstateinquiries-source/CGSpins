"""
Database models and initialization functions for CG Spins Bot
"""

import sqlite3
import time
from typing import Dict, Any, List, Tuple


def init_database() -> None:
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    # Create pending TON payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_ton_payments (
            user_id INTEGER PRIMARY KEY,
            package TEXT NOT NULL,
            payment_id TEXT NOT NULL,
            amount_nano INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create processed transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_transactions (
            tx_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            package TEXT NOT NULL,
            amount_nano INTEGER NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Stars transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stars_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            package TEXT NOT NULL,
            amount_stars INTEGER NOT NULL,
            telegram_payment_charge_id TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table for persistent storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            package TEXT DEFAULT 'None',
            level TEXT DEFAULT 'Spinner',
            spin_points INTEGER DEFAULT 0,
            hits INTEGER DEFAULT 0,
            total_spins INTEGER DEFAULT 0,
            spins_available INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT NULL,
            payment_method TEXT DEFAULT NULL,
            nfts TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ [Backend] Database initialized successfully")


def load_pending_payments() -> Dict[int, Dict[str, Any]]:
    """Load pending TON payments from database and fix legacy prefixed IDs"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM pending_ton_payments')
    rows = cursor.fetchall()
    
    pending_payments = {}
    legacy_fixes = 0
    
    for row in rows:
        user_id, package, expected_amount, timestamp, verified, processed_tx, source_wallet, attempts, payment_id = row
        
        # Fix legacy "cgspins_" prefixed IDs
        if payment_id and payment_id.startswith("cgspins_"):
            old_id = payment_id
            payment_id = payment_id[len("cgspins_"):]
            print(f"🛠️ [Backend] Fixed legacy prefixed ID for user {user_id}: '{old_id}' → '{payment_id}'")
            
            # Update database with corrected ID
            cursor.execute('UPDATE pending_ton_payments SET payment_id = ? WHERE user_id = ?', (payment_id, user_id))
            legacy_fixes += 1
        
        pending_payments[user_id] = {
            "package": package,
            "expected_amount": expected_amount,
            "timestamp": timestamp,
            "verified": bool(verified),
            "processed_tx": processed_tx,
            "source_wallet": source_wallet,
            "attempts": attempts,
            "payment_id": payment_id
        }
    
    # Commit all legacy ID fixes
    if legacy_fixes > 0:
        conn.commit()
        print(f"🛠️ [Backend] Fixed {legacy_fixes} legacy prefixed payment IDs in database")
    
    conn.close()
    
    if pending_payments:
        print(f"📥 [Backend] Loaded {len(pending_payments)} pending payments from database:")
        for user_id, payment_info in pending_payments.items():
            age = int(time.time() - payment_info.get("timestamp", 0))
            print(f"   - User {user_id}: {payment_info['package']} package, {age}s old, ID: {payment_info['payment_id']}")
    else:
        print(f"📥 [Backend] No pending payments found in database")
    
    return pending_payments


def load_processed_transactions() -> set:
    """Load processed transaction hashes from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    # Load TON transactions
    cursor.execute('SELECT tx_hash FROM processed_transactions')
    ton_txs = {row[0] for row in cursor.fetchall()}
    
    # Load Stars transactions
    cursor.execute('SELECT transaction_id FROM stars_transactions')
    stars_txs = {row[0] for row in cursor.fetchall()}
    
    # Combine both types of transactions
    processed_txs = ton_txs.union(stars_txs)
    
    conn.close()
    print(f"📥 [Backend] Loaded {len(ton_txs)} TON transactions and {len(stars_txs)} Stars transactions from database")
    return processed_txs


def load_ton_transactions() -> list:
    """Load TON transaction data from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tx_hash, user_id, package, amount_nano, processed_at
        FROM processed_transactions
        ORDER BY processed_at DESC
    ''')
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            'tx_hash': row[0],
            'user_id': row[1],
            'package': row[2],
            'amount': row[3] / 1e9,  # Convert from nanoTON to TON
            'processed_at': row[4]
        })
    conn.close()
    return transactions


def load_stars_transactions() -> list:
    """Load Stars transaction data from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT transaction_id, user_id, package, amount, timestamp
        FROM stars_transactions
        ORDER BY timestamp DESC
    ''')
    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            'id': row[0],
            'user_id': row[1],
            'package': row[2],
            'amount_stars': row[3],
            'processed_at': row[4]
        })
    conn.close()
    return transactions 