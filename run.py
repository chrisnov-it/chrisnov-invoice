from app import create_app
from app.models import RecurringInvoice, Invoice, InvoiceItem, Currency, Client, User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import click
from app.extensions import db
from sqlalchemy import inspect, text

app = create_app()

def add_column_if_missing(table_name, column_name, column_sql):
    """Add a SQLite column for existing local databases created before migrations."""
    # Guard against SQL injection: table_name and column_name must be
    # simple identifiers (letters, digits, underscores only).
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
        raise ValueError(f"Invalid column name: {column_name!r}")
    # column_sql is a DDL fragment like "column_name TYPE DEFAULT ...".
    # Allow only alphanumerics, underscores, spaces, parens, quotes, dots,
    # hyphens, and the equals sign — no semicolons or SQL keywords.
    if not re.match(r"^[a-zA-Z0-9_().',\s=-]+$", column_sql):
        raise ValueError(f"Invalid column SQL: {column_sql!r}")

    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
    if column_name not in existing_columns:
        db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_sql}'))
        click.echo(f"Added missing column {table_name}.{column_name}.")

def ensure_ownership_columns():
    add_column_if_missing('clients', 'user_id', 'user_id INTEGER NULL')
    add_column_if_missing('clients', 'website', 'website VARCHAR(255)')
    add_column_if_missing('clients', 'nik', 'nik VARCHAR(30)')
    add_column_if_missing('clients', 'npwp', 'npwp VARCHAR(30)')
    add_column_if_missing('clients', 'custom_fields', 'custom_fields TEXT')
    add_column_if_missing('invoices', 'user_id', 'user_id INTEGER NULL')
    add_column_if_missing('recurring_invoices', 'user_id', 'user_id INTEGER NULL')
    add_column_if_missing('invoice_items', 'unit', "unit VARCHAR(20) DEFAULT 'pieces'")
    add_column_if_missing('recurring_invoice_items', 'unit', "unit VARCHAR(20) DEFAULT 'pieces'")

    if User.query.count() == 1:
        owner_id = User.query.first().id
        Client.query.filter_by(user_id=None).update({'user_id': owner_id})
        Invoice.query.filter_by(user_id=None).update({'user_id': owner_id})
        RecurringInvoice.query.filter_by(user_id=None).update({'user_id': owner_id})
        click.echo("Assigned existing ownerless records to the only user account.")
    db.session.commit()

@app.cli.command("init-db")
def init_db_command():
    """Create all database tables and seed initial data."""
    db.create_all()
    click.echo("Initialized the database and created all tables.")
    ensure_ownership_columns()

    if Currency.query.count() == 0:
        currencies = [
            {'code': 'IDR', 'name': 'Indonesian Rupiah', 'symbol': 'Rp'},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€'}
        ]
        for c in currencies:
            db.session.add(Currency(code=c['code'], name=c['name'], symbol=c['symbol']))
        db.session.commit()
        click.echo("Seeded currency data.")
    else:
        click.echo("Currency data already exists.")


@app.cli.command("generate-recurring")
def generate_recurring_invoices():
    """Generate invoices from recurring invoice schedules."""
    today = datetime.utcnow().date()
    due_recurring_invoices = RecurringInvoice.query.filter(
        RecurringInvoice.is_active,
        RecurringInvoice.next_due_date <= today
    ).all()

    for r_invoice in due_recurring_invoices:
        # Create a new standard invoice
        new_invoice = Invoice(
            invoice_number=generate_invoice_number(r_invoice.user_id),
            user_id=r_invoice.user_id,
            client_id=r_invoice.client_id,
            issue_date=today,
            due_date=today + timedelta(days=30), # Or calculate based on payment terms
            currency=r_invoice.currency,
            tax_rate=r_invoice.tax_rate,
            notes=r_invoice.notes,
            status='unpaid' # Or 'draft'
        )

        for r_item in r_invoice.items:
            new_item = InvoiceItem(
                description=r_item.description,
                unit=r_item.unit,
                quantity=r_item.quantity,
                rate=r_item.rate
            )
            new_item.calculate_amount()
            new_invoice.items.append(new_item)
        
        new_invoice.calculate_totals()
        db.session.add(new_invoice)

        # Update the next due date
        if r_invoice.frequency == 'daily':
            r_invoice.next_due_date += timedelta(days=r_invoice.interval)
        elif r_invoice.frequency == 'weekly':
            r_invoice.next_due_date += timedelta(weeks=r_invoice.interval)
        elif r_invoice.frequency == 'monthly':
            r_invoice.next_due_date += relativedelta(months=r_invoice.interval)
        elif r_invoice.frequency == 'yearly':
            r_invoice.next_due_date += relativedelta(years=r_invoice.interval)

        # Deactivate if end date is reached
        if r_invoice.end_date and r_invoice.next_due_date > r_invoice.end_date:
            r_invoice.is_active = False

        click.echo(f"Generated invoice {new_invoice.invoice_number} from recurring invoice {r_invoice.id}.")

    db.session.commit()
    click.echo("Recurring invoice generation complete.")

@app.cli.command("migrate-user-id")
@click.option('--admin-id', type=int, default=None,
              help='User ID to assign orphaned rows to. Defaults to DATABASE_ADMIN_USER_ID.')
