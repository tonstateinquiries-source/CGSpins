# 📋 **GitHub Repository Upload List**

## ✅ **FILES TO UPLOAD** (Essential for deployment)

### **Core Application Files**
- `main.py` - Main bot application
- `config.py` - Configuration (with environment variables)
- `translations.py` - Multi-language support
- `requirements.txt` - Python dependencies

### **Deployment Configuration**
- `Procfile` - Railway process definition
- `railway.json` - Railway configuration
- `railway_config.py` - Railway-specific config

### **Source Code Modules**
- `src/` folder (entire directory)
  - `src/__init__.py`
  - `src/models/` (all files)
  - `src/services/` (all files) 
  - `src/utils/` (all files)

### **Assets & Images**
- `cgpackages.png` - Packages menu image
- `cgspins1.png` - Main menu image
- `cgspins_ava.png` - Avatar image

### **Documentation**
- `README.md` - Project documentation
- `DEPLOYMENT.md` - Deployment instructions
- `RAILWAY_DEPLOYMENT.md` - Railway-specific guide
- `RAILWAY_TROUBLESHOOTING.md` - Troubleshooting guide

### **Configuration Files**
- `.gitignore` - Git ignore rules
- `.env.example` - Environment variables template

---

## ❌ **FILES TO EXCLUDE** (Do NOT upload)

### **Database Files**
- `*.db` - Database files
- `*.db-shm` - Database shared memory
- `*.db-wal` - Database write-ahead log

### **Export Files**
- `*_export_*.csv` - User/transaction exports
- `transactions_export_*.csv`
- `users_export_*.csv`

### **Backup Directories**
- `backup_*/` - All backup folders
- `cleanup_backup_*/` - Cleanup backup folders
- `src_backup_*/` - Source code backups

### **Cache & Temporary Files**
- `__pycache__/` - Python cache
- `venv/` - Virtual environment
- `*.log` - Log files

### **Deployment Archives**
- `cgspins-deployment.zip` - Deployment archive

---

## 🚀 **Upload Instructions**

### **Method 1: Manual Upload (Recommended)**
1. Go to https://github.com/tonstateinquiries-source/CGSpins
2. Click "Add file" → "Upload files"
3. Drag and drop all files from the ✅ list above
4. Commit with message: "Initial commit: CG Spins Telegram Bot"

### **Method 2: Selective Upload**
Upload these files in this order:
1. **Core files:** `main.py`, `config.py`, `translations.py`, `requirements.txt`
2. **Deployment:** `Procfile`, `railway.json`, `railway_config.py`
3. **Source code:** Upload entire `src/` folder
4. **Assets:** `cgpackages.png`, `cgspins1.png`, `cgspins_ava.png`
5. **Documentation:** `README.md`, `DEPLOYMENT.md`, etc.

---

## ✅ **Verification Checklist**

After upload, verify these files are in the repository:
- [ ] `main.py` (main application)
- [ ] `config.py` (with environment variables)
- [ ] `requirements.txt` (with all dependencies)
- [ ] `Procfile` (Railway process definition)
- [ ] `railway.json` (Railway configuration)
- [ ] `src/` folder (complete source code)
- [ ] Image files (`cgpackages.png`, `cgspins1.png`, `cgspins_ava.png`)
- [ ] `.gitignore` (excludes sensitive files)

---

## 🎯 **Next Steps After Upload**

1. **Go to Railway Dashboard**
2. **Connect GitHub repository**
3. **Set environment variables:**
   ```
   BOT_TOKEN=8311672539:AAGYEfx8rFqhpOceXZVqE5R6_59XT_I5Tvk
   BOT_USERNAME=your_bot_username_here
   ADMIN_USER_IDS=8059922747
   TON_API_KEY=AGJQUFOYHFLEG6IAAAAC4PGPQD77EA6BN6O7HNKLRHISROVWNACB423KZS3DADE7IOXNWYI
   TON_WALLET_ADDRESS=EQAlSNKjRlmJ1nz86lRKyqap39BiJ39LF1DkmqjXb-EL22D6
   ```
4. **Deploy!**

---

**Total files to upload: ~35 files**
**Total size: ~2-3 MB**
