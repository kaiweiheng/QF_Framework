import os
from Strategy import *
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
	def plot_single_factor_graph(date, price_hist, ticker):
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		# x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		x = date
		y = price_hist

		fig, ax = plt.subplots()
		fig.set_figheight(8)
		fig.set_figwidth(int(len(date))/5)
		ax.plot(x, y, 'w', linewidth=0.25, label="c")

		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(ticker))
		ax.grid(color = 'w')
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		# ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(5)))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)


	@staticmethod
	def plot_trade_graph(date, price_hist, ticker, trade_hist):
		plt.rcParams['font.size'] = 7		
		output_path = os.path.join('data','output',"%s.png"%(ticker))
		Strategy.check_parents_dir_exist(output_path)

		# x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		x = date
		y = price_hist

		fig, ax = plt.subplots()
		fig.set_figheight(8)
		fig.set_figwidth(int(len(date))/5)
		ax.plot(x, y, 'w', linewidth=0.25, label="c")


		long_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		long_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] > 0 ]
		ax.scatter(long_x, long_action, c = 'g', marker = '^',   s= 2.0, label = 'l')

		short_x = [ x[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0]
		short_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_hist[i] < 0 ]		
		ax.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 2.0, label = 's')


		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(ticker))
		ax.grid(color = 'w')
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		# ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(5)))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)
