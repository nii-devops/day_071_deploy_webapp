import os
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Import your forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from time import sleep
from typing import List

from dotenv import load_dotenv, dotenv_values
load_dotenv()



'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
#app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")

ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URI")

db = SQLAlchemy(model_class=Base)
db.init_app(app)


# #######################################
# <-------- CONFIGURE TABLES ---------->
# #######################################

# TODO: Create a User table for all your registered users. 
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    f_name: Mapped[str] = mapped_column(String(80), nullable=False)
    l_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    posts = relationship("BlogPost", back_populates="author", cascade='all, delete')
    comments = relationship("Comment", back_populates="comment_author", cascade='all, delete')


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates='posts')

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # Parent relationship between with Comments
    comments = relationship("Comment", back_populates='parent_post', cascade='all, delete')


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ##### <----- Child relationship with User (parent) ----> #######
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    comment_author = relationship("User", back_populates="comments")
    
    # ####### <----- Child relationship with BlogPost (parent) ----> #######
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('blog_posts.id'))
    parent_post = relationship('BlogPost', back_populates="comments")

    text: Mapped[str] = mapped_column(Text, nullable=False)





with app.app_context():
    db.create_all()


#Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)        
    return decorated_function


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['get', 'post'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user_email = register_form.email.data
        password = register_form.password.data
        result = db.session.execute(db.select(User).where(User.email==user_email))
        user = result.scalar()
        if user:
            flash(f"User with email ({user_email}) exists.", category='warning')
            return redirect(url_for('login'))

        else:
            hashed_passwd = generate_password_hash(password, method='scrypt', salt_length=8)
            new_user = User(
                f_name=register_form.f_name.data,
                l_name=register_form.l_name.data,
                email=user_email,
                password=hashed_passwd,
            )
            # Write data to DB
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully.', category='success')
            login_user(new_user)
            return redirect(url_for('get_all_posts'))

    return render_template("register.html", form=register_form)


# TODO: Retrieve a user from the database based on their email. 
@app.route('/login', methods=['get', 'post'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        # Check if user exists.
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        if user:
            # Check if Password matches that in DB
            if check_password_hash(user.password, password):
                login_user(user)
                # flash("Login successful. Redirecting...", category='success')
                sleep(2)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Wrong password! Try again.", category='danger')
        else:
            flash(f"User with email ({email}) does not exist. Register user.", category='danger')
            return redirect(url_for('register'))

    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=['get', 'post'])
@login_required
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Instantiate CommentForm
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        commenter_email = current_user.email
        if not current_user.is_authenticated:
            flash("Submission failed! You need to login or register to comment.", category='warning')
        else:
            new_comment = Comment(
                text=(comment_form.text.data).replace("<p>", "").replace("</p>", ""),
                comment_author = current_user,
                parent_post = requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for('show_post', post_id=post_id))
    result = db.session.execute(db.select(Comment).where(Comment.post_id==post_id))
    comments = result.scalars().all()

    return render_template("post.html",post=requested_post, current_user=current_user, form=comment_form, comments=comments)


# TODO: Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# TODO: Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
#@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )

    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# TODO: Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/purge-database")
def purge_db():
    result = db.session.execute(db.select(User).order_by(User.id))
    users = result.scalars().all()
    for user in users:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/users")
def users():
    result = db.session.execute(db.select(User).order_by(User.id))
    all_users = result.scalars().all()
    return render_template("users.html", users=all_users)


if __name__ == "__main__":
    app.run(debug=False, port=5002)
