import json
import mstarpy
import datetime
from collections import defaultdict
class PortfolioManager:
    def __init__(self, file):
        self.file = file
        self.scheme_leftover_units = {}
        self.nav_scheme_mapping = {}
        self.folio_isin_mapping = {}
        self.total_portfolio_val = 0
        self.end_date = datetime.datetime.now()
        self.start_date = self.end_date - datetime.timedelta(days=1)
        self.transactions = []
        self.dtSummary = []
        self.total_trxn_amount = 0
        self.total_portfolio_gain = 0

    def read_data(self):
        """Read the JSON data from file"""
        with open(self.file, 'r') as file:
            data = json.load(file)
            self.trxns = data['data'][0]['dtTransaction']
            self.dtSummary = data['data'][0]['dtSummary']

    @staticmethod
    def convert_date(trxnDate):
        """Convert date string to datetime object."""
        return datetime.datetime.strptime(trxnDate, "%d-%b-%Y")

    def sort_trxns(self):
        """Sort transactions by transaction date"""
        """Performs FIFO automatically as dates are sorted"""
        self.trxns = sorted(self.trxns, key=lambda x: self.convert_date(x['trxnDate']))

    """def process_trxns(self):
        """#Calculated the value of each BROKER-SCHEME using FOlIO
    """
        for info in self.trxns:
            if float(info["trxnAmount"]) != 0:
                folio = info["folio"]
                units = float(info["trxnUnits"])
                if folio not in self.scheme_leftover_units:
                    self.scheme_leftover_units[folio] = units
                    self.folio_isin_mapping[folio] = info["isin"]
                    """#Mapping folio and isin to use in finding history NAV as isin is required for each NAV
    """
                else:
                    self.scheme_leftover_units[folio] += units

                self.total_trxn_amount += float(info["trxnAmount"])
        print(self.scheme_leftover_units)
"""

    def process_trxns(self):
        holdings = defaultdict(list)
        for info in self.trxns:
            folio = info["folio"]
            units = float(info["trxnUnits"])
            purchase_price = float(info["purchasePrice"]) if info["purchasePrice"] else 0
            self.folio_isin_mapping[folio] = info["isin"]
            # If it's a buy, add the units to holdings
            if units > 0:
                holdings[folio].append((units, purchase_price))

            # If it's a sell, apply FIFO to deduct units
            elif units < 0:
                units_to_sell = abs(units)
                while units_to_sell > 0 and holdings[folio]:
                    oldest_units, _ = holdings[folio][0]
                    if oldest_units <= units_to_sell:
                        units_to_sell -= oldest_units
                        holdings[folio].pop(0)
                    else:
                        holdings[folio][0] = (oldest_units - units_to_sell, purchase_price)
                        units_to_sell = 0
            self.total_trxn_amount += float(info["trxnAmount"])
        # Store the remaining units in scheme_leftover_units
        self.scheme_leftover_units = {folio: sum(units for units, _ in folio_units) for folio, folio_units in
                                      holdings.items()}
        print(self.scheme_leftover_units)

    def fetch_nav_from_dtSummary(self):
        for info in self.dtSummary:
            nav = float(info["nav"])
            folio = info["folio"]
            self.nav_scheme_mapping[self.folio_isin_mapping[folio]] = nav

    def fetch_nav_from_mstarpy(self):
        """Fetch current NAV for each scheme using isin and store in Dictionary"""
        print("Printing lastest nav of each isin using mstarpy:")
        print("mstarpy takes time in fetching data")
        print("please wait till the loop runs...")
        for isin in self.folio_isin_mapping.values():
            fund = mstarpy.Funds(term=isin, country="in")
            history = fund.nav(start_date=self.start_date, end_date=self.end_date, frequency="daily")
            self.nav_scheme_mapping[isin] = round(float(history[-1]["nav"]), 4) #use the lastest value

            print(history)

    def calculate_total_portfolio_value(self):
        """Calculate the total portfolio value based on units and NAV."""
        self.total_portfolio_val = 0
        for folio in self.scheme_leftover_units:
            scheme_total_value = self.scheme_leftover_units[folio] * \
                                 self.nav_scheme_mapping[self.folio_isin_mapping[folio]] #Fetching ISIN using the mapping
            print(str(folio)+"\t"+str(scheme_total_value))
            self.total_portfolio_val += scheme_total_value
        return self.total_portfolio_val

    def calculate_total_portfolio_gain(self):
        self.total_portfolio_val = 0
        for folio in self.scheme_leftover_units:
            scheme_total_value = self.scheme_leftover_units[folio] * \
                                    self.nav_scheme_mapping[self.folio_isin_mapping[folio]]
            self.total_portfolio_val += scheme_total_value
        self.total_portfolio_gain = self.total_portfolio_val - self.total_trxn_amount
        print(self.total_portfolio_val)

        return self.total_portfolio_gain

def main():
    portfolio_manager = PortfolioManager(file='transaction_detail.json')

    # Step 1: Read data from file
    portfolio_manager.read_data()

    # Step 2: Sort transactions
    portfolio_manager.sort_trxns()

    # Step 3: Process transactions to calculate leftover units per Broker-schema pair using folio
    portfolio_manager.process_trxns()

    # Step 4: Fetch current NAV for each scheme using isin
    portfolio_manager.nav_from_dtSummary()

    while True:
        choice = int(input("Enter 1: Total Portfolio value :\nEnter 2. Total Portfolio Gain :\nEnter 3 to exit : "))
        if(choice == 1):
            # Step 5: Calculate the total portfolio value
            total_value = round(portfolio_manager.calculate_total_portfolio_value(), 4)

            print("\nTotal Profolio Value :"+str(total_value))
        elif(choice == 2):
            # Step 5: Calculate the total portfolio gains
            total_value = round(portfolio_manager.calculate_total_portfolio_gain(), 4)
            print(total_value)
        else:
            print("Exiting...")
            exit(1)


if __name__ == "__main__":
    main()