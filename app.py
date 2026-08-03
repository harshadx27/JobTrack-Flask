from datetime import date, datetime, UTC
from flask import (
    Flask,
    abort,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory,
    send_file,
)
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    func,
    or_,
    extract,
)
from forms import LoginForm, RegisterForm, AddForm, EditForm, ProfileForm, PasswordForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)
import os
import uuid
import csv
import io
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

load_dotenv()  # reads a local .env file (see .env.example) into os.environ

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
Bootstrap5(app)

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads", "resumes")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="user",
        cascade="all, delete",
    )


class JobApplication(db.Model):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(100))
    platform: Mapped[str | None] = mapped_column(String(50))
    job_link: Mapped[str | None] = mapped_column(String(500))
    salary: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(30))
    applied_date: Mapped[date | None] = mapped_column(Date)
    interview_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    resume: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="applications")


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_resume_filename(filename):
    """Prefix the sanitized filename with a random token so two users
    uploading e.g. 'resume.pdf' never overwrite each other's file."""
    safe_name = secure_filename(filename)
    return f"{uuid.uuid4().hex}_{safe_name}"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if user:
            # User already exists
            flash(
                "You've already signed up with that email, log in instead!", "warning"
            )
            return redirect(url_for("login"))

        hash_and_salted_password = generate_password_hash(
            form.password.data, method="pbkdf2:sha256", salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("dashboard"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        )
        user = result.scalar()
        if not user:
            flash("That email does not exist, please try again.", "danger")
            return redirect(url_for("login"))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again.", "danger")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("dashboard"))

    return render_template("login.html", form=form, current_user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    status_counts = dict(
        db.session.execute(
            db.select(JobApplication.status, func.count())
            .where(JobApplication.user_id == current_user.id)
            .group_by(JobApplication.status)
        ).all()
    )

    total_applications = db.session.scalar(
        db.select(func.count(JobApplication.id)).where(
            JobApplication.user_id == current_user.id
        )
    )

    recent_applications = (
        db.session.execute(
            db.select(JobApplication)
            .where(JobApplication.user_id == current_user.id)
            .order_by(JobApplication.applied_date.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    upcoming_interviews = (
        db.session.execute(
            db.select(JobApplication)
            .where(
                JobApplication.user_id == current_user.id,
                JobApplication.interview_date.is_not(None),
                JobApplication.interview_date >= date.today(),
            )
            .order_by(JobApplication.interview_date.asc())
            .limit(5)
        )
        .scalars()
        .all()
    )

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_applications=total_applications,
        status_counts=status_counts,
        recent_applications=recent_applications,
        upcoming_interviews_appl=upcoming_interviews,
    )


@app.route("/applications")
@login_required
def applications():

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    platform = request.args.get("platform", "")
    sort = request.args.get("sort", "newest")

    query = build_filtered_applications_query()

    # ---------------- PAGINATION ---------------- #

    page = request.args.get("page", 1, type=int)

    pagination = db.paginate(
        query,
        page=page,
        per_page=10,
        error_out=False,
    )

    return render_template(
        "applications.html",
        applications=pagination.items,
        pagination=pagination,
        search=search,
        status=status,
        platform=platform,
        sort=sort,
        active_page="applications",
    )


def build_filtered_applications_query():
    """Build the same filtered/sorted query used by the applications page,
    reading search/status/platform/sort from the current request's query
    string. Shared by the CSV and PDF export routes so both exports always
    match whatever the user currently has filtered on screen."""

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    platform = request.args.get("platform", "")
    sort = request.args.get("sort", "newest")

    query = db.select(JobApplication).where(JobApplication.user_id == current_user.id)

    if search:
        query = query.where(
            or_(
                JobApplication.company.ilike(f"%{search}%"),
                JobApplication.role.ilike(f"%{search}%"),
                JobApplication.location.ilike(f"%{search}%"),
            )
        )

    if status:
        query = query.where(JobApplication.status == status)

    if platform:
        query = query.where(JobApplication.platform == platform)

    if sort == "oldest":
        query = query.order_by(JobApplication.created_at.asc())
    elif sort == "company_asc":
        query = query.order_by(JobApplication.company.asc())
    elif sort == "company_desc":
        query = query.order_by(JobApplication.company.desc())
    elif sort == "interview":
        query = query.order_by(JobApplication.interview_date.asc())
    else:
        query = query.order_by(JobApplication.created_at.desc())

    return query


@app.route("/export/csv")
@login_required
def export_csv():

    applications = (
        db.session.execute(build_filtered_applications_query()).scalars().all()
    )

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(
        [
            "Company",
            "Role",
            "Status",
            "Platform",
            "Location",
            "Salary",
            "Applied Date",
            "Interview Date",
        ]
    )

    for application in applications:

        writer.writerow(
            [
                application.company,
                application.role,
                application.status,
                application.platform,
                application.location,
                application.salary,
                application.applied_date,
                application.interview_date,
            ]
        )

    memory_file = io.BytesIO()
    memory_file.write(output.getvalue().encode("utf-8"))
    memory_file.seek(0)
    output.close()

    return send_file(
        memory_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="jobtrack_applications.csv",
    )


@app.route("/export/pdf")
@login_required
def export_pdf():

    applications = (
        db.session.execute(build_filtered_applications_query()).scalars().all()
    )

    total = len(applications)
    status_counts = {}
    for application in applications:
        status_counts[application.status] = status_counts.get(application.status, 0) + 1

    interviewed = status_counts.get("Interview Scheduled", 0)
    offers = status_counts.get("Offer Received", 0)
    rejected = status_counts.get("Rejected", 0)

    interview_rate = round((interviewed / total) * 100, 1) if total else 0
    offer_rate = round((offers / total) * 100, 1) if total else 0
    rejection_rate = round((rejected / total) * 100, 1) if total else 0

    # ---------------- DESIGN TOKENS ---------------- #
    ink = colors.HexColor("#0f172a")
    slate = colors.HexColor("#475569")
    muted = colors.HexColor("#94a3b8")
    card_bg = colors.HexColor("#f8fafc")
    border = colors.HexColor("#e2e8f0")
    blue = colors.HexColor("#2563eb")
    purple = colors.HexColor("#8b5cf6")
    green = colors.HexColor("#22c55e")
    red = colors.HexColor("#ef4444")
    amber = colors.HexColor("#f59e0b")

    status_color_map = {
        "Applied": blue,
        "Interview Scheduled": purple,
        "Offer Received": green,
        "Rejected": red,
        "Pending": amber,
    }

    memory_file = io.BytesIO()

    doc = SimpleDocTemplate(
        memory_file,
        pagesize=letter,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
    )

    content_width = letter[0] - doc.leftMargin - doc.rightMargin

    styles = getSampleStyleSheet()
    story = []

    kicker_style = ParagraphStyle(
        "kicker",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=colors.HexColor("#93c5fd"),
        spaceAfter=4,
    )
    title_style = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=23,
        textColor=colors.white,
        leading=26,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=colors.HexColor("#cbd5e1"),
        spaceBefore=6,
    )
    card_kicker_style = ParagraphStyle(
        "card_kicker",
        fontName="Helvetica-Bold",
        fontSize=7.2,
        textColor=slate,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    card_number_style = ParagraphStyle(
        "card_number",
        fontName="Helvetica-Bold",
        fontSize=19,
        alignment=TA_CENTER,
        leading=22,
    )
    section_title_style = ParagraphStyle(
        "section_title",
        fontName="Helvetica-Bold",
        fontSize=12.5,
        textColor=ink,
        spaceAfter=2,
    )
    legend_style = ParagraphStyle(
        "legend",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=ink,
        leading=13,
    )
    legend_count_style = ParagraphStyle(
        "legend_count",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=muted,
        leading=13,
    )
    cell_style = ParagraphStyle(
        "cell",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=ink,
    )
    table_header_style = ParagraphStyle(
        "th",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.white,
    )

    def status_chip(status_name):
        color = status_color_map.get(status_name, muted)
        return Paragraph(
            f'<font color="{color.hexval()}"><b>&#9679;</b></font> {status_name}',
            legend_style,
        )

    # ---------------- HEADER BANNER ---------------- #

    header_inner = [
        [Paragraph("J&nbsp;O&nbsp;B&nbsp;T&nbsp;R&nbsp;A&nbsp;C&nbsp;K", kicker_style)],
        [Paragraph("Application Report", title_style)],
        [
            Paragraph(
                f"Prepared for {current_user.name}  &middot;  Generated "
                f"{datetime.now(UTC).strftime('%d %B %Y')}",
                subtitle_style,
            )
        ],
    ]
    header_table = Table(header_inner, colWidths=[content_width])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ink),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, 0), 18),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("TOPPADDING", (0, 2), (-1, 2), 2),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.28 * inch))

    # ---------------- STAT CARDS ---------------- #

    def stat_card(label, value, accent):
        inner = Table(
            [
                [Paragraph(label.upper(), card_kicker_style)],
                [
                    Paragraph(
                        value,
                        ParagraphStyle(
                            "num", parent=card_number_style, textColor=accent
                        ),
                    )
                ],
            ],
            colWidths=[content_width / 4 - 8],
        )
        inner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), card_bg),
                    ("LINEABOVE", (0, 0), (-1, 0), 2.5, accent),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                    ("TOPPADDING", (0, 1), (-1, 1), 0),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
                    ("BOX", (0, 0), (-1, -1), 0.75, border),
                ]
            )
        )
        return inner

    cards = [
        stat_card("Total Applications", str(total), ink),
        stat_card("Interview Rate", f"{interview_rate}%", purple),
        stat_card("Offer Rate", f"{offer_rate}%", green),
        stat_card("Rejection Rate", f"{rejection_rate}%", red),
    ]
    card_row = Table([cards], colWidths=[content_width / 4] * 4)
    card_row.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(card_row)
    story.append(Spacer(1, 0.32 * inch))

    def section_header(text):
        bar_and_text = Table(
            [["", Paragraph(text, section_title_style)]],
            colWidths=[6, content_width - 6],
        )
        bar_and_text.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), blue),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 0),
                    ("TOPPADDING", (0, 0), (0, 0), 0),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 0),
                    ("LEFTPADDING", (1, 0), (1, 0), 8),
                    ("TOPPADDING", (1, 0), (1, 0), 0),
                    ("BOTTOMPADDING", (1, 0), (1, 0), 0),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return bar_and_text

    # ---------------- STATUS BREAKDOWN ---------------- #

    if total:

        story.append(section_header("Status Breakdown"))
        story.append(Spacer(1, 0.14 * inch))

        drawing = Drawing(160, 140)
        pie = Pie()
        pie.x = 10
        pie.y = 5
        pie.width = 130
        pie.height = 130
        pie.data = list(status_counts.values())
        pie.labels = None
        pie.simpleLabels = 0
        pie.slices.strokeWidth = 1.2
        pie.slices.strokeColor = colors.white
        for i, status_name in enumerate(status_counts.keys()):
            pie.slices[i].fillColor = status_color_map.get(status_name, muted)
        drawing.add(pie)

        legend_rows = []
        for status_name, count in status_counts.items():
            pct = round((count / total) * 100, 1)
            legend_rows.append(
                [
                    status_chip(status_name),
                    Paragraph(f"{count} &middot; {pct}%", legend_count_style),
                ]
            )
        legend_table = Table(legend_rows, colWidths=[1.7 * inch, 1.3 * inch])
        legend_table.setStyle(
            TableStyle(
                [
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        combo = Table(
            [[drawing, legend_table]],
            colWidths=[content_width * 0.35, content_width * 0.65],
        )
        combo.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(combo)
        story.append(Spacer(1, 0.3 * inch))

    # ---------------- APPLICATIONS TABLE ---------------- #

    story.append(section_header("Applications"))
    story.append(Spacer(1, 0.14 * inch))

    def th(text):
        return Paragraph(text, table_header_style)

    table_data = [
        [
            th("Company"),
            th("Role"),
            th("Status"),
            th("Platform"),
            th("Applied"),
            th("Interview"),
            th("Salary"),
        ]
    ]

    for application in applications:
        salary_display = f"{application.salary:,}" if application.salary else "-"
        table_data.append(
            [
                Paragraph(application.company or "-", cell_style),
                Paragraph(application.role or "-", cell_style),
                (
                    status_chip(application.status)
                    if application.status
                    else Paragraph("-", cell_style)
                ),
                Paragraph(application.platform or "-", cell_style),
                Paragraph(
                    str(application.applied_date) if application.applied_date else "-",
                    cell_style,
                ),
                Paragraph(
                    (
                        str(application.interview_date)
                        if application.interview_date
                        else "-"
                    ),
                    cell_style,
                ),
                Paragraph(salary_display, cell_style),
            ]
        )

    col_widths = [
        content_width * 0.135,
        content_width * 0.155,
        content_width * 0.225,
        content_width * 0.115,
        content_width * 0.12,
        content_width * 0.12,
        content_width * 0.13,
    ]

    applications_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    applications_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ink),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 1), (-1, -1), 0.5, border),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, border),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, card_bg]),
            ]
        )
    )
    story.append(applications_table)

    if not total:
        story.append(
            Paragraph("No applications match the current filters.", styles["Normal"])
        )

    def draw_footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setStrokeColor(border)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(
            doc.leftMargin, 0.5 * inch, letter[0] - doc.rightMargin, 0.5 * inch
        )
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(muted)
        canvas_obj.drawString(doc.leftMargin, 0.35 * inch, "Job Application Tracker")
        canvas_obj.drawRightString(
            letter[0] - doc.rightMargin, 0.35 * inch, f"Page {doc_obj.page}"
        )
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="jobtrack_applications_report.pdf",
    )


