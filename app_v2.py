import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Nomes das Abas Esperadas no Arquivo ---
SHEET_MAPA = "Mapa de Riscos"
SHEET_PLANO = "Plano de Respostas"

# --- Nomes das Colunas (Programático) ---
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
    # Nomes do Plano de Ação
    'o_que': 'O Quê (Ação)',
    'quando': 'Quando (Prazo)',
    'onde': 'Onde (Local)',
    'por_que': 'Por Quê (Justificativa)',
    'por_quem': 'Por Quem (Responsável)',
    'como': 'Como (Detalhamento)',
    'custo': 'Custo Estimado'
}

# --- Paletas de Cores ---
RISK_COLORS = {
    'Inaceitável': '#D32F2F', 'Indesejável': '#F57C00',
    'Gerenciável': '#FBC02D', 'Aceitável': '#388E3C'
}
CHART_PALETTE = ['#0E6E52', '#008080', '#69A8A0', '#A9C4C0', '#D3D3D3']

# --- Ordem das Categorias (para gráficos) ---
CAT_AVALIACAO = ['Aceitável', 'Gerenciável', 'Indesejável', 'Inaceitável']
CAT_IMPACTO_PROB = [1, 2, 3, 4]

# --- Mapeamento de Controles e Pesos ---
CONTROLES_PESOS = {
    "INEXISTENTE": 1.0, "FRACO": 0.8, "MEDIANO": 0.6,
    "SATISFATÓRIO": 0.4, "FORTE": 0.2
}
CONTROLES_NIVEIS = list(CONTROLES_PESOS.keys())


