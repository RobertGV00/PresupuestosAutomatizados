import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="VREFORMAS", layout="centered")

# -------- CARGAR PRECIOS DESDE EXCEL --------
@st.cache_data
def cargar_precios_excel(path="precios.xlsx"):
    df = pd.read_excel(path)
    df.columns = [col.replace("Categoría", "Categoria") for col in df.columns]
    precios = {}
    for categoria in df['Categoria'].unique():
        sub_df = df[df['Categoria'] == categoria]
        conceptos = dict(zip(sub_df['Concepto'], sub_df['Precio_unitario']))
        precios[categoria] = conceptos
    return precios

PRECIOS = cargar_precios_excel("precios.xlsx")  # Ruta local

# -------- INICIALIZAR ESTADO --------
if "presupuesto_acumulado" not in st.session_state:
    st.session_state.presupuesto_acumulado = {}

# -------- FUNCIONES --------
def calcular_presupuesto(categoria, inputs, precios):
    total = 0
    detalle = {}
    for concepto, valor in inputs.items():
        precio_unitario = precios[categoria][concepto]
        subtotal = valor * precio_unitario
        if valor > 0:
            detalle[concepto] = subtotal
            total += subtotal
    return total, detalle

def generar_pdf_completo(nombre, email, telefono, datos, logo_path="logo.png"):
    pdf = FPDF()
    pdf.add_page()

    # REGISTRAR FUENTE UTF-8
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass

    pdf.cell(200, 10, txt="Presupuesto de Reforma", ln=1, align="C")
    pdf.ln(10)

    pdf.set_font("DejaVu", size=10)
    pdf.cell(200, 10, f"Cliente: {nombre}", ln=1)
    pdf.cell(200, 10, f"Email: {email}", ln=1)
    pdf.cell(200, 10, f"Teléfono: {telefono}", ln=1)
    pdf.cell(200, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ln=1)
    pdf.ln(10)

    total_general = 0

    for categoria, detalle in datos.items():
        pdf.set_font("DejaVu", "B", 11)
        pdf.cell(200, 10, f"Categoría: {categoria}", ln=1)
        pdf.set_font("DejaVu", size=10)
        for concepto, precio in detalle.items():
            pdf.multi_cell(0, 10, f"{concepto}: {precio:.2f} €")
            total_general += precio
        pdf.ln(5)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(200, 10, f"Total estimado: {total_general:.2f} €", ln=1)

    filename = "presupuesto_completo.pdf"
    pdf.output(filename)
    return filename


# -------- INTERFAZ --------

st.title("Calculadora de Presupuesto por Secciones")

nombre = st.text_input("Nombre del cliente")
email = st.text_input("Email")
telefono = st.text_input("Teléfono")

categoria = st.selectbox("Selecciona una categoría para añadir:", list(PRECIOS.keys()))
inputs = {}

st.subheader("Introduce las cantidades:")

for concepto in PRECIOS[categoria]:
    valor = st.number_input(f"{concepto}:", min_value=0.0, format="%.2f", step=0.5, key=f"{categoria}_{concepto}")
    inputs[concepto] = valor

if st.button("Añadir al presupuesto"):
    total, detalle = calcular_presupuesto(categoria, inputs, PRECIOS)
    if detalle:
        st.session_state.presupuesto_acumulado[categoria] = detalle
        st.success(f"Se añadió {categoria} al presupuesto.")
    else:
        st.warning("Debes introducir al menos un valor mayor a 0.")

# -------- RESUMEN ACUMULADO --------
if st.session_state.presupuesto_acumulado:
    st.subheader("Resumen del presupuesto acumulado:")
    total_acumulado = 0
    for cat, det in st.session_state.presupuesto_acumulado.items():
        st.markdown(f"**{cat}**")
        for concepto, precio in det.items():
            st.write(f"- {concepto}: {precio:.2f} €")
            total_acumulado += precio
    st.success(f"Total acumulado: {total_acumulado:.2f} €")

    if st.button("Generar PDF completo"):
        if nombre and email and telefono:
            archivo = generar_pdf_completo(nombre, email, telefono, st.session_state.presupuesto_acumulado)
            with open(archivo, "rb") as f:
                st.download_button("Descargar PDF completo", f, file_name="presupuesto_completo.pdf", mime="application/pdf")
        else:
            st.warning("Rellena los datos del cliente antes de generar el PDF.")
else:
    st.info("Añade al menos una categoría al presupuesto para generar el total.")
