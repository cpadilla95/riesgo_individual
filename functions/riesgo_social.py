import numbers
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from flask import Flask, request
from functions import main as fn
from util import variables as var

def obtener_riesgo_social(df, probit_df):
    rosa_vientos = float(request.form['rosa_vientos'])/100

    df['Probabilidad Muerte'] = df.apply(lambda x: prob_muerte(
        x['Nivel de Afectación'], rosa_vientos, probit_df
    ), axis=1)

    df['Densidad poblacional Día'] = df.apply(lambda x: densidad(
        x['Personas Dia'], x['Área total'], x['OFF SITE/ONSITE']
    ), axis=1)
    df['Densidad poblacional Noche'] = df.apply(lambda x: densidad(
        x['Personas Noche'], x['Área total'], x['OFF SITE/ONSITE']
    ), axis=1)

    df['Fatalidad Dia'] = df.apply(lambda x: num_personas(
        x['Personas Dia'], x['Densidad poblacional Día'], x['Area intersectada (m2)'], x['OFF SITE/ONSITE']
    ), axis=1)
    df['Fatalidad Noche'] = df.apply(lambda x: num_personas(
        x['Personas Noche'], x['Densidad poblacional Noche'], x['Area intersectada (m2)'], x['OFF SITE/ONSITE']
    ), axis=1)
    df['Fatalidad Total'] = df['Fatalidad Dia'] + df['Fatalidad Noche']
    
    df['Probabilidad de Fatalidad Dia'] = df['Frecuencia SF'] * df['Probabilidad Muerte'] * 0.6
    df['Probabilidad de Fatalidad Noche'] = df['Frecuencia SF'] * df['Probabilidad Muerte'] * 0.4
    df['Probabilidad de Fatalidad Total'] = df['Probabilidad de Fatalidad Dia'] + df['Probabilidad de Fatalidad Noche']

    return df

def prob_muerte(rad, rosa_vientos, probit_df):
    if isinstance(rad, numbers.Number):
        prob = fn.probit2(rad, probit_df)
    else:
        prob = rosa_vientos
    return prob

def densidad(personas, area, tipo):
    if tipo == 'ONSITE':
        val = personas / area
    else:
        val = None
    return val

def num_personas(personas, densidad, area, tipo):
    if tipo == 'ONSITE':
        val = densidad*area
    else:
        val = personas
    return val

def get_graph_df(df, tipo, onsite):
    fatalidad = f"Fatalidad {tipo}"
    prob_fatalidad = f"Probabilidad de {fatalidad}"

    df = df[
        (df['OFF SITE/ONSITE'] == onsite) &
        (df[fatalidad] >= 1) &
        (~df['Nivel de Afectación'].isin(var.afectacion_baja))
    ]
    df = df[['Suceso Final', 'CodEsc', fatalidad, prob_fatalidad]]
    df = df.sort_values(by=fatalidad, ascending=False)
    df['Frecuencia Acumulada'] = df[prob_fatalidad].cumsum()
    df = df.sort_values([fatalidad, 'Frecuencia Acumulada'], ascending=[True, False])
    return df

def graph_rs(writer, df, tipo, onsite):
    sheet_name = f"{onsite} {tipo}"
    fig, ax = plt.subplots()
    ax.plot(var.fatalidades, var.limite_inferior, linestyle = 'dashed', label = 'Límite Inferior', color = 'green')
    ax.plot(var.fatalidades, var.limite_superior, linestyle = 'dashed', label = 'Límite Superior', color = 'red')
    ax.set_yscale('log')
    ax.set_ylabel('Frecuencia (1/año)')
    ax.set_xscale('log')
    ax.set_xlabel('Fatalidades')
    ax.legend(loc = 'upper right')
    ax.set_title(f"Riesgo Social {sheet_name} (HSE UK)")
    graph_df = get_graph_df(df, tipo, onsite)
    ax.plot(
        graph_df[f"Fatalidad {tipo}"],
        graph_df['Frecuencia Acumulada'],
        label = f"RS {sheet_name}",
        color = 'blue'
    )
    limit_x = 100 if graph_df[f"Fatalidad {tipo}"].max() < 100 else 1000
    ax.set_xlim(left=1)
    ax.set_xlim(right=limit_x)
    limit_y =  0.000001 if graph_df['Frecuencia Acumulada'].min() > 0.000001 else 0.00000001
    ax.set_ylim(bottom=limit_y)

    ax.text(
        var.fatalidades[0] * 7,
        var.limite_superior[0] * 0.7,
        'No Tolerable',
        bbox={'facecolor': 'white', 'alpha': 0.4, 'pad': 3}
    )
    ax.text(
        var.fatalidades[0] * 3,
        var.limite_inferior[0] * 0.7,
        '  Tolerable \n con ALARP',
        bbox={'facecolor': 'white', 'alpha': 0.4, 'pad': 3}
    )
    ax.text(
        var.fatalidades[0] * 1.5,
        limit_y * 5,
        'Aceptable',
        bbox={'facecolor': 'white', 'alpha': 0.4, 'pad': 3}
    )

    imgdata = BytesIO()
    fig.savefig(imgdata, format='png')
    graph_df.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.insert_image('I3', '', {'image_data': imgdata})
