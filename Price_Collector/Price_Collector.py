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

