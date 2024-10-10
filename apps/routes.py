import pandas as pd
import uuid
import logging

from flask import render_template, flash, redirect, url_for, request, current_app, abort, send_file, request, jsonify, session
from apps import db
from apps.forms import LoginForm, RegistrationForm, ProfileForm
from apps.models import User, Siswa, PoseData, ExpresionData, ActiveAdminSession
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from .decorators import admin_required
from .decorators import user_required
from io import BytesIO
from datetime import datetime, timedelta, date

# Home route
@current_app.route('/')
    
#index orang tua
@current_app.route('/index')
@login_required
def index():
    try:
        
        all_siswa = Siswa.query.all()

        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return render_template('home/index.html', title='Home', all_siswa=all_siswa)
    except Exception as e:
        current_app.logger.error(f"Error in index route: {e}")
        return "Internal Server Error", 500

# Admin dashboard route
@current_app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    try:
        if current_user.role != 'admin':
            return redirect(url_for('index'))

        current_session_id = session.get('session_id')
        active_session = ActiveAdminSession.query.filter_by(admin_id=current_user.id, session_id=current_session_id).first()

        if not active_session:
            logout_user()
            return redirect(url_for('login'))

        return render_template('home/index_admin.html', title='Admin Dashboard')
    except Exception as e:
        current_app.logger.error(f"Error in admin_dashboard route: {e}")
        return "Internal Server Error", 500

@current_app.route('/statistik')
@login_required
@user_required
def statistik():
    return render_template('siswa/statistik.html', title='Statistik')

# Route untuk ekspor ke Excel
@current_app.route('/export_excel')
@login_required
@user_required
def export_excel():
    # Ambil semua data
    expresion_data = ExpresionData.query.all()
    pose_data = PoseData.query.all()

    # Siapkan data untuk diekspor
    expresion_data_list = [(data.timestamp, data.expresion, data.confidence) for data in expresion_data]
    pose_data_list = [(data.timestamp, data.pose, data.confidence) for data in pose_data]

    # Buat dataframe pandas
    df_expresion = pd.DataFrame(expresion_data_list, columns=['Timestamp', 'Expresion', 'Confidence'])
    df_pose = pd.DataFrame(pose_data_list, columns=['Timestamp', 'Pose', 'Confidence'])

    # Tulis ke Excel menggunakan pandas ExcelWriter
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_expresion.to_excel(writer, sheet_name='ExpresionData', index=False)
        df_pose.to_excel(writer, sheet_name='PoseData', index=False)
    
    output.seek(0)
    
    # Return file Excel untuk didownload
    return send_file(output, download_name='statistik.xlsx', as_attachment=True)

@current_app.route('/emotion_history', methods=['GET'])
@login_required
def get_emotion_history():
    try:
        # Get the current time and one minute ago
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=1)
        
        # Query to get emotion history in the last minute
        emotion_data = ExpresionData.query.filter(
            ExpresionData.timestamp >= start_time,
            ExpresionData.timestamp <= end_time
        ).all()
        
        # Accumulate the count of each emotion
        emotion_count = {
            "senang": 0,
            "sedih": 0,
            "normal": 0,
            "marah": 0,
            "cemas": 0,
            "bosan": 0,
            # Add other emotions as needed
        }
        
        for data in emotion_data:
            if data.expresion in emotion_count:
                emotion_count[data.expresion] += 1
        
        # Detect if there is a combination of emotions that is not normal
        emotion_status = "normal"
        if emotion_count.get('marah', 0) > 0 and emotion_count.get('sedih', 0) > 0:
            emotion_status = "not normal"
        
        # Add additional logic as needed for "normal" or "not normal"
        
        return jsonify({
            'emotion_count': emotion_count,
            'status': emotion_status,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logging.error(f"Error fetching emotion history: {str(e)}")
        return jsonify({'error': 'Failed to fetch emotion history'}), 500
    
@current_app.route('/get/statistik', methods=['GET'])
def get_statistik():
    today = date.today()
    try:
         # Query hanya data ekspresi dan pose dari hari ini
        expresion_data = ExpresionData.query.filter(db.func.date(ExpresionData.timestamp) == today).all()
        pose_data = PoseData.query.filter(db.func.date(PoseData.timestamp) == today).all()

        if not expresion_data or not pose_data:
            logging.error('Data ekspresi atau pose tidak ditemukan')
            return jsonify({'error': 'Data not found'}), 404

        expresion_list = [{'timestamp': data.timestamp, 'expresion': data.expresion} for data in expresion_data]
        pose_list = [{'timestamp': data.timestamp, 'pose': data.pose} for data in pose_data]

        return jsonify({
            'expresion_data': expresion_list,
            'pose_data': pose_list
        })
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'error': 'Failed to fetch emotion history'}), 500

# Route to display the data siswa page
@current_app.route('/data_siswa')
@login_required
@admin_required
def data_siswa():
    try:
        # Fetch all siswa data from the database
        all_siswa = Siswa.query.all()
        return render_template('siswa/data_siswa.html', title='Data Siswa', all_siswa=all_siswa)
    except Exception as e:
        current_app.logger.error(f"Error in data_siswa route: {e}")
        return "Internal Server Error", 500
    
