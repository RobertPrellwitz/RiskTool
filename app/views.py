from securities.securities import Equity
from flask import render_template, current_app, request, redirect, url_for
import pandas

def equity_page(equity_key):
    eqdb = current_app.config["eqdb"]
    equity = eqdb.get_equity(equity_key)
    return render_template("equity.html", equity = equity)

def holdings_page():
    eqdb = current_app.config["eqdb"]
    if request.method == "GET":
        equities = eqdb.get_equities()
        return render_template("holdings.html", equities=sorted(equities))
    else:
        form_equity_keys = request.form.getlist("equity_keys")
        for form_equity_key in form_equity_keys:
            eqdb.delete_equity(int(form_equity_key))
        return redirect(url_for("holdings_page"))

def get_holdings():
    df = pandas.read_csv('currentholding.csv', engine='python', header=6, skipfooter=4)