@app.route("/application/<int:application_id>")
@login_required
def application_details(application_id):

    application = db.session.scalar(
        db.select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )

    if application is None:
        abort(404)

    return render_template("application_details.html", application=application)


@app.route("/application/<int:application_id>/resume")
@login_required
def download_resume(application_id):

    application = db.session.scalar(
        db.select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )

    if application is None or not application.resume:
        abort(404)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        application.resume,
        as_attachment=False,
    )


@app.route("/add-application", methods=["GET", "POST"])
@login_required
def add_application():

    form = AddForm()

    if form.validate_on_submit():

        resume_filename = None

        uploaded_file = form.resume.data

        if uploaded_file and getattr(uploaded_file, "filename", ""):

            file = uploaded_file

            if allowed_file(file.filename):

                filename = unique_resume_filename(file.filename)

                upload_folder = app.config["UPLOAD_FOLDER"]

                os.makedirs(upload_folder, exist_ok=True)

                filepath = os.path.join(upload_folder, filename)

                file.save(filepath)

                resume_filename = filename

            else:

                flash("Only PDF, DOC and DOCX files are allowed.", "danger")

                return redirect(url_for("add_application"))

        new_application = JobApplication(
            company=form.company.data,
            role=form.role.data,
            location=form.location.data,
            platform=form.platform.data,
            job_link=form.job_link.data,
            salary=form.salary.data,
            status=form.status.data,
            applied_date=form.applied_date.data,
            interview_date=form.interview_date.data,
            notes=form.notes.data,
            resume=resume_filename,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            user=current_user,
        )

        db.session.add(new_application)
        db.session.commit()

        flash("Application added successfully.", "success")

        return redirect(url_for("applications"))

    return render_template(
        "application_form.html", form=form, is_edit=False, active_page="add_application"
    )


