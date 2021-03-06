import pandas
import requests
from wallstreet import Stock, Call, Put
import numpy as np
import scipy.stats as si
import sympy as sy
from sympy.stats import Normal, cdf
from datetime import datetime
from app.models.user_models import UserProfileForm
from flask_user import current_user, login_required, roles_required
import os

class Position:

    def get_data_from_file(self, csv):
        df = pandas.read_csv(csv, engine='python')
        df.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
        return df

    def get_etrade_data_from_file(self, csv):
        df = pandas.read_csv(csv, engine='python', header=6, skipfooter=4)
        df.drop(df.filter(regex="Unnamed"), axis=1, inplace=True)
        return df

    def check_equity(self, group):
        tup = group.shape
        x = tup[0];
        y = tup[1];
        z = 0
        for i in range(x):
            if group.iloc[i, 1] == "Equity":
                # group.iloc[i, 6] = 'NaN'
                z = z + 1
        if z == 0:
            ticker = group.iloc[0,2]
            new_row = pandas.DataFrame({'Symbol' : ticker, 'Type' : 'Equity', 'Option Underlier': ticker, 'Quantity' : 0,
                                  'Strike Price' : 0, 'Expiration Date' : ''}, index = [0])
            group = pandas.concat([new_row, group]).reset_index(drop=True)
            return group
        else:
            return group

    def get_holdings(self, df):
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

    def get_group_holdings(self, df):
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

    def prep_for_exp(self, df):
        df['Month'] = df.apply(lambda x: self.add_month(x['Type'], x['Expiration Date']), axis=1)
        df['Day'] = df.apply(lambda x: self.add_day(x['Type'], x['Expiration Date']), axis=1)
        df['Year'] = df.apply(lambda x: self.add_year(x['Type'], x['Expiration Date']), axis=1)
        df['Strike Price'] = df.apply(lambda x: self.set_strike(x['Type'], x['Strike Price']), axis=1)
        df[['Time', 'Rate', 'Vol']] = df.apply(lambda x: pandas.Series(
            self.opt_vol_r_T(x['Type'], x['Symbol'], x['Option Type'], x['Option Underlier'], x['Day'], x['Month'],
                             x['Year'], x['Strike Price'])), axis=1)
        return df

    def group_process(self,df, ticker):
        df["Option Underlier"] = df.apply(lambda x: self.add_und(x["Type"], x["Option Underlier"], x["Symbol"]),
                                          axis=1)
        group = self.filter_holdings(df, ticker)
        group = self.check_equity(group)
        group['Expiration Date'] = group.apply(lambda x: self.date(x['Expiration Date'], x['Type']), axis=1)
        deltas = group.copy()
        vols = group.copy()
        group = self.get_group_holdings(group)
        group.loc["Total Exposure"] = pandas.Series(group[['Exposure']].sum(), index=['Exposure'])
        group = group.to_html(header=True, index=True, na_rep="--", table_id="Portfolio",
                              columns=['Symbol', 'Option Underlier',
                                       'Option Type', 'Quantity', 'Strike Price', 'Expiration Date', 'Market Price',
                                       'Option Delta', 'Exposure'],
                              formatters={'Quantity': '{:.0f}'.format, "Market Price": "${:,.2f}".format,
                                          "Option Delta": "{:.1%}".format,
                                          "Exposure": "{:,.0f}".format})
        return (group, deltas, vols)

    def vols_process(self, vols):
        vols = self.prep_for_exp(vols)
        vol_exp = self.group_vol_exp(vols)
        # vol_exp.loc['Totals'] = vol_exp.sum(numeric_only=True)
        vol_exp = vol_exp.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        vol_exp.loc['Totals'] = vol_exp.sum(numeric_only=True, axis=0)
        # vol_exp = vol_exp.to_html(index=True, header=True, table_id='vol_exp', float_format='${:.0f}'.format,
        #                           formatters={'Quantity': '{:.0f}'.format})
        vol_exp = vol_exp.to_html(index=True, header=True, table_id='vol_exp',
                                  formatters={'Quantity': '{:.0f}'.format})
        return vol_exp

    def delta_process(self, vars):
        vars = self.prep_for_exp(vars)
        total = self.group_exp(vars)
        exposure = total.iloc[:, [0, 1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]]
        exposure.loc["Total Exposure"] = exposure.sum(numeric_only=True, axis=0)
        exposure = exposure.to_html(index=True, header=True, table_id="Exposure",
                                    formatters={'Quantity': '{:.0f}'.format})
        return exposure


    def group_exp(self, df):
        ticker = df.iloc[0,2]
        stock_px = float(Stock(ticker).price)
        inc = max(round(stock_px / 100),0.25)
        price = round(stock_px + (inc * 5))
        for i in range(10):
            df[f'$ {price}'] = df.apply(lambda x: self.eqty_exp(x['Type'], price, x['Option Type'], x['Quantity'],
                                        x['Strike Price'], x['Rate'], x['Time'], x['Vol']), axis = 1)
            price = price - inc
        return df

    def group_vol_exp(self, df):
        ticker = df.iloc[0, 2]
        stock_px = float(Stock(ticker).price)
        tup = df.shape
        x = tup[0]
        y= tup[1]
        z = 0
        vol = 0 ; avgvol = 0
        for i in range (x):
            if df.iloc[i, 1] == "Option":
                vol = df.iloc[i, 12] + vol
                z = z + 1
        avgvol = vol / z
        inc = avgvol * 0.1
        vol = avgvol - inc * 5
        temp = round(vol*100)
        for i in range (10):
            temp = round(vol*100,2)
            df[f'{temp}%'] = df.apply(lambda x: self.vol_exp(x['Type'], stock_px, x['Option Type'], x['Quantity'],
                                        x['Strike Price'], x['Rate'], x['Time'], vol, avgvol), axis=1)
            vol = vol + inc
        return df


    def eqty_exp(self, type, stock_px, option, qty, strike, rate, time, vol):
            if type == "Equity":
                delta = 1
                exp = delta * qty
            elif option == "CALL":
                delta = self.delta_call(stock_px,strike,time, rate, vol)
                exp = delta * qty * 100
            elif option == "PUT":
                delta = self.delta_put(stock_px,strike,time, rate, vol)
                exp = delta * qty * 100
            else:
                exp = 0
            exp = round(exp)
            return exp

    def vol_exp(self,type, stock_px, option, qty, strike, rate, time, vol, avg_vol):
        if type == 'Equity':
            value = 0
        elif option == 'CALL':
            call_value = self.euro_call(stock_px, strike, time, rate, vol)
            position_value = self.euro_call(stock_px, strike, time, rate, avg_vol)
            value = round((call_value - position_value) * 100 * qty)
        elif option == 'PUT':
            put_value = self.euro_put(stock_px, strike, time, rate, vol)
            position_value = self.euro_put(stock_px, strike, time, rate, avg_vol)
            value = round((put_value-position_value) * 100 * qty)
        else:
            value = 0
        return value

    def euro_call(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        call = (S * si.norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0))
        return call

    def euro_put(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        put = (K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0) - S * si.norm.cdf(-d1, 0.0, 1.0))
        return put

    def delta_call(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        delta_call = si.norm.cdf(d1, 0.0, 1.0)
        return delta_call

    def delta_put(self, S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        delta_put = si.norm.cdf(-d1, 0.0, 1.0)
        return -delta_put

    def theta_call(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        prob_density = 1 / np.sqrt(2 * np.pi) * np.exp(-d1 ** 2 * 0.5)
        theta = (-sigma * S * prob_density) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * si.norm.cdf(d2, 0.0, 1.0)
        return theta

    def theta_put(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        prob_density = 1 / np.sqrt(2 * np.pi) * np.exp(-d1 ** 2 * 0.5)
        theta = (-sigma * S * prob_density) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * si.norm.cdf(-d2, 0.0, 1.0)
        return theta

    def gamma(S, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        prob_density = 1 / np.sqrt(2 * np.pi) * np.exp(-d1 ** 2 * 0.5)
        gamma = prob_density / (S * sigma * np.sqrt(T))
        return gamma

    def vega(S, S0, K, T, r, sigma):
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        prob_density = 1 / np.sqrt(2 * np.pi) * np.exp(-d1 ** 2 * 0.5)
        vega = S0 * prob_density * np.sqrt(T)
        return vega

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

    def opt_prices(self, type, symbol, option, underlying, day, month, year, strike):
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

    def opt_vol_r_T(self, type, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            time = 1
            rate = 1
            vol = 1
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            time = call.BandS.T
            rate = float(call.BandS.r)
            vol = float(call.implied_volatility())
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            time = put.BandS.T
            rate = float(put.BandS.r)
            vol = float(put.implied_volatility())
        else:
            time = 0;
            rate = 0;
            vol = 0

        return time, rate, vol

    def opt_time(self, type, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            time = 1
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            time = call.BandS.T
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            time = put.BandS.T
        else:
            time = 0
        return time

    def opt_rate(self, type, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            rate = 1
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            rate = float(call.BandS.r)
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            rate = float(put.BandS.r)
        else:
            rate = 0
        return rate

    def opt_vol(self, type, symbol, option, underlying, day, month, year, strike):
        if type == "Equity":
            vol = 1
        elif option == "CALL":
            call = Call(underlying, day, month, year, strike)
            vol = float(call.implied_volatility())
        elif option == "PUT":
            put = Put(underlying, day, month, year, strike)
            vol = float(put.implied_volatility())
        else:
            vol = 0
        return vol

    def share_exp(self, type, quantity, delta):
        if type == 'Equity':
            exp = quantity
        else:
            exp = quantity * delta * 100
        return exp

    def filter_holdings(self, df, ticker):
        filter = df['Option Underlier'] == ticker
        position = df[filter]
        return position

    def get_port_data(self):
        email = current_user.email
        string = 'app/static/portfolios/' + str(email)
        return string

    def save_user_port(self, df):
        email = current_user.email
        df.to_csv(os.path.join('app/static/portfolios', email), encoding='utf-8', index=False)


