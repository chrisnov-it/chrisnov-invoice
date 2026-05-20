import os
import shutil
import sqlite3
from datetime import datetime
from flask import current_app
from app.extensions import db

class BackupService:
    REQUIRED_TABLES = {
        'users',
        'clients',
        'invoices',
        'invoice_items',
        'recurring_invoices',
        'recurring_invoice_items',
        'settings',
        'currencies',
    }

    REQUIRED_COLUMNS = {
        'users': {'id', 'email', 'password_hash'},
        'clients': {'id', 'user_id'},
        'invoices': {'id', 'user_id', 'client_id', 'invoice_number'},
        'invoice_items': {'id', 'invoice_id'},
        'recurring_invoices': {'id', 'user_id', 'client_id'},
        'recurring_invoice_items': {'id', 'recurring_invoice_id'},
        'settings': {'key', 'value'},
        'currencies': {'id', 'code', 'name', 'symbol'},
    }

    @staticmethod
    def get_db_path():
        """Get the absolute path to the SQLite database file."""
        # Config says 'sqlite:///chrisnov_invoice.db'
        # Usually this means it's in the instance folder if using Flask-SQLAlchemy correctly
        return os.path.join(current_app.instance_path, 'chrisnov_invoice.db')

    @staticmethod
    def create_backup_copy():
        """Create a timestamped backup copy and return its path."""
        db_path = BackupService.get_db_path()
        if not os.path.exists(db_path):
            return None, "Database file not found."

        backup_dir = os.path.join(current_app.instance_path, 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            shutil.copy2(db_path, backup_path)
            return backup_path, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def validate_backup_file(file_path):
        """Validate that a restore file is a usable Chrisnov Invoice SQLite DB."""
        if not os.path.exists(file_path):
            return False, "Backup file not found."

        if os.path.getsize(file_path) == 0:
            return False, "Backup file is empty."

        connection = None
        try:
            connection = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
            integrity_result = connection.execute('PRAGMA integrity_check').fetchone()
            if not integrity_result or integrity_result[0] != 'ok':
                return False, "SQLite integrity check failed."

            rows = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
            tables = {row[0] for row in rows}
            missing_tables = BackupService.REQUIRED_TABLES - tables
            if missing_tables:
                missing = ', '.join(sorted(missing_tables))
                return False, f"Backup is missing required table(s): {missing}."

            for table_name, required_columns in BackupService.REQUIRED_COLUMNS.items():
                column_rows = connection.execute(f'PRAGMA table_info({table_name})').fetchall()
                columns = {row[1] for row in column_rows}
                missing_columns = required_columns - columns
                if missing_columns:
                    missing = ', '.join(sorted(missing_columns))
                    return False, f"Table {table_name} is missing required column(s): {missing}."

            return True, None
        except sqlite3.DatabaseError as e:
            return False, f"Invalid SQLite database: {e}"
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def restore_from_file(uploaded_file_path):
        """Validate and replace the current database with the uploaded file."""
        db_path = BackupService.get_db_path()
        is_valid, validation_error = BackupService.validate_backup_file(uploaded_file_path)
        if not is_valid:
            return False, validation_error
        
        safety_backup = None
        try:
            db.session.remove()

            # Create a safety backup of current state
            if os.path.exists(db_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safety_backup = f"{db_path}.pre_restore_{timestamp}"
                shutil.copy2(db_path, safety_backup)

            # Copy uploaded file to db path
            shutil.copy2(uploaded_file_path, db_path)

            is_restored_valid, restored_error = BackupService.validate_backup_file(db_path)
            if not is_restored_valid:
                raise RuntimeError(restored_error)
            
            # Remove safety backup if everything went well
            if safety_backup and os.path.exists(safety_backup):
                os.remove(safety_backup)
                
            return True, None
        except Exception as e:
            # Attempt to restore safety backup if it exists
            if safety_backup and os.path.exists(safety_backup):
                shutil.copy2(safety_backup, db_path)
                os.remove(safety_backup)
            return False, str(e)
