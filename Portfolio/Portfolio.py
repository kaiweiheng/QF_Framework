import logging
import sys
sys.path.append("Price_Collector")
from obb_Price_Collector import *

sys.path.append("Strategy")
from Grid_Trade import *
from VIX_Trade import *


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

		for ticker in self.holding_list:

			daliy_price = obb_Price_Collector.get_price_for_a_stock(ticker, start_date = self.data_start_date)		

			#to init your strategy for every product
			self.strategy_obj_list.append(
				Grid_Trade( init_balance = self.total_balance/len(self.holding_list), daily_peice_hist = daliy_price, ticker = ticker, sim_start_date = daliy_price['date'].values[0],
				n_band_one_side = 5, band_interval = 0.025 ) )			

			# self.strategy_obj_list.append(  
			# 	VIX_Trade(init_balance = self.total_balance/len(self.holding_list), daily_peice_hist = daliy_price, ticker = ticker, sim_start_date = daliy_price['date'].values[0],
			# 	VIX_his = self.indices_value_dict['^VVIX'])
			#   )



		# portfolio_simulate_dates  =  [ obj.daily_peice_hist['date'] for obj in self.strategy_obj_list if len(obj.daily_peice_hist) == max([ len(obj.daily_peice_hist) for obj in self.strategy_obj_list ]) ][0]

		


		num_of_date_to_sim = 300 #for debug hardcode, to let graph easier to look
		for obj in self.strategy_obj_list:
			obj.daily_peice_hist[  obj.daily_peice_hist['date'] >= self.sim_start_date ]
			for date in obj.daily_peice_hist['date'].values[:num_of_date_to_sim ]:
				obj.determin_action_of_a_day(date)


		for obj in self.strategy_obj_list:
			if obj.have_trigged_trade != 0:
				obj.plot_trade_graph(obj.daily_peice_hist['date'].values[:num_of_date_to_sim ] ,obj.daily_peice_hist['c'].values[:num_of_date_to_sim ])
				print("%s %s \n"%(obj.ticker, obj.have_trigged_trade))



	def simulate(self):

		return 0