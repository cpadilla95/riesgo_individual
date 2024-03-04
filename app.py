import pandas as pd
import numpy as np
import os
import re
import sys
from io import BytesIO
from util import variables as var, read_files
from functions import main as fn, aad_functions as aad_fn, aai_functions as aai_fn
from flask import Flask, render_template, request, send_file
from fileinput import filename

app = Flask(__name__)

aad_df = None
aai_df = None
ductos_df = None

# Root endpoint
@app.get('/')
def home():
    return render_template('upload-file.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global aad_df, aai_df, ductos_df

    # Leer el archivo usando Flask request
    file = request.files['file']
    # Leer Pestaña de Sustancias
    sustancias_df = read_files.sustancias(file)
    # Leer Pestaña de Ductos
    ductos_df = pd.read_excel(file, sheet_name='Input - Ductos', skiprows=3, usecols='A', names=['Codigo'])
    # Leer Pestaña Riesgo AAD
    aad_df = read_files.riesgo_AAD(file, sustancias_df)
    # Leer Pestaña Riesgo AAI
    aai_df = read_files.riesgo_AAI(file)

    return render_template('file-uploaded.html')

@app.route('/preview', methods=['GET', 'POST'])
def preview():
    global aad_df, aai_df

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        aad_df.to_excel(writer, sheet_name="RI AAD", float_format="%.2f")
        aai_df.to_excel(writer, sheet_name="RI AAI", float_format="%.2f")
    output.seek(0)

    return send_file(output, download_name="vista_previa_riesgos.xlsx", as_attachment=True)

@app.route('/compute', methods=['GET', 'POST'])
def compute():
    global aad_df, aai_df, ductos_df

    # Leer probabilidades
    if getattr(sys, 'frozen', False):
        temp_path = sys._MEIPASS
        probit_df = pd.read_csv(temp_path + '/static/Probit.csv', delimiter=',')
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))
        probit_df = pd.read_csv(app_path + '/static/Probit.csv', delimiter=',')

    # Calcular probabilidades y frecuencias AAD
    aad_df = aad_fn.obtener_probabilidades(aad_df, float(request.form['p2AAD']), ductos_df)
    frecuencias_df = aad_fn.obtener_frecuencias(aad_df)
    aad_df = aad_df.join(frecuencias_df)

    # Calcular probabilidades y frecuencias AAI
    aai_df = aai_fn.obtener_probabilidades(
        aai_df,
        float(request.form['p1AAI']),
        float(request.form['p2AAI']),
        float(request.form['pResidual'])
    )
    aai_df = aai_fn.obtener_frecuencias(aai_df)

    # Definir dataframes a calcular
    prob_muerte_aad = pd.DataFrame(columns=['EQUIPO', 'CODIGO ESCENARIO'] + var.distancias)
    prob_muerte_aai = pd.DataFrame(columns=['CUERPO DE AGUA', 'CODIGO ESCENARIO'] + var.distancias)

    iso_riesgo_aad = pd.DataFrame({
        'EQUIPO': aad_df['EQUIPO'], 'CODIGO ESCENARIO': aad_df['CODIGO ESCENARIO'],
        '1.00EXP-03': 0, '1.00EXP-04': 0, '1.00EXP-05': 0, '1.00EXP-06': 0,
        '1.00EXP-07': 0, '1.00EXP-08': 0, '1.00EXP-09': 0, '1.00EXP-10': 0,
        '1.00EXP-11': 0, '1.00EXP-12': 0
    })

    iso_riesgo_aai = pd.DataFrame({
        'EQUIPO': aai_df['CUERPO DE AGUA'], 'CODIGO ESCENARIO': aai_df['CODIGO ESCENARIO'],
        '1.00EXP-03': 0, '1.00EXP-04': 0, '1.00EXP-05': 0, '1.00EXP-06': 0,
        '1.00EXP-07': 0, '1.00EXP-08': 0, '1.00EXP-09': 0, '1.00EXP-10': 0,
        '1.00EXP-11': 0, '1.00EXP-12': 0
    })

    iso_riesgo_equipo_aad = pd.DataFrame({
        'EQUIPO': aad_df['EQUIPO'], '1.00EXP-03': 0, '1.00EXP-04': 0,
        '1.00EXP-05': 0, '1.00EXP-06': 0, '1.00EXP-07': 0, '1.00EXP-08': 0,
        '1.00EXP-09': 0, '1.00EXP-10': 0, '1.00EXP-11': 0, '1.00EXP-12': 0
    }).groupby('EQUIPO').sum()

    iso_riesgo_equipo_aai = pd.DataFrame({
        'CUERPO DE AGUA': aai_df['CUERPO DE AGUA'], '1.00EXP-03': 0, '1.00EXP-04': 0,
        '1.00EXP-05': 0, '1.00EXP-06': 0, '1.00EXP-07': 0, '1.00EXP-08': 0,
        '1.00EXP-09': 0, '1.00EXP-10': 0, '1.00EXP-11': 0, '1.00EXP-12': 0
    }).groupby('CUERPO DE AGUA').sum()

    rosa_vientos = float(request.form['rosa_vientos'])/100
    col = 0
    for dist in var.distancias:
        for risk in [aad_df, aai_df]:
            rad_incendio = fn.radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA'])
            rad_chorro = fn.radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO'])
            rad_bola = fn.radiacion(dist, risk['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'])

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

            if 'EQUIPO' in risk.columns:
                prob_muerte_aad['EQUIPO'] = risk['EQUIPO']
                prob_muerte_aad['CODIGO ESCENARIO'] = risk['CODIGO ESCENARIO']
                prob_muerte_aad[dist] =  0.6 * (
                    probit2_incendio * risk['Frecuencias']['PF'] + probit2_chorro * risk['Frecuencias']['JF'] +
                    probit2_bola * risk['Frecuencias']['BLEVE'] + llamarada_dia * risk['Frecuencias']['FF'] +
                    presion_dia * risk['Frecuencias']['EXP']
                ) + 0.4 * (
                    probit2_incendio * risk['Frecuencias']['PF'] + probit2_chorro * risk['Frecuencias']['JF'] +
                    probit2_bola * risk['Frecuencias']['BLEVE'] + llamarada_noche * risk['Frecuencias']['FF'] +
                    presion_noche * risk['Frecuencias']['EXP']            
                )
            else:
                prob_muerte_aai['CUERPO DE AGUA'] = risk['CUERPO DE AGUA']
                prob_muerte_aai['CODIGO ESCENARIO'] = risk['CODIGO ESCENARIO']
                prob_muerte_aai[dist] = 0.6 * (
                    probit2_incendio * risk['Frecuencias']['PF'] +
                    llamarada_dia * risk['Frecuencias']['FF']
                ) + 0.4 * (
                    probit2_incendio * risk['Frecuencias']['PF'] +
                    llamarada_noche * risk['Frecuencias']['FF']
                )

            if col > 0:
                d1 = var.distancias[col - 1]
                d2 = var.distancias[col]

                if 'EQUIPO' in risk.columns:
                    df3 = iso_riesgo_aad.join(prob_muerte_aad[[d1, d2]])
                    df4 = iso_riesgo_equipo_aad.join(prob_muerte_aad[['EQUIPO', d1, d2]].groupby('EQUIPO').sum())
                    iso_riesgo_aad = fn.iso_riesgo_indv(iso_riesgo_aad, d1, d2, df3)
                    iso_riesgo_equipo_aad = fn.iso_riesgo_eq(iso_riesgo_equipo_aad, d1, d2, df4)
                else:
                    df3 = iso_riesgo_aai.join(prob_muerte_aai[[d1, d2]])
                    df4 = iso_riesgo_equipo_aai.join(prob_muerte_aai[['CUERPO DE AGUA', d1, d2]].groupby('CUERPO DE AGUA').sum())
                    iso_riesgo_aai = fn.iso_riesgo_indv(iso_riesgo_aai, d1, d2, df3)
                    iso_riesgo_equipo_aai = fn.iso_riesgo_eq(iso_riesgo_equipo_aai, d1, d2, df4)
        col += 1
 
    prob_muerte_equipo_aad = prob_muerte_aad.groupby('EQUIPO').sum().drop(columns=['CODIGO ESCENARIO'])
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
        aai_df.to_excel(writer, sheet_name="Datos AAI")
        aai_sheet = writer.sheets['Datos AAI']
        aai_sheet.set_tab_color('blue')
        prob_muerte_aai.to_excel(writer, sheet_name="R_Indv AAI_Esc", index=False)
        prob_muerte_equipo_aai.to_excel(writer, sheet_name="R_Indv AAI_Eqp")
        iso_riesgo_aai.to_excel(writer, sheet_name="Dist_Isoriesgo AAI_Esc", index=False)
        iso_riesgo_equipo_aai.to_excel(writer, sheet_name="Dist_Isoriesgo AAI_Eqp")
    output.seek(0)

    file_name = f"Cáculo Riesgo Individual_{request.form['file_name']}.xlsx"
    return send_file(output, download_name=file_name, as_attachment=True)
 
# Main Driver Function
if __name__ == '__main__':
    # Run the application on the local development server
    app.run(debug=True)
