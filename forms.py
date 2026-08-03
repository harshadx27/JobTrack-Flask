from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    DateField,
    TextAreaField,
    SelectField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Optional,
    URL,
    Email,
    Length,
    EqualTo,
    NumberRange,
)
from flask_wtf.file import FileField, FileAllowed


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8)]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class JobApplicationForm(FlaskForm):

    company = StringField("Company", validators=[DataRequired()])

    role = StringField("Role", validators=[DataRequired()])

    location = StringField("Location", validators=[Optional()])

    platform = StringField("Platform", validators=[Optional()])

    job_link = StringField("Job Link", validators=[Optional(), URL()])

    salary = IntegerField(
        "Salary", validators=[Optional(), NumberRange(min=0, message="Salary can't be negative.")]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Applied", "Applied"),
            ("Interview Scheduled", "Interview Scheduled"),
            ("Pending", "Pending"),
            ("Rejected", "Rejected"),
            ("Offer Received", "Offer Received"),
        ],
        validators=[DataRequired()],
    )

    applied_date = DateField(
        "Applied Date",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    interview_date = DateField(
        "Interview Date",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    notes = TextAreaField("Notes", validators=[Optional()])

    resume = FileField(
        "Resume",
        validators=[
            FileAllowed(
                ["pdf", "doc", "docx"], "Only PDF, DOC, and DOCX files are allowed."
            )
        ],
    )


class AddForm(JobApplicationForm):
    pass


class EditForm(JobApplicationForm):
    pass


class ProfileForm(FlaskForm):

    name = StringField("Full Name", validators=[DataRequired(), Length(max=100)])

    email = StringField("Email", validators=[DataRequired(), Email()])

    submit = SubmitField("Save Changes")


class PasswordForm(FlaskForm):

    current_password = PasswordField("Current Password", validators=[DataRequired()])

    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8)]
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )

    submit = SubmitField("Update Password")