# Route to add data
@current_app.route('/add_data_siswa', methods=['GET', 'POST'])
@login_required
@admin_required
def add_data_siswa():
    if request.method == 'POST':
        try:
            # Logic to add new data
            id_siswa = request.form['id_siswa']
            name = request.form['name']
            birth_date = request.form['birth_date']
            kelas = request.form['kelas']
            new_siswa = Siswa(id_siswa=id_siswa, name=name, birth_date=birth_date, kelas=kelas)
            db.session.add(new_siswa)
            db.session.commit()
            flash('Data siswa added successfully!')
            return redirect(url_for('data_siswa'))
        except Exception as e:
            current_app.logger.error(f"Error in add_data_siswa route: {e}")
            return "Internal Server Error", 500
    return render_template('siswa/create_data_siswa.html', title='Tambah Data Siswa')

# Route to edit data
@current_app.route('/edit_data_siswa-<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_data_siswa(id):
    siswa = Siswa.query.get_or_404(id)
    if request.method == 'POST':
        try:
            # Logic to edit data
            siswa.id_siswa = request.form['id_siswa']
            siswa.name = request.form['name']
            siswa.birth_date = request.form['birth_date']
            siswa.kelas = request.form['kelas']
            db.session.commit()
            flash('Data siswa updated successfully!')
            return redirect(url_for('data_siswa'))
        except Exception as e:
            current_app.logger.error(f"Error in edit_data_siswa route: {e}")
            return "Internal Server Error", 500
    return render_template('siswa/edit_data_siswa.html', title='Edit Data Siswa', siswa=siswa)

@current_app.route('/delete_data_siswa-<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_data_siswa(id):
    try:
        siswa = Siswa.query.get_or_404(id)
        db.session.delete(siswa)
        db.session.commit()
        flash('Data siswa berhasil dihapus!')
    except Exception as e:
        current_app.logger.error(f"Error deleting siswa: {e}")
        flash('Terjadi kesalahan saat menghapus data siswa.', 'error')
    return redirect(url_for('data_siswa'))

#profile
@current_app.route('/profile-<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Verifikasi bahwa pengguna yang sedang masuk hanya dapat mengakses profil mereka sendiri
    if current_user.id != user_id:
        abort(403)  # Mengembalikan error 403 Forbidden jika mencoba mengakses profil orang lain

    form = ProfileForm(obj=user)  # Populate the form with user data

    if form.validate_on_submit():
        form.populate_obj(user)  # Update user object with form data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))

    return render_template('accounts/profile.html', title='Profile', user=user, form=form)

# Login route

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username_or_email.data) | (User.email == form.username_or_email.data)).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            # Generate a new session ID
            new_session_id = str(uuid.uuid4())
            if user.role == 'admin':
                # Remove existing admin session
                ActiveAdminSession.query.filter_by(admin_id=user.id).delete()

                # Create a new session
                new_session = ActiveAdminSession(admin_id=user.id, session_id=new_session_id)
                db.session.add(new_session)
                db.session.commit()

            session['session_id'] = new_session_id

            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                if user.role == 'admin':
                    next_page = url_for('admin_dashboard')
                else:
                    next_page = url_for('index')
            return redirect(next_page)

        flash('Invalid username or password', 'danger')

    return render_template('accounts/login.html', title='Sign In', form=form)

# Login route
@current_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        # Query user by username or email
        user = User.query.filter(
            (User.username == form.username_or_email.data) | 
            (User.email == form.username_or_email.data)
        ).first()

        # Check if user exists and password is valid
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            # Generate a new session ID
            new_session_id = str(uuid.uuid4())
            session['session_id'] = new_session_id

            # Admin-specific logic for session handling
            if user.role == 'admin':
                # Remove old admin sessions
                old_sessions = ActiveAdminSession.query.filter_by(admin_id=user.id).all()
                for old_session in old_sessions:
                    db.session.delete(old_session)
                db.session.commit()

                # Create new admin session
                new_admin_session = ActiveAdminSession(admin_id=user.id, session_id=new_session_id)
                db.session.add(new_admin_session)
                db.session.commit()

            # Redirect to appropriate page
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('admin_dashboard') if user.role == 'admin' else url_for('index')

            return redirect(next_page)

        flash('Invalid username or password', 'danger')

    return render_template('accounts/login.html', title='Sign In', form=form)

# Logout route
@current_app.route('/logout')
def logout():
    if current_user.is_authenticated:
        # Access session ID from session
        session_id = session.get('session_id')
        if session_id:
            # Find the corresponding admin session
            admin_session = ActiveAdminSession.query.filter_by(admin_id=current_user.id, session_id=session_id).first()
            if admin_session:
                db.session.delete(admin_session)
                db.session.commit()

    # Log the user out
    logout_user()
    return redirect(url_for('index'))

# Registration route
@current_app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data) 
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('accounts/register.html', title='Register', form=form)

@current_app.route('/check_session')
@login_required
def check_session():
    active_session = ActiveAdminSession.query.filter_by(admin_id=current_user.id, session_id=session.sid).first()
    return jsonify({'session_valid': bool(active_session)})

@current_app.errorhandler(403)
def page_not_found(e):
    return render_template('home/page-403.html'), 404
@current_app.errorhandler(404)
def page_not_found(e):
    return render_template('home/page-404.html'), 404
@current_app.errorhandler(500)
def page_not_found(e):
    return render_template('home/page-500.html'), 500
