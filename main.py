# %matplotlib inline
import sys
sys.path.append("Portfolio")
from Portfolio import *

# product_list = ["SVXY","QQQ","SPY","MSFT","TSM","PDD","AMD","CVX","XOM","TQQQ","BILI","NVDA","BABA"]

# hang seng tech index 
# KTEC, EWH
# holding_list = ["SVXY"],

#other idea is to compare tech/borad market 
# simulator = Portfolio(total_balance = 100000, underlying = None,holding_list = ["SVXY","VIXY"], indices = ["^VVIX"], data_start_date = "2012-01-01", sim_start_date = "2015-09-01" )
simulator = Portfolio(total_balance = 100000, underlying = "QQQ",holding_list = ["SVXY"],  data_start_date = "2012-01-01", sim_start_date = "2015-09-01" )