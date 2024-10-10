from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to login first.', 'danger')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('You are not authorized to access this page.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function

def user_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to login first.', 'danger')
            return redirect(url_for('login'))
        if current_user.role != 'user':
            flash('You are not authorized to access this page.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function
