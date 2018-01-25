import networkx as nx
import threading
from os.path import isfile
from sklearn.neighbors import NearestNeighbors
import numpy as np
from editdistance import eval as word_distance
import time
from graph_utils import visualize_path,crosstrack_distance, PositionOnPath, position_on_path, closest_point_on_circle, metric_distance, angle_between_edges, intersection_point, approximately_on_path, CrossingPosition, three_cases_wrt_crossing_lines
from functools import partial
from aenum import Enum
from itertools import chain
from math import fabs
import gmplot
import dill

class Graph:
	class __Graph:
		def __init__(self, path_to_file=None):
			if path_to_file == None:
				self._graph = nx.Graph()
			else:
				if isfile(path_to_file):
					self._graph = nx.read_gpickle(path_to_file)
				else:
					self._graph = nx.Graph()
		def __str__(self):
			return str(self._graph)

		def __repr__(self):
			return repr(self._graph)

		def __getattr__(self, item):
			return getattr(self._graph, item)

		def __getitem__(self, item):
			return self._graph[item]

		def __iter__(self):
			return iter(self._graph)

		def __len__(self):
			return len(self._graph)

		def add_edge_with_distance(self, *args, **kwargs):
			srcname=None
			destname=None
			coordinates_list = flatten(args)
			if len(coordinates_list) != 4:
				print(coordinates_list)
				raise ValueError(
					'Only latitude and longitude of source and destination must be entered')
			p1 = (float(coordinates_list[0]), float(coordinates_list[1]))
			p2 = (float(coordinates_list[2]), float(coordinates_list[3]))
			distance = metric_distance(p1, p2)
			if srcname:
				self.add_vertex(*p1, name=srcname)
			if p1 not in self._graph:
				self.add_vertex(*p1)
			if destname:
				self.add_vertex(*p2, name=destname)
			if p2 not in self._graph:
				self.add_vertex(*p2)
			if kwargs:
				self._graph.add_edge(p1, p2, weight=distance, **kwargs)
			else:
				self._graph.add_edge(p1, p2, weight=distance)


		def get_vertices_with_name(self, name, edit_distance=0):
			wd = partial(word_distance, name.lower())

			def fn(node):
				return wd(self._graph.node[node]['name'].lower())
			return sorted((v for v in self._graph if fn(v) <= edit_distance), key=fn)

		def merge_nearby_points(self, seq, threshold=1):
			node_array = self._graph.nodes()
			nbrs = NearestNeighbors(
				radius=threshold, metric=metric_distance, n_jobs=-1).fit(node_array)
			nearest_points = nbrs.radius_neighbors(seq)
			distances, indices = nearest_points
			distances = [x.tolist() for x in distances]
			indices = [x.tolist() for x in indices]
			result = (seq[i] if len(distance_arr) == 0 else node_array[indices[i][0]]
					  for i, distance_arr in enumerate(distances))
			return result

		def find_nearby_edge_points(self, lat, lon, threshold=10):
			edge_array = self._graph.edges()
			# distlist = [_edge_point_distance(e, (lat, lon)) for e in edge_array if _is_point_on_edge(e, (lat, lon))]
			distlist = [_edge_point_distance(e, (lat, lon)) for e in edge_array]
			flist = sorted((dist, i)
						   for i, dist in enumerate(distlist) if dist <= threshold)
			distances, indices = zip(*flist)

			#index = distlist.index(min(distlist))
			for i in indices:
				edge = edge_array[i]
				yield edge, closest_point_on_circle(edge[0], edge[1], (lat, lon))

		def getalldestinations(self, location):
			nearbyedges = list(self.find_nearby_edge_points(
				location[0], location[1], 15))
			nearbynodes = set(n[0][0] for n in nearbyedges)
			connectedcomps = (nx.node_connected_component(
				self._graph, n) for n in nearbynodes)
			possiblenodes = set(chain.from_iterable(connectedcomps))
			possibledests = ((self._graph.node[n]['name'], n) for n in possiblenodes if self._graph.node[n]
							 ['name'] != None or self._graph.node[n]['name'] != self._graph.node[n]['id'])
			return possibledests

		def import_files(path_to_folder):
			raise NotImplementedError

		def find_nearby_nodes(self, lat, lon, threshold=10):
			node_array = self._graph.nodes()
			nbrs = NearestNeighbors(
				radius=threshold, metric=metric_distance, n_jobs=-1).fit(node_array)
			nearest_points = sorted(nbrs.radius_neighbors((lat, lon)))
			distances, indices = nearest_points
			result = [node_array[i] for i in indices]
			return result

		def add_vertex(self, lat, lon, **kwargs):
			lat = float(lat)
			lon = float(lon)

			if (lat, lon) not in self._graph:
				id = _generate_unique_node()
			else:
				id = self._graph.node[(lat, lon)]['id']

			if kwargs:
				if 'name' in kwargs:
					self._graph.add_node((lat, lon), id=id, **kwargs)
				else:
					self._graph.add_node((lat, lon), id=id, name=id, **kwargs)
			else:
				self._graph.add_node((lat, lon), id=id, name=id)

		def add_vertices(self, nodes):
			for n in nodes:
				if len(n) == 3:
					lat=n[0]
					lon=n[1]
					attr=n[2]
					self.add_vertex(lat, lon, **attr[0])
				elif len(n) == 2:
					self.add_vertex(*n)
				else:
					raise TypeError("incorrect type of node " +
									str(type(node)) + " or its elements")

		def merge_with_path(self, seq, road_width=15, same_point_distance=10, theta=10):
			path_points = list(item[0] for item in seq)
			path_attr = list({} if len(item) == 1 else item[1] for item in seq)
			if len(self._graph) != 0:
				merged_path_points = list(self.merge_nearby_points(
					path_points, same_point_distance))
			else:
				merged_path_points = [item[0] for item in seq]
			path = dict(zip(merged_path_points, path_attr))
			graph_edge_array = self._graph.edges()
			new_graph = graph_edge_array[:]
			path_edge_array = [(merged_path_points[i], merged_path_points[i + 1])
							   for i in range(len(merged_path_points) - 1)]

			# def pred(item):
			#     if item[0] <= theta:
			#         return True
			#     else:
			#         return False

			# PointE = Enum('PointE', 'Mergeable',
			#               'Crossing', 'CorM', 'Separate')

			# def key(item):
			#     if len(item[0]) == 0 and len(item[1]) != 0:
			#         return PointE.Crossing
			#     elif len(item[0]) != 0:
			#         pea = [it[2] for it in item[0]]
			#         gea = [graph_edge_array[it[1]] for it in item[0]]
			#         flip_projectionable_points = flip(_projectable_points, gea)

			#         if any(flip_projectionable_points(p) for p in pea):
			#             return PointE.Mergeable
			#     return PointE.Separate

			# angle_dict = {item:
			#               _partition(sorted((angle_between_edges(e, item), i) for i, e in enumerate(graph_edge_array), pred))
			#               for item in path_edge_array}

			# filtered_dict = {k: groupby(key, i) for k, i in angle_dict.items()}

			# for e in path_edge_array:
			#     ord_gr_edges = sorted(angle_dict[e])
			#     for ge in ord_gr_edges:
			#         if _are_edges_nearby(e, ge, road_width):
			#             _merge_edges(self._graph, e, ge, path)

			for e in path_edge_array:
				EDGE_NOT_ADDED = True
				for ge in graph_edge_array:
					if angle_between_edges(e, ge) <= theta:
						p_pt = _projectable_points(e, ge)
						if len(p_pt) != 0:
							s = set(e)
							np_pt = s - p_pt
							# if len(np_pt) == 2:
							#     gep1 = ge[0] if metric_distance(
							#         e[0], ge[0]) <= metric_distance(e[0], ge[1]) else ge[1]
							#     gep2 = ge[0] if metric_distance(
							#         e[1], ge[0]) <= metric_distance(e[1], ge[1]) else ge[1]
							#     new_graph.extend([(gep1, e[0]), (gep2, e[1])])
							if len(np_pt) == 1:
								np_pt = next(iter(np_pt))
								p_pt = next(iter(p_pt))
								genppt = ge[0] if metric_distance(
									np_pt, ge[0]) <= metric_distance(np_pt, ge[1]) else ge[1]
								if ge in new_graph:
									new_graph.remove(ge)
								new_graph.append((genppt, np_pt))
								new_graph.extend(
									[(ge[0], closest_point_on_circle(ge[0], ge[1], p_pt)), (ge[1], closest_point_on_circle(ge[0], ge[1], p_pt))])
								EDGE_NOT_ADDED = False
							if len(np_pt) == 0:
								gep1 = ge[0] if metric_distance(
									e[0], ge[0]) <= metric_distance(e[1], ge[0]) else ge[1]
								tlist = list(ge)
								tlist.remove(gep1)
								gep2 = tlist[0]
								if ge in new_graph:
									new_graph.remove(ge)
								new_graph.extend(
									[(closest_point_on_circle(ge[0], ge[1], e[0]), gep1), (gep2, closest_point_on_circle(ge[0], ge[1], e[1])), (e[0], e[1])])
								EDGE_NOT_ADDED = False
						else:
							p_pt = _projectable_points(ge, e)
							if len(p_pt) == 2:
								gep1 = ge[0] if metric_distance(
									e[0], ge[0]) <= metric_distance(e[0], ge[1]) else ge[1]
								gep2 = ge[0] if metric_distance(
									e[1], ge[0]) <= metric_distance(e[1], ge[1]) else ge[1]
								new_graph.extend([(closest_point_on_circle(
									e[0], e[1], gep1), e[0]), (closest_point_on_circle(e[0], e[1], gep2), e[1])])
								EDGE_NOT_ADDED = False
					else:
						ipoint = intersection_point(ge[0], ge[1], e[0], e[1])

						cp = three_cases_wrt_crossing_lines(ge, e, ipoint)

						# p = approximately_on_path(ge[0], ge[1], ipoint)
						if cp == CrossingPosition.OnBoth:
							edge_e1i = (ipoint, e[0])
							edge_e2i = (ipoint, e[1])
							edge_g1i = (ipoint, ge[0])
							edge_g2i = (ipoint, ge[1])
							delta = metric_distance(e[0], e[1]) - (metric_distance(
								edge_e1i[0], edge_e1i[1]) + metric_distance(edge_e2i[0], edge_e2i[1]))
							if delta == 0.0:
								new_graph.extend(
									[edge_e1i, edge_e2i, edge_g1i, edge_g2i])
							# elif delta<0:
							#     if metric_distance(edge_e1i[0],edge_e1i[1])<metric_distance(edge_e2i[0],edge_e2i[1]):
							#         new_graph.extend([edge_e1i,e,edge_g1i,edge_g2i])
							#     else:
							#         new_graph.extend([edge_e2i,e,edge_g1i,edge_g2i])
							if ge in new_graph:
								new_graph.remove(ge)
							EDGE_NOT_ADDED = False

						elif cp == CrossingPosition.OnOldEdge:
							close_point = e[0] if metric_distance(
								e[0], ipoint) < metric_distance(e[1], ipoint) else e[1]
							if metric_distance(close_point,ipoint)>same_point_distance:
								continue
							ipoint=closest_point_on_circle(ge[0],ge[1],close_point)
							edge_e1i = (ipoint, e[0])
							edge_e2i = (ipoint, e[1])
							edge_g1i = (ipoint, ge[0])
							edge_g2i = (ipoint, ge[1])
							delta = metric_distance(e[0], e[1]) - (metric_distance(
								edge_e1i[0], edge_e1i[1]) + metric_distance(edge_e2i[0], edge_e2i[1]))
							# if delta == 0.0:
							#     new_graph.extend([edge_e1i, edge_e2i, edge_g1i, edge_g2i])
							if delta < 0:
								if metric_distance(edge_e1i[0], edge_e1i[1]) < metric_distance(edge_e2i[0], edge_e2i[1]):
									new_graph.extend(
										[edge_e1i, e, edge_g1i, edge_g2i])
								else:
									new_graph.extend(
										[edge_e2i, e, edge_g1i, edge_g2i])
							if ge in new_graph:
								new_graph.remove(ge)
							EDGE_NOT_ADDED = False
						
						elif cp==CrossingPosition.OnNewEdge:
							continue

							close_point = ge[0] if metric_distance(
								ge[0], ipoint) < metric_distance(ge[1], ipoint) else ge[1]
							if metric_distance(close_point,ipoint)>same_point_distance:
								continue
							ipoint=closest_point_on_circle(e[0],e[1],close_point)
							edge_e1i = (ipoint, e[0])
							edge_e2i = (ipoint, e[1])
							edge_g1i = (ipoint, ge[0])
							edge_g2i = (ipoint, ge[1])
							delta = metric_distance(ge[0], ge[1]) - (metric_distance(
								edge_g1i[0], edge_g1i[1]) + metric_distance(edge_g2i[0], edge_g2i[1]))
							# if delta == 0.0:
							#     new_graph.extend([edge_e1i, edge_e2i, edge_g1i, edge_g2i])
							if delta < 0:
								if metric_distance(edge_e1i[0], edge_e1i[1]) < metric_distance(edge_e2i[0], edge_e2i[1]):
									new_graph.extend(
										[edge_e1i, e, edge_g1i, edge_g2i])
								else:
									new_graph.extend(
										[edge_e2i, e, edge_g1i, edge_g2i])
							if ge in new_graph:
								new_graph.remove(ge)
							EDGE_NOT_ADDED = False


				if EDGE_NOT_ADDED:
					new_graph.append((e[0], e[1]))

			s1 = set(new_graph) - set(graph_edge_array)

			visualize_path(set(new_graph),'curgraph.html')

			s2 = set(graph_edge_array) - set(new_graph)
			for s in s1:
				self.add_edge_with_distance(s)

			self._graph.remove_edges_from(s2)

			for n, attr in path.items():
				self._graph.node[n].update(attr)

		def save_graph(self,file=None):
			if file is None:
				nx.write_gpickle(self._graph, 'graph.gpickle')
			else:
				# print(type(self._graph.nodes()[0]))
				# print(type(self._graph.nodes()[0][0]))
				# with open('backup.gml','wb') as f:
				# 	dill.dump(self._graph,f)
				
				nx.write_gpickle(self._graph, file)

		def draw_html(self,file=None):
			if file is None:
				file=str(time.time()+'.html')
			nodes=self._graph.nodes()
			lat,lon=zip(*nodes)
			gmap=gmplot.GoogleMapPlotter(lat[0],lon[0],16)
			gmap.scatter(lat,lon, 'k', marker=True)
			# gmap.plot(lat, lon, 'cornflowerblue', edge_width=10)
			gmap.draw(file)

	_instance = None
	_lock = threading.RLock()

	def __init__(self, path_to_file=None):
		if Graph._instance is None:
			with Graph._lock:
				if Graph._instance is None:
					Graph._instance = Graph.__Graph(path_to_file)

	@property
	def status(self):
		with Graph._lock:
			return Graph._instance is None

	def __getattr__(self, name):
		with Graph._lock:
			return getattr(Graph._instance, name)

	def __str__(self):
		with Graph._lock:
			return str(Graph._instance)

	def __repr__(self):
		with Graph._lock:
			return repr(Graph._instance)

	def reset(self):
		with Graph._lock:
			Graph._instance = None

	def reinitialize(self, path_to_file=None):
		if Graph._instance is None:
			with Graph._lock:
				if Graph._instance is None:
					Graph._instance = Graph.__Graph(path_to_file)
		else:
			raise ValueError('Reset the Graph first')

	def __getitem__(self, item):
		return Graph._instance[item]

	def __iter__(self):
		return iter(Graph._instance)

	def __len__(self):
		return len(Graph._instance)


