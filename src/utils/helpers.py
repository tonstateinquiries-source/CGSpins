"""
Utility helper functions for CG Spins Bot
"""

import time
from typing import Dict, Any, List, Optional
import config


def create_keyboard(*buttons) -> Any:
    """Helper function to create inline keyboard with 2 buttons per row"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = []
    row = []
    for i, button in enumerate(buttons):
        row.append(InlineKeyboardButton(text=button[0], callback_data=button[1]))
        if len(row) == 2 or i == len(buttons) - 1:  # Add row when it has 2 buttons or it's the last button
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Generate unique referral link for user"""
    # Simple referral link using only user ID
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def parse_referral_start(start_param: str) -> tuple[bool, int, str]:
    """Parse referral start parameter and return (is_referral, referrer_id, hash)"""
    if not start_param or not start_param.startswith("ref_"):
        return False, 0, ""
    
    try:
        parts = start_param.split("_")
        if len(parts) == 2:
            referrer_id = int(parts[1])
            return True, referrer_id, ""
        return False, 0, ""
    except (ValueError, IndexError):
        return False, 0, ""


def calculate_referral_reward(package_name: str) -> int:
    """Calculate referral reward based on package purchased"""
    reward_map = {
        "Bronze": 5,    # 5 spin points for Bronze package
        "Silver": 10,   # 10 spin points for Silver package
        "Gold": 25,     # 25 spin points for Gold package
        "Black": 50     # 50 spin points for Black package
    }
    return reward_map.get(package_name, 5)


def process_referral_bonus(user_data: Dict[int, Dict[str, Any]], referrer_id: int, referred_user_id: int, package_name: str) -> None:
    """Process referral bonus for both users"""
    try:
        # Add reward to referrer
        if referrer_id in user_data:
            reward_points = calculate_referral_reward(package_name)
            user_data[referrer_id]["spin_points"] = user_data[referrer_id].get("spin_points", 0) + reward_points
            user_data[referrer_id]["referrals"] = user_data[referrer_id].get("referrals", 0) + 1
            
            # Log referral bonus
            print(f"🎁 [Backend] Referral bonus: User {referrer_id} earned {reward_points} points from {referred_user_id}'s {package_name} purchase")
        
        # Add bonus to referred user (small welcome bonus)
        if referred_user_id in user_data:
            user_data[referred_user_id]["spin_points"] = user_data[referred_user_id].get("spin_points", 0) + 2
            
            # Log welcome bonus
            print(f"🎁 [Backend] Welcome bonus: User {referred_user_id} earned 2 points from referral")
            
    except Exception as e:
        print(f"❌ [Backend] Error processing referral bonus: {e}")


def get_referral_stats(user_data: Dict[int, Dict[str, Any]], user_id: int, bot_username: str) -> Dict[str, Any]:
    """Get comprehensive referral statistics for user"""
    print(f"🔍 [Backend] Getting referral stats for user {user_id}")
    
    if user_id not in user_data:
        print(f"❌ [Backend] User {user_id} not in user_data")
        return {}
    
    user = user_data[user_id]
    referrals_count = user.get("referrals", 0)
    
    print(f"✅ [Backend] User {user_id} has {referrals_count} referrals")
    
    # Calculate total earnings from referrals (this will be updated when packages are bought)
    total_earnings = 0
    # Note: Total earnings are calculated when packages are purchased, not stored persistently
    
    stats = {
        "referrals_count": referrals_count,
        "total_earnings": total_earnings,
        "referral_link": generate_referral_link(bot_username, user_id)
    }
    
    print(f"✅ [Backend] Generated referral stats for user {user_id}: {stats}")
    return stats


def calculate_level(points: int) -> str:
    """Calculate user level based on spin points"""
    for level_name, level_info in config.LEVELS.items():
        if level_info["min_points"] <= points <= level_info["max_points"]:
            return level_name
    return "High-Roller"  # Default for very high points


def get_level_progress(points: int) -> tuple:
    """Get current level and progress to next level"""
    current_level = calculate_level(points)
    current_level_info = config.LEVELS[current_level]
    
    if current_level == "High-Roller":
        return current_level, 0, 0  # Max level reached
    
    # Find next level
    level_names = list(config.LEVELS.keys())
    current_index = level_names.index(current_level)
    if current_index + 1 < len(level_names):
        next_level = level_names[current_index + 1]
        next_level_info = config.LEVELS[next_level]
        progress = points - current_level_info["min_points"]
        total_needed = next_level_info["min_points"] - current_level_info["min_points"]
        return current_level, progress, total_needed
    
    return current_level, 0, 0


def add_spin_points(user_data: Dict[int, Dict[str, Any]], user_id: int, points: int, reason: str) -> bool:
    """Add spin points to user and update level"""
    if user_id in user_data:
        user = user_data[user_id]
        old_level = user.get("level", "Spinner")
        user["spin_points"] = user.get("spin_points", 0) + points
        user["level"] = calculate_level(user["spin_points"])
        
        print(f"🎯 User {user_id} earned {points} points for {reason}. Total: {user['spin_points']}, Level: {user['level']}")
        
        # Check if level increased
        if user["level"] != old_level:
            print(f"🎉 User {user_id} leveled up from {old_level} to {user['level']}!")
            return True  # Level increased
    return False  # No level change


