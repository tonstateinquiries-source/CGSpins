"""
Game mechanics service for CG Spins Bot
"""

import random
from typing import Dict, Any, Tuple, List
import config


def calculate_level(points: int) -> str:
    """Calculate user level based on spin points"""
    for level_name, level_info in config.LEVELS.items():
        if level_info["min_points"] <= points <= level_info["max_points"]:
            return level_name
    return "High-Roller"  # Default for very high points


def get_level_progress(points: int) -> Tuple[str, int, int]:
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


def calculate_spin_result(dice_value: int, user: Dict[str, Any], user_id: int, user_data: Dict[int, Dict[str, Any]] = None) -> Tuple[bool, str, int, bool]:
    """Calculate spin result and return (is_winning, win_message, hits, nft_earned)"""
    import translations
    
    is_winning = dice_value == 64
    
    if not is_winning:
        return False, translations.get_text(user_id, "spin_value_message", value=dice_value), 0, False
    
    # Award points for 777 hit
    if user_data:
        level_increased = add_spin_points(user_data, user_id, config.HIT_POINTS, "777 hit")
    else:
        # Fallback: just add points to user dict
        user["spin_points"] = user.get("spin_points", 0) + config.HIT_POINTS
    
    # Calculate hits based on package
    package = user.get('package', 'None')
    package_multipliers = {
        "Bronze": 1,
        "Silver": 3, 
        "Gold": 10,
        "Black": 25
    }
    
    if package != 'None':
        hits = package_multipliers.get(package, 1)
        user['hits'] = user.get('hits', 0) + hits
        
        # Check if user earned NFT
        required_hits = {
            "Bronze": 1,
            "Silver": 3,
            "Gold": 10,
            "Black": 25
        }
        
        if user.get('hits', 0) >= required_hits[package]:
            # User earned NFT - reset spins
            user['spins_available'] = 0
            user['total_spins'] = 0
            win_message = translations.get_text(user_id, "jackpot_message", hits=hits, points=config.HIT_POINTS)
            return True, win_message, hits, True  # True = NFT earned
        else:
            win_message = translations.get_text(user_id, "jackpot_message", hits=hits, points=config.HIT_POINTS)
            return True, win_message, hits, False
    else:
        # No package - just award points
        win_message = translations.get_text(user_id, "jackpot_message", hits=0, points=config.HIT_POINTS)
        return True, win_message, 0, False


def create_spin_response(is_winning: bool, win_message: str, user: Dict[str, Any], nft_earned: bool = False) -> str:
    """Create formatted response message for spin result"""
    import translations
    
    # Get user_id from user data (we need to pass it as parameter)
    user_id = user.get('user_id', 0)  # This will be set when calling the function
    
    current_level, progress, total_needed = get_level_progress(user.get('spin_points', 0))
    level_emoji = config.LEVELS[current_level]["emoji"]
    
    if is_winning:
        response = f"""
{translations.get_text(user_id, "slot_machine_title")}

<b>Result:</b> {translations.get_text(user_id, "result_winning")}

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

<b>Result:</b> {translations.get_text(user_id, "result_not_777")}

<b>{win_message}</b>

{translations.get_text(user_id, "level_label", emoji=level_emoji, level=current_level)}
{translations.get_text(user_id, "total_spins_made_label", spins=user.get('total_spins', 0))}
{translations.get_text(user_id, "total_hits_label", hits=user.get('hits', 0))}
{translations.get_text(user_id, "spins_available_with_count", spins=user.get('spins_available', 0))}
        """
        
        if total_needed > 0:
            response += f"\n{translations.get_text(user_id, 'progress_to_next_level', progress=progress, total=total_needed)}"
    
    return response


