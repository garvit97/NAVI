import nvector as nv
from aenum import Enum
from math import fabs
from geopy.distance import vincenty as vc
from numpy.linalg import norm
from math import cos, sin, acos, degrees, atan2, radians
from itertools import chain
import cmath
import gmplot

# Enum to represent position of a point with respect to a path
PositionOnPath = Enum('PositionOnPath', 'NotOnPathOnCircle OnPath NotOnCircle')

# Constants
EARTH_RADIUS = 6371e3


def crosstrack_distance(a1, a2, b):
	frame = nv.FrameE(a=EARTH_RADIUS, f=0)
	pointA1 = frame.GeoPoint(a1[0], a1[1], degrees=True)
	pointA2 = frame.GeoPoint(a2[0], a2[1], degrees=True)
	pointB = frame.GeoPoint(b[0], b[1], degrees=True)
	pathA = nv.GeoPath(pointA1, pointA2)
	cr_distance = pathA.cross_track_distance(
		pointB, method='greatcircle').ravel()
	return cr_distance[0]


def closest_point_on_circle(a1, a2, b):
	frame = nv.FrameE(a=EARTH_RADIUS, f=0)
	pointA1 = frame.GeoPoint(a1[0], a1[1], degrees=True)
	pointA2 = frame.GeoPoint(a2[0], a2[1], degrees=True)
	pointB = frame.GeoPoint(b[0], b[1], degrees=True)
	pathA = nv.GeoPath(pointA1, pointA2)
	closest_point = pathA.closest_point_on_great_circle(pointB).to_geo_point()
	lat, lon = closest_point.latitude_deg.tolist(
	)[0], closest_point.longitude_deg.tolist()[0]
	return lat, lon


def position_on_path(a1, a2, b):
	frame = nv.FrameE(a=EARTH_RADIUS, f=0)
	pointA1 = frame.GeoPoint(a1[0], a1[1], degrees=True)
	pointA2 = frame.GeoPoint(a2[0], a2[1], degrees=True)
	pointB = frame.GeoPoint(b[0], b[1], degrees=True)
	pathA = nv.GeoPath(pointA1, pointA2)
	if pathA.on_great_circle(pointB):
		if pathA.on_path(pointB):
			return PositionOnPath.OnPath
		else:
			return PositionOnPath.NotOnPathOnCircle
	else:
		return PositionOnPath.NotOnCircle


def approximately_on_path(a1, a2, b, threshold=2):
	if(fabs(crosstrack_distance(a1, a2, b)) <= threshold):
		closest_point = closest_point_on_circle(a1, a2, b)
		if(position_on_path(a1, a2, closest_point) == PositionOnPath.OnPath):
			return True
	return False

def on_path(a1, a2, b):
	closest_point = closest_point_on_circle(a1, a2, b)
	if(position_on_path(a1, a2, closest_point) == PositionOnPath.OnPath):
		return True
	return False

def approximately_on_circle_not_on_path(a1, a2, b, threshold=2):
	if(fabs(crosstrack_distance(a1, a2, b)) <= threshold):
		closest_point = closest_point_on_circle(a1, a2, b)
		if(position_on_path(a1, a2, closest_point) == PositionOnPath.NotOnPathOnCircle):
			return True
	return False


def intersection_point(a1, a2, b1, b2):
	frame = nv.FrameE(a=EARTH_RADIUS, f=0)
	pointA1 = frame.GeoPoint(a1[0], a1[1], degrees=True)
	pointA2 = frame.GeoPoint(a2[0], a2[1], degrees=True)
	pointB1 = frame.GeoPoint(b1[0], b1[1], degrees=True)
	pointB2 = frame.GeoPoint(b2[0], b2[1], degrees=True)
	pathA = nv.GeoPath(pointA1, pointA2)
	pathB = nv.GeoPath(pointB1, pointB2)
	ipoint = pathA.intersect(pathB).to_geo_point()
	return float(ipoint.latitude_deg[0]), float(ipoint.longitude_deg[0])


def nearest_point_of_edge(a1, a2, b):
	return a1 if vc(a1, b).meters <= vc(a2, b).meters else a2


def metric_distance(p1, p2):
	""" Distance between two GPS coordinates in meters """
	return vc(p1, p2).meters


def surface_distance(p1, p2):
	frame = nv.FrameE(name='WGS84')
	a1 = frame.GeoPoint(p1[0], p1[1], degrees=True)
	a2 = frame.GeoPoint(p2[0], p2[1], degrees=True)
	a_12_e = a1.to_ecef_vector() - a2.to_ecef_vector()
	d = norm(a_12_e.pvector, axis=0)[0]
	return d

# function to return bearing between 2 points (angle from north)


def getBearing(loc1, loc2):
	lat1 = radians(loc1[0])
	lat2 = radians(loc2[0])
	lon1 = radians(loc1[1])
	lon2 = radians(loc2[1])
	dLon = lon2 - lon1
	y = sin(dLon) * cos(lat2)
	x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
	brng = degrees(atan2(y, x))
	brng = (brng + 360) % 360
	return brng

# function to return angle between 2 lines with bearings brng1 and brng2


def getDifference(brng1, brng2):
	angle = (brng2 - brng1)
	if(angle > 180):
		angle = angle - 360
	if(angle < -180):
		angle = angle + 360
	return (angle)


def angle_between_edges(e1, e2):
	b1 = getBearing(e1[0], e1[1])
	b2 = getBearing(e2[0], e2[1])
	d=fabs(getDifference(b1,b2))
	if d>90:
		return 180-d
	return d 

def visualize_path(elist,name):
	nodes=list({edge[i] for edge in elist for i in range(2)})
	lats,longs=list(zip(*nodes))
	gmp=gmplot.GoogleMapPlotter(lats[0],longs[0],16)
	gmp.scatter(lats,longs,'#FF00FF',size=1,marker=False)
	for e in elist:
		tlat,tlon=list(zip(*e))
		gmp.plot(tlat,tlon,color='red',edge_width=3)
	gmp.draw(name)

CrossingPosition=Enum('CrossingPosition','OnOldEdge OnNewEdge OnBoth OnNone')

def three_cases_wrt_crossing_lines(oldedge,newedge,ipoint):
	b1=on_path(oldedge[0],oldedge[1],ipoint)
	b2=on_path(newedge[0],newedge[1],ipoint)

	if b1 and b2:
		return CrossingPosition.OnBoth

	if b1:
		return CrossingPosition.OnOldEdge

	if b2:
		return CrossingPosition.OnNewEdge

	return CrossingPosition.OnNone

	
