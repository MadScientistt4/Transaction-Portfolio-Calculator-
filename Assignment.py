import json
import mstarpy
import datetime

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

    def process_trxns(self):
        """Calculated the value of each BROKER-SCHEME using FOlIO"""
        for info in self.trxns:
            if float(info["trxnAmount"]) != 0:
                folio = info["folio"]
                units = float(info["trxnUnits"])
                if folio not in self.scheme_leftover_units:
                    self.scheme_leftover_units[folio] = units
                    self.folio_isin_mapping[folio] = info["isin"]
                    """Mapping folio and isin to use in finding history NAV as isin is required for each NAV"""
                else:
                    self.scheme_leftover_units[folio] += units
            print(units)

    def total_trxns(self):
        for info in self.trxns:
            if float(info["trxnAmount"]) != 0:
                folio = info["folio"]
                units = float(info["trxnUnits"])
                if folio not in self.scheme_leftover_units:
                    self.scheme_leftover_units[folio] = units
                    self.folio_isin_mapping[folio] = info["isin"]
                    """Mapping folio and isin to use in finding history NAV as isin is required for each NAV"""
                else:
                    self.scheme_leftover_units[folio] += units
                self.total_trxn_amount += float(info["trxnAmount"])
        print(self.scheme_leftover_units)
    def fetch_nav(self):
        """Fetch current NAV for each scheme using isin and store in Dictionary"""
        print("Printing lastest nav of each isin using mstarpy:")
        print("mstarpy takes time in fetching data")
        print("please wait till the loop runs...")
        for isin in self.folio_isin_mapping.values():
            fund = mstarpy.Funds(term=isin, country="in")
            history = fund.nav(start_date=self.start_date, end_date=self.end_date, frequency="daily")
            self.nav_scheme_mapping[isin] = float(history[-1]["nav"]) #use the lastest value

            print(history)

    def calculate_total_portfolio_value(self):
        """Calculate the total portfolio value based on units and NAV."""
        self.total_portfolio_val = 0
        for folio in self.scheme_leftover_units:
            scheme_total_value = self.scheme_leftover_units[folio] * \
                                 self.nav_scheme_mapping[self.folio_isin_mapping[folio]] #Fetching ISIN using the mapping
            print(scheme_total_value)
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
    while True:
        choice = int(input("Enter 1: Total Portfolio value :\nEnter 2. Total Portfolio Gain :\nEnter 3 to exit :"))
        if(choice == 1):
            portfolio_manager = PortfolioManager(file='transaction_detail.json')

            # Step 1: Read data from file
            portfolio_manager.read_data()

            # Step 2: Sort transactions
            portfolio_manager.sort_trxns()

            # Step 3: Process transactions to calculate leftover units per Broker-schema pair using folio
            portfolio_manager.process_trxns()

            # Step 4: Fetch current NAV for each scheme using isin
            portfolio_manager.fetch_nav()

            # Step 5: Calculate the total portfolio value
            total_value = portfolio_manager.calculate_total_portfolio_value()

            print("\nTotal Profolio Value :"+str(total_value))
        elif(choice == 2):
            portfolio_manager = PortfolioManager(file='transaction_detail.json')

            # Step 1: Read data from file
            portfolio_manager.read_data()

            # Step 2: Sort transactions
            portfolio_manager.sort_trxns()

            portfolio_manager.total_trxns()

            # Step 4: Fetch current NAV for each scheme using isin
            portfolio_manager.fetch_nav()

            # Step 5: Calculate the total portfolio gains
            total_value = portfolio_manager.calculate_total_portfolio_gain()
            print(total_value)

        else:
            print("Exiting...")
            exit(1)


if __name__ == "__main__":
    main()