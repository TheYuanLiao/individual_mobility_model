import pandas as pd
import geopandas as gpd
import validation


def config_product(visit_factories=None, home_locations_paths=None, gravity_models=None):
    if visit_factories is None:
        raise Exception("visit_factories must be set")
    if home_locations_paths is None:
        raise Exception("home_locations_paths must be set")
    if gravity_models is None:
        raise Exception("gravity_models must be set")
    cfgs = []
    for v in visit_factories:
        for hlp in home_locations_paths:
            for gm in gravity_models:
                cfgs.append(Config(v, hlp, gm))
    return cfgs


class Config:
    def __init__(self, visit_factory=None, home_locations_path=None, gravity_model=None):
        self.visit_factory = visit_factory
        self.home_locations_path = home_locations_path
        self.gravity_model = gravity_model

    def describe(self):
        return {
            "visits": self.visit_factory.describe(),
            "home_locations": self.home_locations_path,
            "gravity_model": self.gravity_model.describe()
        }


class Result:
    def __init__(self):
        self.sparse_odms = dict()
        self.seed_odms = dict()
        self.dense_odms = dict()
        self.spssim_scores = dict()
        self.distance_metrics = dict()


class Pipeline:
    """
    Pipeline will perform the model -> result execution.
    """

    def __init__(self):
        self.sampers = validation.Sampers()
        self.spssim = validation.SPSSIM()
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
            seed_odm = cfg.gravity_model.seed(
                distances=self.sampers.distances[scale],
            )
            seed_odm = self.sampers.distance_cut(scale, seed_odm)
            dense_odm = cfg.gravity_model.gravitate(
                sparse_odm=sparse_odm,
                seed=seed_odm,
            )
            dense_odm = self.sampers.distance_cut(scale, dense_odm)

            spssim_score = self.spssim.score(
                self.sampers.odm[scale],
                sparse_odm,
                self.sampers.quantile_groups[scale],
            )

            distance_metrics = self.distance_metrics.compute(
                self.sampers.quantile_groups[scale],
                [
                    sparse_odm,
                    seed_odm,
                    dense_odm,
                    self.sampers.odm[scale]
                ],
                ['model', 'gravity_seed', 'gravity', 'sampers'],
            )

            result.sparse_odms[scale] = sparse_odm
            result.seed_odms[scale] = seed_odm
            result.dense_odms[scale] = dense_odm
            result.spssim_scores[scale] = spssim_score
            result.distance_metrics[scale] = distance_metrics

        return result

