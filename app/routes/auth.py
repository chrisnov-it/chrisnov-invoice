from urllib.parse import urlparse

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.extensions import limiter
from app.models import Client, Invoice, RecurringInvoice, User

bp = Blueprint('auth', __name__, url_prefix='/auth')


def is_safe_next_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith('/')


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AUTH', '5 per minute'), methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if not current_app.config.get('ALLOW_REGISTRATION', True):
        flash('Registration is currently closed.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Name, email, and password are required.', 'error')
            return render_template('auth/register.html', name=name, email=email)

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
            return render_template('auth/register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html', name=name, email=email)

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('auth/register.html', name=name, email=email)

        is_first_user = User.query.count() == 0
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if is_first_user:
            Client.query.filter_by(user_id=None).update({'user_id': user.id})
            Invoice.query.filter_by(user_id=None).update({'user_id': user.id})
            RecurringInvoice.query.filter_by(user_id=None).update({'user_id': user.id})

        db.session.commit()

        login_user(user)
        flash('Welcome! Your account has been created.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_AUTH', '5 per minute'), methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        next_url = request.args.get('next')
        if is_safe_next_url(next_url):
            return redirect(next_url)

        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