@app.route("/statistics")
@login_required
def statistics():

    applications = (
        db.session.execute(
            db.select(JobApplication).where(JobApplication.user_id == current_user.id)
        )
        .scalars()
        .all()
    )

    total = len(applications)

    applied = sum(1 for a in applications if a.status == "Applied")

    interview = sum(1 for a in applications if a.status == "Interview Scheduled")

    offers = sum(1 for a in applications if a.status == "Offer Received")

    rejected = sum(1 for a in applications if a.status == "Rejected")

    pending = total - offers - rejected

    interview_rate = round((interview / total) * 100, 1) if total else 0

    offer_rate = round((offers / total) * 100, 1) if total else 0

    rejection_rate = round((rejected / total) * 100, 1) if total else 0

    success_rate = (
        round((offers / (offers + rejected)) * 100, 1) if (offers + rejected) else 0
    )

    monthly_data = db.session.execute(
        db.select(
            extract("month", JobApplication.applied_date), func.count(JobApplication.id)
        )
        .where(JobApplication.user_id == current_user.id)
        .group_by(extract("month", JobApplication.applied_date))
        .order_by(extract("month", JobApplication.applied_date))
    ).all()

    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    platform_counts = dict(
        db.session.execute(
            db.select(JobApplication.platform, func.count(JobApplication.id))
            .where(JobApplication.user_id == current_user.id)
            .group_by(JobApplication.platform)
        ).all()
    )

    platform_labels = list(platform_counts.keys())
    platform_values = list(platform_counts.values())

    status_counts = {}

    for application in applications:
        status = application.status
        status_counts[status] = status_counts.get(status, 0) + 1

    status_labels = list(status_counts.keys())
    status_values = list(status_counts.values())

    status_color_map = {
        "Applied": "#2563eb",
        "Interview Scheduled": "#9f78fa",
        "Offer Received": "#22c55e",
        "Rejected": "#ef4444",
        "Pending": "#f59e0b",
    }
    status_colors = [status_color_map.get(label, "#94a3b8") for label in status_labels]

    return render_template(
        "statistics.html",
        active_page="statistics",
        total=total,
        applied=applied,
        interview=interview,
        offers=offers,
        rejected=rejected,
        pending=pending,
        interview_rate=interview_rate,
        offer_rate=offer_rate,
        rejection_rate=rejection_rate,
        success_rate=success_rate,
        platform_labels=platform_labels,
        platform_values=platform_values,
        status_labels=status_labels,
        status_values=status_values,
        status_colors=status_colors,
    )


