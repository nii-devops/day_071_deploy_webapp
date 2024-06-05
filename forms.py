from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title       = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle    = StringField("Subtitle", validators=[DataRequired()])
    img_url     = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body        = CKEditorField("Blog Content", validators=[DataRequired()])
    submit      = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    f_name      = StringField(label='First name(s)', validators=[DataRequired()])
    l_name      = StringField(label='Last name', validators=[DataRequired()])
    email       = EmailField(label='Email', validators=[DataRequired()])
    password    = PasswordField(label='Password', validators=[DataRequired()])
    submit      = SubmitField("Register")


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email       = EmailField(label='Email', validators=[DataRequired()])
    password    = PasswordField(label='Password', validators=[DataRequired()])
    submit      = SubmitField("Login")


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    text    = CKEditorField("Post Comment", validators=[DataRequired()])
    submit  = SubmitField("Submit Comment")

