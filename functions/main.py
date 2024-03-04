import pandas as pd
from math import log
from util import variables as var

def interpolacion(dist, x1, x2, y1, y2):
  return ( x1 + (
    (x2 - x1)/(y2 - y1)
  ) * (dist - y1) )

def probit2(rad, probit_df):
  probit2 = 0
  if rad > 0:
    t = 30
    rad1 = rad * 1000
    v = t * pow(rad1, 4/3)
    prob = -36.38 + 2.56 * log(v)
    prob = float(0) if prob < 0 else prob
    search = pd.merge_asof(pd.DataFrame({'Probit': [prob]}), probit_df, on='Probit')
    probit2 = (search['%'].tolist()[0])/100
  return probit2

def radiacion(dist, tabla):
  tabla.fillna(0, inplace=True)
  return tabla.apply(lambda x: 37.5
    if dist < x['37.5'] or dist == 0 else (
      interpolacion(dist, 20.9, 37.5, x['20.9'], x['37.5']) if x['37.5'] < dist < x['20.9'] else (
        interpolacion(dist, 14.5, 20.9, x['14.5'], x['20.9']) if x['20.9'] < dist < x['14.5'] else (
          interpolacion(dist, 12.5, 14.5, x['12.5'], x['14.5']) if x['14.5'] < dist < x['12.5'] else (
            interpolacion(dist, 9.5, 12.5, x['9.5'], x['12.5']) if x['12.5'] < dist < x['9.5'] else (
              interpolacion(dist, 7.3, 9.5, x['7.3'], x['9.5']) if x['9.5'] < dist < x['7.3'] else (
                interpolacion(dist, 5, 7.3, x['5'], x['7.3']) if x['7.3'] < dist < x['5'] else (
                  interpolacion(dist, 1.6, 5, x['1.6'], x['5']) if x['5'] < dist < x['1.6'] else 0
                )
              )
            )
          )
        )
      )
    ), axis=1)

def iso_riesgo(d1, d2, uno, dos, dist, ries):
  iso_riesgo = dist
  if ries < uno and ries > dos:
    iso_riesgo = d1 + ((d2 - d1) / (dos - uno)) * (ries - uno)
  return iso_riesgo

def iso_riesgo_indv(iso_riesgo_df, d1, d2, df3):
  iso_riesgo_df['1.00EXP-03'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-03'], ries=pow(10, -3)
  ), axis=1)
  iso_riesgo_df['1.00EXP-04'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-04'], ries=pow(10, -4)
  ), axis=1)
  iso_riesgo_df['1.00EXP-05'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-05'], ries=pow(10, -5)
  ), axis=1)
  iso_riesgo_df['1.00EXP-06'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-06'], ries=pow(10, -6)
  ), axis=1)
  iso_riesgo_df['1.00EXP-07'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-07'], ries=pow(10, -7)
  ), axis=1)
  iso_riesgo_df['1.00EXP-08'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-08'], ries=pow(10, -8)
  ), axis=1)
  iso_riesgo_df['1.00EXP-09'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-09'], ries=pow(10, -9)
  ), axis=1)
  iso_riesgo_df['1.00EXP-10'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-10'], ries=pow(10, -10)
  ), axis=1)
  iso_riesgo_df['1.00EXP-11'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-11'], ries=pow(10, -11)
  ), axis=1)
  iso_riesgo_df['1.00EXP-12'] = df3.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-12'], ries=pow(10, -12)
  ), axis=1)

  return iso_riesgo_df

def iso_riesgo_eq(iso_riesgo_equipo_df, d1, d2, df4):
  iso_riesgo_equipo_df['1.00EXP-03'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-03'], ries=pow(10, -3)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-04'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-04'], ries=pow(10, -4)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-05'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-05'], ries=pow(10, -5)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-06'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-06'], ries=pow(10, -6)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-07'] = df4.apply(lambda x: iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-07'], ries=pow(10, -7)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-08'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-08'], ries=pow(10, -8)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-09'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-09'], ries=pow(10, -9)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-10'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-10'], ries=pow(10, -10)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-11'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-11'], ries=pow(10, -11)
  ), axis=1)
  iso_riesgo_equipo_df['1.00EXP-12'] = df4.apply(lambda x: iso_riesgo(
    d1, d2, x[d1], x[d2], x['1.00EXP-12'], ries=pow(10, -12)
  ), axis=1)

  return iso_riesgo_equipo_df
