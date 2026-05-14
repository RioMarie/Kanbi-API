from flask import jsonify, Blueprint, request
from app import db
from app.models import Users
from marshmallow import Schema, fields, validate, ValidationError
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

login_schema = LoginSchema()

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
   
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return error_response(err.messages, 400)
    except Exception:
        return error_response('Request must be JSON', 400)
    
    try:
        # Find user by email (case-insensitive)
        user = Users.query.filter(
            Users.email.ilike(data['email'].lower())
        ).first()
        
        if not user:
            return error_response('Invalid email or password', 401)
        
        # Check password
        if not check_password_hash(user.password_hash, data['password']):
            return error_response('Invalid email or password', 401)
        
        # Create JWT token (expires in 24 hours)
        access_token = create_access_token(
            identity=str(user.id), # ← Convert to string
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email
            }
        }), 200
    
    except Exception as e:
        return error_response(f'Login failed: {str(e)}', 500)
    
    
def error_response(message, status_code):
    return jsonify({'error': message}), status_code