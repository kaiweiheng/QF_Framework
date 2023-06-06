from Strategy import *
import pandas as pd
import numpy as np 

class VIX_Trade(Strategy):
	"""
	load VIX, VIXY, SVXY
	UVXY
	long  VIXY, short SVXY when VIX below 15
	short VIXY, long  SVXY when VIX over 40
	"""
	def __init__(self, **args):
		super(VIX_Trade, self).__init__(**args)
		# self.arg = arg
		
		self.VIX_his = args['VIX_his']
		self.daily_peice_hist = pd.merge(self.daily_peice_hist, self.VIX_his, how = 'inner', left_on = 'date', right_on = 'date')


	def determin_action_of_a_day(self, date):

		# print("\n %s %s "%(self.ticker, date))
		# print(self.VIX_his[ self.VIX_his['date']  == date ])
		vix_value_of_today = self.daily_peice_hist[ self.daily_peice_hist['date']  == date ]['value'].values[0]
		close_of_today = self.daily_peice_hist[ self.daily_peice_hist['date'] == date ]['c'].values[0]

		self.trade_record.append( [ date, close_of_today, 0 ] )

		if vix_value_of_today < 15:
			self.have_trigged_trade += 1
			# long  VIXY, short SVXY 
			if self.ticker == "SVXY":
				self.trade_record[-1] = [ date, close_of_today, -100 ]
			elif self.ticker == "VIXY":
				self.trade_record[-1] = [ date, close_of_today, 100 ]

			# print("%s  %s \n"%(self.ticker, self.trade_record[-1]))

		elif  vix_value_of_today > 40:
			self.have_trigged_trade += 1
			# long  SVXY when VIX over 40
			if self.ticker == "SVXY":
				self.trade_record[-1] = [ date, close_of_today, 100 ]
			elif self.ticker == "VIXY":
				self.trade_record[-1] = [ date, close_of_today, -100 ]

			# print("%s  %s \n"%(self.ticker, self.trade_record[-1]))

		return 0

	def plot_trade_graph(self, date, price_hist):
		plt.rcParams['font.size'] = 7
		output_path = os.path.join('data','output',"%s.png"%(self.ticker))
		Strategy.check_parents_dir_exist(output_path)

		x = [d for d in date ]
		# x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		y = price_hist

		vix_hist = self.daily_peice_hist[ (self.daily_peice_hist['date'] >= date[0]) & (self.daily_peice_hist['date'] <= date[-1])   ]['value'].values

		trade_record = np.array(self.trade_record)[:,-1].astype('float')

		fig, ax = plt.subplots()
		ax.plot(x, y, 'w', linewidth=0.25, label="c")

		ax2 = ax.twinx()  
		ax2.plot(x, vix_hist, linewidth=0.25, label="c")


		long_x = [ x[i] for i in range(0, len(price_hist)) if trade_record[i] > 0 ]
		long_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_record[i] > 0 ]
		ax.scatter(long_x, long_action, c = 'g', marker = '^',   s= 1.0, label = 'l')

		short_x = [ x[i] for i in range(0, len(price_hist)) if trade_record[i] < 0]
		short_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_record[i] < 0 ]		
		ax.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 1.0, label = 's')		



		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(self.ticker))
		ax.grid()
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)
		return 0