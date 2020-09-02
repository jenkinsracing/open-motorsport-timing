from flask import Blueprint, render_template, flash, request, redirect, url_for, current_app, session
from flask_login import login_user, logout_user, login_required, current_user

from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed

from app.extensions import cache
from app.forms import LoginForm, RegisterForm
from app.models import db, User, UserDetail

from app import stripe_utils
from app.utils import user_sub_count, get_project_limit


main = Blueprint('main', __name__)


@main.route('/')
@cache.cached(timeout=1000)
def index():
    return render_template('index.html')


@main.route('/privacy')
@cache.cached(timeout=30000)
def privacy():
    return render_template('privacy.html')


@main.route('/terms')
@cache.cached(timeout=30000)
def terms():
    return render_template('terms.html')


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).one()
        login_user(user)

        # Tell Flask-Principal the identity changed
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

        # flash("Logged in successfully.", "success")  # TODO fix alert getting stuck on project route
        return redirect(request.args.get("next") or url_for("projects.index"))

    return render_template("login.html", form=form)


@main.route("/logout")
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    flash("You have been logged out.", "success")

    return redirect(url_for(".index"))


@main.route("/register", methods=["GET", "POST"])
def register():
    """Register new user."""
    form = RegisterForm()

    if form.validate_on_submit():
        u = User(form.email.data, form.username.data, form.password.data)
        u.user_details = UserDetail(first_name=form.firstname.data, last_name=form.lastname.data, job_title=form.jobtitle.data)
        db.session.add(u)
        db.session.commit()

        flash("Thank you for registering. You can now log in.", "success")
        return redirect(request.args.get("next") or url_for(".index"))
    # else:
    #     flash('Form error.')
    return render_template("register.html", form=form)


@main.route("/user", methods=["GET", "POST"])
@login_required
def user():
    project_count = user_sub_count(current_user)
    user_upcoming_invoice = stripe_utils.get_upcoming_invoice(current_user)
    user_invoices = stripe_utils.get_invoices(current_user)
    return render_template("user.html", project_count=project_count, user_upcoming_invoice=user_upcoming_invoice, user_invoices=user_invoices)

