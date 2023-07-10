import sys

sys.path.append("Analysis")
from Simple_Anlysis import *

sys.path.append("Preprocess")
from Preprocessor import *

from Strategy import *
import pandas as pd
import numpy as np 

'''
Dev Note:
1. Draw back in 2020 crash is too high, stop loss?
2. entry a position then stucked, training UVXY_VXX
3. In extrame volitiled env cause loss, mv5 or mv10 as another condition?

'''


class VIX_arbitrage(Strategy):
	"""docstring for VIX_arbitrage"""
	def __init__(self, **args):
		super(VIX_arbitrage, self).__init__(**args)
		# self.arg = arg


		self.daily_price_of_another_product = args['daily_price_of_another_product']
		self.ticker_of_another_product = args['ticker_of_another_product']
		self.tracking_index_ticker = args['tracking_index_ticker']
		self.tracking_index = args['tracking_index_hist']


		# self.tracking_index['re_%s'%(self.tracking_index_ticker)] = Preprocessor.calculate_return(self.tracking_index[ ['date','value'] ], 'value', 'value')
		# self.tracking_index['c_%s'%(self.tracking_index_ticker)] = self.tracking_index['value']
		self.tracking_index = self.tracking_index.dropna(subset = ['re_%s'%(self.tracking_index_ticker)])
		self.tracking_index = self.tracking_index[['date','c_%s'%(self.tracking_index_ticker),'re_%s'%(self.tracking_index_ticker)]]

		self.daily_price_of_another_product['c_%s'%(self.ticker_of_another_product)] =  self.daily_price_of_another_product['c']
		self.daily_price_of_another_product['re_%s'%(self.ticker_of_another_product)] = Preprocessor.calculate_return(self.daily_price_of_another_product[ ['date','c']])
		self.daily_price_of_another_product = self.daily_price_of_another_product[['date','c_%s'%(self.ticker_of_another_product),'re_%s'%(self.ticker_of_another_product)]]
		

		self.daily_price_hist['c_%s'%(self.ticker)] = self.daily_price_hist['c']
		self.daily_price_hist['re_%s'%(self.ticker)] = Preprocessor.calculate_return( self.daily_price_hist[['date','c']] )
		self.daily_price_hist = self.daily_price_hist[['date','c_%s'%(self.ticker),'re_%s'%(self.ticker)]]


		self.daily_price_hist = pd.merge(self.daily_price_hist, self.daily_price_of_another_product, how = 'inner', left_on = 'date', right_on = 'date')
		self.daily_price_hist = pd.merge(self.daily_price_hist, self.tracking_index, how = 'inner', left_on = 'date', right_on = 'date')

		self.daily_price_hist['diff'] = self.daily_price_hist['re_%s'%(self.ticker)] - self.daily_price_hist['re_%s'%(self.ticker_of_another_product)]

		self.daily_price_hist = self.daily_price_hist.dropna(subset = ['diff'])



		self.training_dates, self.validation_dates = self.get_training_val_date()
		self.sim_dates = self.get_sim_dates()

		self.training_price = self.select_rows_according_to_dates(self.daily_price_hist, self.training_dates[0], self.training_dates[-1])
		self.validation_price = self.select_rows_according_to_dates(self.daily_price_hist, self.validation_dates[0], self.validation_dates[-1])
		self.testing_price = self.select_rows_according_to_dates(self.daily_price_hist, self.sim_dates[0], self.sim_dates[-1])				


		#to be explore multivariable regression (no-time series) or time series model can help with determine a better entry timeing

		self.trade_record_for_paired_product = []

		# Simple_Anlysis.return_histogram([self.training_price['over'].replace([np.inf, -np.inf], 0, inplace = False).values, 
		# 	self.validation_price['over'].replace([np.inf, -np.inf], 0, inplace = False).values, 
		# 	self.testing_price['over'].replace([np.inf, -np.inf], 0, inplace = False).values], ['train','val','testing'],
		# 	"%s_%s"%(self.ticker, self.ticker_of_another_product))

		############################################################################
		from sklearn import linear_model

		self.dataset = self.daily_price_hist.copy()
		self.dataset = self.dataset[['date','diff']]
		self.dataset['y'] = self.dataset['diff'].shift(-1)
		
		self.dataset['y_b'] = 1
		self.dataset.loc[ self.dataset.y < 0, 'y_b'  ] = 0

		self.dataset['mv3'] = Preprocessor.moving_average(self.dataset, 'diff', 3) 		
		self.dataset['mv5'] = Preprocessor.moving_average(self.dataset, 'diff', 5) 
		self.dataset['mv10'] = Preprocessor.moving_average(self.dataset, 'diff', 10) 		

		self.dataset = self.dataset.dropna()

		self.dataset_train = self.select_rows_according_to_dates(self.dataset, self.training_dates[0], self.training_dates[-1])
		self.dataset_val = self.select_rows_according_to_dates(self.dataset, self.validation_dates[0], self.validation_dates[-1])
		self.dataset_test = self.select_rows_according_to_dates(self.dataset, self.sim_dates[0], self.sim_dates[-1])				

		quantiles =  self.dataset_train['diff'].quantile([.15, .85]).values
		lower_quantile, higher_quantile = quantiles[0], quantiles[1]

		# self.dataset_train = self.dataset_train[ (self.dataset_train['diff'] < lower_quantile) | (self.dataset_train['diff'] > higher_quantile)   ]
		# self.dataset_val = self.dataset_val[ (self.dataset_val['diff'] < lower_quantile) | (self.dataset_val['diff'] > higher_quantile)   ]
		
		reg = linear_model.LinearRegression()

		reg.fit(self.dataset_train[['diff','mv3','mv5','mv10']].values, self.dataset_train[['y']].values)

		train_prediction = reg.predict(self.dataset_train[['diff','mv3','mv5','mv10']].values)
		train_prediction_b = [  1 if p > 0 else 0 for p in train_prediction]

		accuracy, precision, recall = self.calculate_accuracy(train_prediction_b, self.dataset_train['y_b'].values)

		val_prediction = reg.predict(self.dataset_val[['diff','mv3','mv5','mv10']].values)
		val_prediction_b = [  1 if p > 0 else 0 for p in val_prediction]

		accuracy, precision, recall = self.calculate_accuracy(val_prediction_b, self.dataset_val['y_b'].values)

		self.dataset['signal'] = reg.predict(self.dataset[['diff','mv3','mv5','mv10']].values)
		# self.dataset['signal'] = 	self.dataset['y']			
		self.dataset = self.dataset[['date','signal', 'mv3','mv5','mv10']]

		self.daily_price_hist = pd.merge(self.daily_price_hist, self.dataset, how = 'inner', left_on = 'date', right_on = 'date')
		self.daily_price_hist = self.daily_price_hist.dropna()

		self.training_price = self.select_rows_according_to_dates(self.daily_price_hist, self.training_dates[0], self.training_dates[-1])
		self.validation_price = self.select_rows_according_to_dates(self.daily_price_hist, self.validation_dates[0], self.validation_dates[-1])
		self.testing_price = self.select_rows_according_to_dates(self.daily_price_hist, self.sim_dates[0], self.sim_dates[-1])


		###################################################################################################

	def determin_action_of_a_day(self, date, lower_quantile = -0.1, higher_quantile = 0):

		# at the beginning of the day, get essential info
		diff_of_the_day = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['diff'].values[0]
		price_for_this_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker)].values[0]
		price_for_paired_product = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['c_%s'%(self.ticker_of_another_product)].values[0]		
		signal = self.daily_price_hist[ self.daily_price_hist['date'] == date ]['signal'].values[0]

		# define pnl from position of yesterday
		_, product_pnl, product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker, price_for_this_product)
		_, paired_product_pnl, paired_product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker_of_another_product, price_for_paired_product)
		total_pnl_rate = 0 if (product_margine + paired_product_margine) == 0 else (product_pnl + paired_product_pnl)/ (product_margine + paired_product_margine)

		max_quantity_to_open_paried_product = max( 0, int(self.cash / (price_for_this_product +  price_for_paired_product)) )
		max_quantity_to_close_paired_product = max(0, self.position[self.ticker] )
		quantity = max_quantity_to_open_paried_product

		#dummy record even no deal actually happen at this date
		self.trade_record_for_paired_product.append([date, price_for_this_product, 0, self.ticker])

		if diff_of_the_day < lower_quantile and self.last_time_action != 1 and quantity != 0:			

			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, quantity, self.ticker]

			self.trade_record.append(Order(date = date , ticker = self.ticker, price = price_for_this_product, quantity = quantity))			
			self.trade_record.append(Order(date = date , ticker = self.ticker_of_another_product, price = price_for_paired_product, quantity = -quantity))
						
			self.have_trigged_trade += 1
			self.last_time_action = 1


		#or considering stop profit in 50 bps or 100 bps
		#to be define the optimal exist condition
		elif total_pnl_rate > 0.0 and self.last_time_action == 1:
		# elif self.last_time_action == 1:
			quantity = max_quantity_to_close_paired_product
			self.trade_record_for_paired_product[-1] = [date, price_for_this_product, -quantity, self.ticker]			
			
			self.trade_record.append(Order(date = date , ticker = self.ticker, price = price_for_this_product, quantity = -quantity))
			self.trade_record.append(Order(date = date , ticker = self.ticker_of_another_product, price = price_for_paired_product, quantity = quantity))

			self.have_trigged_trade += 1
			self.last_time_action = -1

		#to be added open shot position when no existed position	

		self.determin_position_of_a_day(date, comission = 1)

		_, product_pnl, product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker, price_for_this_product)
		_, paired_product_pnl, paired_product_margine, _ = self.determine_pnl_related_of_a_product(self.ticker_of_another_product, price_for_paired_product)
		self.total_value_records.append(self.cash + product_pnl + product_margine + paired_product_pnl + paired_product_margine )


	@staticmethod
	def calculate_accuracy(predictions, ground_truths):

		tp, tn, fp, fn = 0, 0, 0, 0
		for i in range(0, len(predictions)):
			if predictions[i] == 1 and predictions[i] == ground_truths[i]:
				tp += 1
			elif predictions[i] == 0 and predictions[i] == ground_truths[i]:
				tn += 1
			elif predictions[i] == 1 and predictions[i] != ground_truths[i]:
				fp += 1
			elif predictions[i] == 0 and predictions[i] != ground_truths[i]:						
				fn += 1
		accuracy =  (tp + tn) / (tp + tn + fp + fn)
		precision = tp / (tp + fp)
		recall = tp / (tp + fn)
		return accuracy, precision, recall

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


	@staticmethod
	def make_assessment(df, index_column_name, benchmark_column_name, path, remark, frequency = 'Q'):
		dfs = Simple_Anlysis.split_df_according_to_frequency(df, frequency)
		cumulated_re_df, period_re_df, annualised_re = dict(), dict(), dict()
		draw_down_df, sharp_df, beta_df = dict(), dict(), dict()


		aggregated_df = []

		for i in range(0, len(dfs)):
			df_current_period, df_cumulated = dfs[i], pd.concat(dfs[:i+1]).sort_values(by = 'date' )

			# print(df_cumulated)

			_, end_date = Simple_Anlysis.get_first_and_last_record_of_a_df(df_current_period, 'date')

			end_date = pd.to_datetime(str(end_date)).strftime('%Y/%m/%d')

			benchmark_f_o_f_return = Simple_Anlysis.caculate_period_on_period_return(df_current_period, benchmark_column_name)
			index_f_o_f_return = Simple_Anlysis.caculate_period_on_period_return(df_current_period, index_column_name)			
			period_re_df[end_date] = [ benchmark_f_o_f_return, index_f_o_f_return]


			benchmark_cumulated_return = Simple_Anlysis.caculate_period_on_period_return(df_cumulated, benchmark_column_name)
			index_cumulated_return = Simple_Anlysis.caculate_period_on_period_return(df_cumulated, index_column_name)						
			cumulated_re_df[end_date] = [   benchmark_cumulated_return, index_cumulated_return] 

			benchmark_ann_return = Simple_Anlysis.caculate_period_on_period_return(df_cumulated, benchmark_column_name, True)
			index_ann_return = Simple_Anlysis.caculate_period_on_period_return(df_cumulated, index_column_name, True)
			annualised_re['%s%s_%s'%(i+1,frequency, end_date)] = [ benchmark_ann_return, index_ann_return]


			benchmark_drawdown = Simple_Anlysis.calculate_max_draw_down(df_cumulated, benchmark_column_name)
			index_drawdown = Simple_Anlysis.calculate_max_draw_down(df_cumulated, index_column_name)
			draw_down_df['%s%s_%s'%(i+1,frequency, end_date)] = [  benchmark_drawdown, index_drawdown ]


			index_sharp = Simple_Anlysis.calculate_sharp_ratio(df_cumulated, index_column_name, benchmark_column_name)
			sharp_df['%s%s_%s'%(i+1,frequency, end_date)] = [index_sharp ]


			index_beta, _ , _ = Simple_Anlysis.calculate_beta(df_cumulated, index_column_name, benchmark_column_name)
			beta_df['%s%s_%s'%(i+1,frequency, end_date)] = [index_beta]			


		aggregated_df.append( pd.DataFrame(cumulated_re_df, index = ["b_cumu_re", "i_cumu_re" ] ) )
		aggregated_df.append( pd.DataFrame(period_re_df, index = ["b_%so%s_re"%(frequency,frequency),"i_%so%s_re"%(frequency,frequency) ] ) )
		aggregated_df.append( pd.DataFrame(annualised_re, index = ["b_ann_re", "i_ann_re" ] )  )
		aggregated_df.append( pd.DataFrame(draw_down_df, index = ["b_drawdon","i_drawdown"] ) )
		aggregated_df.append( pd.DataFrame(sharp_df, index = ["Sharp_ann"]) )
		aggregated_df.append( pd.DataFrame(beta_df, index = ["Beta"])  )										

		startrow = 0
		with pd.ExcelWriter('%s_%s.xlsx'%(path,remark) , engine='xlsxwriter') as writer:
		# with pd.ExcelWriter('%s.xlsx'%(path), mode = 'a', engine='openpyxl') as writer:		
			for df in aggregated_df:
				df.to_excel(writer,sheet_name='%s'%(remark),startrow = startrow , startcol=0)   
				startrow = startrow + 3 + len(df)
		aggregated_df = [df.to_markdown() for df in aggregated_df]
		return aggregated_df

