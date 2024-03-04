import pandas as pd
import numpy as np
from util import variables as var

###############################################
def sustancias(file):
    df = pd.read_excel(file, sheet_name='Identificacion de Sustancias', skiprows=4)
    stop_row = df[df['Código'].isna()]
    if not stop_row.empty:
        df = df.loc[0:stop_row.index.tolist()[0]-1]
    return df

###############################################
def riesgo_AAD(file, sustancias_df):
    df = pd.read_excel(
        file,
        header=None,
        sheet_name='Resultados AAD - RI',
        skiprows=7,
        usecols = 'C:D, G:J, M, P:Q, AA:AH, AL:AS, AW:BD, BH:BI, BM:BN, BR:BV, BZ:CD'
    )
    df.columns = var.column_names_aad
    stop_row = df[df['SUSTANCIA'].isna()]
    if not stop_row.empty:
        df = df.loc[0:stop_row.index.tolist()[0]-1]

    df.replace(r'^\-$',np.NaN,inplace=True,regex=True)
    df['EQUIPO'] = df['EQUIPO'].fillna(method='ffill', axis=0)
    df['MODIFICADORES FRECUENCIA'] = df['MODIFICADORES FRECUENCIA'].astype(float)
    df.insert(0, 'COD ESC FRECUENCIAS', df['CODIGO ESCENARIO'].str[3:])
    df.insert(5, 'FASE SUSTANCIA', df['SUSTANCIA'].apply(
        lambda x:'Gas' if any(gas == x for gas in var.gases) else 'Liquido'
    ))

    df2 = df['CODIGO ESCENARIO'].str.split('/', expand=True)
    df2.columns = ['Localización', 'Iniciador', 'Código']
    df2 = pd.merge(df2, sustancias_df, on='Código', how='left')
    df.insert(6, 'CATEGORIA INFLAMABILIDAD', df2['Categoria'])
    df.insert(7, 'REACTIVIDAD', df2['Reactividad'])

    df['FRECUENCIA FALLA MOD (AÑO -1)'] = np.where(
        df['MODIFICADORES FRECUENCIA'].isna,
        df['FRECUENCIA FALLA (año x m -1)'],
        df['FRECUENCIA FALLA (año x m -1)'] * df['MODIFICADORES FRECUENCIA']
    )
    
    return df

###############################################
def riesgo_AAI(file):
    df = pd.read_excel(
        file,
        header=None,
        sheet_name='Resultados AAI - RI',
        skiprows=7,
        usecols = 'E:J, R:Y, AC:AJ, AN:AU, AY:AZ, BD:BE, BI:BM, BQ:BU'
    )
    df.columns = var.column_names_aai
    stop_row = df[df['SUSTANCIA'].isna()]
    if not stop_row.empty:
        df = df.loc[0:stop_row.index.tolist()[0]-1]

    df.replace(r'^\-$',np.NaN,inplace=True,regex=True)
    df['CUERPO DE AGUA'] = df['CUERPO DE AGUA'].fillna(method='ffill', axis=0)
    df['TRAMO'] = df['TRAMO'].fillna(method='ffill', axis=0)
    df['MODIFICADORES FRECUENCIA'] = df['MODIFICADORES FRECUENCIA'].astype(float)

    df['FRECUENCIA FALLA MOD (AÑO -1)'] = np.where(
        df['MODIFICADORES FRECUENCIA'].isna,
        df['FRECUENCIA FALLA (año x m -1)'],
        df['FRECUENCIA FALLA (año x m -1)'] * df['MODIFICADORES FRECUENCIA']
    )

    df2 = df.apply(lambda x: get_escenario_aai(
        x['CUERPO DE AGUA'], x['INICIADOR'], x['SUSTANCIA']
    ), axis=1)
    df.insert(0, 'CODIGO ESCENARIO', df2)
    
    return df

def get_escenario_aai(cuerpo, init, sustancia):
    codigo = f"{cuerpo.item()}/{init.item()[:2]}/{sustancia.item()}"
    return codigo