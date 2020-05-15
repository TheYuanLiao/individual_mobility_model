import geopandas as gpd
import pandas as pd

metric_epsg = "EPSG:8058"


def validation_zones():
    zones = gpd.read_file('./../../dbs/australia/zones/zones.shp')
    zones = zones.rename(columns={"SA3_CODE16": "zone"})
    zones.zone = zones.zone.astype(int)

    # filter zones that are not part of travel survey
    hts = validation_travel_survey()
    zone_ids = hts.zone.unique()
    zones = zones[zones.zone.isin(zone_ids)]
    zones = zones.to_crs(metric_epsg)
    return zones


def zone_populations():
    pop = pd.read_excel("./../../dbs/australia/data_by_sa3.xlsx", sheet_name=1).rename(columns={"SA3_ID": "zone", "WEIGHTED_POPULATION": "census_population"})
    pop = pop[pop['WAVE'] == '2018/19']
    pop_sa3 = pop.set_index('zone').census_population
    return validation_zones().set_index('zone').join(pop_sa3)


def validation_boundary():
    return validation_zones().assign(a=1).dissolve(by='a').simplify(tolerance=0.2).to_crs("EPSG:4326")


def validation_travel_survey():
    hts = pd.read_excel("./../../dbs/australia/hts/hts.xlsx", sheet_name=2)
    hts = hts.rename(columns={"SA3_ID": "zone"})
    return hts
