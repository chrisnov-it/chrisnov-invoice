from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from app.models import Client
from app import db
from flask_login import current_user

bp = Blueprint('clients', __name__, url_prefix='/clients')

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
        client = Client(
            name=request.form['name'],
            user_id=current_user.id,
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            company=request.form.get('company')
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
        client.name = request.form['name']
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.address = request.form.get('address')
        client.company = request.form.get('company')
        
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
