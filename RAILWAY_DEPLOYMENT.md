# 🚀 Railway Deployment Guide

## ✅ Pre-Deployment Checklist

### 1. **Environment Variables Setup**
In Railway dashboard, add these environment variables:

```
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username_here
ADMIN_USER_IDS=123456789,987654321
TON_API_KEY=your_ton_api_key_here
TON_WALLET_ADDRESS=your_ton_wallet_address_here
```

### 2. **Database Setup**
- Railway will automatically provide `DATABASE_URL` environment variable
- The bot will automatically create tables on first run
- No manual database setup required

### 3. **Files Ready for Deployment**
✅ `main.py` - Main bot file
✅ `config.py` - Configuration
✅ `translations.py` - Internationalization
✅ `requirements.txt` - Dependencies
✅ `Procfile` - Process definition
✅ `railway.json` - Railway configuration
✅ `src/` - Source code modules
✅ Image files: `cgpackages.png`, `cgspins1.png`, `cgspins_ava.png`

### 4. **Features Ready**
✅ TON & Stars payments
✅ Admin notifications for purchases & NFT wins
✅ Referral system with 15% & 25% rates
✅ Multi-language support (EN/RU)
✅ Admin panel with full functionality
✅ Database statistics & integrity checks
✅ Package pricing: Bronze 450⭐/2💎, Silver 900⭐/4💎, Gold 5000⭐/24💎, Black 10000⭐/49💎

## 🚀 Deployment Steps

1. **Connect Repository**
   - Go to Railway dashboard
   - Click "New Project"
   - Connect your GitHub repository

2. **Add Environment Variables**
   - Go to Variables tab
   - Add all required environment variables (see above)

3. **Deploy**
   - Railway will automatically detect Python project
   - It will use the `Procfile` and `railway.json` configuration
   - Deployment will start automatically

4. **Monitor**
   - Check deployment logs
   - Verify bot starts without errors
   - Test basic functionality

## 🔧 Post-Deployment Testing

1. **Test Bot Commands**
   - `/start` - Should show main menu with image
   - `/help` - Should show help menu
   - `/referral` - Should show referral info

2. **Test Admin Panel**
   - Use admin commands to verify functionality
   - Check database statistics
   - Test user management features

3. **Test Payments**
   - Test Stars payment flow
   - Test TON payment flow
   - Verify admin notifications work

## 📊 Monitoring

- Check Railway logs for any errors
- Monitor database performance
- Watch for admin notifications
- Track user registrations and payments

## 🆘 Troubleshooting

**Bot not starting:**
- Check environment variables are set correctly
- Verify BOT_TOKEN is valid
- Check Railway logs for errors

**Database errors:**
- Ensure DATABASE_URL is set by Railway
- Check if tables are created properly
- Verify database permissions

**Payment issues:**
- Verify TON_API_KEY is correct
- Check TON_WALLET_ADDRESS format
- Ensure admin notifications are working

## 🎯 Success Indicators

✅ Bot responds to `/start`
✅ Admin panel accessible
✅ Package purchases work
✅ Admin notifications received
✅ Database statistics available
✅ No errors in Railway logs

---

**Ready for deployment! 🚀**
