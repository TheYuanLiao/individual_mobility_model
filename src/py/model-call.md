

```python
%load_ext autoreload
%autoreload 2
```

    The autoreload extension is already loaded. To reload it, use:
      %reload_ext autoreload
    


```python
import mscthesis
import models
import importlib
importlib.reload(models)
```




    <module 'models' from '/Users/kristofferek/Documents/git/mscthesis/src/py/models.py'>




```python
geotweets = mscthesis.read_geotweets('sweden').set_index('userid')
tweetcount = geotweets.groupby('userid').size()
geotweets = geotweets.drop(
    labels=tweetcount[tweetcount < 5].index,
)
geotweets.head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>region</th>
      <th>createdat</th>
      <th>tweetid</th>
      <th>latitude</th>
      <th>longitude</th>
      <th>month</th>
      <th>weekday</th>
      <th>hourofday</th>
      <th>timezone</th>
      <th>ym</th>
      <th>label</th>
      <th>geometry</th>
    </tr>
    <tr>
      <th>userid</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>5616</th>
      <td>0</td>
      <td>2015-05-07 15:12:52+00:00</td>
      <td>596331871241379840</td>
      <td>57.599221</td>
      <td>18.436371</td>
      <td>5</td>
      <td>4</td>
      <td>17</td>
      <td>Europe/Stockholm</td>
      <td>2015-05</td>
      <td>other</td>
      <td>POINT (18.43637 57.59922)</td>
    </tr>
    <tr>
      <th>5616</th>
      <td>0</td>
      <td>2015-07-20 09:12:12+00:00</td>
      <td>623057810864111616</td>
      <td>57.599221</td>
      <td>18.436371</td>
      <td>7</td>
      <td>1</td>
      <td>11</td>
      <td>Europe/Stockholm</td>
      <td>2015-07</td>
      <td>other</td>
      <td>POINT (18.43637 57.59922)</td>
    </tr>
    <tr>
      <th>5616</th>
      <td>0</td>
      <td>2015-12-23 14:43:00+00:00</td>
      <td>679673567416565760</td>
      <td>57.599221</td>
      <td>18.436371</td>
      <td>12</td>
      <td>3</td>
      <td>15</td>
      <td>Europe/Stockholm</td>
      <td>2015-12</td>
      <td>other</td>
      <td>POINT (18.43637 57.59922)</td>
    </tr>
    <tr>
      <th>5616</th>
      <td>0</td>
      <td>2016-07-25 18:42:00+00:00</td>
      <td>757647103011262465</td>
      <td>57.599221</td>
      <td>18.436371</td>
      <td>7</td>
      <td>1</td>
      <td>20</td>
      <td>Europe/Stockholm</td>
      <td>2016-07</td>
      <td>other</td>
      <td>POINT (18.43637 57.59922)</td>
    </tr>
    <tr>
      <th>5616</th>
      <td>0</td>
      <td>2016-08-10 06:31:05+00:00</td>
      <td>763261365930909696</td>
      <td>57.599221</td>
      <td>18.436371</td>
      <td>8</td>
      <td>3</td>
      <td>8</td>
      <td>Europe/Stockholm</td>
      <td>2016-08</td>
      <td>other</td>
      <td>POINT (18.43637 57.59922)</td>
    </tr>
  </tbody>
</table>
</div>




```python
travel_survey_trips_mean = 3.143905 # PI? It's magic!
travel_survey_trips_std = 1.880373

model = models.PreferentialReturn(
    p=0.66, gamma=0.6, 
    region_sampling=models.RegionZipfProb(s=1.2),
    jump_size_sampling=models.JumpSizeTrueProb(),
)
sampler = models.Sampler(
    model, 
    daily_trips_sampling=models.NormalDistribution(
        travel_survey_trips_mean, 
        travel_survey_trips_std,
    ),
    n_days=7*20,
    geotweets_path="./../../dbs/sweden/geotweets.csv",
)

