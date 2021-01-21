import pandas
from app.securities.securities import Equity, Security

class Equity_Data:
    def __init__(self):
        self.equities = {}
        self._equities_key =0


    def add_equity(self, equity):
        self._equities_key += 1
        self.equities[self._equities_key] = equity
        return self._equities_key

    def update_equity(self, equity_key, equity):
        self.equities[equity_key] = equity

    def get_equity(self, equity_key):
        equity = self.equities.get(equity_key)
        if equity is None:
            return None
        equity_ = Equity(equity.name, equity.ticker)
        return equity_

    def delete_equity(self, equity_key):
        if equity_key in self.equities:
            del self.equities[equity_key]

    def get_equities(self):
        equities = []
        for equity_key, equity in self.equities.items():
            equity_ = Equity(equity.name, equity.ticker, equity.shares)
            equities.append((equity_key, equity_))
        return equities

class Security_Data:
    def __init__(self):
        self.securities = {}
        self._securities_key =0

    def add_security(self, security):
        self._securities_key += 1
        self.securities[self._securities_key] = security
        return self._securities_key

    def update_security(self, security_key, security):
        self.securities[security_key] = security

    def get_security(self, security_key):
        security = self.securities.get(security_key)
        if security is None:
            return None
        security_ = Security(security.name, security.ticker)
        return security_

    def delete_security(self, security_key):
        if security_key in self.securities:
            del self.securities[security_key]

    def get_securities(self):
        securities = []
        for security_key, security in self.securities.items():
            security_ = Security(security.symbol, security.type, security.underlying, security.optiontype, security.position, security.strike, security.expiration)
            securities.append((security_key, security_))
        return securities

    def get_holdings(self, csv):
        df = pandas.read_csv(csv, engine='python', header=6, skipfooter=4)
        # df = pandas.read_csv(csv)
        tup = df.to_numpy()
        return tup

    def seed_holdings(self, holdings):
        secdb = Security_Data()
        for item in holdings:
            symbol = item[0]
            sectype = item[1]
            underlying = item[2]
            optiontype = item[3]
            position = item[4]
            strike = item[5]
            expiration = item[6]
            secdb.add_security(Security(symbol, sectype, underlying, optiontype, position, strike, expiration))
        return secdb






