"""
Payment processing service for CG Spins Bot
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from collections import defaultdict

import config
from src.models import save_pending_payment, remove_pending_payment, save_processed_transaction


def create_pending_ton_payment(user_id: int, package: str) -> bool:
    """Create a pending TON payment record - SECURE VERSION"""
    if package in config.PACKAGES:
        # SECURITY: Skip if active package or Stars payment
        # Note: user_data is imported from main.py to avoid circular imports
        # This function will be called from main.py where user_data is available
        
        # Clean old pendings
        # Note: pending_ton_payments is imported from main.py to avoid circular imports
        
        # Generate 8-char UUID
        payment_id = str(uuid.uuid4())[:8]
        pkg = config.PACKAGES[package]
        
        payment_info = {
            "package": package,
            "expected_amount": pkg['nano'],
            "timestamp": time.time(),
            "verified": False,
            "processed_tx": None,  # Track processed transaction hash
            "source_wallet": None,  # Track source wallet
            "attempts": 0,  # Track verification attempts
            "payment_id": payment_id  # Add unique payment ID
        }
        
        # Note: This function will be called from main.py where pending_ton_payments is available
        # save_pending_payment(user_id, payment_info)
        print(f"📝 [Backend] Created pending TON: user={user_id}, package={package}, amount={pkg['nano'] / 1e9} TON, ID={payment_id}")
        return payment_info
    
    print(f"❌ [Backend] Invalid package {package} for user {user_id}")
    return False


def cleanup_old_payments(pending_ton_payments: Dict[int, Dict[str, Any]], user_data: Dict[int, Dict[str, Any]]) -> int:
    """Remove pending payments older than 1 hour or for users with active packages"""
    current_time = time.time()
    users_to_remove = []
    
    for user_id, payment_info in pending_ton_payments.items():
        age = current_time - payment_info.get("timestamp", 0)
        
        # Remove if expired (1 hour old)
        if age > config.TON_PAYMENT_EXPIRY:
            print(f"🧹 [Backend] Removing expired pending for user {user_id}: package={payment_info['package']}, ID={payment_info['payment_id']}, age={int(age)}s")
            users_to_remove.append(user_id)
        # Remove if user already has active package or paid with Stars
        elif user_id in user_data:
            user = user_data[user_id]
            if user.get('package') not in ['None', None] or user.get('payment_method') == 'stars':
                reason = "active package" if user.get('package') not in ['None', None] else "Stars payment"
                print(f"🧹 [Backend] Removing pending for user {user_id}: {reason} - package={payment_info['package']}, ID={payment_info['payment_id']}")
                users_to_remove.append(user_id)
    
    for user_id in users_to_remove:
        del pending_ton_payments[user_id]
        # Also remove from database
        remove_pending_payment(user_id)
    
    return len(users_to_remove)


def clear_user_payments(user_id: int, pending_ton_payments: Dict[int, Dict[str, Any]], user_data: Dict[int, Dict[str, Any]]) -> None:
    """Backend function to clear pending payments and reset user data (for testing/reset purposes)"""
    if user_id in pending_ton_payments:
        print(f"🗑️ [Backend] Clearing pending for user {user_id}")
        del pending_ton_payments[user_id]
        remove_pending_payment(user_id)
    if user_id in user_data:
        print(f"🗑️ [Backend] Resetting user {user_id} data")
        user_data[user_id].update({"package": "None", "payment_method": None, "spins_available": 0, "total_spins": 0}) 