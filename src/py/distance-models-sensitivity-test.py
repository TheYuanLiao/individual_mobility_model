import sys
import subprocess
import os
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import kurtosis
from scipy import optimize
import random
from tqdm import tqdm


def get_repo_root():
    """Get the root directory of the repo."""
    dir_in_repo = os.path.dirname(os.path.abspath('__file__'))
    return subprocess.check_output('git rev-parse --show-toplevel'.split(),
                                   cwd=dir_in_repo,
                                   universal_newlines=True).rstrip()


ROOT_dir = get_repo_root()
sys.path.append(ROOT_dir)
sys.path.insert(0, ROOT_dir + '/lib')


def pdf_fit(df, df_out, func_name=None):
    def r2_cal(y, y_fit):
        # residual sum of squares
        ss_res = np.sum((y - y_fit) ** 2)

        # total sum of squares
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        # r-squared
        r2 = 1 - (ss_res / ss_tot)
        return r2
    x = df_out.loc[:, 'd'].values
    y = df_out.loc[:, 'y'].values
    P_d = np.cumsum(np.diff(x)*y[1:])
    if func_name == 'powerlaw_al':
        def powerlaw_al(d, d0, beta):
            return (d + d0)**(-beta)

        def powerlaw_alMLE(params):
            d0, beta, sd = params[0], params[1], params[2] # inputs are guesses at our parameters
            yhat = (x + d0)**(-beta)
            L = (len(x)/2 * np.log(2 * np.pi) + len(x)/2 * np.log(sd ** 2) + 1 / (2 * sd ** 2) * sum((y - yhat) ** 2))
            # return negative LL
            return L
        guess = np.array([5,5,2])
        results = optimize.minimize(powerlaw_alMLE, guess, method = 'Nelder-Mead', options={'disp': False})
        para1, para2, _ = results['x']
        aic = -2*results['fun'] + 2*3
        yhat = powerlaw_al(x, para1, para2)
        para3 = np.nan

    if func_name == 'lognormal':
        def lognormal(d, miu, sigma):
            return 1/(d*sigma*(2*np.pi)**0.5)*np.exp(-(np.log(d) - miu)**2/(2*sigma**2))

        # define likelihood function
        def lognormalMLE(params):
            miu, sigma, sd = params[0], params[1], params[2] # inputs are guesses at our parameters
            yhat = 1/(x*sigma*(2*np.pi)**0.5)*np.exp(-(np.log(x) - miu)**2/(2*sigma**2))
            L = (len(x)/2 * np.log(2 * np.pi) + len(x)/2 * np.log(sd ** 2) + 1 / (2 * sd ** 2) * sum((y - yhat) ** 2))
            # return negative LL
            return L
        guess = np.array([5,5,2])
        results = optimize.minimize(lognormalMLE, guess, method = 'Nelder-Mead', options={'disp': False})
        para1, para2, _ = results['x']
        aic = -2*results['fun'] + 2*3
        yhat = lognormal(x, para1, para2)
        para3 = np.nan

    if func_name == 'truncated_power_law':
        def truncated_power_law(d, d0, beta, K):
            return (d + d0) ** (-beta) * np.exp(-d / K)

        def truncated_power_lawMLE(params):
            d0, beta, K, sd = params[0], params[1], params[2], params[3] # inputs are guesses at our parameters
            yhat = (x + d0) ** (-beta) * np.exp(-x / K)
            L = (len(x)/2 * np.log(2 * np.pi) + len(x)/2 * np.log(sd ** 2) + 1 / (2 * sd ** 2) * sum((y - yhat) ** 2))
            # return negative LL
            return L
        guess = np.array([5,5,5,2])
        results = optimize.minimize(truncated_power_lawMLE, guess, method = 'Nelder-Mead', options={'disp': False})
        para1, para2, para3, _ = results['x']
        aic = -2*results['fun'] + 2*4
        yhat = truncated_power_law(x, para1, para2, para3)

    paras_dict = {'para1': para1, 'para2': para2, 'para3': para3, 'd': x, 'd_P': x[1:],
                  'p_dhat': yhat, 'P_dhat': np.cumsum(np.diff(x)*yhat[1:])}
    success = results['success']
    P_dhat = np.cumsum(np.diff(x)*yhat[1:])
    r2 = r2_cal(y, yhat)

    #_, ks_p = stats.ks_2samp(P_d, P_dhat)
    _, ks_p = stats.ks_2samp(y, yhat)
    ks = kurtosis(df.distance, fisher=True)
    median = np.median(df.distance)
    return (func_name, r2, ks_p, aic, success, median, ks), paras_dict


def pdf_extraction(df):
    df_out = pd.DataFrame()
    _, bins = np.histogram(np.log10(df.distance), bins='fd')
    values, base = np.histogram(df.distance, bins=10**bins, density=True)
    x = 10**bins[0:-1]
    y = values
    df_out.loc[:, 'd'] = x
    df_out.loc[:, 'y'] = y
    df_out = df_out.loc[df_out.y > 1e-10, :]
    return df_out


class RegionOptimalModelGenerate:
    def __init__(self, runid=None, region=None):
        self.runid = runid
        self.region = region
        self.trips = pd.read_csv(ROOT_dir + f'/dbs/{self.region}/visits/visits_{self.runid}_trips_dom.csv')
        self.trips = self.trips.loc[self.trips.distance >= 0.1, :]
        self.pdfs = []

    def pdf_generator(self, n=None):
        """
        Generate PDFs based on n slices of the trip data.
        :return: a list of PDFs
        :rtype: list
        """
        sd = 815
        list_in = [x for x in range(0, len(self.trips))]
        random.Random(sd).shuffle(list_in)
        list2use = [list_in[i::n] for i in range(n)]
        for lst in list2use:
            self.pdfs.append(pdf_extraction(self.trips.iloc[lst]))

    def optimal_model(self, pdf=None):
        list_paras = []
        for func_name in ['powerlaw_al', 'lognormal', 'truncated_power_law']:
            ot, _ = pdf_fit(self.trips, pdf, func_name=func_name)
            list_paras.append(ot)
        col_names = ['func_name', 'r2', 'ks_p', 'aic', 'success', 'median', 'ks']
        df_paras = pd.DataFrame(list_paras, columns=col_names)
        df_paras = df_paras.loc[df_paras["r2"].idxmax(), :].to_frame(0).T
        return df_paras


if __name__ == '__main__':
    region_list = ['sweden', 'netherlands', 'saopaulo', 'australia', 'austria', 'barcelona',
                   'capetown', 'cebu', 'egypt', 'guadalajara', 'jakarta',
                   'johannesburg', 'kualalumpur', 'lagos', 'madrid', 'manila', 'moscow', 'nairobi',
                   'rio', 'saudiarabia', 'stpertersburg', 'surabaya']
    runid = 7
    n = 10
    list_df_paras = []
    for region in tqdm(region_list, desc='PDF and fitting'):
        region_omg = RegionOptimalModelGenerate(runid=runid, region=region)
        region_omg.pdf_generator(n=n)
        df_paras = pd.concat([region_omg.optimal_model(pdf=pdf) for pdf in region_omg.pdfs])
        print(df_paras.head(3))
        df_paras.loc[:, 'dat_id'] = list(range(1, n + 1))
        df_paras.loc[:, 'region'] = region
        list_df_paras.append(df_paras)
    df = pd.concat(list_df_paras)
    df.to_csv(ROOT_dir + f'/results/multi-region_trips_rid_{runid}_optimal_models.csv', index=False)

