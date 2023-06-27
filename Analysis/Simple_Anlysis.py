import os
import xlsxwriter
from Strategy import *
from datetime import date
import matplotlib.pyplot as plt

class Simple_Anlysis(object):
	"""docstring for Simple_Anlysis"""
	def __init__(self, arg):
		super(Simple_Anlysis, self).__init__()
		self.arg = arg
	
	@staticmethod
	def return_histogram(data_list, labels,  file_name):
		plt.style.use('seaborn-deep')
		n_bins = 100
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s_return_histogram.png"%(file_name))
		Strategy.check_parents_dir_exist(output_path)

		fig, ax = plt.subplots()
		# for i in range(0, len(data_list)):
		# 	# ax.hist(data,histtype="stepfilled", bins=n_bins, alpha=0.5, density=True)
		# 	ax.hist(data_list[i], n_bins, histtype='step', stacked=True, fill=False, density = True, label = labels[i])		
		ax.hist(data_list, n_bins, label = labels, density = True)					
		ax.legend(loc = 'upper right',prop={'size': 7})
		ax.set_title('stack step (unfilled)')
		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)



	@staticmethod
	def plot_single_factor_graph(date, price_hist, ticker, if_save = False):
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		x, y = date, price_hist

		fig, ax = plt.subplots()
		fig.set_figheight(8)
		fig.set_figwidth(int(len(date))/10)
		ax.plot(x, y, 'w', linewidth=0.25)

		ax.set(xlabel='time', ylabel='y1', title='%s Trade Record'%(ticker))
		ax.grid(color = 'w')
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		# ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(5)))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab

		if if_save:
			fig.savefig(output_path, dpi = 250)

		return ax, fig

	@staticmethod
	def plot_two_factors_graph(date, y1, y2, ticker, if_save = False):
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		ax, fig = Simple_Anlysis.plot_single_factor_graph(date = date, price_hist = y1, ticker = ticker)
		color = 'c'
		x = date
		ax2 = ax.twinx()
		ax2.set_ylabel('y2')
		ax2.plot(date, y2, linewidth=0.25, color = color)
		ax2.tick_params(axis = 'y')
		ax2.grid(color = color)
		fig.tight_layout()
		plt.close(fig) #not showing in the jupyter lab

		if if_save:
			fig.savefig(output_path, dpi = 250)		

		return ax, ax2, fig



	@staticmethod
	def plot_trade_and_diff_graph(date, price_hist, diff, ticker, trade_hist):
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		ax, ax2, fig = Simple_Anlysis.plot_two_factors_graph(date = date, y1 = price_hist, y2 = diff, ticker = ticker)
	
		x , y = date , price_hist

		long_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		long_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		ax.scatter(long_x, long_action, c = 'g', marker = '^',   s= 2.0, label = 'l')
		# ax2.scatter(long_x, long_action, c = 'g', marker = '^',   s= 2.0, label = 'l')		

		short_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0]
		short_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0 ]		
		ax.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 2.0, label = 's')
		# ax2.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 2.0, label = 's')

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)



	@staticmethod
	def plot_trade_graph(date, price_hist, ticker, trade_hist):
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		ax, fig = Simple_Anlysis.plot_single_factor_graph(date = date, price_hist = price_hist, ticker = ticker)
	
		x , y = date , price_hist

		long_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		long_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		ax.scatter(long_x, long_action, c = 'g', marker = '^',   s= 2.0, label = 'l')

		short_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0]
		short_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0 ]		
		ax.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 2.0, label = 's')

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)


	@staticmethod
	def calculate_cumulated_return():
		return 0

	@staticmethod
	def calculate_annualised_return():
		return 0


	@staticmethod
	def calculate_beta():
		return 0