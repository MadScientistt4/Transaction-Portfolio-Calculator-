# Transaction Portfolio Calculator 
## Setup
- Install python3 if not installed already
- Clone the repository using: `git clone https://github.com/MadScientistt4/Transaction-Portfolio-Calculator-.git`
- cd into the project root folder
- Create a Python3 virtual env using: `python3 -m venv ./virtualenv`
- Activate the virtual env for your command line,

For Windows:
`.\virtualenv\Scripts\activate`

For Linux:
`source ./virtualenv/bin/activate`
- install packages using requirements.txt file `pip install -r requirements.txt`
  
  ## Run
- cd into the project root folder
- Activate virtual env like mentioned above
- You can choose how to calculated NAV(net asset values) values by 2 methods:
- 1. by using the data in dtSummary
  2. by using mstarpy library
- Now you can calculate your Total Portfolio and Portfolio gains or XIFF of portfolio

# Working of Code:
- Sorting dataTransaction in file by date
- Process Transactions by FIFO method per scheme
- Fetching NAV(net asset values) using ISIN of scheme
- Calulating Portfolio Value = sum (units of scheme x NAV of scheme)
- Caluting Portfolio Gains = sum (( remaining unit of scheme x Current NAV ) - Amount of money spent in purchasing scheme)
- Calulating XIRR using the portfolio value
  
# Answers Obtained for given transactions.json
- Portfolio Value - 45,68,788.7004
- Portfolio Gains - 11,92,570.9704
- XIRR for portfolio - 64.87%
 
