import sys

sys.path.append("Analysis")
from Simple_Anlysis import *

sys.path.append("Preprocess")
from Preprocessor import *

from Strategy import *
import pandas as pd
import numpy as np 


class VIX_arbitrage(Strategy):
	"""docstring for VIX_arbitrage"""
	def __init__(self, **args):
		super(VIX_arbitrage, self).__init__(**args)
		# self.arg = arg


		self.daily_price_of_another_product = args['daily_price_of_another_product']
		self.ticker_of_another_product = args['ticker_of_another_product']

		self.daily_price_of_another_product['c_%s'%(self.ticker_of_another_product)] =  self.daily_price_of_another_product['c']
		self.daily_price_of_another_product['re_%s'%(self.ticker_of_another_product)] = Preprocessor.calculate_return(self.daily_price_of_another_product[ ['date','c']])
		self.daily_price_of_another_product = self.daily_price_of_another_product[['date','c_%s'%(self.ticker_of_another_product),'re_%s'%(self.ticker_of_another_product)]]
		

		self.daily_price_hist['c_%s'%(self.ticker)] = self.daily_price_hist['c']
		self.daily_price_hist['re_%s'%(self.ticker)] = Preprocessor.calculate_return( self.daily_price_hist[['date','c']] )
		self.daily_price_hist = self.daily_price_hist[['date','c_%s'%(self.ticker),'re_%s'%(self.ticker)]]


		self.daily_price_hist = pd.merge(self.daily_price_hist, self.daily_price_of_another_product, how = 'inner', left_on = 'date', right_on = 'date')

		self.daily_price_hist['diff'] = self.daily_price_hist['re_%s'%(self.ticker)] - self.daily_price_hist['re_%s'%(self.ticker_of_another_product)]
		self.daily_price_hist = self.daily_price_hist.dropna(subset = ['diff'])

		print("%s %s \n"%(self.ticker, self.ticker_of_another_product))
		print( self.daily_price_hist[['re_%s'%(self.ticker),'re_%s'%(self.ticker_of_another_product)]].corr() )
		# print(self.daily_price_hist.describe())

		self.training_dates, self.validation_dates = self.get_training_val_date()
		self.sim_dates = self.get_sim_dates()

		self.training_price = self.select_rows_according_to_dates(self.daily_price_hist, self.training_dates[0], self.training_dates[-1])
		self.validation_price = self.select_rows_according_to_dates(self.daily_price_hist, self.validation_dates[0], self.validation_dates[-1])
		self.testing_price = self.select_rows_according_to_dates(self.daily_price_hist, self.sim_dates[0], self.sim_dates[-1])				

		 # self.trade_record = pd.DataFrame(columns=['date', 'price', 'quantity','product_ticker'])
		self.trade_record_for_paired_product = []
		# print(dir(Simple_Anlysis))
		Simple_Anlysis.return_histogram([self.training_price['diff'].values, self.validation_price['diff'].values, self.testing_price['diff'].values], 
			['train','val','testing'],
			"%s_%s"%(self.ticker, self.ticker_of_another_product))


		self.position = {self.ticker:0, self.ticker_of_another_product:0}
		self.position_avg_price = {self.ticker:0, self.ticker_of_another_product:0}		

		self.integration = 1
		self.integration_records = []
		self.integration_tmp = 1
		# Simple_Anlysis.plot_single_factor_graph( self.testing_price['date'].values, self.testing_price['diff'].values, "%s_%s"%(self.ticker, self.ticker_of_another_product) )
		


	def determin_action_of_a_day(self, date, lower_quantile = -0.1, higher_quantile = 0):

		# get the diff of the date
		diff_of_the_day = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['diff'].values[0]
		price_for_this_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker)].values[0]
		price_for_paired_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker_of_another_product)].values[0]		
		
		self.integration = self.integration * (1 + diff_of_the_day)
		self.integration_records.append(self.integration)

		self.trade_record_for_paired_product.append([date, price_for_this_product, 0, self.ticker])
		quantity = 100

		if diff_of_the_day < lower_quantile and self.last_time_action != 1:
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, quantity, self.ticker]
			
			self.trade_record.append([date, price_for_this_product, quantity, self.ticker])
			#deduct margine if adding or no position, if close position return margine and calculate pnl 
			self.cash = self.cash - quantity * price_for_this_product  if self.position[self.ticker] >= 0 else \
			self.cash + quantity * self.position_avg_price[self.ticker] + quantity * (self.position_avg_price[self.ticker] - price_for_this_product)

			total_value_tmp = self.position_avg_price[self.ticker] * self.position[self.ticker]
			self.position_avg_price[self.ticker] = 0 if self.position[self.ticker] + quantity == 0 else \
			(total_value_tmp + quantity*price_for_this_product)/( self.position[self.ticker] + quantity)
			
			self.position[self.ticker] += quantity 


			self.trade_record.append([date, price_for_paired_product, -quantity, self.ticker_of_another_product])			
			#deduct margine if adding or no position, if close position return margine and calculate pnl
			self.cash = self.cash - quantity * price_for_paired_product if self.position[self.ticker_of_another_product] <= 0 else \
			self.cash + quantity * self.position_avg_price[self.ticker_of_another_product] + quantity * (price_for_paired_product - self.position_avg_price[self.ticker_of_another_product])
			
			total_value_tmp = self.position_avg_price[self.ticker_of_another_product] * self.position[self.ticker_of_another_product]
			self.position_avg_price[self.ticker_of_another_product] = 0 if self.position[self.ticker_of_another_product] - quantity == 0 else\
			(total_value_tmp - quantity*price_for_paired_product)/( self.position[self.ticker_of_another_product] - quantity  )
			
			self.position[self.ticker_of_another_product] -= quantity  
			
			self.have_trigged_trade += 1
			self.last_time_action = 1

			self.integration = 1 * (1 + diff_of_the_day)
			# self.integration
			self.integration_records[-1] = self.integration
			self.integration_tmp = (self.integration + 1) / 2

		# elif diff_of_the_day > higher_quantile and self.last_time_action == 1: 
		#or considering stop profit in 50 bps or 100 bps
		elif self.integration > 1 and self.last_time_action == 1:
	
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, -quantity, self.ticker]			
			
			self.trade_record.append([date, price_for_this_product, -quantity, self.ticker])
			#deduct margine if adding or no position, if close position return margine and calculate pnl
			self.cash = self.cash - quantity * price_for_this_product if self.position[self.ticker] <= 0 else \
			self.cash + quantity * self.position_avg_price[self.ticker] + quantity * (price_for_this_product - self.position_avg_price[self.ticker])

			total_value_tmp = self.position_avg_price[self.ticker] * self.position[self.ticker]
			self.position_avg_price[self.ticker] = 0 if self.position[self.ticker] - quantity == 0 else\
			(total_value_tmp - quantity*price_for_this_product)/( self.position[self.ticker] - quantity)

			self.position[self.ticker] -= quantity 

			self.trade_record.append([date, price_for_paired_product, quantity, self.ticker_of_another_product])			
			#deduct margine if adding or no position, if close position return margine and calculate pnl
			self.cash = self.cash - quantity  * price_for_paired_product if self.position[self.ticker_of_another_product] >= 0 else \
			self.cash + quantity * self.position_avg_price[self.ticker_of_another_product] + quantity * (self.position_avg_price[self.ticker_of_another_product] - price_for_paired_product)


			total_value_tmp = self.position_avg_price[self.ticker_of_another_product] * self.position[self.ticker_of_another_product]
			self.position_avg_price[self.ticker_of_another_product] = 0 if self.position[self.ticker_of_another_product] + quantity == 0 else \
			(total_value_tmp + quantity*price_for_paired_product)/( self.position[self.ticker_of_another_product] + quantity  )

			self.position[self.ticker_of_another_product] += quantity

			self.have_trigged_trade += 1
			self.last_time_action = -1

			# self.integration = 1
			# self.integration_records[-1] = diff_of_the_day


		self.position_value[self.ticker] = abs(self.position[self.ticker] * self.position_avg_price[self.ticker])+\
		self.position[self.ticker] * (price_for_this_product - self.position_avg_price[self.ticker]) 

		self.position_value[self.ticker_of_another_product] = abs(self.position[self.ticker_of_another_product] * self.position_avg_price[self.ticker_of_another_product]) +\
		self.position[self.ticker_of_another_product] * (price_for_paired_product - self.position_avg_price[self.ticker_of_another_product]) 


		# print(" %s %s, %s %s %s %s %s, %s %s %s %s %s\n"%(date, self.cash, self.ticker, self.position[self.ticker] , price_for_this_product ,self.position_value[self.ticker], self.position_avg_price[self.ticker] , 
		# 	self.ticker_of_another_product, self.position[self.ticker_of_another_product], price_for_paired_product ,self.position_value[self.ticker_of_another_product], self.position_avg_price[self.ticker_of_another_product] ))

		self.total_value_records.append( self.cash + abs(self.position_value[self.ticker]) + abs(self.position_value[self.ticker_of_another_product])  )
		# return 0

	@staticmethod
	def get_product_pairs(product_list):
		output = []

		while len(product_list) > 0:
			for i in range(1,len(product_list)):
				output.append( [product_list[0], product_list[i]] )	
			product_list = product_list[1:]
		return output