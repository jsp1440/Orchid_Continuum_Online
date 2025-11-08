# 🔧 Fix Google Drive Storage Quota Error

## Problem
Your app shows: **"The user's Drive storage quota has been exceeded"**

**Why?** The service account only has 15 GB storage (full!), but YOU have 2 TB!

---

## ✅ Solution: Enable Domain-Wide Delegation

This lets the service account create files **as you**, using YOUR 2 TB storage.

---

## 📋 Setup Steps (5 minutes)

### Step 1: Get Your Service Account Email

1. Go to **Google Cloud Console**: https://console.cloud.google.com
2. Click **IAM & Admin** → **Service Accounts**
3. Find your service account (should look like: `xxxxx@xxxxx.iam.gserviceaccount.com`)
4. Copy the **Client ID** (long number like `123456789012345678901`)

---

### Step 2: Enable Domain-Wide Delegation

**In Google Cloud Console:**

1. Still on the **Service Accounts** page
2. Click on your service account
3. Click **"Show Domain-Wide Delegation"** at the top
4. Click **"Enable G Suite Domain-Wide Delegation"**
5. Click **Save**

---

### Step 3: Authorize in Google Workspace Admin

⚠️ **IMPORTANT:** This step is REQUIRED for @gmail.com accounts upgraded to Workspace!

1. Go to **Google Workspace Admin Console**: https://admin.google.com
2. Navigate to: **Security** → **Access and data control** → **API Controls**
3. Click **"Manage Domain Wide Delegation"**
4. Click **"Add new"**
5. Enter:
   - **Client ID**: `[paste the Client ID from Step 1]`
   - **OAuth Scopes**: Copy/paste this exactly:
     ```
     https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/drive.file
     ```
6. Click **"Authorize"**

---

### Step 4: Restart Your App

After completing the above:

1. **In Replit**: Click the **Run** button to restart your app
2. Check the logs - you should see:
   ```
   ✅ Using domain-wide delegation to impersonate Fcospresident@gmail.com
   📊 Files will use Fcospresident@gmail.com's 2TB storage quota
   ```

---

## 🎯 Result

✅ **Before:** Service account uses its 15 GB (FULL!)  
✅ **After:** Files use YOUR 2 TB storage!

---

## ⚠️ Troubleshooting

### "I don't have access to Google Workspace Admin Console"

**Option A:** Get admin access
- If this is your Workspace account, you should be the admin
- Log in with your admin credentials at https://admin.google.com

**Option B:** Have your Workspace admin do Step 3
- Send them the Client ID and OAuth scopes
- They can authorize the service account

### "I can't find my service account"

Check your secrets in Replit:
1. Look at `GOOGLE_SERVICE_ACCOUNT_JSON` secret
2. The service account email is in the `client_email` field

---

## 📊 How to Verify It's Working

After setup, create a test file and check who owns it:

```python
# In Google Drive, right-click any file created by your app
# Click "Share" 
# Owner should be: Fcospresident@gmail.com (not the service account!)
```

✅ **Success!** Files now use your 2 TB quota!

---

## 🔗 Official Google Documentation

- Domain-Wide Delegation Guide: https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority
- Service Account Setup: https://cloud.google.com/iam/docs/service-accounts-create
