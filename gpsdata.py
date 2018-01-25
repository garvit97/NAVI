import threading
import time
import gps
import tts
class gpsdata:
	class currentdata(threading.Thread):
		def __init__(self):
			threading.Thread.__init__(self)
			self.session = gps.gps()
			self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
			self.loc = [-1,-1]
			self.STOP=False
			self.Heading = -1
			self.mode = -1
			self.speed = -1
			self.error = [-1,-1,-1]
		def run(self):
			while self.STOP==False:
				report = self.session.next()
				if report['class'] == 'TPV' and hasattr(report,'mode'):
					self.mode = report['mode']
				if self.mode == 3:
					if report['class'] == 'TPV' and hasattr(report,'lat'):
						self.loc[0] = report['lat']
						self.loc[1] = report['lon']
					if report['class'] == 'TPV' and hasattr(report,'epx'):
						self.error[0] = report['epx']
						self.error[1] = report['epy']
					if report['class'] == 'TPV' and hasattr(report,'eps'):
						self.error[2] = report['eps']
					if report['class'] == 'TPV' and hasattr(report,'track'):
						self.Heading = report['track']
					if report['class'] == 'TPV' and hasattr(report,'speed'):
						self.speed = report['speed']

				else:
					self.loc = [-1,-1]
					self.Heading = -1
					self.speed = -1
					self.error = [-1,-1,-1]
	def __init__(self):
		self.tts = tts.tts()
		self.data = self.currentdata()
		self.data.start()
	def error(self):
		return self.data.error
	def speed(self):
		return self.data.speed
	def loc(self):
		return self.data.loc
	def heading(self):
		return self.data.Heading
	def stop(self):
		self.data.STOP=True
	
	
   
	
