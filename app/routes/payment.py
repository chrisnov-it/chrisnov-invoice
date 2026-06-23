"""
Payment routes for Midtrans Snap integration.
Generates payment links and handles webhook notifications.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Invoice
from app import db
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)
bp = Blueprint('payment', __name__, url_prefix='/payment')

@bp.route('/<int:invoice_id>/pay')
@login_required
def pay(invoice_id):
    """Generate Midtrans payment link for an invoice."""
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()

    if not PaymentService.is_configured():
        flash('Payment gateway not configured. Please set Midtrans keys in settings.', 'warning')
        return redirect(url_for('invoices.view', id=invoice.id))

    if invoice.status == 'paid':
        flash('This invoice has already been paid.', 'info')
        return redirect(url_for('invoices.view', id=invoice.id))

    success, result = PaymentService.create_snap_transaction(invoice)

    if success and result.get('redirect_url'):
        # Update status to unpaid when payment link is generated
        if invoice.status == 'draft':
            invoice.status = 'unpaid'
            db.session.commit()
        return redirect(result['redirect_url'])
    else:
        flash(f'Failed to create payment link: {result.get("error", "Unknown error")}', 'error')
        return redirect(url_for('invoices.view', id=invoice.id))

@bp.route('/<int:invoice_id>/status')
@login_required
def check_status(invoice_id):
    """Check payment status for an invoice."""
    invoice = Invoice.query.filter_by(id=invoice_id, user_id=current_user.id).first_or_404()

    if not invoice.midtrans_order_id:
        return jsonify({'status': 'no_payment', 'message': 'No payment link generated yet'})

    result = PaymentService.check_transaction_status(invoice.midtrans_order_id)

    # Auto-update invoice status if payment completed
    if result.get('status') == 'paid' and invoice.status != 'paid':
        invoice.status = 'paid'
        db.session.commit()
        flash('Payment confirmed! Invoice marked as paid.', 'success')
        return jsonify({'status': 'paid', 'message': 'Payment confirmed!'})

    return jsonify(result)

@bp.route('/midtrans-webhook', methods=['POST'])
def midtrans_webhook():
    """
    Midtrans payment notification webhook.
    Called by Midtrans when payment status changes.
    No auth required — uses order_id verification.
    """
    try:
        notification = request.get_json()
        if not notification:
            return jsonify({'status': 'error', 'message': 'No payload'}), 400

        order_id = notification.get('order_id', '')
        transaction_status = notification.get('transaction_status', '')

        # Extract invoice ID from order_id (format: INV-{id}-{hash})
        if order_id.startswith('INV-'):
            parts = order_id.split('-')
            if len(parts) >= 2:
                try:
                    invoice_id = int(parts[1])
                except ValueError:
                    invoice_id = None
            else:
                invoice_id = None
        else:
            invoice_id = None

        if not invoice_id:
            return jsonify({'status': 'error', 'message': 'Invalid order ID format'}), 400

        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return jsonify({'status': 'error', 'message': 'Invoice not found'}), 404

        # Update invoice status based on Midtrans notification
        if transaction_status in ('capture', 'settlement'):
            if invoice.status != 'paid':
                invoice.status = 'paid'
                db.session.commit()
                logger.info(f'Invoice {invoice.invoice_number} marked as paid via Midtrans webhook')
        elif transaction_status in ('deny', 'cancel', 'expire'):
            if invoice.status != 'cancelled' and invoice.status != 'paid':
                invoice.status = 'unpaid'
                db.session.commit()

        return jsonify({'status': 'ok'})

    except Exception as e:
        logger.error(f'Midtrans webhook error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/settings')
@login_required
def settings():
    """Payment gateway settings page."""
    return render_template('settings/payment.html',
                         midtrans_configured=PaymentService.is_configured(),
                         midtrans_client_key=PaymentService.get_client_keys())
