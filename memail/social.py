
import numpy as np
import random
import math
import disp_interface as di
from sklearn.cluster import KMeans
class _data_:
    def __init__(self, vec, cluster = 0, fix = False):
        self.vec = vec
        self.cluster = cluster
        self.fix = fix

class _center_:
    def __init__(self, id, d, vec = []):
        if len(vec):
            self.vec = vec
        else:
            self.vec = [random.random() for i in range(d)]
            norm = 0
            for i in range(d):
                norm = norm + abs(self.vec[i])
            for i in range(d):
                self.vec[i] = self.vec[i]/float(d)
        self.id = id
        self.d = d




#def k_clustering(num_cluster, datas):

def _norm(vec):
    l = len(vec)
    val = 0
    for i in range(l):
        val = val + abs(vec[i])
    return val

def _renormalize(vec):
    l = len(vec)
    vec1 = [0 for i in range(l)]
    norm = _norm(vec)
    for i in range(l):
        vec1[i] = vec[i]/norm
    return vec1

def _dist(center, data):
    l = min(len(center.vec), len(data.vec))
    val = 0
    for i in range(l):
        val = val + abs(center.vec[i] - data.vec[i])*abs(center.vec[i] - data.vec[i])
    return math.sqrt(val)

def get_center(inode_set):
    _len = len(inode_set)
    if _len == 0:
        return
    dim = len(inode_set[0].vec)
    vec = [0 for i in range(dim)]
    for inode in inode_set:
        for i in range(dim):
            vec[i] = vec[i] + inode.vec[i]/float(_len)

def k_mean(datas, centers):
    reshape_data = []
    for data in datas:
        reshape_data.append(data.vec)
    kmean = KMeans(n_clusters = len(centers), init='k-means++', n_init=10, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=0, random_state=None, copy_x=True, n_jobs=1)
    kmean.fit(np.array(reshape_data))
    for i in range(len(centers)):
        centers[i].vec = kmean.cluster_centers_[i]

def update_cluster(datas, centers):
    dict_assign = {}
    for data in datas:
        dist = 1000000
        assign = centers[0]
        for center in centers:
            if _dist(center, data) < dist:
                dist = _dist(center, data)
                #print dist
                assign = center
        data.cluster = assign.id
        try:
            dict_assign[assign].append(data.vec)
        except:
            dict_assign[assign] = [data.vec]



    for center in centers:
        try:
            data_center = dict_assign[center]
        except:
            data_center = []
        if len(data_center) > 0:
            dim = len(data_center[0])
            vec = [0 for i in range(dim)]
            for data in data_center:
                for i in range(dim):
                    vec[i] = vec[i] + data[i]/float(len(data_center))
            center.vec = vec


#the social clustering: takes a bounch of inodes for eamils and generate the social clustering result.
def social_clustering(inode_set, iter = 50, num_cluster = 10):
    social_dict = {}
    clusters = []
    datas = []
    for inode in inode_set:
        if inode.type == "email":
            try:
                social_dict[inode.email['sender']].append(inode)
            except:
                social_dict[inode.email['sender']] = [inode]
    
    #average:
    dim = 0
    senders = []
    for key, value in social_dict.iteritems():
        dim = len(value[0].vec)
        val = [0 for i in range(dim)]
        for element in value:
            for i in range(dim):
                val[i] = val[i] + element.vec[i]
        val = _renormalize(val)
        #social_dict[key] = val
        datas.append(_data_(vec = val))
        senders.append(key)


    for i in range(num_cluster):
        center = _center_(id = i, d = dim)
        clusters.append(center)
    
    
#for i in range(iter):
        #print "social training... iteration: " + str(i)
#update_cluster(datas, clusters)
    k_mean(datas, clusters)
            #for data in datas:

    dist_matrix = [[0  for center in clusters] for inode in inode_set]
    for i in range(len(inode_set)):
        for j in range(num_cluster):
            #print i, j
            dist_matrix[i][j] = -_dist(clusters[j], inode_set[i])

    exs = np.array(dist_matrix)

    #compute description
    cluster_matrix = [[0  for center in clusters] for sender in senders]
    for i in range(len(senders)):
        for j in range(num_cluster):
            cluster_matrix[i][j] = _dist(clusters[j], datas[i])

    sxs = np.array(cluster_matrix)
    txs = di.assign_topic(sxs, 15)
    descriptions = []
    for i in range(num_cluster):
        des_temp = ""
        for id in txs[i]:
            des_temp = des_temp + str(senders[id]) + "\n"
        descriptions.append(des_temp)


    return exs, descriptions



