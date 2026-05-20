from flask import Flask, redirect, url_for, flash
import os
from flask_session import Session
from config import Config
from app.models import Setting, Currency, User
from app.extensions import db, mail, migrate, csrf, login_manager
from flask_babel import Babel, gettext, ngettext, lazy_gettext, _
from flask import request, session, g
from flask_wtf.csrf import CSRFError
from flask_login import current_user

USER_SETTING_KEYS = [
    'BUSINESS_NAME',
    'BUSINESS_ADDRESS',
    'BUSINESS_PHONE',
    'BUSINESS_EMAIL',
    'BUSINESS_WEBSITE',
    'TAX_RATE',
    'DEFAULT_CURRENCY',
    'LOGO_FILENAME',
    'MAIL_SERVER',
    'MAIL_PORT',
    'MAIL_USE_TLS',
    'MAIL_USE_SSL',
    'MAIL_USERNAME',
    'MAIL_PASSWORD',
    'MAIL_DEFAULT_SENDER',
    'PDF_TEMPLATE',
    'PDF_HEADER_COLOR',
    'PDF_ACCENT_COLOR',
    'PDF_LOGO_POSITION',
    'PDF_FOOTER_TEXT',
    'PDF_SHOW_LOGO',
]

def format_currency_filter(amount, currency_code, app):
    """Jinja2 filter to format currency with thousand separators"""
    with app.app_context():
        currency = Currency.query.filter_by(code=currency_code).first()
        if not currency:
            default_currency_code = app.config.get('DEFAULT_CURRENCY', 'IDR')
            currency = Currency.query.filter_by(code=default_currency_code).first()

        if not currency:
            # Fallback if no currency is found at all
            symbol = ''
            position = 'before'
            thousands_separator = ','
            decimal_separator = '.'
        else:
            symbol = currency.symbol
            # These attributes need to be added to the Currency model if they are to be dynamic
            position = 'before' 
            thousands_separator = '.'
            decimal_separator = ','

        # Format the amount with thousands separator
        if amount is None:
            amount = 0
            
        if amount == int(amount):
            # If amount is a whole number, format without decimal places
            formatted_amount = f"{int(amount):,}".replace(',', thousands_separator)
        else:
            # Format with 2 decimal places and thousands separator
            formatted_amount = f"{amount:,.2f}".replace(',', 'THOUSANDS_PLACEHOLDER').replace('.', decimal_separator).replace('THOUSANDS_PLACEHOLDER', thousands_separator)

        if position == 'before':
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.validate_production_secrets()
    
    # Initialize extensions
    # Initialize session first to ensure it's available for Babel
    sess = Session()
    sess.init_app(app)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('Your form session expired or was invalid. Please try again.', 'error')
        return redirect(request.referrer or url_for('dashboard.index'))

    def coerce_setting_value(value):
        if value is None:
            return None
        if value.isdigit():
            return int(value)
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        return value

    @app.before_request
    def require_login():
        allowed_endpoints = {
            'auth.login',
            'auth.register',
            'static',
            'set_language',
        }
        if request.endpoint in allowed_endpoints or request.endpoint is None:
            return None
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.full_path if request.query_string else request.path))
        return None

    def load_global_settings():
        for key in USER_SETTING_KEYS:
            if hasattr(config_class, key):
                app.config[key] = getattr(config_class, key)

        try:
            for setting in Setting.query.filter(~Setting.key.startswith('user:')).all():
                app.config[setting.key] = coerce_setting_value(setting.value)
        except Exception as e:
            # This can happen if the database is not yet initialized.
            print(f"Could not load global settings from DB: {e}")

    @app.before_request
    def load_request_settings():
        load_global_settings()
        if current_user.is_authenticated:
            prefix = f'user:{current_user.id}:'
            for setting in Setting.query.filter(Setting.key.startswith(prefix)).all():
                app.config[setting.key.removeprefix(prefix)] = coerce_setting_value(setting.value)
        return None
    
    # Language selection function
    def get_locale():
        # Check if user has selected a language in session
        if session.get('language'):
            return session.get('language')
            
        # Check Accept-Language header
        return request.accept_languages.best_match(['en', 'id']) or 'en'
    
    # Initialize Babel for internationalization
    babel = Babel(app, locale_selector=get_locale)
    
    # Add language selection route
    @app.route('/set_language/<lang>', methods=['POST'])
    def set_language(lang):
        if lang not in ['en', 'id']:
            flash('Invalid language selected.', 'error')
            return redirect(request.referrer or url_for('dashboard.index'))
        session['language'] = lang
        session.modified = True
        return ('', 204)

    # The database initialization logic has been moved to a separate CLI command.
    # This prevents the app from trying to re-create tables on every startup.

    def load_settings_from_db(app):
        try:
            for setting in Setting.query.all():
                # Handle type conversion
                if not setting.key.startswith('user:'):
                    app.config[setting.key] = coerce_setting_value(setting.value)
        except Exception as e:
            # This can happen if the database is not yet initialized
            print(f"Could not load settings from DB: {e}")
    # Load settings from DB at startup
    with app.app_context():
        load_global_settings()

    # Add currency formatting filter
    @app.template_filter('format_currency')
    def format_currency(amount, currency_code):
        return format_currency_filter(amount, currency_code, app)

    # Make config and locale available in all templates
    @app.context_processor
    def inject_global_vars():
        return dict(
            config=app.config,
            current_locale=get_locale(),
            current_user=current_user
        )
    
    # Register blueprints
    from app.routes import auth, dashboard, clients, invoices, settings, recurring_invoices

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(clients.bp)
    app.register_blueprint(invoices.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(recurring_invoices.bp)
    
    return app