def calculate_spin_result(dice_value: int, user: Dict[str, Any], user_data: Dict[int, Dict[str, Any]], user_id: int) -> tuple:
    """Calculate spin result and return (is_winning, win_message, hits, nft_earned)"""
    import translations
    
    is_winning = dice_value == 64
    
    if not is_winning:
        return False, translations.get_text(user_id, "spin_value_message", value=dice_value), 0, False
    
    # Award points for 777 hit
    level_increased = add_spin_points(user_data, user_id, config.HIT_POINTS, "777 hit")
    
    # Calculate hits based on package - FIXED: Each 777 gives 1 hit, different packages need different total hits
    package = user.get('package', 'None')
    
    if package != 'None':
        # Each 777 roll gives exactly 1 hit
        hits = 1
        user['hits'] = user.get('hits', 0) + hits
        
        # Check if user earned NFT based on package requirements
        required_hits = {
            "Bronze": 1,   # Need 1 hit total
            "Silver": 3,   # Need 3 hits total  
            "Gold": 10,    # Need 10 hits total
            "Black": 25    # Need 25 hits total
        }
        
        current_hits = user.get('hits', 0)
        needed_hits = required_hits[package]
        
        if current_hits >= needed_hits:
            # User earned NFT - main handler will reset spins
            win_message = translations.get_text(user_id, "jackpot_message", hits=hits, points=config.HIT_POINTS)
            return True, win_message, hits, True  # True = NFT earned
        else:
            # Show progress towards NFT
            win_message = translations.get_text(user_id, "jackpot_progress", hits=hits, points=config.HIT_POINTS, current=current_hits, needed=needed_hits)
            return True, win_message, hits, False
    else:
        # No package - just award points
        win_message = translations.get_text(user_id, "jackpot_message", hits=0, points=config.HIT_POINTS)
        return True, win_message, 0, False


def create_spin_response(is_winning: bool, win_message: str, user: Dict[str, Any], nft_earned: bool = False) -> str:
    """Create formatted response message for spin result"""
    import translations
    
    # Get user_id from user data
    user_id = user.get('user_id', 0)
    
    current_level, progress, total_needed = get_level_progress(user.get('spin_points', 0))
    level_emoji = config.LEVELS[current_level]["emoji"]
    
    if is_winning:
        response = f"""
{translations.get_text(user_id, "slot_machine_title")}

<b>{translations.get_text(user_id, "result_label")}</b> {translations.get_text(user_id, "result_winning")}

<b>{win_message}</b>

{translations.get_text(user_id, "level_label", emoji=level_emoji, level=current_level)}
{translations.get_text(user_id, "total_spins_made_label", spins=user.get('total_spins', 0))}
{translations.get_text(user_id, "total_hits_label", hits=user.get('hits', 0))}
{translations.get_text(user_id, "spins_available_with_count", spins=user.get('spins_available', 0))}
        """
        
        # Add level up message if applicable
        if total_needed > 0:
            response += f"\n{translations.get_text(user_id, 'progress_to_next_level', progress=progress, total=total_needed)}"
    else:
        response = f"""
{translations.get_text(user_id, "slot_machine_title")}

<b>{translations.get_text(user_id, "result_label")}</b> {translations.get_text(user_id, "result_not_777")}

<b>{win_message}</b>

{translations.get_text(user_id, "level_label", emoji=level_emoji, level=current_level)}
{translations.get_text(user_id, "total_spins_made_label", spins=user.get('total_spins', 0))}
{translations.get_text(user_id, "total_hits_label", hits=user.get('hits', 0))}
{translations.get_text(user_id, "spins_available_with_count", spins=user.get('spins_available', 0))}
        """
        
        if total_needed > 0:
            response += f"\n{translations.get_text(user_id, 'progress_to_next_level', progress=progress, total=total_needed)}"
    
    return response


def send_nft_reward_message(user_data: Dict[int, Dict[str, Any]], user_id: int, package: str) -> tuple[str, list[str]]:
    """Generate NFT reward message and update user data"""
    import random
    
    if package in config.NFT_DROPS:
        # Randomly select an NFT from the package
        nft_name = random.choice(config.NFT_DROPS[package])
        
        # Add NFT to user's collection
        if user_id in user_data:
            # Initialize nfts field if it doesn't exist
            if "nfts" not in user_data[user_id]:
                user_data[user_id]["nfts"] = []
            user_data[user_id]["nfts"].append(nft_name)
        
        # Create reward message with correct package emojis
        package_emoji = {"Bronze": "🥉", "Silver": "🥈", "Gold": "🥇", "Black": "💎"}
        emoji = package_emoji.get(package, "🎁")
        
        import translations
        reward_text = f"""{translations.get_text(user_id, "nft_earned_title")}

{translations.get_text(user_id, "package_reward", emoji=emoji, package=package)}

{translations.get_text(user_id, "you_won", nft_name=nft_name)}

{translations.get_text(user_id, "withdrawal_info")}"""
        
        return reward_text, user_data[user_id].get("nfts", [])
    
    return "", [] 