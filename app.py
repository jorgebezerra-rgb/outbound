import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # Importar para o gráfico da nova aba

# 🔧 CONFIGURAÇÕES GLOBAIS
st.set_page_config(
    page_title="Dashboard de Desempenho",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL da planilha publicada
url_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQc7pTiScl6n_M9hRk1xrTBPUVdG6jtErnsS3skoZiC-49NdFyQd5D3877D3M4wM8kXf27gZvCjY5vo/pub?gid=390048025&single=true&output=csv"


@st.cache_data(ttl=600)
def carregar_dados(url_csv):
    try:
        df = pd.read_csv(url_csv, thousands='.')

        # Limpeza e conversão
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

        # Substitui todos os NaN por vazio
        df = df.fillna('')

        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()


def gerar_grafico_acumulado(df, area):
    """Função que cria o gráfico de barras/linhas (seu código)."""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {area}.")
        return

    # --- Cores dinâmicas ---
    cores = [
        "#46bdc6" if (str(r).strip() != '' and str(d).strip() != '' and float(r) >= float(d))
        else "#FF4C4C"
        for r, d in zip(df["Realizado Acumulado"], df["Dentro Acumulado"])
    ]

    fig = go.Figure()

    # --- BARRAS ---
    fig.add_trace(go.Bar(
        x=df['Hora'],
        y=df['Realizado Acumulado'],
        name='Realizado Acumulado',
        
        # --- MUDANÇA AQUI ---
        # Trocamos 'marker_color=cores' por 'marker=dict(...)'
        marker=dict(
            color=cores,
            cornerradius=5  # <-- Define o arredondamento
        ),
        # --------------------
        
        text=df['Realizado Acumulado'],
        texttemplate='%{text:.0f}',
        textposition='outside',
        textfont=dict(size=14, color='white', family='Arial'),
        textangle=-90,  # Ângulo do texto
        width=0.8
    ))

    # --- LINHA META ---
    fig.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Meta Acumulada'],
        name='Meta',
        mode='lines',
        line=dict(color='lime', dash='dash', width=3, shape='spline'),
        marker=dict(size=6)
    ))

    # --- LINHA TENDÊNCIA ---
    fig.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Tendência'],
        name='Tendência',
        mode='lines',
        line=dict(color='orange', dash='dot',  width=3, shape='spline')
    ))

    # --- EIXOS ---
    fig.update_xaxes(
        type='category',
        showgrid=False,
        title_text='Hora',
        tickfont=dict(size=12, color='white'),
        title_font=dict(size=13, color='white')
    )
    
    # (Mantém a remoção do eixo Y que fizemos antes)
    fig.update_yaxes(
        showgrid=False,
        showticklabels=False,
        title_text=None,
    )

    # --- LAYOUT ---
    fig.update_layout(
        title_text=f'{area.upper()}',
        title_x=0,
        title_y=0.97,
        title_font=dict(size=14, color='orange', family='Arial Black'),
        font=dict(size=13, color='white', family='Arial'),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        barmode='overlay',
        margin=dict(l=40, r=20, t=60, b=40),
        uniformtext=dict(minsize=13, mode='show'),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, theme=None, key=f"acumulado_chart_{area}")


# (Cole esta função no lugar da sua 'grafico_hora_a_hora' antiga)
# (Cole esta função no lugar da sua 'grafico_hora_a_hora' antiga)
def grafico_hora_a_hora(df, area):
    # 1. Lógica de Cores
    cores_hora = []
    for r, m in zip(df["Realizado Hora"], df["Meta Planejada"]):
        if (str(r).strip() != '' and str(m).strip() != ''):
            if float(r) >= float(m):
                cores_hora.append("#46bdc6") # Verde/Ciano
            else:
                cores_hora.append("#FF4C4C") # Vermelho
        else:
            cores_hora.append("#888888") # Cor neutra

    # 2. Criar a Figura
    fig_hora = go.Figure()

    # 3. Adicionar Barras (Realizado Hora)
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
        textfont=dict(size=13, color='white', family='Arial') 
    ))

    # 4. Adicionar Linha (Meta Planejada)
    fig_hora.add_trace(go.Scatter(
        x=df['Hora'],
        y=df['Meta Planejada'],
        name='Meta Planejada',
        mode='lines',
        line=dict(color='lime', width=3, shape='spline'),
        line_shape='spline' 
    ))

    # --- MUDANÇA (A): CÁLCULO DO EIXO DINÂMICO ---
    # Precisamos converter de volta para numérico, pois o carregar_dados()
    # pode ter transformado 'NaN' em ''
    y_realizado = pd.to_numeric(df['Realizado Hora'], errors='coerce')
    y_meta = pd.to_numeric(df['Meta Planejada'], errors='coerce')

    # Pega o valor máximo das duas colunas, tratando valores vazios
    max_realizado = y_realizado.max()
    max_meta = y_meta.max()

    # Define max_val como 0 se ambas as colunas estiverem vazias ou só tiverem NaN
    if pd.isna(max_realizado): max_realizado = 0
    if pd.isna(max_meta): max_meta = 0
    
    max_val = max(max_realizado, max_meta)

    # Define o limite superior (o "respiro" que você pediu)
    # Adicionei 1500 para garantir um bom espaço, mas pode ser 1000
    limite_superior = max_val + 1500 
    # -----------------------------------------------

    # 5. Configurar Layout
    fig_hora.update_layout(
        title_text=area.upper(),
        title_x=0,
        title_font=dict(size=14, color='orange', family='Arial Black'),
        font=dict(size=13, color='white', family='Arial'),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        barmode='overlay',
        margin=dict(l=40, r=20, t=60, b=40),
        uniformtext=dict(minsize=13, mode='show'), 
        showlegend=False,
        legend=dict(font=dict(color='white'))
    )
    
    # 6. Eixos
    fig_hora.update_xaxes(
        type='category',
        showgrid=False,
        title_text='Hora'
    )
    
    # --- MUDANÇA (B): APLICANDO O EIXO DINÂMICO ---
    fig_hora.update_yaxes(
        showgrid=False,
        showticklabels=False,
        title_text=None,
        range=[0, limite_superior]  # <-- Define o range máximo dinamicamente
    )
    # ---------------------------------------------

    # 7. Mostrar o Gráfico
    st.plotly_chart(fig_hora, use_container_width=True, theme=None, key=f"hora_chart_{area}")

