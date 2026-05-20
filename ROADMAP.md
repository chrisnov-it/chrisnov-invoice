# 🗺️ Project Roadmap: The Future of Chrisnov Invoice

Welcome to the future of **Chrisnov Invoice**! We are committed to making this the most elegant and efficient invoicing tool for freelancers and small businesses. Below is our vision for upcoming versions.

## ✅ Completed (v1.2.0 "Standalone & Secure")

- [x] **Desktop Mode Support**: Standalone Windows executable (.exe) using `flaskwebgui` and `PyInstaller`.
- [x] **Database Backup & Restore**: Built-in system to export/import the entire database from the Settings menu.
- [x] **Refined i18n System**: Official `pybabel` implementation for stable and standardized translations.
- [x] **CSRF Protection**: Protect all mutating forms and language switching requests with CSRF tokens.
- [x] **Basic User Authentication**: Register, login, logout, password hashing, and route protection.
- [x] **Core Per-user Data Ownership**: Scope clients, invoices, recurring invoices, and user settings to the logged-in account.

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
   - Validate uploaded SQLite backups before restore, check required tables, run integrity checks, and avoid replacing the active database blindly.
   - Move toward user-scoped export/restore so hosted deployments never expose another user's records.
3. **Recurring Invoice XSS Fix**
   - Replace unsafe JavaScript interpolation in recurring invoice edit forms with JSON-safe template output.
4. **Money Precision Upgrade**
   - Replace floating-point invoice amounts with `Decimal`/`Numeric` or integer minor units to avoid rounding drift.
5. **Currency Settings Consistency**
   - Make added currencies available in invoice forms and persist default currency changes reliably.
6. **Migration Hygiene**
   - Add a baseline Alembic revision and ensure existing databases are stamped correctly for future schema upgrades.
7. **Production Secret Management**
   - Require a real `SECRET_KEY` in hosted deployments and avoid falling back to the development secret outside local use.
8. **Side-effect Cleanup**
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
