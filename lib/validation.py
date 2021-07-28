import pandas as pd
import numpy as np


class DistanceMetrics:
    def __init__(self):
        pass

    def compute(self, quantile_groups=None, odms=None, titles=None):
        """
        :param quantile_groups:
        pd.SeriesGroupby mapping distance groups to indexes.
        Obtained by Sampers.prepare
        """
        if len(odms) != len(titles):
            raise Exception("odms and titles must have same length")
        metrics = []
        for grpkey in quantile_groups.groups:
            odm_grps = [o.iloc[quantile_groups.indices[grpkey]] for o in odms]
            metrics.append(
                [grpkey] + [g.sum() for g in odm_grps]
            )
        return pd.DataFrame(
            metrics,
            columns=['distance'] + [t + '_sum' for t in titles]
        ).set_index('distance')

    def kullback_leibler(self, distances, titles=None):
        """
        :param distances:
        A data frame, output of compute(); _sum will be used to calculate Kullback-Leibler divergence measure
        titles[0] ground truth, titles[1] model
        """
        if (titles is None) | (len(titles) != 2):
            raise Exception("Two distance distributions need to be specified.")

        dis = distances.loc[(distances[titles[0] + '_sum'] != 0) | (distances[titles[1] + '_sum'] != 0), :]
        L = len(dis)
        d_ground_truth = dis[titles[0] + '_sum'].values
        d_model = dis[titles[1] + '_sum'].values
        # find zeros to merge to the next bin freq rate
        zeros = list(np.where(d_ground_truth == 0)[0]) + list(np.where(d_model == 0)[0])
        zeros = list(set(zeros))
        tomerge = list(set(zeros + [x + 1 for x in zeros if x < L - 1] + [x - 1 for x in zeros if x == L - 1]))
        tomerge = sorted(tomerge)
        if not tomerge:
            d_gt_out = d_ground_truth
            d_m_out = d_model
        else:
            d_gt_out = d_ground_truth[0:tomerge[0]]
            d_m_out = d_model[0:tomerge[0]]
            end_ind = tomerge[0]
            start_ind = end_ind
            i = 0
            while i < len(tomerge):
                if end_ind < tomerge[i]:
                    end_ind = tomerge[i]
                    d_gt_out = np.append(d_gt_out, d_ground_truth[start_ind:end_ind])
                    d_m_out = np.append(d_m_out, d_model[start_ind:end_ind])
                    start_ind = end_ind
                else:
                    if (i == len(tomerge) - 1) | (tomerge[min(len(tomerge) - 1, i + 1)] - tomerge[i] > 1):
                        end_ind = tomerge[i] + 1
                        d_gt_out = np.append(d_gt_out, [sum(d_ground_truth[start_ind:end_ind])])
                        d_m_out = np.append(d_m_out, [sum(d_model[start_ind:end_ind])])
                        start_ind = end_ind
                    else:
                        end_ind = tomerge[i + 1]
                    i = i + 1
        if len(np.where(d_m_out == 0)[0]) == 0:
            d_kl = sum(d_gt_out * np.log10(d_gt_out / d_m_out))
        else:
            d_kl = 999
        return d_kl