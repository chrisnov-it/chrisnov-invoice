from app import create_app
from app.models import RecurringInvoice, Invoice, InvoiceItem, Currency, Client, User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import click
from app.extensions import db
from sqlalchemy import inspect, text

app = create_app()

def add_column_if_missing(table_name, column_name, column_sql):
    """Add a SQLite column for existing local databases created before migrations."""
    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns(table_name)}
    if column_name not in existing_columns:
        db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {column_sql}'))
        click.echo(f"Added missing column {table_name}.{column_name}.")

def ensure_ownership_columns():
    add_column_if_missing('clients', 'user_id', 'user_id INTEGER')
    add_column_if_missing('clients', 'website', 'website VARCHAR(255)')
    add_column_if_missing('invoices', 'user_id', 'user_id INTEGER')
    add_column_if_missing('recurring_invoices', 'user_id', 'user_id INTEGER')
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
