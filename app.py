from flask import Flask, redirect, render_template, request, session,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate
import re
from flask_bcrypt import Bcrypt 

app = Flask(__name__)
app.secret_key = 'sneaky sneaky'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///duber.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    email = db.Column(db.String(45))
    password = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, server_default = func.now())
    updated_at = db.Column(db.DateTime, server_default = func.now(), onupdate = func.now())
    

    def name(self):
        return self.first_name +" "+ self.last_name

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key = True)
    start = db.Column(db.String(45))
    end = db.Column(db.String(45))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete='cascade'), nullable = False)
    user = db.relationship('User', foreign_keys=[user_id], backref="user_rides")
    created_at = db.Column(db.DateTime, server_default = func.now())
    updated_at = db.Column(db.DateTime, server_default = func.now(), onupdate = func.now())

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/process", methods=['POST'])
def process():
    password = bcrypt.generate_password_hash(request.form['password'])
    print(password)
    
    valid = True
    if len(request.form['first_name']) < 1:
        valid = False
        flash("First name is required")
    if len(request.form['last_name']) < 1:
        valid = False
        flash("Last name is required")
    if not EMAIL_REGEX.match(request.form['email']):
        valid = False
        flash("Invalid Email address!")
    if len(request.form['password']) < 5:
        valid = False
        print("Password must be at least 5 characters")
    if request.form['confirm'] != request.form['password']:
        valid = False
        flash("Passwords must match")
    if request.form['first_name'].isalpha() == False or request.form['last_name'].isalpha() == False:
        valid = False
        flash("Fields must contain no special characters")
    if valid:
        flash("Registration was a success")
        new_user = User(first_name = request.form['first_name'], last_name = request.form['last_name'], email = request.form['email'], password = password)
        db.session.add(new_user)
        db.session.commit()
    return redirect("/")

@app.route("/login", methods=['POST'])
def login():
    result = User.query.filter_by( email = request.form['email'])
    print(result)
    if result:
        if bcrypt.check_password_hash(result[0].password, request.form['password']):
            session['id'] = result[0].id
            session['name'] = result[0].first_name
            session['last'] = result[0].last_name
            flash("login success")
            return redirect("/dashboard")
        else:
            flash("You could not be logged in")
            return redirect("/")
    else:
        flash("Something Went Wrong")
        return redirect("/")

@app.route("/dashboard")
def success():
    if 'id' not in session:
        return redirect("/")
    else: 
        requests = Ride.query.all()        
        return render_template("dashboard.html", requests = requests)

@app.route("/ride", methods=['POST'])
def tweet():
    if len(request.form['start']) < 1 or len(request.form['end']) < 1 or len(request.form['start']) > 45 or len(request.form['end']) > 45 or request.form['start'].isspace() or request.form['end'].isspace():
        flash("Invalid travel request!!")
        return redirect("/dashboard")
    else:        
        new_ride = Ride(start = request.form['start'], end = request.form['end'], user_id = session['id'])
        db.session.add(new_ride)
        db.session.commit()
        return redirect("/dashboard")

@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)