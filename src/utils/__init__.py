"""
Utility functions for CG Spins Bot
"""

from .helpers import (
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

from .logger import setup_logger, get_logger
from .error_handler import (
    handle_errors, 
    safe_execute, 
    safe_async_execute, 
    ErrorRecovery, 
    log_function_call,
    BotError,
    TONAPIError,
    DatabaseError,
    PaymentError,
    UserDataError
)

from .monitoring import metrics, health_checker, alert_system, BotMetrics, HealthChecker, AlertSystem

__all__ = [
    'create_keyboard',
    'generate_referral_link',
    'parse_referral_start',
    'calculate_referral_reward',
    'process_referral_bonus',
    'get_referral_stats',
    'calculate_level',
    'get_level_progress',
    'add_spin_points',
    'calculate_spin_result',
    'create_spin_response',
    'send_nft_reward_message'
]