@app.route("/profile")
@login_required
def profile():
    return render_template(
        "profile.html",
        active_page="profile",
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():

    form = ProfileForm(
        name=current_user.name,
        email=current_user.email,
    )

    if form.validate_on_submit():

        # Check if another user already uses this email

        existing_user = db.session.scalar(
            db.select(User).where(
                User.email == form.email.data,
                User.id != current_user.id,
            )
        )

        if existing_user:

            flash("Email already exists.", "danger")

            return redirect(url_for("edit_profile"))

        current_user.name = form.name.data
        current_user.email = form.email.data

        db.session.commit()

        flash("Profile updated successfully.", "success")

        return redirect(url_for("profile"))

    return render_template(
        "edit_profile.html",
        form=form,
        active_page="profile",
    )


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    form = PasswordForm()

    if form.validate_on_submit():

        if not check_password_hash(
            current_user.password,
            form.current_password.data,
        ):

            flash("Current password is incorrect.", "danger")

            return redirect(url_for("change_password"))

        current_user.password = generate_password_hash(
            form.new_password.data,
            method="pbkdf2:sha256",
            salt_length=8,
        )

        db.session.commit()

        flash(
            "Password updated successfully.",
            "success",
        )

        return redirect(url_for("profile"))

    return render_template(
        "change_password.html",
        form=form,
        active_page="profile",
    )


@app.route("/application/<int:application_id>/edit", methods=["GET", "POST"])
@login_required
def edit_application(application_id):

    application = db.session.scalar(
        db.select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )

    if application is None:
        abort(404)

    form = EditForm(obj=application)

    # EditForm(obj=application) pre-fills every field from the model,
    # including `resume` -- but `application.resume` is just a filename
    # string, not an uploaded file. Clear it here so the field only holds
    # real upload data (a FileStorage) when the user actually chooses a new
    # file; otherwise `form.resume.data` would be that string and crash
    # `allowed_file(file.filename)` below.
    if request.method == "GET":
        form.resume.data = None

    if form.validate_on_submit():

        application.company = form.company.data
        application.role = form.role.data
        application.location = form.location.data
        application.platform = form.platform.data
        application.job_link = form.job_link.data
        application.salary = form.salary.data
        application.status = form.status.data
        application.applied_date = form.applied_date.data
        application.interview_date = form.interview_date.data
        application.notes = form.notes.data
        application.updated_at = datetime.now(UTC)

        # Resume upload -- only when a new file was actually chosen.
        uploaded_file = form.resume.data
        if uploaded_file and getattr(uploaded_file, "filename", ""):

            file = uploaded_file

            if allowed_file(file.filename):

                filename = unique_resume_filename(file.filename)

                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                file.save(filepath)

                application.resume = filename

            else:

                flash("Only PDF, DOC and DOCX files are allowed.", "danger")

                return redirect(
                    url_for("edit_application", application_id=application.id)
                )

        db.session.commit()

        flash("Application updated successfully.", "success")

        return redirect(
            url_for(
                "application_details",
                application_id=application.id,
            )
        )

    return render_template(
        "application_form.html",
        form=form,
        application=application,
        is_edit=True,
    )


@app.route("/application/<int:application_id>/delete", methods=["POST"])
@login_required
def delete_application(application_id):
    application = db.session.scalar(
        db.select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )

    if application is None:
        abort(404)

    db.session.delete(application)
    db.session.commit()

    flash("Application deleted successfully.", "success")
    return redirect(url_for("applications"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
