from flask_socketio import SocketIO, emit, join_room
from flask import request
from models import Messages, User, db
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    print(f'Client joined room: {room}')

@socketio.on('private_message')
def handle_private_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message_content = data['message']
    
    # Create a unique room name for the chat (smaller ID first)
    room = f"chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"
    
    # Save message to database
    new_message = Messages(
        sender_id=sender_id,
        receiver_id=receiver_id,
        messages=message_content,
        created_at=datetime.utcnow()
    )
    db.session.add(new_message)
    db.session.commit()
    
    # Emit the message to the room
    emit('new_message', {
        'id': new_message.id,
        'sender_id': sender_id,
        'message': message_content,
        'created_at': new_message.created_at.isoformat()
    }, room=room)
