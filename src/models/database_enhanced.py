"""
Database models and initialization functions for CG Spins Bot
Enhanced with connection pooling and performance optimizations
"""

import sqlite3
import time
import threading
from typing import Dict, Any, List, Tuple
from contextlib import contextmanager
from queue import Queue, Empty
import atexit

# Connection pool for better performance
class DatabasePool:
    """Thread-safe database connection pool"""
    
    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = database_path
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._initialize_pool()
        
        # Register cleanup on exit
        atexit.register(self.close_all_connections)
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self.max_connections):
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            # Optimize for performance
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=MEMORY')
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = None
        try:
            # Try to get connection from pool
            try:
                conn = self.pool.get_nowait()
            except Empty:
                # Create new connection if pool is empty
                conn = sqlite3.connect(
                    self.database_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA synchronous=NORMAL')
                conn.execute('PRAGMA cache_size=10000')
                conn.execute('PRAGMA temp_store=MEMORY')
            
            yield conn
            
        finally:
            if conn:
                try:
                    # Return connection to pool
                    self.pool.put_nowait(conn)
                except:
                    # Pool is full, close the connection
                    conn.close()
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break

# Global connection pool instance
_db_pool = None

def get_db_pool() -> DatabasePool:
    """Get the global database pool instance"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool('cgspins.db')
    return _db_pool

def init_database() -> None:
    """Initialize SQLite database with required tables and optimizations"""
    with get_db_pool().get_connection() as conn:
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
                influencer_earnings REAL DEFAULT 0.0,
                influencer_tier INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create influencer commissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS influencer_commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id INTEGER NOT NULL,
                referred_user_id INTEGER NOT NULL,
                package TEXT NOT NULL,
                commission_amount REAL NOT NULL,
                commission_rate REAL NOT NULL,
                payment_type TEXT NOT NULL,
                transaction_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create performance indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_package ON users(package)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_level ON users(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_spin_points ON users(spin_points)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_influencer_tier ON users(influencer_tier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_payments_created_at ON pending_ton_payments(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processed_transactions_processed_at ON processed_transactions(processed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_influencer_commissions_influencer_id ON influencer_commissions(influencer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_influencer_commissions_created_at ON influencer_commissions(created_at)')
        
        conn.commit()
    
    print("✅ [Backend] Database initialized successfully with connection pooling and optimizations")


def load_pending_payments() -> Dict[int, Dict[str, Any]]:
    """Load pending TON payments from database and fix legacy prefixed IDs"""
    pending_payments = {}
    
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, package, payment_id, amount_nano, created_at FROM pending_ton_payments')
        rows = cursor.fetchall()
        
        for row in rows:
            user_id, package, payment_id, amount_nano, created_at = row
            
            # Fix legacy payment IDs that have "cgspins_" prefix
            if payment_id.startswith("cgspins_"):
                clean_payment_id = payment_id.replace("cgspins_", "")
                print(f"🔧 [Backend] Fixed legacy payment ID for user {user_id}: {payment_id} -> {clean_payment_id}")
                
                # Update in database
                cursor.execute('UPDATE pending_ton_payments SET payment_id = ? WHERE user_id = ?', (clean_payment_id, user_id))
                payment_id = clean_payment_id
            
            pending_payments[user_id] = {
                "package": package,
                "payment_id": payment_id,
                "expected_amount": amount_nano,
                "timestamp": created_at if isinstance(created_at, (int, float)) else time.time()
            }
        
        conn.commit()
    
    print(f"📥 [Backend] Loaded {len(pending_payments)} pending TON payments from database")
    return pending_payments


def load_processed_transactions() -> set:
    """Load processed transaction hashes from database"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        # Load TON transactions
        cursor.execute('SELECT tx_hash FROM processed_transactions')
        ton_txs = {row[0] for row in cursor.fetchall()}
        
        # Load Stars transactions
        cursor.execute('SELECT transaction_id FROM stars_transactions')
        stars_txs = {row[0] for row in cursor.fetchall()}
        
        # Combine both types of transactions
        processed_txs = ton_txs.union(stars_txs)
    
    print(f"📥 [Backend] Loaded {len(ton_txs)} TON transactions and {len(stars_txs)} Stars transactions from database")
    return processed_txs


def load_ton_transactions() -> list:
    """Load TON transaction data from database"""
    with get_db_pool().get_connection() as conn:
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
        return transactions


def load_stars_transactions() -> list:
    """Load Stars transaction data from database"""
    with get_db_pool().get_connection() as conn:
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
        return transactions


def load_influencer_commissions(influencer_id: int = None) -> list:
    """Load influencer commission data from database"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        if influencer_id:
            cursor.execute('''
                SELECT id, influencer_id, referred_user_id, package, commission_amount, 
                       commission_rate, payment_type, transaction_id, created_at
                FROM influencer_commissions
                WHERE influencer_id = ?
                ORDER BY created_at DESC
            ''', (influencer_id,))
        else:
            cursor.execute('''
                SELECT id, influencer_id, referred_user_id, package, commission_amount, 
                       commission_rate, payment_type, transaction_id, created_at
                FROM influencer_commissions
                ORDER BY created_at DESC
            ''')
        
        commissions = []
        for row in cursor.fetchall():
            commissions.append({
                'id': row[0],
                'influencer_id': row[1],
                'referred_user_id': row[2],
                'package': row[3],
                'commission_amount': row[4],
                'commission_rate': row[5],
                'payment_type': row[6],
                'transaction_id': row[7],
                'created_at': row[8]
            })
        return commissions


def save_influencer_commission(influencer_id: int, referred_user_id: int, package: str, 
                              commission_amount: float, commission_rate: float, 
                              payment_type: str, transaction_id: str = None) -> None:
    """Save influencer commission to database"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO influencer_commissions 
            (influencer_id, referred_user_id, package, commission_amount, commission_rate, payment_type, transaction_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (influencer_id, referred_user_id, package, commission_amount, commission_rate, payment_type, transaction_id))
        conn.commit()
        print(f"💰 [Influencer] Commission saved: {influencer_id} earned {commission_amount} from {referred_user_id} ({package})")


def update_influencer_earnings(user_id: int, additional_earnings: float) -> None:
    """Update influencer total earnings in database"""
    try:
        with get_db_pool().get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current earnings first
            cursor.execute('SELECT influencer_earnings FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            current_earnings = result[0] if result else 0.0
            
            # Update earnings
            cursor.execute('''
                UPDATE users 
                SET influencer_earnings = influencer_earnings + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (additional_earnings, user_id))
            
            # Check if update was successful
            rows_affected = cursor.rowcount
            conn.commit()
            
            # Get new earnings
            cursor.execute('SELECT influencer_earnings FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            new_earnings = result[0] if result else 0.0
            
            print(f"💰 [Influencer] Updated earnings for user {user_id}: {current_earnings} + {additional_earnings} = {new_earnings} (rows affected: {rows_affected})")
            
    except Exception as e:
        print(f"❌ [Influencer] Error updating earnings for user {user_id}: {e}")
        import traceback
        traceback.print_exc()


def get_influencer_stats(influencer_id: int) -> dict:
    """Get comprehensive influencer statistics"""
    with get_db_pool().get_connection() as conn:
        cursor = conn.cursor()
        
        # Get total earnings
        cursor.execute('SELECT influencer_earnings FROM users WHERE user_id = ?', (influencer_id,))
        result = cursor.fetchone()
        total_earnings = result[0] if result else 0.0
        
        # Get commission count and total
        cursor.execute('''
            SELECT COUNT(*), SUM(commission_amount) 
            FROM influencer_commissions 
            WHERE influencer_id = ?
        ''', (influencer_id,))
        result = cursor.fetchone()
        commission_count = result[0] if result[0] else 0
        total_commissions = result[1] if result[1] else 0.0
        
        # Get recent commissions (last 10)
        recent_commissions = load_influencer_commissions(influencer_id)[:10]
        
        return {
            'total_earnings': total_earnings,
            'commission_count': commission_count,
            'total_commissions': total_commissions,
            'recent_commissions': recent_commissions
        }
