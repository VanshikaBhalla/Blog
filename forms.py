from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, email
from flask_ckeditor import CKEditorField


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class CommentForm(FlaskForm):
    comment = StringField("Comment", validators=[DataRequired()])
    submit = SubmitField("Add comment")


class RegisterForm(FlaskForm):
    email = EmailField(label="email", validators=[DataRequired(message="fields can't be empty!"), email(check_deliverability=True)])
    name = StringField(label="name", validators=[DataRequired(message="fields can't be empty!")])
    password = PasswordField(label="password", validators=[DataRequired(message="fields can't be empty!")])
    submit = SubmitField(label="Register")


class LoginForm(FlaskForm):
    email = EmailField(label="email", validators=[DataRequired(message="fields can't be empty!"), email(check_deliverability=True)])
    password = PasswordField(label="password", validators=[DataRequired(message="fields can't be empty!")])
    submit = SubmitField(label="Login")


