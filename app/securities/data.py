import pandas
import requests
from wallstreet import Stock, Call, Put
import numpy as np
import scipy.stats as si
from datetime import datetime

class Position:

    def get_holdings(self):
        csv = "currentholding.csv"
        df = pandas.read_csv(csv, engine='python', header=6, skipfooter=4)
        df.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
        df["Option Underlier"] = df.apply(lambda x: self.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
                                          axis=1)
        df['Expiration Date'] = df.apply(lambda x: self.date(x['Expiration Date'], x['Type']), axis=1)
        df['Month'] = df.apply(lambda x: self.add_month(x['Type'], x['Expiration Date']), axis=1)
        df['Day'] = df.apply(lambda x: self.add_day(x['Type'], x['Expiration Date']), axis=1)
        df['Year'] = df.apply(lambda x: self.add_year(x['Type'], x['Expiration Date']), axis=1)
        df['Strike Price'] = df.apply(lambda x: self.set_strike(x['Type'], x['Strike Price']), axis=1)
        df[['Market Price', 'Option Delta']] = df.apply(
            lambda x: pandas.Series(
                self.opt_values(x['Type'], x['Symbol'], x['Option Type'], x['Option Underlier'], x['Day'],
                                x['Month'],
                                x['Year'], x['Strike Price'])), axis=1)
        df['Exposure'] = df.apply(lambda x: self.share_exp(x['Type'], x['Quantity'], x['Option Delta']), axis=1)
        return df

    def delta_call(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        delta_call = si.norm.cdf(d1, 0.0, 1.0)
        return delta_call

    def delta_put(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        delta_put = si.norm.cdf(-d1, 0.0, 1.0)
        return -delta_put
    def add_und(self,type, under, sym):
        if type == "Equity":
            return sym
        else:
            return under

    def date(self,expiration, type):
        if type == "Option":
            date = datetime.strptime(expiration, '%m/%d/%Y')
        else:
            date = 'NaN'
        return date

    def add_month(self, type, date):
        if type == "Option":
            month = date.month
        else:
            month = 0
        return month

    def add_year(self, type, date):
        if type == "Option":
            year = date.year
        else:
            year = 0
        return year

    def add_day(self, type, date):
        if type == "Option":
            day = date.day
        else:
            day = 0
        return day

    def set_strike(self, type, strike):
        if type == "Option":
            strike = float(strike)
        else:
            strike = 'Nan'
        return strike

    def opt_values(self, type, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            price = Stock(symbol).price
            delta = 1
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            price = call.price
            delta = call.delta()
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            price = put.price
            delta = put.delta()
        else:
            price = 0
            delta = 0
        return price, delta

    def opt_prices(self, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            price = Stock(symbol).price
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            price = call.price
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            price = put.price
        else:
            price = 0
        return price

    def share_exp(self, type, quantity, delta):
        if type == 'Equity':
            exp = quantity
        else:
            exp = quantity * delta * 100
        return exp


