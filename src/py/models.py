import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
from math import pi, cos, sin
import mscthesis
import validation


class PreferentialReturn:
    """
    :param p:
    Required.
    Parameter p in pS^(-gamma)

    :param gamma:
    Required.
    Parameter gamma in pS^(-gamma)

    :param region_sampling:
    How regions should be sampled when returning.
    Defaults to the true probability of visiting a region.

    :param jump_size_sampling:
    How jump sizes should be sampled when exploring.
    Defaults to the true distribution observed from tweets.
    """

    def __init__(self, p=None, gamma=None, region_sampling=None, jump_size_sampling=None):
        if p is None:
            raise Exception('p must be set')
        self.p = p

        if gamma is None:
            raise Exception('gamma must be set')
        self.gamma = gamma

        self.regions = None
        self.exploration_prob = None

        if region_sampling is None:
            region_sampling = RegionTrueProb()
        self.region_sampling = region_sampling

        if jump_size_sampling is None:
            jump_size_sampling = JumpSizeTrueProb()
        self.jump_size_sampling = jump_size_sampling

    def describe(self):
        return {
            "p": self.p,
            "gamma": self.gamma,
            "region_sampling": self.region_sampling.describe(),
            "jump_size_sampling": self.jump_size_sampling.describe(),
        }

    def fit(self, tweets):
        self.region_sampling.fit(tweets)
        self.jump_size_sampling.fit(tweets)

        self.regions = tweets.groupby('region').head(1).set_index('region')

        S = self.regions.shape[0]
        self.exploration_prob = self.p * (S ** -self.gamma)

    def next(self, prev):
        """
        Draws the next visit, either by exploration or return.
        The model must be `fit` before this can be called.

        :param prev:
        Previous return from this function.

        :return:
        For exploration a list ["point", latitude, longitude, -1]
        For return a list ["region", latitude, longitude, region]
        """
        r = np.random.uniform(0, 1)
        if r < self.exploration_prob:
            prev_lat, prev_lng = prev[1], prev[2]
            jump_size_m = self.jump_size_sampling.sample()
            direction_rad = np.random.uniform(0, pi)
            lat, lng = latlngshift(prev_lat, prev_lng, jump_size_m, direction_rad)
            return ["point", lat, lng, -1]
        else:
            previous_region_idx = None
            if prev[0] == 'region':
                previous_region_idx = prev[3]
            region_idx = self.region_sampling.sample(previous_region_idx=previous_region_idx)
            region = self.regions.loc[region_idx]
            return ["region", region.latitude, region.longitude, region_idx]


def latlngshift(lat, lng, delta_m, direction_rad):
    """
    Shifts the latitude and longitude by `delta_m` meters in `direction_rad`.
    This is not 100% accurate, but close.
    """
    dlat = sin(direction_rad) * delta_m
    dlng = cos(direction_rad) * delta_m
    r_earth_m = 6371000.0
    newlat = lat + (dlat / r_earth_m) * (180 / pi)
    newlng = lng + (dlng / r_earth_m) * (180 / pi) / cos(lat * pi / 180)
    return newlat, newlng


class RegionTrueProb:
    """
    A region probability sampler that follows the true distribution of observed regions.
    """

    def __init__(self):
        self.region_probs = None

    def describe(self):
        return {
            "name": "trueProb",
        }

    def fit(self, tweets):
        visits = tweets.groupby('region').size().sort_values(ascending=False)
        self.region_probs = visits / visits.sum()

    def sample(self, previous_region_idx=None):
        return np.random.choice(
            a=self.region_probs.index,
            p=self.region_probs.values,
            size=1,
        )[0]


class RegionZipfProb:
    """
    A region probability sampler that preserves the "rank" of observed regions, but
    with probabilities sampled from a zipfian distribution.

    :param s
    Parameter S of the Zipf distribution
    """

    def __init__(self, s=1.2):
        self.s = s
        self.region_probs = None

    def describe(self):
        return {
            "name": "zipf",
            "s": self.s
        }

    def fit(self, tweets):
        visits = tweets.groupby('region').size().sort_values(ascending=False)
        probs = np.power(np.arange(1, visits.shape[0] + 1), -self.s)
        self.region_probs = pd.Series(probs / np.sum(probs), index=visits.index)

    def sample(self, previous_region_idx=None):
        return np.random.choice(
            a=self.region_probs.index,
            p=self.region_probs.values,
            size=1,
        )[0]


