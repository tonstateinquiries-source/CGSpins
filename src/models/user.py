"""
User data models and functions for CG Spins Bot
"""

import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, List


def save_processed_transaction(tx_hash: str, user_id: int, package: str, amount: int, payment_id: str, source_wallet: str) -> None:
    """Save processed transaction to database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO processed_transactions 
        (tx_hash, user_id, package, amount_nano, processed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (tx_hash, user_id, package, amount, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print(f"💾 Saved processed transaction {tx_hash[:20]}... to database")


def save_pending_payment(user_id: int, payment_info: Dict[str, Any]) -> None:
    """Save or update pending TON payment in database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO pending_ton_payments 
        (user_id, package, expected_amount, timestamp, verified, processed_tx, source_wallet, attempts, payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, 
        payment_info["package"], 
        payment_info["expected_amount"], 
        payment_info["timestamp"], 
        1 if payment_info["verified"] else 0,
        payment_info["processed_tx"], 
        payment_info["source_wallet"], 
        payment_info["attempts"], 
        payment_info["payment_id"]
    ))
    
    conn.commit()
    conn.close()
    print(f"💾 Saved pending payment for user {user_id} to database")


def remove_pending_payment(user_id: int) -> None:
    """Remove pending TON payment from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM pending_ton_payments WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    print(f"🗑️ Removed pending payment for user {user_id} from database")


def save_stars_transaction(transaction_id: str, user_id: int, package: str, amount: int) -> None:
    """Save Stars transaction to database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO stars_transactions 
        (transaction_id, user_id, package, amount, timestamp, payment_method)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (transaction_id, user_id, package, amount, time.time(), 'stars'))
    
    conn.commit()
    conn.close()
    print(f"💾 Saved Stars transaction {transaction_id} to database")


def save_user_data(user_id: int, user_info: Dict[str, Any]) -> None:
    """Save user data to database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    now = time.time()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, balance, package, level, spin_points, hits, total_spins, spins_available, referrals, referred_by, payment_method, nfts, language, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        user_info.get('balance', 1000),
        user_info.get('package', 'None'),
        user_info.get('level', 'Spinner'),
        user_info.get('spin_points', 0),
        user_info.get('hits', 0),
        user_info.get('total_spins', 0),
        user_info.get('spins_available', 0),
        user_info.get('referrals', 0),
        user_info.get('referred_by'),
        user_info.get('payment_method'),
        str(user_info.get('nfts', [])),
        user_info.get('language', 'en'),
        user_info.get('created_at', now),
        now
    ))
    
    conn.commit()
    conn.close()
    print(f"💾 [Backend] Saved user {user_id} data to database")


def load_user_data(user_id: int) -> Dict[str, Any]:
    """Load user data from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Safely parse NFTs field (it's at the end now)
        nfts_data = []
        try:
            if len(row) > 12 and row[12] and row[12] != '[]':
                nfts_data = eval(row[12]) if isinstance(row[12], str) else []
        except:
            nfts_data = []
        
        return {
            'user_id': row[0],
            'balance': row[1],
            'package': row[2],
            'level': row[3],
            'spin_points': row[4],
            'hits': row[5],
            'total_spins': row[6],
            'spins_available': row[7],
            'referrals': row[8],
            'payment_method': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'referred_by': row[12] if len(row) > 12 else None,
            'nfts': nfts_data,
            'language': row[14] if len(row) > 14 else 'en'
        }
    
    # Return default user data if not found
    return {
        'user_id': user_id,
        'balance': 1000,
        'package': 'None',
        'level': 'Spinner',
        'spin_points': 0,
        'hits': 0,
        'total_spins': 0,
        'spins_available': 0,
        'referrals': 0,
        'referred_by': None,
        'payment_method': None,
        'nfts': [],
        'language': 'en',
        'created_at': time.time(),
        'updated_at': time.time()
    }


def get_user_data(user_id: int) -> Dict[str, Any]:
    """Get user data from database (alias for load_user_data)"""
    return load_user_data(user_id)


def get_all_users() -> Dict[int, Dict[str, Any]]:
    """Get all users from database"""
    conn = sqlite3.connect('cgspins.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id FROM users')
    user_ids = cursor.fetchall()
    conn.close()
    
    all_users = {}
    for (user_id,) in user_ids:
        all_users[user_id] = load_user_data(user_id)
    
    return all_users 