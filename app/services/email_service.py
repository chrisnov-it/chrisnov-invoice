from flask import current_app
from flask_mail import Mail, Message
from app.services.pdf_service import generate_invoice_pdf
import os

def get_mail_connection_label():
    server = current_app.config.get('MAIL_SERVER') or '(not configured)'
    port = current_app.config.get('MAIL_PORT') or '(no port)'
    encryption = 'SSL' if current_app.config.get('MAIL_USE_SSL') else 'TLS' if current_app.config.get('MAIL_USE_TLS') else 'plain'
    return f'{server}:{port} ({encryption})'

def validate_mail_settings():
    missing = []
    if not current_app.config.get('MAIL_SERVER'):
        missing.append('mail server')
    if not current_app.config.get('MAIL_PORT'):
        missing.append('port')
    if not current_app.config.get('MAIL_DEFAULT_SENDER'):
        missing.append('from email')

    if missing:
        return False, f"Please configure {', '.join(missing)} before sending email."
    return True, None

def send_mail_message(message):
    """Send email using the current request's resolved mail configuration."""
    valid, error = validate_mail_settings()
    if not valid:
        raise RuntimeError(error)

    configured_mail = Mail(current_app._get_current_object())
    configured_mail.send(message)

def send_invoice_email(invoice, recipient_email, subject=None, message=None):
    """Send invoice via email with PDF attachment"""
    try:
        # Generate PDF
        pdf_buffer = generate_invoice_pdf(invoice, current_app.config)

        # Create email message
        if not subject:
            subject = f"Invoice {invoice.invoice_number} from {current_app.config['BUSINESS_NAME']}"

        if not message:
            # Import here to avoid circular imports
            from app import format_currency_filter
            
            total_formatted = format_currency_filter(invoice.total, invoice.currency, current_app.config)
            
            message = f"""
            Dear {invoice.client.name},

            Please find attached invoice {invoice.invoice_number} for {total_formatted}.

            Invoice Details:
            - Invoice Number: {invoice.invoice_number}
            - Issue Date: {invoice.issue_date.strftime('%B %d, %Y')}
            - Due Date: {invoice.due_date.strftime('%B %d, %Y')}
            - Total Amount: {total_formatted}

            Thank you for your business!

            Best regards,
            {current_app.config['BUSINESS_NAME']}
            {current_app.config['BUSINESS_ADDRESS']}
            Phone: {current_app.config['BUSINESS_PHONE']}
            Email: {current_app.config['BUSINESS_EMAIL']}
            """
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=message,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )

        # Attach PDF
        msg.attach(
            f"{invoice.invoice_number}.pdf",
            "application/pdf",
            pdf_buffer.getvalue()
        )

        # Send email
        send_mail_message(msg)

        return True, "Invoice sent successfully via email"

    except Exception as e:
        return False, f"Failed to send invoice email: {str(e)}"

def send_invoice_to_client(invoice):
    """Send invoice to the client's email address"""
    if not invoice.client.email:
        return False, "Client has no email address"

    # Import here to avoid circular imports
    from app import format_currency_filter
    
    total_formatted = format_currency_filter(invoice.total, invoice.currency, current_app.config)

    return send_invoice_email(
        invoice,
        invoice.client.email,
        subject=f"Invoice {invoice.invoice_number} from {current_app.config['BUSINESS_NAME']}",
        message=f"""
        Dear {invoice.client.name},

        Please find attached invoice {invoice.invoice_number} for {total_formatted}.

        Invoice Details:
        - Invoice Number: {invoice.invoice_number}
        - Issue Date: {invoice.issue_date.strftime('%B %d, %Y')}
        - Due Date: {invoice.due_date.strftime('%B %d, %Y')}
        - Total Amount: {total_formatted}

        If you have any questions about this invoice, please don't hesitate to contact us.

        Thank you for your business!

        Best regards,
        {current_app.config['BUSINESS_NAME']}
        {current_app.config['BUSINESS_ADDRESS']}
        Phone: {current_app.config['BUSINESS_PHONE']}
        Email: {current_app.config['BUSINESS_EMAIL']}
        """
    )
