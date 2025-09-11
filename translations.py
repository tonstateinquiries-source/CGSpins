



"""
Translation system for CG Spins Bot
Supports English and Russian languages
"""

TRANSLATIONS = {
    "en": {
        # Main Menu
        "buy_spins": "💰 Buy Spins",
        "start_spinning": "🎰 Start Spinning", 
        "my_profile": "👤 My Profile",
        "referral_program": "🎯 Referral Program",
        "faq": "❓ FAQ",
        "support": "👨\u200d💻 Support",
        "language": "🌐 Language",
        "admin_panel": "⚙️ Admin Panel",
        "influencer_dashboard_button": "🌟 Influencer Dashboard",
        
    
        # Welcome Message
        "welcome_title": "⭐️ <b>Why CG Spins?</b>",
        "welcome_description": "Fair odds, instant action, and NFTs with real-world value – don't miss out!",
        "start_winning": "🎰 <b>Start Winning Now!</b>",
        "welcome_message": """👋 <b>Welcome to CG Spins!</b>

The only <b>Telegram bot</b> where every 🎰 spin can unlock exclusive NFT collectibles worth <b>$5 to $15K</b>. Join and win big – your first spin could change everything!

🕹️ <b>How It Works:</b>
<blockquote>➖ Send 🎰 to spin the slots.
➖ Land 777 for a hit. Collect hits in your chosen pack to claim NFTs.
➖ No apps – just spin directly in this chat!</blockquote>

⭐️ <b>Why CG Spins?</b>
Fair odds, instant action, and NFTs with real-world value – don't miss out!

🎰 <b>Start Winning Now!</b>""",
        
        # Referral messages
        "referral_welcome": "🎯 <b>Welcome! You were invited by {referrer_name}!</b>\n💎 <b>Bonus:</b> You'll get 2 extra spin points when you buy your first package!",
        
        # FAQ Section
        "faq_title": "❓ <b>FREQUENTLY ASKED QUESTIONS</b>",
        "how_to_play_title": "🎰 <b>HOW TO PLAY</b>",
        "packages_pricing_title": "🎁 <b>PACKAGES & PRICING</b>",
        "nft_system_title": "🏆 <b>NFT SYSTEM</b>",
        "points_levels_title": "⭐ <b>POINTS & LEVELS</b>",
        "referral_program_title": "🎯 <b>REFERRAL PROGRAM</b>",
        "game_rules_title": "💡 <b>GAME RULES</b>",
        "technical_title": "🔧 <b>TECHNICAL</b>",
        "ready_to_play_title": "🎉 <b>READY TO PLAY?</b>",
        
        # FAQ Questions and Answers
        "how_to_start": "How do I start playing?",
        "how_to_start_answer": "Simply send 🎰 to this chat to spin the slots! You need to purchase a package first to get spins.",
        "what_is_777": "What is a \"777 hit\"?",
        "what_is_777_answer": "A 777 hit occurs when the slot machine shows value 64 (the maximum). This is your winning combination!",
        "how_to_get_spins": "How do I get spins?",
        "how_to_get_spins_answer": "Buy a package using 💰 Buy Spins button. Choose from <b>Bronze</b>, <b>Silver</b>, <b>Gold</b>, or <b>Black</b> packages.",
        
        "what_packages_available": "What packages are available?",
        "what_packages_available_answer": "We have 4 packages:",
        "how_much_cost": "How much do packages cost?",
        "how_much_cost_answer": "Package prices:",
        "can_pay_both": "Can I pay with both Stars and TON?",
        "can_pay_both_answer": "Yes! You can pay with Telegram Stars (in-app) or TON cryptocurrency (Tonkeeper wallet).",
        
        "how_to_win_nfts": "How do I win NFTs?",
        "how_to_win_nfts_answer": "Collect the required number of 777 hits for your package:",
        "what_nfts_can_win": "What NFTs can I win?",
        "what_nfts_can_win_answer": "Each package has exclusive NFTs:",
        "when_get_nft": "When do I get my NFT?",
        "when_get_nft_answer": "NFTs are added to your profile within 15 minutes after winning.",
        "what_happens_after_win": "What happens after I win an NFT?",
        "what_happens_after_win_answer": "Your package resets immediately - you can't continue spinning. Buy a new package to play again!",
        
        "what_are_spin_points": "What are spin points?",
        "what_are_spin_points_answer": "Points are earned by hitting 777. Each 777 hit gives you 10 points, plus bonus points from packages.",
        "what_are_levels": "What are the levels?",
        "what_are_levels_answer": "Levels are determined by points:",
        "do_levels_give_benefits": "Do levels give me any benefits?",
        "do_levels_give_benefits_answer": "Your level determines the rarity of NFT models and backgrounds you receive! Each NFT has different models, backgrounds, and variations. Higher levels = rarer NFT appearances!",
        
        "how_referral_works": "How does the referral system work?",
        "how_referral_works_answer": "Share your referral link. When friends join and buy packages, you both get bonus points!",
        "what_earn_referrals": "What do I earn from referrals?",
        "what_earn_referrals_answer": "You earn points based on your friend's package:",
        "what_friend_gets": "What does my friend get?",
        "what_friend_gets_answer": "Your friend gets a welcome bonus of 2 points when they join through your link.",
        
        "multiple_packages": "Can I have multiple packages at once?",
        "multiple_packages_answer": "No, you can only have one active package at a time.",
        "run_out_spins": "What happens if I run out of spins?",
        "run_out_spins_answer": "You need to buy a new package to continue playing.",
        "can_get_refund": "Can I get a refund?",
        "can_get_refund_answer": "All purchases are final. Make sure you understand the game before buying.",
        "is_game_fair": "Is the game fair?",
        "is_game_fair_answer": "Yes! We use Telegram's built-in dice system (1-64 values) which is completely random and fair.",
        
        "how_contact_support": "How do I contact support?",
        "how_contact_support_answer": "Use the /start command to access the main menu and navigate to support options.",
        "technical_issues": "What if I have technical issues?",
        "technical_issues_answer": "Try restarting the bot with /start. If problems persist, contact our support team.",
        
        "ready_to_play_final": "Start your journey to NFT riches! Every spin could be your lucky one! 🍀",
        
        # Complete FAQ Message
        "faq_message": """❓ <b>FREQUENTLY ASKED QUESTIONS</b>

🎰 <b>HOW TO PLAY</b>

<b>How do I start playing?</b>
Simply send 🎰 to this chat to spin the slots! You need to purchase a package first to get spins.

<b>What is a "777 hit"?</b>
A 777 hit occurs when the slot machine shows value 64 (the maximum). This is your winning combination!

<b>How do I get spins?</b>
Buy a package using 💰 Buy Spins button. Choose from <b>Bronze</b>, <b>Silver</b>, <b>Gold</b>, or <b>Black</b> packages.

🎁 <b>PACKAGES & PRICING</b>

<b>What packages are available?</b>
We have 4 packages:
🥉 <b>Bronze:</b> 30 spins, 1 hit needed for NFT
🥈 <b>Silver:</b> 60 spins, 3 hits needed for NFT  
🥇 <b>Gold:</b> 300 spins, 10 hits needed for NFT
⚫ <b>Black:</b> 600 spins, 25 hits needed for NFT

<b>How much do packages cost?</b>
🥉 <b>Bronze:</b> 450 Stars or 2 TON
🥈 <b>Silver:</b> 900 Stars or 4 TON
🥇 <b>Gold:</b> 5000 Stars or 24 TON
⚫ <b>Black:</b> 10000 Stars or 49 TON

<b>Can I pay with both Stars and TON?</b>
Yes! You can pay with Telegram Stars (in-app) or TON cryptocurrency (Tonkeeper wallet).

🏆 <b>NFT SYSTEM</b>

<b>How do I win NFTs?</b>
Collect the required number of 777 hits for your package:
🥉 <b>Bronze:</b> 1 hit = NFT
🥈 <b>Silver:</b> 3 hits = NFT
🥇 <b>Gold:</b> 10 hits = NFT
⚫ <b>Black:</b> 25 hits = NFT

<b>What NFTs can I win?</b>
Each package has exclusive NFTs:
🥉 <b>Bronze:</b> 38 NFTs (Bow Tie, Bunny Muffin, etc.) - up to $25
🥈 <b>Silver:</b> 15 NFTs (Bonded Ring, Diamond Ring, etc.) - $50-$200
🥇 <b>Gold:</b> 3 NFTs (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K
⚫ <b>Black:</b> 2 NFTs (Heart Locket, Plush Pepe) - up to $15K

<b>When do I get my NFT?</b>
NFTs are added to your profile within 15 minutes after winning.

<b>What happens after I win an NFT?</b>
Your package resets immediately - you can't continue spinning. Buy a new package to play again!

⭐ <b>POINTS & LEVELS</b>

<b>What are spin points?</b>
Points are earned by hitting 777. Each 777 hit gives you 10 points, plus bonus points from packages.

<b>What are the levels?</b>
🎰 <b>Spinner:</b> 0-19 points
🎁 <b>Collector:</b> 20-49 points  
👑 <b>VIP:</b> 50-99 points
💎 <b>High-Roller:</b> 100+ points

<b>Do levels give me any benefits?</b>
Your level determines the rarity of NFT models and backgrounds you receive! Each NFT has different models, backgrounds, and variations. Higher levels = rarer NFT appearances!

🎯 <b>REFERRAL PROGRAM</b>

<b>How does the referral system work?</b>
Share your referral link. When friends join and buy packages, you both get bonus points!

<b>What do I earn from referrals?</b>
You earn points based on your friend's package:
🥉 <b>Bronze:</b> +5 points
🥈 <b>Silver:</b> +10 points
🥇 <b>Gold:</b> +25 points
⚫ <b>Black:</b> +50 points

<b>What does my friend get?</b>
Your friend gets a welcome bonus of 2 points when they join through your link.

💡 <b>GAME RULES</b>

<b>Can I have multiple packages at once?</b>
No, you can only have one active package at a time.

<b>What happens if I run out of spins?</b>
You need to buy a new package to continue playing.

<b>Can I get a refund?</b>
All purchases are final. Make sure you understand the game before buying.

<b>Is the game fair?</b>
Yes! We use Telegram's built-in dice system (1-64 values) which is completely random and fair.

🔧 <b>TECHNICAL</b>

<b>How do I contact support?</b>
Use the /start command to access the main menu and navigate to support options.

<b>What if I have technical issues?</b>
Try restarting the bot with /start. If problems persist, contact our support team.

🎉 <b>READY TO PLAY?</b>

Start your journey to NFT riches! Every spin could be your lucky one! 🍀""",
        
        # Package details
        "bronze_package": "🥉 <b>Bronze:</b> 30 spins, 1 hit needed",
        "silver_package": "🥈 <b>Silver:</b> 60 spins, 3 hits needed",
        "gold_package": "🥇 <b>Gold:</b> 300 spins, 10 hits needed",
        "black_package": "⚫ <b>Black:</b> 600 spins, 25 hits needed",
        
        "bronze_price": "🥉 <b>Bronze:</b> 1 Star or 0.01 TON",
        "silver_price": "🥈 <b>Silver:</b> 900 Stars or 4 TON",
        "gold_price": "🥇 <b>Gold:</b> 5000 Stars or 24 TON",
        "black_price": "⚫ <b>Black:</b> 10000 Stars or 49 TON",
        
        "bronze_nft_requirement": "🥉 <b>Bronze:</b> 1 hit = NFT",
        "silver_nft_requirement": "🥈 <b>Silver:</b> 3 hits = NFT",
        "gold_nft_requirement": "🥇 <b>Gold:</b> 10 hits = NFT",
        "black_nft_requirement": "⚫ <b>Black:</b> 25 hits = NFT",
        
        "bronze_nft_list": "🥉 <b>Bronze:</b> 38 NFTs (Bow Tie, Bunny Muffin, etc.) - up to $25",
        "silver_nft_list": "🥈 <b>Silver:</b> 15 NFTs (Bonded Ring, Diamond Ring, etc.) - $50-$200",
        "gold_nft_list": "🥇 <b>Gold:</b> 3 NFTs (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K",
        "black_nft_list": "⚫ <b>Black:</b> 2 NFTs (Heart Locket, Plush Pepe) - up to $15K",
        
        "bronze_referral": "🥉 <b>Bronze:</b> +5 points",
        "silver_referral": "🥈 <b>Silver:</b> +10 points",
        "gold_referral": "🥇 <b>Gold:</b> +25 points",
        "black_referral": "⚫ <b>Black:</b> +50 points",
        
        # Level descriptions
        "spinner_level": "🎰 <b>Spinner:</b> 0-19 points",
        "collector_level": "🎁 <b>Collector:</b> 20-49 points",
        "vip_level": "👑 <b>VIP:</b> 50-99 points",
        "high_roller_level": "💎 <b>High-Roller:</b> 100+ points",
        
        # Navigation
        "back_to_main": "← Back to Menu",
        "back_to_main_menu": "🏠 Back to Menu",
        "back": "← Back",
        "main_menu": "🏠 Main Menu",
        
        # Profile
        "your_profile": "👤 <b>Your Profile</b>",
        "spins_available": "Spins Available",
        "package": "Package",
        "level": "Level",
        "spin_points": "Spin Points",
        "total_spins_made": "Total Spins Made",
        "total_hits": "Total Hits",
        "referrals": "Referrals",
        "nfts": "NFTs",
        "your_nft_collection": "Your NFT Collection",
        "user_data_not_found": "❌ <b>User data not found!</b>\n\nPlease start the bot with /start first.",
        "packages_available": "Packages Available",
        "choose_package": "✅ <b>Choose one below</b>",
        "bronze_package_short": "🥉 Bronze Package",
        "silver_package_short": "🥈 Silver Package",
        "gold_package_short": "🥇 Gold Package",
        "black_package_short": "⚫ Black Package",
        
        # Error messages
        "user_data_not_found_error": "❌ User data not found!",
        "invalid_package_error": "❌ Invalid package selected!",
        "already_have_package_error": "❌ You already have an active {package} package!",
        "payment_failed_error": "❌ Failed to create payment. Please try again.",
        "payment_creation_failed_error": "❌ Payment creation failed. Please try again.",
        "request_processing_error": "⏳ Request already being processed",
        "menu_cooldown_error": "⏳ Please wait before requesting menu again",
        "error_loading_menu": "❌ Error loading menu, please try again",
        "error_loading_referral_data": "❌ Error loading referral data!",
        "referral_link_copied": "📋 Referral link copied!\n\n{referral_link}",
        "invoice_sent": "✅ Invoice sent! Check your messages.",
        "payment_error": "❌ Payment error! Please try again.",
        "payment_error_invalid_amount": "❌ Payment error: Invalid amount. Please try again or contact support.",
        "out_of_spins": "❌ <b>Out of Spins!</b>\n\nYou've used all your spins. Please purchase a package to get more spins!",
        "access_denied": "❌ <b>Access Denied</b>\n\nOnly admin can {action}.",
        "database_reset_success": "🗑️ <b>Database completely reset!</b>\n\nAll user data, pending payments, and transactions have been cleared.\n\nUse /start to initialize fresh data.",
        "database_reset_failed": "❌ <b>Database reset failed!</b>\n\nError: {error}",
        "user_data_reset_success": "✅ <b>User data reset!</b>\n\nPackage: None\nSpins: 0\nHits: 0\n\nYou can now buy a new package.",
        "user_data_not_found_reply": "❌ User data not found. Please use /start first.",
        "error_getting_status": "❌ <b>Error getting status:</b>\n\n{error}",
        
        # Spin interface
        "slot_machine_ready": "🎰 <b>SLOT MACHINE READY!</b>",
        "your_package": "Your Package",
        "spins_available_label": "Spins Available",
        "need_purchase_package": "❌ <b>You need to purchase a package first!</b>\n\nPlease buy a package to get spins and start playing.",
        "how_to_spin": "🎯 <b>How to Spin:</b>",
        "simply_send_emoji": "Simply send 🎰 to this chat to spin the slots!",
        "hit_rates_by_level": "🎰 <b>Hit Rates by Level:</b>",
        "bronze_hit_rate": "➖ <b>Bronze:</b> 1 hit of 777 needed",
        "silver_hit_rate": "➖ <b>Silver:</b> 3 hits of 777 needed",
        "gold_hit_rate": "➖ <b>Gold:</b> 10 hits of 777 needed",
        "black_hit_rate": "➖ <b>Black:</b> 25 hits of 777 needed",
        "ready_to_win": "🚀 Ready to win? Send 🎰 now!",
        
        # NFT Price translations
        "nft_price_up_to": "NFT Price: up to ${price}",
        "nft_price_range": "NFT Price: ${min}–${max}",
        
        # Package descriptions
        "bronze_description": "Perfect for beginners!",
        "silver_description": "Great value for regular players",
        "gold_description": "Premium package for serious players",
        "black_description": "Elite package for high rollers",
        "hit_combination_needed": "🎰 <b>{hits} hit of 777 combination needed</b>",
        "bronze_hit_required": "🎰 <b>1 hit of 777 combination needed</b>",
        "silver_hit_required": "🎰 <b>3 hits of 777 combination needed</b>",
        "gold_hit_required": "🎰 <b>10 hits of 777 combination needed</b>",
        "black_hit_required": "🎰 <b>25 hits of 777 combination needed</b>",
        "nft_drops": "🎁 NFT Drops:",
        "pricing": "Pricing:",
        "stars_telegram_payments": "⭐️ {stars} Stars (Telegram Payments)",
        "ton_tonkeeper": "💎 {ton} TON (Tonkeeper)",
        
        # Package buttons
        "pay_with_stars": "⭐️ Pay with Stars ({stars})",
        "pay_with_ton": "💎 Pay with TON ({ton})",
        "back_to_packages": "← Back to Packages",
        "back_to_main": "← Back to Main",
        
        # Referral program
        "your_referral_program": "🎯 <b>Your Referral Program</b>",
        "total_referrals": "👥 <b>Total Referrals:</b> {count}",
        "total_earnings": "🎁 <b>Total Earnings:</b> {earnings} Spin Points",
        "referral_rewards": "💰 <b>Referral Rewards:</b>",
        "bronze_package_reward": "🥉 Bronze Package: +5 points",
        "silver_package_reward": "🥈 Silver Package: +10 points",
        
        # Influencer menu
        "influencer_dashboard": "🌟 <b>Influencer Dashboard</b>",
        "influencer_welcome": "Welcome to your influencer dashboard! Track your earnings and manage your referral link.",
        "influencer_total_earnings": "💰 <b>Total Earnings:</b> ${earnings:.2f}",
        "influencer_total_commissions": "📊 <b>Total Commissions:</b> {count}",
        "influencer_copy_link": "📋 Copy Link",
        "influencer_view_commissions": "📊 View All Commissions",
        "influencer_back_to_dashboard": "← Back to Dashboard",
        "influencer_your_commissions": "📊 <b>Your Commissions</b>",
        "influencer_page": "📄 Page {current} of {total}",
        "influencer_no_commissions": "📊 No commissions found yet. Start sharing your link!",
        "influencer_link_copied": "📋 Link copied: {link}",
        "influencer_your_tier": "👤 <b>Your Tier:</b> {tier} ({rate}% commission)",
        "influencer_commission_rate": "💎 <b>Commission Rate:</b> {rate}%",
        "influencer_your_link": "🔗 <b>Your Influencer Link:</b>",
        "influencer_how_it_works": "📈 <b>How it works:</b>",
        "influencer_how_it_works_text": "• Share your influencer link with your audience\n• When they join and buy packages, you earn {rate}% commission\n• Commissions are calculated on the package price\n• You can track all your earnings here",
        "influencer_pro_tip": "💡 <b>Pro tip:</b> Share your link in your content, stories, and posts to maximize your earnings!",
        "influencer_recent_commissions": "📋 <b>Recent Commissions:</b>",
        "influencer_earnings_profile": "🌟 <b>Influencer Earnings:</b> ${earnings:.2f}",
        "influencer_commission_rate_profile": "💎 <b>Commission Rate:</b> {rate}%",
        "gold_package_reward": "🥇 Gold Package: +25 points",
        "black_package_reward": "🖤 Black Package: +50 points",
        "your_referral_link": "🔗 <b>Your Referral Link:</b>",
        "how_it_works": "📱 <b>How it works:</b>",
        "how_it_works_text": "Share your link with friends. When they join and buy packages, you both earn bonus points!",
        "copy_link": "📋 Copy Link",
        "share_stats": "📊 Share Stats",
        
        # Payment success messages
        "ton_payment_successful": "✅ <b>TON Payment Successful!</b>",
        "package_activated": "📦 <b>{package} Package Activated</b>",
        "amount_paid": "💎 Amount Paid: {amount} TON",
        "spins_added": "🔄 Spins Added: {spins} spins",
        "points_earned": "🎯 Points Earned: +{points} Spin Points",
        "current_level": "🏆 Current Level: {level}",
        "package_activated_message": "Your package has been activated and you now have {spins} spins to play!",
        "start_spinning_button": "🎰 Start Spinning",
        "view_packages_button": "📦 View Packages",
        "main_menu_button": "🏠 Main Menu",
        
        # Payment success messages
        "stars_payment_successful": "✅ Stars Payment Successful!",
        "ton_payment_successful": "✅ TON Payment Successful!",
        "package_activated_label": "Package Activated",
        "spins_added_label": "Spins Added:",
        "points_earned_label": "Points Earned:",
        "current_level_label": "Current Level:",
        "level_up": "LEVEL UP!",
        "you_are_now": "You are now a",
        
        # Slot machine messages
        "slot_machine_title": "🎰 <b>SLOT MACHINE</b> 🎰",
        "result_label": "Result:",
        "result_winning": "🎉 <b>WINNING 777!</b> 🎉",
        "result_not_777": "❌ Not 777",
        "level_label": "🏆 <b>Level:</b> {emoji} {level}",
        "total_spins_made_label": "🎰 <b>Total Spins Made:</b> {spins}",
        "total_hits_label": "💎 <b>Total Hits:</b> {hits}",
        "spins_available_label": "🔄 Spins Available",
        "spins_available_with_count": "🔄 <b>Spins Available:</b> {spins}",
        "progress_to_next_level": "🎯 <b>Progress:</b> {progress}/{total} points to next level",
        "spin_value_message": "🎰 Spin Value: {value}/64 - Try again!",
        "jackpot_message": "🎉 JACKPOT! 777! +{hits} hits (NFT earned) +{points} points",
        "jackpot_progress": "🎉 JACKPOT! 777! +{hits} hits +{points} points\n🎯 Progress: {current}/{needed} hits",
        
        # NFT reward messages
        "nft_earned_title": "🎉 <b>NFT EARNED!</b> 🎉",
        "package_reward": "{emoji} <b>{package} Package Reward</b>",
        "you_won": "🎁 <b>You won:</b> <code>{nft_name}</code>",
        "withdrawal_info": "⬇️ <b>Withdrawal:</b> NFT will be added to your profile in 15 minutes",
        
        # Error messages
        "user_data_not_found_error": "❌ <b>User data not found!</b>\n\nPlease start the bot with /start first.",
        "user_data_not_found_reply": "❌ User data not found. Please use /start first.",
        
        # Button text
        "back_to_menu": "🏠 Back to Menu",
        "my_profile": "👤 My Profile",
        "copy_link": "📋 Copy Link",
        "share_stats": "📊 Share Stats",
        "back": "← Back",
        "join_cg_spins": "🎮 Join CG Spins",
        
        # Language selection
        "select_language": "🌐 <b>Select Language</b>",
        "english": "🇺🇸 English",
        "russian": "🇷🇺 Русский",
        "language_changed": "✅ Language changed to {language}",
        # Package details (keeping English names)
        "bronze_package": "🥉 <b>Bronze:</b> 30 spins, 1 hit needed",
        "silver_package": "🥈 <b>Silver:</b> 60 spins, 3 hits needed",
        "gold_package": "🥇 <b>Gold:</b> 300 spins, 10 hits needed",
        "black_package": "⚫ <b>Black:</b> 600 spins, 25 hits needed",
        
        "bronze_price": "🥉 <b>Bronze:</b> 1 Star or 0.01 TON",
        "silver_price": "🥈 <b>Silver:</b> 900 Stars or 4 TON",
        "gold_price": "🥇 <b>Gold:</b> 5000 Stars or 24 TON",
        "black_price": "⚫ <b>Black:</b> 10000 Stars or 49 TON",
        
        "bronze_nft_requirement": "🥉 <b>Bronze:</b> 1 hit = NFT",
        "silver_nft_requirement": "🥈 <b>Silver:</b> 3 hits = NFT",
        "gold_nft_requirement": "🥇 <b>Gold:</b> 10 hits = NFT",
        "black_nft_requirement": "⚫ <b>Black:</b> 25 hits = NFT",
        
        "bronze_nft_list": "🥉 <b>Bronze:</b> 38 NFTs (Bow Tie, Bunny Muffin, etc.) - up to $25",
        "silver_nft_list": "🥈 <b>Silver:</b> 15 NFTs (Bonded Ring, Diamond Ring, etc.) - $50-$200",
        "gold_nft_list": "🥇 <b>Gold:</b> 3 NFTs (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K",
        "black_nft_list": "⚫ <b>Black:</b> 2 NFTs (Heart Locket, Plush Pepe) - up to $15K",
        
        "bronze_referral": "🥉 <b>Bronze:</b> +5 points",
        "silver_referral": "🥈 <b>Silver:</b> +10 points",
        "gold_referral": "🥇 <b>Gold:</b> +25 points",
        "black_referral": "⚫ <b>Black:</b> +50 points",
        
        # Level descriptions (keeping English names)
        "spinner_level": "🎰 <b>Spinner:</b> 0-19 points",
        "collector_level": "🎁 <b>Collector:</b> 20-49 points",
        "vip_level": "👑 <b>VIP:</b> 50-99 points",
        "high_roller_level": "💎 <b>High-Roller:</b> 100+ points",

    },
    
    "ru": {
        # Main Menu
        "buy_spins": "💰 Купить спины",
        "start_spinning": "🎰 Начать крутить",
        "my_profile": "👤 Мой профиль",
        "referral_program": "🎯 Реферальная программа",
        "faq": "❓ Часто задаваемые вопросы",
        "support": "👨\u200d💻 Поддержка",
        "language": "🌐 Язык",
        "admin_panel": "⚙️ Панель администратора",
        "influencer_dashboard_button": "🌟 Панель инфлюенсера",
        
        # Welcome Message
        "welcome_title": "⭐️ <b>Почему CG Spins?</b>",
        "welcome_description": "Честные шансы, мгновенные действия и NFT с реальной стоимостью – не упустите!",
        "start_winning": "🎰 <b>Начните выигрывать прямо сейчас!</b>",
        "welcome_message": """👋 <b>Добро пожаловать в CG Spins!</b>

Единственный <b>Telegram-бот</b>, где каждый 🎰 спин может дать возможность получить эксклюзивные NFT коллекции стоимостью от <b>$5 до $15K</b>. Присоединяйтесь и выигрывайте большие призы – ваш первый спин может изменить всё!

🕹️ <b>Как это работает:</b>
<blockquote>➖ Отправьте 🎰 для вращения слотов.
➖ Попадите на 777 для получения подарка. Соберите нужное количество попаданий в выбранном пакете, чтобы получить NFT.
➖ Никаких приложений – просто крутите прямо в этом чате!</blockquote>

⭐️ <b>Почему CG Spins?</b>
Честные шансы, мгновенные действия и NFT с реальной стоимостью – не упустите!

🎰 <b>Начните выигрывать прямо сейчас!</b>""",
        
        # Referral messages
        "referral_welcome": "🎯 <b>Добро пожаловать! Вас пригласил {referrer_name}!</b>\n💎 <b>Бонус:</b> Вы получите 2 дополнительных очка спинов при покупке первого пакета!",
        
        # FAQ Section
        "faq_title": "❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>",
        "how_to_play_title": "🎰 <b>КАК ИГРАТЬ</b>",
        "packages_pricing_title": "🎁 <b>ПАКЕТЫ И ЦЕНЫ</b>",
        "nft_system_title": "🏆 <b>СИСТЕМА NFT</b>",
        "points_levels_title": "⭐ <b>ОЧКИ И УРОВНИ</b>",
        "referral_program_title": "🎯 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>",
        "game_rules_title": "💡 <b>ПРАВИЛА ИГРЫ</b>",
        "technical_title": "🔧 <b>ТЕХНИЧЕСКАЯ ПОДДЕРЖКА</b>",
        "ready_to_play_title": "🎉 <b>ГОТОВЫ ИГРАТЬ?</b>",
        
        # FAQ Questions and Answers
        "how_to_start": "Как начать играть?",
        "how_to_start_answer": "Просто отправьте 🎰 в этот чат, чтобы крутить слоты! Сначала нужно купить пакет, чтобы получить спины.",
        "what_is_777": "Что такое \"попадание 777\"?",
        "what_is_777_answer": "Попадание 777 происходит, когда игровой автомат показывает значение 64 (максимальное). Это ваша выигрышная комбинация!",
        "how_to_get_spins": "Как получить спины?",
        "how_to_get_spins_answer": "Купите пакет, используя кнопку 💰 Купить спины. Выберите из пакетов <b>Bronze</b>, <b>Silver</b>, <b>Gold</b> или <b>Black</b>.",
        
        "what_packages_available": "Какие пакеты доступны?",
        "what_packages_available_answer": "У нас есть 4 пакета:",
        "how_much_cost": "Сколько стоят пакеты?",
        "how_much_cost_answer": "Цены на пакеты:",
        "can_pay_both": "Могу ли я платить и Stars, и TON?",
        "can_pay_both_answer": "Да! Вы можете платить Telegram Stars (в приложении) или криптовалютой TON (кошелек Tonkeeper).",
        
        "how_to_win_nfts": "Как выиграть NFT?",
        "how_to_win_nfts_answer": "Соберите необходимое количество попаданий 777 для вашего пакета:",
        "what_nfts_can_win": "Какие NFT можно выиграть?",
        "what_nfts_can_win_answer": "У каждого пакета есть эксклюзивные NFT:",
        "when_get_nft": "Когда я получу свой NFT?",
        "when_get_nft_answer": "NFT добавляются в ваш профиль в течение 15 минут после выигрыша.",
        "what_happens_after_win": "Что происходит после выигрыша NFT?",
        "what_happens_after_win_answer": "Ваш пакет сразу сбрасывается - вы не можете продолжать крутить. Купите новый пакет, чтобы играть снова!",
        
        "what_are_spin_points": "Что такое очки спинов?",
        "what_are_spin_points_answer": "Очки зарабатываются при попадании 777. Каждое попадание 777 дает вам 10 очков, плюс бонусные очки от пакетов.",
        "what_are_levels": "Какие есть уровни?",
        "what_are_levels_answer": "Уровни определяются количеством очков:",
        "do_levels_give_benefits": "Дают ли уровни какие-то преимущества?",
        "do_levels_give_benefits_answer": "Ваш уровень определяет редкость моделей и фонов NFT, которые вы получаете! У каждого NFT есть разные модели, фоны и вариации. Высокие уровни = более редкие NFT!",
        
        "how_referral_works": "Как работает реферальная система?",
        "how_referral_works_answer": "Поделитесь своей реферальной ссылкой. Когда друзья присоединяются и покупают пакеты, вы оба получите бонусные очки!",
        "what_earn_referrals": "Что я зарабатываю от рефералов?",
        "what_earn_referrals_answer": "Вы зарабатываете очки в зависимости от пакета вашего друга:",
        "what_friend_gets": "Что получает мой друг?",
        "what_friend_gets_answer": "Ваш друг получает приветственный бонус в 2 очка, когда присоединяется по вашей ссылке.",
        
        "multiple_packages": "Могу ли я иметь несколько пакетов одновременно?",
        "multiple_packages_answer": "Нет, у вас может быть только один активный пакет за раз.",
        "run_out_spins": "Что происходит, если у меня закончились спины?",
        "run_out_spins_answer": "Вам нужно купить новый пакет, чтобы продолжить играть.",
        "can_get_refund": "Могу ли я получить возврат?",
        "can_get_refund_answer": "Все покупки окончательны. Убедитесь, что понимаете игру, прежде чем покупать.",
        "is_game_fair": "Честная ли игра?",
        "is_game_fair_answer": "Да! Мы используем встроенную систему кубиков Telegram (значения 1-64), которая полностью случайна и честна.",
        
        "how_contact_support": "Как связаться с поддержкой?",
        "how_contact_support_answer": "Используйте команду /start для доступа к главному меню и перехода к опциям поддержки.",
        "technical_issues": "Что делать при технических проблемах?",
        "technical_issues_answer": "Попробуйте перезапустить бота командой /start. Если проблемы продолжаются, обратитесь в нашу службу поддержки.",
        
        "ready_to_play_final": "Начните свой путь к богатству NFT! Каждый спин может стать вашим счастливым моментом! 🍀",
        
        # Complete FAQ Message
        "faq_message": """❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>

🎰 <b>КАК ИГРАТЬ</b>

<b>Как начать играть?</b>
Просто отправьте 🎰 в этот чат, чтобы крутить слоты! Сначала нужно купить пакет, чтобы получить спины.

<b>Что такое "попадание 777"?</b>
Попадание 777 происходит, когда игровой автомат показывает значение 64 (максимальное). Это ваша выигрышная комбинация!

<b>Как получить спины?</b>
Купите пакет, используя кнопку 💰 Купить спины. Выберите из пакетов <b>Bronze</b>, <b>Silver</b>, <b>Gold</b> или <b>Black</b>.

🎁 <b>ПАКЕТЫ И ЦЕНЫ</b>

<b>Какие пакеты доступны?</b>
У нас есть 4 пакета:
🥉 <b>Bronze:</b> 30 спинов, нужно 1 попадание для NFT
🥈 <b>Silver:</b> 60 спинов, нужно 3 попадания для NFT  
🥇 <b>Gold:</b> 300 спинов, нужно 10 попаданий для NFT
⚫ <b>Black:</b> 600 спинов, нужно 25 попаданий для NFT

<b>Сколько стоят пакеты?</b>
🥉 <b>Bronze:</b> 450 Stars или 2 TON
🥈 <b>Silver:</b> 900 Stars или 4 TON
🥇 <b>Gold:</b> 5000 Stars или 24 TON
⚫ <b>Black:</b> 10000 Stars или 49 TON

<b>Могу ли я платить и Stars, и TON?</b>
Да! Вы можете платить Telegram Stars (в приложении) или криптовалютой TON (кошелек Tonkeeper).

🏆 <b>СИСТЕМА NFT</b>

<b>Как выиграть NFT?</b>
Соберите необходимое количество попаданий 777 для вашего пакета:
🥉 <b>Bronze:</b> 1 попадание = NFT
🥈 <b>Silver:</b> 3 попадания = NFT
🥇 <b>Gold:</b> 10 попаданий = NFT
⚫ <b>Black:</b> 25 попаданий = NFT

<b>Какие NFT можно выиграть?</b>
У каждого пакета есть эксклюзивные NFT:
🥉 <b>Bronze:</b> 38 NFT (Bow Tie, Bunny Muffin и др.) - до $25
🥈 <b>Silver:</b> 15 NFT (Bonded Ring, Diamond Ring и др.) - $50-$200
🥇 <b>Gold:</b> 3 NFT (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K
⚫ <b>Black:</b> 2 NFT (Heart Locket, Plush Pepe) - до $15K

<b>Когда я получу свой NFT?</b>
NFT добавляются в ваш профиль в течение 15 минут после выигрыша.

<b>Что происходит после выигрыша NFT?</b>
Ваш пакет сразу сбрасывается - вы не можете продолжать крутить. Купите новый пакет, чтобы играть снова!

⭐ <b>ОЧКИ И УРОВНИ</b>

<b>Что такое очки спинов?</b>
Очки зарабатываются при попадании 777. Каждое попадание 777 дает вам 10 очков, плюс бонусные очки от пакетов.

<b>Какие есть уровни?</b>
🎰 <b>Spinner:</b> 0-19 очков
🎁 <b>Collector:</b> 20-49 очков  
👑 <b>VIP:</b> 50-99 очков
💎 <b>High-Roller:</b> 100+ очков

<b>Дают ли уровни какие-то преимущества?</b>
Ваш уровень определяет редкость моделей и фонов NFT, которые вы получаете! У каждого NFT есть разные модели, фоны и вариации. Высокие уровни = более редкие NFT!

🎯 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>

<b>Как работает реферальная система?</b>
Поделитесь своей реферальной ссылкой. Когда друзья присоединяются и покупают пакеты, вы оба получите бонусные очки!

<b>Что я зарабатываю от рефералов?</b>
Вы зарабатываете очки в зависимости от пакета вашего друга:
🥉 <b>Bronze:</b> +5 очков
🥈 <b>Silver:</b> +10 очков
🥇 <b>Gold:</b> +25 очков
⚫ <b>Black:</b> +50 очков

<b>Что получает мой друг?</b>
Ваш друг получает приветственный бонус в 2 очка, когда присоединяется по вашей ссылке.

💡 <b>ПРАВИЛА ИГРЫ</b>

<b>Могу ли я иметь несколько пакетов одновременно?</b>
Нет, у вас может быть только один активный пакет за раз.

<b>Что происходит, если у меня закончились спины?</b>
Вам нужно купить новый пакет, чтобы продолжить играть.

<b>Могу ли я получить возврат?</b>
Все покупки окончательны. Убедитесь, что понимаете игру, прежде чем покупать.

<b>Честная ли игра?</b>
Да! Мы используем встроенную систему кубиков Telegram (значения 1-64), которая полностью случайна и честна.

🔧 <b>ТЕХНИЧЕСКАЯ ПОДДЕРЖКА</b>

<b>Как связаться с поддержкой?</b>
Используйте команду /start для доступа к главному меню и перехода к опциям поддержки.

<b>Что делать при технических проблемах?</b>
Попробуйте перезапустить бота командой /start. Если проблемы продолжаются, обратитесь в нашу службу поддержки.

🎉 <b>ГОТОВЫ ИГРАТЬ?</b>

Начните свой путь к богатству NFT! Каждый спин может стать вашим счастливым моментом! 🍀""",
        
        # Package details (keeping English names)
        "bronze_package": "🥉 <b>Bronze:</b> 30 спинов, нужно 1 попадание для NFT",
        "silver_package": "🥈 <b>Silver:</b> 60 спинов, нужно 3 попадания для NFT",
        "gold_package": "🥇 <b>Gold:</b> 300 спинов, нужно 10 попаданий для NFT",
        "black_package": "⚫ <b>Black:</b> 600 спинов, нужно 25 попаданий для NFT",
        
        "bronze_price": "🥉 <b>Bronze:</b> 1 Star или 0.01 TON",
        "silver_price": "🥈 <b>Silver:</b> 900 Stars или 4 TON",
        "gold_price": "🥇 <b>Gold:</b> 5000 Stars или 24 TON",
        "black_price": "⚫ <b>Black:</b> 10000 Stars или 49 TON",
        
        "bronze_nft_requirement": "🥉 <b>Bronze:</b> 1 попадание = NFT",
        "silver_nft_requirement": "🥈 <b>Silver:</b> 3 попадания = NFT",
        "gold_nft_requirement": "🥇 <b>Gold:</b> 10 попаданий = NFT",
        "black_nft_requirement": "⚫ <b>Black:</b> 25 попаданий = NFT",
        
        "bronze_nft_list": "🥉 <b>Bronze:</b> 38 NFT (Bow Tie, Bunny Muffin и др.) - до $25",
        "silver_nft_list": "🥈 <b>Silver:</b> 15 NFT (Bonded Ring, Diamond Ring и др.) - $50-$200",
        "gold_nft_list": "🥇 <b>Gold:</b> 3 NFT (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K",
        "black_nft_list": "⚫ <b>Black:</b> 2 NFT (Heart Locket, Plush Pepe) - до $15K",
        
        "bronze_referral": "🥉 <b>Bronze:</b> +5 очков",
        "silver_referral": "🥈 <b>Silver:</b> +10 очков",
        "gold_referral": "🥇 <b>Gold:</b> +25 очков",
        "black_referral": "⚫ <b>Black:</b> +50 очков",
        
        # Level descriptions (keeping English names)
        "spinner_level": "🎰 <b>Spinner:</b> 0-19 очков",
        "collector_level": "🎁 <b>Collector:</b> 20-49 очков",
        "vip_level": "👑 <b>VIP:</b> 50-99 очков",
        "high_roller_level": "💎 <b>High-Roller:</b> 100+ очков",
        
        # Navigation
        "back_to_main": "← Назад в меню",
        "back_to_main_menu": "🏠 Назад в меню",
        "back": "← Назад",
        "main_menu": "🏠 Главное меню",
        
        # Profile
        "your_profile": "👤 <b>Ваш профиль</b>",
        "spins_available": "Доступные спины",
        "package": "Пакет",
        "level": "Уровень",
        "spin_points": "Очки спинов",
        "total_spins_made": "Всего спинов сделано",
        "total_hits": "Всего попаданий",
        "referrals": "Рефералы",
        "nfts": "NFT",
        "your_nft_collection": "Ваша коллекция NFT",
        "user_data_not_found": "❌ <b>Данные пользователя не найдены!</b>\n\nПожалуйста, сначала запустите бота командой /start.",
        "packages_available": "Доступные пакеты",
        "choose_package": "✅ <b>Выберите один ниже</b>",
        "bronze_package_short": "🥉 Bronze Package",
        "silver_package_short": "🥈 Silver Package",
        "gold_package_short": "🥇 Gold Package",
        "black_package_short": "⚫ Black Package",
        
        # Error messages
        "user_data_not_found_error": "❌ Данные пользователя не найдены!",
        "invalid_package_error": "❌ Выбран неверный пакет!",
        "already_have_package_error": "❌ У вас уже есть активный пакет {package}!",
        "payment_failed_error": "❌ Не удалось создать платеж. Попробуйте еще раз.",
        "payment_creation_failed_error": "❌ Создание платежа не удалось. Попробуйте еще раз.",
        "request_processing_error": "⏳ Запрос уже обрабатывается",
        "menu_cooldown_error": "⏳ Пожалуйста, подождите перед повторным запросом меню",
        "error_loading_menu": "❌ Ошибка загрузки меню, попробуйте еще раз",
        "error_loading_referral_data": "❌ Ошибка загрузки данных рефералов!",
        "referral_link_copied": "📋 Реферальная ссылка скопирована!\n\n{referral_link}",
        "invoice_sent": "✅ Счет отправлен! Проверьте ваши сообщения.",
        "payment_error": "❌ Ошибка платежа! Попробуйте еще раз.",
        "payment_error_invalid_amount": "❌ Ошибка платежа: Неверная сумма. Попробуйте еще раз или обратитесь в поддержку.",
        "out_of_spins": "❌ <b>Спины закончились!</b>\n\nВы использовали все свои спины. Пожалуйста, купите пакет, чтобы получить больше спинов!",
        "access_denied": "❌ <b>Доступ запрещен</b>\n\nТолько администратор может {action}.",
        "database_reset_success": "🗑️ <b>База данных полностью сброшена!</b>\n\nВсе данные пользователей, ожидающие платежи и транзакции были очищены.\n\nИспользуйте /start для инициализации свежих данных.",
        "database_reset_failed": "❌ <b>Сброс базы данных не удался!</b>\n\nОшибка: {error}",
        "user_data_reset_success": "✅ <b>Данные пользователя сброшены!</b>\n\nПакет: None\nСпины: 0\nПопадания: 0\n\nТеперь вы можете купить новый пакет.",
        "user_data_not_found_reply": "❌ Данные пользователя не найдены. Пожалуйста, сначала используйте /start.",
        "error_getting_status": "❌ <b>Ошибка получения статуса:</b>\n\n{error}",
        
        # Spin interface
        "slot_machine_ready": "🎰 <b>ИГРОВОЙ АВТОМАТ ГОТОВ!</b>",
        "your_package": "Ваш пакет",
        "spins_available_label": "Доступные спины",
        "need_purchase_package": "❌ <b>Сначала нужно купить пакет!</b>\n\nПожалуйста, купите пакет, чтобы получить спины и начать играть.",
        "how_to_spin": "🎯 <b>Как крутить:</b>",
        "simply_send_emoji": "Просто отправьте 🎰 в этот чат, чтобы крутить слоты!",
        "hit_rates_by_level": "🎰 <b>Требования для попаданий по уровням:</b>",
        "bronze_hit_rate": "➖ <b>Bronze:</b> нужно 1 попадание 777",
        "silver_hit_rate": "➖ <b>Silver:</b> нужно 3 попадания 777",
        "gold_hit_rate": "➖ <b>Gold:</b> нужно 10 попаданий 777",
        "black_hit_rate": "➖ <b>Black:</b> нужно 25 попаданий 777",
        "ready_to_win": "🚀 Готовы выиграть? Отправьте 🎰 сейчас!",
        
        # NFT Price translations
        "nft_price_up_to": "Цена NFT: до ${price}",
        "nft_price_range": "Цена NFT: ${min}–${max}",
        
        # Package descriptions
        "bronze_description": "Идеально для начинающих!",
        "silver_description": "Отличное соотношение цены и качества для постоянных игроков",
        "gold_description": "Премиум пакет для крупных игроков",
        "black_description": "Элитный пакет для крупных игроков",
        "hit_combination_needed": "🎰 <b>Нужно {hits} попадание комбинации 777</b>",
        "bronze_hit_required": "🎰 <b>Нужно 1 попадание комбинации 777</b>",
        "silver_hit_required": "🎰 <b>Нужно 3 попадания комбинации 777</b>",
        "gold_hit_required": "🎰 <b>Нужно 10 попаданий комбинации 777</b>",
        "black_hit_required": "🎰 <b>Нужно 25 попаданий комбинации 777</b>",
        "nft_drops": "🎁 NFT дропы:",
        "pricing": "Цена:",
        "stars_telegram_payments": "⭐️ {stars} Stars (Telegram Payments)",
        "ton_tonkeeper": "💎 {ton} TON (Tonkeeper)",
        
        # Package buttons
        "pay_with_stars": "⭐️ Оплатить Stars ({stars})",
        "pay_with_ton": "💎 Оплатить TON ({ton})",
        "back_to_packages": "← Назад к пакетам",
        "back_to_main": "← Назад в меню",
        
        # Referral program
        "your_referral_program": "🎯 <b>Ваша реферальная программа</b>",
        "total_referrals": "👥 <b>Всего рефералов:</b> {count}",
        "total_earnings": "🎁 <b>Общий заработок:</b> {earnings} очков спинов",
        "referral_rewards": "💰 <b>Реферальные награды:</b>",
        "bronze_package_reward": "🥉 Bronze Package: +5 очков",
        "silver_package_reward": "🥈 Silver Package: +10 очков",
        
        # Influencer menu
        "influencer_dashboard": "🌟 <b>Панель инфлюенсера</b>",
        "influencer_welcome": "Добро пожаловать в панель инфлюенсера! Отслеживайте свой заработок и управляйте реферальной ссылкой.",
        "influencer_total_earnings": "💰 <b>Общий заработок:</b> ${earnings:.2f}",
        "influencer_total_commissions": "📊 <b>Всего комиссий:</b> {count}",
        "influencer_copy_link": "📋 Скопировать ссылку",
        "influencer_view_commissions": "📊 Все комиссии",
        "influencer_back_to_dashboard": "← Назад к панели",
        "influencer_your_commissions": "📊 <b>Ваши комиссии</b>",
        "influencer_page": "📄 Страница {current} из {total}",
        "influencer_no_commissions": "📊 Комиссии пока не найдены. Начните делиться своей ссылкой!",
        "influencer_link_copied": "📋 Ссылка скопирована: {link}",
        "influencer_your_tier": "👤 <b>Ваш уровень:</b> {tier} ({rate}% комиссия)",
        "influencer_commission_rate": "💎 <b>Ставка комиссии:</b> {rate}%",
        "influencer_your_link": "🔗 <b>Ваша ссылка инфлюенсера:</b>",
        "influencer_how_it_works": "📈 <b>Как это работает:</b>",
        "influencer_how_it_works_text": "• Поделитесь своей ссылкой с аудиторией\n• Когда они присоединятся и купят пакеты, вы получите {rate}% комиссию\n• Комиссии рассчитываются от стоимости пакета\n• Вы можете отслеживать весь свой заработок здесь",
        "influencer_pro_tip": "💡 <b>Профессиональный совет:</b> Делитесь ссылкой в контенте, историях и постах для максимизации заработка!",
        "influencer_recent_commissions": "📋 <b>Последние комиссии:</b>",
        "influencer_earnings_profile": "🌟 <b>Заработок инфлюенсера:</b> ${earnings:.2f}",
        "influencer_commission_rate_profile": "💎 <b>Ставка комиссии:</b> {rate}%",
        "gold_package_reward": "🥇 Gold Package: +25 очков",
        "black_package_reward": "🖤 Black Package: +50 очков",
        "your_referral_link": "🔗 <b>Ваша реферальная ссылка:</b>",
        "how_it_works": "📱 <b>Как это работает:</b>",
        "how_it_works_text": "Поделитесь своей ссылкой с друзьями. Когда они присоединятся и купят пакеты, вы оба получите бонусные очки!",
        "copy_link": "📋 Копировать ссылку",
        "share_stats": "📊 Поделиться статистикой",
        
        # Payment success messages
        "ton_payment_successful": "✅ <b>TON платеж успешен!</b>",
        "package_activated": "📦 <b>{package} пакет активирован</b>",
        "amount_paid": "💎 Сумма оплаты: {amount} TON",
        "spins_added": "🔄 Спинов добавлено: {spins} спинов",
        "points_earned": "🎯 Очков заработано: +{points} очков спинов",
        "current_level": "🏆 Текущий уровень: {level}",
        "package_activated_message": "Ваш пакет активирован, и теперь у вас есть {spins} спинов для игры!",
        "start_spinning_button": "🎰 Начать крутить",
        "view_packages_button": "📦 Посмотреть пакеты",
        "main_menu_button": "🏠 Главное меню",
        
        # Payment success messages
        "stars_payment_successful": "✅ Оплата Stars успешна!",
        "ton_payment_successful": "✅ <b>Оплата TON успешна!</b>",
        "package_activated_label": "Пакет активирован",
        "spins_added_label": "Спинов добавлено:",
        "points_earned_label": "Очков заработано:",
        "current_level_label": "Текущий уровень:",
        "level_up": "ПОВЫШЕНИЕ УРОВНЯ!",
        "you_are_now": "Теперь вы",
        
        # Slot machine messages
        "slot_machine_title": "🎰 <b>ИГРОВОЙ АВТОМАТ</b> 🎰",
        "result_label": "Результат:",
        "result_winning": "🎉 <b>ВЫИГРЫШ 777!</b> 🎉",
        "result_not_777": "❌ Не 777",
        "level_label": "🏆 <b>Уровень:</b> {emoji} {level}",
        "total_spins_made_label": "🎰 <b>Всего спинов сделано:</b> {spins}",
        "total_hits_label": "💎 <b>Всего попаданий:</b> {hits}",
        "spins_available_label": "🔄 Доступно спинов",
        "spins_available_with_count": "🔄 <b>Доступно спинов:</b> {spins}",
        "progress_to_next_level": "🎯 <b>Прогресс:</b> {progress}/{total} очков до следующего уровня",
        "spin_value_message": "🎰 Значение спина: {value}/64 - Попробуйте еще раз!",
        "jackpot_message": "🎉 ДЖЕКПОТ! 777! +{hits} попаданий (NFT заработан) +{points} очков",
        "jackpot_progress": "🎉 ДЖЕКПОТ! 777! +{hits} попаданий +{points} очков\n🎯 Прогресс: {current}/{needed} попаданий",
        
        # NFT reward messages
        "nft_earned_title": "🎉 <b>NFT ЗАРАБОТАН!</b> 🎉",
        "package_reward": "{emoji} <b>Награда {package} пакета</b>",
        "you_won": "🎁 <b>Вы выиграли:</b> <code>{nft_name}</code>",
        "withdrawal_info": "⬇️ <b>Вывод:</b> NFT будет добавлен в ваш профиль через 15 минут",
        
        # Error messages
        "user_data_not_found_error": "❌ <b>Данные пользователя не найдены!</b>\n\nПожалуйста, начните с /start.",
        "user_data_not_found_reply": "❌ Данные пользователя не найдены. Пожалуйста, используйте /start.",
        
        # Button text
        "back_to_menu": "🏠 Назад в меню",
        "my_profile": "👤 Мой профиль",
        "copy_link": "📋 Копировать ссылку",
        "share_stats": "📊 Поделиться статистикой",
        "back": "← Назад",
        "join_cg_spins": "🎮 Присоединиться к CG Spins",
        
        # Language selection
        "select_language": "🌐 <b>Выберите язык</b>",
        "english": "🇺🇸 English",
        "russian": "🇷🇺 Русский",
        "language_changed": "✅ Язык изменен на {language}",
        # Package details (keeping English names)
        "bronze_package": "🥉 <b>Bronze:</b> 30 спинов, нужно 1 попадание для NFT",
        "silver_package": "🥈 <b>Silver:</b> 60 спинов, нужно 3 попадания для NFT",
        "gold_package": "🥇 <b>Gold:</b> 300 спинов, нужно 10 попаданий для NFT",
        "black_package": "⚫ <b>Black:</b> 600 спинов, нужно 25 попаданий для NFT",
        
        "bronze_price": "🥉 <b>Bronze:</b> 1 Star или 0.01 TON",
        "silver_price": "🥈 <b>Silver:</b> 900 Stars или 4 TON",
        "gold_price": "🥇 <b>Gold:</b> 5000 Stars или 24 TON",
        "black_price": "⚫ <b>Black:</b> 10000 Stars или 49 TON",
        
        "bronze_nft_requirement": "🥉 <b>Bronze:</b> 1 попадание = NFT",
        "silver_nft_requirement": "🥈 <b>Silver:</b> 3 попадания = NFT",
        "gold_nft_requirement": "🥇 <b>Gold:</b> 10 попаданий = NFT",
        "black_nft_requirement": "⚫ <b>Black:</b> 25 попаданий = NFT",
        
        "bronze_nft_list": "🥉 <b>Bronze:</b> 38 NFT (Bow Tie, Bunny Muffin и др.) - до $25",
        "silver_nft_list": "🥈 <b>Silver:</b> 15 NFT (Bonded Ring, Diamond Ring и др.) - $50-$200",
        "gold_nft_list": "🥇 <b>Gold:</b> 3 NFT (Heroic Helmet, Precious Peach, Durov's Cap) - $500-$2K",
        "black_nft_list": "⚫ <b>Black:</b> 2 NFT (Heart Locket, Plush Pepe) - до $15K",
        
        "bronze_referral": "🥉 <b>Bronze:</b> +5 очков",
        "silver_referral": "🥈 <b>Silver:</b> +10 очков",
        "gold_referral": "�� <b>Gold:</b> +25 очков",
        "black_referral": "⚫ <b>Black:</b> +50 очков",
        
        # Level descriptions (keeping English names)
        "spinner_level": "🎰 <b>Spinner:</b> 0-19 очков",
        "collector_level": "🎁 <b>Collector:</b> 20-49 очков",
        "vip_level": "👑 <b>VIP:</b> 50-99 очков",
        "high_roller_level": "💎 <b>High-Roller:</b> 100+ очков",

    }
}


