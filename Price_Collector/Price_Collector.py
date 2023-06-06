import os
import pandas as pd 
class Price_Collector(object):
	"""docstring for Price_Collector"""
	def __init__(self, arg):
		super(Price_Collector, self).__init__()
		self.arg = arg
	
	@staticmethod
	def read_csv_if_exist(path):
		output = False
		if os.path.exists(path):
			output = pd.read_csv(path)
		return output 

	@staticmethod
	def check_parents_dir_exist(path):
		parents_dir = os.path.dirname(path)
		if not os.path.exists(parents_dir):
			os.makedirs(parents_dir)

	@staticmethod
	def calculate_return(price, return_column = 'c' , base_column = 'c'):
		'''
		to calculate return with close of last time priod 
		'''
		price['base_last_period'] = price[base_column].shift(1)
		price['re'] = ( price[ return_column ].astype('float') - price['base_last_period'].astype('float') ) / price['base_last_period'].astype('float')
		return price['re'].values


