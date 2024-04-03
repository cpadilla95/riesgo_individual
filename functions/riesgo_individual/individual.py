import pandas as pd
from flask import Flask, request
from io import BytesIO
from util import variables as var
from functions import main as fn
from functions.riesgo_individual import aad as aad_fn, aai as aai_fn

def obtener_riesgo_individual(aad_df, aai_df, ductos_df, probit_df):
  rosa_vientos = float(request.form['rosa_vientos'])/100
  
  # Calcular AAD
  aad_df = aad_fn.obtener_probabilidades(aad_df, float(request.form['p2AAD']), ductos_df)
  frecuencias_df = aad_fn.obtener_frecuencias(aad_df)
  aad_df = aad_df.join(frecuencias_df)
  prob_muerte_aad = pd.DataFrame(columns=['EQUIPO', 'CODIGO ESCENARIO'] + var.distancias)
  iso_riesgo_aad = pd.DataFrame({
    'EQUIPO': aad_df['EQUIPO'], 'CODIGO ESCENARIO': aad_df['CODIGO ESCENARIO'],
    '1.00EXP-03': 0, '1.00EXP-04': 0, '1.00EXP-05': 0, '1.00EXP-06': 0,
    '1.00EXP-07': 0, '1.00EXP-08': 0, '1.00EXP-09': 0, '1.00EXP-10': 0,
    '1.00EXP-11': 0, '1.00EXP-12': 0
  })
  iso_riesgo_equipo_aad = pd.DataFrame({
    'EQUIPO': aad_df['EQUIPO'], '1.00EXP-03': 0, '1.00EXP-04': 0,
    '1.00EXP-05': 0, '1.00EXP-06': 0, '1.00EXP-07': 0, '1.00EXP-08': 0,
    '1.00EXP-09': 0, '1.00EXP-10': 0, '1.00EXP-11': 0, '1.00EXP-12': 0
  }).groupby('EQUIPO').sum()
  riesgos = [aad_df]

  # Calcular AAI
  if len(aai_df) > 0:
    aai_df = aai_fn.obtener_probabilidades(
      aai_df,
      float(request.form['p1AAI']),
      float(request.form['p2AAI']),
      float(request.form['pResidual'])
    )
    aai_df = aai_fn.obtener_frecuencias(aai_df)
    prob_muerte_aai = pd.DataFrame(columns=['CUERPO DE AGUA', 'CODIGO ESCENARIO'] + var.distancias)
    iso_riesgo_aai = pd.DataFrame({
      'EQUIPO': aai_df['CUERPO DE AGUA'], 'CODIGO ESCENARIO': aai_df['CODIGO ESCENARIO'],
      '1.00EXP-03': 0, '1.00EXP-04': 0, '1.00EXP-05': 0, '1.00EXP-06': 0,
      '1.00EXP-07': 0, '1.00EXP-08': 0, '1.00EXP-09': 0, '1.00EXP-10': 0,
      '1.00EXP-11': 0, '1.00EXP-12': 0
    })
    iso_riesgo_equipo_aai = pd.DataFrame({
      'CUERPO DE AGUA': aai_df['CUERPO DE AGUA'], '1.00EXP-03': 0, '1.00EXP-04': 0,
      '1.00EXP-05': 0, '1.00EXP-06': 0, '1.00EXP-07': 0, '1.00EXP-08': 0,
      '1.00EXP-09': 0, '1.00EXP-10': 0, '1.00EXP-11': 0, '1.00EXP-12': 0
    }).groupby('CUERPO DE AGUA').sum()
    riesgos.append(aai_df)

  col = 0
  for dist in var.distancias:
    for risk in riesgos:
      rad_incendio = radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA'])
      rad_chorro = radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO'])
      rad_bola = radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'])

      probit2_incendio = rad_incendio.apply(lambda x: fn.probit2(x, probit_df))
      probit2_chorro = rad_chorro.apply(lambda x: fn.probit2(x, probit_df))
      probit2_bola= rad_bola.apply(lambda x: fn.probit2(x, probit_df))

      llamarada_dia = risk['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)']['Dia 100% LII'].apply(
        lambda x: rosa_vientos if dist < x else 0
      )
      llamarada_noche = risk['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)']['Noche 100% LII'].apply(
        lambda x: rosa_vientos if dist < x else 0
      )

      presion_dia= risk['SOBREPRESION (PSI) EXPLOSION DIA']['4.3'].apply(lambda x: rosa_vientos if dist < x else 0)
      presion_noche = risk['SOBREPRESION (PSI) EXPLOSION NOCHE']['4.3'].apply(lambda x: rosa_vientos if dist < x else 0)
      prob_muerte =  0.6 * (
        probit2_incendio * risk['Frecuencias']['PF'] + probit2_chorro * risk['Frecuencias']['JF'] +
        probit2_bola * risk['Frecuencias']['BLEVE'] + llamarada_dia * risk['Frecuencias']['FF'] +
        presion_dia * risk['Frecuencias']['EXP']
      ) + 0.4 * (
        probit2_incendio * risk['Frecuencias']['PF'] + probit2_chorro * risk['Frecuencias']['JF'] +
        probit2_bola * risk['Frecuencias']['BLEVE'] + llamarada_noche * risk['Frecuencias']['FF'] +
        presion_noche * risk['Frecuencias']['EXP']            
      )
      if 'EQUIPO' in risk.columns:
        prob_muerte_aad['EQUIPO'] = risk['EQUIPO']
        prob_muerte_aad['CODIGO ESCENARIO'] = risk['CODIGO ESCENARIO']
        prob_muerte_aad[dist] =  prob_muerte
      else:
        prob_muerte_aai['CUERPO DE AGUA'] = risk['CUERPO DE AGUA']
        prob_muerte_aai['CODIGO ESCENARIO'] = risk['CODIGO ESCENARIO']
        prob_muerte_aai[dist] = prob_muerte

      if col > 0:
        d1 = var.distancias[col - 1]
        d2 = var.distancias[col]

        if 'EQUIPO' in risk.columns:
          df3 = iso_riesgo_aad.join(prob_muerte_aad[[d1, d2]])
          df4 = iso_riesgo_equipo_aad.join(prob_muerte_aad[['EQUIPO', d1, d2]].groupby('EQUIPO').sum())
          iso_riesgo_aad = iso_riesgo_indv(iso_riesgo_aad, d1, d2, df3)
          iso_riesgo_equipo_aad = iso_riesgo_eq(iso_riesgo_equipo_aad, d1, d2, df4)
        else:
          df3 = iso_riesgo_aai.join(prob_muerte_aai[[d1, d2]])
          df4 = iso_riesgo_equipo_aai.join(prob_muerte_aai[['CUERPO DE AGUA', d1, d2]].groupby('CUERPO DE AGUA').sum())
          iso_riesgo_aai = iso_riesgo_indv(iso_riesgo_aai, d1, d2, df3)
          iso_riesgo_equipo_aai = iso_riesgo_eq(iso_riesgo_equipo_aai, d1, d2, df4)
    col += 1
 
  prob_muerte_equipo_aad = prob_muerte_aad.groupby('EQUIPO').sum().drop(columns=['CODIGO ESCENARIO'])
  if len(aai_df) > 0:
    prob_muerte_equipo_aai = prob_muerte_aai.groupby('CUERPO DE AGUA').sum().drop(columns=['CODIGO ESCENARIO'])

  output = BytesIO()
  with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    ### AAD ###
    aad_df.to_excel(writer, sheet_name="Datos AAD")
    aad_sheet = writer.sheets['Datos AAD']
    aad_sheet.set_tab_color('blue')
    prob_muerte_aad.to_excel(writer, sheet_name="R_Indv AAD_Esc", index=False)
    prob_muerte_equipo_aad.to_excel(writer, sheet_name="R_Indv AAD_Eqp")
    iso_riesgo_aad.to_excel(writer, sheet_name="Dist_Isoriesgo AAD_Esc", index=False)
    iso_riesgo_equipo_aad.to_excel(writer, sheet_name="Dist_Isoriesgo AAD_Eqp")
    ### AAI ###
    if len(aai_df) > 0:
      aai_df.to_excel(writer, sheet_name="Datos AAI")
      aai_sheet = writer.sheets['Datos AAI']
      aai_sheet.set_tab_color('blue')
      prob_muerte_aai.to_excel(writer, sheet_name="R_Indv AAI_Esc", index=False)
      prob_muerte_equipo_aai.to_excel(writer, sheet_name="R_Indv AAI_Eqp")
      iso_riesgo_aai.to_excel(writer, sheet_name="Dist_Isoriesgo AAI_Esc", index=False)
      iso_riesgo_equipo_aai.to_excel(writer, sheet_name="Dist_Isoriesgo AAI_Eqp")
  output.seek(0)
  return output

def interpolacion(dist, x1, x2, y1, y2):
  return ( x1 + (
    (x2 - x1)/(y2 - y1)
  ) * (dist - y1) )

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