# def _testiter(iter_):
#     return isinstance(iter_, Iterable) and not (isinstance(iter_, str) and len(iter_) == 1)


# def flatten(nested_iter):
#     return 
#     """ Recursively flatten the list """
#     for element in nested_iter:
#         yield from flatten(element) if _testiter(element) else [element]

def flatten(x):
	result = []
	for el in x:
		if hasattr(el, "__iter__") and not isinstance(el, basestring):
			result.extend(flatten(el))
		else:
			result.append(el)
	return result

def __get_nearest_neighbors(seq, dataset, radius=1):
	nbrs = NearestNeighbors(radius=radius, metric=metric_distance).fit(dataset)
	return nbrs.radius_neighbors()


def _generate_unique_node():
	return str(time.time())


def _edge_point_distance(e, b):
	return fabs(crosstrack_distance(e[0], e[1], b))


def _are_edges_nearby(test_edge, actual_edge, threshold):
	return _edge_point_distance(actual_edge, test_edge[0]) <= threshold and _edge_point_distance(actual_edge, test_edge[1]) <= threshold


def _is_point_on_edge(e, b):
	c = closest_point_on_circle(e[0], e[1], b)
	pop = position_on_path(e[0], e[1], c)
	if pop == PositionOnPath.OnPath:
		return True
	return False


def _projectable_points(e1, e2):
	if _are_edges_nearby(e1,e2,15):
		b1 = _is_point_on_edge(e2, e1[0])
		b2 = _is_point_on_edge(e2, e1[1])
	else:
		b1=b2=False

	def fn():
		if b1:
			yield e1[0]
		if b2:
			yield e1[1]

	return set(fn())


def _merge_edges(graph, test_edge, actual_edge, attrdict):
	raise NotImplementedError


def _partition(a, pred):
	ain = []
	aout = []
	for x in a:
		if pred(x):
			ain.append(x)
		else:
			aout.append(x)
	return (ain, aout)
