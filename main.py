import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --------- CARGAR PRECIOS DESDE EXCEL ---------

@st.cache_data
def cargar_precios_excel(path="precios.xlsx"):
    df = pd.read_excel(path)

    # Asegurar que el nombre de columna sea 'Categoria'
    df.columns = [col.replace("Categoría", "Categoria") for col in df.columns]

    precios = {}
    for categoria in df['Categoria'].unique():
        sub_df = df[df['Categoria'] == categoria]
        conceptos = dict(zip(sub_df['Concepto'], sub_df['Precio_unitario']))
        precios[categoria] = conceptos
    return precios

PRECIOS = cargar_precios_excel("precios.xlsx")

# --------- FUNCIONES ---------

def calcular_presupuesto(categoria, inputs, precios):
    total = 0
    detalle = {}
    for concepto, valor in inputs.items():
        precio_unitario = precios[categoria][concepto]
        subtotal = valor * precio_unitario
        total += subtotal
        detalle[concepto] = subtotal
    return total, detalle

def generar_pdf(nombre, email, telefono, categoria, detalle, total, logo_path="logo.png"):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass  # Por si no hay logo

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Presupuesto de Reforma", ln=1, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, f"Cliente: {nombre}", ln=1)
    pdf.cell(200, 10, f"Email: {email}", ln=1)
    pdf.cell(200, 10, f"Teléfono: {telefono}", ln=1)
    pdf.cell(200, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=1)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 10, f"Categoría: {categoria}", ln=1)
    pdf.set_font("Arial", size=10)
    for item, precio in detalle.items():
        pdf.multi_cell(0, 10, f"{item}: {precio:.2f} €")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, f"Total estimado: {total:.2f} €", ln=1)

    filename = "presupuesto_generado.pdf"
    pdf.output(filename)
    return filename

# --------- INTERFAZ ---------

st.set_page_config(page_title="Presupuesto Reformas", layout="centered")
st.title("Calculadora de Presupuestos de Reforma")

nombre = st.text_input("Nombre del cliente")
email = st.text_input("Email")
telefono = st.text_input("Teléfono")

categoria = st.selectbox("Selecciona la categoría de reforma:", list(PRECIOS.keys()))
inputs = {}

st.subheader("Introduce las cantidades necesarias:")

for concepto in PRECIOS[categoria]:
    valor = st.number_input(f"{concepto}:", min_value=0.0, format="%.2f", step=0.5)
    inputs[concepto] = valor

if st.button("Calcular y generar PDF"):
    if nombre and email and telefono:
        total, detalle = calcular_presupuesto(categoria, inputs, PRECIOS)
        pdf_file = generar_pdf(nombre, email, telefono, categoria, detalle, total)

        with open(pdf_file, "rb") as file:
            st.success(f"Presupuesto generado correctamente: {total:.2f} €")
            st.download_button(
                label="Descargar PDF",
                data=file,
                file_name="presupuesto.pdf",
                mime="application/pdf"
            )
    else:
        st.warning("Por favor completa todos los campos del cliente antes de continuar.")
