# 🤖 AI Research Feed Widget - Embedding Instructions

**Live AI-to-AI conversation and research insights for your Neon One website!**

---

## 🎯 What This Widget Does

Shows members:
- ✅ Real-time Julius AI ↔ Replit Agent conversations
- ✅ Research insights as they're discovered
- ✅ Hypothesis proposals
- ✅ Task progress tracking
- ✅ Conservation priorities
- ✅ Statistics and timeline

**Perfect for:**
- Scientific Method Botany Research page
- Members-only research dashboard
- Admin monitoring panel
- Educational transparency

---

## 📋 Embedding in Neon One CMS

### **Option 1: Full Widget (Recommended)**

Shows AI conversation + Research insights + Statistics

```html
<!-- Add this to your Neon One page HTML -->
<div id="ai-research-feed" 
     data-widget="ai-research-feed"
     data-auto-init="true"
     data-api-base="https://orchid-continuum.replit.app"
     data-refresh-interval="60000"
     data-max-messages="20">
</div>

<script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
```

### **Option 2: Insights Only**

Show only research insights (for public pages)

```html
<div id="ai-research-feed" 
     data-widget="ai-research-feed"
     data-auto-init="true"
     data-api-base="https://orchid-continuum.replit.app"
     data-show-communication="false"
     data-show-insights="true">
</div>

<script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
```

### **Option 3: Admin Mode**

Full access with extended details

```html
<div id="ai-research-feed" 
     data-widget="ai-research-feed"
     data-auto-init="true"
     data-api-base="https://orchid-continuum.replit.app"
     data-admin-mode="true"
     data-refresh-interval="30000">
</div>

<script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
```

---

## ⚙️ Configuration Options

| Attribute | Default | Description |
|-----------|---------|-------------|
| `data-api-base` | (required) | Your Orchid Continuum API URL |
| `data-refresh-interval` | 60000 | Update frequency in milliseconds |
| `data-max-messages` | 20 | Number of messages/insights to show |
| `data-show-communication` | true | Show AI conversation tab |
| `data-show-insights` | true | Show research insights tab |
| `data-admin-mode` | false | Enable extended admin features |

---

## 🎨 Customization

### **Color Scheme**

The widget uses a purple gradient by default. To match your brand:

```html
<style>
  .ai-research-feed {
    background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%) !important;
  }
</style>
```

### **Size**

```html
<style>
  #ai-research-feed {
    max-width: 1200px;
    margin: 0 auto;
  }
</style>
```

---

## 🔒 Access Control

### **Members-Only**

Use Neon One's built-in member gates:

```html
<!-- Only visible to logged-in members -->
<div class="members-only-content">
    <div id="ai-research-feed" data-widget="ai-research-feed" data-auto-init="true" 
         data-api-base="https://orchid-continuum.replit.app"></div>
    <script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
</div>
```

### **Admin-Only**

Use Neon One's admin role gates:

```html
<!-- Only visible to admins -->
<div class="admin-only-content">
    <div id="ai-research-feed" data-widget="ai-research-feed" data-auto-init="true" 
         data-api-base="https://orchid-continuum.replit.app"
         data-admin-mode="true"></div>
    <script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
</div>
```

---

## 📱 Responsive Design

Widget automatically adapts to mobile devices:
- ✅ Stacks tabs vertically on small screens
- ✅ Adjusts grid layouts
- ✅ Touch-friendly buttons
- ✅ Optimized scrolling

---

## 🔧 API Endpoints Required

Your Orchid Continuum backend must provide these endpoints:

### **1. GET /api/ai-communication**

Returns AI conversation messages

Query params:
- `limit` (optional): Number of messages (default 20)

Response:
```json
[
  {
    "id": 1,
    "task_id": "task_001",
    "from_agent": "julius_ai",
    "to_agent": "replit_agent",
    "message_type": "response",
    "status": "completed",
    "prompt_text": "Extract orchid traits from TraitBank",
    "result_summary": "Extracted 500,000 trait measurements",
    "created_at": "2025-10-21T09:00:00Z"
  }
]
```

### **2. GET /api/research-insights**

Returns research insights

Query params:
- `limit` (optional): Number of insights (default 20)

Response:
```json
[
  {
    "id": 1,
    "insight_type": "finding",
    "research_area": "pollination",
    "insight_text": "87% of moth-pollinated orchids are white or pale colored",
    "confidence_level": "high",
    "proposed_followup": "Investigate geographic distribution",
    "julius_generated": true,
    "impact_score": 8,
    "created_at": "2025-10-21T10:30:00Z"
  }
]
```

