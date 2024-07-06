from flask import Flask, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

# Configure Flask app
app = Flask(__name__, static_url_path='/static', static_folder='/Users/oferkorichoner/Desktop/jhon brise/new cours/doom_librarry/static/img')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('/Users/oferkorichoner/Desktop/jhon brise/new cours/doom_librarry/static', 'img')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
CORS(app)  # Enable CORS for all routes

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year_published = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Integer, nullable=False)
    img = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'author': self.author,
            'year_published': self.year_published,
            'type': self.type,
            'img': self.img
        }

# Customer model
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    mail = db.Column(db.String(120), nullable=True, unique=True)
    gender = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'age': self.age,
            'mail': self.mail,
            'gender': self.gender
        }

# Loan model
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    loan_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=False)
    customer = db.relationship('Customer', backref=db.backref('loans', lazy=True))
    book = db.relationship('Book', backref=db.backref('loan_records', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'loan_date': self.loan_date,
            'return_date': self.return_date,
            'customer': self.customer.to_dict() if self.customer else None,
            'book': self.book.to_dict() if self.book else None
        }

# Routes
@app.route('/', methods=['GET'])
def welcome():
    return jsonify({'message': 'Welcome to the Library'})

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.form
    required_fields = ['name', 'author', 'year_published', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing data"}), 400

    if 'img' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['img']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(img_path)
        img_url = url_for('static', filename=f'img/{filename}')
    else:
        return jsonify({"error": "File type not allowed"}), 400

    new_book = Book(
        name=data['name'],
        author=data['author'],
        year_published=data['year_published'],
        type=data['type'],
        img=img_url
    )
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added!'}), 201

@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    return jsonify([book.to_dict() for book in books])

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book.to_dict())

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    for key, value in data.items():
        setattr(book, key, value)
    db.session.commit()
    return jsonify(book.to_dict())

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    Loan.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()
    return '', 204

@app.route('/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])

@app.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify(customer.to_dict())

@app.route('/add_customer', methods=['POST'])
def add_customer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No input data provided'}), 400

    try:
        new_customer = Customer(
            name=data['name'],
            city=data['city'],
            age=data['age'],
            mail=data.get('mail'),
            gender=data['gender']
        )
        db.session.add(new_customer)
        db.session.commit()
        return jsonify(new_customer.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.get_json()
    for key, value in data.items():
        setattr(customer, key, value)
    db.session.commit()
    return jsonify(customer.to_dict())

@app.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return '', 204

@app.route('/loans', methods=['GET'])
def get_loans():
    loans = Loan.query.all()
    formatted_loans = []
    for loan in loans:
        loan_dict = loan.to_dict()
        formatted_loan = {
            'customer_id': loan_dict['customer']['id'] if loan_dict['customer'] else None,
            'customer_name': loan_dict['customer']['name'] if loan_dict['customer'] else 'Unknown',
            'customer_email': loan_dict['customer']['mail'] if loan_dict['customer'] else 'Unknown',
            'book_name': loan_dict['book']['name'] if loan_dict['book'] else 'Unknown',
            'book_id': loan_dict['book']['id'] if loan_dict['book'] else None,
            'loan_date': loan_dict['loan_date'],
            'return_date': loan_dict['return_date']
        }
        formatted_loans.append(formatted_loan)
    return jsonify(formatted_loans)

@app.route('/loans/<email>', methods=['GET'])
def get_loans_by_email(email):
    customer = Customer.query.filter_by(mail=email).first()
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    loans = Loan.query.filter_by(cust_id=customer.id).all()
    formatted_loans = []
    for loan in loans:
        loan_dict = loan.to_dict()
        formatted_loan = {
            'customer_id': loan_dict['customer']['id'],
            'customer_name': loan_dict['customer']['name'],
            'customer_email': loan_dict['customer']['mail'],
            'book_name': loan_dict['book']['name'],
            'book_id': loan_dict['book']['id'],
            'loan_date': loan_dict['loan_date'],
            'return_date': loan_dict['return_date']
        }
        formatted_loans.append(formatted_loan)
    return jsonify(formatted_loans)

@app.route('/add_loan', methods=['POST'])
def add_loan():
    data = request.get_json()
    book_id = data['book_id']
    ongoing_loan = Loan.query.filter_by(book_id=book_id).filter(Loan.return_date >= datetime.now()).first()
    if ongoing_loan:
        return jsonify({'error': 'Book is currently on loan'}), 400

    book = Book.query.get(book_id)
    if book.type == 1:
        max_loan_days = 10
    elif book.type == 2:
        max_loan_days = 5
    elif book.type == 3:
        max_loan_days = 2
    else:
        return jsonify({'error': 'Invalid book type'}), 400

    loan_date = datetime.now()
    return_date = loan_date + timedelta(days=max_loan_days)

    new_loan = Loan(
        cust_id=data['cust_id'],
        book_id=data['book_id'],
        loan_date=loan_date,
        return_date=return_date
    )
    db.session.add(new_loan)
    db.session.commit()
    return jsonify(new_loan.to_dict()), 201

@app.route('/loans/<int:book_id>/return', methods=['PUT'])
def return_loan(book_id):
    loan = Loan.query.filter_by(book_id=book_id).first()
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404
    db.session.delete(loan)
    db.session.commit()
    return jsonify({'message': 'Book returned successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
