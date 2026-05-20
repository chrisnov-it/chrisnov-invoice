from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.models import Setting, Currency
from app import db
from app.services.backup_service import BackupService
from flask import send_file
from flask_login import current_user

bp = Blueprint('settings', __name__, url_prefix='/settings')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def user_logo_directory():
    return os.path.join(current_app.static_folder, 'uploads', 'users', str(current_user.id))

def user_logo_filename(original_filename):
    extension = secure_filename(original_filename).rsplit('.', 1)[1].lower()
    return f'logo.{extension}'

def user_logo_setting_value(filename):
    return f'uploads/users/{current_user.id}/{filename}'

def remove_current_user_logo():
    logo_filename = current_app.config.get('LOGO_FILENAME')
    if not logo_filename:
        return False

    if '/' in logo_filename or '\\' in logo_filename:
        logo_path = os.path.join(current_app.static_folder, *logo_filename.replace('\\', '/').split('/'))
    else:
        logo_path = os.path.join(current_app.static_folder, 'images', 'logo.png')

    if os.path.exists(logo_path):
        os.remove(logo_path)
        return True
    return False

def update_setting(key, value):
    """Update a setting in the database."""
    setting_key = f'user:{current_user.id}:{key}'
    setting = db.session.get(Setting, setting_key)
    if setting:
        setting.value = value
    else:
        setting = Setting(key=setting_key, value=value)
        db.session.add(setting)

def get_setting(key, default=None):
    setting_key = f'user:{current_user.id}:{key}'
    setting = db.session.get(Setting, setting_key)
    return setting.value if setting else default

def current_user_can_manage_database():
    """Only the configured database owner can export or restore the full DB."""
    return current_user.id == current_app.config.get('DATABASE_ADMIN_USER_ID', 1)

def require_database_admin():
    if not current_user_can_manage_database():
        abort(403)

@bp.route('/')
def index():
    """Display settings page"""
    return render_template(
        'settings/index.html',
        can_manage_database=current_user_can_manage_database()
    )

@bp.route('/currencies', methods=['GET', 'POST'])
def currencies():
    """Manage currency settings"""
    if request.method == 'POST':
        if 'add_currency' in request.form:
            require_database_admin()
            code = request.form.get('code')
            name = request.form.get('name')
            symbol = request.form.get('symbol')

            if not all([code, name, symbol]):
                flash('All currency fields are required.', 'error')
            elif len(code) != 3:
                flash('Currency code must be 3 characters long.', 'error')
            elif Currency.query.filter_by(code=code).first():
                flash(f'Currency with code {code} already exists.', 'error')
            else:
                new_currency = Currency(code=code.upper(), name=name, symbol=symbol)
                db.session.add(new_currency)
                db.session.commit()
                flash(f'Currency {name} ({code}) added successfully!', 'success')

        elif 'delete_currency' in request.form:
            require_database_admin()
            currency_id = request.form.get('currency_id')
            currency_to_delete = Currency.query.get(currency_id)
            if currency_to_delete:
                if currency_to_delete.code == current_app.config.get('DEFAULT_CURRENCY'):
                    flash('Cannot delete the default currency.', 'error')
                else:
                    db.session.delete(currency_to_delete)
                    db.session.commit()
                    flash(f'Currency {currency_to_delete.name} deleted successfully!', 'success')
            else:
                flash('Currency not found.', 'error')

        elif 'default_currency' in request.form:
            default_currency = request.form.get('default_currency')
            if Currency.query.filter_by(code=default_currency).first():
                update_setting('DEFAULT_CURRENCY', default_currency)
                current_app.config['DEFAULT_CURRENCY'] = default_currency
                db.session.commit()
                flash(f'Default currency updated to {default_currency}', 'success')
            else:
                flash('Invalid currency selected', 'error')

        return redirect(url_for('settings.currencies'))

    currencies = Currency.query.all()
    return render_template(
        'settings/currencies.html',
        currencies=currencies,
        can_manage_currencies=current_user_can_manage_database()
    )

