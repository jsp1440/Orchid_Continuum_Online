# AI Status UI Banner Guide

## 🎨 What Was Added

A **visual banner** that appears at the top of every page when AI features are disabled (`ORCHID_AI_ENABLED=false`).

---

## 📍 Implementation

### **1. Template Context Injection** (`app.py`)
```python
@app.context_processor
def inject_ai_status():
    """Make AI status available to all templates."""
    from app.settings import ORCHID_AI_ENABLED
    from app.ai_utils import get_ai_status
    return {
        'ORCHID_AI_ENABLED': ORCHID_AI_ENABLED,
        'ai_status': get_ai_status()
    }
```

All templates now have access to:
- `ORCHID_AI_ENABLED` - Boolean flag
- `ai_status` - Full AI status dict

### **2. Banner in Base Template** (`templates/base.html`)

**Banner appears when**: `ORCHID_AI_ENABLED=false`

```html
{% if not ORCHID_AI_ENABLED %}
<div class="ai-paused-banner" id="aiPausedBanner">
    <span class="ai-paused-banner-icon">🔒</span>
    <span class="ai-paused-banner-text">
        <strong>AI Features Temporarily Paused</strong> — 
        Browse our gallery, search database, and explore orchid collections 
        while we manage API quotas. All research features remain available!
    </span>
    <button class="ai-paused-banner-dismiss" onclick="dismissAiBanner()">
        Dismiss
    </button>
</div>
{% endif %}
```

---

## 🎨 Banner Features

### **Visual Design**
- **Dark gradient background** with orange accent border
- **🔒 Lock icon** to indicate paused state
- **Informative message** explaining what's happening
- **Dismiss button** for user control

### **User Experience**
✅ **Persistent dismissal** - Stored in localStorage  
✅ **Non-blocking** - Doesn't prevent site usage  
✅ **Informative** - Explains why AI is paused  
✅ **Actionable** - Shows what users CAN still do  

### **CSS Styling**
```css
.ai-paused-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-left: 4px solid #f39c12;
    padding: 12px 16px;
    color: #f39c12;
    /* ... */
}
```

**Colors**:
- **Orange (#f39c12)** - Warning/notice (not error)
- **Dark blue gradient** - Matches site theme
- **Subtle shadow** - Professional look

---

## 🔍 Banner States

### **State 1: AI Enabled** (`ORCHID_AI_ENABLED=true`)
- **Banner**: Not shown
- **AI features**: Fully operational
- **User sees**: Normal site with AI chat, search assistant, etc.

### **State 2: AI Disabled** (`ORCHID_AI_ENABLED=false`)
- **Banner**: Visible at top of page
- **AI features**: Return placeholder responses
- **User sees**: Banner + friendly "AI paused" messages in API responses

### **State 3: Banner Dismissed** (User clicked "Dismiss")
- **Banner**: Hidden (saved in localStorage)
- **AI features**: Still disabled
- **User sees**: No banner, but AI still returns "paused" messages

---

## 📊 Banner vs. API Response Messages

### **Banner (Visual UI)**
```
🔒 AI Features Temporarily Paused — Browse our gallery, search database, 
and explore orchid collections while we manage API quotas.
```
- **Where**: Top of page (all pages)
- **When**: AI disabled via env var
- **Purpose**: Site-wide notification

### **API Response Messages** (In Code)
```json
{
  "success": true,
  "response": "🔒 AI features are temporarily paused...",
  "ai_paused": true
}
```
- **Where**: API endpoints (`/globe/chat`, `/api/search/chat`, etc.)
- **When**: User tries to use AI feature
- **Purpose**: Feature-specific feedback

---

## 🛠️ Customization

### **Change Banner Message**
Edit `templates/base.html`:
```html
<span class="ai-paused-banner-text">
    <strong>Your Custom Message Here</strong> — 
    Additional details...
</span>
```

### **Change Banner Color**
Edit CSS in `templates/base.html`:
```css
.ai-paused-banner {
    border-left: 4px solid #YOUR_COLOR;  /* Change accent color */
    color: #YOUR_COLOR;                   /* Change text color */
}
```

### **Add Icon**
Replace 🔒 with any emoji or Feather icon:
```html
<!-- Emoji -->
<span class="ai-paused-banner-icon">⏸️</span>

<!-- Feather Icon -->
<i data-feather="pause-circle" class="ai-paused-banner-icon"></i>
```

---

## 🧪 Testing

### **Test Banner Visibility**
```bash
# Deploy with AI disabled (default)
# Visit any page on your site

Expected:
✅ Orange banner at top of page
✅ "AI Features Temporarily Paused" message visible
✅ Dismiss button works
✅ Banner stays dismissed after page refresh
```

### **Test Banner Removal**
```bash
# Enable AI in Render Dashboard
ORCHID_AI_ENABLED=true

# Redeploy

Expected:
✅ No banner visible
✅ AI features work normally
```

---

## 📱 Responsive Design

The banner is **fully responsive**:

- **Desktop**: Full-width with icon, text, and button
- **Tablet**: Slightly smaller padding
- **Mobile**: Stacks icon above text if needed

CSS handles this automatically via flexbox.

---

## ♿ Accessibility

✅ **Color contrast**: Orange on dark blue meets WCAG AA standards  
✅ **Keyboard accessible**: Dismiss button is focusable  
✅ **Screen reader friendly**: Text clearly explains status  
✅ **Non-intrusive**: Doesn't block content or navigation  

---

## 🎯 Benefits

| Benefit | Impact |
|---------|--------|
| **Transparent Communication** | Users know why AI is unavailable |
| **Reduces Support Tickets** | Self-explanatory message |
| **Maintains Trust** | Shows professional management of resources |
| **Non-Blocking** | Users can still use all non-AI features |
| **User Control** | Dismissible for returning visitors |

---

## 📝 Example User Journey

### **Scenario**: OpenAI quota exhausted mid-day

**Admin action**: Set `ORCHID_AI_ENABLED=false` in Render

**User experience**:
1. ✅ Visits site → Sees orange banner at top
2. ✅ Reads message → Understands AI is temporarily paused
3. ✅ Clicks "Dismiss" → Banner disappears
4. ✅ Tries AI chat → Gets friendly "AI paused" response
5. ✅ Uses gallery/search → Everything works normally
6. ✅ Returns next day → Banner stays dismissed
7. ✅ Admin re-enables AI → Banner disappears for everyone

**Result**: Zero downtime, informed users, professional experience! 🎉

---

## 🔗 Related Files

```
✅ app.py (lines 94-102)        - Context processor injection
✅ templates/base.html           - Banner HTML & CSS
✅ app/settings.py               - ORCHID_AI_ENABLED flag
✅ app/ai_utils.py               - get_ai_status() function
```

---

## 🎉 Summary

**You now have a complete UI/UX system for AI status!**

- ✅ **Visual banner** when AI is disabled
- ✅ **Dismissible** for better UX
- ✅ **Persistent** (localStorage)
- ✅ **Professional** appearance
- ✅ **Informative** messaging
- ✅ **Accessible** design

**Your users will always know the status of AI features!** 🌸
