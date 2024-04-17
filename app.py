from flask import Flask, render_template, url_for, redirect, session, request
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, length, ValidationError
from flask_bcrypt import Bcrypt # use to harsh passwords
from sqlalchemy import Date
from datetime import datetime
from school import graded, reg_validator

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3' # connect to the db file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey' # secret key used to secure a session cookie
db = SQLAlchemy(app) # database instance
app.app_context().push()
bcrypt = Bcrypt(app)

app.config["SESSION_PERMANENT"] = False #treated as a session cookie, the momment you quit your browser, the session will be deleted.
app.config["SESSION_TYPE"] = "filesystem" # ensures contents of lecturer information is stored in the server files and not the cookie itself for PRIVACY.
Session(app) # activating the session

login_manager = LoginManager() # handles login: loading users from IDs etc
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(lecturer_id):
    return Lecturer.query.get(int(lecturer_id))

@login_manager.user_loader
def load_user(student_id):
    return Student.query.get(int(student_id))

# database table

# student
class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

# lecturer table
class Lecturer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    gradings = db.relationship('Grading', backref='Lecturer') # lecturer can grade many students
    units = db.relationship('Units', backref='Lecturer') # lecturer can have many units
    lecturer_info = db.relationship('Lecturer_info', back_populates='lecturer', uselist=False, cascade='all, delete-orphan')

# more lecturer information
class Lecturer_info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    national_id = db.Column(db.String(20), nullable=False, unique=True)
    phone_number = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(20), nullable=False, unique=True)
    gender = db.Column(db.String(10))
    birth_date = db.Column(Date)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'), nullable=False, unique=True) # one to one relationship
    lecturer = db.relationship('Lecturer', back_populates='lecturer_info')

# Grading table
class Grading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_no = db.Column(db.String(20), nullable=False)
    cat = db.Column(db.Integer)
    finals = db.Column(db.Integer)
    total = db.Column(db.Integer)
    final_grade = db.Column(db.String(5))
    # foreign key
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id'))

# units
class Units(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_code = db.Column(db.String(20), nullable=False)
    unit_name = db.Column(db.String(80), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturer.id')) #foreign key

class SignupForm(FlaskForm):
    username = StringField(validators=[InputRequired(), length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), length(min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Signup")

    def validate_username(self, username):
        existing_user_username = Lecturer.query.filter_by(username=username.data).first()

        if existing_user_username:
            raise ValidationError("That username already Exists. Please choose a different one")
        
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), length(min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        lecturer = Lecturer.query.filter_by(username=form.username.data).first() # check if user exists
        student = Student.query.filter_by(username=form.username.data).first()
        session['username'] = form.username.data
        # If they are, check their password hash
        if lecturer:
            if bcrypt.check_password_hash(lecturer.password, form.password.data):
                session["username"] = form.username.data
                login_user(lecturer)
                return redirect(url_for('lecturer'))
        elif student:
            if bcrypt.check_password_hash(student.password, form.password.data):
                session["username"] = form.username.data
                login_user(student)
                return redirect(url_for('student'))
        else:
            return f"User Not found"
    return render_template('login.html', form=form)

@app.route("/logout", methods=['GET', 'POST'])
@login_required # to logout, you have to be logged in
def logout():
    session.pop('username', None)
    logout_user()
    return redirect(url_for('login'))

# lecturer dashboard
@app.route("/lecturer", methods=['GET', 'POST'])
@login_required
def lecturer():
    username = session.get('username')
    if username:
        return render_template('lecturer.html', username=username)
    else:
        return "Not logged in"

# lecturer dashboard
@app.route("/student", methods=['GET', 'POST'])
@login_required
def student():
    username = session.get('username')
    if username:
        return render_template('student.html', username=username)
    else:
        return "Not logged in"

# SIGNUP
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = Lecturer(username=form.username.data, password=hashed_password)
        std_user=form.username.data
        if reg_validator(std_user):
            new_student = Student(username=std_user, password=hashed_password)
            if new_student:
                db.session.add(new_student)
        else:
            db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

# LOGIN
@app.route("/grading", methods=['GET', 'POST'])
@login_required
def grading():
    username = session.get('username')
    user = Lecturer.query.filter_by(username=username).first() # used to get the lecturer in the current session so as to get their id later on
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        cat = request.form["cat"]
        finals = request.form["finals"]
        total = int(cat) + int(finals)
        final_grade = graded(total)
        lecturer_id = user.id # retrieving lecturer id
        new_grade = Grading(reg_no=reg_no, cat=cat, finals=finals, total=total, final_grade=final_grade, lecturer_id=lecturer_id)
        db.session.add(new_grade)
        db.session.commit()
        return redirect(url_for("grading"))
    else:
        username = session.get('username')
        id = session.get('id')
        return render_template('grading.html', username=username, id=id)

# LECTURER PROFILE
@app.route("/lecturer_information", methods=['GET', 'POST'])
@login_required
def lecturer_information():
    username = session.get('username')
    user = Lecturer.query.filter_by(username=username).first() # used to get the lecturer in the current
    if request.method == "POST":
        national_id = request.form["national_id"]
        phone_number = request.form["phone_number"]
        email = request.form["email"]
        gender = request.form["gender"]
        birth_date = request.form["birth_date"]
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d')
        lecturer_id = user.id # retrieving lecturer id
        lec_info = Lecturer_info(national_id=national_id, phone_number=phone_number, email=email, gender=gender, birth_date=birth_date, lecturer_id=lecturer_id)
        db.session.add(lec_info)
        db.session.commit()
        return redirect(url_for("lecturer"))
    else:
        return render_template("lecturer_info.html")

@app.route("/performance_report", methods=['GET', 'POST'])
@login_required
def performance_report():
    username = session.get('username')
    user = Lecturer.query.filter_by(username=username).first()
    # performance = Grading.query.all()
    performance = Grading.query.filter_by(lecturer_id=user.id)
    return render_template('performance_report.html', performance=performance)

@app.route("/single_student_performance", methods=['GET', 'POST'])
@login_required
def single_student_performance():
    if request.method == "POST":
        reg_no = request.form["reg_no"]
        performance = Grading.query.filter_by(reg_no=reg_no).first()
        return render_template("single_student_performance.html", performance=performance)
    else:
        return redirect(url_for("performance_report"))
    
@app.route("/teaching_units", methods=['GET', 'POST'])
@login_required
def teaching_units():
    username = session.get('username')
    user = Lecturer.query.filter_by(username=username).first() # used to get the lecturer in the current
    if request.method == "POST":
        unit_code = request.form["unit_code"]
        unit_name = request.form["unit_name"]
        lecturer_id = user.id # retrieving lecturer id
        new_unit = Units(unit_code=unit_code, unit_name=unit_name, lecturer_id=lecturer_id)
        db.session.add(new_unit)
        db.session.commit()
        return redirect(url_for("lecturer"))
    else:
        return render_template("units.html")

@app.route('/about')
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)

