import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FLASK_APP = os.getenv('FLASK_APP')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ASSETS_ROOT = os.getenv('ASSETS_ROOT')
    FLASK_ENV = os.getenv('FLASK_ENV')
