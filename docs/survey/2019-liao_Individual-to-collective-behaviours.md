[Source](./../references/2019-liao_Individual-to-collective-behaviours.pdf)

## Method

Comparison between geotagged tweets and individual trip information from Swedish National Travel Survey. Comparison is done over spatio-temportal characteristics and population distribution, that should capture behaviour distortion and population bias respectively.

### Features

6 spatial features are calculated for each individual:

| Type                                | Feature                                             | Description                                                                        |
| ----------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Geographical characteristics        | Radius of gyration                                  | Travel distance range                                                              |
| weighted by the visiting frequency. |
|                                     | Location distance variable                          | Geographical dispersion degree of visited locations.                               |
|                                     | Mean trip distance                                  | Average distance between two consecutive geotagged tweets.                         |
|                                     |
| Network properties                  | Clustering coefficient                              | To which degree the visited locations are connected together.                      |
|                                     | Mean node degree                                    | Overall visiting frequency.                                                        |
|                                     | Max node degree divided by the sum of total degrees | Degree of how centralised the overall visited locations are by visiting frequency. |

### Clustering

Hierarchial clustering:

- min-max normalization
- euclidian distance
- [Ward's method](https://en.wikipedia.org/wiki/Ward%27s_method)

Downsampling of tweets is done to test impact of geotweeting frequency.

## Evaluation

## Cherry picks

Hence, the assumption that the distinct patterns of four user groups are solely due to their difference in geotweeting frequency does not hold. We conclude that the group identities of the users are robust regardless of the users’ geotweeting frequency.

Compared to the one-day travel diary, the Twitter dataset in this study has strengths and weaknesses as a proxy for human mobility. Based on another ongoing study where we compare geotagged tweets with different data sources, the main strengths of geotagged social media data are in long collection duration, a large number of involved individuals, boundary-free spatial coverage, ease of access, low cost, and accurate location informa- tion. The main weaknesses are incomplete individual trajectories caused by high sparsity in the time dimension (plus behaviour bias), lack of socio-demographic information (plus population bias), and lack of trip information
