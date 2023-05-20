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


	def determin_action_of_a_day(self, date):

		num_of_vix = self.VIX_his[ self.VIX_his['date']  == date ]

		print(num_of_vix)
		print("  ")
		# print("date %s VIX  %s \n"%(date, num_of_vix['value']))

		return 0