def get_text(user_id, key, **kwargs):
    """Get translated text for user"""
    user_lang = get_user_language(user_id)
    print(f"🌐 [Translation] User {user_id} requesting key '{key}', language: {user_lang}")
    
    # Check if language exists
    if user_lang not in TRANSLATIONS:
        print(f"⚠️ [Translation] Language '{user_lang}' not found, falling back to English")
        user_lang = "en"
    
    # Check if key exists in the language
    if key not in TRANSLATIONS[user_lang]:
        print(f"⚠️ [Translation] Key '{key}' not found in language '{user_lang}', falling back to English")
        if key not in TRANSLATIONS["en"]:
            print(f"❌ [Translation] Key '{key}' not found in any language!")
            return f"[Missing: {key}]"
        user_lang = "en"
    
    text = TRANSLATIONS[user_lang][key]
    print(f"🌐 [Translation] Returning text for key '{key}' in language '{user_lang}': {text[:50]}...")
    return text.format(**kwargs) if kwargs else text

def get_user_language(user_id):
    """Get user's preferred language"""
    # Import here to avoid circular imports
    from main import user_data
    from src.models import load_user_data
    
    # Handle case where user_id might be the user_data object instead of actual user ID
    if hasattr(user_id, 'keys') and hasattr(user_id, 'values'):
        # user_id is actually user_data object, try to extract the actual user_id
        print(f"⚠️ [Translation] user_id parameter is actually user_data object: {type(user_id)}")
        # Return default language since we can't determine the user
        return 'en'
    
    # Ensure user_id is an integer
    if not isinstance(user_id, int):
        print(f"⚠️ [Translation] user_id is not an integer: {type(user_id)} = {user_id}")
        return 'en'
    
    # Always get fresh data from database to ensure we have the latest language setting
    try:
        # Check if user exists in user_data by trying to access it
        if user_data.get(user_id):
            # Update user_data with fresh database data
            fresh_data = load_user_data(user_id)
            user_data[user_id].update(fresh_data)
            return user_data[user_id].get('language', 'en')
        else:
            # Load from database if not in memory
            fresh_data = load_user_data(user_id)
            user_data[user_id] = fresh_data
            return fresh_data.get('language', 'en')
    except Exception as e:
        print(f"⚠️ [Translation] Error getting language for user {user_id}: {e}")
        # Fallback: load directly from database
        try:
            fresh_data = load_user_data(user_id)
            return fresh_data.get('language', 'en')
        except:
            return 'en'  # Ultimate fallback

