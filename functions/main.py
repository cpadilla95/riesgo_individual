import pandas as pd
from math import log

def probit(rad):
  t = 30
  rad1 = rad * 1000
  v = t * pow(rad1, 4/3)
  prob = -36.38 + 2.56 * log(v)
  prob = float(0) if prob < 0 else prob
  return prob

def probit2(rad, probit_df):
  probit2 = 0
  if rad > 0:
    prob = probit(rad)
    search = pd.merge_asof(pd.DataFrame({'Probit': [prob]}), probit_df, on='Probit')
    probit2 = (search['%'].tolist()[0])/100
  return probit2