samples = sampler.sample(geotweets)
```

    done with 250
    done with 500
    done with 750
    done with 1000
    done with 1250
    done with 1500
    done with 1750
    done with 2000
    done with 2250
    done with 2500
    done with 2750
    done with 3000
    done with 3250
    done with 3500
    done with 3750
    done with 4000
    


```python
samples.reset_index().sort_values(['userid', 'day', 'timeslot']).head(20)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>userid</th>
      <th>day</th>
      <th>timeslot</th>
      <th>kind</th>
      <th>latitude</th>
      <th>longitude</th>
      <th>region</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>5616</td>
      <td>0</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>1</th>
      <td>5616</td>
      <td>0</td>
      <td>1</td>
      <td>region</td>
      <td>59.405498</td>
      <td>17.954750</td>
      <td>6</td>
    </tr>
    <tr>
      <th>2</th>
      <td>5616</td>
      <td>0</td>
      <td>2</td>
      <td>region</td>
      <td>57.398813</td>
      <td>18.874708</td>
      <td>52</td>
    </tr>
    <tr>
      <th>3</th>
      <td>5616</td>
      <td>0</td>
      <td>3</td>
      <td>region</td>
      <td>59.405498</td>
      <td>17.954750</td>
      <td>6</td>
    </tr>
    <tr>
      <th>4</th>
      <td>5616</td>
      <td>0</td>
      <td>4</td>
      <td>region</td>
      <td>59.445959</td>
      <td>17.942841</td>
      <td>347</td>
    </tr>
    <tr>
      <th>5</th>
      <td>5616</td>
      <td>1</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>6</th>
      <td>5616</td>
      <td>1</td>
      <td>1</td>
      <td>region</td>
      <td>59.445959</td>
      <td>17.942841</td>
      <td>347</td>
    </tr>
    <tr>
      <th>7</th>
      <td>5616</td>
      <td>1</td>
      <td>2</td>
      <td>region</td>
      <td>59.609415</td>
      <td>16.621037</td>
      <td>505</td>
    </tr>
    <tr>
      <th>8</th>
      <td>5616</td>
      <td>2</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>9</th>
      <td>5616</td>
      <td>2</td>
      <td>1</td>
      <td>region</td>
      <td>59.619067</td>
      <td>16.592795</td>
      <td>371</td>
    </tr>
    <tr>
      <th>10</th>
      <td>5616</td>
      <td>3</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>11</th>
      <td>5616</td>
      <td>3</td>
      <td>1</td>
      <td>region</td>
      <td>59.652696</td>
      <td>17.930374</td>
      <td>2</td>
    </tr>
    <tr>
      <th>12</th>
      <td>5616</td>
      <td>3</td>
      <td>2</td>
      <td>region</td>
      <td>59.402809</td>
      <td>17.944212</td>
      <td>10</td>
    </tr>
    <tr>
      <th>13</th>
      <td>5616</td>
      <td>3</td>
      <td>3</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>14</th>
      <td>5616</td>
      <td>3</td>
      <td>4</td>
      <td>region</td>
      <td>59.609415</td>
      <td>16.621037</td>
      <td>505</td>
    </tr>
    <tr>
      <th>15</th>
      <td>5616</td>
      <td>3</td>
      <td>5</td>
      <td>region</td>
      <td>59.652696</td>
      <td>17.930374</td>
      <td>2</td>
    </tr>
    <tr>
      <th>16</th>
      <td>5616</td>
      <td>3</td>
      <td>6</td>
      <td>region</td>
      <td>59.533885</td>
      <td>18.094632</td>
      <td>424</td>
    </tr>
    <tr>
      <th>17</th>
      <td>5616</td>
      <td>4</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
    <tr>
      <th>18</th>
      <td>5616</td>
      <td>4</td>
      <td>1</td>
      <td>region</td>
      <td>59.405498</td>
      <td>17.954750</td>
      <td>6</td>
    </tr>
    <tr>
      <th>19</th>
      <td>5616</td>
      <td>5</td>
      <td>0</td>
      <td>region</td>
      <td>59.426889</td>
      <td>17.954336</td>
      <td>5</td>
    </tr>
  </tbody>
</table>
</div>




```python
samples.to_csv('./../../dbs/sweden/visits-zipf1.2.csv')
```


```python

```