# Admin Panel Translations
ADMIN_TRANSLATIONS = {
    "en": {
        # Admin Panel Main Menu
        "admin_panel_title": "⚙️ <b>Admin Panel</b>",
        "admin_welcome": "Welcome to the admin panel. Choose an option:",
        
        # Admin Menu Options
        "user_management": "👥 User Management",
        "game_management": "🎮 Game Management", 
        "financial_management": "💰 Financial Management",
        "system_management": "🔧 System Management",
        "content_management": "📝 Content Management",
        "analytics_reports": "📊 Analytics & Reports",
        "back_to_main": "🏠 Back to Main Menu",
        
        # User Management
        "user_management_title": "👥 <b>User Management</b>",
        "view_all_users": "👀 View All Users",
        "user_details": "👤 User Details",
        "reset_user_data": "🔄 Reset User Data",
        "ban_unban_users": "🚫 Ban/Unban Users",
        "add_remove_spins": "➕➖ Add/Remove Spins",
        
        # Game Management
        "game_management_title": "🎮 <b>Game Management</b>",
        "package_statistics": "📦 Package Statistics",
        "nft_distribution": "🎁 NFT Distribution",
        "hit_statistics": "🎯 Hit Statistics",
        "game_settings": "⚙️ Game Settings",
        
        # Financial Management
        "financial_management_title": "💰 <b>Financial Management</b>",
        "payment_tracking": "💳 Payment Tracking",
        "revenue_analytics": "📈 Revenue Analytics",
        "pending_payments": "⏳ Pending Payments",
        "transaction_history": "📋 Transaction History",
        
        # System Management
        "system_management_title": "🔧 <b>System Management</b>",
        "bot_statistics": "📊 Bot Statistics",
        "database_management": "🗄️ Database Management",
        "logs_monitoring": "📝 Logs & Monitoring",
        "maintenance_mode": "🔧 Maintenance Mode",
        
        # Content Management
        "content_management_title": "📝 <b>Content Management</b>",
        "broadcast_messages": "📢 Broadcast Messages",
        "update_translations": "🌐 Update Translations",
        "package_pricing": "💲 Package Pricing",
        "faq_management": "❓ FAQ Management",
        
        # Analytics & Reports
        "analytics_reports_title": "📊 <b>Analytics & Reports</b>",
        "daily_reports": "📅 Daily Reports",
        "weekly_reports": "📆 Weekly Reports",
        "monthly_reports": "📆 Monthly Reports",
        "popular_packages": "🏆 Popular Packages",
        "user_retention": "👥 User Retention",
        "export_data": "📤 Export Data",
        
        # Common Admin Messages
        "access_denied": "❌ Access denied. Admin privileges required.",
        "admin_only": "🔒 This feature is only available to administrators.",
        "operation_successful": "✅ Operation completed successfully!",
        "operation_failed": "❌ Operation failed. Please try again.",
        "invalid_user_id": "❌ Invalid user ID provided.",
        "user_not_found": "❌ User not found.",
        "enter_user_id": "Please enter a user ID:",
        "enter_message": "Please enter your message:",
        "broadcast_sent": "📢 Broadcast message sent to all users!",
    },
    "ru": {
        # Admin Panel Main Menu
        "admin_panel_title": "⚙️ <b>Панель администратора</b>",
        "admin_welcome": "Добро пожаловать в панель администратора. Выберите опцию:",
        
        # Admin Menu Options
        "user_management": "👥 Управление пользователями",
        "game_management": "🎮 Управление игрой",
        "financial_management": "💰 Финансовое управление",
        "system_management": "🔧 Управление системой",
        "content_management": "📝 Управление контентом",
        "analytics_reports": "📊 Аналитика и отчеты",
        "back_to_main": "🏠 Назад в главное меню",
        
        # User Management
        "user_management_title": "👥 <b>Управление пользователями</b>",
        "view_all_users": "👀 Просмотр всех пользователей",
        "user_details": "👤 Детали пользователя",
        "reset_user_data": "🔄 Сброс данных пользователя",
        "ban_unban_users": "🚫 Блокировка/разблокировка пользователей",
        "add_remove_spins": "➕➖ Добавить/удалить спины",
        
        # Game Management
        "game_management_title": "🎮 <b>Управление игрой</b>",
        "package_statistics": "📦 Статистика пакетов",
        "nft_distribution": "🎁 Распределение NFT",
        "hit_statistics": "🎯 Статистика попаданий",
        "game_settings": "⚙️ Настройки игры",
        
        # Financial Management
        "financial_management_title": "💰 <b>Финансовое управление</b>",
        "payment_tracking": "💳 Отслеживание платежей",
        "revenue_analytics": "📈 Аналитика доходов",
        "pending_payments": "⏳ Ожидающие платежи",
        "transaction_history": "📋 История транзакций",
        
        # System Management
        "system_management_title": "🔧 <b>Управление системой</b>",
        "bot_statistics": "📊 Статистика бота",
        "database_management": "🗄️ Управление базой данных",
        "logs_monitoring": "📝 Логи и мониторинг",
        "maintenance_mode": "🔧 Режим обслуживания",
        
        # Content Management
        "content_management_title": "📝 <b>Управление контентом</b>",
        "broadcast_messages": "📢 Массовые сообщения",
        "update_translations": "🌐 Обновление переводов",
        "package_pricing": "💲 Ценообразование пакетов",
        "faq_management": "❓ Управление FAQ",
        
        # Analytics & Reports
        "analytics_reports_title": "📊 <b>Аналитика и отчеты</b>",
        "daily_reports": "📅 Ежедневные отчеты",
        "weekly_reports": "📆 Еженедельные отчеты",
        "monthly_reports": "📆 Ежемесячные отчеты",
        "popular_packages": "🏆 Популярные пакеты",
        "user_retention": "👥 Удержание пользователей",
        "export_data": "📤 Экспорт данных",
        
        # Common Admin Messages
        "access_denied": "❌ Доступ запрещен. Требуются права администратора.",
        "admin_only": "🔒 Эта функция доступна только администраторам.",
        "operation_successful": "✅ Операция выполнена успешно!",
        "operation_failed": "❌ Операция не удалась. Попробуйте еще раз.",
        "invalid_user_id": "❌ Предоставлен неверный ID пользователя.",
        "user_not_found": "❌ Пользователь не найден.",
        "enter_user_id": "Пожалуйста, введите ID пользователя:",
        "enter_message": "Пожалуйста, введите ваше сообщение:",
        "broadcast_sent": "📢 Массовое сообщение отправлено всем пользователям!",
    }
}

def get_admin_text(user_id: int, key: str, **kwargs) -> str:
    """Get admin panel text in user's language"""
    language = get_user_language(user_id)
    text = ADMIN_TRANSLATIONS.get(language, {}).get(key, ADMIN_TRANSLATIONS["en"].get(key, key))
    
    # Format with provided parameters
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # If formatting fails, return original text
    
    return text

