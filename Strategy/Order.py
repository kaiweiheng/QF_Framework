import pandas as pd
class Order(object):
	"""docstring for Order"""
	def __init__(self, date, ticker, price, quantity):
		super(Order, self).__init__()
		
		# self.trade_record = pd.DataFrame(columns=['date', 'price', 'quantity','product_ticker'])
		# self.arg = arg

		self.date = date
		self.ticker = ticker
		self.price = price
		self.quantity = quantity
	
	def to_DataFrame(self):
		return pd.DataFrame({ 'date': [self.date], 'ticker': [self.ticker], 'price':[self.price], 'quantity':[self.quantity] } )