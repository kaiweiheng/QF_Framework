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

		self.daily_price = dict()
		#init strategy with data retrived
		for ticker in self.holding_list:

			self.daily_price[ticker] = obb_Price_Collector.get_price_for_a_stock(ticker, start_date = self.data_start_date)		
			#to init your strategy for every product

		self.run_sim_at_a_data_set(data_set = 'training_price', plot_diff = True, plot_pnl = True)	

		self.run_sim_at_a_data_set(data_set = 'validation_price', plot_diff = True, plot_pnl = True)		

		self.run_sim_at_a_data_set(data_set = 'testing_price', plot_diff = True, plot_pnl = True)					
		

	def run_sim_at_a_data_set(self, data_set, plot_diff = False, plot_pnl = False):

		self.strategy_obj_list = []
		product_pairs = VIX_arbitrage.get_product_pairs(self.holding_list)
		for pairs in product_pairs:
			product_a_ticker , product_b_ticker = pairs[0], pairs[1]
			self.strategy_obj_list.append(  
				VIX_arbitrage(init_balance = 10000 , daily_price_hist = self.daily_price[product_a_ticker], ticker = product_a_ticker, sim_start_date = self.sim_start_date,
				VIX_his = self.indices_value_dict['^VVIX'], daily_price_of_another_product = self.daily_price[product_b_ticker] , ticker_of_another_product = product_b_ticker ))		

		aggregated_trading_record = []
		for obj in self.strategy_obj_list:

			quantiles =  obj.training_price['diff'].quantile([.1, .5]).values
			lower_quantile, higher_quantile = quantiles[0], quantiles[1]

			for date in getattr(obj, data_set)['date'].values:
			# for date in obj.training_dates:
				obj.determin_action_of_a_day(date, lower_quantile, higher_quantile)

			trade_record =  pd.DataFrame(obj.trade_record_for_paired_product,columns=['date', 'price', 'quantity','ticker']) 
			print("%s_%s %s traded %s, end value %s \n lower %.3f higher %.3f\n"%(obj.ticker, obj.ticker_of_another_product , data_set , obj.have_trigged_trade 
				, obj.total_value_records[-1], lower_quantile, higher_quantile ) )		

			for record in obj.trade_record_already_processed:
				aggregated_trading_record.append(record.to_DataFrame())

			trade_record = trade_record['quantity'].values


			# Simple_Anlysis.plot_two_factors_graph( getattr(obj, data_set)['date'].values, 
			# 	obj.total_value_records, getattr(obj, data_set)['diff'].values, 
			# 	"%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set) )
			Simple_Anlysis.plot_trade_and_diff_graph( getattr(obj, data_set)['date'].values, 
				obj.total_value_records, getattr(obj, data_set)['diff'].values, 
				"%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record )			

			# if plot_diff:
			# 	Simple_Anlysis.plot_trade_graph( getattr(obj, data_set)['date'].values, getattr(obj, data_set)['diff'].values, "%s_%s_%s_diff"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record)
			
			# if plot_pnl:
			# 	Simple_Anlysis.plot_trade_graph( getattr(obj, data_set)['date'].values, obj.total_value_records, "%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record)		

		# aggregated_trading_record = pd.concat(aggregated_trading_record)
		# aggregated_trading_record.to_csv(os.path.join('data','output','total_trade_record.csv'), index=False)


		return 0


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
