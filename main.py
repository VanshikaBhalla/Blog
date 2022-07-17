from flask import Flask, render_template, redirect, url_for, flash, abort
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from sqlalchemy.orm import relationship
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from datetime import date
import os

date = date.today()

# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user is not None:
            if current_user.id != 1:
                return abort(403)
            # Otherwise, continue with the route function
            return f(*args, **kwargs)
        else:
            return redirect(url_for('.login'))
    return decorated_function


# Delete this code:
# import requests
# posts = requests.get("https://api.npoint.io/43644ec4f0013682fc0d").json()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=int(user_id)).first()
    return user


gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False,
                    use_ssl=False, base_url=None)
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///posts.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # Create reference to the User object, the "posts" refers to the 'posts' property in the User class.
    author = relationship("User", back_populates="posts")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # ***************Parent Relationship*************#
    comments = relationship("Comment", back_populates="parent_post")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    # This will act like a List of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

    # *******Add parent relationship*******#
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    # *******Add child relationship*******#
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    # ***************Child Relationship*************#
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


# db.create_all()

posts = BlogPost.query.all()

# for i in range(BlogPost.query.count()+1):
#     blog = BlogPost.query.filter_by(id=i).first()
#     if blog:
#         blog_dict = {'id': blog.id, 'date': blog.date, 'title': blog.title, 'body': blog.body,
#                      'subtitle': blog.subtitle, 'author': blog.author, 'img_url': blog.img_url}
#         posts.append(blog_dict)
#     else:
#         pass


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("you're already registered to the site, login instead!")
            return redirect(url_for('.login'))
        else:
            new_user = User(name=form.name.data, email=form.email.data,
                            password=generate_password_hash(password=form.password.data, method='pbkdf2:sha256',
                                                            salt_length=8))
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            return redirect(url_for('.get_all_posts'))

    return render_template("register.html", form=form, year=date.year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("logged in, successfully!")
                return redirect(url_for('.get_all_posts'))
            else:
                flash('invalid password!')
                return redirect(url_for('.login'))
        else:
            flash("you aren't registered to this site, register instead!")
            return redirect(url_for('.register'))

    return render_template("login.html", form=form, year=date.year)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.get_all_posts'))


@app.route('/', methods=['GET', 'POST'])
def get_all_posts():
    return render_template("index.html", all_posts=posts, year=date.year)


@app.route("/post/<int:index>", methods=['GET', 'POST'])
@login_required
def show_post(index):

    requested_post = None
    for blog_post in posts:
        if blog_post.id == index:
            requested_post = blog_post
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        new_comment = Comment(comment_author=current_user, parent_post=BlogPost.query.filter_by(id=index).first(), text=form.comment.data)
        db.session.add(new_comment)
        db.session.commit()
        form.comment.data = ""
        return redirect(url_for('.show_post', index=index))
    return render_template("post.html", post=requested_post, current_user=current_user, year=date.year, form=form, post_comments=Comment.query.filter_by(post_id=index).all())


@app.route('/new-post', methods=['POST', 'GET'])
@admin_only
def new_post():
    new_post_form = CreatePostForm()
    if new_post_form.validate_on_submit():
        post = BlogPost(title=new_post_form.title.data, subtitle=new_post_form.subtitle.data, body=new_post_form.body.data,
                        img_url=new_post_form.img_url.data, date=date.strftime("%B %d, %Y"), author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.get_all_posts'))
    return render_template('make-post.html', form=new_post_form, current_user=current_user, year=date.year)


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post_to_be_edited = BlogPost.query.filter_by(id=post_id).first()
    edit_form = CreatePostForm(title=post_to_be_edited.title, subtitle=post_to_be_edited.subtitle, body=post_to_be_edited.body,
                               author=post_to_be_edited.author, img_url=post_to_be_edited.img_url)
    if edit_form.validate_on_submit():
        post_to_be_edited.title = edit_form.title.data
        post_to_be_edited.subtitle = edit_form.subtitle.data
        post_to_be_edited.img_url = edit_form.img_url.data
        post_to_be_edited.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('.show_post', index=post_to_be_edited.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user, year=date.year)


@app.route('/delete/<int:post_id>')
@admin_only
def delete(post_id):
    BlogPost.query.filter_by(id=post_id).delete()
    db.session.commit()

    return redirect(url_for('.get_all_posts'))


@app.route('/delete_comment/<int:post_id>/<int:comment_id>')
@login_required
def delete_comment(comment_id, post_id):
    Comment.query.filter_by(id=comment_id).delete()
    db.session.commit()

    return redirect(url_for('.show_post', index=post_id))


@app.route("/about")
def about():
    return render_template("about.html", year=date.year)


@app.route("/contact")
def contact():
    return render_template("contact.html", year=date.year)


if __name__ == "__main__":
    app.run(debug=True)
