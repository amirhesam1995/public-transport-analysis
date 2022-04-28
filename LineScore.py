import sys
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, './library/')
import zipfile
import os
import time
import pymongo as pym
import pandas as pd
import folium
import numpy as np
import requests
import numba
from shapely.geometry import Polygon, LineString, asShape, mapping, Point
import math
import geopy
from shapely.geometry import Polygon, MultiPolygon, Point, mapping
from geopy.distance import geodesic, great_circle
from folium.plugins import FastMarkerCluster
from datetime import datetime
from geopy.distance import geodesic, great_circle

from libAccessibility import arrayTimeCompute, ListFunctionAccessibility
from libHex import area_geojson
from scipy.sparse import coo_matrix
import math
import time
import numpy

inf = 10000000

from numba import jit, int32, int64

city = 'Budapest'  # name of the city
urlMongoDb = "mongodb://localhost:27017/";  # url of the mongodb database

client = pym.MongoClient(urlMongoDb)
gtfsDB = client['PublicTransportAnalysisBudapest']


def setPosField2(gtfsDB, city):
    pos = 0
    for route in gtfsDB['routes'].find({'city': city}).sort([('_id', pym.ASCENDING)]):
        gtfsDB['routes'].update_one({'_id': route['_id']},
                                    {'$set':
                                        {
                                            'pos': pos
                                        }
                                    })
        pos += 1
        print('{0}'.format(pos), end="\r")
    gtfsDB['routes'].create_index([("pos", pym.ASCENDING)])


setPosField2(gtfsDB, city)

from tqdm import tqdm

for j in tqdm(gtfsDB["routes"].find({'city': city}).sort([('_id', pym.ASCENDING)])):
    gtfsDB['connections'].update_many({'route_id': j['route_id']},
                                      {'$set':
                                          {
                                              'pos': j['pos'],
                                          }
                                      });
    # print('{0}'.format(j["pos"]), end="\r")
    gtfsDB['connections'].create_index([("pos", pym.ASCENDING)])

stoppss = gtfsDB['stops']

from tqdm import tqdm

toal = gtfsDB['connections'].find({}).count()
for k in tqdm(gtfsDB['connections'].find({'city': city}).sort([('_id', pym.ASCENDING)]), total=toal):
    timeStart0 = time.time()
    gtfsDB['connections'].update_one({'_id': k['_id']},
                                     {'$set':
                                         {
                                             'distance': round(geodesic((stoppss.find_one({'pos': k["pStart"]})[
                                                                             'point']["coordinates"][1],
                                                                         stoppss.find_one({'pos': k["pStart"]})[
                                                                             'point']["coordinates"][0]),
                                                                        (stoppss.find_one({'pos': k["pEnd"]})[
                                                                             'point']["coordinates"][1],
                                                                         stoppss.find_one({'pos': k["pEnd"]})[
                                                                             'point']["coordinates"][0])).meters)
                                         }
                                     }
                                     )

    gtfsDB['connections'].create_index([("distance", pym.ASCENDING)])

timeList = [8]  # [7,10,13,16,19,22] # List of starting time for computing the isochrones
# timeList = [7,10,13,16,19,22] # List of starting time for computing the isochrones
hStart = timeList[0] * 3600
lenroute = gtfsDB['routes'].find().count()


def makeArrayConnections2(gtfsDB, hStart, city):
    print("start making connections array")
    fields = {'tStart': 1, 'tEnd': 1, 'pStart': 1, 'pEnd': 1, '_id': 0}
    typeMatch = {'city': city, 'tStart': {'$gte': hStart},
                 'tStart': {"$type": "number"}, 'tEnd': {"$type": "number"},
                 'pStart': {"$type": "number"}, 'pEnd': {"$type": "number"}, }
    pipeline = [
        {'$match': {'city': city, 'tStart': {'$gte': hStart}}},
        {'$sort': {'tStart': 1}},
        {'$project': {'_id': "$_id", "c": ['$tStart', '$tEnd', '$pStart', '$pEnd', '$pos', '$distance']}},
    ]
    allCC = list(gtfsDB['connections'].aggregate(pipeline))
    print("done recover all cc", len(allCC))
    allCC = np.array([x["c"] for x in allCC])
    print("cenverted")
    # arrayCC = np.full((gtfsDB['connections'].find({"city":city,'tStart':{'$gte':hStart}}).count(),4),1.,dtype = np.int)
    # countC = 0
    # tot = gtfsDB['connections'].find({'tStart':{'$gte':hStart},'city':city}).count()

    print('Num of connection', len(allCC))
    return allCC


arrayCC = makeArrayConnections2(gtfsDB, hStart, city)

# ### List of list of the points and stops neighbors

# In[ ]:


from libStopsPoints import listPointsStopsN

arraySP = listPointsStopsN(gtfsDB, city)


