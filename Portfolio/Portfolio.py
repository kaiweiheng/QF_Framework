import sys
import logging
import datetime

sys.path.append("Price_Collector")
from obb_Price_Collector import *

sys.path.append("Strategy")
from Grid_Trade import *
from VIX_arbitrage import *

class Portfolio(object):
	"""
	Portfolio
		-- class to get data, sim strategy and compare with underlying


	underlying: str, benchmark instrument code usually an ETF 
	holding_list: list str, 
	

	"""
	def __init__(self, underlying = None, holding_list = None, indices = None, **arg ):
		super(Portfolio, self).__init__()
		# self.arg = arg


		self.underlying = underlying
		self.total_balance = arg['total_balance']
		self.data_start_date = arg['data_start_date']
		self.sim_start_date = arg['sim_start_date']
		#init the total balance
		self.strategy_obj_list = []
		self.holding_list = []
		self.indices_value_dict = dict()

		#to get all necessary data to make analysis
		if underlying != None:
			# self.holding_list = openbb.etf.holdings(underlying).reset_index()
			self.holding_list, self.underlying_weight= obb_Price_Collector.get_underlying_holdings(underlying)
		
		if holding_list != None:
			for i in holding_list:
				self.holding_list.append(i)

		if indices != None:
			for index in indices:
				self.indices_value_dict[index] = obb_Price_Collector.get_value_for_an_index(index)


		self.holding_list = [l for l in self.holding_list if type(l) != float] #in case cash holding for etf will cause error
		print("Retriving Data for Following products %s \n"%(self.holding_list))

		num_of_sim_date = 200 #for debug hardcode, to let graph easier to look

		daily_price = dict()
		#init strategy with data retrived
		for ticker in self.holding_list:

			daily_price[ticker] = obb_Price_Collector.get_price_for_a_stock(ticker, start_date = self.data_start_date)		
			#to init your strategy for every product


			# self.strategy_obj_list.append(
			# 	Grid_Trade( init_balance = self.total_balance/len(self.holding_list), daily_price_hist = daily_price, ticker = ticker, sim_start_date = daily_price['date'].values[0],
			# 	n_band_one_side = 5, band_interval = 0.025 ) )			


		product_pairs = VIX_arbitrage.get_product_pairs(self.holding_list)
		for pairs in product_pairs:
			product_a_ticker , product_b_ticker = pairs[0], pairs[1]
			self.strategy_obj_list.append(  
				VIX_arbitrage(init_balance = 10000 , daily_price_hist = daily_price[product_a_ticker], ticker = product_a_ticker, sim_start_date = self.sim_start_date,
				VIX_his = self.indices_value_dict['^VVIX'], daily_price_of_another_product = daily_price[product_b_ticker] , ticker_of_another_product = product_b_ticker ))

		#optimized hyperparameter by using data >= data_date and > sim_date TBD
		for obj in self.strategy_obj_list:
			# training_dates, _ = obj.get_training_val_date()

			print("init_cash = %s \n" %(obj.cash))
			for date in obj.sim_dates:
				obj.determin_action_of_a_day(date)

			trade_record =  pd.DataFrame(obj.trade_record_for_paired_product,columns=['date', 'price', 'quantity','ticker']) 
			print("%s_%s traded %s %s %s \n"%(obj.ticker, obj.ticker_of_another_product , obj.have_trigged_trade, trade_record['quantity'].sum(), obj.total_value_records[-1] ) )


			# print(pd.DataFrame(obj.trade_record,columns=['date', 'price', 'quantity','ticker']))

			trade_record = trade_record['quantity'].values
			# Simple_Anlysis.plot_trade_graph( obj.testing_price['date'].values, obj.testing_price['diff'].values, "%s_%s"%(obj.ticker, obj.ticker_of_another_product), trade_record)
			
			Simple_Anlysis.plot_trade_graph( obj.testing_price['date'].values, obj.total_value_records, "%s_%s"%(obj.ticker, obj.ticker_of_another_product), trade_record)			
			Simple_Anlysis.plot_trade_graph( obj.testing_price['date'].values, obj.integration_records, "%s_%s_integration"%(obj.ticker, obj.ticker_of_another_product), trade_record)						

			#check the distribution of training, validation and sim, to varifify patterns are consistant all crossing the time

			#pick the top 5% diff in training see the effectiveness, with trading cost

			#proporgate to validation set, and come up with diff margine see if it is profitable

			# print(len(training_dates))	



		'''
		#simulate with optimized hyperparameter as out sample testing
		for obj in self.strategy_obj_list:
			sim_dates = obj.get_sim_dates(num_of_sim_date)
			for date in sim_dates:
				obj.determin_action_of_a_day(date)

		# eval and draw results
		for obj in self.strategy_obj_list:
			sim_dates = obj.get_sim_dates(num_of_sim_date)
			if obj.have_trigged_trade != 0:
				obj.plot_trade_graph( sim_dates , obj.daily_peice_hist[ (obj.daily_peice_hist['date'] >= sim_dates[0]) & (obj.daily_peice_hist['date'] <= sim_dates[-1])   ]['c'].values)
				print("%s traded %s \n"%(obj.ticker, obj.have_trigged_trade))
		'''