@bp.route('/email', methods=['GET', 'POST'])
def email():
    """Manage email settings"""
    if request.method == 'POST':
        try:
            mail_port = int(request.form.get('mail_port', '1025'))
            if not (1 <= mail_port <= 65535):
                raise ValueError
        except (TypeError, ValueError):
            flash('Mail port must be a number between 1 and 65535.', 'error')
            return redirect(url_for('settings.email'))

        mail_password = request.form.get('mail_password', '')
        if mail_password == '':
            mail_password = get_setting('MAIL_PASSWORD', current_app.config.get('MAIL_PASSWORD') or '')

        # Update email settings
        settings_to_update = {
            'MAIL_SERVER': request.form.get('mail_server', 'localhost'),
            'MAIL_PORT': mail_port,
            'MAIL_USE_TLS': str(request.form.get('mail_use_tls') == 'on'),
            'MAIL_USE_SSL': str(request.form.get('mail_use_ssl') == 'on' and not (request.form.get('mail_use_tls') == 'on')),
            'MAIL_USERNAME': request.form.get('mail_username', ''),
            'MAIL_PASSWORD': mail_password,
            'MAIL_DEFAULT_SENDER': request.form.get('mail_default_sender', 'noreply@chrisnov-invoice.local')
        }

        for key, value in settings_to_update.items():
            update_setting(key, str(value))
            if key in ['MAIL_USE_TLS', 'MAIL_USE_SSL']:
                current_app.config[key] = value.lower() == 'true'
            else:
                current_app.config[key] = value

        db.session.commit() # Commit changes to the database

        flash('Email settings updated successfully!', 'success')
        return redirect(url_for('settings.email'))

    return render_template('settings/email.html')

@bp.route('/business', methods=['GET', 'POST'])
def business():
    """Manage business information settings"""
    if request.method == 'POST':
        if 'remove_logo' in request.form:
            if remove_current_user_logo():
                current_app.config['LOGO_FILENAME'] = None
                update_setting('LOGO_FILENAME', '')
                flash('Logo removed successfully!', 'success')
            else:
                flash('No logo to remove.', 'info')
            return redirect(url_for('settings.business'))

        # Handle logo upload
        if 'business_logo' in request.files:
            file = request.files['business_logo']
            if file and allowed_file(file.filename):
                remove_current_user_logo()
                logo_dir = user_logo_directory()
                os.makedirs(logo_dir, exist_ok=True)
                filename = user_logo_filename(file.filename)
                logo_setting = user_logo_setting_value(filename)
                current_app.config['LOGO_FILENAME'] = logo_setting
                update_setting('LOGO_FILENAME', logo_setting)
                file.save(os.path.join(logo_dir, filename))

        # Update business information
        business_name = request.form.get('business_name', '').strip()
        business_email = request.form.get('business_email', '').strip()
        business_phone = request.form.get('business_phone', '').strip()
        business_website = request.form.get('business_website', '').strip()
        business_address = request.form.get('business_address', '').strip()

        # Validate required fields
        if not business_name or not business_email or not business_address:
            flash('Business name, email, and address are required fields.', 'error')
            return redirect(url_for('settings.business'))

        # Update tax rate and currency
        try:
            tax_rate = float(request.form.get('tax_rate', '10')) / 100
            if not (0 <= tax_rate <= 1):
                raise ValueError("Tax rate must be between 0 and 100")
        except (ValueError, TypeError):
            flash('Invalid tax rate. Please enter a number between 0 and 100.', 'error')
            return redirect(url_for('settings.business'))

        default_currency = request.form.get('default_currency', 'USD')
        if not Currency.query.filter_by(code=default_currency).first():
            flash('Invalid currency selected.', 'error')
            return redirect(url_for('settings.business'))

        # Create a dictionary of settings to update
        settings_to_update = {
            'BUSINESS_NAME': business_name,
            'BUSINESS_EMAIL': business_email,
            'BUSINESS_PHONE': business_phone,
            'BUSINESS_WEBSITE': business_website,
            'BUSINESS_ADDRESS': business_address,
            'TAX_RATE': str(tax_rate),
            'DEFAULT_CURRENCY': default_currency
        }

        # Update database and config
        for key, value in settings_to_update.items():
            update_setting(key, value)
            if key == 'TAX_RATE':
                current_app.config[key] = float(value)
            else:
                current_app.config[key] = value
        
        db.session.commit()

        flash('Business information updated successfully!', 'success')
        return redirect(url_for('settings.business'))

    return render_template('settings/business.html')


