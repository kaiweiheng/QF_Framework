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
		# self.long_position_value, self.short_position_value = {self.ticker:0, self.ticker_of_another_product:0}, {self.ticker:0, self.ticker_of_another_product:0}
		# Simple_Anlysis.plot_single_factor_graph( self.testing_price['date'].values, self.testing_price['diff'].values, "%s_%s"%(self.ticker, self.ticker_of_another_product) )
		


	def determin_action_of_a_day(self, date):

		# get the diff of the date
		diff_of_the_day = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['diff'].values[0]
		price_for_this_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker)].values[0]
		price_for_paired_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker_of_another_product)].values[0]		
		
		self.trade_record_for_paired_product.append([date, price_for_this_product, 0, self.ticker])
		
		# if diff < - 0.1, long the pair
		if diff_of_the_day < -0.1 and self.last_time_action != 1:
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, 100, self.ticker]
			
			##############################################
			#for long product, deduct cash, update average price for long, add long position 
			self.trade_record.append([date, price_for_this_product, 100, self.ticker])
			self.cash = self.cash - 100 * price_for_this_product  #cash will be deducted if no short position on, otherwise add from avg price

			total_value_tmp = self.position_avg_price[self.ticker] * self.position[self.ticker]
			self.position_avg_price[self.ticker] = 0 if self.position[self.ticker] + 100 == 0 else  (total_value_tmp + 100*price_for_this_product)/( self.position[self.ticker]+ 100)
			
			self.position[self.ticker] += 100 
			##############################################			

			#for short position, deduct cash as margine, update average price for short, adding short position
			self.trade_record.append([date, price_for_paired_product, -100, self.ticker_of_another_product])			
			self.cash = self.cash + 100 * price_for_paired_product
			
			total_value_tmp = self.position_avg_price[self.ticker_of_another_product] * self.position[self.ticker_of_another_product]
			# self.position_avg_price[self.ticker_of_another_product] = (total_value_tmp - 100*price_for_paired_product)/( self.position[self.ticker_of_another_product] -100  )
			self.position_avg_price[self.ticker_of_another_product] = 0 if self.position[self.ticker_of_another_product] - 100 == 0 else  (total_value_tmp - 100*price_for_paired_product)/( self.position[self.ticker_of_another_product] -100  )
			
			##############################################
			self.position[self.ticker_of_another_product] -= 100  
			self.have_trigged_trade += 1
			self.last_time_action = 1
		# else if diff > 0.2 short the pair
		# elif diff_of_the_day > 0.1 and self.last_time_action != -1:
		elif diff_of_the_day > 0 and self.last_time_action == 1: # close long deal condition to be tried with integration of return changed, not only return
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, -100, self.ticker]			
			
			##############################################
			#close long order, add cash, update average price, deduct long position
			self.trade_record.append([date, price_for_this_product, -100, self.ticker])
			self.cash = self.cash + 100 * price_for_this_product

			total_value_tmp = self.position_avg_price[self.ticker] * self.position[self.ticker]
			self.position_avg_price[self.ticker] = 0 if self.position[self.ticker] - 100 == 0 else (total_value_tmp - 100*price_for_this_product)/( self.position[self.ticker] - 100)

			self.position[self.ticker] -= 100 
			##############################################
			self.trade_record.append([date, price_for_paired_product, 100, self.ticker_of_another_product])			
			self.cash = self.cash - 100 * price_for_paired_product

			total_value_tmp = self.position_avg_price[self.ticker_of_another_product] * self.position[self.ticker_of_another_product]
			self.position_avg_price[self.ticker_of_another_product] = 0 if self.position[self.ticker_of_another_product] + 100 == 0 else (total_value_tmp + 100*price_for_paired_product)/( self.position[self.ticker_of_another_product] + 100  )

			self.position[self.ticker_of_another_product] += 100

			self.have_trigged_trade += 1
			self.last_time_action = -1


		print(" %s  %s %s %s %s %s %s\n"%(date, self.ticker, self.position[self.ticker] ,self.position_avg_price[self.ticker] , 
			self.ticker_of_another_product, self.position[self.ticker_of_another_product], self.position_avg_price[self.ticker_of_another_product]))


		self.position_value[self.ticker] = self.position[self.ticker] * price_for_this_product
		self.position_value[self.ticker_of_another_product] = self.position[self.ticker_of_another_product] * price_for_paired_product


		self.total_value_records.append( self.cash + self.position_value[self.ticker] + self.position_value[self.ticker_of_another_product]  )
		return 0

	@staticmethod
	def get_product_pairs(product_list):
		output = []

		while len(product_list) > 0:
			for i in range(1,len(product_list)):
				output.append( [product_list[0], product_list[i]] )	
			product_list = product_list[1:]
		return output