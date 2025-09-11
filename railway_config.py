"""
Railway-specific configuration for CG Spins Bot
This file handles database configuration for Railway deployment
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Database configuration for Railway
DATABASE_URL = os.getenv('DATABASE_URL')

def get_railway_db_connection():
    """Get database connection for Railway PostgreSQL"""
    try:
        if DATABASE_URL:
            # Parse DATABASE_URL for Railway
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        else:
            # Fallback to SQLite for local development
            import sqlite3
            return sqlite3.connect('cgspins.db')
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        # Fallback to SQLite
        import sqlite3
        return sqlite3.connect('cgspins.db')

def init_railway_database():
    """Initialize database tables for Railway PostgreSQL"""
    conn = get_railway_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                package TEXT DEFAULT 'None',
                spins_available INTEGER DEFAULT 0,
                total_spins INTEGER DEFAULT 0,
                total_hits INTEGER DEFAULT 0,
                spin_points INTEGER DEFAULT 0,
                level TEXT DEFAULT 'Spinner',
                referrals INTEGER DEFAULT 0,
                nfts TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create pending_ton_payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_ton_payments (
                user_id BIGINT,
                package TEXT,
                amount_nano BIGINT,
                payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, payment_id)
            )
        """)
        
        # Create processed_transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_transactions (
                transaction_hash TEXT PRIMARY KEY,
                user_id BIGINT,
                amount_nano BIGINT,
                package TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create stars_transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stars_transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id BIGINT,
                package TEXT,
                amount_stars INTEGER,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create influencers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS influencers (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                tier INTEGER,
                total_earnings REAL DEFAULT 0.0,
                total_referrals INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create influencer_referrals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS influencer_referrals (
                id SERIAL PRIMARY KEY,
                influencer_id BIGINT,
                referred_user_id BIGINT,
                package TEXT,
                commission_amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create influencer_commissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS influencer_commissions (
                id SERIAL PRIMARY KEY,
                influencer_id BIGINT,
                amount REAL,
                package TEXT,
                referred_user_id BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logging.info("✅ Railway database initialized successfully")
        
    except Exception as e:
        logging.error(f"❌ Error initializing Railway database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_railway_database()
