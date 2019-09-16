from flask import Flask, request, redirect, render_template, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import cgi
import re

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = '5252008'

class Blog(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.String(10000))
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect("/login")


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_username = request.form['username']
        user_password = request.form['password']
        user = User.query.filter_by(username=user_username).first()
        
        if not user:
            flash("User does not exist", "error")
            return redirect("/login")

        if user.password != user_password:
            flash("User password is incorrect", "error")
            return redirect("/login")
        
        if user and user.password == user_password:
            session['username'] = user_username
            flash("Logged in successfully!")
            return redirect("/newpost") 
            
    return render_template("login.html", title = "Log In")

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_username = request.form['username']
        user_password = request.form['password']
        user_verify = request.form['verify']

        if not re.match(r"^\w{3,20}$", user_username):
            flash("That's not a valid username", "error")
        if not re.match(r"^\w{3,20}$", user_password):
            flash("That's not a valid password", "error")
        if user_password != user_verify:
            flash("Passwords don't match", "error")
        if re.match(r"^\w{3,20}$", user_username) and re.match(r"^\w{3,20}$", user_password) and user_password == user_verify:
            existing_user = User.query.filter_by(username=user_username).first()
            if not existing_user:
                new_user = User(user_username, user_password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = user_username
                flash("Registration complete!")
                return redirect("/newpost")
            else:
                flash("This user already exists", "error")

    return render_template("register.html", title = "Register")

@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    return redirect('/login')


@app.route("/blog")
def blog():
    encoded_username = request.args.get("user")
    user_bloglist = []

    encoded_blog_id = request.args.get("id")
    blog = ""
    header_title = "All Blogz"

    if encoded_username:
        user = User.query.filter_by(username = encoded_username).first()
        user_bloglist = Blog.query.filter_by(owner = user).all()
        header_title = user.username + "'s Blog"
    
    if encoded_blog_id:
        blog = Blog.query.get(int(encoded_blog_id))
        header_title = blog.title

    return render_template('blog.html', bloglist = Blog.query.all(), title = header_title, 
        blog = blog, blog_id = encoded_blog_id and cgi.escape(encoded_blog_id, quote=True), 
        user_bloglist = user_bloglist, blog_user = encoded_username and cgi.escape(encoded_username, quote=True))

@app.route("/newpost", methods = ['POST', 'GET'])
def add_post():
    blog_owner = User.query.filter_by(username = session['username']).first()

    title_error = ""
    body_error = ""
    if request.method == 'POST':
        
        blog_title = request.form['title']
        blog_body = request.form['body']
        

        if (not blog_title) or (blog_title.strip() == ""):
            title_error = "Please fill in the title"
        if (not blog_body) or (blog_body.strip() == ""):
            body_error = "Please fill in the body"

        if title_error or body_error:
            return render_template('newpost.html', title = "New Entry", blog_owner = blog_owner, title_error=title_error, body_error=body_error)

        new_blog = Blog(blog_title, blog_body, blog_owner)
        db.session.add(new_blog)
        db.session.commit()

        return redirect("/blog?id=" + str(new_blog.id))

    return render_template('newpost.html', title = "New Entry", blog_owner = blog_owner)

@app.route("/")
def index():  
    return render_template("index.html", userlist = User.query.all(), title="Blogz")

if __name__ == '__main__':
    app.run()