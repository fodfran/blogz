from flask import request, redirect, render_template, session, flash, url_for
import cgi
import re

from app import app, db
from models import User, Blog
from hashutils import check_pw_hash

app.secret_key = '5252008'


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

        if not check_pw_hash(user_password, user.pw_hash):
            flash("User password is incorrect", "error")
            return redirect("/login")
        
        if user and check_pw_hash(user_password, user.pw_hash):
            session['username'] = user_username
            flash("Logged in successfully!")
            return redirect("/newpost") 
            
    return render_template("login.html", title = "Log In", lo_status="active")

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

    return render_template("register.html", title = "Register", re_status="active")

@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    return redirect('/login')


@app.route("/blog/<int:page_num>")
def blog(page_num):
    encoded_username = request.args.get("user")
    user_bloglist = []

    encoded_blog_id = request.args.get("id")
    blog = ""
    header_title = "All Blogz"

    if encoded_username:
        user = User.query.filter_by(username = encoded_username).first()
        user_bloglist = Blog.query.filter_by(owner = user).order_by(Blog.pub_date.desc()).paginate(per_page=5, page=page_num, error_out=False)
        header_title = user.username + "'s Blog"
    
    if encoded_blog_id:
        blog = Blog.query.get(int(encoded_blog_id))
        header_title = blog.title

    return render_template('blog.html', bloglist = Blog.query.order_by(Blog.pub_date.desc()).paginate(per_page=5, page=page_num, error_out=False), title = header_title, 
        blog = blog, blog_id = encoded_blog_id and cgi.escape(encoded_blog_id, quote=True), 
        user_bloglist = user_bloglist, blog_user = encoded_username and cgi.escape(encoded_username, quote=True), bl_status="active")

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

        return redirect("/blog/1?id=" + str(new_blog.id))

    return render_template('newpost.html', title = "New Entry", blog_owner = blog_owner, ne_status="active")

@app.route("/")
def index():  
    return render_template("index.html", userlist = User.query.all(), title="Blogz", ho_status="active")

if __name__ == '__main__':
    app.run()