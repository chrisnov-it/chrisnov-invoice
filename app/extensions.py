from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
