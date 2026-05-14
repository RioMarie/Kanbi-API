from app.routes.cards import bp as cards_bp
from app.routes.columns import bp as columns_bp
from app.routes.boards import bp as boards_bp
from app.routes.users import bp as users_bp
from app.routes.session import bp as session_bp

def register_blueprints(app):
    app.register_blueprint(cards_bp)
    app.register_blueprint(columns_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(session_bp)