# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2026-05-20

### Added
- **User Accounts**: Register, login, logout, password hashing, and route protection.
- **Core Per-user Data Ownership**: Scope clients, invoices, recurring invoices, and user settings to the logged-in account.
- **CSRF Protection**: Protect all mutating forms and language switching requests with CSRF tokens.
- **Production Deploy Workflow**: Deploy `main` to the VPS through GitHub Actions with database backup, dependency install, schema initialization, service restart, and health check.

### Fixed
- **Recurring Invoice XSS**: Safely render recurring invoice item data in the edit form without injecting user content into HTML.

### Changed
- **Repository Hygiene**: Ignore local root screenshots and internal development notes; keep release history centralized in `CHANGELOG.md`.
- **Branch Naming**: Move deployment workflow from `master` to `main`.
- **App Versioning**: Add a single `APP_VERSION` config value and show the current version in the app footer.

## [1.2.0] - 2026-01-06

### Added
- **Native Windows Support**: Added desktop mode through `run_desktop.py` using `flaskwebgui`.
- **Standalone Windows Build**: Added `build_exe.py` to bundle the app into `ChrisnovInvoice.exe`.
- **Backup & Restore**: New settings section to export and import database backups (`.db` files).
- **Portable Usage Improvements**: Optimized project structure for easier local and desktop use.
- New dependencies: `flaskwebgui`, `pyinstaller`.

### Changed
- **Release Packaging**: Added support for publishing `ChrisnovInvoice-Windows-v1.2.0.zip` for non-technical Windows users.
- **Project Visibility**: Updated `.gitignore` to ensure essential documentation and translation sources are tracked.

### Fixed
- **Translation System**: Standardized translation compilation using official `pybabel`.
- **Corrupt MO Files**: Resolved issue where manual binary generation caused compatibility errors in Python 3.14.
- **Backup Translation Coverage**: Fully translated the Backup & Restore interface into Bahasa Indonesia.

## [1.1.0] - 2025-12-30 "Elegant & Global Update"

### Added
- **Internationalization (i18n)**: 
  - Added full support for Bahasa Indonesia.
  - Implemented persistent language switching (stores preference in session).
  - Added language switcher dropdown to the top navigation bar.
- **App Branding**:
  - Implemented Logo display in the App Sidebar (Dashboard).
  - Logo persistence: Uploaded logos are now correctly saved to the database.
- **Elegant PDF Template**:
  - Redesigned "Elegant" template to a classic, serif-based layout.
  - Added centered logo support to the "Elegant" template.

### Improved
- **Settings UI**:
  - Refined PDF Template previews in Settings to accurately reflect "Modern", "Classic/Elegant", and "Professional" layouts.
  - Added "Details" section preview for the Elegant template.
  - Sidebar header spacing: Added padding to "Chrisnov IT Solutions" label to improve readability.
- **Developer Experience**:
  - Moved `translations` directory to standard `app/translations` location for better compatibility.

### Fixed
- **Language Switcher**: Fixed issue where the app would revert to English due to missing session persistence or incorrect translation directory.
- **Logo Display**: Fixed 404 errors for logo images by standardizing file storage to `logo.png`.
- **PDF Generation**: Fixed various layout overlaps in "Modern" and "Professional" templates.