### **3. GET /api/ai-stats**

Returns statistics

Response:
```json
{
  "total_tasks": 42,
  "completed_tasks": 38,
  "pending_tasks": 4,
  "total_insights": 156,
  "hypotheses_tested": 23,
  "research_proposals": 12,
  "recent_activity": [
    {
      "title": "Task 042 completed: Climate vulnerability analysis",
      "timestamp": "2025-10-21T14:20:00Z"
    }
  ]
}
```

---

## 🚀 Deployment Options

### **Option A: CDN Hosting** (Recommended)

1. Upload `ai-research-feed.js` to your CDN
2. Update script src in embed code
3. Use same CDN as other Orchid Continuum widgets

### **Option B: Neon One Direct**

1. Upload as custom JavaScript in Neon One
2. No external dependencies needed
3. Widget is self-contained

### **Option C: Inline**

For testing, paste entire `ai-research-feed.js` content into Neon One page

---

## 📍 Integration with Existing Widget

You mentioned having a "Scientific Method Botany Research" widget. 

**Perfect integration:**

```html
<!-- Your existing widget -->
<div id="scientific-method-widget"></div>

<!-- Add AI Research Feed below -->
<h2>🤖 Live AI Research</h2>
<p>Watch Julius AI and Replit Agent collaborate in real-time to discover orchid evolution patterns!</p>

<div id="ai-research-feed" 
     data-widget="ai-research-feed"
     data-auto-init="true"
     data-api-base="https://orchid-continuum.replit.app">
</div>

<script src="https://your-cdn.com/ai-research-feed/ai-research-feed.js"></script>
```

**Benefits:**
- Members see scientific method in action (your widget)
- Members see AI applying scientific method (AI feed)
- Shows transparency: "This is how we do research!"
- Educational: "Watch AI discover patterns autonomously"

---

## 🎊 Use Cases

### **1. Research Transparency**

Show members that FCOS uses cutting-edge AI for orchid research:
- "Our research is done by autonomous AI agents"
- "Watch discoveries happen in real-time"
- "Every insight is captured and analyzed"

### **2. Educational Value**

Members learn:
- How AI conducts scientific research
- What kinds of patterns AI discovers
- How hypotheses are generated and tested
- The scientific method in action

### **3. Member Engagement**

Members can:
- Follow ongoing research projects
- See their orchid submissions being analyzed
- Watch conservation priorities emerge
- Feel part of cutting-edge science

### **4. Admin Monitoring**

Admins can:
- Track AI progress
- Review research insights
- Approve/reject proposals
- Monitor system health

---

## 💡 Content Ideas

**Page Title:** "Live AI Orchid Research Lab"

**Description:**
> "Watch Julius AI and Replit Agent work together to analyze 35,320 orchid species, discover evolutionary patterns, and identify conservation priorities. This autonomous research system runs 24/7, continuously generating insights about pollination, climate adaptation, and trait evolution."

**Member Value Proposition:**
> "As an FCOS member, you have exclusive access to our AI research lab. See discoveries as they happen, follow hypothesis testing, and contribute to cutting-edge botanical science!"

---

## 🔍 SEO & Accessibility

Widget includes:
- ✅ Semantic HTML
- ✅ ARIA labels
- ✅ Keyboard navigation
- ✅ Screen reader support
- ✅ Mobile-first design

---

## 📊 Analytics Tracking

Add Google Analytics events:

```javascript
// Track widget interactions
document.addEventListener('DOMContentLoaded', () => {
    const widget = document.getElementById('ai-research-feed');
    widget.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-btn')) {
            gtag('event', 'ai_feed_tab_click', {
                'tab_name': e.target.dataset.tab
            });
        }
    });
});
```

---

## 🎯 Next Steps

1. **Add API endpoints** to Orchid Continuum backend
2. **Upload widget** to CDN
3. **Embed in Neon One** on Scientific Method page
4. **Set as members-only** initially
5. **Promote to members** in newsletter
6. **Gather feedback** and iterate

---

## 🌟 Future Enhancements

Could add:
- Click to expand full task details
- Filter insights by research area
- Download insight reports
- Share insights on social media
- Comment/discussion on insights
- Email notifications for new discoveries

---

**This widget turns your autonomous AI research into a member engagement tool!** 🚀

**Members don't just hear about research - they WATCH it happen!** 🔬✨
