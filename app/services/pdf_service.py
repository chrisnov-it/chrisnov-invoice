from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from flask import current_app, has_app_context
from io import BytesIO
import os
from xml.sax.saxutils import escape

def pdf_text(value):
    """Escape user-controlled text before rendering it as ReportLab Paragraph markup."""
    if value is None:
        return ''
    return escape(str(value)).replace('\n', '<br/>')

def logo_alignment(config, fallback=TA_LEFT):
    position = config.get('PDF_LOGO_POSITION', 'left')
    if position == 'center':
        return TA_CENTER
    if position == 'right':
        return TA_RIGHT
    return fallback

def format_currency(amount, currency_code, config):
    """Format currency amount based on currency settings"""
    if currency_code not in config['SUPPORTED_CURRENCIES']:
        currency_code = config['DEFAULT_CURRENCY']

    currency_info = config['SUPPORTED_CURRENCIES'][currency_code]
    symbol = currency_info['symbol']
    position = currency_info['position']
    thousands_separator = currency_info.get('thousands_separator', ',')
    decimal_separator = currency_info.get('decimal_separator', '.')

    # Format the amount with thousands separator
    if amount == int(amount):
        # If amount is a whole number, format without decimal places
        formatted_amount = f"{int(amount):,}".replace(',', thousands_separator)
    else:
        # Format with 2 decimal places and thousands separator
        formatted_amount = f"{amount:,.2f}".replace(',', 'THOUSANDS_PLACEHOLDER').replace('.', decimal_separator).replace('THOUSANDS_PLACEHOLDER', thousands_separator)

    if position == 'before':
        return f"{symbol}{formatted_amount}"
    else:
        return f"{formatted_amount} {symbol}"

def add_logo_if_exists(elements, config, max_width=1.5*inch, max_height=0.8*inch, alignment=TA_LEFT):
    """Add logo to PDF if it exists"""
    logo_filename = config.get('LOGO_FILENAME')
    if not logo_filename:
        return

    static_folder = current_app.static_folder if has_app_context() else os.path.join('app', 'static')
    if '/' in logo_filename or '\\' in logo_filename:
        logo_path = os.path.join(static_folder, *logo_filename.replace('\\', '/').split('/'))
    else:
        logo_path = os.path.join(static_folder, 'images', 'logo.png')
    
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path)
            
            # Get original image size
            original_width = logo.imageWidth
            original_height = logo.imageHeight
            
            # Calculate aspect ratio
            aspect_ratio = original_height / float(original_width)
            
            # Calculate new width and height
            new_width = max_width
            new_height = new_width * aspect_ratio
            
            if new_height > max_height:
                new_height = max_height
                new_width = new_height / aspect_ratio
            
            logo.drawWidth = new_width
            logo.drawHeight = new_height
            logo.hAlign = 'CENTER' if alignment == TA_CENTER else 'LEFT'
            if alignment == TA_RIGHT:
                logo.hAlign = 'RIGHT'
            
            elements.append(logo)
            elements.append(Spacer(1, 0.1*inch))
        except Exception:
            # If logo can't be loaded, skip it
            pass

def generate_invoice_pdf(invoice, config):
    """Generate PDF for invoice"""
    buffer = BytesIO()

    # Get template settings with defaults
    pdf_template = config.get('PDF_TEMPLATE', 'professional')

    # Route to different template generators
    if pdf_template == 'modern':
        return generate_modern_pdf(invoice, config, buffer)
    elif pdf_template == 'minimal':
        return generate_minimal_pdf(invoice, config, buffer)
    elif pdf_template == 'elegant':
        return generate_elegant_pdf(invoice, config, buffer)
    else:  # professional or default
        return generate_professional_pdf(invoice, config, buffer)


