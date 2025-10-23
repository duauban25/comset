# Streamlit Cloud Setup Guide

## Step-by-Step Configuration

### 1. Access Your App Dashboard
- Go to https://share.streamlit.io/
- Find your app: **comset**
- Click the three-dot menu (⋮) in the top-right corner
- Select **"Manage app"**

### 2. Navigate to Secrets
- In the Manage app page, click **"Settings"** (gear icon)
- Scroll down to **"Advanced settings"**
- Click on **"Secrets"**

### 3. Add DATA_DIR Secret
In the Secrets editor, add this line:

```
DATA_DIR = "/mount/data"
```

**Important**: 
- No quotes around the path value
- Exact path: `/mount/data`
- This is the persistent storage directory on Streamlit Cloud

### 4. Save and Restart
- Click **"Save"** button
- Go back to the app dashboard
- Click **"Restart and clear cache"** button (bottom-right)
- Wait 1-2 minutes for the app to rebuild

### 5. Verify Configuration
After restart, check the app:
- Look for the message: `✅ Data dimuat dari: /mount/data/comparative_data.csv`
- If you see `/mount/data/` in the path, configuration is correct ✅
- If you still see `/home/appuser/...`, the secret wasn't applied (try restarting again)

## What This Does

- **DATA_DIR = "/mount/data"**: Tells the app to store all CSV files in Streamlit Cloud's persistent storage
- **Persistent**: Data survives app restarts and updates
- **Shared**: All instances of your app use the same data directory

## Files Created

Once configured, these files will be stored in `/mount/data/`:
- `comparative_data.csv` - Hotel performance data
- `room_capacity.csv` - Hotel room capacity reference

## Troubleshooting

### Still seeing `/home/appuser/...` path?
1. Verify the secret was saved (check Secrets page again)
2. Make sure you clicked "Restart and clear cache"
3. Wait 2-3 minutes for rebuild to complete
4. Refresh the browser page

### Getting permission errors?
- The `/mount/data` directory is automatically created by Streamlit Cloud
- If errors persist, check the app logs in Manage app → Logs

### Need to reset data?
- Delete files in Streamlit Cloud's file system (via SSH or app interface)
- Or upload new CSV files via the app's upload feature

## Summary

✅ **After completing these steps:**
- App data persists between restarts
- All CSV files stored in `/mount/data/`
- Ready for production use