@jit((int32[:], int32[:], int32, int64[:, :], int32[:, :], int32[:, :], int32[:, :], int32[:, :], int32),
     nopython=True)
def coreICSA2(timesValues, timeP, timeStart, arrayCC, S2SPos, S2STime, P2SPos, P2STime, lenroute):
    # print 'inter'
    # global arrayCC
    # arrayCC = CC
    # global S2SPos
    # global S2STime
    count = 0
    pointRoute = [0.] * lenroute

    routee = []
    timesValuesN = numpy.copy(timesValues)
    for c_i in range(len(arrayCC)):
        c = arrayCC[c_i]
        Pstart_i = c[2]
        if timesValues[Pstart_i] <= c[0] or timesValuesN[Pstart_i] <= c[0]:
            count += 1
            Parr_i = c[3]
            if timesValues[Parr_i] > c[1]:
                timesValues[Parr_i] = c[1]
                if c[1] <= timeStart + 3600:
                    # if distn[Parr_i] == 1:
                    routee.append((Pstart_i, Parr_i, c[4], c[5]))
                for neigh_i in range(len(S2SPos[Parr_i])):
                    if S2SPos[Parr_i][neigh_i] != -2:
                        neigh = S2SPos[Parr_i][neigh_i]
                        neighTime = timesValuesN[neigh]
                        if neighTime > c[1] + S2STime[Parr_i][neigh_i]:
                            timesValuesN[neigh] = c[1] + S2STime[Parr_i][neigh_i]
                    else:
                        break

    for i, t in enumerate(timesValues):
        if t > timesValuesN[i]:
            timesValues[i] = timesValuesN[i]

    for (org, des, lin, dis) in routee:
        pointRoute[lin] += dis

    return pointRoute


def coumputeTimeOnePoint(point, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime, P2SPos, P2STime, S2SPos,
                         S2STime, lenroute):
    timeS.fill(inf)  # Inizialize the time of stop
    timeP.fill(inf)
    posPoint = point['pos']  # position of the point in the arrays
    timeP[posPoint] = startTime  # initialize the starting time of the point

    for neigh_i, neigh in enumerate(
            P2PPos[posPoint][P2PPos[posPoint] != -2]):  # loop in the point near to the selected point
        neigh = neigh
        timeP[neigh] = P2PTime[posPoint][neigh_i] + startTime  # initialize to startingTime + WalkingTime all near point

    # loop in the stops near to the selected point
    for neigh_i, neigh in enumerate(P2SPos[posPoint][P2SPos[posPoint] != -2]):
        neigh = neigh
        timeS[neigh] = P2STime[posPoint][neigh_i] + startTime  # initialize to startingTime + WalkingTime all near stops

    # timeSInit = timeS.copy()
    startTime = numpy.int32(startTime)
    arrayCC = arrayCC.astype(numpy.int64)

    routeee = coreICSA2(timeS, timeP, startTime, arrayCC, S2SPos, S2STime, P2SPos, P2STime, lenroute)

    return routeee


def computeAccessibilities(city, startTime, arrayCC, arraySP, gtfsDB, lenroute):
    timeS = arraySP['timeS']
    timeP = arraySP['timeP']
    S2SPos = arraySP['S2SPos']
    S2STime = arraySP['S2STime']
    P2PPos = arraySP['P2PPos']
    P2PTime = arraySP['P2PTime']
    P2SPos = arraySP['P2SPos']
    P2STime = arraySP['P2STime']

    maxVel = 0
    totTime = 0.
    avgT = 0
    tot = len(timeP)

    count = 0

    for point in gtfsDB['points'].find({'city': city}, {'pointN': 0, 'stopN': 0}, no_cursor_timeout=True).sort(
            [('pos', 1)]):

        timeStart0 = time.time()

        # Inizialize the time of stop and point
        # print("starting computation")
        routee = coumputeTimeOnePoint(point, startTime, timeS, timeP, arrayCC, P2PPos, P2PTime,
                                      P2SPos,
                                      P2STime, S2SPos, S2STime, lenroute)

        a_list = list(routee)

        score = {}
        for i, m in enumerate(a_list):
            score[i] = m

        score = {str(k): round(float(v), 2) for k, v in score.items()}

        totTime += time.time() - timeStart0
        avgT = float(totTime) / float(count + 1)
        h = int((tot - count) * avgT / (60 * 60))
        m = (tot - count) * avgT / (60) - h * 60

        gtfsDB['points'].update_one({'_id': point['_id']}, {'$set': {"Score": score}})
        count += 1
        print(
            'point: {0}, time to finish : {1:.1f}h, {2:.1f} m'.format(
                count, h, m),
            end="\r")


computeAccessibilities(city, hStart, arrayCC, arraySP, gtfsDB, lenroute)