class GroupRegionZipfProb:
    """
    A region probability sampler that preserves the "rank" of observed regions, but
    with probabilities sampled from a zipfian distribution.

    :param s
    Parameter S of the Zipf distribution
    """

    def __init__(self, s=1.2):
        self.s = s
        self.region_probs = None

    def describe(self):
        return {
            "name": "zipf",
            "s": self.s
        }

    def fit(self, tweets):
        visits = tweets.groupby('region').size().sort_values(ascending=False)
        probs = np.power(np.arange(1, visits.shape[0] + 1), -self.s)
        self.region_probs = pd.Series(probs / np.sum(probs), index=visits.index)

    def sample(self, previous_region_idx=None):
        return np.random.choice(
            a=self.region_probs.index,
            p=self.region_probs.values,
            size=1,
        )[0]


class RegionTransitionZipf:
    """
    A region probability sampler that scales the observed probability of regions with
    the distance between regions.
    """

    def __init__(self, zipfs=1.2, beta=0.03):
        self.zipfs = zipfs
        self.beta = beta

        self.distances = None
        self.seed = None
        # When previous visit was to a region transition is used
        self.transition_mx = None
        # When previous visit was to a random point global prob is used
        self.region_probabilities = None

    def describe(self):
        return {
            "name": "transitionZipf",
            "zipfs": self.zipfs,
            "beta": self.beta,
        }

    def fit(self, tweets):
        reggrp = tweets.groupby('region')
        regions = reggrp.head(1).set_index('region').sort_index()

        distances_km = pd.DataFrame(
            (6371.0088 * haversine_distances(
                np.radians(regions[['latitude', 'longitude']]),
            )),
            index=regions.index,
            columns=regions.index,
        )
        self.distances = distances_km.stack()
        seed = np.exp(-self.beta * distances_km)
        seed = seed / seed.sum()
        self.seed = seed

        region_counts = reggrp.size().sort_values(ascending=False)
        region_probs = np.power(
            np.arange(1, region_counts.shape[0] + 1),
            -self.zipfs,
        )
        region_probs = pd.Series(
            region_probs / np.sum(region_probs),
            index=region_counts.index,
        ).sort_index()
        self.region_probabilities = region_probs
        fitted = validation.ipf(seed.values, region_probs.values, region_probs.values, max_iter=10)
        transition_mx = pd.DataFrame(
            fitted,
            index=regions.index,
            columns=regions.index,
        )
        # Normalize row (each row should sum to 1)
        transition_mx = transition_mx.div(
            transition_mx.sum(axis=1),  # summation of each row
            axis=0,
        )
        self.transition_mx = transition_mx.stack()

    def sample(self, previous_region_idx=None):
        if previous_region_idx is None:
            probs = self.region_probabilities
            print(probs)
        else:
            probs = self.transition_mx.loc[previous_region_idx]
        return np.random.choice(
            a=probs.index,
            p=probs.values,
            size=1,
        )[0]


class JumpSizeTrueProb:
    """
    A jump size probability sampler that follows the true distribution of observed jump sizes.
    """

    def __init__(self):
        self.jump_sizes_km = None

    def describe(self):
        return {
            "name": "trueProb",
        }

    def fit(self, tweets):
        gaps = mscthesis.gaps(tweets)
        # Don't use tweets in same region for jump size distribution as they will all be 0.
        gaps = gaps[gaps['region_origin'] != gaps['region_destination']]
        lines = gaps[[
            'latitude_origin', 'longitude_origin',
            'latitude_destination', 'longitude_destination',
        ]].values
        self.jump_sizes_km = [6371.0088 * haversine_distances(
            X=np.radians([_[:2]]),
            Y=np.radians([_[2:]]),
        )[0, 0] for _ in lines]

    def sample(self):
        km = np.random.choice(self.jump_sizes_km)
        # should return in meters
        return km * 1000


