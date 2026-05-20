from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.models import RecurringInvoice, RecurringInvoiceItem, Client
from app import db
from datetime import datetime, timedelta
from flask_login import current_user

bp = Blueprint('recurring_invoices', __name__, url_prefix='/recurring')

@bp.route('/')
def index():
    recurring_invoices = RecurringInvoice.query.filter_by(user_id=current_user.id).order_by(RecurringInvoice.next_due_date.asc()).all()
    return render_template('recurring/index.html', recurring_invoices=recurring_invoices)

@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        try:
            client = Client.query.filter_by(id=request.form['client_id'], user_id=current_user.id).first()
            if not client:
                flash('Invalid client selected.', 'error')
                return redirect(url_for('recurring_invoices.new'))

            # Create recurring invoice
            recurring_invoice = RecurringInvoice(
                user_id=current_user.id,
                client_id=client.id,
                frequency=request.form['frequency'],
                interval=int(request.form['interval']),
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None,
                currency=request.form.get('currency', current_app.config['DEFAULT_CURRENCY']),
                tax_rate=float(request.form.get('tax_rate', 0)) / 100,
                notes=request.form.get('notes')
            )
            
            # Set next due date
            recurring_invoice.next_due_date = recurring_invoice.start_date

            # Add items
            descriptions = request.form.getlist('description[]')
            quantities = request.form.getlist('quantity[]')
            rates = request.form.getlist('rate[]')
            
            for desc, qty, rate in zip(descriptions, quantities, rates):
                if desc and qty and rate:
                    item = RecurringInvoiceItem(
                        description=desc,
                        quantity=float(qty),
                        rate=float(rate)
                    )
                    recurring_invoice.items.append(item)
            
            db.session.add(recurring_invoice)
            db.session.commit()
            
            flash('Recurring invoice created successfully!', 'success')
            return redirect(url_for('recurring_invoices.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating recurring invoice: {str(e)}', 'error')
    
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    return render_template('recurring/form.html', 
                         recurring_invoice=None, 
                         clients=clients)

@bp.route('/<int:id>')
def view(id):
    recurring_invoice = RecurringInvoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('recurring/view.html', recurring_invoice=recurring_invoice)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    recurring_invoice = RecurringInvoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            client = Client.query.filter_by(id=request.form['client_id'], user_id=current_user.id).first()
            if not client:
                flash('Invalid client selected.', 'error')
                return redirect(url_for('recurring_invoices.edit', id=recurring_invoice.id))

            recurring_invoice.client_id = client.id
            recurring_invoice.frequency = request.form['frequency']
            recurring_invoice.interval = int(request.form['interval'])
            recurring_invoice.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            recurring_invoice.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form['end_date'] else None
            recurring_invoice.currency = request.form.get('currency', current_app.config['DEFAULT_CURRENCY'])
            recurring_invoice.tax_rate = float(request.form.get('tax_rate', 0)) / 100
            recurring_invoice.notes = request.form.get('notes')

            # Update next due date if start date has changed
            if recurring_invoice.start_date > datetime.utcnow().date():
                recurring_invoice.next_due_date = recurring_invoice.start_date

            # Remove existing items
            RecurringInvoiceItem.query.filter_by(recurring_invoice_id=recurring_invoice.id).delete()

            # Add new items
            descriptions = request.form.getlist('description[]')
            quantities = request.form.getlist('quantity[]')
            rates = request.form.getlist('rate[]')
            
            for desc, qty, rate in zip(descriptions, quantities, rates):
                if desc and qty and rate:
                    item = RecurringInvoiceItem(
                        recurring_invoice_id=recurring_invoice.id,
                        description=desc,
                        quantity=float(qty),
                        rate=float(rate)
                    )
                    db.session.add(item)
            
            db.session.commit()
            flash('Recurring invoice updated successfully!', 'success')
            return redirect(url_for('recurring_invoices.view', id=recurring_invoice.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating recurring invoice: {str(e)}', 'error')
    
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    return render_template('recurring/form.html', recurring_invoice=recurring_invoice, clients=clients)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    recurring_invoice = RecurringInvoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(recurring_invoice)
        db.session.commit()
        flash('Recurring invoice deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting recurring invoice: {str(e)}', 'error')
    
    return redirect(url_for('recurring_invoices.index'))
