from flask import Flask, redirect, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
# ^ All the needed imports ^

# Initiate imports
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'notimportant'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# Create todo databse
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(10),) 
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Task %r>' % self.id
        

# Create users database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False )

    def __repr__(self):
        return '<User %r>' % self.id

# Register and log-in forms
class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=10,)], render_kw={"placeholder": "name"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=5, max=20)], render_kw={"placeholder": "password"})    

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_name = User.query.filter_by(
            username=username.data).first()
        if existing_user_name:
            raise ValidationError(
                "That name is in use."
            )  

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=3, max=10,)], render_kw={"placeholder": "name"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=5, max=20)], render_kw={"placeholder": "password"})    

    submit = SubmitField("Login")
 
# Login routing and user validation
@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))

    return render_template('login.html', form=form)

# Register routing, user validation and password crypting
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# Dashboard and log-in routing, both require user to be logged in
@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))



# Code for adding new entries
@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content) 
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'there was a problem'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)


# Code for deleting entries
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'Opps, that went wrong :c'


# Code for updating entries
@app.route('/update/<int:id>', methods=['GET','POST'])
@login_required
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except:
            return 'Nothing happened... Seems like I am not functioning properly.'   

    else:
        return render_template('update.html', task=task)


if __name__ == '__main__':
    app.run(debug=True)