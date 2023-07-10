import sys
import logging
import datetime

sys.path.append("Price_Collector")
from obb_Price_Collector import *

sys.path.append("Strategy")
from Grid_Trade import *
from VIX_arbitrage import *

sys.path.append("Preprocess")
from Preprocessor import *



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
		self.benchmark_index = dict()

		#to get all necessary data to make analysis
		if underlying != None:
			# self.holding_list = openbb.etf.holdings(underlying).reset_index()
			self.holding_list, self.underlying_weight= obb_Price_Collector.get_underlying_holdings(underlying)
		
		if holding_list != None:
			for i in holding_list:
				self.holding_list.append(i)

		if indices != None:
			for index in indices:
				self.benchmark_index[index] = obb_Price_Collector.get_value_for_an_index(index)
				self.benchmark_index[index]['re_%s'%(index)] = Preprocessor.calculate_return(self.benchmark_index[index][ ['date','value'] ], 'value', 'value')
				self.benchmark_index[index]['c_%s'%(index)] = self.benchmark_index[index]['value']
				self.benchmark_index[index] = self.benchmark_index[index].dropna(subset = ['re_%s'%(index)])
				self.benchmark_index[index] = self.benchmark_index[index][['date','c_%s'%(index),'re_%s'%(index)]]

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

		# self.run_sim_at_a_data_set(data_set = 'testing_price', plot_diff = True, plot_pnl = True)					
		

	def run_sim_at_a_data_set(self, data_set, plot_diff = False, plot_pnl = False):

		self.strategy_obj_list = []
		product_pairs = VIX_arbitrage.get_product_pairs(self.holding_list)
		for pairs in product_pairs:
			product_a_ticker , product_b_ticker = pairs[0], pairs[1]
			self.strategy_obj_list.append(  
				VIX_arbitrage(init_balance = 10000 , daily_price_hist = self.daily_price[product_a_ticker], ticker = product_a_ticker, sim_start_date = self.sim_start_date,
				tracking_index_ticker = "^VVIX", tracking_index_hist = self.benchmark_index["^VVIX"]  , 
				daily_price_of_another_product = self.daily_price[product_b_ticker] , ticker_of_another_product = product_b_ticker ))		

		aggregated_trading_record = []
		for obj in self.strategy_obj_list:

			#to get hyperparameter from the training set
			quantiles =  obj.training_price['diff'].quantile([.1, .55]).values
			lower_quantile, higher_quantile = quantiles[0], quantiles[1]

			#simulation and evaluation
			for date in getattr(obj, data_set)['date'].values:
				obj.determin_action_of_a_day(date, lower_quantile, higher_quantile)

			trade_record =  pd.DataFrame(obj.trade_record_for_paired_product,columns=['date', 'price', 'quantity','ticker']) 

			for record in obj.trade_record_already_processed:
				aggregated_trading_record.append(record.to_DataFrame())

			trade_record = trade_record['quantity'].values


			# Simple_Anlysis.plot_trade_and_diff_graph( getattr(obj, data_set)['date'].values, 
			# 	obj.total_value_records, getattr(obj, data_set)['diff'].values, 
			# 	"%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record )	

			tmp = pd.merge(getattr(obj, data_set), self.benchmark_index['SP500'], how = 'inner', left_on = 'date', right_on = 'date' )


			Simple_Anlysis.plot_trade_and_diff_graph( getattr(obj, data_set)['date'].values, 
				obj.total_value_records, tmp['c_SP500'].values, 
				"%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record )

			# Simple_Anlysis.plot_trade_and_diff_graph( getattr(obj, data_set)['date'].values, 
			# 	getattr(obj, data_set)['mv10'].values, getattr(obj, data_set)['mv5'].values, 
			# 	"%s_%s_%s"%(obj.ticker, obj.ticker_of_another_product, data_set), trade_record )
	

			tmp = pd.DataFrame({ 'date': getattr(obj, data_set)['date'].values, 'total_value' : obj.total_value_records })
			tmp  = pd.merge(tmp, self.benchmark_index['SP500'], how = 'inner', left_on = 'date', right_on = 'date')


			assessment = obj.make_assessment(tmp, 'total_value', 'c_SP500', os.path.join('data','output','%s_%s'%(obj.ticker, obj.ticker_of_another_product) ), data_set, 'Q')


			print("%s_%s %s traded %s, end value %s \n lower %.3f higher %.3f \n"%(obj.ticker, obj.ticker_of_another_product , data_set , obj.have_trigged_trade 
				, obj.total_value_records[-1], lower_quantile, higher_quantile) )		




		aggregated_trading_record = pd.concat(aggregated_trading_record)
		aggregated_trading_record.to_csv(os.path.join('data','output','%s_total_trade_record.csv'%(data_set) ), index=False)


		return 0
