import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Nomes das Abas Esperadas no Arquivo ---
SHEET_MAPA = "Mapa de Riscos"
SHEET_PLANO = "Plano de Respostas"
SHEET_INDICADORES = "1.1. Plano de Ação"

# --- Nomes das Colunas (Programático) ---
# (Estes são os nomes que esperamos encontrar na LINHA 10 (header=9) do Excel)
COL_OBJETIVO = "objetivo_estrategico"
COL_INICIATIVA = "iniciativa"
COL_ACAO = "acao_estrategica"  # <-- Nossa CHAVE de ligação
COL_IND_TITULO = "ind_titulo"
COL_IND_FORMULA = "ind_formula"
COL_IND_UNIDADE = "ind_unidade"
COL_IND_SIT_INICIAL = "ind_sit_inicial"
COL_IND_VALOR = "ind_valor"
COL_IND_PARAMETRO = "ind_parametro"

# Lista de colunas que vamos extrair da aba de indicadores
INDICADORES_COLS_REQUERIDAS = [
    COL_OBJETIVO, COL_INICIATIVA, COL_ACAO,
    COL_IND_TITULO, COL_IND_FORMULA, COL_IND_UNIDADE,
    COL_IND_SIT_INICIAL, COL_IND_VALOR, COL_IND_PARAMETRO
]
INDICADORES_COLS_FFILL = [COL_OBJETIVO, COL_INICIATIVA, COL_ACAO]

# Colunas dos arquivos de Risco (sem mudança)
mapa_cols = [
    'col_vazia', 'acao_estrategica', 'evento_risco', 'causas', 'consequencias',
    'classificacao', 'gestor_risco', 'gp', 'gi', 'nivel_ri', 'avaliacao_ri',
    'desc_controle', 'nivel_controle', 'avaliacao_controle_ac', 'nivel_rr',
    'avaliacao_rr', 'resposta_risco', 'plano_resposta'
]
plano_cols = [
    'col_vazia', 'acao_estrategica', 'evento_risco', 'causas', 'resposta',
    'o_que', 'quando', 'onde', 'por_que', 'por_quem', 'como', 'custo'
]
# (NOVO) Colunas programáticas para '1.1. Plano de Ação' (28 colunas)
indicadores_cols = [
    'objetivo_estrategico', 'iniciativa', 'acao_estrategica', 'situacao_acao', 'responsavel_acao',  # A-E
    'ind_titulo', 'ind_formula', 'ind_unidade', 'ind_sit_inicial', 'ind_valor', 'ind_parametro',  # F-K
    'mes_01', 'mes_02', 'mes_03', 'mes_04', 'mes_05', 'mes_06',  # L-Q
    'mes_07', 'mes_08', 'mes_09', 'mes_10', 'mes_11', 'mes_12',  # R-W
    'unnamed_23', 'unnamed_24', 'calc_painel', 'unnamed_26', 'unnamed_27'  # X-AB
]

# --- Dicionário de Nomes Amigáveis para Exibição ---
FRIENDLY_NAMES = {
    'acao_estrategica': 'Ação Estratégica',
    'evento_risco': 'Evento de Risco',
    'classificacao': 'Classificação',
    'gestor_risco': 'Gestor de Risco',
    'gp': 'Probabilidade (GP)',
    'gi': 'Impacto (GI)',
    'nivel_ri': 'Nível Risco Inerente (RI)',
    'avaliacao_ri': 'Avaliação Risco Inerente',
    'nivel_rr': 'Nível Risco Residual (RR)',
    'avaliacao_rr': 'Avaliação Risco Residual',
    'causas': 'Causas',
    'consequencias': 'Consequências',
    'desc_controle': 'Descrição dos Controles',
    'nivel_controle': 'Nível do Controle',
    'avaliacao_controle_ac': 'Avaliação do Controle Aceitável',
    'resposta_risco': 'Resposta ao Risco',
    'contagem': 'Contagem de Riscos',
    'plano_resposta': 'Plano de Resposta',
    'o_que': 'O Quê (Ação)', 'quando': 'Quando (Prazo)', 'onde': 'Onde (Local)',
    'por_que': 'Por Quê (Justificativa)', 'por_quem': 'Por Quem (Responsável)',
    'como': 'Como (Detalhamento)', 'custo': 'Custo Estimado',
    # Nomes dos Indicadores
    COL_OBJETIVO: 'Objetivo Estratégico',
    COL_INICIATIVA: 'Iniciativa',
    COL_ACAO: 'Ação Estratégica',
    COL_IND_TITULO: 'Indicador (Título)',
    COL_IND_FORMULA: 'Fórmula',
    COL_IND_UNIDADE: 'Unidade de Medida',
    COL_IND_SIT_INICIAL: 'Situação Inicial',
    COL_IND_VALOR: 'Valor (Meta)',
    COL_IND_PARAMETRO: 'Parâmetro'
}