# --- Função para injetar CSS ---
def load_css():
    """ Carrega CSS customizado para os KPIs. """
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
        </style>
    """, unsafe_allow_html=True)


# --- Função para criar KPI Card ---
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


# --- (MODIFICADA) Função de Carregamento de Dados ---
# @st.cache_data # Cache é bom, mas vamos simplificar para o st.session_state
def load_data(uploaded_file):
    """
    Carrega e limpa os dados a partir de um ARQUIVO DE UPLOAD
    com duas abas específicas.
    """
    try:
        df_mapa = pd.read_excel(uploaded_file, sheet_name=SHEET_MAPA, header=9)
        if len(df_mapa.columns) == len(mapa_cols):
            df_mapa.columns = mapa_cols
        else:
            st.error(
                f"Erro na aba '{SHEET_MAPA}': Esperava {len(mapa_cols)} colunas, mas encontrou {len(df_mapa.columns)}.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao ler a aba '{SHEET_MAPA}' do arquivo. Verifique o nome da aba e o formato. Erro: {e}")
        return None, None
    try:
        df_plano = pd.read_excel(uploaded_file, sheet_name=SHEET_PLANO, header=8)
        if len(df_plano.columns) == len(plano_cols):
            df_plano.columns = plano_cols
        else:
            st.error(
                f"Erro na aba '{SHEET_PLANO}': Esperava {len(plano_cols)} colunas, mas encontrou {len(df_plano.columns)}.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao ler a aba '{SHEET_PLANO}' do arquivo. Verifique o nome da aba e o formato. Erro: {e}")
        return None, None

    # Limpeza
    df_mapa.drop(columns=['col_vazia'], inplace=True, errors='ignore')
    df_plano.drop(columns=['col_vazia'], inplace=True, errors='ignore')
    df_mapa.dropna(subset=['acao_estrategica'], inplace=True)
    df_plano.dropna(subset=['acao_estrategica'], inplace=True)
    cols_num_mapa = ['gp', 'gi', 'nivel_ri', 'avaliacao_controle_ac', 'nivel_rr']
    for col in cols_num_mapa:
        if col in df_mapa.columns:
            df_mapa[col] = pd.to_numeric(df_mapa[col], errors='coerce')
    df_plano.replace('#REF!', pd.NA, inplace=True)
    df_mapa['evento_risco'] = df_mapa['evento_risco'].str.strip()
    df_plano['evento_risco'] = df_plano['evento_risco'].str.strip()
    return df_mapa, df_plano


# --- Função Helper para Avaliação ---
def get_avaliacao_from_nivel(nivel):
    if nivel <= 2:
        return "Aceitável"
    elif nivel <= 6:
        return "Gerenciável"
    elif nivel <= 9:
        return "Indesejável"
    else:
        return "Inaceitável"


# --- Configuração da Página ---
st.set_page_config(
    page_title="Painel de Gestão de Riscos",
    page_icon="📊",
    layout="wide"
)
load_css()
st.title("Painel de Gestão de Riscos Estratégicos")
st.write("*Exercício da disciplina de Gestão Estratégica de Riscos*")

# --- (NOVA LÓGICA) Gerenciamento de Estado e Upload ---

# 1. Verifica se os dados NÃO estão no estado da sessão
if "df_mapa" not in st.session_state or "df_plano" not in st.session_state:

    # Mostra o uploader
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo Excel (template de riscos)",
        type=["xlsx"],
        help="O arquivo deve conter as abas 'Mapa de Riscos' e 'Plano de Respostas'"
    )

    if uploaded_file is None:
        st.info("ℹ️ Por favor, faça o upload do arquivo .xlsx de Gestão de Riscos para iniciar o painel.")
        st.stop()  # Para a execução até o upload

    # Se o arquivo foi enviado, tenta carregar e salvar no estado
    df_mapa, df_plano = load_data(uploaded_file)

    if df_mapa is not None and df_plano is not None:
        # Sucesso! Armazena no estado da sessão
        st.session_state.df_mapa = df_mapa
        st.session_state.df_plano = df_plano
        st.rerun()  # Força o script a rodar novamente
    else:
        # load_data() falhou e já exibiu um st.error()
        st.stop()  # Para aqui

# 2. Se os dados JÁ ESTÃO no estado, apenas os recupera
# Esta parte só roda se o if acima for FALSO (ou seja, os dados existem)
df_mapa = st.session_state.df_mapa
df_plano = st.session_state.df_plano

# --- Início da Aplicação (só executa se os dados foram carregados) ---

# --- Barra Lateral de Navegação ---
st.sidebar.image("risk.jpg", use_container_width=True)
st.sidebar.title("Navegação")
page = st.sidebar.radio("Selecione a página:",
                        [
                            "Visão Geral (Dashboard)",
                            "Ficha Individual do Risco",
                            "Simulador de Controles",
                            "Análise Detalhada e Planos de Ação"
                        ])

# --- (NOVO) Botão para Resetar ---
st.sidebar.divider()
if st.sidebar.button("Carregar Novo Arquivo"):
    # Limpa os dados do estado da sessão
    del st.session_state.df_mapa
    del st.session_state.df_plano
    st.rerun()  # Roda o script de novo, o que fará o uploader aparecer

st.sidebar.divider()
st.sidebar.warning(
    """
        **Bem-vindo ao Painel de Riscos!**

        Esta ferramenta transforma sua planilha de Gestão de Riscos 
        em um dashboard interativo.

        **Instruções para Iniciar:**
        1.  Tenha seu arquivo `.xlsx` pronto.
        2.  O arquivo **deve** conter exatamente as abas:
            * `Mapa de Riscos`
            * `Plano de Respostas`
        3.  A estrutura das colunas deve seguir o template original 
            para o qual este painel foi projetado.
        4.  Carregue o arquivo na tela principal para começar.
        """
)  # Mensagem de aviso!

# =================================================
# PÁGINA 1: VISÃO GERAL (Dashboard)
# =================================================
if page == "Visão Geral (Dashboard)":

    # ... (CÓDIGO DA PÁGINA 1 - IDÊNTICO) ...
    st.header("Visão Geral do Portfólio de Riscos")
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    total_riscos = len(df_mapa)
    riscos_ri_inaceitavel = len(df_mapa[df_mapa['avaliacao_ri'] == 'Inaceitável'])
    riscos_rr_inaceitavel = len(df_mapa[df_mapa['avaliacao_rr'] == 'Inaceitável'])
    delta_inaceitaveis = riscos_rr_inaceitavel - riscos_ri_inaceitavel
    with kpi_col1:
        st.markdown(kpi_card("Total de Riscos Mapeados", total_riscos), unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(kpi_card("Riscos Inerentes 'Inaceitáveis'", riscos_ri_inaceitavel, "inaceitavel"),
                    unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(kpi_card_with_delta("Riscos Residuais 'Inaceitáveis'", riscos_rr_inaceitavel, delta_inaceitaveis,
                                        "vs. Risco Inerente", "inaceitavel"), unsafe_allow_html=True)
    st.divider()
    st.subheader("Análise: Risco Inerente (Antes) vs. Risco Residual (Depois)")
    plot_col1, plot_col2 = st.columns(2)
    with plot_col1:
        st.write("**Matriz de Risco Inerente (Antes dos Controles)**")
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
        st.write("**Avaliação do Risco Residual (Depois dos Contles)**")
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
            text_auto=True, color_discrete_sequence=['#616161']
        )
        fig_class.update_layout(xaxis_title=FRIENDLY_NAMES['classificacao'], yaxis_title=FRIENDLY_NAMES['contagem'],
                                margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_class, use_container_width=True)
    with plot_col4:
        df_gestor = df_mapa['gestor_risco'].value_counts().reset_index()
        fig_gestor = px.bar(
            df_gestor, x='gestor_risco', y='count', title="Contagem de Riscos por Gestor",
            labels={'gestor_risco': FRIENDLY_NAMES['gestor_risco'], 'count': FRIENDLY_NAMES['contagem']},
            text_auto=True, color_discrete_sequence=['#616161']
        )
        fig_gestor.update_layout(xaxis_title=FRIENDLY_NAMES['gestor_risco'], yaxis_title=FRIENDLY_NAMES['contagem'],
                                 margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_gestor, use_container_width=True)

# =================================================
# PÁGINA 2: FICHA INDIVIDUAL DO RISCO
# =================================================
elif page == "Ficha Individual do Risco":

    # ... (CÓDIGO DA PÁGINA 2 - IDÊNTICO) ...
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
            st.warning("Este risco não possui um plano de resposta detalhado cadastrado (Plano de Resposta = Não).")
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

# =================================================
# PÁGINA 3: SIMULADOR DE CONTROLES
# =================================================
elif page == "Simulador de Controles":

    # ... (CÓDIGO DA PÁGINA 3 - IDÊNTICO) ...
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

# =================================================
# PÁGINA 4: ANÁLISE DETALHADA
# =================================================
elif page == "Análise Detalhada e Planos de Ação":

    # ... (CÓDIGO DA PÁGINA 4 - IDÊNTICO) ...
    st.header("Análise Detalhada e Planos de Resposta")
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

# Mensagem de erro final
else:
    # Esta mensagem só aparecerá se o arquivo for carregado mas falhar na validação
    st.error(
        "ERRO CRÍTICO: Não foi possível processar os dataframes. Verifique o conteúdo do arquivo e os nomes das abas.")