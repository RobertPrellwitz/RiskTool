
class Equity():
    def __init__(self, ticker, name, shares):
        self.name = name
        self.ticker = ticker
        self.shares = shares


class Option():
    def __init__(self, underlying, symbol, type, strike, expiration ):
        self.underlying = underlying
        self.symbol = symbol
        self.type = type
        self.strike = strike
        self.expiration = expiration

class Security():
    def __init__(self, symbol, type, underlying, optiontype, position, strike, expiration ):
        self.symbol = symbol
        self.type = type
        self.underlying = underlying
        self.optiontype = optiontype
        self.position = position
        self.type = type
        self.strike = strike
        self.expiration = expiration
