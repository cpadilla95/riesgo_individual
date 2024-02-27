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

def get_p1(categoria, reactividad, tasa):
  if categoria.item() == 1:
    if reactividad.item() == 'Baja':
      if tasa < 10:
        return 0.02
      elif tasa > 100:
        return 0.09
      else:
        return 0.04
    else:
      if tasa < 10:
        return 0.2
      elif tasa > 100:
        return 0.7
      else:
        return 0.5
  elif categoria.item() == 2:
    if tasa.item() > 100:
      return 0.1
    else:
      return 0.065
  else:
    if tasa.item() > 100 or pd.isna(tasa.item()):
      return 0.1
    else:
      return 0.06

def p3(df, ductos):
  df2 = pd.DataFrame(columns=['Ducto', 'Bola'])
  df2['Ducto'] = df['CODIGO ESCENARIO'].isin(ductos['Codigo']).astype(int)
  df2['Bola'] = df['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'].sum(axis=1)
  df2['Bola'] = df2.Bola.apply(lambda x: 1 if x != 0 else 0)
  df2['p3'] = df2.Ducto.apply(lambda x: 1 if x == 1 else 0.7)
  df2['p3'] = df2.p3 * df2.Bola
  return df2['p3']

def p4(sobrepresion_dia, sobrepresion_noche):
  sobrepresion = sobrepresion_dia.sum(axis=1) + sobrepresion_noche.sum(axis=1)
  p4 = sobrepresion.apply(lambda x: 0.6 if x == 0 else 0.4) 
  return p4

def obtener_frecuencias(df):
  df2 = pd.DataFrame(columns=['BLEVE', 'EXP', 'FF', 'JF', 'PF'])
  df2['BLEVE'] = df.apply(lambda x: frecuencia_bleve(x['INICIADOR'], x['P1'], x['P3'], x['FRECUENCIA FALLA MOD (AÑO -1)']), axis=1)
  
  df2['EXP'] = df.apply(lambda x: frecuencia_exp(
    x['INICIADOR'], x['FASE SUSTANCIA'], x['P1'], x['P2'], x['P3'], x['P4'], x['FRECUENCIA FALLA MOD (AÑO -1)'],
    x['SOBREPRESION (PSI) EXPLOSION DIA'], x['SOBREPRESION (PSI) EXPLOSION NOCHE']
  ), axis=1)

  df2['FF'] = df.apply(lambda x: frecuencia_ff(
    x['INICIADOR'], x['FASE SUSTANCIA'], x['P1'], x['P2'], x['P3'], x['P4'], x['FRECUENCIA FALLA MOD (AÑO -1)'],
    x['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)']
  ), axis=1)
  df2['JF'] = df.apply(lambda x: frecuencia_jf(
    x['INICIADOR'], x['P1'], x['FRECUENCIA FALLA MOD (AÑO -1)'], x['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO']
  ), axis=1)
  df2['PF'] = df.apply(lambda x: frecuencia_pf(
    x['INICIADOR'], x['FASE SUSTANCIA'], x['P1'], x['P2'], x['P4'], x['FRECUENCIA FALLA MOD (AÑO -1)'],
    x['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA']
  ), axis=1)
  df2.columns=[(['Frecuencias']*5),['BLEVE', 'EXP', 'FF', 'JF', 'PF']]
  return df2

def frecuencia_bleve(iniciador, p1, p3, freq):
  bleve = 0
  if any(init in iniciador.item() for init in var.descarga_instantanea):
    bleve = p1*p3
  return bleve * freq

def frecuencia_exp(iniciador, fase, p1, p2, p3, p4, freq, exp_dia, exp_noche):
  exp = 0
  if (exp_dia.sum() + exp_noche.sum()) > 0:
    if any(init in iniciador.item() for init in var.descarga_instantanea):
      if fase.values[0] == 'Gas':
        exp = (p1 * (1 - p3) * p4) + ((1 - p1) * p4)
      else:
        exp = (p1 * (1 - p3) * p4) + ((1 -p1) * p2 * p4)
    else:
      exp = (1 - p1) * p2 * p4
  return exp * freq

def frecuencia_ff(iniciador, fase, p1, p2, p3, p4, freq, llamarada):
  ff = 0
  if llamarada.sum() > 0:
    if any(init in iniciador.item() for init in var.descarga_instantanea):
      if fase.values[0] == 'Gas':
        ff = (p1 * (1 - p3) * (1 - p4)) + ((1 - p1) * (1 - p4))
      else:
        ff = (p1 * (1 - p3) * (1 - p4)) + ((1 -p1) * p2 * (1 - p4))
    else:
      ff = (1 - p1) * p2 * (1 - p4)
  return ff * freq

def frecuencia_jf(iniciador, p1, freq, chorro):
  jf = 0
  if chorro.sum() > 0:
    if all(init not in iniciador.item() for init in var.descarga_instantanea):
      jf = p1
  return jf * freq

def frecuencia_pf(iniciador, fase, p1, p2, p4, freq, incendio):
  pf = 0
  if incendio.sum() > 0:
    if any(init in iniciador.item() for init in var.descarga_instantanea):
      if fase.values[0] == 'Liquido':
        pf = ((1 - p1) * p2 * p4) + ((1 - p1) * p2 * (1 - p4))
    else:
      if fase.values[0] == 'Liquido':
        pf = p1 + ((1 - p1) * p2 * p4) + ((1 - p1) * p2 * (1 - p4))
  return pf * freq

def iso_riesgo(d1, d2, uno, dos, dist, ries):
  iso_riesgo = dist
  if ries < uno and ries > dos:
    iso_riesgo = d1 + ((d2 - d1) / (dos - uno)) * (ries - uno)
  return iso_riesgo
