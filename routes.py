import os
import json
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Document, ChatSession, ChatMessage
from document_processor import DocumentProcessor
from rag_engine import RAGEngine
from utils import allowed_file, get_file_type

# Initialize processors
document_processor = DocumentProcessor()
rag_engine = RAGEngine()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/chat')
@login_required
def chat():
    # Get user's chat sessions
    chat_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    
    # Get current session or create new one
    session_id = request.args.get('session_id')
    if session_id:
        current_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not current_session:
            current_session = ChatSession(user_id=current_user.id)
            db.session.add(current_session)
            db.session.commit()
    else:
        current_session = ChatSession(user_id=current_user.id)
        db.session.add(current_session)
        db.session.commit()
    
    # Get messages for current session
    messages = ChatMessage.query.filter_by(session_id=current_session.id).order_by(ChatMessage.timestamp.asc()).all()
    
    # Get user's documents
    documents = Document.query.filter_by(user_id=current_user.id, processed=True).all()
    
    return render_template('chat.html', 
                         chat_sessions=chat_sessions,
                         current_session=current_session,
                         messages=messages,
                         documents=documents)

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files selected'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                       f"{current_user.id}_{filename}")
                
                # Save file
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                
                # Create document record
                document = Document(
                    filename=f"{current_user.id}_{filename}",
                    original_filename=filename,
                    file_path=file_path,
                    file_type=get_file_type(filename),
                    file_size=file_size,
                    user_id=current_user.id
                )
                
                db.session.add(document)
                db.session.commit()
                
                # Process document in background (simplified for demo)
                try:
                    text_content = document_processor.extract_text(file_path, document.file_type)
                    document.text_content = text_content
                    
                    # Create chunks and embeddings
                    chunks = document_processor.create_chunks(text_content)
                    document.chunk_count = len(chunks)
                    
                    # Store in vector database
                    rag_engine.add_document(document.id, chunks)
                    
                    document.processed = True
                    db.session.commit()
                    
                    uploaded_files.append({
                        'id': document.id,
                        'filename': document.original_filename,
                        'size': document.file_size,
                        'processed': True
                    })
                    
                except Exception as e:
                    logging.error(f"Document processing error: {e}")
                    document.processed = False
                    db.session.commit()
                    uploaded_files.append({
                        'id': document.id,
                        'filename': document.original_filename,
                        'size': document.file_size,
                        'processed': False,
                        'error': str(e)
                    })
            else:
                return jsonify({'error': f'File type not allowed: {file.filename}'}), 400
        
        return jsonify({'files': uploaded_files})
        
    except Exception as e:
        logging.error(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/ask', methods=['POST'])
@login_required
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question')
        session_id = data.get('session_id')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Get or create chat session
        chat_session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not chat_session:
            chat_session = ChatSession(user_id=current_user.id)
            db.session.add(chat_session)
            db.session.commit()
        
        # Save user message
        user_message = ChatMessage(
            content=question,
            message_type='user',
            session_id=chat_session.id
        )
        db.session.add(user_message)
        
        # Get answer from RAG engine
        response_data = rag_engine.answer_question(question, current_user.id)
        answer = response_data['answer']
        context_docs = response_data.get('context_documents', [])
        
        # Save assistant message
        assistant_message = ChatMessage(
            content=answer,
            message_type='assistant',
            session_id=chat_session.id,
            context_used=json.dumps(context_docs)
        )
        db.session.add(assistant_message)
        
        # Update session timestamp
        chat_session.updated_at = db.func.now()
        db.session.commit()
        
        return jsonify({
            'answer': answer,
            'context_documents': context_docs,
            'message_id': assistant_message.id
        })
        
    except Exception as e:
        logging.error(f"Question answering error: {e}")
        return jsonify({'error': 'Failed to process question'}), 500

@app.route('/new_session', methods=['POST'])
@login_required
def new_session():
    try:
        session_name = request.json.get('name', 'New Chat')
        
        chat_session = ChatSession(
            session_name=session_name,
            user_id=current_user.id
        )
        db.session.add(chat_session)
        db.session.commit()
        
        return jsonify({
            'session_id': chat_session.id,
            'session_name': chat_session.session_name
        })
        
    except Exception as e:
        logging.error(f"New session error: {e}")
        return jsonify({'error': 'Failed to create session'}), 500

@app.route('/delete_document/<int:doc_id>', methods=['DELETE'])
@login_required
def delete_document(doc_id):
    try:
        document = Document.query.filter_by(id=doc_id, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Remove from vector store
        rag_engine.remove_document(doc_id)
        
        # Delete file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Delete document error: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