# --- Paletas de Cores e Categorias ---
RISK_COLORS = {
    'Inaceitável': '#D32F2F', 'Indesejável': '#F57C00',
    'Gerenciável': '#FBC02D', 'Aceitável': '#388E3C'
}
CAT_AVALIACAO = ['Aceitável', 'Gerenciável', 'Indesejável', 'Inaceitável']
CAT_IMPACTO_PROB = [1, 2, 3, 4]
CONTROLES_PESOS = {
    "INEXISTENTE": 1.0, "FRACO": 0.8, "MEDIANO": 0.6,
    "SATISFATÓRIO": 0.4, "FORTE": 0.2
}
CONTROLES_NIVEIS = list(CONTROLES_PESOS.keys())


# ==================================================================
# FUNÇÕES AUXILIARES (CSS, KPIs, CARREGAMENTO DE DADOS)
# ==================================================================

def load_css():
    """ Carrega CSS customizado para os KPIs e Cards de Indicadores. """
    st.markdown("""
        <style>
        .kpi-card {
            background-color: #FFFFFF; border-radius: 8px; padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); border: 1px solid #E0E0E0;
            margin-bottom: 10px;
        }
        .kpi-card h3 { font-size: 1.1rem; font-weight: 600; color: #4F4F4F; margin-bottom: 5px; }
        .kpi-card h1 { font-size: 2.5rem; font-weight: 700; color: #0E6E52; margin: 0; }
        .kpi-card.inaceitavel h1 { color: #D32F2F; }
        .kpi-card .delta { font-size: 1rem; font-weight: 600; color: #388E3C; margin-top: 5px; }
        .kpi-card .delta-negativo { color: #D32F2F; }
        .indicator-card {
            background-color: #F8F9FA; border-radius: 8px; padding: 15px;
            border: 1px solid #E0E0E0; margin-bottom: 10px;
        }
        .indicator-card h5 { font-size: 1.1rem; font-weight: 700; color: #0E6E52; margin-bottom: 10px; }
        .indicator-card p { font-size: 0.95rem; margin-bottom: 5px; }
        .indicator-card strong { color: #333; }
        </style>
    """, unsafe_allow_html=True)


def kpi_card(title, value, class_name=""):
    return f"""<div class="kpi-card {class_name}"><h3>{title}</h3><h1>{value}</h1></div>"""


def kpi_card_with_delta(title, value, delta_value, delta_text, class_name=""):
    delta_class = "delta-negativo" if delta_value > 0 else "delta"
    delta_icon = "▲" if delta_value > 0 else "▼"
    return f"""
    <div class="kpi-card {class_name}">
        <h3>{title}</h3><h1>{value}</h1>
        <div class="{delta_class}">{delta_icon} {delta_value} {delta_text}</div>
    </div>
    """


def load_riscos_data(uploaded_file):
    """ Carrega os dados de Riscos (Mapa e Plano) do arquivo de upload. """
    try:
        df_mapa = pd.read_excel(uploaded_file, sheet_name=SHEET_MAPA, header=9)
        if len(df_mapa.columns) == len(mapa_cols):
            df_mapa.columns = mapa_cols
        else:
            st.error(f"Erro na aba '{SHEET_MAPA}': Estrutura de colunas inesperada.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao ler a aba '{SHEET_MAPA}'. Verifique o nome da aba. Erro: {e}")
        return None, None
    try:
        df_plano = pd.read_excel(uploaded_file, sheet_name=SHEET_PLANO, header=8)
        if len(df_plano.columns) == len(plano_cols):
            df_plano.columns = plano_cols
        else:
            st.error(f"Erro na aba '{SHEET_PLANO}': Estrutura de colunas inesperada.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao ler a aba '{SHEET_PLANO}'. Verifique o nome da aba. Erro: {e}")
        return None, None

    # Limpeza (Riscos)
    df_mapa.drop(columns=['col_vazia'], inplace=True, errors='ignore')
    df_plano.drop(columns=['col_vazia'], inplace=True, errors='ignore')
    df_mapa.dropna(subset=['acao_estrategica'], inplace=True)
    df_plano.dropna(subset=['acao_estrategica'], inplace=True)
    cols_num_mapa = ['gp', 'gi', 'nivel_ri', 'avaliacao_controle_ac', 'nivel_rr']
    for col in cols_num_mapa:
        if col in df_mapa.columns:
            df_mapa[col] = pd.to_numeric(df_mapa[col], errors='coerce')
    df_plano.replace('#REF!', pd.NA, inplace=True)
    df_mapa['acao_estrategica'] = df_mapa['acao_estrategica'].str.strip()
    df_mapa['evento_risco'] = df_mapa['evento_risco'].str.strip()
    df_plano['evento_risco'] = df_plano['evento_risco'].str.strip()
    return df_mapa, df_plano


