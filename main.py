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

def generar_pdf_completo(nombre, email, telefono, datos, logo_path="logo.jpg"):
    pdf = FPDF()
    pdf.add_page()

    # Fuente UTF-8
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=10)

    # CABECERA
    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass

    pdf.set_xy(140, 8)
    pdf.cell(60, 10, "C/Dulce Chacón 17, piso 18G", ln=1, align="R")
    pdf.set_xy(140, 14)
    pdf.cell(60, 10, f"Madrid, {datetime.now().strftime('%d de %B de %Y')}", ln=1, align="R")

    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "PRESUPUESTO DETALLADO", ln=1, align="C")
    pdf.ln(5)

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 8, f"Cliente: {nombre}", ln=1)
    pdf.cell(0, 8, f"Email: {email}", ln=1)
    pdf.cell(0, 8, f"Teléfono: {telefono}", ln=1)
    pdf.ln(8)

    # CONCEPTOS NUMERADOS
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 10, "CONCEPTO", ln=1)

    pdf.set_font("DejaVu", "", 10)
    total_general = 0
    num = 1
    totales_por_categoria = {}

    for categoria, detalle in datos.items():
        subtotal_categoria = 0
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(0, 8, f"{categoria}:", ln=1)
        pdf.set_font("DejaVu", "", 10)
        for concepto, precio in detalle.items():
            pdf.multi_cell(0, 8, f"{num}. {concepto} - {precio:.2f} €")
            subtotal_categoria += precio
            num += 1
        pdf.ln(2)
        totales_por_categoria[categoria] = subtotal_categoria
        total_general += subtotal_categoria

    # CAPÍTULOS + GASTOS + IVA
    pdf.ln(5)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 10, "PRESUPUESTO", ln=1)

    pdf.set_font("DejaVu", "", 10)
    for cap, total in totales_por_categoria.items():
        pdf.cell(0, 8, f"- {cap}: {total:.2f} €", ln=1)

    gastos_generales = total_general * 0.05
    iva = 0.00
    valor_estimado = total_general + gastos_generales + iva

    pdf.cell(0, 8, f"GASTOS GENERALES (5%): {gastos_generales:.2f} €", ln=1)
    pdf.cell(0, 8, f"VALOR ESTIMADO: {valor_estimado:.2f} €", ln=1)
    pdf.cell(0, 8, f"IVA (0%): {iva:.2f} €", ln=1)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, f"TOTAL: {valor_estimado:.2f} €", ln=1)

    # TÉRMINOS
    pdf.ln(10)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 10, "TÉRMINOS Y CONDICIONES:", ln=1)
    pdf.set_font("DejaVu", "", 9)
    pdf.multi_cell(0, 6, """
1. CADUCIDAD DEL PRESUPUESTO: Este presupuesto tiene una validez de 30 días desde la entrega.
2. CONDICIONES DE PAGO: Se pagará el 40% a la firma del presupuesto y el resto al finalizar los trabajos.
3. DURACIÓN: La duración estimada de la obra será acordada con la propiedad, considerando solo días laborables.
4. MODIFICACIONES: Cualquier cambio durante la obra podrá alterar el importe final del presupuesto.
""")

    # FIRMAS
    pdf.ln(10)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 10, "Firmado en _____________________________ con fecha ________________________________", ln=1)
    pdf.ln(10)
    pdf.cell(0, 8, "EL AUTOR DEL PRESUPUESTO", ln=1)
    pdf.cell(0, 8, "Vorobchevici, Vasile", ln=1)
    pdf.ln(8)
    pdf.cell(0, 8, "CONFORME: PROPIEDAD", ln=1)

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