def send_nft_reward_message(user_data: Dict[int, Dict[str, Any]], user_id: int, package: str) -> Tuple[str, List[str]]:
    """Generate NFT reward message and update user data"""
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
    """Process referral bonus for both users and influencer commissions"""
    try:
        print(f"🎁 [Referral Bonus] Processing bonus for referrer {referrer_id} from {referred_user_id}'s {package_name} purchase")
        
        # Add reward to referrer (only if they exist in user_data)
        if referrer_id in user_data:
            reward_points = calculate_referral_reward(package_name)
            user_data[referrer_id]["spin_points"] = user_data[referrer_id].get("spin_points", 0) + reward_points
            
            # Log referral bonus
            print(f"🎁 [Backend] Referral bonus: User {referrer_id} earned {reward_points} points from {referred_user_id}'s {package_name} purchase")
            
            # Save referrer's updated data
            from src.models.user import save_user_data
            save_user_data(referrer_id, user_data[referrer_id])
        else:
            print(f"⚠️ [Referral Bonus] Referrer {referrer_id} not found in user_data")
        
        # Add bonus to referred user (small welcome bonus)
        if referred_user_id in user_data:
            user_data[referred_user_id]["spin_points"] = user_data[referred_user_id].get("spin_points", 0) + 2
            
            # Log welcome bonus
            print(f"🎁 [Backend] Welcome bonus: User {referred_user_id} earned 2 points from referral")
        else:
            print(f"⚠️ [Referral Bonus] Referred user {referred_user_id} not found in user_data")
        
        # Process influencer commission if referrer is an influencer
        import config
        if referrer_id in config.INFLUENCERS:
            print(f"🌟 [Referral Bonus] Processing influencer commission for {referrer_id}")
            process_influencer_commission(referrer_id, referred_user_id, package_name)
        else:
            print(f"ℹ️ [Referral Bonus] Referrer {referrer_id} is not an influencer")
            
    except Exception as e:
        print(f"❌ [Backend] Error processing referral bonus: {e}")
        import traceback
        traceback.print_exc()


def process_influencer_commission(influencer_id: int, referred_user_id: int, package_name: str, payment_type: str = "ton", transaction_id: str = None) -> None:
    """Process influencer commission for package purchase"""
    try:
        import config
        from src.models.database_enhanced import save_influencer_commission, update_influencer_earnings
        
        # Get influencer info
        influencer_info = config.INFLUENCERS[influencer_id]
        commission_rate = influencer_info['commission_rate']
        
        # Get package price (use TON price for commission calculation)
        # Handle both package names (e.g., "Bronze") and package keys (e.g., "bronze")
        package_key = package_name.lower()
        
        # If package_key not found, try to find by name
        if package_key not in config.PACKAGES:
            for key, pkg in config.PACKAGES.items():
                if pkg['name'].lower() == package_name.lower():
                    package_key = key
                    break
        
        if package_key in config.PACKAGES:
            # Use TON price converted to USD for commission calculation (consistent regardless of payment method)
            package_price_ton = config.PACKAGES[package_key]['price_ton']
            package_price_usd = package_price_ton * config.TON_TO_USD_RATE
            commission_amount = package_price_usd * commission_rate
            
            # Save commission to database
            save_influencer_commission(
                influencer_id=influencer_id,
                referred_user_id=referred_user_id,
                package=package_key,
                commission_amount=commission_amount,
                commission_rate=commission_rate,
                payment_type=payment_type,
                transaction_id=transaction_id
            )
            
            # Update influencer total earnings
            update_influencer_earnings(influencer_id, commission_amount)
            
            print(f"💰 [Influencer] Commission processed: {influencer_info['name']} earned ${commission_amount:.2f} ({commission_rate*100:.0f}%) from {referred_user_id}'s {package_name} purchase ({payment_type})")
            
    except Exception as e:
        print(f"❌ [Influencer] Error processing influencer commission: {e}")


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
        "referral_link": f"https://t.me/{bot_username}?start=ref_{user_id}"
    }
    
    print(f"✅ [Backend] Generated referral stats for user {user_id}: {stats}")
    return stats


def generate_referral_link(bot_username: str, user_id: int) -> str:
    """Generate unique referral link for user"""
    # Simple referral link using only user ID
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def parse_referral_start(start_param: str) -> Tuple[bool, int, str]:
    """Parse referral start parameter and return (is_referral, referrer_id, hash)"""
    if not start_param:
        return False, 0, ""
    
    # Handle regular referral links (ref_123456)
    if start_param.startswith("ref_"):
        try:
            parts = start_param.split("_")
            if len(parts) == 2:
                referrer_id = int(parts[1])
                return True, referrer_id, ""
            return False, 0, ""
        except (ValueError, IndexError):
            return False, 0, ""
    
    # Note: Influencers now use regular ref_ links, processed as regular referrals
    
    return False, 0, "" 