from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from app.models import Client
from app import db
from flask_login import current_user
import json
import re

bp = Blueprint('clients', __name__, url_prefix='/clients')


def _validate_nik(value):
    value = (value or '').strip()
    if not value:
        return True, ''
    digits = re.sub(r'\D', '', value)
    if len(digits) != 16:
        return False, 'NIK must contain exactly 16 digits.'
    return True, digits


def _validate_npwp(value):
    value = (value or '').strip()
    if not value:
        return True, ''
    digits = re.sub(r'\D', '', value)
    if len(digits) not in (15, 16):
        return False, 'NPWP must contain 15 or 16 digits.'
    return True, value


def _parse_client_custom_fields():
    keys = request.form.getlist('custom_field_key')
    values = request.form.getlist('custom_field_value')
    result = {}
    for k, v in zip(keys, values):
        k = (k or '').strip()[:50]
        v = (v or '').strip()[:500]
        if not k or not v or k in result:
            continue
        result[k] = v
        if len(result) >= 20:
            break
    return result

@bp.route('/')
def index():
    search = request.args.get('search', '')
    page = max(request.args.get('page', 1, type=int), 1)
    query = Client.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f'%{search}%'),
                Client.email.ilike(f'%{search}%'),
                Client.website.ilike(f'%{search}%'),
                Client.company.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(Client.name).paginate(
        page=page,
        per_page=current_app.config['ITEMS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('clients/index.html', clients=pagination.items, pagination=pagination, search=search)

@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        nik_ok, nik_clean = _validate_nik(request.form.get('nik', ''))
        if not nik_ok:
            flash(f'Invalid NIK: {nik_clean}', 'error')
            return render_template('clients/form.html', client=None)
        npwp_ok, npwp_clean = _validate_npwp(request.form.get('npwp', ''))
        if not npwp_ok:
            flash(f'Invalid NPWP: {npwp_clean}', 'error')
            return render_template('clients/form.html', client=None)
        client = Client(
            name=request.form['name'],
            user_id=current_user.id,
            email=request.form.get('email'),
            website=request.form.get('website'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            company=request.form.get('company'),
            nik=nik_clean or None,
            npwp=npwp_clean or None,
            custom_fields=json.dumps(_parse_client_custom_fields(), ensure_ascii=False)
        )
        
        try:
            db.session.add(client)
            db.session.commit()
            flash('Client created successfully!', 'success')
            return redirect(url_for('clients.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating client: {str(e)}', 'error')
    
    return render_template('clients/form.html', client=None)

@bp.route('/<int:id>')
def view(id):
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('clients/view.html', client=client)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        nik_ok, nik_clean = _validate_nik(request.form.get('nik', ''))
        if not nik_ok:
            flash(f'Invalid NIK: {nik_clean}', 'error')
            return render_template('clients/form.html', client=client)
        npwp_ok, npwp_clean = _validate_npwp(request.form.get('npwp', ''))
        if not npwp_ok:
            flash(f'Invalid NPWP: {npwp_clean}', 'error')
            return render_template('clients/form.html', client=client)
        client.name = request.form['name']
        client.email = request.form.get('email')
        client.website = request.form.get('website')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.company = request.form.get('company')
        client.nik = nik_clean or None
        client.npwp = npwp_clean or None
        client.custom_fields = json.dumps(_parse_client_custom_fields(), ensure_ascii=False)
        
        try:
            db.session.commit()
            flash('Client updated successfully!', 'success')
            return redirect(url_for('clients.view', id=client.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating client: {str(e)}', 'error')
    
    return render_template('clients/form.html', client=client)

@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    client = Client.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Client deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting client: {str(e)}', 'error')
    
    return redirect(url_for('clients.index'))
