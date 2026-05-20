import os

class Config:
    """Base configuration"""
    APP_VERSION = "1.3.0"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///chrisnov_invoice.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_ADMIN_USER_ID = int(os.environ.get('DATABASE_ADMIN_USER_ID', '1'))

    # File Uploads
    UPLOAD_FOLDER = 'app/static/images'
    LOGO_FILENAME = None
    
    # Business Information
    BUSINESS_NAME = "Chrisnov IT Solutions"
    BUSINESS_ADDRESS = "Jl. Soekarno No. 24, Ruteng, Flores, Indonesia"
    BUSINESS_PHONE = "+62859-5536-2932"
    BUSINESS_EMAIL = "contact@chrisnov.com"
    BUSINESS_WEBSITE = "https://chrisnov.com"
    
    # Invoice Settings
    TAX_RATE = 0.11  # 11% tax
    DEFAULT_CURRENCY = "IDR"

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

    # Email Settings (for local email sending)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "noreply@chrisnov-invoice.local"
