import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Simulador Electoral - Chapimarca 2026",
    page_icon="🗳️",
    layout="wide",
)

# Estilos personalizados para la cédula electoral y las tarjetas
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 2.1rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 2rem;
    }
    .candidate-card {
        border: 6px solid #E5E7EB;
        border-radius: 12px;
        padding: 15px;
        background-color: #FAFAFA;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. BASE DE DATOS LOCAL (SQLite)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("votos_chapimarca.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidato TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def registrar_voto(candidato):
    conn = sqlite3.connect("votos_chapimarca.db")
    c = conn.cursor()
    c.execute("INSERT INTO votos (candidato) VALUES (?)", (candidato,))
    conn.commit()
    conn.close()


def obtener_resultados():
    conn = sqlite3.connect("votos_chapimarca.db")
    df = pd.read_sql_query(
        "SELECT candidato, COUNT(*) as votos FROM votos GROUP BY candidato",
        conn,
    )
    conn.close()
    return df


init_db()

# ---------------------------------------------------------
# 3. CONTROL DE SESIÓN (Un solo voto por usuario)
# ---------------------------------------------------------
if "ha_votado" not in st.session_state:
    st.session_state.ha_votado = False

if "candidato_votado" not in st.session_state:
    st.session_state.candidato_votado = None

# ---------------------------------------------------------
# 4. DATOS DE CANDIDATOS (Fotos y Símbolos)
# ---------------------------------------------------------
CANDIDATOS = {
    "David Achulli Gomez": {
        "partido": "Acción Popular",
        "foto": "assets/pala.png",  
        "logo": "assets/david_achulli.jpg",
        "propuesta": "",
    },
    "Robert Cahuana Totocayo": {
        "partido": "Alianza para el Progreso",
        "foto": "assets/alianza.png",
        "logo": "assets/robert.jpg",
        "propuesta": "",
    },
    "Reynaldo Taipe Naveros": {
        "partido": "Ahora Nación",
        "foto": "assets/casco.jpg",
        "logo": "assets/reynaldo.jpg",
        "propuesta": "",
    },
    "Edgar Gomez Taipe": {
        "partido": "Partido Demócrata Verde",
        "foto": "assets/verde.png",
        "logo": "assets/edgar_gomez.jpg",
        "propuesta": "",
    },
    "Percy Rodas Huamani": {
        "partido": "Progresemos",
        "foto": "assets/progresemos.png",
        "logo": "assets/percy_rodas.jpg",
        "propuesta": "",
    },
}

# ---------------------------------------------------------
# 5. ENCABEZADO Y PESTAÑAS
# ---------------------------------------------------------
st.markdown(
    "<h1 class='main-header'>🗳️ Simulación de Voto Municipal - Chapimarca</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='sub-header'>Plataforma participativa y anónima para el Distrito de Chapimarca (Aymaraes)</p>",
    unsafe_allow_html=True,
)

tab1, tab2 = st.tabs(["🎯 Cédula Electoral", "📊 Resultados en Tiempo Real"])

# ---------------------------------------------------------
# TAB 1: CÉDULA ELECTORAL
# ---------------------------------------------------------
with tab1:
    if not st.session_state.ha_votado:
        st.subheader("Cédula Oficial de Votación")
        st.info(
            "ℹ️ Haz clic en el botón de tu candidato preferido para emitir tu voto. Solo puedes votar una vez."
        )

        cols = st.columns(5)

        for idx, (nombre, info) in enumerate(CANDIDATOS.items()):
            with cols[idx]:
                st.image(
                    info["foto"],
                    caption=nombre,
                    use_container_width=True,
                )

                col_logo, col_party = st.columns([1, 2])
                with col_logo:
                    st.image(info["logo"], width=45)
                with col_party:
                    st.caption(f"**{info['partido']}**")

                st.write(f"_{info['propuesta']}_")

                if st.button(
                    f"Votar por {nombre.split()[0]}",
                    key=f"btn_{idx}",
                    use_container_width=True,
                    type="primary",
                ):
                    registrar_voto(nombre)
                    st.session_state.ha_votado = True
                    st.session_state.candidato_votado = nombre
                    st.rerun()

    else:
        st.success(
            f"✅ **¡Tu voto fue registrado!** Seleccionaste a **{st.session_state.candidato_votado}**."
        )
        st.info(
            "🔒 Tu participación ha sido guardada. Revisa los resultados generales en la pestaña **Resultados en Tiempo Real**."
        )

# ---------------------------------------------------------
# TAB 2: RESULTADOS
# ---------------------------------------------------------
with tab2:
    st.subheader("📈 Tendencias y Estimación de Voto")

    df_votos = obtener_resultados()

    df_base = pd.DataFrame({"candidato": list(CANDIDATOS.keys())})
    df_final = pd.merge(df_base, df_votos, on="candidato", how="left").fillna(0)

    total_votos = df_final["votos"].sum()

    m1, m2 = st.columns(2)
    m1.metric("Total de Votos Emitidos", int(total_votos))
    m2.metric("Estatus del Proceso", "Abierto / En curso")

    if total_votos > 0:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_bar = px.bar(
                df_final,
                x="votos",
                y="candidato",
                orientation="h",
                title="Conteo de Votos por Candidato",
                color="candidato",
                color_discrete_sequence=px.colors.qualitative.Set2,
                text="votos",
            )
            fig_bar.update_layout(showlegend=False, yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            fig_pie = px.pie(
                df_final,
                names="candidato",
                values="votos",
                title="Distribución Porcentual (%)",
                hole=0.4,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Aún no hay votos registrados. ¡Sé el primero en votar!")