from flask import Flask, request, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
import cgi

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: the connection string after :// contains the following info:
# user:password@server:portNumber/databaseName

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:SHINee5252008@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = False
db = SQLAlchemy(app)

class Blog(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    body = db.Column(db.String(10000))

    def __init__(self, title, body):
        self.title = title
        self.body = body


@app.route("/blog")
def index():
    encoded_blog_id = request.args.get("id")
    blog_title = ""
    blog_body = ""
    header_title = "Build A Blog"

    if encoded_blog_id:
        blog = Blog.query.get(int(encoded_blog_id))
        blog_title = blog.title
        blog_body = blog.body
        header_title = blog_title

    return render_template('blog.html', bloglist = Blog.query.all(), title = header_title, blog_title=blog_title, blog_body=blog_body, blog_id = encoded_blog_id and cgi.escape(encoded_blog_id, quote=True))

@app.route("/newpost", methods = ['POST', 'GET'])
def add_post():
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
            return render_template('newpost.html', title = "Add Blog Entry", title_error=title_error, body_error=body_error)

        new_blog = Blog(blog_title, blog_body)
        db.session.add(new_blog)
        db.session.commit()

        return redirect("/blog?id=" + str(new_blog.id))

    return render_template('newpost.html', title = "Add Blog Entry")

if __name__ == '__main__':
    app.run()