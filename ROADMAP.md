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
4. **Currency Settings Consistency**
   - Make added currencies available in invoice forms and persist default currency changes reliably.
5. **Migration Hygiene**
   - Add a baseline Alembic revision and ensure existing databases are stamped correctly for future schema upgrades.
6. **Side-effect Cleanup**
   - Move overdue invoice status updates out of dashboard page loads and into an explicit command, job, or service.

---

## 🚀 Phase 1: Visual & Intelligence Tracking

1. **Interactive Dashboard 📊**
   - Integrate Chart.js for visual revenue tracking, income vs. month, and client breakdowns.
2. **Business Analytics**
   - Detailed financial reports and tax summaries for end-of-year accounting.
3. **Enhanced Search & Sorting**
   - Advanced filtering for invoice lists (by status, date range, or client).

## ✨ Phase 2: Communication & Convenience

1. **Automated Payment Reminders ⏰**
   - Configurable "Gentle Nudge" system to automatically email clients 3 days after a due date.
2. **Branded HTML Email Templates ✉️**
   - Move from plain-text emails to pixel-perfect, branded HTML templates that match your business style.
3. **Online Payments Integration 💸**
   - Support for Stripe and PayPal for direct-from-invoice payment processing.

## 🌐 Phase 3: The "SaaS" Leap

1. **Client Portal Lite 🔗**
   - Generate unique, secure links for invoices so clients can view them in-browser without downloading a PDF first.
2. **View Tracking 👁️**
   - Know exactly when a client has opened or viewed their invoice link.
3. **Multi-user Support 👥**
   - Role-based access control (RBAC) for teams (Admin, Accountant, Sales).

---

> [!NOTE]
> Have a feature request or want to contribute? Feel free to [open an issue](https://github.com/chrisnov-it/chrisnov-invoice/issues)!
