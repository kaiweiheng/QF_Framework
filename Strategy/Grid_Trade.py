from Strategy import *
import pandas as pd
import numpy as np 

class Grid_Trade(Strategy):
	"""docstring for Grid_Trade"""
	def __init__(self,**args):
		super(Grid_Trade, self).__init__(**args)
		# self.arg = arg
		self.sim_start_date = args['sim_start_date']
		self.init_central_point = self.daily_peice_hist[  self.daily_peice_hist['date'] == max(self.data_start_date, self.sim_start_date)  ]['c']

		self.n_band_one_side, self.band_interval = args['n_band_one_side'], args['band_interval']
		self.band = []
		tmp = [ i * self.band_interval for i in range(1, self.n_band_one_side+1) ]

		_ = [self.band.append( 1 - i ) for i in tmp[::-1]]
		self.band.append(1)
		_ = [self.band.append(1 + i) for i in tmp]
		self.band = np.array(self.band) * np.array([self.init_central_point])

		self.grid_record = [0]


		# print([ i for i in range(1, self.n_band_one_side*2+1)])

	#to allow trade within days
	# TBD

	#do not allows trade within days
	def determin_action_of_a_day(self, date):

		close_of_today = self.daily_peice_hist[ self.daily_peice_hist['date'] == date ]

		if len(close_of_today) == 0:
			return 0

		# self.trade_record.loc[len(self.trade_record)] = [date, close_of_today, 0 ]
		self.trade_record.append( [ date, close_of_today['c'].values[0], 0 ] )
		grid = pd.cut( close_of_today['c'].values, self.band[0], labels=[ i for i in range(1, self.n_band_one_side*2+1)])[0]

		if np.isnan(grid):
			return 0


		if self.grid_record[-1] < grid and self.grid_record[-1] != 0:
			# print("%s %s short, current grid %s, c %.5f last_grid %s  \n"%(self.ticker, date ,grid, close_of_today['c'].values, self.grid_record[-1]))
			# self.trade_record[-1] = -1
			# self.trade_record.loc[len(self.trade_record)-1] = [date, close_of_today, -1 ]
			self.trade_record[-1] = [ date, close_of_today['c'].values[0], -1 ]
			self.have_trigged_trade += 1


		if self.grid_record[-1] > grid and self.grid_record[-1] != 0:
			# print("%s %s long, current grid %s, c %.5f last_grid %s  \n"%(self.ticker, date ,grid, close_of_today['c'].values, self.grid_record[-1]))
			# self.trade_record[-1] = 1
			# self.trade_record.loc[len(self.trade_record)-1] = [date, close_of_today, 1 ]
			self.trade_record[-1] = [ date, close_of_today['c'].values[0], 1 ]
			self.have_trigged_trade += 1

		self.grid_record.append(grid)
		if len(self.grid_record) > 100:
			self.grid_record = self.grid_record[-100:]
	


	def plot_trade_graph(self, date, price_hist):
		plt.rcParams['font.size'] = 7
		output_path = os.path.join('data','output',"%s.png"%(self.ticker))
		Strategy.check_parents_dir_exist(output_path)

		x = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date]
		y = price_hist

		trade_record = np.array(self.trade_record)[:,-1].astype('float')

		fig, ax = plt.subplots()
		ax.plot(x, y, 'w', linewidth=0.25, label="c")

		long_x = [ x[i] for i in range(0, len(price_hist)) if trade_record[i] > 0 ]
		long_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_record[i] > 0 ]
		ax.scatter(long_x, long_action, c = 'g', marker = '^',   s= 1.0, label = 'l')

		short_x = [ x[i] for i in range(0, len(price_hist)) if trade_record[i] < 0]
		short_action = [ price_hist[i] for i in range(0, len(price_hist)) if trade_record[i] < 0 ]		
		ax.scatter(short_x, short_action, c = 'r' , marker = 'v',   s= 1.0, label = 's')	

		for b in self.band:
			ax.plot(x, [b for i in range(0, len(price_hist))], '--', linewidth = 0.1  )

		ax.set(xlabel='time', ylabel='Price', title='%s Trade Record'%(self.ticker))
		ax.grid()
		
		ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
		ax.xaxis.set_major_locator(mdates.DayLocator(interval=int(  len(date)/10 )))
		ax.tick_params(axis='x', labelrotation=45, labelsize=5)

		plt.close(fig) #not showing in the jupyter lab
		fig.savefig(output_path, dpi = 250)
		return 0