from flask import jsonify, request, Blueprint
from app import db
from app.models import Columns,Boards
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity

class ColumnSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    position = fields.Int(required=True)
    
column_schema = ColumnSchema()

bp = Blueprint('columns', __name__, url_prefix='/api/columns')

@bp.route('', methods=['GET'])
@jwt_required()
def get_columns():
    board_id = request.args.get('board_id')
    
    if not board_id:
        return error_response('board_id is missing', 400)
    
    columns = Columns.query.filter_by(board_id=board_id).all()
    return jsonify([
        {'id': c.id, 'board_id': c.board_id, 'position': c.position, 'title': c.title, 'created_at': c.created_at}
        for c in columns
    ])

@bp.route('/<int:column_id>', methods=['GET'])
@jwt_required()
def get_column(column_id):
    column = Columns.query.get(column_id)
    
    if not column:
        return error_response('Column not found', 400)

    return jsonify({'id': column.id, 'board_id': column.board_id, 'title': column.title, 'position': column.position, 'created_at': column.created_at})

@bp.route('/<int:board_id>', methods=['POST'])
@jwt_required()
def create_column(board_id):
    board = Boards.query.get(board_id)
    
    if not board:
        return error_response('Board not found', 400)
    
    try:
        data = column_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    try:
        data = request.json
        column = Columns(title=data['title'], position=data['position'], board_id=board_id)
    
        db.session.add(column)
        db.session.commit()
        return jsonify({'id': column.id, 'title': column.title}), 201
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete column: {str(e)}', 500)
        
@bp.route('/<int:column_id>', methods=['PUT'])
@jwt_required()
def update_column(column_id):
    column = Columns.query.get(column_id)
    
    if not column:
        return error_response('Column not found', 400)
    
    try:
        data = column_schema.load(request.json)  # Validates + cleans
    except ValidationError as err:
        return error_response(err.messages, 400)
    
    try:
        data = request.json
        column.title = data.get('title', column.title)
        column.position = data.get('position', column.position)
        db.session.commit()
        return jsonify({'id': column.id, 'title': column.title, 'position': column.position})
    except IntegrityError:
        db.session.rollback()
        return error_response(f'Database error: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to update column: {str(e)}', 500)

@bp.route('/<int:column_id>', methods=['DELETE'])
@jwt_required()
def delete_column(column_id):
    column = Columns.query.get(column_id)
    
    if not column:
        return error_response('Column not found', 400)
    
    try:
        db.session.delete(column)
        db.session.commit()
        return '', 204
    except IntegrityError as e:
        db.session.rollback()
        return error_response(f'Cannot delete column with cards: {str(e)}', 400)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to delete column: {str(e)}', 500)
         
def error_response(message, status_code):
    return jsonify({'error': message}), status_code