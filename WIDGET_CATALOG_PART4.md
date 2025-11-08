# Widget Catalog - Part 4: Admin & System Tools
**Section 4 of 5**

---

## 46. Admin Dashboard
**File:** `templates/admin/dashboard.html`
**Route:** `/admin/dashboard`
**Status:** ✅ Central admin control

**What it does:**
Main administrative control panel for platform management and monitoring.

**Features:**
- System health overview
- User statistics
- Database metrics
- Recent activity log
- Quick actions menu
- Widget status monitoring

**Access:** Admin authentication required
**Deployment:** Admin interface
**AI Cost:** FREE

---

## 47. Upload Validation Widget
**File:** `templates/admin/upload_validation.html`
**Route:** `/admin/uploads`
**Status:** ✅ Content moderation tool

**What it does:**
Reviews and validates user-uploaded orchid images before public display.

**Features:**
- Pending uploads queue
- Image preview
- Metadata verification
- Approve/reject actions
- Bulk validation
- Quality scoring

**Access:** Admin only
**Deployment:** Admin tool
**AI Cost:** FREE (or AI-assisted validation if enabled)

---

## 48. Database Management Console
**File:** `templates/admin/database_console.html`
**Route:** `/admin/database`
**Status:** ✅ Admin database tool

**What it does:**
Provides admin interface for database operations including backups, schema viewing, and data export.

**Features:**
- Schema browser
- Row count statistics
- Export data (CSV/JSON)
- Backup trigger
- Index health check
- Query console (read-only)

**Access:** Admin only
**Deployment:** Admin tool
**AI Cost:** FREE

---

## 49. User Management Widget
**File:** `templates/admin/users.html`
**Route:** `/admin/users`
**Status:** ✅ User administration

**What it does:**
Manages user accounts, permissions, and activity monitoring.

**Features:**
- User list with search
- Role assignment
- Account suspension
- Activity logs
- Bulk user operations
- Password reset

**Access:** Admin only
**Database Table:** `user` (Flask-Login)
**Deployment:** Admin interface
**AI Cost:** FREE

---

## 50. Bug Report System Widget
**File:** `bug_report_system.py`, templates in `templates/widgets/`
**Route:** `/widgets/bug-report/`
**Status:** ✅ User feedback tool

**What it does:**
Allows users to submit bug reports with screenshots and automatic context capture.

**Features:**
- Bug report form
- Screenshot upload
- Browser/OS detection
- Priority tagging
- Admin notification
- Status tracking

**Database Table:** `bug_reports`
**Deployment:** Site-wide widget (footer or help menu)
**AI Cost:** FREE

---

## 51. System Monitor Widget
**File:** `comprehensive_system_monitor.py`
**Route:** `/admin/system-monitor`
**Status:** ✅ Real-time monitoring

**What it does:**
Real-time system performance monitoring including CPU, memory, database connections, and API quotas.

**Features:**
- CPU/Memory graphs
- Database connection pool status
- API quota tracking
- Error rate monitoring
- Performance alerts
- Historical data (30 days)

**Database:** `monitoring_data.db` (SQLite)
**Access:** Admin only
**Deployment:** Admin dashboard
**AI Cost:** FREE

---

## 52. Widget Health Dashboard
**File:** `master_ai_widget_manager.py`
**Route:** `/admin/widget-health`
**Status:** ✅ AI widget monitoring

**What it does:**
Monitors health and performance of all platform widgets with AI-powered recommendations.

**Features:**
- Widget status indicators
- Performance metrics
- Error tracking
- AI improvement suggestions
- Daily automated reports
- Historical analytics

**Database:** `ai_widget_manager.db` (SQLite)
**AI Usage:** AI analyzes widget performance data
**Access:** Admin only
**Deployment:** Admin dashboard
**AI Cost:** Minimal (daily report generation)

---

## 53. API Key Manager Widget
**File:** `templates/admin/api_keys.html`
**Route:** `/admin/api-keys`
**Status:** ✅ Credential management

**What it does:**
Manages external API keys with usage tracking and quota monitoring.

