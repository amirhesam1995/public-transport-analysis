[![DOI](https://zenodo.org/badge/104480172.svg)](https://zenodo.org/badge/latestdoi/104480172)
# public-transport-analysis
Urban Public transport analysis (POLITO-TSP).
This repository contains a jupyter notebook and all the related libraries to perform some of the analysis shown  in the <a href="http://citychrone.org" target="_blank">CityChrone platform</a> and compute the data nedeed to add new city in the CityChrone platform.

Take a look at the <a href="http://nbviewer.jupyter.org/github/ocadni/public-transport-analysis/blob/master/public-transport-city.ipynb" target="_blank">demo</a> of the notebook for the city of Budapest.

![budapest image](./budapest.png)

## Prerequisites
1. [python 3.x](https://www.python.org/download/releases/3.0/)
1. [jupyter](http://jupyter.org/)
1. [MongoDB](https://www.mongodb.com/download-center#community) with the privileges to create and modified a database.
1. Docker
1. All the python library needed, listed at the beginning of the notebook.


## Installation
1. Clone this repository.
2. Go to `public-transport-analysis/osrm` and run the commands annotated in `Docker-instructions.txt` 

You will see `running and waiting for requests` message, which means that OSRM server is ready

3. Install Mongo DB `sudo apt-get install mongodb`
4. Install `pip install IPython`


### Optional
For computing the "Sociality Score" the population distribution in the city is nedeed. The population distribution can be download for instance from [SEDAC](https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-density-rev11/data-download) or for Europe form [EUROSTAT](https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/population-distribution-demography/geostat). The public-transport-analysis notebook automatically project the population in a specific tesselletion to the hexagons tesselletions used. The population in each hexagons will be the sum of the population of the overlapping sections proportional to overlapping area.
The population must be stored in a mongodb collections, where each element is a Future of [geojson](https://docs.mongodb.com/manual/reference/geojson/) and in the field "geometry" there should be the a Polygon geometry of the corresponding section. Then the value of the population must be stored in the sub-field of the "properties" field of the element.

## First run for Budapest

1. Open file `public-transport-city.py` and install the libraries that are imported at the beginning (use python3!)
     ATTENTION: You need to use specific versions of the following libraries:

		a.	pymongo   V 3.12.1

		b.	pandas    V 1.5.3

		c.	folium    V 0.14.0 

		d.	numpy     V 1.24.3 

		e.	requests  V 2.29.0

		f.	numba     V 0.57.0

		h.	geopy     V 2.4.1

		i.	shapely   V 1.8.0

		j.	datetime  V 5.4

2. Adjust the date indicated in the line `day = ...` so that it corresponds to a date that is contained in the GTFS file.

3. Ensure that the reference system of the population file is in `EPSG:4326`. If your population files are in another reference system, you should first convert them, using some external tools (e.g., qGIS).

4. To compute the accessibility scores, run `python3 public-transport-city.py`. Inside that script there is a variable `first_run`. By default it is True, which implies the mongo db is modified (adding links, connections, nodes, etc.). However, if you have already filled the databse, e.g., you are running the script for a second time, you do not need to fill the database again: in this case, set ``first_run=False` before running the script.

5. Results are written in the mongo-db, in the table `points`, where fields concerning sociality and velocity score are added

6. Use `public-transport-city.ipnb` to visualize the accessibility map, by skipping the section "COMPUTATION OF ACCESSIBILITY" (you should run all the code before "COMPUTATION OF ACCESSIBILITY" and then the code starting from "RESULTS")
    
## Compute travel time distances and all the accessbility quantities
1. run ```jupyter-notebook``` and open the public-transport-analysis notebook.
1. Set the variable listed at the start of the notebook:
	1. ```city = 'Budapest' # name of the city```
	2. ```urlMongoDb = "mongodb://localhost:27017/"; # url of the mongodb database```
	3. ```directoryGTFS = './gtfs/'+ city+ '/' # directory of the gtfs files.```
	4. ```day = "20170607" #hhhhmmdd [date validity of gtfs files]```
	5. ```dayName = "wednesday" #name of the corresponding day```
	6. ```urlServerOsrm = 'http://localhost:5000/'; #url of the osrm server of the city```
    \[\Optional -- population collection]
    7. ```urlMongoDbPop = "mongodb://localhost:27017/"; # url of the mongodb database of population data```
    8. ```popDbName = "" #name of the population database```
    9. ```popCollectionName = ""#name of the population collection```
    10. ```popField = ""#the field in the properties field in the elements containing the value of the population```
1. run the cells in the notebook.




