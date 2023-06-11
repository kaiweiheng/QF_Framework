class Preprocessor(object):
	"""docstring for Preprocessor"""
	def __init__(self, arg):
		super(Preprocessor, self).__init__()
		self.arg = arg
		
	@staticmethod
	def calculate_return(price, return_column = 'c' , base_column = 'c'):
		'''
		to calculate return with close of last time priod 
		'''
		# price['base_last_period'] = price[base_column].shift(1) #with copy warning
		price = price.assign(base_last_period=price[base_column].shift(1))
		price['re'] = ( price[ return_column ].astype('float') - price['base_last_period'].astype('float') ) / price['base_last_period'].astype('float')
		return price['re'].values


