"""
Midtrans Payment Gateway Integration for Chrisnov Invoice.
Generates Snap payment links for unpaid invoices.
"""
import logging
import uuid
import midtransclient
from flask import current_app

logger = logging.getLogger(__name__)

class PaymentService:
    """Handle Midtrans Snap payment link generation and status updates."""

    @staticmethod
    def get_client_keys():
        """Return the client key for frontend Snap token (safe to expose)."""
        return current_app.config.get('MIDTRANS_CLIENT_KEY', '')

    @staticmethod
    def is_configured():
        """Check if Midtrans is configured."""
        return bool(current_app.config.get('MIDTRANS_SERVER_KEY'))

    @staticmethod
    def create_snap_transaction(invoice):
        """
        Create a Midtrans Snap transaction for an invoice.
        Returns (success: bool, result: dict).
        result contains 'redirect_url' on success, or 'error' on failure.
        """
        if not PaymentService.is_configured():
            return False, {"error": "Midtrans not configured. Set MIDTRANS_SERVER_KEY."}

        try:
            # Use sandbox by default unless production is explicitly set
            is_production = current_app.config.get('MIDTRANS_IS_PRODUCTION', False)
            
            snap = midtransclient.Snap(
                is_production=is_production,
                server_key=current_app.config['MIDTRANS_SERVER_KEY'],
                client_key=current_app.config.get('MIDTRANS_CLIENT_KEY', '')
            )

            # Build customer details from invoice client
            client = invoice.client
            customer_details = {
                "first_name": client.name,
                "email": client.email or '',
                "phone": client.phone or '',
            }

            # Build item details (max 50 items per Midtrans limit)
            items = []
            for item in invoice.items[:50]:
                items.append({
                    "id": f"item-{item.id}",
                    "price": int(item.rate),  # Midtrans uses integer (cents for IDR)
                    "quantity": int(item.quantity),
                    "name": item.description[:50],
                })

            # Add tax as a line item if applicable
            if invoice.tax_amount > 0:
                items.append({
                    "id": "tax",
                    "price": int(invoice.tax_amount),
                    "quantity": 1,
                    "name": f"Tax ({invoice.tax_rate*100:.0f}%)",
                })

            # Generate unique order ID
            order_id = f"INV-{invoice.id}-{uuid.uuid4().hex[:6].upper()}"

            # Determine currency — Midtrans supports IDR only for Snap
            gross_amount = int(invoice.total)

            transaction_details = {
                "order_id": order_id,
                "gross_amount": gross_amount,
            }

            # Credit card options (optional)
            credit_card_options = {
                "secure": True,
                "save_card": False,
            }

            # Call Midtrans Snap API
            response = snap.create_transaction({
                "transaction_details": transaction_details,
                "credit_card": credit_card_options,
                "customer_details": customer_details,
                "item_details": items,
                "callbacks": {
                    "finish": f"https://{current_app.config.get('SERVER_NAME', 'invoice.chrisnov.cloud')}/invoices/{invoice.id}",
                }
            })

            # Store order_id in the invoice for tracking
            invoice.midtrans_order_id = order_id
            from app import db
            db.session.commit()

            logger.info(f"Midtrans transaction created: {order_id}")
            return True, {
                "redirect_url": response.get('redirect_url', ''),
                "token": response.get('token', ''),
                "order_id": order_id,
            }

        except Exception as e:
            logger.error(f"Midtrans transaction failed: {e}")
            return False, {"error": str(e)}

    @staticmethod
    def check_transaction_status(order_id):
        """
        Check the status of a Midtrans transaction.
        Returns dict with status information.
        """
        if not PaymentService.is_configured():
            return {"status": "error", "message": "Midtrans not configured"}

        try:
            is_production = current_app.config.get('MIDTRANS_IS_PRODUCTION', False)
            
            api = midtransclient.CoreApi(
                is_production=is_production,
                server_key=current_app.config['MIDTRANS_SERVER_KEY'],
                client_key=current_app.config.get('MIDTRANS_CLIENT_KEY', '')
            )

            response = api.transaction.status(order_id)
            
            # Map Midtrans status to invoice status
            transaction_status = response.get('transaction_status', '')
            
            status_map = {
                'capture': 'paid',
                'settlement': 'paid',
                'pending': 'unpaid',
                'deny': 'unpaid',
                'cancel': 'cancelled',
                'expire': 'cancelled',
                'refund': 'paid',  # Already paid, now refunded
            }
            
            return {
                "status": status_map.get(transaction_status, 'unknown'),
                "transaction_status": transaction_status,
                "order_id": order_id,
                "payment_type": response.get('payment_type', ''),
                "gross_amount": response.get('gross_amount', 0),
                "transaction_time": response.get('transaction_time', ''),
            }

        except Exception as e:
            logger.error(f"Midtrans status check failed: {e}")
            return {"status": "error", "message": str(e)}
