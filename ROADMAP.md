# 🗺️ Project Roadmap: The Future of Chrisnov Invoice

Welcome to the future of **Chrisnov Invoice**! We are committed to making this the most elegant and efficient invoicing tool for freelancers and small businesses. Below is our vision for upcoming versions.

## ✅ Completed (v1.3.0 "Secure SaaS Foundation")

- [x] **User Accounts**: Register, login, logout, password hashing, and route protection.
- [x] **Core Per-user Ownership**: Scope clients, invoices, recurring invoices, and user settings to each logged-in account.
- [x] **CSRF Protection**: Protect all mutating forms and language switching requests with CSRF tokens.
- [x] **Production Deploy Workflow**: Deploy `main` to the VPS through GitHub Actions with backup, dependency install, schema initialization, restart, and health check.
- [x] **Recurring Invoice XSS Fix**: Safely render recurring invoice items in the edit form.
- [x] **Backup & Restore Hardening**: Restrict full database export/restore to the configured database owner and validate SQLite backups before restore.
- [x] **Production Secret Management**: Require a strong production `SECRET_KEY` and enable stricter session cookie settings.
- [x] **Dependency Security Patch**: Upgrade vulnerable Flask and python-dotenv versions.
- [x] **Auth Rate Limiting & Registration Toggle**: Throttle auth attempts and allow public signup to be disabled by environment.
- [x] **List Pagination**: Paginate invoice, client, and recurring invoice indexes for larger accounts.
- [x] **Per-user Logo Storage**: Prevent users from overwriting one shared logo file.
- [x] **Global Currency Guardrails**: Keep default currency per-user while limiting global currency add/delete actions to the database owner.
- [x] **Overdue Status Job**: Move overdue invoice updates out of dashboard page loads into a CLI command.
- [x] **PostgreSQL-ready Configuration**: Support `DATABASE_URL` for a future database migration without changing the default SQLite setup.
- [x] **App Version Display**: Show the current version in the app footer.

## ✅ Completed (v1.2.0 "Standalone & Secure")

- [x] **Desktop Mode Support**: Standalone Windows executable (.exe) using `flaskwebgui` and `PyInstaller`.
- [x] **Database Backup & Restore**: Built-in system to export/import the entire database from the Settings menu.
- [x] **Refined i18n System**: Official `pybabel` implementation for stable and standardized translations.

## ✅ Completed (v1.1.0 "Elegant & Global")

- [x] **Internationalization**: Full Bahasa Indonesia and English support with session persistence.
- [x] **App Branding**: Logo support in sidebar and "Elegant" PDF template.
- [x] **Template Redesign**: Refined "Modern", "Minimal", and "Elegant" (Serif) styles.
- [x] **Editable Invoice Numbers**: Manual overrides for numbering.

---

## 🔐 Phase 0: Security & SaaS Readiness

1. **Authentication Hardening**
   - Add password reset, optional email verification, stronger production session settings, and account management screens.
2. **Backup & Restore Hardening**
   - Move toward user-scoped export/restore so hosted deployments never expose another user's records.
3. **Money Precision Upgrade**
   - Replace floating-point invoice amounts with `Decimal`/`Numeric` or integer minor units to avoid rounding drift.
4. **Migration Hygiene**
   - Add a baseline Alembic revision and ensure existing databases are stamped correctly for future schema upgrades.

---

## 🚀 Phase 1: Visual & Intelligence Tracking

1. **Interactive Dashboard 📊**
   - Integrate Chart.js for visual revenue tracking, income vs. month, and client breakdowns.
2. **Business Analytics**
   - Detailed financial reports and tax summaries for end-of-year accounting.
3. **Enhanced Search & Sorting**
   - Advanced filtering for invoice lists (by status, date range, or client).

## ✅ Completed (v1.4.0 "Payment Ready")

- [x] **Online Payments Integration (Midtrans) 💸**
  - Generate Snap payment links from any unpaid invoice.
  - Supports QRIS, Virtual Account, Credit Card, and more.
  - Auto-update invoice status to "Paid" on payment confirmation.
  - Midtrans webhook for real-time status updates.

## ✅ Completed (v1.5.0 "Multi-Business Ready")

- [x] **Customizable Item Unit**: Add a `unit` column (hours, days, pieces, project, flat, months, weeks, km, set) to invoice and recurring invoice items.
- [x] **Dynamic Quantity Label**: Rename the quantity column ("Qty" → "Hours", "Days", etc.) via the `ITEM_QTY_LABEL` setting.
- [x] **Unit Column Toggle on PDF**: Show or hide the unit column on generated invoices via `PDF_SHOW_UNIT`.
- [x] **Safe Schema Migration**: `init-db` adds missing columns automatically, preventing "no such column" deploy errors.
- [x] **PDF Text Wrapping Fix**: Long descriptions wrap correctly in the Professional template.

---

## 🔧 Phase 0.5: Multi-Business Readiness (Next)

Targeted quick wins so the app suits any profession (lawyers, consultants, contractors), not just IT services:

1. **Customizable Tax Name**
   - Add a `tax_name` field (e.g. "PPN", "PPh 23", "VAT", "Service Tax") per invoice, with a default in settings.
2. **Invoice Number Prefix**
   - Configurable `INVOICE_PREFIX` so numbers become `LA-2026-0001`, `CONS-2026-0001`, etc.
3. **Payment Terms**
   - Dropdown (Due on Receipt, Net 7/15/30/60) that auto-computes `due_date` from `issue_date`.
4. **Recurring Scheduler**
   - Run the existing `generate-recurring` CLI on a cron / systemd timer so retainer and subscription invoices generate automatically.

## 🔐 Phase 0: Security & SaaS Readiness

1. **Automated Payment Reminders ⏰**
   - Configurable "Gentle Nudge" system to automatically email clients 3 days after a due date.
2. **Branded HTML Email Templates ✉️**
   - Move from plain-text emails to pixel-perfect, branded HTML templates that match your business style.

## 🌐 Phase 3: The "SaaS" Leap

1. **Client Portal Lite 🔗**
   - Generate unique, secure links for invoices so clients can view them in-browser without downloading a PDF first.
2. **View Tracking 👁️**
   - Know exactly when a client has opened or viewed their invoice link.
3. **Multi-user Support 👥**
   - Role-based access control (RBAC) for teams (Admin, Accountant, Sales).

## 💡 Phase 4: Data Integrity & Scale

1. **Money Precision Upgrade**
   - Replace floating-point invoice amounts with `Decimal`/`Numeric` or integer minor units to avoid rounding drift (carried over from the original Phase 0 plan).
2. **Migration Hygiene**
   - Add a baseline Alembic revision and ensure existing databases are stamped correctly for future schema upgrades.

---

> [!NOTE]
> Have a feature request or want to contribute? Feel free to [open an issue](https://github.com/chrisnov-it/chrisnov-invoice/issues)!
