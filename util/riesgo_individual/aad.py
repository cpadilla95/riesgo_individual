import pandas as pd
from util import variables as var


def obtener_probabilidades(df, p2, p5, ductos_df):
    if df["P1"].isna().all():
        df["P1"] = df.apply(
            lambda x: get_p1(
                x["CATEGORIA INFLAMABILIDAD"], x["REACTIVIDAD"], x["TASA (kg/s)"]
            ),
            axis=1,
        )
    if df["P2"].isna().all():
        df["P2"] = float(p2)
    if df["P3"].isna().all():
        df["P3"] = get_p3(df, ductos_df)
    if df["P4"].isna().all():
        df["P4"] = get_p4(
            df["SOBREPRESION (PSI) EXPLOSION DIA"],
            df["SOBREPRESION (PSI) EXPLOSION NOCHE"],
        )
    if df["P5"].isna().all():
        df["P5"] = float(p5) if p5 != "" else 0

    return df


def get_p1(categoria, reactividad, tasa):
    if categoria.item() == 1:
        if reactividad.item() == "Baja":
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


def get_p3(df, ductos):
    df2 = pd.DataFrame(columns=["Ducto", "Bola"])
    df2["Ducto"] = df["CODIGO ESCENARIO"].isin(ductos["Codigo"]).astype(int)
    df2["Bola"] = df["RADIACIÓN TÉRMICA (kW/m2) BOLA DE FUEGO"].sum(axis=1)
    df2["Bola"] = df2.Bola.apply(lambda x: 1 if x != 0 else 0)
    df2["p3"] = df2.Ducto.apply(lambda x: 1 if x == 1 else 0.7)
    df2["p3"] = df2.p3 * df2.Bola
    return df2["p3"]


def get_p4(sobrepresion_dia, sobrepresion_noche):
    sobrepresion = sobrepresion_dia.sum(axis=1) + sobrepresion_noche.sum(axis=1)
    p4 = sobrepresion.apply(lambda x: 0.6 if x == 0 else 0.4)
    return p4


def obtener_frecuencias(df):
    df2 = pd.DataFrame(columns=["BLEVE", "EXP", "FF", "JF", "PF"])
    df2["BLEVE"] = df.apply(
        lambda x: frecuencia_bleve(
            x["INICIADOR"], x["P1"], x["P3"], x["FRECUENCIA FALLA MOD (AÑO -1)"]
        ),
        axis=1,
    )

    df2["EXP"] = df.apply(
        lambda x: frecuencia_exp(
            x["INICIADOR"],
            x["FASE SUSTANCIA"],
            x["P1"],
            x["P2"],
            x["P3"],
            x["P4"],
            x["FRECUENCIA FALLA MOD (AÑO -1)"],
            x["SOBREPRESION (PSI) EXPLOSION DIA"],
            x["SOBREPRESION (PSI) EXPLOSION NOCHE"],
        ),
        axis=1,
    )

    df2["FF"] = df.apply(
        lambda x: frecuencia_ff(
            x["INICIADOR"],
            x["FASE SUSTANCIA"],
            x["P1"],
            x["P2"],
            x["P3"],
            x["P4"],
            x["FRECUENCIA FALLA MOD (AÑO -1)"],
            x["DISPERSIÓN DE NUBE INFLAMABLE - DISTANCIAS DE AFECTACIÓN (m)"],
        ),
        axis=1,
    )
    df2["JF"] = df.apply(
        lambda x: frecuencia_jf(
            x["INICIADOR"],
            x["P1"],
            x["FRECUENCIA FALLA MOD (AÑO -1)"],
            x["RADIACIÓN TÉRMICA (kW/m2) CHORRO DE FUEGO"],
        ),
        axis=1,
    )
    df2["PF"] = df.apply(
        lambda x: frecuencia_pf(
            x["INICIADOR"],
            x["FASE SUSTANCIA"],
            x["P1"],
            x["P2"],
            x["P4"],
            x["FRECUENCIA FALLA MOD (AÑO -1)"],
            x["RADIACIÓN TÉRMICA (kW/m2) INCENDIO DE PISCINA"],
        ),
        axis=1,
    )
    df2.columns = [(["Frecuencias"] * 5), ["BLEVE", "EXP", "FF", "JF", "PF"]]
    return df2


def frecuencia_bleve(iniciador, p1, p3, freq):
    bleve = 0
    if any(init in iniciador.item() for init in var.descarga_instantanea):
        bleve = p1 * p3
    return bleve * freq


def frecuencia_exp(iniciador, fase, p1, p2, p3, p4, freq, exp_dia, exp_noche):
    exp = 0
    if (exp_dia.sum() + exp_noche.sum()) > 0:
        if any(init in iniciador.item() for init in var.descarga_instantanea):
            if fase.values[0] == "Gas":
                exp = (p1 * (1 - p3) * p4) + ((1 - p1) * p4)
            else:
                exp = (p1 * (1 - p3) * p4) + ((1 - p1) * p2 * p4)
        else:
            exp = (1 - p1) * p2 * p4
    return exp * freq


def frecuencia_ff(iniciador, fase, p1, p2, p3, p4, freq, llamarada):
    ff = 0
    if llamarada.sum() > 0:
        if any(init in iniciador.item() for init in var.descarga_instantanea):
            if fase.values[0] == "Gas":
                ff = (p1 * (1 - p3) * (1 - p4)) + ((1 - p1) * (1 - p4))
            else:
                ff = (p1 * (1 - p3) * (1 - p4)) + ((1 - p1) * p2 * (1 - p4))
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
            if fase.values[0] == "Liquido":
                pf = ((1 - p1) * p2 * p4) + ((1 - p1) * p2 * (1 - p4))
        else:
            if fase.values[0] == "Liquido":
                pf = p1 + ((1 - p1) * p2 * p4) + ((1 - p1) * p2 * (1 - p4))
    return pf * freq
