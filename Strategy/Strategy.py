# import logging
# logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
# rootLogger = logging.getLogger()

# # fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
# # fileHandler.setFormatter(logFormatter)
# # rootLogger.addHandler(fileHandler)

# consoleHandler = logging.StreamHandler()
# consoleHandler.setFormatter(logFormatter)
# rootLogger.addHandler(consoleHandler)

# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S')

import os
import datetime
import numpy as np
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from Order import *


class Strategy(object):
	"""
	Parents Class for all Strategy 
		-- all Strategy should inheritate this class  
		-- All Child Class should implement determin_action_of_a_day
		-- within determin_actiion_of_a_day should update self.trade_record indicate long or short
		-- Containing some tools to do simple analysis in general use, like draw a graph

	balace: float, init balance allowance for a strategy on a product 
	daily_price_hist: pd.Dataframe, price hist, o, h, l, c for a product
	ticker: str, ticker for a product
	trade_record: list [[date, price, quantity]], quantity < 0 means short

	"""
	def __init__(self, **args):
		super(Strategy, self).__init__()
		self.cash= args['init_balance']

		self.position, self.position_avg_price = dict(), dict()
		self.total_value_records = []

		self.daily_price_hist = args['daily_price_hist']
		
		self.data_start_date, self.data_end_date = min(self.daily_price_hist['date']), max(self.daily_price_hist['date'])
		self.sim_start_date = args['sim_start_date']

		self.ticker = args['ticker']

		# Order(date = date , ticker = self.ticker, price = price_for_this_product, quantity = quantity)
		self.trade_record, self.trade_record_already_processed = [], []

		self.have_trigged_trade = 0

		self.last_time_action = 0 # 0 for init, -1 for short and 1 for long

		# self.position, self.position_avg_price = {}, {}
		# self.cash = args['init_balance']
		print("%s, start %s , end %s total %s records \n"%(self.ticker, self.data_start_date, self.data_end_date, len(self.daily_price_hist)))


	def determin_action_of_a_day(self):
		raise NotImplementedError()

	def get_trade_records_for_a_day(self, date):
		#selecting trading records in that date by iterating trading records
		trading_records_of_a_day = []
		for record in self.trade_record:
			if record.date == date:
				trading_records_of_a_day.append(record)
				self.trade_record_already_processed.append(record)
		self.trade_record = []
		return trading_records_of_a_day

	def determin_position_of_a_day(self, date, comission = 1):
		trading_records_of_a_day = self.get_trade_records_for_a_day(date)

		#for each each product, update it's quantity and avg price after making deals at that date
		for record in trading_records_of_a_day:
			price, quantity, ticker= record.price, record.quantity, record.ticker 
			if ticker not in self.position.keys():
				quantity_before_action = 0
				avg_price_before_actiion = 0

				self.position[ ticker ] = quantity
				self.position_avg_price[ ticker ] = price

			else:
				quantity_before_action = self.position[ ticker ]
				avg_price_before_actiion = self.position_avg_price[ ticker ]
				
				self.position[ ticker ] += quantity
				self.position_avg_price[ ticker ] = 0 if self.position[ ticker ] == 0 else\
				(quantity_before_action * avg_price_before_actiion + price * quantity ) / (self.position[ ticker ])

			#entry or adding position in the same direction
			if (quantity_before_action <= 0 and quantity < 0) or (quantity_before_action >= 0 and quantity > 0):
				self.cash = self.cash - abs(price * quantity) # - Strategy.determine_commission(quantity) 
			else: 
				#to close position in the opposite direction to the existed,
				#updated cash = pervious cash + return margine + pnl
				self.cash += self.determine_value_for_a_product_of_a_day(quantity, avg_price_before_actiion, price) 

			if comission == 1:
				self.cash -= Strategy.determine_commission(quantity)

	def determine_pnl_related_of_a_product(self, ticker, price):
		'''
		method to define the pnl and rate for a product if close the deal now

		return: pnl_rate, pnl, margine, comssion
		'''
		if ticker not in self.position.keys():
			self.position[ticker], self.position_avg_price[ticker] = 0, 0

		quantity, avg_price = -1 * self.position[ticker], self.position_avg_price[ticker]
		product_pnl = self.determine_pnl_for_a_product_of_a_day(quantity = quantity, avg_price = avg_price, current_price = price)
		product_value = self.determine_margine_for_a_product_of_a_day(quantity = quantity, avg_price = avg_price )
		comission = self.determine_commission(quantity = quantity)
		pnl_rate = 0 if product_value == 0 else (product_pnl - comission)/product_value

		return pnl_rate , product_pnl - comission, product_value, comission

	@staticmethod
	def determine_commission(quantity):
		# https://www.futuhk.com/commissionnew?lang=zh-hk
		comission = max(0.99, quantity * 0.0049) + max(1.0, quantity * 0.005) + 0.003 * quantity 
		if quantity < 0:
			comission  = comission + 0.000008 * quantity + min( 7.27, max(0.01, 0.000145 * quantity) )
		return comission 

	@staticmethod
	def determine_pnl_for_a_product_of_a_day(quantity, avg_price, current_price, comission = 1):
		pnl = quantity * (avg_price - current_price)
		if comission == 1:
			pnl -= Strategy.determine_commission(quantity)
		return pnl

	@staticmethod
	def determine_margine_for_a_product_of_a_day(quantity, avg_price):
		return abs(quantity * avg_price)


	@staticmethod
	def determine_value_for_a_product_of_a_day(quantity, avg_price, current_price, comission = 1):
		'''
		if close position quantity should be quantity traded at that date
		else generally enquiry pnl, quantity should be all the -1 * quantity holding in hand (close position at once)
		'''
		# return abs(quantity * avg_price) + quantity * (avg_price - current_price)
		return Strategy.determine_margine_for_a_product_of_a_day(quantity, avg_price) + Strategy.determine_pnl_for_a_product_of_a_day(quantity, avg_price, current_price, comission)	

	def get_sim_dates(self, limit_num_of_dates = None):
		if type(limit_num_of_dates) == int:
			return  self.daily_price_hist[ self.daily_price_hist['date'] >= self.sim_start_date ]['date'].values[: limit_num_of_dates]
		return self.daily_price_hist[ self.daily_price_hist['date'] >= self.sim_start_date ]['date'].values

	def get_training_val_date(self, split_portion = 0.8):
		training_dates  = self.daily_price_hist[ (self.daily_price_hist['date'] >= self.data_start_date) & (self.daily_price_hist['date'] < self.sim_start_date) ]['date'].values
		val_dates = training_dates[int(split_portion * len(training_dates) ):  ]
		training_dates = training_dates[: int(split_portion * len(training_dates) )]
		return training_dates, val_dates

	def plot_trade_graph(self, date, price_hist):
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s.png"%(self.ticker))
		Strategy.check_parents_dir_exist(output_path)

		x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		y = price_hist

		fig, ax = plt.subplots()
		ax.plot(x, y, 'w', linewidth=0.25, label="c")

		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(self.ticker))
		ax.grid()
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)


	@staticmethod
	def check_parents_dir_exist(path):
		parents_dir = os.path.dirname(path)
		if not os.path.exists(parents_dir):
			os.makedirs(parents_dir)		

	@staticmethod
	def plot_trade_graph(date, price_hist, ticker):
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		y = price_hist

		fig, ax = plt.subplots()
		ax.plot(x, y, 'w', linewidth=0.25, label="c")

		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(ticker))
		ax.grid()
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)


	@staticmethod
	def select_rows_according_to_dates(df, starting_date = None, ending_date = None):
		if starting_date == None: starting_date = min(df['date'].values) 
		if ending_date == None  :   ending_date =  max(df['date'].values) 
		return df[ (df['date'] >= starting_date ) & ( df['date'] <= ending_date ) ]