from flask import Blueprint, redirect, render_template, current_app, request, url_for
from flask_user import current_user, login_required, roles_required
from app import db
from app.models.user_models import UserProfileForm
from app.securities.holdings import Security_Data
from app.securities.data import Position
import pandas

main_blueprint = Blueprint('main', __name__, template_folder='templates')

# The Home page is accessible to anyone
@main_blueprint.route('/')
def home_page():
    return render_template('main/home_page.html')


@main_blueprint.route('/login', methods=['GET', 'POST'])
def sign_in_page():
    return render_template('main/user_login.html')


# The User page is accessible to authenticated users (users that have logged in)
@main_blueprint.route('/member')
@login_required  # Limits access to authenticated users
def member_page():
    return render_template('main/user_page.html')


# The Admin page is accessible to users with the 'admin' role
@main_blueprint.route('/admin')
@roles_required('admin')  # Limits access to users with the 'admin' role
def admin_page():
    return render_template('main/admin_page.html')


@main_blueprint.route('/main/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    # Initialize form
    form = UserProfileForm(request.form, obj=current_user)

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(current_user)

        # Save user_profile
        db.session.commit()

        # Redirect to home page
        return redirect(url_for('main.home_page'))

    # Process GET or invalid POST
    return render_template('main/user_profile_page.html',
                           form=form)
@main_blueprint.route('/equity')
@login_required
def equity_page(equity_key):
    eqdb = current_app.config["eqdb"]
    equity = eqdb.get_equity(equity_key)
    return render_template("equity.html", equity = equity)

@main_blueprint.route('/holdings', methods=['GET', 'POST'])
@login_required
def holdings_page():
    secdb = Security_Data()
    holdings = secdb.get_holdings('holdings2.csv')
    data = secdb.get_data(holdings)
    dataII = data.to_numpy()
    secdb = secdb.seed_holdings(dataII)
    if request.method == "GET":
        securities = secdb.get_securities()
        return render_template("main/holdings.html", securities=securities)
    else:
        form_security_keys = request.form.getlist("security_keys")
        for form_security_key in form_security_keys:
            secdb.delete_equity(int(form_security_key))
        return redirect(url_for("holdings_page"))


@main_blueprint.route('/sample', methods=['GET', 'POST'])
@login_required
def sample_page():
    eqdb = current_app.config["eqdb"]
    if request.method == "GET":
        equities = eqdb.get_equities()
        return render_template("main/sample.html", equities=equities)
    else:
        form_equity_keys = request.form.getlist("equity_keys")
        for form_equity_key in form_equity_keys:
            eqdb.delete_equity(int(form_equity_key))
        return redirect(url_for("sample_page"))


@main_blueprint.route('/Portfolio', methods=['GET', 'POST'])
@login_required
def portfolio_page():
    if request.method == "GET":
        position = Position()
        holdings = position.get_holdings()
        # return render_template("main/portfolio.html", tables=[holdings.to_html(classes='data', header=True)])
        return render_template("main/portfolio.html", column_names=holdings.columns.values, row_data=list(holdings.values.tolist()),link_column='Option Underlier', zip=zip)
    else:
        return redirect(url_for("main/home_page.html"))
