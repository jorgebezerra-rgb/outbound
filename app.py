import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Dashboard de Desempenho",
    layout="wide",
    initial_sidebar_state="collapsed"
)

url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQc7pTiScl6n_M9hRk1xrTBPUVdG6jtErnsS3skoZiC-49NdFyQd5D3877D3M4wM8kXf27gZvCjY5vo/pub?gid=390048025&single=true&output=csv"

# ✅ Cache dos dados (10 min)
@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados(url_csv: str) -> pd.DataFrame:
    df = pd.read_csv(url_csv, thousands='.')
    colunas_numericas = [
        'Meta Planejada', 'Meta Acumulada', 'Realizado Hora',
        'Realizado Acumulado', 'Tendência', 'Dentro', 'Fora',
        'Dentro Acumulado', 'Fora Acumulado'
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('None', '', regex=False),
                errors='coerce'
            )
    df = df.dropna(subset=['Hora'])
    df['Hora'] = df['Hora'].astype(int)
    df = df.sort_values(by='Hora')
    # Evitar strings vazias em colunas numéricas no restante do fluxo
    df = df.fillna('')
    return df

def gerar_grafico_acumulado(df, area):
    if df.empty:
        st.warning(f"Nenhum dado disponível para {area}.")
        return

    cores = [
        "#46bdc6" if (str(r).strip() != '' and str(d).strip() != '' and float(r) >= float(d))
        else "#FF4C4C"
        for r, d in zip(df["Realizado Acumulado"], df["Dentro Acumulado"])
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df['Hora'],
        y=df['Realizado Acumulado'],
        name='Realizado Acumulado',
        marker=dict(
            color=cores,
            cornerradius=8  # ↩️ arredondamento por traço (opcional, além do layout)
        ),
        text=df['Realizado Acumulado'],
        texttemplate='%{text:.0f}',
        textposition='outside',
        textfont=dict(size=14, color='white', family='Arial'),
        textangle=-90,
        width=0.8,
        cliponaxis=False  # ✅ evita corte do texto fora do eixo
    ))

    fig.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Meta Acumulada'],
        name='Meta',
        mode='lines',
        line=dict(color='lime', dash='dash', width=3, shape='spline'),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Tendência'],
        name='Tendência',
        mode='lines',
        line=dict(color='orange', dash='dot',  width=3, shape='spline')
    ))

    fig.update_xaxes(
        type='category',
        showgrid=False,
        title_text='Hora',
        tickfont=dict(size=12, color='white'),
        title_font=dict(size=13, color='white')
    )
    fig.update_yaxes(
        showgrid=False,
        showticklabels=False,
        title_text=None,
    )

    fig.update_layout(
        title_text=f'{area.upper()}',
        title_x=0,
        title_y=0.97,
        title_font=dict(size=14, color='orange', family='Arial Black'),
        font=dict(size=13, color='white', family='Arial'),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        barmode='overlay',
        # ✅ arredondar todas as barras do gráfico
        barcornerradius=12,  # funciona com Plotly >= 5.19
        margin=dict(l=40, r=20, t=80, b=40),  # topo maior por causa do texto -90°
        uniformtext=dict(minsize=13, mode='show'),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, theme=None, key=f"acumulado_chart_{area}")

