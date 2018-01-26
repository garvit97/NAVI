import tts 
import routeSave
from routeSave import getBearing, getDifference
import input
import time
import gmplot
import imu_gps
import dill
import pulseb
import pulsev
from geopy.distance import vincenty as vc, great_circle as distance
from math import sin, cos, atan2, sqrt, degrees, radians, pi,fabs
import math
import threading
from singleton_graph import Graph
from graph_utils import visualize_path

curlocindex=0
#All methods defined
class NAVI:
	def __init__(self):
		self.fav = [None]*10
		self.map = Graph("graph.gml")
		self.tts = tts.tts()
		self.gps = imu_gps.imu_gps()
		self.stop_dev = True
		self.input = input.input()
		self.key = -1
		self.out_of_path = False
		self.selfile = None
		self.attributesfile = None
		self.attr = {}

	def assignBearing(self,pointsList):
		l=len(pointsList)
		x=0
		while x<l:
			pt=pointsList[x]
			if not pt["attributes"] is None:
				if pointsList[x-1]["attributes"] is None:
					pt1=pointsList[x-1]["loc"]
				else:
					pt1=pointsList[x-2]["loc"]
				pt2=pointsList[x]["loc"]
				brng=getBearing(pt1,pt2)
				pt["attributes"]["bearing"]=brng
			x+=1
		return pointsList
	def getDecPt(self,pointsArray):
		l=len(pointsArray)
		x=1
		y=1
		decPt={}
		decPt[0]={"loc":pointsArray[0]['loc'],'attributes':None}
		if (pointsArray[0]["attributes"] is None):
			aPt=pointsArray[0]['loc']
		else:
			aPt=pointsArray[1]['loc']
			decPt[y]={'loc':aPt,'attributes':pointsArray[0]['attributes']}
			y+=1
		brng=getBearing(pointsArray[0]['loc'],pointsArray[1]['loc'])
		while x<(l-1):
			if (pointsArray[x]['attributes'] is None):
				# print("blah blah")
				curPt=pointsArray[x]['loc']
			else:
				curPt=pointsArray[x+1]['loc']
				decPt[y]={'loc':curPt,'attributes':pointsArray[x]['attributes']}
				y+=1
			if (pointsArray[x-1]['attributes'] is None):
				prevPt=pointsArray[x-1]['loc']
			else:
				prevPt=pointsArray[x-2]['loc']
			if (pointsArray[x+1]['attributes'] is None):
				nextPt=pointsArray[x+1]['loc']
			else:
				if (x!=(l-2)):
					nextPt=pointsArray[x+2]['loc']
				else:
					nextPt=pointsArray[x+1]['loc']


			if (x!=(l-2)):
				if (pointsArray[x+2]['attributes'] is None):
					nnextPt=pointsArray[x+2]['loc']
				else:
					nnextPt=pointsArray[x+2]['loc']

			else:
				nnextPt=nextPt

			brng1=getBearing(prevPt,curPt)
			brng2=getBearing(curPt,nextPt)
			diff=getDifference(brng1,brng2)
			#print(prevPt, curPt, nextPt, brng1, brng2,diff)

			if(diff>30 or diff<-30):
				bga=getBearing(aPt,curPt)
				bgb=getBearing(aPt,nextPt)
				bgc=getBearing(aPt,nnextPt)
				dif1=getDifference(brng,bga)
				dif2=getDifference(brng,bgb)
				dif3=getDifference(brng,bgc)
				#print(brng)
				#print("here1")
				# print(dif1,dif2,dif3)
				# print(aPt)
				if((dif3>dif2 and dif2>dif1) or (dif3<dif2 and dif2<dif1)):
					# print("here2")
					bgturn=getBearing(nextPt,nnextPt)
					diff2=getDifference(bga,bgturn)
					# print("hello")
					# print(diff2)
					if(diff2<60 and diff2>30):
						dir="turn slight right"
					elif(diff2>-60 and diff2<-30):
						dir="turn slight left"
					elif(diff2>60):
						dir="turn right"
					elif (diff2<-60):						
						dir="turn left"
					decPt[y]={"loc":curPt,'attributes':None}
					y+=1
					if (pointsArray[x+1]['attributes'] is None):
						x+=1
					else:
						decPt[y]={'loc':pointsArray[x+1]['loc'],'attributes':pointsArray[x+1]['attributes']}
						y+=1
						x+=1
					if (pointsArray[x+1]['attributes'] is None):
						x+=1
					else:
						decPt[y]={'loc':pointsArray[x+1]['loc'],'attributes':pointsArray[x+1]['attributes']}
						y+=1
						x+=1
					if x<l-2:
						aPt=pointsArray[x]['loc']
						brng=getBearing(aPt,pointsArray[x+1]['loc'])
			x+=1
		decPt[y]={"loc":curPt,'attributes':None}

		return decPt
	def sampling(self,sampledpts,attrpts): # takes the attributes and 2-m-sampled arrays and gives an array of decision points		# run these two methods in two threads
		allPts=dict(sampledpts.items()+attrpts.items())
		points=sorted(allPts.items())
		#pointsArray={i:item[1] for i,item in enumerate(points)}
		pointsArray = [item[1] for item in points]
		def draw_map(clist):
			coords=[item['loc'] for item in clist]
			lat,lon=zip(*coords)
			gmap=gmplot.GoogleMapPlotter(lat[0],lon[0],16)
			gmap.scatter(lat,lon, 'k', marker=True)
			gmap.plot(lat,lon, 'cornflowerblue', edge_width=2)
			gmap.draw('route'+str(time.time())+'.html')
		#visualize_path([item['loc'] for item in pointsArray],'route'+str(time.time())+'.html')
		#print pointsArray
		draw_map(pointsArray)
		finalPoints=self.assignBearing(pointsArray)
		return self.getDecPt(finalPoints)	
	def store(self):
		self.attr = {}
		sampledpts = dict()
		self.tts.speak("Enter Destination")
		self.tts.wait()
		name = self.input.text()
		self.tts.speak("Destination saved. Press any key to start route saving")
		while (self.input.key()==False).all() or not self.gps.check_device_pos():
			time.sleep(0.05)
			if not (self.input.key()==False).all() and not self.gps.check_device_pos():
				while not (self.input.key()==False).all():
					time.sleep(0.01)
				self.tts.stop()
				self.tts.speak("Device not placed properly.Correct device position and press any key to start route saving")
		self.tts.stop()
		self.tts.speak("Route saving started")
		curloc = self.gps.loc()
		prevloc=curloc
		timing=time.time()
		sampledpts[timing]={"loc":curloc,'attributes':None}
		num_points = 0
		while True:
			time.sleep(0.02)
			if not self.gps.check_device_pos():
				self.tts.speak("Device not placed properly.")
				self.tts.wait()
				while not self.gps.check_device_pos():
					time.sleep(0.01)
				self.tts.speak("Device correctly placed")
			curloc=self.gps.loc()
			if (vc(prevloc,curloc).meters>1):
				prevloc=curloc
				timing=time.time()
				sampledpts[timing]={"loc":curloc,'attributes':None}
				num_points+=1
			if self.input.pressed(3,0):
				self.key = 1
				self.tts.stop()
				self.tts.speak("Press enter to exit")
			elif self.input.pressed(3,1):
				self.key = 2
				self.tts.stop()
				self.tts.speak("Press enter to add attributes")
			elif self.input.pressed(3,2):
				if self.key == -1:
					self.tts.stop()
					if num_points<10:
						self.tts.speak("Not enough points to save route")
					else:
						self.tts.speak("Press again to save route")
						self.key = 3
				elif self.key == 1:
					self.key = -1
					self.tts.stop()
					self.tts.speak("Returning to home")
					arr = sorted(self.attr.items())
					size = len(arr)
					li = []
					for i in range(size):
						Li.append ((tuple(arr[i][1]["loc"]),{"attributes":arr[i][1]["attributes"]}))
					self.map.merge_with_path(Li)
					return
				elif self.key == 2:
					self.key = -1
					self.tts.stop()
					self.addAttr
					self.addAttr(None,None)
					# add attributes
				elif self.key == 3:
					self.key = -1
					self.tts.stop()
					self.tts.speak("Route saved.Returning to home")
					end_point = self.gps.loc()
					timing=time.time()
					sampledpts[timing]={"loc":end_point,'attributes':None}
					out = self.sampling(sampledpts,self.attr)
					size = len(out)
					Li = []
					for i in range(size-1):
						Li.append ((tuple(out[i]["loc"]),{"attributes":out[i]["attributes"]}))
					i = size-1
					Li.append ((tuple(out[i]["loc"]),{"attributes":out[i]["attributes"],"name":name}))
					self.map.merge_with_path(Li)
					with open('li','wb') as f:
						dill.dump(Li,f)
					print(Li)
					self.map.draw_html("test_points.html")
					self.map.save_graph("graph.gml")
					return
	def addAttr(self,prevloc,brn):
		curloc=self.gps.loc()
		if prev == None:
			brng=brn
		else:
			brng = getBearing(prevloc,curloc)
		self.tts.speak("Select type of attributes")
		type=""
		starts=0
		dir=""
		while True:
			while (inp.key()==False).all():
				time.sleep(0.05)
			if(inp.pressed(0,0)==True):
				self.tts.stop()
				self.tts.speak("Footpath starting")
				self.key = 1
				type="footpath"
				starts=1
			elif(inp.pressed(0,1)==True):
				self.tts.stop()
				self.tts.speak("Footpath ending")
				self.key = 2
				type="footpath"
				starts=-1
			elif(inp.pressed(0,2)==True):
				self.tts.stop()
				self.tts.speak("Bus stop")
				type="bus stop"
				self.key = 3
			elif(inp.pressed(1,0)==True):
				self.tts.stop()
				self.tts.speak("Traffic signal")
				self.key = 4
				type="traffic signal"
			elif(inp.pressed(1,1)==True):
				self.tts.stop()
				self.tts.speak("Public place of utility")
				self.key = 5
				type="public place of utility"
			elif(inp.pressed(1,2)==True):
				self.tts.stop()
				self.tts.speak("Mall or market")
				self.key = 6
				type="mall or market"
			elif(inp.pressed(2,0)==True):
				self.stop.stop()
				self.tts.speak("Barrier")
				self.key=7
				type="barrier"
			elif(inp.pressed(3,2)==True): 
				self.tts.stop()
				if self.key == -1:
					self.tts.speak("Nothing selected")
					continue
				self.tts.speak("Attribute selected. Select Direction")
				self.key = -1
				while True:
					while (inp.key()==False).all():
						time.sleep(0.05)
					if(inp.pressed(0,1)==True):
						self.tts.stop()
						self.tts.speak("front")
						dir="front"
						self.key = 1 
					elif(inp.pressed(2,1)==True):
						self.tts.stop()
						self.tts.speak("behind")
						dir="behind"
						self.key = 1
					elif(inp.pressed(1,2)==True):
						self.tts.stop()
						self.tts.speak("Right")
						dir="right"
						self.key = 1
					elif(inp.pressed(1,0)==True):
						self.tts.stop()
						self.tts.speak("left")
						dir="left"
						self.key = 1
					elif(inp.pressed(3,2)==True):
						if self.key == -1:
							self.tts.speak("Nothing selected")
							continue
						self.tts.stop()
						self.tts.speak("Attribute added.")
						attributes={"type":type,"starts":starts,"dir":dir,"bearing":brng}
						time=time.time()
						self.attr[time]={"loc":curloc,"attributes":attributes}
						self.key = -2
						break
					elif(inp.pressed(3,0)==True):
						self.key = -1
						break
				if self.key!=-1:
					self.key = -1
					break
			elif(inp.pressed(3,0)==True):
				key = -1
				self.tts.speak("Exiting")
				break
		return attrpts

		#code for detecting deviation
	def getBearing(self,loc1,loc2):
		lat1=radians(loc1[0])
		lat2=radians(loc2[0])
		lon1=radians(loc1[1])
		lon2=radians(loc2[1])
		dLon = lon2 - lon1;
		y = sin(dLon) * cos(lat2)
		x = cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(dLon)
		brng = degrees(atan2(y, x))
		brng=(brng+360)%360
		return brng
	def getDifference(self,brng1,brng2):
		angle=(brng2-brng1)
		if(angle>180):
			angle=angle-360
		if(angle<-180):
			angle=angle+360
		return (angle)
	def getDeviationFromPath(self,curloc,loc1,loc2):
		brng1=self.getBearing(curloc,loc1)
		brng2=self.getBearing(curloc,loc2)
		angle=radians(fabs(getDifference(brng1,brng2)))
		a=vc(curloc,loc1).meters
		b=vc(curloc,loc2).meters
		base=vc(loc1,loc2).meters
		h=a*b*sin(angle)/base
		return h
	def detectDeviation(self,waypoints):
		getloc = self.gps()
		loc1 = (float(waypoints[0]["loc"][0]),float(waypoints[0]["loc"][1]))
		
		x = 1

		loc2 = (float(waypoints[x]["loc"][0]), float(waypoints[x]["loc"][1]))
		while x < len(waypoints) and self.stop_dev:
			curloc = tuple(getloc.loc())
			while(vc(curloc,loc2).meters>7 and self.stop_dev):
				curloc = tuple(getloc.loc())
				loc2 = (float(waypoints[x]["loc"][0]), float(waypoints[x]["loc"][1]))
				deviation=self.getDeviationFromPath(curloc,loc1,loc2)
				idealbrng=self.getBearing(curloc,loc2)
				routebrng=getloc.heading() 
				time.sleep(0.2)               
				
				if(deviation<7 and self.getDifference(idealbrng,routebrng)>40 ):
					pulsev.infwave(0.5,1.5)
					while(deviation<7 and self.getDifference(idealbrng,routebrng)>20 and self.stop_dev):
						#code to turn left
						curloc = tuple(getloc.loc())
						deviation=self.getDeviationFromPath(curloc,loc1,loc2)
						idealbrng=self.getBearing(curloc,loc2)
						routebrng=getloc.heading()
						time.sleep(0.5)
					pulsev.switchoff()
				
				if(deviation<7 and self.getDifference(idealbrng,routebrng) < (-40)):
					pulsev.infwave(1.5,0.5)
					while(deviation<7 and self.getDifference(idealbrng,routebrng)< (-20) and self.stop_dev):
						#code to turn right
						curloc = tuple(getloc.loc())
						deviation=self.getDeviationFromPath(curloc,loc1,loc2)
						idealbrng=self.getBearing(curloc,loc2)
						routebrng=getloc.heading() 
						time.sleep(0.5)
					pulsev.switchoff()
				
				if(deviation>7 and self.getDifference(idealbrng,routebrng)>40):
					self.out_of_path = True
					pulsev.infwave(0.5,1.5)
					pulseb.infwave(1,1)
					while(deviation>7 and self.getDifference(idealbrng,routebrng)>20 and self.stop_dev):
						#code to turn left and buzzer as well
						curloc = tuple(getloc.loc())
						deviation=self.getDeviationFromPath(curloc,loc1,loc2)
						idealbrng=self.getBearing(curloc,loc2)
						routebrng=getloc.heading()
						time.sleep(0.5)
					pulsev.switchoff()
					pulseb.switchoff()
				
				if(deviation>7 and self.getDifference(idealbrng,routebrng) < (-40)):
					self.out_of_path = True
					pulsev.infwave(1.5,0.5)
					pulseb.infwave(1,1)    
					while(deviation>7 and self.getDifference(idealbrng,routebrng) < (-20) and self.stop_dev):
						#code to turn right and buzzer as well
						curloc = tuple(getloc.loc())
						deviation=self.getDeviationFromPath(curloc,loc1,loc2)
						idealbrng=self.getBearing(curloc,loc2)
						routebrng=getloc.heading() 
						time.sleep(0.5)
					pulseb.switchoff()
					pulsev.switchoff()
				if(deviation>7 and fabs(self.getDifference(idealbrng,routebrng))<20):
					self.out_of_path = True
					pulseb.infwave(1,1)
					while(deviation>7 and fabs(self.getDifference(idealbrng,routebrng))<20  and self.stop_dev):
						#code for buzzer only
						curloc = tuple(getloc.loc())
						deviation=self.getDeviationFromPath(curloc,loc1,loc2)
						idealbrng=self.getBearing(curloc,loc2)
						routebrng=getloc.heading() 
						time.sleep(0.5)
					pulseb.switchoff()


			if self.curlocindex>x:
				loc1=loc2
				x+=1
	def return_path(self,path):
		#Traversing the navigation file
		self.curlocindex = 0
		self.tts.speak(path[curlocindex]["ins"])
		self.curlocindex+=1
		#starting thread for checking deviation from path
		self.stop_dev = True
		th1=threading.Thread(target=self.detectDeviation,args=(path,))
		th1.setDaemon(True)
		th1.start()
		while curlocindex<len(path):

			if(vc(self.gps.loc(), (float(path[curlocindex]["loc"][0]) ,float(path[curlocindex]["loc"][1]) ) ).meters < 5):
				self.tts.wait()
				self.tts.speak(path[curlocindex]["ins"])
				self.curlocindex+=1
			time.sleep(0.02)
			if self.input.pressed(3,0):
				self.key = 1
				self.tts.wait()
				self.tts.speak("Press enter to exit navigation")
			elif self.input.pressed(3,2):
				if self.key == -1:
					self.tts.wait()
					self.tts.speak("No option selected")
				elif self.key == 1:
					self.key = -1
					self.tts.wait()
					self.tts.speak("Returning to home")
					return 
	# if dviation is greater than some threshold, say 10 m, call this function
	def rerouting(self,Graph, index, fpath, destination):
		curloc = gps.loc()
		noLoc = fpath[index + 1]['loc']
		listSrc = find_nearby_nodes(curloc, 100)
		alterRoute = None
		mindist = nx.shortest_path_length(
			Graph, fpath[0]['loc'], destination) + 500
		for i in range(len(listSrc)):
			source = listSrc[i]
			path = nx.shortest_path(Graph, source, destination)
			dist = vc(curloc, source).meters + nx.shortest_path_length(Graph, source, destination)
			l = len(path)
			j = 0
			while j < l:
				if path[j] == noLoc:
					break
				else:
					if j == l - 1:
						if dist < mindist:
							alterRoute = path
							mindist = dist
				j += 1
		alterPath = None
		if alterRoute is not None:
			alterPath[0] = {'loc' : curloc, 'attributes' :Graph.node[curloc]}
			for k in len(alterRoute):
				alterPath[k + 1] = {'loc': path[k + 1],
									'attributes': Graph.node[path[k + 1]]}

		return alterPath

	def navigation(self,dest):
		#Traversing the navigation file
		self.attr = {}
		self.out_of_path = False
		curloc = self.gps.loc()
		p = routeSave.getPath(self.map,curloc,dest)
		path = routeSave.createFile(p)
		self.curlocindex = 0
		self.tts.speak(path[curlocindex]["ins"])
		self.curlocindex+=1
		#starting thread for checking deviation from path
		self.stop_dev = True
		new_path = None
		th1=threading.Thread(target=self.detectDeviation,args=(path,))
		th1.setDaemon(True)
		th1.start()
		while curlocindex<len(path):
			time.sleep(0.02)
			if(vc(self.gps.loc(), (float(path[curlocindex]["loc"][0]) ,float(path[curlocindex]["loc"][1]) ) ).meters < 5):
				self.tts.wait()
				self.tts.speak(path[curlocindex]["ins"])
				self.curlocindex+=1
			if self.input.pressed(3,0):
				self.key = 1
				self.tts.wait()
				self.tts.speak("Press enter to exit navigation")
			elif self.input.pressed(3,1):
				self.key = 2
				self.tts.wait()
				self.tts.speak("Press enter to add attributes")
			elif self.input.pressed(1,1):
				self.key = 3
				self.tts.wait()
				self.tts.speak("Press enter to return to source")
			elif self.input.pressed(2,1) and self.out_of_path:
				self.key = 4
				new_path = rerouting(map,curlocindex-1,p,dest)
				if new_path == None:
					self.tts.wait()
					self.tts.speak("Rerouting from here is not possible")
				else:	
					self.tts.wait()
					self.tts.speak("Reroute from here")
			elif self.input.pressed(3,2):
				if self.key == -1:
					self.tts.wait()
					self.tts.speak("No option selected")
				elif self.key == 1:
					self.key = -1
					self.tts.wait()
					self.tts.speak("Returning to home")
					arr = sorted(self.attr.items())
					size = len(arr)
					li = []
					for i in range(size):
						Li.append ((tuple(arr[i][1]["loc"]),{"attributes":arr[i][1]["attributes"]}))
					self.map.merge_with_path(Li)
					return -1
				elif self.key == 2:
					self.key = -1
					self.tts.wait()
					self.addAttr
					if(vc(self.gps.loc(), (float(path[curlocindex-1]["loc"][0]) ,float(path[curlocindex-1]["loc"][1]) ) ).meters < 5):
						a = curlocindex -2
					else:
						a = curlocindex-1
					if a <0:
						self.addAttr(None,self.gps.heading())
					else:
						self.addAttr(path[a]["loc"],None)
					# add attributes
				elif self.key == 3:
					self.key = -1
					self.tts.wait()
					self.stop_dev = False
					arr = sorted(self.attr.items())
					size = len(arr)
					li = []
					for i in range(size):
						Li.append ((tuple(arr[i][1]["loc"]),{"attributes":arr[i][1]["attributes"]}))
					self.map.merge_with_path(Li)
					self.tts.speak("Press any key to begin navigation to source")
					path = routeSave.returnFromPt(curlocindex-1,p)
					while (self.input.key()==False).all() or not self.gps.check_device_pos():
						time.sleep(0.05)
						if not (self.input.key()==False).all():
							while not (self.input.key()==False).all():
								time.sleep(0.01)
							self.tts.stop()
							self.tts.speak("Device not placed properly.Correct device position and press any key to start navigation")
					self.tts.stop()
					self.return_path(path)
					return -1
				elif self.key == 4:
					self.key = -1
					self.tts.wait()
					self.stop_dev = False
					self.tts.speak("New path detected")
					self.tts.wait()
					path = routeSave.createFile(new_path)
					self.curlocindex = 0
					self.tts.speak(path[curlocindex]["ins"])
					self.curlocindex+=1
					#starting thread for checking deviation from path
					self.stop_dev = True
					new_path = None
					th1=threading.Thread(target=self.detectDeviation,args=(path,))
					th1.setDaemon(True)
					th1.start()
					continue
	def searchdestination(self,my_loc,keyword):
		s_all = set([x[0] for x in self.map.getalldestination(my_loc)]) # all possible destinations in 15 m
		s_name = set(get_vertices_with_name(keyword,5))
		dest = list(s_all.intersect(s_name))
		return dest[:]
	def nearby(self):
		loc = gps.loc()
		points = self.filter_by_name(self.map.find_nearby_nodes(loc,20))
		page = 0
		while 1:
				for i in range(3):
					for j in range(3):
						time.sleep(0.01)
						if self.input.pressed(i,j):
							self.tts.stop()
							a = i*3+j+page*9
							if a<len(points):
								self.tts.speak(map.node(points[i*3+j+page*9])["name"])
				time.sleep(0.02)
				if self.input.pressed(3,1):
					self.key = -1
					self.tts.stop()
					maxpages = int(float(len(points))/9.0+0.9)
					if pages<maxpages-1:
						page+=1
						self.tts.speak("Page "+str(page+1))
					else:
						self.tts.speak("No more pages")
				elif self.input.pressed(3,0):
					self.key = -1
					self.tts.stop()
					if page>0:
						page-=1
						self.tts.speak("Page "+str(page+1))
					else:
						self.tts.speak("Home Menu")
						return		
	def savetofavourites(self,dest):
		#to save a file as favorites to quickly access it in future
		self.tts.speak('Select key to assign favourite')
		while 1:	
			for i in range(3):
				for j in range(3):
					time.sleep(0.01)
					if self.input.pressed(i,j):
						self.tts.stop()
						self.tts.speak(str(i*3+j+1))
						self.key = i*3+j+1
			time.sleep(0.02)
			if self.input.pressed(3,1):
				self.tts.stop()
				self.tts.speak("0")
				self.key = 0
			elif self.input.pressed(3,0):
				self.key = -1
				self.tts.stop()
				return -1
			elif self.input.pressed(3,2):
				if self.key == -1:
					self.tts.speak("No option selected")
				else:
					if self.favs[self.key] != None:
						self.tts.speak("This key is not empty and has destination "+self.favs[self.key][0]+"stored in it. Press enter to overwrite or Back to choose other key")
						con = False
						while True:
							if self.input.pressed(3,2):
								self.tts.stop()
								self.favs[self.key] = dest
							elif self.input.pressed(3,0):
								self.tts.stop()
								con = True
								break
						if con == True:
							continue
					self.tts.stop()
					self.tts.speak("Destination Saved at "+str(self.key))
					self.favs[self.key] = dest 
					self.key = -1
	def favourites(self):
		self.tts.speak("Select destination")
		while 1:
			for i in range(3):
				for j in range(3):
					time.sleep(0.01)
					if self.input.pressed(i,j):
						self.tts.stop()
						if self.favs[i*3+j+1]==None:
							self.tts.speak("No file at " + str(i*3+j+1))
							break
						self.tts.speak(self.favs[i*3+j+1][0])
						self.key = self.favs[i*3+j+1]
			time.sleep(0.02)
			if self.input.pressed(3,1):
				if self.favs[0]==None:
					self.tts.speak("No file at 0")
				else:
					self.tts.stop()
					self.tts.speak(self.favs[0][0])
					self.key = self.favs[0]
			elif self.input.pressed(3,0):
				self.key = -1
				self.tts.stop()
				return -1
			elif self.input.pressed(3,2):
				if self.key==-1:
					self.tts.speak("No option selected")
				else:
					self.tts.stop()
					a = self.key
					self.key = -1
					return a
	def getdestination(self):
		#Getting the destination for navigation from user
		while True:
			self.tts.speak("Select destination search method")
			destinations = []
			while 1:
				time.sleep(0.02)
				if self.input.pressed(0,0):
					self.tts.stop()
					self.key=1
					self.tts.speak("Search destination by Name")
				elif self.input.pressed(0,1):
					self.tts.stop()
					self.key=2
					self.tts.speak("Scroll through all destinations")
				elif self.input.pressed(0,2) and self.favs!= [None]*10:
					self.tts.stop()
					self.key=3
					self.tts.speak("Get destination from favourites")
				elif self.input.pressed(3,0):
					self.tts.stop()
					self.key = -1
					self.tts.speak("Home menu")
					return -1
				elif self.input.pressed(3,2):
					self.tts.stop()
					if self.key==(-1):
						self.tts.speak("No option selected")
					elif self.key==1:
						self.key = (-1)
						self.tts.speak("Type destination name")
						keyword = self.input.text()
						if keyword == '':
							break
						my_loc = gps.loc()
						destinations = self.searchdestination(my_loc,keyword)
					elif self.key==2:
						self.key = (-1)
						my_loc = gps.loc()
						destinations = self.map.getalldestination(my_loc)
					elif self.key==3:
						self.key = (-1)
						des = self.favourites()
						if des == -1:
							break
						return des
			if destinations == []:
				continue
			self.tts.speak("Select destination")
			page = 0
			while 1:
				for i in range(3):
					for j in range(3):
						time.sleep(0.01)
						if self.input.pressed(i,j):
							self.tts.stop()
							a = i*3+j+page*9
							if a<len(destinations):
								self.tts.speak(destinations[i*3+j+page*9][0])
								self.key = destinations[i*3+j+page*9]
				time.sleep(0.02)
				if self.input.pressed(3,1):
					self.key = -1
					self.tts.stop()
					maxpages = int(float(len(destinations))/9.0+0.9)
					if pages<maxpages-1:
						page+=1
						self.tts.speak("Page "+str(page+1))
					else:
						self.tts.speak("No more pages")
				elif self.input.pressed(3,0):
					self.key = -1
					self.tts.stop()
					if page>0:
						page-=1
						self.tts.speak("Page "+str(page+1))
					else:
						break
				elif self.input.pressed(3,2):
					if self.key==-1:
						self.tts.speak("No option selected")
					else:
						self.tts.stop()
						l = self.key
						self.key=-1
						return l
	def navigate(self):
		self.map.importfiles("bluetooth")
		dest = getdestination()
		if dest == -1:
			return
		self.tts.speak("Destination Selected. Place the device on your waist and press any button to start navigation")
		while (self.input.key()==False).all() or not self.gps.check_device_pos():
			time.sleep(0.05)
			if not (self.input.key()==False).all():
				while not (self.input.key()==False).all():
					time.sleep(0.01)
				self.tts.stop()
				self.tts.speak("Device not placed properly.Correct device position and press any key to start navigation")
		self.tts.stop()
		if self.navigation(dest[1]) == -1:
			return
		while 1:
				time.sleep(0.02)
				if self.input.pressed(0,0):
					self.tts.stop()
					self.key=1
					self.tts.speak("Return to home Menu")
				elif self.input.pressed(0,1):
					if not dest in self.favs:
						self.tts.stop()
						self.key=2
						self.tts.speak("Save this destination in favourites")
				elif self.input.pressed(3,2):
					self.tts.stop()
					if self.key==(-1):
						self.tts.speak("No option selected")
					elif self.key==1:
						self.key = (-1)
						self.tts.speak("Home menu")
						return
					elif self.key==2:
						self.key = (-1)
						if self.savetofavourites(dest) == -1:
							continue
						return
	def home(self):
		#Interface: home menu, when the device starts
		while 1:
			time.sleep(0.02)
			if self.input.pressed(0,0):
				self.tts.stop()
				self.key=1
				self.tts.speak("Navigate")
			elif self.input.pressed(0,1):
				self.tts.stop()
				self.key=2
				self.tts.speak("Store new Route")
			elif self.input.pressed(0,2):
				self.tts.stop()
				self.key=3
				self.tts.speak("What are places near me")
			elif self.input.pressed(3,2):
				self.tts.stop()
				if self.key==(-1):
					self.tts.speak("No option selected")
				elif self.key==1:
					self.key = (-1)
					self.navigate()
				elif self.key==2:
					self.key = (-1)
					self.tts.speak("Route saving mode")
					self.store()
				elif self.key==3:
					self.key = (-1)
					self.tts.speak("Places in 20 m radius")
					self.nearby()