def migrate_user_id(admin_id):
    """Assign NULL user_id rows to the admin user and add NOT NULL constraints.

    For PostgreSQL this runs ALTER COLUMN … SET NOT NULL.
    For SQLite it recreates each table with the constraint.
    """
    if admin_id is None:
        admin_id = app.config.get('DATABASE_ADMIN_USER_ID', 1)

    admin = db.session.get(User, admin_id)
    if admin is None:
        click.echo(f"Error: User with id={admin_id} does not exist.", err=True)
        raise SystemExit(1)

    click.echo(f"Admin user: {admin.name} (id={admin.id})")

    is_sqlite = db.engine.url.drivername == 'sqlite'
    tables = [
        ('clients', 'user_id'),
        ('invoices', 'user_id'),
        ('recurring_invoices', 'user_id'),
    ]

    # ── Step 1: Report and assign NULL rows ──────────────────────
    for table, column in tables:
        count = db.session.execute(
            text(f'SELECT COUNT(*) FROM {table} WHERE {column} IS NULL')
        ).scalar()
        if count:
            click.echo(f"  {table}: {count} orphaned row(s) → assigning to user {admin.id}")
            db.session.execute(
                text(f'UPDATE {table} SET {column} = :uid WHERE {column} IS NULL'),
                {'uid': admin.id},
            )
        else:
            click.echo(f"  {table}: no NULL {column} rows")

    db.session.commit()

    # ── Step 2: Enforce NOT NULL ─────────────────────────────────
    inspector = inspect(db.engine)

    for table, column in tables:
        col_info = next(
            (c for c in inspector.get_columns(table) if c['name'] == column),
            None,
        )
        if col_info is None:
            click.echo(f"  {table}.{column}: column does not exist, skipping")
            continue
        if not col_info.get('nullable', True):
            click.echo(f"  {table}.{column}: already NOT NULL, skipping")
            continue

        if is_sqlite:
            _sqlite_enforce_not_null(table, column, inspector)
        elif db.engine.url.drivername.startswith('mysql'):
            col_type = str(col_info['type'])
            db.session.execute(
                text(f'ALTER TABLE {table} MODIFY COLUMN {column} {col_type} NOT NULL')
            )
            click.echo(f"  {table}.{column}: set NOT NULL")
        else:
            db.session.execute(
                text(f'ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL')
            )
            click.echo(f"  {table}.{column}: set NOT NULL")

    db.session.commit()
    click.echo("Done. All user_id columns are now NOT NULL.")


def _sqlite_enforce_not_null(table, column, inspector):
    """Recreate a SQLite table with a column changed to NOT NULL.

    SQLite does not support ALTER COLUMN, so we:
    1. Create a new table with the desired schema.
    2. Copy all rows from the old table.
    3. Drop the old table.
    4. Rename the new table.
    """
    columns = inspector.get_columns(table)
    pk = inspector.get_pk_constraint(table)
    fks = inspector.get_foreign_keys(table)
    indexes = inspector.get_indexes(table)

    # Build column definitions, flipping the target column to NOT NULL.
    col_defs = []
    for c in columns:
        nullable = 'NOT NULL' if c['name'] == column else ('NOT NULL' if not c.get('nullable', True) else 'NULL')
        default = ''
        if c.get('default') is not None:
            d = c['default']
            if hasattr(d, 'arg'):
                default = f" DEFAULT {d.arg}"
            else:
                default = f" DEFAULT {d}"
        col_defs.append(f"{c['name']} {c['type']} {nullable}{default}")

    # Primary key
    pk_cols = pk.get('constrained_columns', [])
    pk_def = f", PRIMARY KEY ({', '.join(pk_cols)})" if pk_cols else ''

    # Foreign keys
    fk_defs = []
    for fk in fks:
        referred = fk.get('referred_table', '')
        referred_cols = fk.get('referred_columns', [])
        local_cols = fk.get('constrained_columns', [])
        if referred and referred_cols:
            fk_defs.append(
                f"FOREIGN KEY ({', '.join(local_cols)}) "
                f"REFERENCES {referred}({', '.join(referred_cols)})"
            )
    fk_sql = ', ' + ', '.join(fk_defs) if fk_defs else ''

    new_table = f"{table}_new"
    create_sql = f"CREATE TABLE {new_table} ({', '.join(col_defs)}{pk_def}{fk_sql})"
    db.session.execute(text(create_sql))

    # Copy data
    col_names = ', '.join(c['name'] for c in columns)
    db.session.execute(
        text(f'INSERT INTO {new_table} ({col_names}) SELECT {col_names} FROM {table}')
    )

    # Swap tables
    db.session.execute(text(f'DROP TABLE {table}'))
    db.session.execute(text(f'ALTER TABLE {new_table} RENAME TO {table}'))

    # Recreate indexes
    for idx in indexes:
        if idx.get('unique', False):
            idx_cols = ', '.join(idx['column_names'])
            db.session.execute(
                text(f'CREATE UNIQUE INDEX {idx["name"]} ON {table} ({idx_cols})')
            )
        else:
            idx_cols = ', '.join(idx['column_names'])
            db.session.execute(
                text(f'CREATE INDEX {idx["name"]} ON {table} ({idx_cols})')
            )

    click.echo(f"  {table}.{column}: recreated table with NOT NULL")


@app.cli.command("mark-overdue")
@click.option('--user-id', type=int, default=None, help='Limit overdue status updates to one user.')
def mark_overdue_invoices(user_id=None):
    """Mark due invoices as overdue without doing it during dashboard page loads."""
    today = datetime.utcnow().date()
    query = Invoice.query.filter(
        Invoice.due_date < today,
        Invoice.status.in_(['draft', 'sent', 'unpaid'])
    )

    if user_id is not None:
        query = query.filter(Invoice.user_id == user_id)

    updated = query.update({'status': 'overdue'}, synchronize_session=False)
    db.session.commit()
    click.echo(f"Marked {updated} invoice(s) as overdue.")

from app.routes.invoices import generate_invoice_number

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
