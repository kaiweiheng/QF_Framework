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


		self.training_dates, self.validation_dates = self.get_training_val_date()
		self.sim_dates = self.get_sim_dates()

		self.training_price = self.select_rows_according_to_dates(self.daily_price_hist, self.training_dates[0], self.training_dates[-1])
		self.validation_price = self.select_rows_according_to_dates(self.daily_price_hist, self.validation_dates[0], self.validation_dates[-1])
		self.testing_price = self.select_rows_according_to_dates(self.daily_price_hist, self.sim_dates[0], self.sim_dates[-1])				


		self.trade_record_for_paired_product = []

		# Simple_Anlysis.return_histogram([self.training_price['diff'].values, self.validation_price['diff'].values, self.testing_price['diff'].values], ['train','val','testing'],
		# 	"%s_%s"%(self.ticker, self.ticker_of_another_product))


		self.integration = 1
		self.integration_records = []

		# Simple_Anlysis.plot_single_factor_graph( self.testing_price['date'].values, self.testing_price['diff'].values, "%s_%s"%(self.ticker, self.ticker_of_another_product) )
		

	def determin_action_of_a_day(self, date, lower_quantile = -0.1, higher_quantile = 0):

		# at the beginning of the day, get essential info
		diff_of_the_day = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['diff'].values[0]
		price_for_this_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker)].values[0]
		price_for_paired_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker_of_another_product)].values[0]		
		
		self.integration = self.integration * (1 + diff_of_the_day)
		self.integration_records.append(self.integration)

		# define pnl from position of yesterday
		_, product_pnl, product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker, price_for_this_product)
		_, paired_product_pnl, paired_product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker_of_another_product, price_for_paired_product)
		total_pnl_rate = 0 if (product_margine + paired_product_margine) == 0 else (product_pnl + paired_product_pnl)/ (product_margine + paired_product_margine)

		max_quantity_to_open_paried_product = max( 0, int(self.cash / (price_for_this_product +  price_for_paired_product)) )
		max_quantity_to_close_paired_product = max(0, self.position[self.ticker] )
		# print("%s %s \n"%(max_quantity_to_open_paried_product, max_quantity_to_close_paired_product))
		quantity = 100
		#dummy record even no deal actually happen at this date
		self.trade_record_for_paired_product.append([date, price_for_this_product, 0, self.ticker])


		if diff_of_the_day < lower_quantile and self.last_time_action != 1:
			quantity = max_quantity_to_open_paried_product
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, quantity, self.ticker]

			self.trade_record.append(Order(date = date , ticker = self.ticker, price = price_for_this_product, quantity = quantity))			
			self.trade_record.append(Order(date = date , ticker = self.ticker_of_another_product, price = price_for_paired_product, quantity = -quantity))
						
			self.have_trigged_trade += 1
			self.last_time_action = 1

			self.integration = 1 * (1 + diff_of_the_day)
			self.integration_records[-1] = self.integration

		#or considering stop profit in 50 bps or 100 bps
		#to be define the optimal exist condition
		# elif diff_of_the_day > higher_quantile and self.last_time_action == 1:
		elif total_pnl_rate > 0.05 and self.last_time_action == 1:
		# elif self.integration > 1 and self.last_time_action == 1:	
			quantity = max_quantity_to_close_paired_product
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, -quantity, self.ticker]			
			
			self.trade_record.append(Order(date = date , ticker = self.ticker, price = price_for_this_product, quantity = -quantity))
			self.trade_record.append(Order(date = date , ticker = self.ticker_of_another_product, price = price_for_paired_product, quantity = quantity))

			self.have_trigged_trade += 1
			self.last_time_action = -1

			# self.integration = 1
			# self.integration_records[-1] = diff_of_the_day


		self.determin_position_of_a_day(date, comission = 1)

		_, product_pnl, product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker, price_for_this_product)
		_, paired_product_pnl, paired_product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker_of_another_product, price_for_paired_product)
		self.total_value_records.append(self.cash + product_pnl + product_margine + paired_product_pnl + paired_product_margine )


	@staticmethod
	def get_product_pairs(product_list):
		'''
		this method to get product pairs for arbitrage
		usually it envolve to long a product and short another in the same time
		'''
		output = []

		while len(product_list) > 0:
			for i in range(1,len(product_list)):
				output.append( [product_list[0], product_list[i]] )	
			product_list = product_list[1:]
		return output