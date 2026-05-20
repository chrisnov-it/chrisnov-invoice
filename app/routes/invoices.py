from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from app.models import Invoice, InvoiceItem, Client
from app.services.pdf_service import generate_invoice_pdf
from app.services.email_service import send_invoice_to_client
from app import db
from datetime import datetime, timedelta
from flask_login import current_user

bp = Blueprint('invoices', __name__, url_prefix='/invoices')

def generate_invoice_number():
    """Generate unique invoice number"""
    today = datetime.now()
    prefix = f"INV-{today.strftime('%Y%m')}"
    
    # Get last invoice number for this month
    last_invoice = Invoice.query.filter(
        Invoice.user_id == current_user.id,
        Invoice.invoice_number.like(f"{prefix}%")
    ).order_by(Invoice.invoice_number.desc()).first()
    
    if last_invoice:
        last_num = int(last_invoice.invoice_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}-{new_num:04d}"

@bp.route('/')
def index():
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    query = Invoice.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if search:
        query = query.join(Client).filter(
            Client.user_id == current_user.id,
            db.or_(
                Invoice.invoice_number.ilike(f'%{search}%'),
                Client.name.ilike(f'%{search}%')
            )
        )
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    return render_template('invoices/index.html', 
                         invoices=invoices, 
                         status_filter=status_filter,
                         search=search)

@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        try:
            client = Client.query.filter_by(id=request.form['client_id'], user_id=current_user.id).first()
            if not client:
                flash('Invalid client selected.', 'error')
                return redirect(url_for('invoices.new'))

            # Create invoice
            invoice = Invoice(
                invoice_number=request.form['invoice_number'],
                user_id=current_user.id,
                client_id=client.id,
                issue_date=datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date(),
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(),
                currency=request.form.get('currency', current_app.config['DEFAULT_CURRENCY']),
                tax_rate=float(request.form.get('tax_rate') or 0) / 100,
                notes=request.form.get('notes')
            )
            
            # Add items
            descriptions = request.form.getlist('description[]')
            quantities = request.form.getlist('quantity[]')
            rates = request.form.getlist('rate[]')
            
            for desc, qty, rate in zip(descriptions, quantities, rates):
                if desc and qty and rate:
                    item = InvoiceItem(
                        description=desc,
                        quantity=float(qty),
                        rate=float(rate)
                    )
                    item.calculate_amount()
                    invoice.items.append(item)
            
            # Calculate totals
            invoice.calculate_totals()
            
            db.session.add(invoice)
            db.session.commit()
            
            flash('Invoice created successfully!', 'success')
            return redirect(url_for('invoices.view', id=invoice.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating invoice: {str(e)}', 'error')
    
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    invoice_number = generate_invoice_number()
    default_due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('invoices/form.html', 
                         invoice=None, 
                         clients=clients,
                         invoice_number=invoice_number,
                         default_due_date=default_due_date)

@bp.route('/<int:id>')
def view(id):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('invoices/view.html', invoice=invoice)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            client = Client.query.filter_by(id=request.form['client_id'], user_id=current_user.id).first()
            if not client:
                flash('Invalid client selected.', 'error')
                return redirect(url_for('invoices.edit', id=invoice.id))

            invoice.invoice_number = request.form['invoice_number']
            invoice.client_id = client.id
            invoice.issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date()
            invoice.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
            invoice.currency = request.form.get('currency', current_app.config['DEFAULT_CURRENCY'])
            invoice.tax_rate = float(request.form.get('tax_rate') or 0) / 100
            invoice.notes = request.form.get('notes')
            
            # Remove existing items
            InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
            
            # Add new items
            descriptions = request.form.getlist('description[]')
            quantities = request.form.getlist('quantity[]')
            rates = request.form.getlist('rate[]')
            
            for desc, qty, rate in zip(descriptions, quantities, rates):
                if desc and qty and rate:
                    item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=desc,
                        quantity=float(qty),
                        rate=float(rate)
                    )
                    item.calculate_amount()
                    db.session.add(item)
            
            # Calculate totals
            invoice.calculate_totals()
            
            db.session.commit()
            flash('Invoice updated successfully!', 'success')
            return redirect(url_for('invoices.view', id=invoice.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating invoice: {str(e)}', 'error')
    
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    return render_template('invoices/form.html', invoice=invoice, clients=clients)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting invoice: {str(e)}', 'error')
    
    return redirect(url_for('invoices.index'))

@bp.route('/<int:id>/status/<status>', methods=['POST'])
def update_status(id, status):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    valid_statuses = ['draft', 'sent', 'unpaid', 'paid', 'cancelled']
    if status in valid_statuses:
        # Store the previous status
        previous_status = invoice.status
        
        # Update the invoice status
        invoice.status = status
        
        # Clear notes when marking as paid
        if status == 'paid':
            invoice.notes = ""
        
        db.session.commit()
        flash(f'Invoice marked as {status}!', 'success')
    else:
        flash('Invalid status!', 'error')
    
    return redirect(url_for('invoices.view', id=invoice.id))

@bp.route('/<int:id>/download')
def download(id):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        pdf_file = generate_invoice_pdf(invoice, current_app.config)
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"{invoice.invoice_number}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('invoices.view', id=invoice.id))

@bp.route('/<int:id>/email', methods=['POST'])
def email(id):
    invoice = Invoice.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    try:
        success, message = send_invoice_to_client(invoice)

        if success:
            # Update invoice status to unpaid if it was draft (more accurate workflow)
            if invoice.status == 'draft':
                invoice.status = 'unpaid'
                db.session.commit()

            flash(message, 'success')
        else:
            flash(message, 'error')

    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')

    return redirect(url_for('invoices.view', id=invoice.id))
