import json
import mstarpy
import datetime
from collections import defaultdict
#import pyxirr
from scipy.optimize import newton

class PortfolioManager:
    def __init__(self, file):

        self.holdings = defaultdict(list)
        self.file = file
        self.scheme_leftover_units = {}
        self.nav_scheme_mapping = {}
        self.folio_isin_mapping = {}
        self.per_scheme_gain = {}
        self.money_in_scheme = {}
        self.money_gained_from_scheme = {}
        self.end_date = datetime.datetime.now()
        self.start_date = self.end_date - datetime.timedelta(days=1)
        self.transactions = []
        self.dtSummary = []
        self.total_portfolio_val = 0
        self.total_trxn_amount = 0
        self.total_portfolio_gain = 0


    def read_data(self):
        """Read the JSON data from file"""
        with open(self.file, 'r') as file:
            data = json.load(file)
            self.trxns = data['data'][0]['dtTransaction']
            self.dtSummary = data['data'][0]['dtSummary']

    @staticmethod
    def convert_date(trxn_date):
        """Convert date string to datetime object."""
        """ Marked as static method because it doesn't rely on any instance specific data"""
        return datetime.datetime.strptime(trxn_date, "%d-%b-%Y")

    def sort_trxns(self):
        """Sort transactions by transaction date"""
        self.trxns = sorted(self.trxns, key=lambda x: self.convert_date(x['trxnDate']))

    """ #This is a alternative way of calculating Portfolio value. 
        #However, it doesn't account for FIFO. As FIFO is not required for just Portfolio value. 
        #But using FIFO will help in getting in history of data and is recommended 
    def process_trxns(self):
        #Calculated the value of each BROKER-SCHEME using FOlIO
    
        for info in self.trxns:
            if float(info["trxnAmount"]) != 0:
                folio = info["schemeName"]
                units = float(info["trxnUnits"])
                if folio not in self.scheme_leftover_units:
                    self.scheme_leftover_units[folio] = units
                    self.folio_isin_mapping[folio] = info["isin"]
                    #Mapping folio and isin to use in finding history NAV as isin is required for each NAV
    
                else:
                    self.scheme_leftover_units[folio] += units

                self.total_trxn_amount += float(info["trxnAmount"])
        print(self.scheme_leftover_units)
"""

    def process_trxns(self):
        for info in self.trxns:
            """folio is NOT unique in data, so using schemeName instead"""
            folio = info["schemeName"]
            units = float(info["trxnUnits"])
            trxnAmount = float(info["trxnAmount"])
            purchase_price = float(info["purchasePrice"]) if info["purchasePrice"] else 0
            self.folio_isin_mapping[folio] = info["isin"]
            # If it's a buy, add the units to holdings
            if units > 0:
                self.holdings[folio].append((units, purchase_price))
            # purchase price not used in code but maybe necessary when scaling the appilication
            # If it's a sell, apply FIFO to deduct units
            elif units < 0:
                units_to_sell = abs(units)
                while units_to_sell > 0 and self.holdings[folio]:
                    oldest_units, price = self.holdings[folio][0]
                    if oldest_units <= units_to_sell:
                        units_to_sell -= oldest_units
                        self.holdings[folio].pop(0)
                        """After poping if there are still units to sell
                           It will sell from the next oldest unit and so on.."""
                    else:
                        self.holdings[folio][0] = (oldest_units - units_to_sell, purchase_price)
                        units_to_sell = 0
        # Store the trnxAmn for each scheme in dict, used to calculate Portfolio gain
            if trxnAmount != 0:
                if folio not in self.money_in_scheme:
                    self.money_in_scheme[folio] = trxnAmount
                else:
                    self.money_in_scheme[folio] += trxnAmount

        # Store the remaining units for each scheme in scheme_leftover_units
        self.scheme_leftover_units = {folio: sum(units for units, price in folio_units) for folio, folio_units in
                                      self.holdings.items()}
        # scheme_leftover_units will have data in the form { scheme/folio: all_units_in_scheme, ...}
        print("No of units per scheme"+str(self.scheme_leftover_units))


    def add_protofolio_to_trxns(self, protfolio_value):
        """Adding portfolio value to trnxs to calculate xirr value"""
        self.transactions.append((round(protfolio_value, 2), self.end_date))

    def fetch_nav_from_dtSummary(self):
        for info in self.dtSummary:
            nav = float(info["nav"])
            folio = info["schemeName"]
            self.nav_scheme_mapping[self.folio_isin_mapping[folio]] = nav

    def fetch_nav_from_mstarpy(self):
        """Fetch current NAV for each scheme using isin and store in Dictionary"""
        print("Printing lastest nav of each isin using mstarpy :")
        print("Mstarpy takes time in fetching data")
        print("Please wait till the loop runs...")
        for isin in self.folio_isin_mapping.values():
            fund = mstarpy.Funds(term=isin, country="in")
            history = fund.nav(start_date=self.start_date, end_date=self.end_date, frequency="daily")
            self.nav_scheme_mapping[isin] = round(float(history[-1]["nav"]), 4) #use the lastest value
            print(str(isin)+" :"+str(history[-1]["nav"]))


    def calculate_total_portfolio_value(self):
        """Calculate the total portfolio value based on units and NAV."""
        self.total_portfolio_val = 0
        for folio in self.scheme_leftover_units:
            scheme_total_value = self.scheme_leftover_units[folio] * \
                                 self.nav_scheme_mapping[self.folio_isin_mapping[folio]] #Fetching ISIN using the mapping
            self.total_portfolio_val += scheme_total_value
        return self.total_portfolio_val

    def calculate_protfolio_gain(self):
        self.total_portfolio_gain = 0
        for folio in self.money_in_scheme:
            self.money_gained_from_scheme[folio] = self.scheme_leftover_units[folio] * \
                                                    self.nav_scheme_mapping[self.folio_isin_mapping[folio]]\
                                                    - self.money_in_scheme[folio]
            self.total_portfolio_gain += self.scheme_leftover_units[folio] * \
                                         self.nav_scheme_mapping[self.folio_isin_mapping[folio]] \
                                         - self.money_in_scheme[folio]
        return self.total_portfolio_gain

    def process_trxn_XIFF(self):
        for txn in self.trxns:
            trxn_amount = float(txn["trxnAmount"])
            trxn_date = self.convert_date(txn["trxnDate"])
            if trxn_amount != 0:
                # Purchases are negative cash flows
                self.transactions.append((-trxn_amount, trxn_date))
    def calculate_xirr_newton(self):
        """Calculate the XIRR using Newton's method."""

        def xnpv(rate, transactions):
            """This function calculates the npv(Net present value) of the cash flows given discount rate.
            It loops through the transactions , calculates how much each future trxn is worth
            (discounted by the rate) and sums them up"""
            npv = 0.0
            for amount, date in transactions:
                days = (date - transactions[0][1]).days
                npv += amount / (1 + rate) ** (days / 365)
            return npv

        def xirr(transactins, intial_guess=0.1):
            """function uses Newton's method to find rate which makes NPV = 0
            It starts with an initial guess for rate=0.1 and
            then adjusts rate iteratively until it finds the correct value"""
            return newton(lambda rate: xnpv(rate, transactins), intial_guess)

        return xirr(self.transactions)

    """
    #For calulating XIRR using pyxirr library
    def calculate_xirr(self):
        #Calculate XIRR using pyxirr.
        for amount, date in self.transactions:
            print(f"Date: {date}, Amount: {amount}")
        cashflows = {date: amount for amount, date in self.transactions}
        xirr_value = xirr.xirr(cashflows)
        return xirr_value
    """
