from filterpy.kalman import KalmanFilter
import math
import tts
import gpsdata
import numpy as np
import nvector as nv
import threading
from pyquaternion import Quaternion
import time
import RTIMU
import subprocess
g=9.81
setting_file = "RTIMULib"
class read_imu(threading.Thread):
		def __init__(self):
			threading.Thread.__init__(self)
			self.s = RTIMU.Settings(setting_file)
			self.s.FusionType = 1
			self.s.AxisRotation = 13
			self.s.compassAdjDeclination = 0.97
			self.imu = RTIMU.RTIMU(self.s)
			self.imu.IMUInit()
			self.imudata = []
			self.timestamp = time.time()
			self.STOP = True
		def run(self):
			while self.STOP:
				self.imu.IMURead()
				self.imudata = self.imu.getIMUData()
				self.timestamp+=0.005
				while time.time()-self.timestamp<0.005:
					time.sleep(0.0001)
		def getIMUData(self):
			return self.imudata
class imu_gps:
	class work(threading.Thread):
		def __init__(self):
			threading.Thread.__init__(self)
			self.imu = read_imu()
			self.imu.start()
			self.STOP = True
			self.lost = False
			self.tts = tts.tts()
			self.gps = gpsdata.gpsdata()
			self.filter_N = KalmanFilter(dim_x=2,dim_z=2,dim_u=1)
			self.filter_E = KalmanFilter(dim_x=2,dim_z=2,dim_u=1)
			self.timestamp = time.time()

			#getting position and velocity
			vel = self.vel()
			pos = self.pos()
			if vel[0] == -1:
				self.tts.speak("getting your location. Please wait")
				while vel[0] == -1:
					while vel[0] == -1:
						vel = self.vel()
						pos = self.pos()
						time.sleep(0.01)
					time.sleep(2)
					vel = self.vel()
					pos = self.pos()	
				self.tts.speak("Location detected")
				
				vel = self.vel()

			#initialization North Filter	
			self.filter_N.x = np.array([[pos[0]],
										[vel[0]]])       # initial state (location and velocity)
			self.filter_N.F = np.array([[1.,0.01],
										[0.,1.]])    # state transition matrix
			self.filter_N.H = np.array([[1,0],[0,1]])   # Measurement function
			self.filter_N.R = np.array([[pos[2],0.],
										[0.,vel[2]]]) # state uncertainty
			self.filter_N.Q = np.array([[0.00688,0.],
										[0.,0.00688]]) # process uncertainty
			self.filter_N.B = np.array([[0.00005],
										[0.01]])
			#initialization East Filter

			self.filter_E.x = np.array([[pos[1]],
										[vel[1]]])       # initial state (location and velocity)
			self.filter_E.F = np.array([[1.,0.01],
										[0.,1.]])    # state transition matrix
			self.filter_E.H = np.array([[1,0],[0,1]])    # Measurement function
			self.filter_E.R = np.array([[pos[3],0.],
										[0.,vel[2]]]) # state uncertainty
			self.filter_E.Q = np.array([[0.00688,0.],
										[0.,0.00688]]) # process uncertainty
			self.filter_E.B = np.array([[0.00005],
										[0.01]])
		def vel(self):
			imudata = self.imu.getIMUData()
			yaw = imudata["fusionPose"][2]
			v = self.gps.speed()
			error = self.gps.error()[2]
			if error==-1 or v==-1:
				return [-1,-1,-1]
			if v<0.6:
				return [0,0,0]
			else:
				speed = [math.cos(yaw)*v,math.sin(yaw)*v,0.8*0.8]
			return speed

		def dist(self,loc1,loc2):
			wgs84 = nv.FrameE(name='WGS84')
			point1 = wgs84.GeoPoint(latitude=loc1[0], longitude=loc1[1], degrees=True)
			point2 = wgs84.GeoPoint(latitude=loc2[0], longitude=loc2[1], degrees=True)
			s_12, _azi1, _azi2 = point1.distance_and_azimuth(point2)
			return s_12
		def pos(self):
			loc = self.gps.loc()[:]
			error = self.gps.error()
			if error[0] == -1 or loc[0]==-1:
				return [-1,-1,-1,-1]
			loc[0] = self.dist([0,0],[loc[0],0])
			loc[1] = self.dist([0,0],[0,loc[1]])
			
			loc.append(error[0]*error[0])
			loc.append(error[1]*error[1])
			return loc
		def acc(self,imudata):
			q = imudata["fusionQPose"][:]
			q = Quaternion(q[0],q[1],q[2],q[3])
			acc = imudata["accel"][:]
			acc = [x*g for x in acc]
			a_mag_ned = q.rotate(acc)
			# if -0.02<a_mag_ned[0]<0.02:
			# 	a_mag_ned[0]=0
			# if -0.02<a_mag_ned[1]<0.02:
			# 	a_mag_ned[1]=0
			return a_mag_ned
		def run(self):
			count = 0
			no_signal_count = 0
			while self.STOP:
				while time.time()-self.timestamp <0.01:
					time.sleep(0.0001)
				imudata = self.imu.getIMUData()
				a_mag_ned = self.acc(imudata)
				self.filter_N.predict(np.array([[a_mag_ned[0]]]))
				self.filter_E.predict(np.array([[-a_mag_ned[1]]]))
				self.timestamp+=0.01
				if count == 20:
					count = 0
					pos = self.pos()
					vel = self.vel()
					if no_signal_count*0.2 == 3:
						self.lost = True
						self.tts.speak("G P S Signal Lost. Please wait")
						vel = [-1,-1]
						while vel[0] == -1:
							while vel[0] == -1:
								pos = self.pos()
								vel = self.vel()
								time.sleep(0.01)
							time.sleep(2)
							pos = self.pos()
							vel = self.vel()
						self.tts.speak("Signal detected")
						self.timestamp = time.time()
						self.lost = False
					if vel[0] == -1:
						print "no fix number:",(no_signal_count+1)
						no_signal_count+=1
						continue
					no_signal_count = 0
					x_N = np.array([[pos[0]],
									[vel[0]]])
					x_E = np.array([[pos[1]],
									[vel[1]]])
					R_N = np.array([[pos[2],0.],
									[0.,vel[2]]])
					R_E = np.array([[pos[3],0.],
									[0.,vel[2]]])
					self.filter_N.update(x_N,R_N)
					self.filter_E.update(x_E,R_E)
					self.lost == False
				count+=1	
				# if a_mag_ned[0]==0:
				# 	self.filter_N.x[1][0]=0
				# if a_mag_ned[1]==0:
				# 	self.filter_E.x[1][0]=0
				
	def __init__(self):
		self.move = self.work()
		self.move.start()
	def dist_to_point(self,loc,dis,ang):
		frame = nv.FrameE(name='WGS84')
		pointA = frame.GeoPoint(latitude=loc[0], longitude=loc[1], degrees=True)
		pointB, _azimuthb = pointA.geo_point(dis, azimuth=ang, degrees=True)
		lat, lon = pointB.latitude_deg, pointB.longitude_deg
		loc = [lat,lon]
		return loc
	def convert_to_latlon(self,a):
		loc = self.dist_to_point([0,0],a[1],90.0)[:]
		loc = self.dist_to_point(loc,a[0],0.0)[:]
		return loc
	def check_device_pos(self):
		imudata = self.move.imu.getIMUData()
		pitch = math.degrees(imudata["fusionPose"][0])
		roll = math.degrees(imudata["fusionPose"][1])
		a = 30
		if -a<pitch<a and -a<roll<a:
			return True
		return False
	def heading(self):
		if self.check_device_pos()==False:
			self.tts.speak("Device not placed properly.")
			self.tts.wait()
			while not self.check_device_pos():
				time.sleep(0.01)
			self.tts.speak("Device correctly placed")
		while self.move.lost == True:
			time.sleep(0.01)
		imudata = self.move.imu.getIMUData()
		yaw = imudata["fusionPose"][2]
		return yaw
	def loc(self): 
		if self.check_device_pos()==False:
			while not self.check_device_pos():
				time.sleep(0.01)
		while self.move.lost == True:
			time.sleep(0.01)
		a = [0,0]
		a[0] = self.move.filter_N.x[0][0]
		a[1] = self.move.filter_E.x[0][0]
		#a = [x*0.001 for x in a]
		a = self.convert_to_latlon(a)[:]
		return a
	def stop(self):
		self.move.STOP = False
		self.move.imu.STOP = False
		self.move.gps.stop()









