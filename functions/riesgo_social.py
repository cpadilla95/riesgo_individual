import numbers
from flask import Flask, request
from functions import main as fn

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

    df = df[(df['OFF SITE/ONSITE'] == onsite) & (df[fatalidad] >= 1)]
    df = df[['Suceso Final', 'CodEsc', fatalidad, prob_fatalidad]]
    df = df.sort_values(by=fatalidad, ascending=False)
    df['Frecuencia Acumulada'] = df[prob_fatalidad].cumsum()
    df = df.sort_values(by=fatalidad)
    return df