def load_indicadores_data(uploaded_file):
    """ Carrega e limpa os dados de Indicadores da aba '1.1. Plano de Ação'. """
    try:
        df = pd.read_excel(uploaded_file, sheet_name=SHEET_INDICADORES, header=9)
        if len(df.columns) != len(indicadores_cols):
            st.error(f"Erro na aba '{SHEET_INDICADORES}': Estrutura de colunas inesperada.")
            return None
        df.columns = indicadores_cols
        df_indicadores = df[INDICADORES_COLS_REQUERIDAS].copy()
        df_indicadores[INDICADORES_COLS_FFILL] = df_indicadores[INDICADORES_COLS_FFILL].ffill()
        df_indicadores.dropna(subset=[COL_IND_TITULO], inplace=True)
        df_indicadores[COL_ACAO] = df_indicadores[COL_ACAO].str.strip()
        return df_indicadores
    except Exception as e:
        st.error(f"Erro ao ler a aba '{SHEET_INDICADORES}'. Verifique o nome da aba. Erro: {e}")
        return None


def get_avaliacao_from_nivel(nivel):
    if nivel <= 2:
        return "Aceitável"
    elif nivel <= 6:
        return "Gerenciável"
    elif nivel <= 9:
        return "Indesejável"
    else:
        return "Inaceitável"


def reset_app_state():
    """ Limpa o estado da sessão para voltar à tela inicial. """
    keys_to_delete = ['app_mode', 'df_mapa', 'df_plano', 'df_indicadores']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# ==================================================================
# FUNÇÕES DE RENDERIZAÇÃO DE PÁGINA
# ==================================================================

