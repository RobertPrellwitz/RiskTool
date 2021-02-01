from flask import Blueprint, redirect, render_template, current_app, request, url_for, flash
from flask_user import current_user, login_required, roles_required
from app import db
from app.models.user_models import UserProfileForm
from app.securities.holdings import Security_Data
from app.securities.data import Position
import pandas
import os
from datetime import datetime
main_blueprint = Blueprint('main', __name__, template_folder='templates')


# The Home page is accessible to anyone
@main_blueprint.route('/')
def home_page():
    return render_template('main/home_page.html')

@main_blueprint.route('/about')
def about_page():
    return render_template('main/about.html')


@main_blueprint.route('/login', methods=['GET', 'POST'])
def sign_in_page():
    return render_template('main/user_login.html')


# The User page is accessible to authenticated users (users that have logged in)
@main_blueprint.route('/member', methods=['GET', 'POST'])
@login_required  # Limits access to authenticated users
def member_page():
    if request.method == "POST" and 'userport' in request.files:
        position = Position()
        email = current_user.email
        file = request.files['userport']
        file.save(os.path.join('app/static/portfolios', email))
        flash("File Saved!")
        return render_template('main/user_page.html')
    if request.method == "POST" and 'etradeport' in request.files:
        position = Position()
        email = current_user.email
        file = request.files['etradeport']
        file = position.get_etrade_data_from_file(file)
        file.to_csv(os.path.join('app/static/portfolios', email), encoding='utf-8', index=False)
        flash("File Saved!")
        return render_template('main/user_page.html')
    else:
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


# @main_blueprint.route('/holdings', methods=['GET', 'POST'])
# @login_required
# def holdings_page():
#     secdb = Security_Data()
#     holdings = secdb.get_holdings('holdings2.csv')
#     data = secdb.get_data(holdings)
#     dataII = data.to_numpy()
#     secdb = secdb.seed_holdings(dataII)
#     if request.method == "GET":
#         securities = secdb.get_securities()
#         return render_template("main/holdings.html", securities=securities)
#     else:
#         form_security_keys = request.form.getlist("security_keys")
#         for form_security_key in form_security_keys:
#             secdb.delete_equity(int(form_security_key))
#         return redirect(url_for("holdings_page"))


@main_blueprint.route('/Portfolio', methods=['GET', 'POST'])
@login_required
def portfolio_page():
    if request.method == "GET":
        position = Position()
        csv = position.get_port_data()
        df = position.get_data_from_file(csv)
        holdings = position.get_holdings(df)
        return render_template("main/portfolio.html", tables=[
            holdings.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                             columns=['Symbol', 'Option Underlier',
                                      'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                      'Option Delta', 'Exposure'],
                             formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                         "Exposure": "{:,.0f}".format})])
    elif request.method == "POST":

        position = Position()
        email = current_user.email
        file = request.files['userport']
        file.save(os.path.join('app/static/portfolios', email))
        portfolio = 'app/static/portfolios/' + str(email)
        df = position.get_data_from_file(portfolio)
        holdings = position.get_holdings(df)
        return render_template("main/portfolio.html", tables=[
            holdings.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
                             columns=['Symbol', 'Option Underlier',
                                      'Option Type', 'Quantity', 'Strike Price', 'Expiration Date',
                                      'Market Price',
                                      'Option Delta', 'Exposure'],
                             formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                         "Exposure": "{:,.0f}".format})])

    else:
        flash("Something went wrong - you were redirected home!  Please try again.")
        return redirect(url_for("main.member_page"))


