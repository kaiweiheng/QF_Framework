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
		self.balance = args['init_balance'] 
		self.daily_peice_hist = args['daily_peice_hist']
		
		self.data_start_date, self.data_end_date = min(self.daily_peice_hist['date']), max(self.daily_peice_hist['date'])

		self.ticker = args['ticker']
		# self.trade_record = pd.DataFrame(columns=['date', 'price', 'quantity'])
		self.trade_record = []
		print("%s, start %s , end %s total %s records \n"%(self.ticker, self.data_start_date, self.data_end_date, len(self.daily_peice_hist)))

		# logging.info("%s created \n"%(self.ticker))

	def determin_action_of_a_day(self):
		raise NotImplementedError()


	def convert_trade_record_to_dataframe(self):
		return pd.DataFrame(self.trade_record,columns=['date', 'price', 'quantity'])


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

		return 0

	@staticmethod
	def check_parents_dir_exist(path):
		parents_dir = os.path.dirname(path)
		if not os.path.exists(parents_dir):
			os.makedirs(parents_dir)		