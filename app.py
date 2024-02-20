import pandas as pd
import numpy as np
import os
import re
from io import BytesIO
from util import functions as fn, variables as var
from flask import Flask, render_template, request, send_file
from fileinput import filename

app = Flask(__name__)

df = None
probit_df = None
sustancias_df = None
ductos_df = None
file_name = None

# Root endpoint
@app.get('/')
def home():
    return render_template('upload-file.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Read the File using Flask request
    file = request.files['file']

    global df, probit_df, sustancias_df, ductos_df, file_name

    file_name = re.findall(r'(.*)\.', file.filename)[0]

    # Parse the data as a Pandas DataFrame type
    probit_df = pd.read_csv('data/Probit.csv', delimiter=',')

    #
    sustancias_df = pd.read_excel(file, sheet_name='Identificacion de Sustancias', skiprows=4)
    stop_row = sustancias_df[sustancias_df.isnull().all(axis=1) == True].index.tolist()[0]
    sustancias_df = sustancias_df.loc[0:stop_row-1]

    #
    ductos_df = pd.read_excel(file, sheet_name='Input - Ductos', skiprows=3, usecols='A', names=['Codigo'])

    # Parse the data as a Pandas DataFrame type
    df = pd.read_excel(
        file,
        header=None,
        sheet_name='Resultados AAD - RI',
        skiprows=7,
        usecols = 'C:D, G:J, M, P:Q, AA:AH, AL:AS, AW:BD, BH:BI, BM:BN, BR:BV, BZ:CD'
    )

    df.columns = var.column_names
    df.replace(r'^\-$',np.NaN,inplace=True,regex=True)
    df['EQUIPO'] = df['EQUIPO'].fillna(method='ffill', axis=0)
    df['MODIFICADORES FRECUENCIA'] = df['MODIFICADORES FRECUENCIA'].astype(float)
    df.insert(0, 'COD ESC FRECUENCIAS', df['CODIGO ESCENARIO'].str[3:])
    # df.insert(5, 'FASE SUSTANCIA', df['SUSTANCIA'].apply(lambda x: 'Gas' if 'Gas' in x else 'Liquido'))
    df.insert(5, 'FASE SUSTANCIA', df['SUSTANCIA'].apply(
        lambda x:'Gas' if any(gas == x for gas in var.gases) else 'Liquido'
    ))
    df.insert(6, 'CATEGORIA INFLAMABILIDAD', df['SUSTANCIA'].apply(
        lambda x: 1 if any(gas == x for gas in var.gases) else (3 if 'Diesel' in x else 2)
    ))

    return render_template('file-uploaded.html')

@app.route('/preview', methods=['GET', 'POST'])
def preview():
    global df

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="RI AAD", float_format="%.2f")
    output.seek(0)

    return send_file(output, download_name="vista_previa_riesgos.xlsx", as_attachment=True)

