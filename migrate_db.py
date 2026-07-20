"""
Migration script to copy data from SQLite to MySQL.
Usage:
1. Ensure the new MySQL database is created on your VPS.
2. Update the TARGET_DATABASE_URL in this file (or run with environment variable set).
3. Run: python migrate_db.py
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import create_app
from app.extensions import db
from app.models import (
    User, Client, Invoice, InvoiceItem, RecurringInvoice, RecurringInvoiceItem, Setting, Currency
)

# Source DB (SQLite) - the one currently configured in the app if you haven't changed .env yet
SOURCE_DATABASE_URL = 'sqlite:///instance/chrisnov_invoice.db'

# Target DB (MySQL/MariaDB) - change this to match your VPS MySQL credentials
TARGET_DATABASE_URL = os.environ.get('TARGET_DATABASE_URL', 'mysql+pymysql://username:password@localhost/chrisnov_invoice')

def migrate_data():
    app = create_app()
    with app.app_context():
        print(f"Connecting to source (SQLite): {SOURCE_DATABASE_URL}")
        source_engine = create_engine(SOURCE_DATABASE_URL)
        SourceSession = sessionmaker(bind=source_engine)
        source_session = SourceSession()
        
        print(f"Connecting to target (MySQL): {TARGET_DATABASE_URL}")
        target_engine = create_engine(TARGET_DATABASE_URL)
        
        # We need to recreate tables in target
        print("Creating tables in target database...")
        db.metadata.create_all(target_engine)
        
        TargetSession = sessionmaker(bind=target_engine)
        target_session = TargetSession()
        
        models_to_migrate = [
            User,
            Client,
            Invoice,
            InvoiceItem,
            RecurringInvoice,
            RecurringInvoiceItem,
            Setting,
            Currency
        ]
        
        try:
            for model in models_to_migrate:
                table_name = model.__tablename__
                print(f"Migrating {table_name}...")
                
                # Fetch all from source
                rows = source_session.query(model).all()
                print(f" Found {len(rows)} records.")
                
                for row in rows:
                    # Create a new instance for target, making sure we copy all column values
                    target_session.merge(row)
                
                # Commit after each table
                target_session.commit()
                print(f" Migrated {table_name} successfully.")
                
            print("\nMigration completed successfully!")
            
        except Exception as e:
            print(f"\nError during migration: {e}")
            target_session.rollback()
            raise
        finally:
            source_session.close()
            target_session.close()

if __name__ == '__main__':
    # Protection against accidental execution without config
    if 'username:password' in TARGET_DATABASE_URL:
        print("ERROR: Please edit TARGET_DATABASE_URL with your actual MySQL credentials.")
        exit(1)
        
    migrate_data()