**Features:**
- Key entry/rotation
- Usage statistics
- Quota tracking
- Cost estimation
- Key expiration alerts
- Secure storage verification

**Access:** Admin only
**Security:** Keys stored in environment variables only
**Deployment:** Admin interface
**AI Cost:** FREE

---

## 54. Batch Taxonomy Restore Tool
**File:** `batch_taxonomy_restore.py`
**Route:** `/admin/taxonomy-restore` (likely)
**Status:** ✅ Database recovery tool

**What it does:**
Restores orchid taxonomy data from backups or CSV files with conflict resolution.

**Features:**
- CSV/JSON import
- Duplicate detection
- Conflict resolution options
- Dry-run mode
- Progress tracking
- Rollback capability

**Access:** Admin only
**Database Table:** `orchid_taxonomy`
**Deployment:** Admin maintenance tool
**AI Cost:** FREE

---

## 55. Data Enrichment Queue Manager
**File:** `autonomous_pipeline_worker.py`
**Route:** `/admin/enrichment-queue`
**Status:** ✅ Background job monitor

**What it does:**
Manages and monitors automated data enrichment jobs (GBIF, EOL, AI analysis).

**Features:**
- Job queue status
- Progress monitoring
- Pause/resume controls
- Priority adjustment
- Error log viewer
- Performance statistics

**Access:** Admin only
**Workers:** GBIF, EOL enrichment scripts
**Deployment:** Admin dashboard
**AI Cost:** Depends on job type

---

## 56. Log Viewer Widget
**File:** Component in admin dashboard
**Route:** `/admin/logs`
**Status:** ✅ System logs viewer

**What it does:**
Displays application logs with filtering, search, and download capabilities.

**Features:**
- Real-time log streaming
- Log level filtering
- Search by keyword
- Date range selection
- Download logs
- Error highlighting

**Access:** Admin only
**Log Source:** Application logs, worker logs
**Deployment:** Admin tool
**AI Cost:** FREE

---

## 57. Backup & Restore Widget
**File:** Admin utilities
**Route:** `/admin/backup`
**Status:** ✅ Data protection

**What it does:**
Creates and manages database backups with one-click restore functionality.

**Features:**
- One-click backup
- Automated scheduling
- Backup verification
- Restore preview
- Point-in-time recovery
- Cloud storage integration

**Access:** Admin only
**Database:** PostgreSQL dumps
**Deployment:** Admin maintenance
**AI Cost:** FREE

---

## 58. Health Check Endpoint
**File:** Routes in `routes.py`
**Route:** `/healthz`
**Status:** ✅ Production monitoring

**What it does:**
Lightweight health check endpoint for Render.com and uptime monitoring services.

**Features:**
- Instant response (no DB/AI calls)
- HTTP 200 OK status
- Minimal resource usage
- No authentication required
- Always available

**Purpose:** Render.com health checks, uptime monitoring
**Response:** `{"status": "healthy"}`
**AI Cost:** FREE
**Deployment:** Critical production endpoint

---

## 59. Feature Flag Manager
**File:** `app/settings.py`
**Route:** `/admin/feature-flags` (potential)
**Status:** ✅ Configuration management

**What it does:**
Manages platform feature flags including the critical AI kill-switch.

**Feature Flags:**
- `ORCHID_AI_ENABLED` - Master AI kill-switch (default: false)
- Others as needed

**Features:**
- Toggle features on/off
- Environment variable integration
- Restart notification
- Flag documentation
- Historical changes

**Access:** Admin or environment variable
**Deployment:** Admin configuration
**AI Cost:** FREE

---

## 60. Analytics Dashboard
**File:** Admin analytics components
**Route:** `/admin/analytics`
**Status:** ⚠️ Partial implementation

**What it does:**
Displays platform usage analytics including page views, widget usage, and user engagement.

**Features:**
- Traffic statistics
- Widget popularity metrics
- User engagement trends
- Geographic distribution
- Search analytics
- Export reports

**Access:** Admin only
**Data Source:** Application logs, database
**Deployment:** Admin dashboard
**AI Cost:** FREE

---

**End of Part 4**
Next: Part 5 - Embeddable & Integration Widgets (Final)
