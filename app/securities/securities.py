
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
