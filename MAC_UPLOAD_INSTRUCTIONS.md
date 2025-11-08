# 📤 Upload Your Mac Images to Orchid Continuum

## 🚀 Quick Start (2 Minutes)

### Step 1: Download the Script
Download this file to your Mac:
- **File**: `mac_upload_orchid_images.sh` (in this workspace)

### Step 2: Run on Your Mac Terminal

```bash
# Navigate to where you saved the script
cd ~/Downloads

# Make it executable
chmod +x mac_upload_orchid_images.sh

# Run it
./mac_upload_orchid_images.sh
```

### Step 3: Upload the ZIP
The script will:
1. ✅ Find all orchid images from the last 7 days
2. ✅ Create a ZIP file on your Desktop: `orchid_images_YYYYMMDD_HHMMSS.zip`
3. ✅ Open your Desktop folder

**Then:**
- Drag the ZIP file into this Replit workspace
- Tell me: "I uploaded the orchid images zip"

---

## 📁 Where It Searches

The script looks for `.jpg`, `.jpeg`, `.png` files in:
- `~/Downloads`
- `~/Desktop`
- `/tmp/eol_orchid_rescue`
- `~/Documents/orchid_downloads`

**Modified in the last 7 days**

---

## 🔧 Manual Alternative (If Script Doesn't Work)

### Option 1: Manual Search
```bash
# Find images from last 7 days
find ~/Downloads -name "*.jpg" -mtime -7

# Copy them to Desktop
mkdir ~/Desktop/orchid_images
find ~/Downloads -name "*.jpg" -mtime -7 -exec cp {} ~/Desktop/orchid_images/ \;

# Create ZIP
cd ~/Desktop/orchid_images
zip -r ~/Desktop/orchid_images.zip .
```

### Option 2: Specific Folder
If you know exactly where your images are:
```bash
# Replace with your actual path
cd /path/to/your/orchid/images
zip -r ~/Desktop/my_orchid_images.zip *.jpg
```

---

## 🎯 After Upload

Once you upload the ZIP to Replit, I'll automatically:
1. Extract all images
2. Categorize them (photos, herbarium, plates)
3. Import to the database with proper metadata
4. Link to your BloomBuilder species
5. Make them available in the app

---

## ❓ Troubleshooting

**"Permission denied"**
```bash
chmod +x mac_upload_orchid_images.sh
```

**"No images found"**
- Try increasing the time range: change `-mtime -7` to `-mtime -14` (14 days)
- Check if images are in a different folder

**"Command not found: zip"**
```bash
# Use tar instead
tar -czf ~/Desktop/orchid_images.tar.gz ~/Downloads/*.jpg
```

---

## 📞 Need Help?

Just tell me:
- "The script isn't working"
- "I can't find my images"
- "Where are my orchid downloads?"

I'll help you find them! 🌺