@bp.route('/email/test', methods=['POST'])
def test_email():
    """Send a test email to verify configuration"""
    test_email = request.form.get('test_email', '').strip()

    if not test_email:
        flash('Please provide a test email address.', 'error')
        return redirect(url_for('settings.email'))

    try:
        from flask_mail import Message
        from app import mail

        msg = Message(
            subject='Test Email from Invoice Manager',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[test_email],
            body=f"""Hello!

This is a test email from your Invoice Manager application.

If you received this email, your SMTP configuration is working correctly!

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Invoice Manager
{current_app.config['BUSINESS_NAME']}
"""
        )

        mail.send(msg)
        flash(f'Test email sent successfully to {test_email}!', 'success')

    except Exception as e:
        flash(f'Failed to send test email: {str(e)}', 'error')

    return redirect(url_for('settings.email'))

@bp.route('/pdf-templates', methods=['GET', 'POST'])
def pdf_templates():
    """Manage PDF template settings"""
    if request.method == 'POST':
        # Update PDF template settings
        pdf_template = request.form.get('pdf_template', 'professional')
        header_color = request.form.get('header_color', 'blue')
        accent_color = request.form.get('accent_color', 'blue')
        logo_position = request.form.get('logo_position', 'left')
        footer_text = request.form.get('footer_text', '').strip()
        show_logo = request.form.get('show_logo') == 'on'

        # Create a dictionary of settings to update
        settings_to_update = {
            'PDF_TEMPLATE': pdf_template,
            'PDF_HEADER_COLOR': header_color,
            'PDF_ACCENT_COLOR': accent_color,
            'PDF_LOGO_POSITION': logo_position,
            'PDF_FOOTER_TEXT': footer_text or 'Thank you for your business!',
            'PDF_SHOW_LOGO': str(show_logo)
        }

        # Update database and config
        for key, value in settings_to_update.items():
            update_setting(key, value)
            if key == 'PDF_SHOW_LOGO':
                current_app.config[key] = (value.lower() == 'true')
            else:
                current_app.config[key] = value
        
        db.session.commit()

        flash('PDF template settings updated successfully!', 'success')
        return redirect(url_for('settings.pdf_templates'))

    return render_template('settings/pdf_templates.html')

@bp.route('/backup', methods=['GET'])
def backup_index():
    """Display backup and restore options"""
    require_database_admin()
    return render_template('settings/backup.html')

@bp.route('/backup/export', methods=['GET'])
def export_db():
    """Download current database file"""
    require_database_admin()
    db_path = BackupService.get_db_path()
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        return send_file(
            db_path,
            as_attachment=True,
            download_name=f"chrisnov_invoice_backup_{timestamp}.db"
        )
    flash('Database file not found.', 'error')
    return redirect(url_for('settings.backup_index'))

@bp.route('/backup/import', methods=['POST'])
def import_db():
    """Restore database from uploaded file"""
    require_database_admin()
    if 'backup_file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('settings.backup_index'))
    
    file = request.files['backup_file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('settings.backup_index'))
    
    filename = secure_filename(file.filename)
    if file and filename.lower().endswith('.db'):
        # Save temp file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_path = os.path.join(current_app.instance_path, f'temp_restore_{current_user.id}_{timestamp}.db')
        file.save(temp_path)
        
        success, error = BackupService.restore_from_file(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if success:
            flash('Database restored successfully! Please restart the application if you encounter issues.', 'success')
        else:
            flash(f'Restore failed: {error}', 'error')
    else:
        flash('Invalid file format. Please upload a .db file.', 'error')
        
    return redirect(url_for('settings.backup_index'))

