from securites import Equity, Option

class Equity_Data:
    def __init__(self):
        self.holdings = {}
        self._holdings_key =0
        self.type

    def add_security(self, security, type):
        self._holdings_key += 1
        self.holdings[self._holdings_key] = security
        self.type = type
        return self._holdings_key

    def get_security(self, holdings_key):
        security = self.holdings.get(holdings_key)
        if security is None:
            return None
        # security_ = Security