@app.route('/compute', methods=['GET', 'POST'])
def compute():
    global df, probit_df, sustancias_df, ductos_df, file_name

    df['FRECUENCIA FALLA MOD (AÑO -1)'] = np.where(
        df['MODIFICADORES FRECUENCIA'].isna,
        df['FRECUENCIA FALLA (año x m -1)'],
        df['FRECUENCIA FALLA (año x m -1)'] * df['MODIFICADORES FRECUENCIA']
    )

    df['P1'] = fn.p1(df, sustancias_df)
    df['P2'] = float(request.form['p2'])
    df['P3'] = fn.p3(df, ductos_df)
    df['P4'] = fn.p4(df['SOBREPRESION (PSI) EXPLOSION DIA'], df['SOBREPRESION (PSI) EXPLOSION NOCHE'])
    df['P5'] = 0

    frecuencias_df = fn.obtener_frecuencias(df)
    df = df.join(frecuencias_df)

    rad_incendio = pd.DataFrame(columns=var.distancias)
    rad_chorro = pd.DataFrame(columns=var.distancias)
    rad_bola = pd.DataFrame(columns=var.distancias)
    probit2_incendio = pd.DataFrame(columns=var.distancias)
    probit2_chorro = pd.DataFrame(columns=var.distancias)
    probit2_bola = pd.DataFrame(columns=var.distancias)
    llamarada_dia = pd.DataFrame(columns=var.distancias)
    llamarada_noche = pd.DataFrame(columns=var.distancias)
    presion_dia = pd.DataFrame(columns=var.distancias)
    presion_noche = pd.DataFrame(columns=var.distancias)
    prob_muerte = pd.DataFrame(columns=['EQUIPO', 'CODIGO ESCENARIO'] + var.distancias)

    iso_riesgo_df = pd.DataFrame({
        'EQUIPO': df['EQUIPO'], 'CODIGO ESCENARIO': df['CODIGO ESCENARIO'],
        '1.00EXP-03': 0, '1.00EXP-04': 0, '1.00EXP-05': 0, '1.00EXP-06': 0,
        '1.00EXP-07': 0, '1.00EXP-08': 0, '1.00EXP-09': 0, '1.00EXP-10': 0,
        '1.00EXP-11': 0, '1.00EXP-12': 0
    })

    col = 0 
    for dist in var.distancias:
        rad_incendio[dist] = fn.radiacion(dist, df['RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA'])
        rad_chorro[dist] = fn.radiacion(dist, df['RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO'])
        rad_bola[dist] = fn.radiacion(dist, df['RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO'])

        probit2_incendio[dist] = rad_incendio[dist].apply(lambda x: fn.probit2(x, probit_df))
        probit2_chorro[dist] = rad_chorro[dist].apply(lambda x: fn.probit2(x, probit_df))
        probit2_bola[dist] = rad_bola[dist].apply(lambda x: fn.probit2(x, probit_df))

        rosa_vientos = float(request.form['rosa_vientos'])/100
        llamarada_dia[dist] = df['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)']['Dia 100% LII'].apply(
            lambda x: rosa_vientos if dist < x else 0
        )
        llamarada_noche[dist] = df['DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)']['Noche 100% LII'].apply(
            lambda x: rosa_vientos if dist < x else 0
        )

        presion_dia[dist] = df['SOBREPRESION (PSI) EXPLOSION DIA']['4.3'].apply(lambda x: rosa_vientos if dist < x else 0)
        presion_noche[dist] = df['SOBREPRESION (PSI) EXPLOSION NOCHE']['4.3'].apply(lambda x: rosa_vientos if dist < x else 0)

        prob_muerte['EQUIPO'] = df['EQUIPO']
        prob_muerte['CODIGO ESCENARIO'] = df['CODIGO ESCENARIO']
        prob_muerte[dist] = 0.6 * (
            probit2_incendio[dist] * df['Frecuencias']['PF'] + probit2_chorro[dist] * df['Frecuencias']['JF'] +
            probit2_bola[dist] * df['Frecuencias']['BLEVE'] + llamarada_dia[dist] * df['Frecuencias']['FF'] +
            presion_dia[dist] * df['Frecuencias']['EXP']
        ) + 0.4 * (
            probit2_incendio[dist] * df['Frecuencias']['PF'] + probit2_chorro[dist] * df['Frecuencias']['JF'] +
            probit2_bola[dist] * df['Frecuencias']['BLEVE'] + llamarada_noche[dist] * df['Frecuencias']['FF'] +
            presion_noche[dist] * df['Frecuencias']['EXP']            
        )

        if col > 0:
            d1 = var.distancias[col - 1]
            d2 = var.distancias[col]

            df3 = iso_riesgo_df.join(prob_muerte[[d1, d2]])

            iso_riesgo_df['1.00EXP-03'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-03'], ries=pow(10, -3)
            ), axis=1)
            iso_riesgo_df['1.00EXP-04'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-04'], ries=pow(10, -4)
            ), axis=1)
            iso_riesgo_df['1.00EXP-05'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-05'], ries=pow(10, -5)
            ), axis=1)
            iso_riesgo_df['1.00EXP-06'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-06'], ries=pow(10, -6)
            ), axis=1)
            iso_riesgo_df['1.00EXP-07'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-07'], ries=pow(10, -7)
            ), axis=1)
            iso_riesgo_df['1.00EXP-08'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-08'], ries=pow(10, -8)
            ), axis=1)
            iso_riesgo_df['1.00EXP-09'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-09'], ries=pow(10, -9)
            ), axis=1)
            iso_riesgo_df['1.00EXP-10'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-10'], ries=pow(10, -10)
            ), axis=1)
            iso_riesgo_df['1.00EXP-11'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-11'], ries=pow(10, -11)
            ), axis=1)
            iso_riesgo_df['1.00EXP-12'] = df3.apply(lambda x: fn.iso_riesgo(
                d1, d2, x[d1], x[d2], x['1.00EXP-12'], ries=pow(10, -12)
            ), axis=1)
        col += 1
 
    prob_muerte_equipo = prob_muerte.groupby('EQUIPO').sum().drop(columns=['CODIGO ESCENARIO'])

    # Return HTML snippet that will render the table
    # return render_template('view-file.html',  table=iso_riesgo_df.to_html(classes='data', header="true"))
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="RI AAD")
        prob_muerte.to_excel(writer, sheet_name="RI", index=False)
        prob_muerte_equipo.to_excel(writer, sheet_name="RI x Equipo")
        iso_riesgo_df.to_excel(writer, sheet_name="Isoriesgo", index=False)
    output.seek(0)

    return send_file(output, download_name=f"{file_name}_RI.xlsx", as_attachment=True)
 
# Main Driver Function
if __name__ == '__main__':
    # Run the application on the local development server
    app.run(debug=True)
