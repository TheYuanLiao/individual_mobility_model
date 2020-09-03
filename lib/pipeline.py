import pandas as pd
import geopandas as gpd
import validation


def config_product(visit_factories=None, home_locations_paths=None):
    if visit_factories is None:
        raise Exception("visit_factories must be set")
    if home_locations_paths is None:
        raise Exception("home_locations_paths must be set")
    cfgs = []
    for v in visit_factories:
        for hlp in home_locations_paths:
            cfgs.append(Config(v, hlp))
    return cfgs


class Config:
    def __init__(self, visit_factory=None, home_locations_path=None):
        self.visit_factory = visit_factory
        self.home_locations_path = home_locations_path

    def describe(self):
        return {
            "visits": self.visit_factory.describe(),
            "home_locations": self.home_locations_path
        }


class Result:
    def __init__(self):
        self.sparse_odms = dict()
        self.distance_metrics = dict()
        self.divergence_measure = dict()


class Pipeline:
    """
    Pipeline will perform the model -> result execution.
    """

    def __init__(self):
        self.sampers = validation.Sampers()
        self.distance_metrics = validation.DistanceMetrics()
        self.visits = None

    def prepare(self):
        self.sampers.prepare()

    def run(self, cfg):
        print("reading home_locations")
        home_locations = pd.read_csv(cfg.home_locations_path).set_index('userid')
        home_locations = gpd.GeoDataFrame(
            home_locations,
            crs="EPSG:4326",
            geometry=gpd.points_from_xy(home_locations.longitude, home_locations.latitude),
        ).to_crs("EPSG:3006")
        visits = cfg.visit_factory.visits()
        self.visits = visits
        converted_visits = self.sampers.convert(visits)
        result = Result()
        for scale in validation.scales:
            print("scoring on", scale, "scale...")
            print("aligning visits...")
            sparse_odm = self.sampers.align(
                scale=scale,
                home_locations=home_locations,
                visits=converted_visits,
            )
            sparse_odm = self.sampers.distance_cut(scale, sparse_odm)
            distance_metrics = self.distance_metrics.compute(
                self.sampers.quantile_groups[scale],
                [
                    sparse_odm,
                    self.sampers.odm[scale]
                ],
                ['model', 'sampers'],
            )
            divergence_measure = self.distance_metrics.kullback_leibler(distance_metrics, ['model', 'sampers'])
            result.sparse_odms[scale] = sparse_odm
            result.distance_metrics[scale] = distance_metrics
            result.divergence_measure[scale] = divergence_measure

        return result