def grafico_hora_a_hora(df, area):
    cores_hora = []
    for r, m in zip(df["Realizado Hora"], df["Meta Planejada"]):
        if (str(r).strip() != '' and str(m).strip() != ''):
            cores_hora.append("#46bdc6" if float(r) >= float(m) else "#FF4C4C")
        else:
            cores_hora.append("#888888")

    fig_hora = go.Figure()

    fig_hora.add_trace(go.Bar(
        x=df['Hora'],
        y=df['Realizado Hora'],
        name='Realizado Hora',
        marker=dict(
            color=cores_hora,
            cornerradius=8
        ),
        text=df['Realizado Hora'],
        texttemplate='%{text:.0f}',
        textposition='outside',
        textangle=-90,
        textfont=dict(size=13, color='white', family='Arial'),
        cliponaxis=False
    ))

    fig_hora.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Meta Planejada'],
        name='Meta Planejada',
        mode='lines',
        line=dict(color='lime', width=3, shape='spline')
    ))

    y_realizado = pd.to_numeric(df['Realizado Hora'], errors='coerce')
    y_meta = pd.to_numeric(df['Meta Planejada'], errors='coerce')
    max_realizado = 0 if pd.isna(y_realizado.max()) else y_realizado.max()
    max_meta = 0 if pd.isna(y_meta.max()) else y_meta.max()
    max_val = max(max_realizado, max_meta)
    limite_superior = max_val * 1.10 if max_val > 0 else 1  # ✅ 10% de “respiro”

    fig_hora.update_layout(
        title_text=area.upper(),
        title_x=0,
        title_font=dict(size=14, color='orange', family='Arial Black'),
        font=dict(size=13, color='white', family='Arial'),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        barmode='overlay',
        barcornerradius=12,  # ✅ global
        margin=dict(l=40, r=20, t=80, b=40),
        uniformtext=dict(minsize=13, mode='show'),
        showlegend=False
    )

    fig_hora.update_xaxes(type='category', showgrid=False, title_text='Hora')
    fig_hora.update_yaxes(
        showgrid=False,
        showticklabels=False,
        title_text=None,
        range=[0, limite_superior]
    )

    st.plotly_chart(fig_hora, use_container_width=True, theme=None, key=f"hora_chart_{area}")

# --- INÍCIO DA APLICAÇÃO ---

df = carregar_dados(url_csv)

#st.header("Black Friday ")

tab1, tab2 = st.tabs(["📊 Dashboard Acumulado", "📈 Dashboard Hora a Hora"])

with tab1:
    st.header("📊 Produtividade Inbound :blue[Acumulado]:")

    areas = {
        'Packing AutoStore': df[df['Área'] == 'Packing Autostore'].copy(),
        'Picking AutoStore': df[df['Área'] == 'Picking Autostore'].copy(),
        'Shipping': df[df['Área'] == 'Shipping'].copy(),
        'Packing MR': df[df['Área'] == 'Packing MR'].copy(),
        'Consolidação MR': df[df['Área'] == 'Consolidação MR'].copy(),
    }

    with st.container():
        area_items = list(areas.items())
        for i in range(0, len(area_items), 3):
            cols = st.columns(3)
            for j, (nome_area, df_area) in enumerate(area_items[i:i+3]):
                with cols[j]:
                    with st.container(border=True):
                        total_realizado = pd.to_numeric(df_area['Realizado Hora'], errors='coerce').sum()
                        total_meta = pd.to_numeric(df_area['Meta Planejada'], errors='coerce').sum()
                        desvio = total_realizado - total_meta
                        delta_formatado = (f'{(desvio/total_meta):.1%}' if total_meta > 0 else None)

                        col_met1, col_met2, col_met3 = st.columns(3)
                        with col_met1:
                            st.metric("Total Realizado (Hora)", f"{total_realizado:.0f}")
                        with col_met2:
                            st.metric("Total Meta (Hora)", f"{total_meta:.0f}")
                        with col_met3:
                            st.metric("Desvio", f"{desvio:.0f}", delta=delta_formatado)

                        st.divider()
                        gerar_grafico_acumulado(df_area, nome_area)

with tab2:
    st.header("📊 Produtividade Inbound :blue[HxH]:")
    #st.markdown("### 🔹 Visão Geral das Áreas")

    areas = {
        'Packing AutoStore': df[df['Área'] == 'Packing Autostore'].copy(),
        'Picking AutoStore': df[df['Área'] == 'Picking Autostore'].copy(),
        'Shipping': df[df['Área'] == 'Shipping'].copy(),
        'Packing MR': df[df['Área'] == 'Packing MR'].copy(),
        'Consolidação MR': df[df['Área'] == 'Consolidação MR'].copy(),
    }

    with st.container():
        area_items = list(areas.items())
        for i in range(0, len(area_items), 3):
            cols = st.columns(3)
            for j, (nome_area, df_area) in enumerate(area_items[i:i+3]):
                with cols[j]:
                    with st.container(border=True):
                        grafico_hora_a_hora(df_area, nome_area)