def generate_professional_pdf(invoice, config, buffer):
    """Generate professional template PDF"""
    # Create PDF with professional margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    elements = []
    styles = getSampleStyleSheet()

    # Template settings
    header_color = config.get('PDF_HEADER_COLOR', 'blue')
    color_map = {
        'blue': colors.HexColor('#1e3a8a'),
        'green': colors.HexColor('#059669'),
        'purple': colors.HexColor('#7c3aed'),
        'gray': colors.HexColor('#374151'),
        'orange': colors.HexColor('#ea580c'),
        'red': colors.HexColor('#dc2626')
    }
    header_bg_color = color_map.get(header_color, colors.HexColor('#1e3a8a'))
    accent_color = color_map.get(config.get('PDF_ACCENT_COLOR', 'blue'), colors.HexColor('#1e3a8a'))

    # Status colors
    status_color_map = {
        'draft': colors.HexColor('#9ca3af'),
        'sent': colors.HexColor('#3b82f6'),
        'unpaid': colors.HexColor('#f59e0b'),
        'paid': colors.HexColor('#10b981'),
        'overdue': colors.HexColor('#ef4444'),
        'cancelled': colors.HexColor('#6b7280')
    }

    # Styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.white, alignment=TA_LEFT)
    invoice_title_style = ParagraphStyle('InvoiceTitle', parent=title_style, alignment=TA_RIGHT)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=header_bg_color, spaceAfter=6, spaceBefore=6)
    normal_style = ParagraphStyle('CompactNormal', parent=styles['Normal'], fontSize=9, leading=11)

    # Header section
    header_elements = []
    if config.get('PDF_SHOW_LOGO', True):
        add_logo_if_exists(header_elements, config, alignment=logo_alignment(config))

    header_elements.extend([
        Paragraph(f"<b>{pdf_text(config['BUSINESS_NAME'])}</b>", title_style),
        Paragraph(pdf_text(config['BUSINESS_ADDRESS']), normal_style),
        Paragraph(f"Phone: {pdf_text(config['BUSINESS_PHONE'])}", normal_style),
        Paragraph(f"Email: {pdf_text(config['BUSINESS_EMAIL'])}", normal_style),
    ])

    if config.get('BUSINESS_WEBSITE'):
        header_elements.append(Paragraph(f"Website: {pdf_text(config['BUSINESS_WEBSITE'])}", normal_style))

    pdf_status = 'unpaid' if invoice.status == 'draft' else invoice.status

    header_data = [[
        header_elements,
        [
            Paragraph("<b>INVOICE</b>", invoice_title_style),
            Paragraph(f"#{pdf_text(invoice.invoice_number)}", ParagraphStyle('InvoiceNumber', parent=styles['Normal'], fontSize=12, textColor=colors.white, alignment=TA_RIGHT, spaceBefore=6)),
            Paragraph(pdf_status.upper(), ParagraphStyle('Status', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backgroundColor=status_color_map.get(pdf_status, colors.HexColor('#9ca3af')), borderWidth=0, borderRadius=3, padding=4, alignment=TA_RIGHT))
        ]
    ]]

    header_table = Table(header_data, colWidths=[4.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), header_bg_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))

    # Horizontal layout: Bill To and Invoice Details
    horizontal_data = [[
        [
            Paragraph("<b>Bill To:</b>", heading_style),
            Paragraph(f"<b>{pdf_text(invoice.client.name)}</b>", normal_style),
            Paragraph(pdf_text(invoice.client.company), normal_style),
            Paragraph(pdf_text(invoice.client.address), normal_style),
            Paragraph(pdf_text(invoice.client.email), normal_style),
            Paragraph(pdf_text(invoice.client.phone), normal_style)
        ],
        [
            Paragraph("<b>Invoice Details:</b>", heading_style),
            Table([
                ['Invoice Number:', pdf_text(invoice.invoice_number)],
                ['Issue Date:', invoice.issue_date.strftime('%B %d, %Y')],
                ['Due Date:', invoice.due_date.strftime('%B %d, %Y')]
            ], colWidths=[1.2*inch, 2.8*inch], style=[
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ])
        ]
    ]]

    horizontal_layout = Table(horizontal_data, colWidths=[3.5*inch, 3.5*inch])
    horizontal_layout.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 8)]))
    elements.append(horizontal_layout)
    elements.append(Spacer(1, 0.2*inch))

    # Items table
    elements.append(Paragraph("<b>Items</b>", heading_style))
    data = [['Description', 'Quantity', 'Rate', 'Amount']]
    for item in invoice.items:
        data.append([pdf_text(item.description), f"{item.quantity:.2f}", format_currency(item.rate, invoice.currency, config), format_currency(item.amount, invoice.currency, config)])

    items_table = Table(data, colWidths=[3.5*inch, 1*inch, 1*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.1*inch))

    # Totals
    totals_data = [
        ['Subtotal:', format_currency(invoice.subtotal, invoice.currency, config)],
        [f"Tax ({invoice.tax_rate * 100:.1f}%):", format_currency(invoice.tax_amount, invoice.currency, config)],
        ['Total:', format_currency(invoice.total, invoice.currency, config)]
    ]
    totals_table = Table(totals_data, colWidths=[5*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 11),
        ('FONTSIZE', (0, -1), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, accent_color),
        ('TEXTCOLOR', (0, -1), (-1, -1), accent_color)
    ]))
    elements.append(totals_table)

    # Notes and footer
    if invoice.notes:
        elements.append(Spacer(1, 0.15*inch))
        elements.append(Paragraph("<b>Notes:</b>", heading_style))
        elements.append(Paragraph(pdf_text(invoice.notes), normal_style))

    elements.append(Spacer(1, 0.2*inch))
    footer_text = config.get('PDF_FOOTER_TEXT', f"Thank you for your business!<br/>{config['BUSINESS_NAME']}")
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER)
    elements.append(Paragraph(pdf_text(footer_text), footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_modern_pdf(invoice, config, buffer):
    """Generate modern template PDF - stylish, two-column design"""
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0, bottomMargin=0, leftMargin=0, rightMargin=0)
    elements = []
    styles = getSampleStyleSheet()

    # Template settings
    accent_color_name = config.get('PDF_ACCENT_COLOR', 'green')
    color_map = {
        'blue': colors.HexColor('#3b82f6'),
        'green': colors.HexColor('#10b981'),
        'purple': colors.HexColor('#8b5cf6'),
        'gray': colors.HexColor('#6b7280'),
        'orange': colors.HexColor('#f97316'),
        'red': colors.HexColor('#ef4444')
    }
    accent_color = color_map.get(accent_color_name, colors.HexColor('#10b981'))
    light_accent_color = colors.Color(accent_color.red, accent_color.green, accent_color.blue, alpha=0.1)

    # Custom fonts
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        # Assuming 'Helvetica-Neue' is available or falling back
        pdfmetrics.registerFont(TTFont('Helvetica-Neue', 'HelveticaNeue.ttf'))
        pdfmetrics.registerFont(TTFont('Helvetica-Neue-Bold', 'HelveticaNeue-Bold.ttf'))
        main_font = 'Helvetica-Neue'
        main_font_bold = 'Helvetica-Neue-Bold'
    except Exception:
        main_font = 'Helvetica'
        main_font_bold = 'Helvetica-Bold'

    # Custom styles
    heading_style = ParagraphStyle('ModernHeading', fontName=main_font_bold, fontSize=10, textColor=colors.HexColor('#6b7280'), spaceAfter=4, alignment=TA_LEFT)
    normal_style = ParagraphStyle('ModernNormal', fontName=main_font, fontSize=9, textColor=colors.HexColor('#374151'), leading=12)
    
    # --- Left Column (Sidebar) ---
    sidebar_elements = [Spacer(1, 0.75*inch)]
    
    # Logo
    if config.get('PDF_SHOW_LOGO', True):
        add_logo_if_exists(sidebar_elements, config, max_width=1.6*inch, max_height=1*inch)
        sidebar_elements.append(Spacer(1, 0.2*inch))

    sidebar_elements.extend([
        Paragraph("INVOICE", ParagraphStyle('SidebarTitle', fontName=main_font_bold, fontSize=24, textColor=accent_color, leading=28, spaceAfter=6)),
        Paragraph(f"<b># {pdf_text(invoice.invoice_number)}</b>", ParagraphStyle('SidebarSubtitle', fontName=main_font, fontSize=11, textColor=colors.HexColor('#374151'))),
        Spacer(1, 0.3*inch),
        Paragraph("BILL TO", heading_style),
        Paragraph(f"<b>{pdf_text(invoice.client.name)}</b>", normal_style),
        Paragraph(pdf_text(invoice.client.company), normal_style),
        Paragraph(pdf_text(invoice.client.address), normal_style),
        Paragraph(pdf_text(invoice.client.email), normal_style),
        Spacer(1, 0.3*inch),
        Paragraph("DETAILS", heading_style),
        Paragraph(f"<b>Issue Date:</b> {invoice.issue_date.strftime('%d %b %Y')}", normal_style),
        Paragraph(f"<b>Due Date:</b> {invoice.due_date.strftime('%d %b %Y')}", normal_style),
    ])

    # --- Right Column (Main Content) ---
    main_elements = [
        Spacer(1, 0.75*inch),
        Paragraph(f"<b>{pdf_text(config.get('BUSINESS_NAME', 'Your Business'))}</b>", ParagraphStyle('BusinessName', fontName=main_font_bold, fontSize=16, alignment=TA_RIGHT, leading=20, spaceAfter=6)),
        Paragraph(pdf_text(config.get('BUSINESS_ADDRESS', 'Your Address')), ParagraphStyle('BusinessAddress', parent=normal_style, alignment=TA_RIGHT)),
        Paragraph(pdf_text(config.get('BUSINESS_EMAIL', 'your@email.com')), ParagraphStyle('BusinessEmail', parent=normal_style, alignment=TA_RIGHT)),
        Spacer(1, 1.5*inch),
        Paragraph("ITEMS & SERVICES", ParagraphStyle('ItemsHeader', fontName=main_font_bold, fontSize=14, textColor=colors.black, spaceAfter=12)),
    ]

    # Items table
    data = [['DESCRIPTION', 'QTY', 'RATE', 'AMOUNT']]
    for item in invoice.items:
        data.append([
            Paragraph(pdf_text(item.description), normal_style),
            f"{item.quantity:.2f}",
            format_currency(item.rate, invoice.currency, config),
            format_currency(item.amount, invoice.currency, config)
        ])

    items_table = Table(data, colWidths=[2.3*inch, 0.6*inch, 0.8*inch, 1*inch], repeatRows=1)
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), main_font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6b7280')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#e5e7eb')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    main_elements.append(items_table)
    main_elements.append(Spacer(1, 0.2*inch))

    # Totals
    totals_data = [
        ['Subtotal', format_currency(invoice.subtotal, invoice.currency, config)],
        [f"Tax ({invoice.tax_rate * 100:.1f}%)", format_currency(invoice.tax_amount, invoice.currency, config)],
        ['', ''],
        ['TOTAL', format_currency(invoice.total, invoice.currency, config)]
    ]
    totals_table = Table(totals_data, colWidths=[3.2*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), main_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), main_font_bold),
        ('FONTSIZE', (0, -1), (-1, -1), 16),
        ('TEXTCOLOR', (0, -1), (-1, -1), accent_color),
        ('LINEABOVE', (0, -2), (-1, -2), 1, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, -2), (-1, -2), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -3), 4),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    main_elements.append(totals_table)
    
    # Notes
    if invoice.notes:
        main_elements.append(Spacer(1, 0.3*inch))
        main_elements.append(Paragraph("NOTES", heading_style))
        main_elements.append(Paragraph(pdf_text(invoice.notes), normal_style))

    # --- Main Layout Table ---
    layout_table = Table([[sidebar_elements, main_elements]], colWidths=[2.5*inch, 5.5*inch])
    layout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), light_accent_color),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0.4*inch),
        ('RIGHTPADDING', (0, 0), (0, 0), 0.4*inch),
        ('LEFTPADDING', (1, 0), (1, 0), 0.4*inch),
        ('RIGHTPADDING', (1, 0), (1, 0), 0.4*inch),
    ]))
    elements.append(layout_table)

    # Footer (Flexible positioning)
    elements.append(Spacer(1, 0.5*inch))
    footer_text = config.get('PDF_FOOTER_TEXT', f"Thank you for your business!")
    elements.append(Paragraph(pdf_text(footer_text), ParagraphStyle('Footer', fontName=main_font, fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_minimal_pdf(invoice, config, buffer):
    """Generate minimal template PDF - clean, text-focused, no colors"""
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    styles = getSampleStyleSheet()

    # Custom fonts
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont('Helvetica-Neue', 'HelveticaNeue.ttf'))
        pdfmetrics.registerFont(TTFont('Helvetica-Neue-Bold', 'HelveticaNeue-Bold.ttf'))
        main_font = 'Helvetica-Neue'
        main_font_bold = 'Helvetica-Neue-Bold'
    except Exception:
        main_font = 'Helvetica'
        main_font_bold = 'Helvetica-Bold'

    # Custom styles
    title_style = ParagraphStyle('MinimalTitle', fontName=main_font_bold, fontSize=16, textColor=colors.black, spaceAfter=24)
    heading_style = ParagraphStyle('MinimalHeading', fontName=main_font_bold, fontSize=9, textColor=colors.HexColor('#374151'), spaceAfter=6, alignment=TA_LEFT, textTransform='uppercase')
    normal_style = ParagraphStyle('MinimalNormal', fontName=main_font, fontSize=10, textColor=colors.black, leading=14)
    
    # Header
    header_data = [[
        Paragraph(pdf_text(config.get('BUSINESS_NAME', 'Your Business')), title_style),
        Paragraph('INVOICE', ParagraphStyle('MinimalInvoiceTitle', parent=title_style, alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    elements.append(header_table)
    elements.append(Spacer(1, 0.1*inch))

    # Business & Client Info
    info_data = [[
        [
            Paragraph(pdf_text(config.get('BUSINESS_ADDRESS', 'Your Address')), normal_style),
            Paragraph(pdf_text(config.get('BUSINESS_EMAIL', 'your@email.com')), normal_style),
        ],
        [
            Paragraph(f"<b>{pdf_text(invoice.client.name)}</b>", normal_style),
            Paragraph(pdf_text(invoice.client.address), normal_style),
        ]
    ]]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))

    # Invoice Details
    details_data = [[
        [
            Paragraph("INVOICE NUMBER", heading_style),
            Paragraph(pdf_text(invoice.invoice_number), normal_style),
        ],
        [
            Paragraph("ISSUE DATE", heading_style),
            Paragraph(invoice.issue_date.strftime('%Y-%m-%d'), normal_style),
        ],
        [
            Paragraph("DUE DATE", heading_style),
            Paragraph(invoice.due_date.strftime('%Y-%m-%d'), normal_style),
        ]
    ]]
    details_table = Table(details_data, colWidths=[2.33*inch, 2.33*inch, 2.33*inch])
    details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(details_table)
    elements.append(Spacer(1, 0.4*inch))

    # Items table
    data = [['DESCRIPTION', 'QTY', 'RATE', 'AMOUNT']]
    for item in invoice.items:
        data.append([
            Paragraph(pdf_text(item.description), normal_style),
            f"{item.quantity:.2f}",
            format_currency(item.rate, invoice.currency, config),
            format_currency(item.amount, invoice.currency, config)
        ])

    items_table = Table(data, colWidths=[3.5*inch, 1*inch, 1*inch, 1.5*inch], repeatRows=1)
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), main_font_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e5e7eb')),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.1*inch))

    # Totals
    totals_data = [
        ['Subtotal', format_currency(invoice.subtotal, invoice.currency, config)],
        [f"Tax ({invoice.tax_rate * 100:.1f}%)", format_currency(invoice.tax_amount, invoice.currency, config)],
        ['Total', format_currency(invoice.total, invoice.currency, config)]
    ]
    totals_table = Table(totals_data, colWidths=[5.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), main_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), main_font_bold),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)

    # Footer
    if invoice.notes:
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("NOTES", heading_style))
        elements.append(Paragraph(pdf_text(invoice.notes), normal_style))
        
    elements.append(Spacer(1, 0.5*inch))
    footer_text = config.get('PDF_FOOTER_TEXT', f"Thank you for your business!")
    elements.append(Paragraph(pdf_text(footer_text), ParagraphStyle('Footer', fontName=main_font, fontSize=9, alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_elegant_pdf(invoice, config, buffer):
    """Generate elegant template PDF - classic serif design"""
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
    elements = []
    styles = getSampleStyleSheet()

    # Fonts - Times New Roman (Built-in)
    main_font = 'Times-Roman'
    main_font_bold = 'Times-Bold'

    # Styles
    title_style = ParagraphStyle('ElegantTitle', fontName=main_font_bold, fontSize=20, leading=24, alignment=TA_CENTER, textColor=colors.black, spaceAfter=4)
    subtitle_style = ParagraphStyle('ElegantSubtitle', fontName=main_font, fontSize=10, leading=12, alignment=TA_CENTER, textColor=colors.black)
    invoice_label_style = ParagraphStyle('ElegantInvoiceLabel', fontName=main_font_bold, fontSize=14, leading=18, alignment=TA_CENTER, textColor=colors.black, spaceBefore=12, spaceAfter=12)
    
    heading_style = ParagraphStyle('ElegantHeading', fontName=main_font_bold, fontSize=10, textColor=colors.black, spaceAfter=2, alignment=TA_LEFT)
    normal_style = ParagraphStyle('ElegantNormal', fontName=main_font, fontSize=10, textColor=colors.black, leading=12)
    right_style = ParagraphStyle('ElegantRight', fontName=main_font, fontSize=10, textColor=colors.black, leading=12, alignment=TA_RIGHT)

    # --- Header ---
    if config.get('PDF_SHOW_LOGO', True):
        add_logo_if_exists(elements, config, alignment=TA_CENTER)
        
    elements.append(Paragraph(pdf_text(config.get('BUSINESS_NAME', 'Your Business').upper()), title_style))
    elements.append(Paragraph(pdf_text(config.get('BUSINESS_ADDRESS', 'Your Address')), subtitle_style))
    elements.append(Paragraph(pdf_text(config.get('BUSINESS_EMAIL', 'your@email.com')), subtitle_style))
    
    elements.append(Spacer(1, 0.4*inch))
    elements.append(Paragraph("INVOICE", invoice_label_style))
    elements.append(Spacer(1, 0.2*inch))

    # --- Info Section (3 Columns) ---
    # Column 1: Bill To
    col1 = [
        Paragraph("<b>BILLED TO:</b>", heading_style),
        Paragraph(pdf_text(invoice.client.name), normal_style),
        Paragraph(pdf_text(invoice.client.company), normal_style),
        Paragraph(pdf_text(invoice.client.address), normal_style),
    ]

    # Column 2: (Empty spacer)
    col2 = []

    # Column 3: Details
    col3 = [
        Paragraph("<b>DETAILS:</b>", heading_style),
        Paragraph(f"Invoice #: {pdf_text(invoice.invoice_number)}", normal_style),
        Paragraph(f"Issued: {invoice.issue_date.strftime('%B %d, %Y')}", normal_style),
        Paragraph(f"Due: {invoice.due_date.strftime('%B %d, %Y')}", normal_style),
    ]

    info_data = [[col1, col2, col3]]
    info_table = Table(info_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.4*inch))

    # --- Items Table ---
    # Header
    data = [[
        Paragraph('<b>DESCRIPTION</b>', heading_style),
        Paragraph('<b>QTY</b>', ParagraphStyle('ElegantQtyHeader', parent=heading_style, alignment=TA_RIGHT)),
        Paragraph('<b>RATE</b>', ParagraphStyle('ElegantRateHeader', parent=heading_style, alignment=TA_RIGHT)),
        Paragraph('<b>AMOUNT</b>', ParagraphStyle('ElegantAmountHeader', parent=heading_style, alignment=TA_RIGHT))
    ]]
    
    for item in invoice.items:
        data.append([
            Paragraph(pdf_text(item.description), normal_style),
            Paragraph(f"{item.quantity:.2f}", right_style),
            Paragraph(format_currency(item.rate, invoice.currency, config), right_style),
            Paragraph(format_currency(item.amount, invoice.currency, config), right_style)
        ])

    items_table = Table(data, colWidths=[3.5*inch, 1*inch, 1*inch, 1.5*inch], repeatRows=1)
    items_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),  # Header line
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.1*inch))

    # --- Totals ---
    totals_data = []
    totals_data.append(['Subtotal', format_currency(invoice.subtotal, invoice.currency, config)])
    if invoice.tax_rate > 0:
        totals_data.append([f"Tax ({invoice.tax_rate * 100:.1f}%)", format_currency(invoice.tax_amount, invoice.currency, config)])
    totals_data.append(['Total', format_currency(invoice.total, invoice.currency, config)])

    totals_table = Table(totals_data, colWidths=[5.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), main_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), main_font_bold),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black), # Total line
        ('TOPPADDING', (0, -1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)

    # --- Footer ---
    if invoice.notes:
        elements.append(Spacer(1, 0.4*inch))
        elements.append(Paragraph("<b>NOTES</b>", heading_style))
        elements.append(Paragraph(pdf_text(invoice.notes), normal_style))
        
    elements.append(Spacer(1, 0.6*inch))
    footer_text = config.get('PDF_FOOTER_TEXT', f"Thank you for your business!")
    elements.append(Paragraph(pdf_text(footer_text), ParagraphStyle('Footer', fontName=main_font, fontSize=9, alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    return buffer