class Sampler:
    """
    Sampler is a convenience wrapper for sampling new trajectories for a group of users.

    :param model:
    The initialized preferential return model.

    :param daily_trips_sampling:
    How many trips should be sampled every day.
    """

    def __init__(self, model=None, daily_trips_sampling=None, n_days=1, geotweets_path=None):
        if model is None:
            raise Exception("model must be set")
        self.model = model

        if daily_trips_sampling is None:
            daily_trips_sampling = StaticDistribution(4)
        self.daily_trips_sampling = daily_trips_sampling

        if geotweets_path is None:
            raise Exception("geotweets_path must be set")
        self.geotweets_path = geotweets_path

        self.n_days = n_days

        # variable for caching the output
        self._visits = None

    def describe(self):
        return {
            "model": self.model.describe(),
            "daily_trips_sampling": self.daily_trips_sampling.describe(),
            "n_days": self.n_days,
            "geotweets_path": self.geotweets_path
        }

    def sample(self, tweets=None):
        """
        Samples new tweets for each user in `tweets` for `n_days`.

        :param tweets:
        pd.DataFrame (userid*, region, label, latitude, longitude, ...rest))

        :param n_days:
        How many days should be sampled.

        :return:
        The sampled tweets for each users
        pd.DataFrame (*userid, day, timeslot, kind, latitude, longitude, region)
        """
        if tweets is None:
            raise Exception("must set tweets when sampling")

        samples = []
        n_done = 0
        for uid in tweets.index.unique():
            utweets = tweets.loc[uid]
            # Re-fit the model on this user
            self.model.fit(utweets)

            # Find home location
            home = utweets[utweets['label'] == 'home'].iloc[0]

            for day in range(self.n_days):
                # Every days starts at home location
                prev = ['region', home.latitude, home.longitude, home.region]
                samples.append([uid, day, 0] + prev)

                for timeslot in range(self.daily_trips_sampling.sample()):
                    current = self.model.next(prev)
                    samples.append([uid, day, (timeslot+1)] + current)
                    if current[0] == 'point':
                        break
                    prev = current

            n_done += 1
            if n_done % 250 == 0:
                print("done with", n_done)

        return pd.DataFrame(
            samples,
            columns=['userid', 'day', 'timeslot', 'kind', 'latitude', 'longitude', 'region'],
        ).set_index('userid')

    def visits(self):
        if self._visits is None:
            geotweets = mscthesis.read_geotweets_raw(self.geotweets_path).set_index('userid')

            # this code should be somewhere else...
            geotweets = geotweets[(geotweets['weekday'] < 6) & (0 < geotweets['weekday'])]
            home_visits = geotweets.query("label == 'home'").groupby('userid').size()
            geotweets = geotweets.loc[home_visits.index]
            tweetcount = geotweets.groupby('userid').size()
            geotweets = geotweets.drop(labels=tweetcount[tweetcount < 20].index)
            regioncount = geotweets.groupby(['userid', 'region']).size().groupby('userid').size()
            geotweets = geotweets.drop(labels=regioncount[regioncount < 2].index)
            # Ensure the tweets are sorted chronologically
            geotweets = geotweets.sort_values(by=['userid', 'createdat'])

            self._visits = self.sample(
                geotweets,
            )

        return self._visits


class StaticDistribution:
    def __init__(self, n):
        self.n = n

    def describe(self):
        return {
            "name": "static",
            "n": self.n,
        }

    def sample(self):
        return self.n


class NormalDistribution:
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def describe(self):
        return {
            "name": "normal",
            "mean": self.mean,
            "std": self.std,
        }

    def sample(self):
        return max(1, int(round(np.random.normal(self.mean, self.std))))


class VisitsFromFile:
    def __init__(self, file_path=None):
        if file_path is None:
            raise Exception("file_path must be set")
        self.file_path = file_path

    def describe(self):
        return {
            "type": "from_file",
            "path": self.file_path,
        }

    def visits(self):
        return pd.read_csv(self.file_path).set_index('userid')


class VisitsFromGeotweetsFile:
    def __init__(self, file_path=None):
        if file_path is None:
            raise Exception("file_path must be set")
        self.file_path = file_path

        # cache variable
        self._visits = None

    def describe(self):
        return {
            "type": "from_geotweets_file",
            "path": self.file_path,
        }

    def visits(self):
        if self._visits is None:
            v = mscthesis.read_geotweets_raw(self.file_path).set_index('userid')
            v = v[(v['weekday'] < 6) & (0 < v['weekday'])]
            v = geotweets_to_visits(v)
            self._visits = v
        return self._visits


def geotweets_to_visits(geotweets):
    first_day = geotweets['createdat'].min()
    v = geotweets.assign(
        kind='region',
        day=(geotweets['createdat'] - first_day).dt.days,
    ).rename(columns={
        "hourofday": "timeslot"
    })[[
        'region',
        'latitude',
        'longitude',
        'day',
        'timeslot',
        'kind',
        'label',
    ]]
    return v