def main():
    portfolio_manager = PortfolioManager(file='transaction_detail.json')

    # Step 1: Read data from file
    portfolio_manager.read_data()

    # Step 2: Sort transactions
    portfolio_manager.sort_trxns()

    # Step 3: Process transactions to calculate leftover units per Broker-schema pair using folio
    portfolio_manager.process_trxns()

    # Step 4: Fetch current NAV for each scheme using isin
    choice = int(input("Enter which method to fetch NAV\n"
                       "Enter 1: NAV from dtSummary :\n"
                       "Enter 2: NAV using mstarpy :"))
    if choice == 1:
        portfolio_manager.fetch_nav_from_dtSummary()
    elif choice == 2:
        portfolio_manager.fetch_nav_from_mstarpy()

    while True:
        choice = int(input("\nEnter 1: Total Portfolio value :\n"
                           "Enter 2: Total Portfolio Gain :\n"
                           "Enter 3: XIRR value\n"
                           "Enter 4 to exit : "))
        if(choice == 1):
            # Step 5: Calculate the total portfolio value
            total_portfolio_value = round(portfolio_manager.calculate_total_portfolio_value(), 4)

            print("\nTotal Profolio Value : $"+str(total_portfolio_value))
        elif(choice == 2):
            # Step 6: Calculate the total portfolio gains
            total_portfolio_gain = round(portfolio_manager.calculate_protfolio_gain(), 4)
            print("\nPortfolio gain : $"+str(total_portfolio_gain))
        elif choice ==3:
            # Step 7: Calculate XIRR using newton's method and xnpv values
            total_portfolio_value = portfolio_manager.calculate_total_portfolio_value()
            portfolio_manager.process_trxn_XIFF()
            portfolio_manager.add_protofolio_to_trxns(total_portfolio_value)
            xirr_val = portfolio_manager.calculate_xirr_newton() * 100
            val = round(xirr_val, 4)
            print("\nXIRR value for portfolio : "+str(val)+"%")
        else:
            print("\nExiting...")
            exit(1)


if __name__ == "__main__":
    main()