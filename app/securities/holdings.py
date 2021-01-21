from app.securities.securities import Equity

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









