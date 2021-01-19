class Equity:
    def __init__(self, name, ticker):
        self.name = name
        self.ticker = ticker

class Option:
    def __init__(self, underlying, symbol, type, strike, expiration ):
        self.underlying = underlying
        self.symbol = symbol
        self.type = type
        self.strike = strike
        self.expiration = expiration
