from flask import Blueprint, render_template
from app.models import Invoice, Client
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import current_user

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    # Get statistics
    total_clients = Client.query.filter_by(user_id=current_user.id).count()
    total_invoices = Invoice.query.filter_by(user_id=current_user.id).count()
    
    # Calculate total revenue (paid invoices)
    total_revenue = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        Invoice.user_id == current_user.id
    ).scalar() or 0
    
    # Calculate monthly revenue growth
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    # Start of previous month
    if start_of_month.month == 1:
        start_of_prev_month = start_of_month.replace(year=start_of_month.year - 1, month=12)
    else:
        start_of_prev_month = start_of_month.replace(month=start_of_month.month - 1)
    
    # Revenue this month
    revenue_this_month = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        Invoice.user_id == current_user.id,
        Invoice.issue_date >= start_of_month
    ).scalar() or 0
    
    # Revenue last month
    revenue_last_month = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.status == 'paid',
        Invoice.user_id == current_user.id,
        Invoice.issue_date >= start_of_prev_month,
        Invoice.issue_date < start_of_month
    ).scalar() or 0
    
    # Calculate growth percentage
    if revenue_last_month > 0:
        revenue_growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
    elif revenue_this_month > 0:
        revenue_growth = 100 # 100% growth if starting from 0
    else:
        revenue_growth = 0
        
    # Calculate pending amount (sent/unpaid but not paid)
    pending_amount = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.user_id == current_user.id,
        Invoice.status.in_(['sent', 'unpaid', 'overdue'])
    ).scalar() or 0
    
    # Get recent invoices
    recent_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.created_at.desc()).limit(5).all()
    
    # Get counts by status
    draft_count = Invoice.query.filter_by(user_id=current_user.id, status='draft').count()
    sent_count = Invoice.query.filter_by(user_id=current_user.id, status='sent').count()
    unpaid_count = Invoice.query.filter_by(user_id=current_user.id, status='unpaid').count()
    paid_count = Invoice.query.filter_by(user_id=current_user.id, status='paid').count()
    overdue_count = Invoice.query.filter_by(user_id=current_user.id, status='overdue').count()
    
    return render_template('dashboard/index.html',
                         total_clients=total_clients,
                         total_invoices=total_invoices,
                         total_revenue=total_revenue,
                         revenue_growth=revenue_growth,
                         pending_amount=pending_amount,
                         recent_invoices=recent_invoices,
                         draft_count=draft_count,
                         sent_count=sent_count,
                         unpaid_count=unpaid_count,
                         paid_count=paid_count,
                         overdue_count=overdue_count)
