import pandas as pd
import os
import sys
from io import BytesIO
from util import read_files, riesgo_social as soc_fn
from util.riesgo_individual import individual as indv_fn
from flask import Flask, render_template, request, send_file
from cachetools import cached, TTLCache

app = Flask(__name__)
cache = TTLCache(maxsize=100, ttl=60)


def read_probit_df():
    if getattr(sys, "frozen", False):
        temp_path = sys._MEIPASS
        df = pd.read_csv(temp_path + "/static/Probit.csv", delimiter=",")
    else:
        app_path = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(app_path + "/static/Probit.csv", delimiter=",")
    return df


@cached(cache)
def read_social_df():
    file = request.files["file"]
    df = read_files.riesgo_social(file)
    return df


@cached(cache)
def read_individual_df():
    file = request.files["file"]
    # Leer Pestaña de Sustancias
    sustancias_df = read_files.sustancias(file)
    # Leer Pestaña de Ductos
    ductos_df = pd.read_excel(
        file, sheet_name="Input - Ductos", skiprows=3, usecols="A", names=["Codigo"]
    )
    # Leer Pestaña Riesgo AAD
    aad_df = read_files.riesgo_AAD(file, sustancias_df)
    # Leer Pestaña Riesgo AAI
    aai_df = read_files.riesgo_AAI(file)
    return ductos_df, aad_df, aai_df


# Root endpoint
@app.get("/")
def home():
    return render_template("main.html")


@app.route("/riesgo_individual", methods=["GET", "POST"])
def riesgo_individual():
    return render_template("upload-riesgo-individual.html")


@app.route("/riesgo_social", methods=["GET", "POST"])
def riesgo_social():
    return render_template("upload-riesgo-social.html")


@app.route("/riesgo_individual/upload", methods=["GET", "POST"])
def individual_upload():
    # Leer el archivo
    read_individual_df()
    return render_template("individual-uploaded.html")


@app.route("/riesgo_individual/preview", methods=["GET", "POST"])
def individual_preview():
    output = BytesIO()
    ductos_df, aad_df, aai_df = read_individual_df()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        aad_df.to_excel(writer, sheet_name="RI AAD", float_format="%.2f")
        aai_df.to_excel(writer, sheet_name="RI AAI", float_format="%.2f")
    output.seek(0)

    return send_file(
        output, download_name="vista_previa_riesgos.xlsx", as_attachment=True
    )


@app.route("/riesgo_individual/compute", methods=["GET", "POST"])
def individual_compute():
    probit_df = read_probit_df()
    ductos_df, aad_df, aai_df = read_individual_df()
    riesgo_individual = indv_fn.obtener_riesgo_individual(
        aad_df, aai_df, ductos_df, probit_df
    )

    file_name = f"Cáculo Riesgo Individual_{request.form['file_name']}.xlsx"
    return send_file(riesgo_individual, download_name=file_name, as_attachment=True)


@app.route("/riesgo_social/upload", methods=["GET", "POST"])
def social_upload():
    # Leer el archivo
    read_social_df()
    return render_template("social-uploaded.html")


@app.route("/riesgo_social/preview", methods=["GET", "POST"])
def social_preview():
    social_df = read_social_df()
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        social_df.to_excel(writer, sheet_name="Preview")
    output.seek(0)

    return send_file(
        output, download_name="vista_previa_riesgos.xlsx", as_attachment=True
    )


@app.route("/riesgo_social/compute", methods=["GET", "POST"])
def social_compute():
    probit_df = read_probit_df()
    social_df = read_social_df()
    social_df = soc_fn.obtener_riesgo_social(social_df, probit_df)

    file_name = f"Cálculo Riesgo Social_{request.form['file_name']}.xlsx"
    return send_file(social_df, download_name=file_name, as_attachment=True)


# Main Driver Function
if __name__ == "__main__":
    # Run the application on the local development server
    app.run(debug=True)
