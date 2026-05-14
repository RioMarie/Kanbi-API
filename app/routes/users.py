from flask import jsonify, Blueprint, request
from app import db
from app.models import Users
from werkzeug.security import generate_password_hash
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError

class UserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

user_schema = UserSchema()

bp = Blueprint('users', __name__, url_prefix='/api/users')

@bp.route('', methods=['GET'])
def get_users():
    users = Users.query.all()
    return jsonify([
        {'id': u.id, 'email': u.email, 'created_at': u.created_at}
        for u in users
    ])

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = Users.query.get(user_id)
    
    if not user:
        return error_response('User not found', 400)

    return jsonify({'id': user.id, 'email': user.email, 'created_at': user.created_at})

@bp.route('', methods=['POST'])
def create_user():
    
    try:
        data = user_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    # Check if email already exists
    existing_user = Users.query.filter(
        Users.email.ilike(data['email'])  # ilike = case-insensitive LIKE
    ).first()

    if existing_user:
        return error_response('Email already exists', 409)
        
    try:
        user = Users(
            email=data['email'].lower(),  # Store as lowercase,
            password_hash=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'id': user.id, 'email': user.email}), 201
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create user: {str(e)}', 500)

def error_response(message, status_code):
    return jsonify({'error': message}), status_code