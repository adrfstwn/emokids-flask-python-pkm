import os
from apps import create_app, db
from apps.models import User
from dotenv import load_dotenv

load_dotenv()

def seed_admin():
    app = create_app()
    with app.app_context():
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        # Check if the admin user already exists
        if not User.query.filter_by(username=admin_username).first():
            admin_user = User(
                username=admin_username,
                email=admin_email,
                role='admin'
            )
            admin_user.set_password(admin_password)

            db.session.add(admin_user)
            db.session.commit()

            print("Admin user created")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    seed_admin()
