import os

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

class Config:
    """Base configuration"""
    APP_VERSION = "1.5.0"
    APP_ENV = os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV', 'development')
    DEV_SECRET_KEY = 'dev-secret-key-change-in-production'
    SECRET_KEY = os.environ.get('SECRET_KEY') or DEV_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///chrisnov_invoice.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    DATABASE_ADMIN_USER_ID = int(os.environ.get('DATABASE_ADMIN_USER_ID', '1'))
    ALLOW_REGISTRATION = os.environ.get('ALLOW_REGISTRATION', 'true').lower() in ('1', 'true', 'yes', 'on')

    # File Uploads
    UPLOAD_FOLDER = 'app/static/images'
    LOGO_FILENAME = None
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per hour')
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH', '5 per minute')

    # Pagination
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', '25'))
    
    # Business Information
    BUSINESS_NAME = "Chrisnov IT Solutions"
    BUSINESS_ADDRESS = "Jl. Soekarno No. 24, Ruteng, Flores, Indonesia"
    BUSINESS_PHONE = "+62859-5536-2932"
    BUSINESS_EMAIL = "contact@chrisnov.com"
    BUSINESS_WEBSITE = "https://chrisnov.com"
    
    # Invoice Settings
    TAX_RATE = 0.11  # 11% tax
    DEFAULT_CURRENCY = "IDR"
    ITEM_QTY_LABEL = "Qty"
    UNITS = ['hours', 'days', 'pieces', 'project', 'flat', 'months', 'weeks', 'km', 'set']
    DEFAULT_UNIT = "pieces"

    # Supported Currencies
    SUPPORTED_CURRENCIES = {
        'IDR': {'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'position': 'before'},
        'USD': {'name': 'US Dollar', 'symbol': '$', 'position': 'before'},
        'EUR': {'name': 'Euro', 'symbol': '€', 'position': 'before'}
    }

    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'sessions'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = APP_ENV.lower() == 'production'
    WTF_CSRF_SSL_STRICT = APP_ENV.lower() == 'production'

    @classmethod
    def is_production(cls):
        return cls.APP_ENV.lower() == 'production'

    @classmethod
    def validate_production_secrets(cls):
        if not cls.is_production():
            return

        if not os.environ.get('SECRET_KEY') or cls.SECRET_KEY == cls.DEV_SECRET_KEY:
            raise RuntimeError('SECRET_KEY must be set to a strong value when APP_ENV=production.')

        if len(cls.SECRET_KEY) < 32:
            raise RuntimeError('SECRET_KEY must be at least 32 characters when APP_ENV=production.')

    # Midtrans Payment Gateway
    MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY', '')
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY', '')
    MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'

    # Email Settings (for local email sending)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "noreply@chrisnov-invoice.local"
