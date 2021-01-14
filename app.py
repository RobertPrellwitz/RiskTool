from calendar import day_name,_localized_day
from datetime import datetime
from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def home_page():
    today = datetime.today()
    date = today.strftime("%A")
    return render_template("home.html", date = date)

@app.route("/Portfolio")
def Portfolio_page():
    return render_template("Portfolio.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
