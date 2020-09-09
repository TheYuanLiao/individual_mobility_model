import pandas as pd
import pprint
import gs_model
import json
import os

## Define data path
region = 'saopaulo' # 'sweden', 'netherlands', 'saopaulo'
if region == 'sweden':
    scale_list = ['national', 'east', 'west']
else:
    scale_list = ['national']
geotweets_path = os.getcwd() + f'/dbs/{region}/geotweets_v.csv'
rs_path = os.getcwd() + '/results/'


if __name__ == "__main__":
    df_para = pd.read_csv(rs_path + f'{region}-grid-search-2.csv')
    para_dict = {}
    for scale in scale_list:
        para_dict[scale] = df_para.loc[df_para[scale] == min(df_para[scale]),
                                       ['runid', 'p', 'gamma', 'beta', scale]].rename(columns={scale: 'kl'}).to_dict('r')[0]
    pprint.pprint(para_dict)
    for scale in scale_list:
        print(f'Running {region} - {scale}...')
        p_list = [para_dict[scale]['p']]
        gamma_list = [para_dict[scale]['gamma']]
        beta_list = [para_dict[scale]['beta']]
        run_id = para_dict[scale]['runid']
        if region == 'sweden':
            divergence = gs_model.sweden_visits(p_list, gamma_list, beta_list, run_id, scale)
        else:
            divergence = gs_model.generic_visits(p_list, gamma_list, beta_list, run_id, region, scale='national')
        para_dict[scale]['kl-v'] = divergence[scale]
    with open(rs_path + f"{region}-v.json", 'w') as f:
        json.dump(para_dict, f, indent=2)