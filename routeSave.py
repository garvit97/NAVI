import json
import math
from time import time as gettime
import gmplot
import sys
import time
from geopy.distance import vincenty as vc
import networkx as nx
def getBearing(loc1,loc2):
	lat1=math.radians(loc1[0])
	lat2=math.radians(loc2[0])
	lon1=math.radians(loc1[1])
	lon2=math.radians(loc2[1])
	dLon = lon2 - lon1;
	y = math.sin(dLon) * math.cos(lat2)
	x = math.cos(lat1)*math.sin(lat2)-math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
	brng = math.degrees(math.atan2(y, x))
	brng=(brng+360)%360
	return brng

def getDifference(brng1,brng2):
	angle=(brng2-brng1)
	if(angle>180):
		angle=angle-360
	if(angle<-180):
		angle=angle+360
	return (angle)

def createFile(fpath): #fpath is a list of vertices
	instructions=[]
	curPt=fpath[0]
	# print(curPt)
	instructions[0]={"loc":curPt['loc'],"ins":"Move straight "}
	i=1
	j=1
	l=len(fpath)
	while (j<l-1):
		curPt=fpath[j]      
		print(curPt)
		if curPt["attributes"] is None:
			if fpath[j-1]["attributes"] is None:
				prevPt=fpath[j-1]
			elif fpath[j-2]["attributes"] is None:
				prevPt=fpath[j-2]
			else:
				prevPt=fpath[j-3]
			if (j<(l-2)):
				if fpath[j+1]["attributes"] is None:
					nextPt=fpath[j+1]
				elif fpath[j+2]["attributes"] is None:
					nextPt=fpath[j+2]
			else:
				nextPt=fpath[j+1]


			brng1=getBearing(prevPt['loc'],curPt['loc'])
			brng2=getBearing(curPt['loc'],nextPt['loc'])
			diff=getDifference(brng1,brng2)
			print(prevPt, curPt, nextPt, brng1, brng2,diff)

			if(diff>30 or diff<-30):
				
				if(diff<60 and diff>30):
					dir="turn slight right ahead"
				elif(diff>-60 and diff<-30):
					dir="turn slight left ahead"
				elif(diff>60):
					dir="turn right ahead"
				elif(diff<-60):                     
					dir="turn left ahead"
				instructions[i]={"loc":curPt["loc"],"ins":dir}
				i+=1


		else:
			attr=curPt["attributes"]
			prevPt=fpath[j-1]
			brng2=getBearing(prevPt["loc"],curPt["loc"])
			differ=getDifference(brng2,attr["bearing"])
			dir=attr["dir"]
			starts=" "
			if differ>120 or differ<-120:
				if attr["dir"]=="left":
					dir="right"
				elif attr["dir"]=="right":
					dir="left"
				elif attr["dir"]=="front":
					dir="behind"
				elif attr["dir"]=="behind":
					dir="front"
				if attr['starts']==-1:
					starts=" starting "
				elif attr['starts']==1: 
					starts=" ending "
			elif differ>60 and differ<120:
				if attr["dir"]=="left":
					dir="front"
				elif attr["dir"]=="right":
					dir="behind"
				elif attr["dir"]=="front":
					dir="right"
				elif attr["dir"]=="behind":
					dir="right"
				if attr['starts']==1:
					starts=" starting "
				elif attr['starts']==-1: 
					starts=" ending "
			elif differ>-120 and differ<-60:
				if attr["dir"]=="left":
					dir="behind"
				elif attr["dir"]=="right":
					dir="front"
				elif attr["dir"]=="front":
					dir="left"
				elif attr["dir"]=="behind":
					dir="right"
				if attr['starts']==1:
					starts=" starting "
				elif attr['starts']==-1: 
					starts=" ending "

			ins=" There is a "+attr['type']+ starts+" on your " + dir
			instructions[i]={"loc":curPt['loc'],"ins":ins}
			i+=1
		j+=1
	instructions[i]={"loc":fpath[j]['loc'],"ins":"you have reached your destination"}

	return instructions

def returnFromPt(index, path):
	newpath={}
	newpath[0]={"loc":gps.loc(),"attributes":None}
	i=1
	while index>-1:
		newpath[i]=path[index]
		index-=1
		i+=1
	inst2=createFile(newpath)
	return inst2

def getPath(Graph,curloc,destination):
	nearby=find_nearby_edge_points(curloc[0],curloc[1], 15)
	source1=nearby[0][0]
	source2=nearby[0][1]
	intersection=nearby[1]
	len1=vc(intersection,source1).meters+nx.shortest_path_length(Graph,source1,destination)
	len2=vc(intersection,source2).meters+nx.shortest_path_length(Graph,source2,destination)
	if(len1>=len2):
		path=nx.shortest_path(Graph,source2,destination)
	else:
		path=nx.shortest_path(Graph,source1,destination)
	finalpath={}
	finalpath[0]={'loc':curloc,'attributes':None}
	finalpath[1]={'loc':list(intersection),'attributes':None}
	i=2
	k=0
	while k<len(path):
		finalpath[i]={'loc':list(path[k]),'attributes':Graph.node[path[k]]["attributes"]}
		i+=1
		k+=1
	return finalpath


# if __name__=="__main__":
#   with open("filenew4.json") as dataf:
#       points=json.load(dataf)
#       # print(inputf)
#       # for e in enumerate(points.items()):
#       #   if(e[0]<6):
#       #       print(e)
#       # sys.exit(0)
#       list1=sorted(points.items())
#       pointsArray={i:item[1] for i,item in enumerate(list1)}
#       # print(pointsArray)
#       with open("filenew42.json",'w') as data_f2:
#           json.dump(pointsArray, data_f2,indent=2)
#       # inputPts=inputf["points"]
#       outPts=getDecPt(pointsArray)
#       with open("filenew41.json",'w') as data_f:
#           json.dump(outPts, data_f,indent=2)
		
#       mylist=[outPts[item]['loc'] for item in outPts]
#       latt,lont=zip(*mylist)
#       latlist=list(latt)
#       lonlist=list(lont)
#       print(len(latlist))
#       gmap = gmplot.GoogleMapPlotter(latlist[0],lonlist[0], 120)
#       gmap.plot(latlist, lonlist, 'cornflowerblue', edge_width=2)
#       gmap.scatter([latlist[0],latlist[-1]], [lonlist[0],lonlist[-1]], '#3B0B39', size=40, marker=False)
#       gmap.draw("map.html")
#   # with open("navList.json") as pathf:
#   #   inputList=json.load(pathf)
#   #   navPts=inputList["navPoints"]
#   #   inst=createFile(navPts)
#   #   with open("dirToUser.json",'w') as speakthis:
#   #       json.dump(inst,speakthis,indent=2)

#   # with open("directions2.json") as dataf2:
#   #   inputf2=json.load(dataf2)
#   #   print(inputf2)
#   #   inputPts2=inputf2["points"]
#   #   outPts2=assignBearing(inputPts2)
#   #   with open("filenew2.json",'w') as data_f2:
#   #       json.dump(outPts2, data_f2,indent=3)

#   # pts=sample2m()
#   # with open("filenew3.json",'w') as data_f3:
#   #   json.dump(pts, data_f3,indent=3)










