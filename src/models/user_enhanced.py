"""
Enhanced user data models with caching and performance optimizations
Maintains 100% compatibility with existing functionality
"""

import sqlite3
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Import the enhanced database pool
from .database_enhanced import get_db_pool
from ..utils.cache import cache_manager
from ..utils.performance import track_performance, track_sync_operation

@track_performance("database")
def save_processed_transaction(tx_hash: str, user_id: int, package: str, amount: int, payment_id: str, source_wallet: str) -> None:
    """Save processed transaction to database with caching"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processed_transactions 
            (tx_hash, user_id, package, amount_nano, processed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (tx_hash, user_id, package, amount, datetime.now().isoformat()))
        
        conn.commit()
    
    # Invalidate related caches
    cache_manager.invalidate_payment_status(user_id)
    print(f"�� Saved processed transaction {tx_hash[:20]}... to database")

@track_performance("database")
def save_pending_payment(user_id: int, payment_info: Dict[str, Any]) -> None:
    """Save pending payment to database with caching"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO pending_ton_payments 
            (user_id, package, payment_id, amount_nano, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            payment_info["package"],
            payment_info["payment_id"],
            payment_info["expected_amount"],
            payment_info["timestamp"]
        ))
        
        conn.commit()
    
    # Cache payment status
    cache_manager.set_payment_status(user_id, payment_info)
    print(f"💾 Saved pending payment for user {user_id} to database")

@track_performance("database")
def remove_pending_payment(user_id: int) -> None:
    """Remove pending payment from database and cache"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM pending_ton_payments WHERE user_id = ?', (user_id,))
        conn.commit()
    
    # Invalidate payment cache
    cache_manager.invalidate_payment_status(user_id)
    print(f"🗑️ Removed pending payment for user {user_id} from database")

@track_performance("database")
def save_stars_transaction(transaction_id: str, user_id: int, package: str, amount: int) -> None:
    """Save Stars transaction to database with caching"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO stars_transactions 
            (transaction_id, user_id, package, amount_stars, processed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (transaction_id, user_id, package, amount, time.time()))
        
        conn.commit()
    
    # Invalidate user data cache
    cache_manager.invalidate_user_data(user_id)
    print(f"💾 Saved Stars transaction {transaction_id} to database")

@track_performance("database")
def save_user_data(user_id: int, user_info: Dict[str, Any]) -> None:
    """Save user data to database with intelligent caching"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        now = time.time()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, balance, package, level, spin_points, hits, total_spins, spins_available, referrals, referred_by, payment_method, nfts, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(user_info.get('nfts', [])),
            user_info.get('created_at', now),
            now
        ))
        
        conn.commit()
    
    # Cache user data with longer TTL for frequently accessed data
    cache_ttl = 300 if user_info.get('package') != 'None' else 60  # Longer cache for active users
    cache_manager.set_user_data(user_id, user_info, cache_ttl)
    print(f"💾 [Backend] Saved user {user_id} data to database")

@track_performance("database")
def load_user_data(user_id: int) -> Dict[str, Any]:
    """Load user data from database with caching"""
    # Try cache first
    cached_data = cache_manager.get_user_data(user_id)
    if cached_data is not None:
        return cached_data
    
    # Load from database
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, balance, package, level, spin_points, hits, total_spins, 
                   spins_available, referrals, referred_by, payment_method, nfts, 
                   created_at, updated_at
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            user_data = {
                'balance': row[1],
                'package': row[2],
                'level': row[3],
                'spin_points': row[4],
                'hits': row[5],
                'total_spins': row[6],
                'spins_available': row[7],
                'referrals': row[8],
                'referred_by': row[9],
                'payment_method': row[10],
                'nfts': json.loads(row[11]) if row[11] else [],
                'created_at': row[12],
                'updated_at': row[13]
            }
            
            # Cache the loaded data
            cache_ttl = 300 if user_data.get('package') != 'None' else 60
            cache_manager.set_user_data(user_id, user_data, cache_ttl)
            
            return user_data
        else:
            # Return default user data
            default_data = {
                'balance': 0.0,
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
                'created_at': time.time(),
                'updated_at': time.time()
            }
            
            # Cache default data
            cache_manager.set_user_data(user_id, default_data, 60)
            
            return default_data

@track_performance("database")
def get_user_stats() -> Dict[str, Any]:
    """Get user statistics with caching"""
    # Try cache first
    cached_stats = cache_manager.get_stats("user_stats")
    if cached_stats is not None:
        return cached_stats
    
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        # Get total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Get users by package
        cursor.execute('SELECT package, COUNT(*) FROM users GROUP BY package')
        package_stats = dict(cursor.fetchall())
        
        # Get users by level
        cursor.execute('SELECT level, COUNT(*) FROM users GROUP BY level')
        level_stats = dict(cursor.fetchall())
        
        # Get active users (with packages)
        cursor.execute('SELECT COUNT(*) FROM users WHERE package != "None"')
        active_users = cursor.fetchone()[0]
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'package_distribution': package_stats,
            'level_distribution': level_stats,
            'timestamp': time.time()
        }
        
        # Cache stats for 5 minutes
        cache_manager.set_stats("user_stats", stats)
        
        return stats

@track_performance("database")
def cleanup_old_data(days_old: int = 30) -> Dict[str, int]:
    """Clean up old data to maintain performance"""
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        # Clean old processed transactions
        cursor.execute('DELETE FROM processed_transactions WHERE processed_at < ?', (cutoff_time,))
        old_transactions = cursor.rowcount
        
        # Clean old Stars transactions
        cursor.execute('DELETE FROM stars_transactions WHERE processed_at < ?', (cutoff_time,))
        old_stars = cursor.rowcount
        
        # Clean old pending payments (already handled by main cleanup, but just in case)
        cursor.execute('DELETE FROM pending_ton_payments WHERE created_at < ?', (cutoff_time,))
        old_pendings = cursor.rowcount
        
        conn.commit()
    
    # Clear caches after cleanup
    cache_manager.clear_all_caches()
    
    cleanup_stats = {
        'old_transactions': old_transactions,
        'old_stars': old_stars,
        'old_pendings': old_pendings
    }
    
    print(f"🧹 Cleaned up old data: {cleanup_stats}")
    return cleanup_stats