@main_blueprint.route('/Group', methods=['GET', 'POST'])
@login_required
# @csrf.exempt
def group_page():
    # if request.method == "GET":
    #     position = Position()
    #     ticker = "AAPL"
    #     csv = position.get_port_data()
    #     df = position.get_data_from_file(csv)
    #     df["Option Underlier"] = df.apply(lambda x: position.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
    #                                       axis=1)
    #     group = position.filter_holdings(df, ticker)
    #     group = position.get_holdings(group)
    #     group.loc["Total Exposure"] = group.sum(["Exposure"],axis =0)
    #     return render_template("main/group.html", tables=[
    #         group.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
    #                       columns=['Symbol', 'Option Underlier',
    #                                'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
    #                                'Option Delta', 'Exposure'],
    #                       formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
    #                                   "Exposure": "{:,.0f}".format})])
    if request.method == "POST":
        position = Position()
        ticker = request.form.get('ticker').upper()
        csv = position.get_port_data()
        df = position.get_data_from_file(csv)
        df["Option Underlier"] = df.apply(lambda x: position.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
                                          axis=1)
        group = position.filter_holdings(df, ticker)
        group = position.check_equity(group)
        group['Expiration Date'] = group.apply(lambda x: position.date(x['Expiration Date'], x['Type']), axis=1)
        vars = group.copy()
        vols = group.copy()
        group = position.get_group_holdings(group)
        group.loc["Total Exposure"] = pandas.Series(group[['Exposure']].sum(), index=['Exposure'])
        vars = position.prep_for_exp(vars)
        total = position.group_exp(vars)
        exposure = total.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        vols = position.prep_for_exp(vols)
        vol_exp = position.group_vol_exp(vols)
        vol_exp.loc['Totals'] = vol_exp.sum(numeric_only=True)
        vol_exp = vol_exp.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        exposure.loc["Total Exposure"] = exposure.sum(numeric_only=True, axis=0)
        group = group.to_html(header=True, index=True, na_rep="--", table_id="Portfolio",
                          columns=['Symbol', 'Option Underlier',
                                   'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                   'Option Delta', 'Exposure'],
                          formatters={'Quantity':'{:.0f}'.format,"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                      "Exposure": "{:,.0f}".format})
        exposure = exposure.to_html(index=True, header=True, table_id="Exposure", formatters={'Quantity':'{:.0f}'.format})
        vol_exp = vol_exp.to_html(index=True, header=True, table_id='vol_exp', float_format='${:.0f}'.format, formatters={'Quantity':'{:.0f}'.format})

        return render_template("main/group.html", tables=[group, exposure, vol_exp], titles=['', 'Group Holdings', 'Equity Exposure', 'Volatility Exposure'])
    else:
        flash("Something went wrong - you were redirected home!  Please try again.")
        return redirect(url_for("main.member_page"))


@main_blueprint.route('/Sample2', methods=['GET', 'POST'])
def sample2_page():
    if request.method == "GET":
        position = Position()
        csv = "holdings2.csv"
        df = position.get_etrade_data_from_file(csv)
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

@main_blueprint.route('/NewEquity', methods=['GET', 'POST'])
@login_required
# @csrf.exempt
def new_equity_page():
    # if request.method == "GET":
    #     position = Position()
    #     ticker = "FSLY"
    #     csv = position.get_port_data()
    #     df = position.get_data_from_file(csv)
    #     group = position.filter_holdings(df, ticker)
    #     group = position.get_holdings(group)
    #     group.loc["Total Exposure"] = group.sum(["Exposure"],axis =0)
    #     return render_template("main/group.html", tables=[
    #         group.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
    #                       columns=['Symbol', 'Option Underlier',
    #                                'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
    #                                'Option Delta', 'Exposure'],
    #                       formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
    #                                   "Exposure": "{:,.0f}".format})])
    if request.method == "POST":
        position = Position()
        ticker = request.form.get('ticker').upper()
        quantity = request.form.get("quantity")
        quantity = int(quantity)
        csv = position.get_port_data()
        df = position.get_data_from_file(csv)
        df.loc[len(df.index)] = [ticker, 'Equity', '', '', quantity, '', '']
        df.sort_values(by=['Symbol'], inplace=True)
        position.save_user_port(df)
        df["Option Underlier"] = df.apply(lambda x: position.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
                                          axis=1)
        group = position.filter_holdings(df, ticker)
        group = position.check_equity(group)
        group['Expiration Date'] = group.apply(lambda x: position.date(x['Expiration Date'], x['Type']), axis=1)
        vars = group.copy()
        vols = group.copy()
        group = position.get_group_holdings(group)
        group.loc["Total Exposure"] = pandas.Series(group[['Exposure']].sum(), index=['Exposure'])
        vars = position.prep_for_exp(vars)
        total = position.group_exp(vars)
        exposure = total.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        vols = position.prep_for_exp(vols)
        vol_exp = position.group_vol_exp(vols)
        vol_exp.loc['Totals'] = vol_exp.sum(numeric_only=True)
        vol_exp = vol_exp.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        exposure.loc["Total Exposure"] = exposure.sum(numeric_only=True, axis=0)
        group = group.to_html(header=True, index=True, na_rep="--", table_id="Portfolio",
                          columns=['Symbol', 'Option Underlier',
                                   'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                   'Option Delta', 'Exposure'],
                          formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                      "Exposure": "{:,.0f}".format})
        exposure = exposure.to_html(index=True, header=True, table_id="Exposure",
                                    formatters={'Quantity': '{:.0f}'.format})
        vol_exp = vol_exp.to_html(index=True, header=True, table_id='vol_exp', float_format='${:.0f}'.format,
                                  formatters={'Quantity': '{:.0f}'.format})

        return render_template("main/group.html", tables=[group, exposure, vol_exp],
                        titles=['', 'Group Holdings', 'Equity Exposure', 'Volatility Exposure'])
    else:
        flash("Something went wrong - you were redirected home!  Please try again.")
        return redirect(url_for("main.member_page"))

@main_blueprint.route('/NewOption', methods=['GET', 'POST'])
@login_required
# @csrf.exempt
def new_option_page():
#     if request.method == "GET":
#         position = Position()
#         ticker = "FSLY"
#         csv = position.get_port_data()
#         df = position.get_data_from_file(csv)
#         group = position.filter_holdings(df, ticker)
#         group = position.get_holdings(group)
#         group.loc["Total Exposure"] = group.sum(["Exposure"],axis =0)
#         return render_template("main/group.html", tables=[
#             group.to_html(header=True, index=False, na_rep="--", table_id="Portfolio",
#                           columns=['Symbol', 'Option Underlier',
#                                    'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
#                                    'Option Delta', 'Exposure'],
#                           formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
#                                       "Exposure": "{:,.0f}".format})])
    if request.method == "POST":
        position = Position()
        symbol = request.form.get('symbol')
        underlier = request.form.get('underlying').upper()
        type = request.form.get('type').upper()
        quantity = request.form.get("quantity")
        strike = request.form.get('strike price')
        expiry = request.form.get('expiration')
        quantity = int(quantity)
        strike = int(strike)
        csv = position.get_port_data()
        df = position.get_data_from_file(csv)
        df.loc[len(df.index)] = [symbol, 'Option', underlier, type, quantity, strike, expiry]
        df.sort_values(by=['Symbol'], inplace=True)
        position.save_user_port(df)
        df["Option Underlier"] = df.apply(lambda x: position.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
                                          axis=1)
        group = position.filter_holdings(df, underlier)
        group = position.check_equity(group)
        group['Expiration Date'] = group.apply(lambda x: position.date(x['Expiration Date'], x['Type']), axis=1)
        vars = group.copy()
        vols = group.copy()
        group = position.get_group_holdings(group)
        group.loc["Total Exposure"] = pandas.Series(group[['Exposure']].sum(), index=['Exposure'])
        vars = position.prep_for_exp(vars)
        total = position.group_exp(vars)
        exposure = total.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        vols = position.prep_for_exp(vols)
        vol_exp = position.group_vol_exp(vols)
        vol_exp.loc['Totals'] = vol_exp.sum(numeric_only=True)
        vol_exp = vol_exp.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        exposure.loc["Total Exposure"] = exposure.sum(numeric_only=True, axis=0)
        group = group.to_html(header=True, index=True, na_rep="--", table_id="Portfolio",
                          columns=['Symbol', 'Option Underlier',
                                   'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                   'Option Delta', 'Exposure'],
                          formatters={"Market Price": "${:,.2f}".format, "Option Delta": "{:.1%}".format,
                                      "Exposure": "{:,.0f}".format})
        exposure = exposure.to_html(index=True, header=True, table_id="Exposure",
                                    formatters={'Quantity': '{:.0f}'.format})
        vol_exp = vol_exp.to_html(index=True, header=True, table_id='vol_exp', float_format='${:.0f}'.format,
                                  formatters={'Quantity': '{:.0f}'.format})

        return render_template("main/group.html", tables=[group, exposure, vol_exp], titles=['', 'Group Holdings', 'Equity Exposure', 'Volatility Exposure'])
    else:
        flash("Something went wrong - you were redirected home!  Please try again.")
        return redirect(url_for("main.member_page"))