# --- INÍCIO DA APLICAÇÃO ---

# 1. Carrega os dados UMA VEZ
df = carregar_dados(url_csv)

# 2. Cria as Abas (Tabs)
tab1, tab2 = st.tabs(["📊 Dashboard Acumulado", "📈 Dashboard Hora a Hora"])


# 3. Conteúdo da Aba 1 (Seu dashboard principal)
with tab1:
    st.header("📊 Dashboard de Desempenho Acumulado")
    st.markdown("### 🔹 Visão Geral das Áreas")

    areas = {
        'Packing AutoStore': df[df['Área'] == 'Packing Autostore'].copy(),
        'Picking AutoStore': df[df['Área'] == 'Picking Autostore'].copy(),
        'Shipping': df[df['Área'] == 'Shipping'].copy(),
        'Packing MR': df[df['Área'] == 'Packing MR'].copy(),
        'Consolidação MR': df[df['Área'] == 'Consolidação MR'].copy(),
    }

    # 🔹 Mostrar 3 gráficos por linha
    with st.container():
        area_items = list(areas.items())
        for i in range(0, len(area_items), 3):  # grupos de 3
            cols = st.columns(3)
            for j, (nome_area, df_area) in enumerate(area_items[i:i+3]):
                with cols[j]:
                    
                    # --- INÍCIO DA MUDANÇA (CARDS) ---
                    
                    # 1. Calcular os totais
                    # Usamos pd.to_numeric para garantir que ' ' (fillna) virem NaN e sejam somados corretamente
                    total_realizado = pd.to_numeric(df_area['Realizado Hora'], errors='coerce').sum()
                    total_meta = pd.to_numeric(df_area['Meta Planejada'], errors='coerce').sum()

                    desvio = total_realizado - total_meta

                    if total_meta > 0:
                        percentual = (desvio / total_meta)

                        delta_formatado = f'{percentual:.1%}'
                    else:
                        delta_formatado = None

                    # 2. Criar sub-colunas para os cards ficarem lado a lado
                    col_met1, col_met2, col_met3 = st.columns(3)
                    
                    with col_met1:
                        # Usamos :.0f para formatar sem casas decimais
                        st.metric(
                            label="Total Realizado (Hora)", 
                            value=f"{total_realizado:.0f}"
                        )
                    with col_met2:
                        st.metric(
                            label="Total Meta (Hora)", 
                            value=f"{total_meta:.0f}"
                        )
                    with col_met3:
                        st.metric(
                            label="Desvio",
                            value=f"{desvio:.0f}",
                            delta=delta_formatado
                        )
                    
                    # --- FIM DA MUDANÇA ---

                    # 3. Gerar o gráfico (como já estava)
                    gerar_grafico_acumulado(df_area, nome_area)

# 4. Conteúdo da Aba 2 (A nova página)
with tab2:
    # Header corrigido para a Aba 2
    st.header("📊 Dashboard de Desempenho Hora a Hora")
    st.markdown("### 🔹 Visão Geral das Áreas")

    # Filtra os dados (exatamente como na Aba 1)
    areas = {
        'Packing AutoStore': df[df['Área'] == 'Packing Autostore'].copy(),
        'Picking AutoStore': df[df['Área'] == 'Picking Autostore'].copy(),
        'Shipping': df[df['Área'] == 'Shipping'].copy(),
        'Packing MR': df[df['Área'] == 'Packing MR'].copy(),
        'Consolidação MR': df[df['Área'] == 'Consolidação MR'].copy(),
    }

    # 🔹 Mostrar 3 gráficos por linha
    with st.container():
        area_items = list(areas.items())
        for i in range(0, len(area_items), 3):  # grupos de 3
            cols = st.columns(3)
            for j, (nome_area, df_area) in enumerate(area_items[i:i+3]):
                with cols[j]:
                    # Chama a função correta
                    grafico_hora_a_hora(df_area, nome_area)