import geopandas
from shapely.geometry import Polygon

countries = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres')).to_crs("EPSG:3035")
sweden = countries[countries['name'] == "Sweden"]

counties = geopandas.read_file('../../../alla_lan/alla_lan.shp').to_crs("EPSG:3035")
gothenburg = counties[counties['ID'] == "14"]
stockholm = counties[(counties['ID'] == "01") | (counties['ID'] == '04') | (counties['ID'] == '03')]

gbgcity = geopandas.GeoSeries([
    Polygon([(4425000, 3830000), (4425000, 3865000), (4460000, 3865000), (4460000, 3830000)])
],  crs=gothenburg.crs)