def render_page_visao_geral(df_mapa):
    st.header("Visão Geral do Portfólio de Riscos")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    total_riscos = len(df_mapa)
    riscos_ri_inaceitavel = len(df_mapa[df_mapa['avaliacao_ri'] == 'Inaceitável'])
    riscos_rr_inaceitavel = len(df_mapa[df_mapa['avaliacao_rr'] == 'Inaceitável'])
    delta_inaceitaveis = riscos_rr_inaceitavel - riscos_ri_inaceitavel
    with kpi_col1: st.markdown(kpi_card("Total de Riscos Mapeados", total_riscos), unsafe_allow_html=True)
    with kpi_col2: st.markdown(kpi_card("Riscos Inerentes 'Inaceitáveis'", riscos_ri_inaceitavel, "inaceitavel"),
                               unsafe_allow_html=True)
    with kpi_col3: st.markdown(
        kpi_card_with_delta("Riscos Residuais 'Inaceitáveis'", riscos_rr_inaceitavel, delta_inaceitaveis,
                            "vs. Risco Inerente", "inaceitavel"), unsafe_allow_html=True)
    st.divider()
    st.subheader("Análise: Risco Inerente (Antes) vs. Risco Residual (Depois)")
    plot_col1, plot_col2, plot_col3 = st.columns(3)
    with plot_col1:
        st.write("**Matriz de Risco (Prob x Impacto)**")
        df_ri_matrix = df_mapa.groupby(['gp', 'gi']).size().reset_index(name='contagem')
        fig_ri = px.density_heatmap(
            df_ri_matrix, x='gi', y='gp', z='contagem', text_auto=True,
            title="Heatmap Risco Inerente (GP x GI)", labels=FRIENDLY_NAMES,
            category_orders={'gi': CAT_IMPACTO_PROB, 'gp': CAT_IMPACTO_PROB},
            color_continuous_scale='YlOrRd'
        )
        fig_ri.update_layout(xaxis_title=FRIENDLY_NAMES['gi'], yaxis_title=FRIENDLY_NAMES['gp'],
                             xaxis=dict(tickmode='linear'), yaxis=dict(tickmode='linear'),
                             margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_ri, use_container_width=True)
    with plot_col2:
        st.write("**Avaliação Inerente (Antes dos Controles)**")
        df_ri = df_mapa['avaliacao_ri'].value_counts().reset_index()
        fig_ri_bar = px.bar(
            df_ri, x='avaliacao_ri', y='count', text_auto=True,
            title="Contagem de Riscos por Avaliação Inerente",
            labels={'avaliacao_ri': FRIENDLY_NAMES['avaliacao_ri'], 'count': FRIENDLY_NAMES['contagem']},
            category_orders={'avaliacao_ri': CAT_AVALIACAO},
            color='avaliacao_ri', color_discrete_map=RISK_COLORS
        )
        fig_ri_bar.update_layout(xaxis_title=FRIENDLY_NAMES['avaliacao_ri'], yaxis_title=FRIENDLY_NAMES['contagem'],
                                 margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
        st.plotly_chart(fig_ri_bar, use_container_width=True)
    with plot_col3:
        st.write("**Avaliação Residual (Depois dos Controles)**")
        df_rr = df_mapa['avaliacao_rr'].value_counts().reset_index()
        fig_rr = px.bar(
            df_rr, x='avaliacao_rr', y='count', text_auto=True,
            title="Contagem de Riscos por Avaliação Residual",
            labels={'avaliacao_rr': FRIENDLY_NAMES['avaliacao_rr'], 'count': FRIENDLY_NAMES['contagem']},
            category_orders={'avaliacao_rr': CAT_AVALIACAO},
            color='avaliacao_rr', color_discrete_map=RISK_COLORS
        )
        fig_rr.update_layout(xaxis_title=FRIENDLY_NAMES['avaliacao_rr'], yaxis_title=FRIENDLY_NAMES['contagem'],
                             margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
        st.plotly_chart(fig_rr, use_container_width=True)
    st.divider()
    st.subheader("Detalhamento dos Riscos")
    plot_col3, plot_col4 = st.columns(2)
    with plot_col3:
        df_class = df_mapa['classificacao'].value_counts().reset_index()
        fig_class = px.bar(
            df_class, x='classificacao', y='count', title="Contagem de Riscos por Classificação",
            labels={'classificacao': FRIENDLY_NAMES['classificacao'], 'count': FRIENDLY_NAMES['contagem']},
            text_auto=True, color_discrete_sequence=['#003366']
        )
        fig_class.update_layout(xaxis_title=FRIENDLY_NAMES['classificacao'], yaxis_title=FRIENDLY_NAMES['contagem'],
                                margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_class, use_container_width=True)
    with plot_col4:
        df_gestor = df_mapa['gestor_risco'].value_counts().reset_index()
        fig_gestor = px.bar(
            df_gestor, x='gestor_risco', y='count', title="Contagem de Riscos por Gestor",
            labels={'gestor_risco': FRIENDLY_NAMES['gestor_risco'], 'count': FRIENDLY_NAMES['contagem']},
            text_auto=True, color_discrete_sequence=['#0E6E52']
        )
        fig_gestor.update_layout(xaxis_title=FRIENDLY_NAMES['gestor_risco'], yaxis_title=FRIENDLY_NAMES['contagem'],
                                 margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_gestor, use_container_width=True)


def render_page_indicadores(df_indicadores, df_mapa):
    st.header("Análise de Indicadores e Riscos por Ação Estratégica")
    st.info(
        "Selecione uma Ação Estratégica para ver os Indicadores de Planejamento e os Riscos de Gestão associados a ela.")
    acoes_riscos = df_mapa['acao_estrategica'].unique()
    acoes_indicadores = df_indicadores[COL_ACAO].unique()
    lista_completa_acoes = sorted(list(set(list(acoes_riscos) + list(acoes_indicadores))))
    acao_selecionada = st.selectbox("Selecione a Ação Estratégica:", lista_completa_acoes)
    st.divider()
    col_ind, col_risc = st.columns(2)
    with col_ind:
        st.subheader("Indicadores de Planejamento")
        indicadores_filtrados = df_indicadores[df_indicadores[COL_ACAO] == acao_selecionada]
        if indicadores_filtrados.empty:
            st.warning("Nenhum indicador de planejamento associado a esta Ação.")
        else:
            st.markdown(f"**{FRIENDLY_NAMES[COL_OBJETIVO]}:** _{indicadores_filtrados.iloc[0][COL_OBJETIVO]}_")
            st.markdown(f"**{FRIENDLY_NAMES[COL_INICIATIVA]}:** _{indicadores_filtrados.iloc[0][COL_INICIATIVA]}_")
            st.write("")
            for _, row in indicadores_filtrados.iterrows():
                st.markdown(
                    f"""
                    <div class="indicator-card">
                        <h5>{row[COL_IND_TITULO]}</h5>
                        <p><strong>{FRIENDLY_NAMES[COL_IND_FORMULA]}:</strong> {row[COL_IND_FORMULA]}</p>
                        <p><strong>{FRIENDLY_NAMES[COL_IND_SIT_INICIAL]}:</strong> {row[COL_IND_SIT_INICIAL]}</p>
                        <p><strong>{FRIENDLY_NAMES[COL_IND_VALOR]}:</strong> {row[COL_IND_VALOR]} ({row[COL_IND_UNIDADE]})</p>
                        <p><strong>{FRIENDLY_NAMES[COL_IND_PARAMETRO]}:</strong> {row[COL_IND_PARAMETRO]}</p>
                    </div>
                    """, unsafe_allow_html=True)
    with col_risc:
        st.subheader("Riscos de Gestão")
        riscos_filtrados = df_mapa[df_mapa['acao_estrategica'] == acao_selecionada]
        if riscos_filtrados.empty:
            st.warning("Nenhum risco de gestão associado a esta Ação.")
        else:
            for _, row in riscos_filtrados.iterrows():
                aval_rr = row['avaliacao_rr']
                if aval_rr == 'Inaceitável':
                    st.error(f"**Risco:** {row['evento_risco']}")
                elif aval_rr == 'Indesejável':
                    st.warning(f"**Risco:** {row['evento_risco']}")
                elif aval_rr == 'Gerenciável':
                    st.info(f"**Risco:** {row['evento_risco']}")
                else:
                    st.success(f"**Risco:** {row['evento_risco']}")
                with st.expander("Ver detalhes do risco"):
                    st.markdown(f"**Causas:** {row['causas']}")
                    st.markdown(f"**Consequências:** {row['consequencias']}")
                    st.markdown(f"**Risco Inerente:** {row['nivel_ri']} ({row['avaliacao_ri']})")
                    st.markdown(f"**Risco Residual:** {row['nivel_rr']:.1f} ({row['avaliacao_rr']})")
                    st.markdown(f"**Controle Existente:** {row['desc_controle']} (`{row['nivel_controle']}`)")
                st.write("")


def render_page_ficha_individual(df_mapa, df_plano):
    st.header("Ficha Individual do Risco")
    st.info("Selecione um evento de risco para ver seu perfil completo, desde a identificação até o plano de resposta.")
    lista_riscos_completa = df_mapa['evento_risco'].unique().tolist()
    risco_selecionado = st.selectbox("Selecione um Evento de Risco para ver seu perfil:", lista_riscos_completa,
                                     index=0)
    risco_data = df_mapa[df_mapa['evento_risco'] == risco_selecionado].iloc[0]
    plano_data = df_plano[df_plano['evento_risco'] == risco_selecionado]
    st.divider()
    with st.container(border=True):
        st.subheader(f"1. Identificação do Risco")
        st.markdown(f"#### {risco_data['evento_risco']}")
        st.markdown(f"**{FRIENDLY_NAMES['acao_estrategica']}:** _{risco_data['acao_estrategica']}_")
        id_col1, id_col2 = st.columns(2)
        with id_col1:
            st.markdown(f"**{FRIENDLY_NAMES['classificacao']}:** `{risco_data['classificacao']}`")
            st.markdown(f"**{FRIENDLY_NAMES['gestor_risco']}:** `{risco_data['gestor_risco']}`")
        with id_col2:
            st.markdown(f"**{FRIENDLY_NAMES['causas']}:** _{risco_data['causas']}_")
            st.markdown(f"**{FRIENDLY_NAMES['consequencias']}:** _{risco_data['consequencias']}_")
    st.write("")
    with st.container(border=True):
        st.subheader("2. Análise e Avaliação")
        eval_col1, eval_col2, eval_col3 = st.columns(3)
        with eval_col1:
            st.markdown("##### Risco Inerente (RI)")
            aval_ri = risco_data['avaliacao_ri']
            nivel_ri = risco_data['nivel_ri']
            if aval_ri == 'Inaceitável':
                st.error(f"### {nivel_ri} ({aval_ri})")
            elif aval_ri == 'Indesejável':
                st.warning(f"### {nivel_ri} ({aval_ri})")
            elif aval_ri == 'Gerenciável':
                st.info(f"### {nivel_ri} ({aval_ri})")
            else:
                st.success(f"### {nivel_ri} ({aval_ri})")
            st.markdown(f"**{FRIENDLY_NAMES['gp']}:** `{risco_data['gp']}`")
            st.markdown(f"**{FRIENDLY_NAMES['gi']}:** `{risco_data['gi']}`")
        with eval_col2:
            st.markdown("##### Controles Existentes")
            st.markdown(f"**Descrição:**")
            st.markdown(f"_{risco_data['desc_controle']}_")
            st.markdown(f"**Nível:** `{risco_data['nivel_controle']}` (Peso: `{risco_data['avaliacao_controle_ac']}`)")
        with eval_col3:
            st.markdown("##### Risco Residual (RR)")
            aval_rr = risco_data['avaliacao_rr']
            nivel_rr = risco_data['nivel_rr']
            if aval_rr == 'Inaceitável':
                st.error(f"### {nivel_rr:.1f} ({aval_rr})")
            elif aval_rr == 'Indesejável':
                st.warning(f"### {nivel_rr:.1f} ({aval_rr})")
            elif aval_rr == 'Gerenciável':
                st.info(f"### {nivel_rr:.1f} ({aval_rr})")
            else:
                st.success(f"### {nivel_rr:.1f} ({aval_rr})")
            st.markdown(f"**Resposta ao Risco:** `{risco_data['resposta_risco']}`")
    st.write("")
    with st.container(border=True):
        st.subheader("3. Plano de Resposta (Tratamento)")
        if plano_data.empty or risco_data['plano_resposta'] == 'Não':
            st.warning("Este risco não possui um plano de resposta detalhado cadastrado.")
        else:
            plano = plano_data.iloc[0]
            st.info(f"**Detalhes do plano para '{plano['resposta']}' o risco:**")
            plan_col1, plan_col2 = st.columns(2)
            with plan_col1:
                st.markdown(f"**{FRIENDLY_NAMES['o_que']}:**\n_{plano['o_que']}_")
                st.markdown(f"**{FRIENDLY_NAMES['por_quem']}:**\n_{plano['por_quem']}_")
                st.markdown(f"**{FRIENDLY_NAMES['quando']}:**\n_{plano['quando']}_")
                st.markdown(f"**{FRIENDLY_NAMES['onde']}:**\n_{plano['onde']}_")
            with plan_col2:
                st.markdown(f"**{FRIENDLY_NAMES['por_que']}:**\n_{plano['por_que']}_")
                st.markdown(f"**{FRIENDLY_NAMES['como']}:**\n_{plano['como']}_")
                st.markdown(f"**{FRIENDLY_NAMES['custo']}:**\n_{plano['custo']}_")


def render_page_simulador(df_mapa):
    st.header("Simulador de Eficácia dos Controles")
    st.info("Esta ferramenta permite simular o impacto da melhoria de um controle sobre o Risco Residual. (...)")
    lista_riscos_completa = df_mapa['evento_risco'].unique().tolist()
    risco_selecionado = st.selectbox("Selecione um Evento de Risco para simular:", lista_riscos_completa)
    risco_data = df_mapa[df_mapa['evento_risco'] == risco_selecionado].iloc[0]
    nivel_ri_fixo = risco_data['nivel_ri']
    aval_ri_fixa = risco_data['avaliacao_ri']
    nivel_controle_original = risco_data['nivel_controle']
    ac_original = risco_data['avaliacao_controle_ac']
    nivel_rr_original = risco_data['nivel_rr']
    aval_rr_original = risco_data['avaliacao_rr']
    st.divider()
    sim_col1, sim_col2 = st.columns([1, 2])
    with sim_col1:
        st.subheader("Dados Iniciais")
        st.metric(label=f"Risco Inerente (RI) - Fixo", value=f"{nivel_ri_fixo} ({aval_ri_fixa})")
        st.markdown(f"### Risco Residual Original (RR)")
        if aval_rr_original == 'Inaceitável':
            st.error(f"## {nivel_rr_original:.1f} ({aval_rr_original})")
        elif aval_rr_original == 'Indesejável':
            st.warning(f"## {nivel_rr_original:.1f} ({aval_rr_original})")
        elif aval_rr_original == 'Gerenciável':
            st.info(f"## {nivel_rr_original:.1f} ({aval_rr_original})")
        else:
            st.success(f"## {nivel_rr_original:.1f} ({aval_rr_original})")
        st.caption(f"Baseado no controle original: '{nivel_controle_original}' (Peso: {ac_original})")
    with sim_col2:
        st.subheader("Simulação")
        nivel_controle_simulado = st.select_slider("Arraste para simular um novo Nível de Controle:",
                                                   options=CONTROLES_NIVEIS, value=nivel_controle_original)
        ac_simulado = CONTROLES_PESOS[nivel_controle_simulado]
        nivel_rr_simulado = nivel_ri_fixo * ac_simulado
        aval_rr_simulada = get_avaliacao_from_nivel(nivel_rr_simulado)
        st.markdown(f"### Novo Risco Residual (Simulado)")
        if aval_rr_simulada == 'Inaceitável':
            st.error(f"## {nivel_rr_simulado:.1f} ({aval_rr_simulada})")
        elif aval_rr_simulada == 'Indesejável':
            st.warning(f"## {nivel_rr_simulado:.1f} ({aval_rr_simulada})")
        elif aval_rr_simulada == 'Gerenciável':
            st.info(f"## {nivel_rr_simulado:.1f} ({aval_rr_simulada})")
        else:
            st.success(f"## {nivel_rr_simulado:.1f} ({aval_rr_simulada})")
        st.caption(f"Cálculo: {nivel_ri_fixo} (RI) × {ac_simulado} (Peso de '{nivel_controle_simulado}')")
    st.divider()
    st.write(f"**Descrição do Risco:** {risco_data['evento_risco']}")
    st.write(f"**Causas:** {risco_data['causas']}")
    st.write(f"**Controle Original Descrito:** {risco_data['desc_controle']}")


def render_page_analise_detalhada(df_mapa, df_plano):
    st.header("Análise Detalhada (Tabelas)")
    st.subheader("Filtros de Riscos")
    lista_acoes = ['Todas'] + df_mapa['acao_estrategica'].unique().tolist()
    lista_gestores = ['Todos'] + df_mapa['gestor_risco'].unique().tolist()
    lista_avaliacoes = ['Todas'] + CAT_AVALIACAO
    filt_col1, filt_col2, filt_col3 = st.columns(3)
    with filt_col1:
        filtro_acao = st.selectbox("Filtrar por Ação Estratégica:", lista_acoes)
    with filt_col2:
        filtro_gestor = st.selectbox("Filtrar por Gestor:", lista_gestores)
    with filt_col3:
        filtro_aval_rr = st.selectbox("Filtrar por Avaliação Residual:", lista_avaliacoes)
    st.divider()
    st.subheader("Mapa de Riscos Filtrado")
    df_mapa_filtrado = df_mapa.copy()
    if filtro_acao != 'Todas': df_mapa_filtrado = df_mapa_filtrado[df_mapa_filtrado['acao_estrategica'] == filtro_acao]
    if filtro_gestor != 'Todos': df_mapa_filtrado = df_mapa_filtrado[df_mapa_filtrado['gestor_risco'] == filtro_gestor]
    if filtro_aval_rr != 'Todas': df_mapa_filtrado = df_mapa_filtrado[
        df_mapa_filtrado['avaliacao_rr'] == filtro_aval_rr]
    st.dataframe(df_mapa_filtrado.rename(columns=FRIENDLY_NAMES))
    st.divider()
    st.subheader("Detalhamento do Plano de Resposta (Drill-Down)")
    lista_riscos_filtrados = df_mapa_filtrado['evento_risco'].unique().tolist()
    if not lista_riscos_filtrados:
        st.warning("Nenhum risco encontrado para os filtros selecionados.")
    else:
        risco_selecionado = st.selectbox("Selecione o Evento de Risco para ver o Plano de Resposta:",
                                         lista_riscos_filtrados)
        plano_selecionado = df_plano[df_plano['evento_risco'] == risco_selecionado]
        if plano_selecionado.empty:
            st.error(f"Plano de resposta não encontrado para o risco: '{risco_selecionado}'")
        else:
            plano = plano_selecionado.iloc[0]
            st.info(f"**Plano de Resposta para:** {plano['evento_risco']}")
            plan_col1, plan_col2 = st.columns(2)
            with plan_col1:
                st.markdown(f"**{FRIENDLY_NAMES['o_que']}:**\n_{plano['o_que']}_")
                st.markdown(f"**{FRIENDLY_NAMES['por_quem']}:**\n_{plano['por_quem']}_")
                st.markdown(f"**{FRIENDLY_NAMES['quando']}:**\n_{plano['quando']}_")
            with plan_col2:
                st.markdown(f"**{FRIENDLY_NAMES['como']}:**\n_{plano['como']}_")
                st.markdown(f"**{FRIENDLY_NAMES['custo']}:**\n_{plano['custo']}_")


# ==================================================================
# LÓGICA PRINCIPAL DO APP (ROTEADOR)
# ==================================================================

# --- Configuração Inicial da Página ---
st.set_page_config(
    page_title="Painel de Gestão de Riscos",
    page_icon="📊",
    layout="wide"
)
load_css()
st.title("Painel de Análise de Riscos e Indicadores")

# --- ETAPA 1: Seleção de Modo ---
if 'app_mode' not in st.session_state:
    st.header("Selecione o Modo de Análise")
    st.info("Escolha como você deseja analisar os dados.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Análise de Riscos (Padrão)", use_container_width=True):
            st.session_state.app_mode = 'risk_only'
            st.rerun()
    with col2:
        if st.button("📈 Análise Integrada (Riscos + Indicadores)", use_container_width=True):
            st.session_state.app_mode = 'integrated'
            st.rerun()

    st.stop()  # Para a execução até que um modo seja escolhido

# --- ETAPA 2: Carregamento de Dados (Baseado no Modo) ---
# Esta etapa só é executada se o 'app_mode' foi definido
app_mode = st.session_state.app_mode

# Verifica se os dados necessários para o modo já foram carregados
data_loaded = 'df_mapa' in st.session_state

if not data_loaded:
    st.header("Carregamento de Arquivos")

    if app_mode == 'risk_only':
        st.info("Por favor, carregue o arquivo de Gestão de Riscos.")
        uploader_riscos = st.file_uploader(
            "Arquivo de Gestão de Riscos",
            type=["xlsx"],
            help=f"Deve conter as abas '{SHEET_MAPA}' e '{SHEET_PLANO}'"
        )

        if uploader_riscos is None:
            st.stop()

        df_mapa, df_plano = load_riscos_data(uploader_riscos)

        if df_mapa is not None and df_plano is not None:
            st.session_state.df_mapa = df_mapa
            st.session_state.df_plano = df_plano
            st.rerun()
        else:
            st.stop()

    elif app_mode == 'integrated':
        st.info("Por favor, carregue os dois arquivos .xlsx para iniciar o painel.")
        col1, col2 = st.columns(2)
        with col1:
            uploader_riscos = st.file_uploader(
                "1. Arquivo de Gestão de Riscos",
                type=["xlsx"],
                help=f"Deve conter as abas '{SHEET_MAPA}' e '{SHEET_PLANO}'"
            )
        with col2:
            uploader_planejamento = st.file_uploader(
                "2. Arquivo de Planejamento Estratégico",
                type=["xlsx"],
                help=f"Deve conter a aba '{SHEET_INDICADORES}'"
            )

        if uploader_riscos is None or uploader_planejamento is None:
            st.stop()

        df_mapa, df_plano = load_riscos_data(uploader_riscos)
        df_indicadores = load_indicadores_data(uploader_planejamento)

        if df_mapa is not None and df_plano is not None and df_indicadores is not None:
            st.session_state.df_mapa = df_mapa
            st.session_state.df_plano = df_plano
            st.session_state.df_indicadores = df_indicadores
            st.rerun()
        else:
            st.error("Falha no carregamento de um ou mais arquivos. Verifique os erros acima.")
            st.stop()

# --- ETAPA 3: Exibição do Aplicativo (Dados Carregados) ---
# O script só chega aqui se o modo está definido E os dados estão carregados

# Recupera os dados do estado
df_mapa = st.session_state.df_mapa
df_plano = st.session_state.df_plano
if app_mode == 'integrated':
    df_indicadores = st.session_state.df_indicadores

# Monta a Sidebar
st.sidebar.image("risk.jpg", use_container_width=True)
st.sidebar.title("Navegação")

# Define a lista de páginas com base no modo
if app_mode == 'risk_only':
    page_list = [
        "Visão Geral (Dashboard)",
        "Ficha Individual do Risco",
        "Simulador de Controles",
        "Análise Detalhada (Tabelas)"
    ]
else:  # modo 'integrated'
    page_list = [
        "Visão Geral (Dashboard)",
        "Análise de Indicadores",
        "Ficha Individual do Risco",
        "Simulador de Controles",
        "Análise Detalhada (Tabelas)"
    ]

page = st.sidebar.radio("Selecione a página:", page_list)
st.sidebar.divider()
st.sidebar.button("Mudar Modo / Novos Arquivos", on_click=reset_app_state, use_container_width=True)
st.sidebar.divider()
st.sidebar.info(
    """
    **Bem-vindo ao Painel de Riscos!**
    Esta ferramenta transforma suas planilhas em um dashboard interativo.
    **Instruções para Iniciar:**
    1.  Tenha seu(s) arquivo(s) `.xlsx` prontos.
    2.  Verifique se os nomes das abas e colunas 
        seguem o template original.
    """
)

# Roteador de Páginas
if page == "Visão Geral (Dashboard)":
    render_page_visao_geral(df_mapa)

elif page == "Análise de Indicadores":
    render_page_indicadores(df_indicadores, df_mapa)

elif page == "Ficha Individual do Risco":
    render_page_ficha_individual(df_mapa, df_plano)

elif page == "Simulador de Controles":
    render_page_simulador(df_mapa)

elif page == "Análise Detalhada (Tabelas)":
    render_page_analise_detalhada(df_mapa, df_plano)
    

