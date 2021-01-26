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
    return render_template("equity.html", equity=equity)


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


@main_blueprint.route('/Portfolio', methods=['GET', 'POST'])
@login_required
def portfolio_page():
    if request.method == "GET":
        position = Position()
        csv = "holdings2.csv"
        df = position.get_data_from_file(csv)
        holdings = position.get_holdings(df)
        return render_template("main/portfolio.html", tables=[
            holdings.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                             columns=['Symbol', 'Option Underlier',
                                      'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                      'Option Delta', 'Exposure'],
                             formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                         "Exposure": "{:,.0f}".format})])
    else:
        return redirect(url_for("main/home_page.html"))


@main_blueprint.route('/Group', methods=['GET', 'POST'])
@login_required
# @csrf.exempt
def group_page():
    if request.method == "GET":
        position = Position()
        ticker = "FSLY"
        csv = "currentholding.csv"
        df = position.get_data_from_file(csv)
        group = position.filter_holdings(df, ticker)
        group = position.get_holdings(group)
        return render_template("main/group.html", tables=[
            group.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                          columns=['Symbol', 'Option Underlier',
                                   'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                   'Option Delta', 'Exposure'],
                          formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                      "Exposure": "{:,.0f}".format})])
    elif request.method == "POST":
        position = Position()
        ticker = request.form.get('ticker')
        # , meta = {'csrf': False}
        csv = "currentholding.csv"
        df = position.get_data_from_file(csv)
        group = position.filter_holdings(df, ticker)
        data = position.check_equity(group)
        group = position.get_holdings(group)
        vars = position.prep_for_exp(data)
        total = position.group_exp(vars)
        exposure = total.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        exposure.loc["Total Exposure"] = exposure.sum(numeric_only=True, axis=0)
        group = group.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                          columns=['Symbol', 'Option Underlier',
                                   'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                   'Option Delta', 'Exposure'],
                          formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                      "Exposure": "{:,.0f}".format})
        exposure = exposure.to_html(index=True, header=True, table_id="Exposure")

        return render_template("main/group.html", tables=[group, exposure])
    else:
        return redirect(url_for("main/home_page.html"))


@main_blueprint.route('/Sample2', methods=['GET', 'POST'])
@login_required
def sample2_page():
    if request.method == "GET":
        position = Position()
        csv = "holdings2.csv"
        df = position.get_data_from_file(csv)
        sample2 = position.get_holdings(df)
        return render_template("main/sample2.html", tables=[
            sample2.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                            columns=['Symbol', 'Option Underlier',
                                     'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                     'Option Delta', 'Exposure'],
                            formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                        "Exposure": "{:,.0f}".format})])
    else:
        return redirect(url_for("main/home_page.html"))
