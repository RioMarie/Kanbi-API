from flask import jsonify, request, Blueprint
from app import db
from app.models import Cards, Columns
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity

class CardSchema(Schema):
    column_id = fields.Int(required=False)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    position = fields.Int(required=True)
    description = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    due_date = fields.Date(required=True)
    priority = fields.Int(required=True)
    
card_schema = CardSchema()

bp = Blueprint('cards', __name__, url_prefix='/api/cards')

@bp.route('', methods=['GET'])
@jwt_required()
def get_cards():
    column_id = request.args.get('column_id')
    
    if not column_id:
        return error_response('column_id is missing', 400)
    
    cards = Cards.query.filter_by(column_id=column_id).all()
    return jsonify([
        {
            'id': c.id, 
            'column_id': c.column_id, 
            'title': c.title, 
            'description': c.description,
            'due_date': c.due_date,
            'priority': c.priority, 
            'position': c.position, 
            'created_at': c.created_at, 
        }
        for c in cards
    ])

@bp.route('/<int:card_id>', methods=['GET'])
@jwt_required()
def get_card(card_id):
    card = Cards.query.get(card_id)
    
    if not card:
        return error_response('Card not found', 400)

    return jsonify(
        {
            'id': card.id, 
            'column_id': card.column_id, 
            'title': card.title, 
            'description': card.description,
            'due_date': card.due_date,
            'priority': card.priority, 
            'position': card.position, 
            'created_at': card.created_at, 
        })

@bp.route('/<int:column_id>', methods=['POST'])
@jwt_required()
def create_card(column_id):
    column = Columns.query.get(column_id)
    
    if not column:
        return error_response('Column not found', 400)
    
    try:
        data = card_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    try:
        data = request.json
        card = Cards(
            title=data['title'], 
            position=data['position'], 
            description=data['description'], 
            due_date=data['due_date'], 
            priority=data['priority'], 
            column_id=column_id)
    
        db.session.add(card)
        db.session.commit()
        return jsonify({'id': card.id, 'title': card.title, 'description': card.description}), 201
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create card: {str(e)}', 500)
        
@bp.route('/<int:card_id>', methods=['PUT'])
@jwt_required()
def update_card(card_id):
    card = Cards.query.get(card_id)
    
    if not card:
        return error_response('Card not found', 404)
    
    if not request.is_json:
        return error_response('Request must be JSON', 400)
    
    data = request.json
    
    if not data:
        return error_response('Request body cannot be empty', 400)
    
    try:
        # Validate column_id if provided
        if 'column_id' in data:
            column_id = data['column_id']
            if not isinstance(column_id, int):
                return error_response('column_id must be an integer', 400)
            
            # Check if column exists
            column = Columns.query.get(column_id)
            if not column:
                return error_response('Column not found', 404)
            
            card.column_id = column_id
        
        # Update other fields
        if 'title' in data:
            title = data['title']
            if not isinstance(title, str):
                return error_response('title must be a string', 400)
            title = title.strip()
            if not title:
                return error_response('title cannot be empty', 400)
            card.title = title
        
        if 'description' in data:
            description = data['description']
            if isinstance(description, str):
                card.description = description.strip()
        
        if 'position' in data:
            position = data['position']
            if not isinstance(position, int):
                return error_response('position must be an integer', 400)
            card.position = position
        
        if 'due_date' in data:
            card.due_date = data['due_date']
        
        if 'priority' in data:
            priority = data['priority']
            if not isinstance(priority, int):
                return error_response('priority must be an integer', 400)
            card.priority = priority
        
        db.session.commit()
        return jsonify({
            'id': card.id,
            'column_id': card.column_id,
            'title': card.title,
            'description': card.description,
            'position': card.position,
            'due_date': card.due_date,
            'priority': card.priority,
            'created_at': card.created_at
        })
    
    except IntegrityError as e:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update card: {str(e)}', 500)

@bp.route('/<int:card_id>', methods=['DELETE'])
@jwt_required()
def delete_card(card_id):
    card = Cards.query.get(card_id)
    
    if not card:
        return error_response('Card not found', 400)
    
    try:
        db.session.delete(card)
        db.session.commit()
        return '', 204
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete card: {str(e)}', 500)
         
def error_response(message, status_code):
    return jsonify({'error': message}), status_code