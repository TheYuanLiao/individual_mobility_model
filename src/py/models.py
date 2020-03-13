import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
from math import pi, cos, sin
import mscthesis


class SongModel:
    def __init__(self, p=None, gamma=None, zipf=None):
        if p is None:
            raise Exception('p must be set')
        if gamma is None:
            raise Exception('gamma must be set')
        if zipf is None:
            raise Exception('zipf must be set')
        self.p = p
        self.gamma = gamma
        self.zipf = zipf
        self.location_probs = None
        self.exploration_prob = None
        self.tweets = None
        self.regions = None
        self.jump_sizes_km = None

    def fit(self, tweets):
        self.tweets = tweets
        self._fit_exploration_prob()
        self._fit_regions()
        self._fit_jumps()

    def _fit_exploration_prob(self):
        if self.exploration_prob is None:
            observed_locations = self._fit_location_prob()
            self.exploration_prob = self.p * (observed_locations.shape[0] ** (-self.gamma))
        return self.exploration_prob

    def _fit_location_prob(self):
        if self.location_probs is None:
            visits = self.tweets.groupby('region').size().sort_values(ascending=False)
            probs = np.power(np.arange(1, visits.shape[0] + 1), self.zipf)
            probs = probs / np.sum(probs)
            self.location_probs = pd.Series(probs, index=visits.index)
        return self.location_probs

    def _fit_regions(self):
        if self.regions is None:
            self.regions = self.tweets.groupby('region').head(1).set_index('region')
        return self.regions

    def _fit_jumps(self):
        if self.jump_sizes_km is None:
            g = mscthesis.gaps(self.tweets)
            lines = g[['latitude_origin', 'longitude_origin', 'latitude_destination', 'longitude_destination']].values
            self.jump_sizes_km = [6371.0088 * haversine_distances(
                X=np.radians([_[:2]]),
                Y=np.radians([_[2:]]),
            )[0, 0] for _ in lines]

    def sample(self, prev_sample):
        r = np.random.uniform(0, 1)
        prev_lat, prev_lng = None, None
        if prev_sample[0] == 'region':
            prev_lat, prev_lng = prev_sample[2], prev_sample[3]
        else:
            prev_lat, prev_lng = prev_sample[1], prev_sample[2]
        if r < self.exploration_prob:
            return self._sample_exploration(prev_lat, prev_lng)
        else:
            return self._sample_return()

    def _sample_exploration(self, prev_lat, prev_lng):
        jump_size_m = np.random.choice(self.jump_sizes_km) * 1000
        direction_rad = np.random.uniform(0, pi)
        lat, lng = latlngshift(prev_lat, prev_lng, jump_size_m, direction_rad)
        return "point", lat, lng

    def _sample_return(self):
        region_idx = np.random.choice(self.location_probs.index, 1, p=self.location_probs.values)[0]
        region = self.regions.loc[region_idx]
        return "region", region_idx, region.latitude, region.longitude


def latlngshift(lat, lng, delta_m, direction_rad):
    dlat = sin(direction_rad) * delta_m
    dlng = cos(direction_rad) * delta_m
    r_earth_m = 6371000.0
    newlat = lat + (dlat / r_earth_m) * (180 / pi)
    newlng = lng + (dlng / r_earth_m) * (180 / pi) / cos(lat * pi / 180)
    return newlat, newlng
