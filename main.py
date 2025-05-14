from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from functools import reduce
import operator
import json
from starlette.responses import Response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar los datos
df = pd.read_excel("data.xlsx")

@app.get("/", response_class=HTMLResponse)
def read_index():
    with open("index_with_ajax.html", encoding="utf-8") as f:
        return f.read()

def aplicar_filtro(columna, valores, logica):
    if not valores:
        return pd.Series([True] * len(df))
    condiciones = [df[columna].astype(str).str.contains(valor, case=False, na=False) for valor in valores]
    return reduce(operator.or_, condiciones) if logica == "OR" else reduce(operator.and_, condiciones)

@app.get("/buscar")
def buscar(request: Request):
    args = request.query_params

    draw = int(args.get("draw", 1))
    start = int(args.get("start", 0))
    length = int(args.get("length", 10))

    titulo_vals = [args.get(f"titulo{i}", "") for i in range(1, 6)]
    autor_vals  = [args.get(f"autor{i}", "") for i in range(1, 6)]

    logica_titulo = args.get("logica_titulo", "AND")
    logica_autor = args.get("logica_autor", "AND")

    f1 = aplicar_filtro("Nombre del Libro", [v for v in titulo_vals if v], logica_titulo)
    f2 = aplicar_filtro("Autor", [v for v in autor_vals if v], logica_autor)

    filtrado = df[f1 & f2].copy()

    if "link" in filtrado.columns:
        filtrado["Nombre del Libro"] = filtrado.apply(
            lambda row: f'<a href="{row["link"]}" target="_blank">{row["Nombre del Libro"]}</a>' if pd.notna(row["Nombre del Libro"]) and pd.notna(row["link"]) else row["Nombre del Libro"],
            axis=1
        )

    filtrado = filtrado.replace([float("inf"), float("-inf")], None)
    filtrado = filtrado.fillna("")

    total = len(df)
    total_filtrado = len(filtrado)

    paginado = filtrado.iloc[start:start + length]
    data = paginado[["Nombre del Libro", "Autor", "PÁGINAS"]].to_dict(orient="records")

    json_data = json.dumps({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total_filtrado,
        "data": data
    }, allow_nan=False)

    return Response(content=json_data, media_type="application/json")
