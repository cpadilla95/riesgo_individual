import pandas as pd


def obtener_probabilidades(df, p1, p2, pResidual):
    df["P1"] = p1
    df["P2"] = p2
    df["P Residual"] = pResidual
    return df


def obtener_frecuencias(df):
    df2 = pd.DataFrame(columns=["BLEVE", "EXP", "FF", "JF", "PF"])
    df2["FF"] = (
        df["FRECUENCIA FALLA MOD (AÑO -1)"]
        * (1 - df["P1"])
        * (1 - df["P2"])
        * df["P2"]
        * (1 - df["P Residual"])
    )
    df2["PF"] = (
        df["FRECUENCIA FALLA MOD (AÑO -1)"] * (1 - df["P1"]) * (1 - df["P2"]) * df["P2"]
    )
    df2["BLEVE"] = 0
    df2["EXP"] = 0
    df2["JF"] = 0
    df2.columns = [(["Frecuencias"] * 5), ["BLEVE", "EXP", "FF", "JF", "PF"]]
    df = df.join(df2)
    return df
