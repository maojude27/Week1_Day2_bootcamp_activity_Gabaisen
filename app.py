# app.py
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here_please_change_this_in_production'

DATABASE = 'database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            print(f"Disconnected from database: {self.db_path}")

    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    birthday TEXT,
                    address TEXT,
                    image_url TEXT
                )
            ''')
            self.conn.commit()
            print("User table checked/created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()

    def add_user(self, username, password_hash, name, birthday, address, image_url=None):
        try:
            self.cursor.execute(
                'INSERT INTO users (username, password, name, birthday, address, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                (username, password_hash, name, birthday, address, image_url)
            )
            self.conn.commit()
            print(f"User '{username}' added successfully.")
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            print(f"Error adding user '{username}': Username already exists.")
            raise e
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"Error adding user '{username}': {e}")
            raise e

    def get_user_by_username(self, username):
        self.cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return self.cursor.fetchone()

    def get_user_by_id(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return self.cursor.fetchone()

def get_db_instance():
    db_instance = getattr(g, '_database_instance', None)
    if db_instance is None:
        db_instance = g._database_instance = Database(DATABASE)
    return db_instance

@app.teardown_appcontext
def close_db_connection(exception):
    db_instance = getattr(g, '_database_instance', None)
    if db_instance is not None:
        db_instance.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

@app.route('/register', methods=('GET', 'POST'))
def register():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        birthday = request.form.get('birthday')
        address = request.form.get('address')
        image = request.files.get('image')

        image_url = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/static/uploads/{filename}'

        db = get_db_instance()
        existing_user = db.get_user_by_username(username)

        if existing_user:
            message = 'Username already exists!'
        elif not username or not password or not name:
            message = 'Please fill out username, password, and name fields!'
        else:
            hashed_password = generate_password_hash(password)
            try:
                db.add_user(username, hashed_password, name, birthday, address, image_url)
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                message = 'Username already exists (Integrity Error).'
            except Exception as e:
                message = f'An error occurred during registration: {e}'

    return render_template('register.html', message=message)

@app.route('/login', methods=('GET', 'POST'))
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db_instance()
        user = db.get_user_by_username(username)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('profile'))
        else:
            message = 'Incorrect username or password!'

    return render_template('login.html', message=message)

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        db = get_db_instance()
        user_data = db.get_user_by_id(user_id)

        if user_data:
            # Convert birthday to age
            try:
                birth_year = int(user_data['birthday'][:4])  # assumes 'YYYY-MM-DD' or 'YYYY'
                current_year = datetime.now().year
                age = current_year - birth_year
            except Exception:
                age = 'N/A'  # fallback if birthday is malformed

            return render_template('profile.html', user=user_data, age=age)
        else:
            session.pop('user_id', None)
            session.pop('username', None)
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('templates', exist_ok=True)

    if not os.path.exists(DATABASE):
        print(f"Database '{DATABASE}' not found, initializing and creating tables...")
        temp_db = Database(DATABASE)
        temp_db.create_tables()
        temp_db.close()
    else:
        print(f"Database '{DATABASE}' already exists. Ensuring tables are present...")
        temp_db = Database(DATABASE)
        temp_db.create_tables()
        temp_db.close()

    app.run(debug=True)