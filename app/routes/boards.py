from flask import jsonify, request, Blueprint
from app import db
from app.models import Boards, Columns, Cards
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity

class BoardSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    
board_schema = BoardSchema()

bp = Blueprint('boards', __name__, url_prefix='/api/boards')

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get all boards with columns and cards for the authenticated user"""
    user_id = int(get_jwt_identity())
    
    try:
        # Fetch all boards for the user
        boards = Boards.query.filter_by(user_id=user_id).all()
        
        if not boards:
            return jsonify([]), 200
        
        dashboard_data = []
        
        for board in boards:
            # Fetch columns for this board
            columns = Columns.query.filter_by(board_id=board.id).order_by(Columns.position).all()
            
            columns_data = []
            for column in columns:
                # Fetch cards for this column
                cards = Cards.query.filter_by(column_id=column.id).order_by(Cards.position).all()
                
                cards_data = [
                    {
                        'id': card.id,
                        'title': card.title,
                        'description': card.description,
                        'due_date': card.due_date.isoformat() if card.due_date else None,
                        'priority': card.priority,
                        'position': card.position,
                        'created_at': card.created_at.isoformat() if card.created_at else None
                    }
                    for card in cards
                ]
                
                columns_data.append({
                    'id': column.id,
                    'title': column.title,
                    'position': column.position,
                    'created_at': column.created_at.isoformat() if column.created_at else None,
                    'cards': cards_data
                })
            
            dashboard_data.append({
                'id': board.id,
                'title': board.title,
                'created_at': board.created_at.isoformat() if board.created_at else None,
                'columns': columns_data
            })
        
        return jsonify(dashboard_data), 200
    
    except Exception as e:
        return error_response(f'Failed to fetch dashboard: {str(e)}', 500)
    
@bp.route('', methods=['GET'])
@jwt_required()
def get_boards():
    user_id = get_jwt_identity()  # Get from JWT token
    
    # Convert back to integer
    try:
        user_id = int(user_id)
    except ValueError:
        return error_response('Invalid user_id in token', 400)

    boards = Boards.query.filter_by(user_id=user_id).all()
    return jsonify([
        {'id': b.id, 'title': b.title, 'created_at': b.created_at}
        for b in boards
    ])

@bp.route('/<int:board_id>', methods=['GET'])
@jwt_required()
def get_board(board_id):

    user_id = int(get_jwt_identity())
    
    try:
        # Fetch board by user_id and board_id
        board = Boards.query.filter_by(user_id=user_id, id=board_id).first()
        
        if not board:
            return error_response('Board not found', 400)
        
      
        # Fetch columns for this board
        columns = Columns.query.filter_by(board_id=board.id).order_by(Columns.position).all()
            
        columns_data = []
        for column in columns:
            # Fetch cards for this column
            cards = Cards.query.filter_by(column_id=column.id).order_by(Cards.position).all()
                
            cards_data = [
                {
                    'id': card.id,
                    'title': card.title,
                    'description': card.description,
                    'due_date': card.due_date.isoformat() if card.due_date else None,
                    'priority': card.priority,
                    'position': card.position,
                    'created_at': card.created_at.isoformat() if card.created_at else None
                }
                for card in cards
            ]
                
            columns_data.append({
                'id': column.id,
                'title': column.title,
                'position': column.position,
                'created_at': column.created_at.isoformat() if column.created_at else None,
                'cards': cards_data
            })
            
        dashboard_data = {
            'id': board.id,
            'title': board.title,
            'created_at': board.created_at.isoformat() if board.created_at else None,
            'columns': columns_data
        }
            
        return jsonify(dashboard_data), 200
    
    except Exception as e:
        return error_response(f'Failed to fetch dashboard: {str(e)}', 500)
    



@bp.route('', methods=['POST'])
@jwt_required()
def create_board():
    user_id = get_jwt_identity()  # Get from JWT token
    
    if not user_id:
        return error_response('user_id not found', 400)
    
    try:
        data = board_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    try:
        data = request.json
        board = Boards(title=data['title'], user_id=user_id)
    
        db.session.add(board)
        db.session.commit()
        return jsonify({'id': board.id, 'title': board.title}), 201
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to create bord: {str(e)}', 500)
    
        
@bp.route('/<int:board_id>', methods=['PUT'])
@jwt_required()
def update_board(board_id):
    board = Boards.query.get(board_id)
    
    if not board:
        return error_response('Board not found', 400)
    
    try:
        data = board_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    try:
        data = request.json
        board.title = data.get('title', board.title)
        db.session.commit()
        return jsonify({'id': board.id, 'title': board.title})
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update board: {str(e)}', 500)

@bp.route('/<int:board_id>', methods=['DELETE'])
@jwt_required()
def delete_board(board_id):
    board = Boards.query.get(board_id)
    
    if not board:
        return error_response('Board not found', 400)
    
    try:
        db.session.delete(board)
        db.session.commit()
        return '', 204
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete board: {str(e)}', 500)
         
def error_response(message, status_code):
    return jsonify({'error': message}), status_code