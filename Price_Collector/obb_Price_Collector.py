import os
import pandas as pd

# import openbb 
from openbb_terminal.sdk import widgets
from openbb_terminal.sdk import openbb
from openbb_terminal.helper_classes import TerminalStyle
from openbb_terminal.core.config.paths import REPOSITORY_DIRECTORY

from Price_Collector import *
import datetime
class obb_Price_Collector(Price_Collector):
	"""docstring for obb_Price_Collector"""
	def __init__(self, arg):
		super(obb_Price_Collector, self).__init__()
		self.arg = arg
	
	@staticmethod
	def get_price_for_a_stock(ticker, start_date = '2000-01-01', end_date = '2023-04-01'):

		# US_daily = openbb.stocks.load(symbol = US_ticker,start_date = '2000-11-01', source = "AlphaVantage")
		path = os.path.join('data','raw','openbb','%s.csv'%(ticker))
		daily_price = Price_Collector.read_csv_if_exist(path)
		if type(daily_price) == bool and daily_price == False:
			Price_Collector.check_parents_dir_exist(path)
			daily_price = openbb.stocks.load(symbol = ticker,start_date = start_date, end_date = end_date)
			daily_price = daily_price.reset_index()
			daily_price = daily_price.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Adj Close": "adj_c", "Volume": "v"})			
			
			if len(daily_price) > 0:
				daily_price.to_csv(path,  index = False)
			else:
				print("no price data for %s between %s and %s\n"%(ticker, start_date, end_date))
			daily_price = Price_Collector.read_csv_if_exist(path)

		daily_price['date'] = pd.to_datetime(daily_price['date'], format='%Y-%m-%d') 
		
		return daily_price


	@staticmethod
	def get_underlying_holdings(etf_ticker):
		cons_weights, cons_names = dict(), dict()
		path = os.path.join('data','raw','openbb','%s.csv'%(etf_ticker))
		etf_cons = Price_Collector.read_csv_if_exist(path)
		if type(etf_cons) == bool and etf_cons == False:
			Price_Collector.check_parents_dir_exist(path)			
			etf_cons = openbb.etf.holdings(etf_ticker).reset_index()
			etf_cons = etf_cons.rename(columns = {"Symbol":"ticker", "Name":"Name", "% Of Etf":"Weight"} )
			etf_cons.to_csv(path , index = False)

		etf_cons = etf_cons[  (etf_cons['Name']  != 'Cash') ]

		etf_cons['Weight'] = [ float(i[:-1])/100  for i in etf_cons['Weight'].values ] 
		holding_list = etf_cons['ticker'].to_list()

		# Need special dealing with HK stocks, like 0700.HK displayed as 700.HK
		return holding_list, etf_cons


	@staticmethod
	def get_value_for_an_index(ticker):

		# index_avaliable = openbb.economy.available_indices()
		# display(index_avaliable)
		path = os.path.join('data','raw','openbb','%s.csv'%(ticker))
		index_values = Price_Collector.read_csv_if_exist(path)
		if type(index_values) == bool and index_values == False:
			Price_Collector.check_parents_dir_exist(path)
			index_values = openbb.economy.index([ticker]).reset_index()
			index_values = index_values.rename(columns = {"Date":"date", ticker:"value"} )
			
			if len(index_values) > 0:
				index_values.to_csv(path,  index = False)
			else:
				print("no price data for %s between %s and %s\n"%(ticker, start_date, end_date))
			index_values = Price_Collector.read_csv_if_exist(path)			

		index_values['date'] = pd.to_datetime(index_values['date'], format='%Y-%m-%d')			
		return index_values