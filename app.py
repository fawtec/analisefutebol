"""
Analisador de Futebol de Formação
Uma aplicação Streamlit para análise técnica de partidas de futebol de base
Autor: Sistema desenvolvido para análise de desempenho
Versão: 2.0 - Arquitetura Limpa
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional

# Importações locais
from adversarios import GerenciadorAdversarios
from models import (
    EstatisticasTime, EstatisticasJogo, ContextoAdversario,
    AvaliacaoFase, AvaliacaoModelo, Jogo, ModeloJogo
)
from analytics import (
    indice_desenvolvimento, calcular_metricas_jogo, calcular_dominio
)
from storage import salvar_jogos, carregar_jogos
from utils import gerar_id

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

st.set_page_config(
    page_title="Analisador Futebol Formação",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhor visualização
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #1f77b4;
    }
    .metric-card-adversario {
        border-left: 5px solid #ff4b4b;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .title-team {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# =============================================================================

def inicializar_sessao():
    """Inicializa todas as variáveis de sessão necessárias"""
    # 🔥 NOME DO CLUBE
    if "nome_clube" not in st.session_state:
        st.session_state.nome_clube = "Meu Time"
    
    if "gerenciador_adv" not in st.session_state:
        st.session_state.gerenciador_adv = GerenciadorAdversarios()
    
    if "jogos" not in st.session_state:
        st.session_state.jogos = carregar_jogos()

    if "modelos" not in st.session_state:
        st.session_state.modelos = [
            ModeloJogo("Posse de Bola", 5, "Controle do jogo com passes curtos"),
            ModeloJogo("Contra-ataque", 3, "Explorar velocidade nos contra-golpes"),
            ModeloJogo("Pressão Alta", 4, "Marcar subindo, recuperar bola rápido"),
            ModeloJogo("Transição Rápida", 4, "Saída rápida ao ataque após recuperação"),
        ]

# =============================================================================
# COMPONENTES DA INTERFACE
# =============================================================================

def sidebar_menu() -> str:
    """Renderiza o menu lateral e retorna a opção selecionada"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/football2.png", width=80)
        
        # 🔥 INPUT DO NOME DO CLUBE
        nome_clube = st.text_input(
            "🏆 Nome do Clube:",
            value=st.session_state.nome_clube,
            key="input_nome_clube"
        )
        
        # Atualizar session state
        if nome_clube != st.session_state.nome_clube:
            st.session_state.nome_clube = nome_clube
        
        st.markdown(f"### {st.session_state.nome_clube}")
        st.divider()
        
        menu = st.radio(
            "Navegação:",
            ["📝 Registrar Jogo", 
             "📊 Análise do Jogo", 
             "📈 Resumo da Temporada",
             "📋 Histórico de Adversários",
             "⚙️ Configurar Modelos"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Métricas rápidas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Jogos", len(st.session_state.jogos))
        with col2:
            if st.session_state.jogos:
                vitorias = sum(1 for j in st.session_state.jogos if j.resultado == "Vitória")
                st.metric("Vitórias", vitorias)
        
        # Botões de ação
        if st.button("💾 Salvar Dados", use_container_width=True):
            if salvar_jogos(st.session_state.jogos):
                st.success("Dados salvos com sucesso!")
            else:
                st.error("Erro ao salvar dados")
        
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.session_state.jogos = carregar_jogos()
            st.rerun()
    
    return menu

def renderizar_placar_destaque(gols_marcados: int, gols_sofridos: int, resultado: str):
    """Renderiza o placar em destaque com nomes corrigidos"""
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown(f"# 🏆 {gols_marcados} x {gols_sofridos}")
        
        if resultado == "Vitória":
            st.success(f"### {resultado}!")
        elif resultado == "Derrota":
            st.error(f"### {resultado}")
        else:
            st.warning(f"### {resultado}")

def renderizar_metricas_time(
    titulo: str,
    metricas: Dict[str, float],
    numeros_absolutos: Dict[str, Any],
    is_meu_time: bool = True
):
    """Renderiza as métricas de um time de forma organizada (SEM DELTAS)"""
    
    estilo_card = "metric-card" + ("" if is_meu_time else " metric-card-adversario")
    icone = "🏠" if is_meu_time else "✈️"
    
    with st.container():
        st.markdown(f"<div class='{estilo_card}'>", unsafe_allow_html=True)
        
        # Título
        st.markdown(f"### {icone} {titulo}")
        st.divider()
        
        # 🔥 MÉTRICAS SEM DELTAS - filtrar apenas as que não começam com 'delta_'
        metricas_sem_delta = {k: v for k, v in metricas.items() if not k.startswith('delta_')}
        
        for chave, valor in metricas_sem_delta.items():
            st.metric(
                label=chave,
                value=f"{valor:.1f}%"
                # ❌ DELTA REMOVIDO
            )
        
        # Números absolutos
        st.caption(
            f"📊 {numeros_absolutos.get('finalizacoes', 0)} finalizações, "
            f"{numeros_absolutos.get('passes_certos', 0)} passes certos, "
            f"{numeros_absolutos.get('defesas', 0)} defesas"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

def renderizar_grafico_comparativo(metricas_meu: Dict, metricas_adv: Dict):
    """Renderiza gráfico de comparação entre os times"""
    
    categorias = ['Posse', 'Finalizações', 'Precisão', 'Passes', 'Eficiência']
    valores_meu = [
        metricas_meu.get('Posse de Bola', 0),
        metricas_meu.get('Finalizações', 0),
        metricas_meu.get('Precisão de Finalizações', 0),
        metricas_meu.get('Taxa de Acerto de Passes', 0),
        metricas_meu.get('Eficiência Ofensiva', 0)
    ]
    valores_adv = [
        metricas_adv.get('Posse de Bola', 0),
        metricas_adv.get('Finalizações', 0),
        metricas_adv.get('Precisão de Finalizações', 0),
        metricas_adv.get('Taxa de Acerto de Passes', 0),
        metricas_adv.get('Eficiência Ofensiva', 0)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=st.session_state.nome_clube,
        x=categorias,
        y=valores_meu,
        marker_color='#1f77b4',
        text=[f'{v:.1f}%' for v in valores_meu],
        textposition='auto',
        textfont=dict(size=12)
    ))
    
    fig.add_trace(go.Bar(
        name='Adversário',
        x=categorias,
        y=valores_adv,
        marker_color='#ff4b4b',
        text=[f'{v:.1f}%' for v in valores_adv],
        textposition='auto',
        textfont=dict(size=12)
    ))
    
    fig.update_layout(
        title="📊 Comparação de Desempenho",
        barmode='group',
        yaxis_title="Porcentagem (%)",
        yaxis_range=[0, 100],
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PÁGINA DE ANÁLISE DO JOGO (MODIFICADA)
# =============================================================================

def pagina_analise_jogo():
    """Página de análise detalhada do jogo"""
    st.header("📊 Análise do Jogo")
    
    if not st.session_state.jogos:
        st.warning("Nenhum jogo registrado ainda.")
        st.info("💡 Vá em '📝 Registrar Jogo' para começar!")
        return
    
    # Seleção do jogo
    jogos_lista = [
        f"{j.data.strftime('%d/%m/%Y')} - {j.contexto.nome} ({j.categoria})"
        for j in st.session_state.jogos
    ]
    
    idx = st.selectbox(
        "Selecione o jogo para análise:",
        range(len(jogos_lista)),
        format_func=lambda x: jogos_lista[x]
    )
    
    jogo = st.session_state.jogos[idx]
    
    # =========================================================================
    # CÁLCULOS DAS MÉTRICAS
    # =========================================================================
    metricas = calcular_metricas_jogo(jogo)
    
    # Extrair métricas para facilitar o acesso
    posse_meu = metricas['posse']['meu_time']
    posse_adv = metricas['posse']['adversario']
    
    perc_finalizacoes_meu = metricas['finalizacoes']['meu_time']
    perc_finalizacoes_adv = metricas['finalizacoes']['adversario']
    
    precisao_meu = metricas['precisao']['meu_time']
    precisao_adv = metricas['precisao']['adversario']
    
    taxa_passe_meu = metricas['passes']['meu_time']
    taxa_passe_adv = metricas['passes']['adversario']
    
    eficiencia_meu = metricas['eficiencia']['meu_time']
    eficiencia_adv = metricas['eficiencia']['adversario']
    
    # =========================================================================
    # CABEÇALHO DA ANÁLISE
    # =========================================================================
    st.subheader(f"⚔️ {jogo.data.strftime('%d/%m/%Y')} - {jogo.contexto.nome}")
    
    # 🔥 PLACAR COM NOMES CORRIGIDOS
    renderizar_placar_destaque(jogo.gols_pro, jogo.gols_contra, jogo.resultado)
    
    st.divider()
    
    # =========================================================================
    # MÉTRICAS PRINCIPAIS - ORGANIZADAS LADO A LADO
    # =========================================================================
    st.subheader("📊 PORCENTAGENS DE DOMÍNIO DO JOGO")
    
    # 🔥 DICIONÁRIOS DE MÉTRICAS (COM DELTAS PARA USO INTERNO, MAS SERÃO FILTRADOS)
    metricas_meu_dict = {
        'Posse de Bola': posse_meu,
        'Finalizações': perc_finalizacoes_meu,
        'Precisão de Finalizações': precisao_meu,
        'Taxa de Acerto de Passes': taxa_passe_meu,
        'Eficiência Ofensiva': eficiencia_meu,
        'delta_Posse de Bola': posse_meu - posse_adv,
        'delta_Finalizações': perc_finalizacoes_meu - perc_finalizacoes_adv,
        'delta_Precisão de Finalizações': precisao_meu - precisao_adv,
        'delta_Taxa de Acerto de Passes': taxa_passe_meu - taxa_passe_adv,
        'delta_Eficiência Ofensiva': eficiencia_meu - eficiencia_adv
    }
    
    metricas_adv_dict = {
        'Posse de Bola': posse_adv,
        'Finalizações': perc_finalizacoes_adv,
        'Precisão de Finalizações': precisao_adv,
        'Taxa de Acerto de Passes': taxa_passe_adv,
        'Eficiência Ofensiva': eficiencia_adv
    }
    
    # Números absolutos
    numeros_meu = {
        'finalizacoes': jogo.estatisticas.meu_time.finalizacoes,
        'passes_certos': jogo.estatisticas.meu_time.passes_certos,
        'defesas': jogo.estatisticas.meu_time.defesas_goleiro
    }
    
    numeros_adv = {
        'finalizacoes': jogo.estatisticas.adversario.finalizacoes,
        'passes_certos': jogo.estatisticas.adversario.passes_certos,
        'defesas': jogo.estatisticas.adversario.defesas_goleiro
    }
    
    # Renderizar duas colunas
    col_esquerda, col_direita = st.columns(2)
    
    with col_esquerda:
        # 🔥 TÍTULO COM NOME DO CLUBE
        renderizar_metricas_time(
            titulo=f"{st.session_state.nome_clube} (SEU TIME)",
            metricas=metricas_meu_dict,
            numeros_absolutos=numeros_meu,
            is_meu_time=True
        )
    
    with col_direita:
        renderizar_metricas_time(
            titulo=f"{jogo.contexto.nome} (ADVERSÁRIO)",
            metricas=metricas_adv_dict,
            numeros_absolutos=numeros_adv,
            is_meu_time=False
        )
    
    st.divider()
    
    # =========================================================================
    # GRÁFICO DE COMPARAÇÃO
    # =========================================================================
    renderizar_grafico_comparativo(metricas_meu_dict, metricas_adv_dict)
    
    st.divider()
    
    # =========================================================================
    # TABELAS DE DADOS
    # =========================================================================
    tab1, tab2, tab3 = st.tabs(["📋 Números Brutos", "📈 Porcentagens", "🏆 Resumo do Domínio"])
    
    with tab1:
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown(f"**📊 Dados do {st.session_state.nome_clube}**")
            df_meu = pd.DataFrame([
                {"Métrica": "Passes Certos", "Valor": jogo.estatisticas.meu_time.passes_certos},
                {"Métrica": "Passes Errados", "Valor": jogo.estatisticas.meu_time.passes_errados},
                {"Métrica": "Finalizações", "Valor": jogo.estatisticas.meu_time.finalizacoes},
                {"Métrica": "Finalizações no Alvo", "Valor": jogo.estatisticas.meu_time.finalizacoes_no_alvo},
                {"Métrica": "Defesas", "Valor": jogo.estatisticas.meu_time.defesas_goleiro},
                {"Métrica": "Escanteios", "Valor": jogo.estatisticas.meu_time.escanteios},
                {"Métrica": "Faltas", "Valor": jogo.estatisticas.meu_time.faltas},
                {"Métrica": "Cartões Amarelos", "Valor": jogo.estatisticas.meu_time.cartoes_amarelos},
                {"Métrica": "Cartões Vermelhos", "Valor": jogo.estatisticas.meu_time.cartoes_vermelhos},
            ])
            st.dataframe(df_meu, use_container_width=True, hide_index=True)
        
        with col_t2:
            st.markdown(f"**📊 Dados do {jogo.contexto.nome}**")
            df_adv = pd.DataFrame([
                {"Métrica": "Passes Certos", "Valor": jogo.estatisticas.adversario.passes_certos},
                {"Métrica": "Passes Errados", "Valor": jogo.estatisticas.adversario.passes_errados},
                {"Métrica": "Finalizações", "Valor": jogo.estatisticas.adversario.finalizacoes},
                {"Métrica": "Finalizações no Alvo", "Valor": jogo.estatisticas.adversario.finalizacoes_no_alvo},
                {"Métrica": "Defesas", "Valor": jogo.estatisticas.adversario.defesas_goleiro},
                {"Métrica": "Escanteios", "Valor": jogo.estatisticas.adversario.escanteios},
                {"Métrica": "Faltas", "Valor": jogo.estatisticas.adversario.faltas},
                {"Métrica": "Cartões Amarelos", "Valor": jogo.estatisticas.adversario.cartoes_amarelos},
                {"Métrica": "Cartões Vermelhos", "Valor": jogo.estatisticas.adversario.cartoes_vermelhos},
            ])
            st.dataframe(df_adv, use_container_width=True, hide_index=True)
    
    with tab2:
        df_percentuais = pd.DataFrame({
            "Indicador": [
                "Posse de Bola",
                "Finalizações",
                "Precisão de Finalizações",
                "Taxa de Acerto de Passes",
                "Eficiência Ofensiva"
            ],
            st.session_state.nome_clube: [
                f"{posse_meu:.1f}%",
                f"{perc_finalizacoes_meu:.1f}%",
                f"{precisao_meu:.1f}%",
                f"{taxa_passe_meu:.1f}%",
                f"{eficiencia_meu:.1f}%"
            ],
            jogo.contexto.nome: [
                f"{posse_adv:.1f}%",
                f"{perc_finalizacoes_adv:.1f}%",
                f"{precisao_adv:.1f}%",
                f"{taxa_passe_adv:.1f}%",
                f"{eficiencia_adv:.1f}%"
            ],
            "Diferença": [
                f"{posse_meu - posse_adv:+.1f}%",
                f"{perc_finalizacoes_meu - perc_finalizacoes_adv:+.1f}%",
                f"{precisao_meu - precisao_adv:+.1f}%",
                f"{taxa_passe_meu - taxa_passe_adv:+.1f}%",
                f"{eficiencia_meu - eficiencia_adv:+.1f}%"
            ]
        })
        st.dataframe(df_percentuais, use_container_width=True, hide_index=True)
    
    with tab3:
        dominios = calcular_dominio(
            posse_meu, perc_finalizacoes_meu, precisao_meu,
            taxa_passe_meu, eficiencia_meu, posse_adv,
            perc_finalizacoes_adv, precisao_adv, taxa_passe_adv,
            eficiencia_adv
        )
        
        if dominios:
            st.success(f"✅ {st.session_state.nome_clube} DOMINOU: {', '.join(dominios)}")
        else:
            dominios_adv = calcular_dominio(
                posse_adv, perc_finalizacoes_adv, precisao_adv,
                taxa_passe_adv, eficiencia_adv, posse_meu,
                perc_finalizacoes_meu, precisao_meu, taxa_passe_meu,
                eficiencia_meu
            )
            if dominios_adv:
                st.warning(f"⚠️ {jogo.contexto.nome} DOMINOU: {', '.join(dominios_adv)}")
            else:
                st.info("⚖️ JOGO EQUILIBRADO")
    
    # Índice de Desenvolvimento
    st.divider()
    indice = indice_desenvolvimento(jogo)
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.metric("📊 ÍNDICE DE DESENVOLVIMENTO", f"{indice:.1f}")
        if indice >= 70:
            st.success("🔝 DESEMPENHO EXCELENTE")
        elif indice >= 50:
            st.info("📈 BOM DESEMPENHO")
        else:
            st.warning("📉 PRECISA MELHORAR")

# =============================================================================
# DEMAIS PÁGINAS (SEM ALTERAÇÕES)
# =============================================================================

def pagina_registrar_jogo():
    """Página de registro de novo jogo"""
    st.header("📝 Registrar Novo Jogo")
    
    with st.form("form_jogo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        # =====================================================================
        # COLUNA 1: Informações Básicas e Adversário
        # =====================================================================
        with col1:
            with st.container(border=True):
                st.subheader("📅 Informações Básicas")
                data = st.date_input("Data do jogo:", datetime.now())
                local = st.text_input("Local:", "Estádio")
                categoria = st.selectbox(
                    "Categoria:", 
                    ["Sub-15", "Sub-17", "Sub-20", "Profissional"]
                )
            
            with st.container(border=True):
                st.subheader("🆚 Adversário")
                
                # Busca adversários existentes
                nomes_adv = st.session_state.gerenciador_adv.listar_nomes()
                
                opcao_adv = st.radio(
                    "Selecionar adversário:",
                    ["📌 Escolher existente", "➕ Criar novo"],
                    horizontal=True,
                    key="opcao_adv"
                )
                
                if opcao_adv == "📌 Escolher existente" and nomes_adv:
                    adversario_nome = st.selectbox(
                        "Selecione:",
                        nomes_adv,
                        key="adv_existente"
                    )
                    adv_data = st.session_state.gerenciador_adv.buscar_por_nome(adversario_nome)
                    if adv_data:
                        adversario_nivel = adv_data.nivel
                        adversario_estilo = adv_data.estilo
                        adversario_formacao = adv_data.formacao_base
                        adversario_obs = adv_data.observacoes
                        st.info(f"🔄 Jogaram {adv_data.vezes_jogado} vezes")
                
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        adversario_nome = st.text_input("Nome:", key="adv_novo_nome")
                        adversario_nivel = st.slider("Nível (1-5):", 1, 5, 3, key="adv_nivel")
                    with col_b:
                        adversario_estilo = st.selectbox(
                            "Estilo:", 
                            ["Posse", "Transição", "Direto", "Defensivo"],
                            key="adv_estilo"
                        )
                        adversario_formacao = st.text_input("Formação:", "4-4-2", key="adv_formacao")
                    adversario_obs = st.text_area("Observações:", "", key="adv_obs")
        
        # =====================================================================
        # COLUNA 2: Placar e Formação
        # =====================================================================
        with col2:
            with st.container(border=True):
                st.subheader("⚽ Placar")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    # 🔥 RENOMEADO PARA "Gols Marcados" mas mantendo a variável
                    gols_pro = st.number_input("Gols Marcados:", 0, 20, 0)
                with col_g2:
                    # 🔥 RENOMEADO PARA "Gols Sofridos" mas mantendo a variável
                    gols_contra = st.number_input("Gols Sofridos:", 0, 20, 0)
            
            with st.container(border=True):
                st.subheader("📋 Formação")
                formacao_usada = st.text_input("Formação do seu time:", "4-3-3")
        
        st.divider()
        
        # =====================================================================
        # DADOS DO SEU TIME
        # =====================================================================
        with st.container(border=True):
            st.subheader("📊 Dados do Seu Time")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                st.markdown("**⚔️ Ataque**")
                finalizacoes = st.number_input("Finalizações:", 0, 50, 0, key="fin_meu")
                finalizacoes_alvo = st.number_input("No alvo:", 0, 50, 0, key="alvo_meu")
                escanteios = st.number_input("Escanteios:", 0, 20, 0, key="esc_meu")
            
            with col4:
                st.markdown("**🔄 Posse e Passes**")
                passes_certos = st.number_input("Passes certos:", 0, 500, 0, key="pass_c_meu")
                passes_errados = st.number_input("Passes errados:", 0, 500, 0, key="pass_e_meu")
            
            with col5:
                st.markdown("**🛡️ Defesa**")
                defesas = st.number_input("Defesas do goleiro:", 0, 20, 0, key="def_meu")
                desarmes = st.number_input("Desarmes:", 0, 50, 0, key="des_meu")
                faltas = st.number_input("Faltas cometidas:", 0, 50, 0, key="fal_meu")
            
            col6, col7 = st.columns(2)
            with col6:
                st.markdown("**🟨 Disciplina**")
                amarelos = st.number_input("Cartões amarelos:", 0, 5, 0, key="am_meu")
                vermelhos = st.number_input("Cartões vermelhos:", 0, 2, 0, key="verm_meu")
        
        # =====================================================================
        # DADOS DO ADVERSÁRIO
        # =====================================================================
        with st.container(border=True):
            st.subheader("🆚 Dados do Adversário")
            col8, col9, col10 = st.columns(3)
            
            with col8:
                st.markdown("**⚔️ Ataque**")
                finalizacoes_adv = st.number_input("Finalizações adv:", 0, 50, 0, key="fin_adv")
                finalizacoes_alvo_adv = st.number_input("No alvo adv:", 0, 50, 0, key="alvo_adv")
                escanteios_adv = st.number_input("Escanteios adv:", 0, 20, 0, key="esc_adv")
            
            with col9:
                st.markdown("**🔄 Posse e Passes**")
                passes_certos_adv = st.number_input("Passes certos adv:", 0, 500, 0, key="pass_c_adv")
                passes_errados_adv = st.number_input("Passes errados adv:", 0, 500, 0, key="pass_e_adv")
            
            with col10:
                st.markdown("**🛡️ Defesa**")
                defesas_adv = st.number_input("Defesas adv:", 0, 20, 0, key="def_adv")
                desarmes_adv = st.number_input("Desarmes adv:", 0, 50, 0, key="des_adv")
                faltas_adv = st.number_input("Faltas adv:", 0, 50, 0, key="fal_adv")
            
            col11, col12 = st.columns(2)
            with col11:
                st.markdown("**🟨 Disciplina**")
                amarelos_adv = st.number_input("Amarelos adv:", 0, 5, 0, key="am_adv")
                vermelhos_adv = st.number_input("Vermelhos adv:", 0, 2, 0, key="verm_adv")
        
        # =====================================================================
        # AVALIAÇÃO DO MODELO
        # =====================================================================
        with st.container(border=True):
            st.subheader("📝 Avaliação do Modelo de Jogo")
            
            modelo_escolhido = st.selectbox(
                "Modelo utilizado:",
                [m.nome for m in st.session_state.modelos]
            )
            
            col13, col14, col15, col16 = st.columns(4)
            with col13:
                cumprimento_of = st.slider("Cumprimento Ofensivo:", 1, 5, 3)
            with col14:
                eficacia_of = st.slider("Eficácia Ofensiva:", 1, 5, 3)
            with col15:
                cumprimento_def = st.slider("Cumprimento Defensivo:", 1, 5, 3)
            with col16:
                eficacia_def = st.slider("Eficácia Defensiva:", 1, 5, 3)
        
        # =====================================================================
        # SUBMISSÃO DO FORMULÁRIO
        # =====================================================================
        submitted = st.form_submit_button(
            "✅ Registrar Jogo",
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            try:
                # Criar estatísticas
                meu_time = EstatisticasTime(
                    gols=gols_pro,
                    finalizacoes=finalizacoes,
                    finalizacoes_no_alvo=finalizacoes_alvo,
                    escanteios=escanteios,
                    passes_certos=passes_certos,
                    passes_errados=passes_errados,
                    defesas_goleiro=defesas,
                    desarmes=desarmes,
                    faltas=faltas,
                    cartoes_amarelos=amarelos,
                    cartoes_vermelhos=vermelhos
                )
                
                adversario_time = EstatisticasTime(
                    gols=gols_contra,
                    finalizacoes=finalizacoes_adv,
                    finalizacoes_no_alvo=finalizacoes_alvo_adv,
                    escanteios=escanteios_adv,
                    passes_certos=passes_certos_adv,
                    passes_errados=passes_errados_adv,
                    defesas_goleiro=defesas_adv,
                    desarmes=desarmes_adv,
                    faltas=faltas_adv,
                    cartoes_amarelos=amarelos_adv,
                    cartoes_vermelhos=vermelhos_adv
                )
                
                estatisticas = EstatisticasJogo(
                    meu_time=meu_time,
                    adversario=adversario_time
                )
                
                contexto = ContextoAdversario(
                    nome=adversario_nome,
                    nivel=adversario_nivel,
                    estilo=adversario_estilo,
                    formacao_base=adversario_formacao,
                    observacoes=adversario_obs if 'adversario_obs' in locals() else ""
                )
                
                avaliacao = AvaliacaoModelo(
                    fases=[
                        AvaliacaoFase("Ofensiva", cumprimento_of, eficacia_of),
                        AvaliacaoFase("Defensiva", cumprimento_def, eficacia_def),
                    ]
                )
                
                jogo = Jogo(
                    id=gerar_id(),
                    data=datetime.combine(data, datetime.now().time()),
                    categoria=categoria,
                    local=local,
                    contexto=contexto,
                    formacao_usada=formacao_usada,
                    gols_pro=gols_pro,
                    gols_contra=gols_contra,
                    estatisticas=estatisticas,
                    avaliacao_modelo=avaliacao
                )
                
                # Salvar/atualizar adversário
                if opcao_adv == "➕ Criar novo":
                    st.session_state.gerenciador_adv.adicionar(
                        nome=adversario_nome,
                        nivel=adversario_nivel,
                        estilo=adversario_estilo,
                        formacao=adversario_formacao,
                        observacoes=adversario_obs if 'adversario_obs' in locals() else ""
                    )
                
                st.session_state.gerenciador_adv.atualizar_estatisticas(
                    nome=adversario_nome,
                    gols_pro=gols_pro,
                    gols_contra=gols_contra
                )
                
                st.session_state.jogos.append(jogo)
                salvar_jogos(st.session_state.jogos)
                
                st.success("✅ Jogo registrado com sucesso!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Erro ao registrar: {str(e)}")

# =============================================================================
# DEMAIS PÁGINAS (RESUMO, HISTÓRICO, CONFIGURAÇÕES) - SEM ALTERAÇÕES
# =============================================================================

def pagina_resumo_temporada():
    """Página com resumo estatístico da temporada"""
    st.header("📈 Resumo da Temporada")
    
    if not st.session_state.jogos:
        st.warning("Nenhum jogo registrado ainda.")
        return
    
    # =========================================================================
    # MÉTRICAS GERAIS
    # =========================================================================
    total_jogos = len(st.session_state.jogos)
    vitorias = sum(1 for j in st.session_state.jogos if j.resultado == "Vitória")
    empates = sum(1 for j in st.session_state.jogos if j.resultado == "Empate")
    derrotas = sum(1 for j in st.session_state.jogos if j.resultado == "Derrota")
    
    gols_pro = sum(j.gols_pro for j in st.session_state.jogos)
    gols_contra = sum(j.gols_contra for j in st.session_state.jogos)
    aproveitamento = ((vitorias * 3 + empates) / (total_jogos * 3)) * 100
    
    # Cards de métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Jogos", total_jogos)
    with col2:
        st.metric("Vitórias", vitorias)
    with col3:
        st.metric("Empates", empates)
    with col4:
        st.metric("Derrotas", derrotas)
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        # 🔥 RENOMEADO
        st.metric("Gols Marcados", gols_pro)
    with col6:
        # 🔥 RENOMEADO
        st.metric("Gols Sofridos", gols_contra)
    with col7:
        st.metric("Saldo", gols_pro - gols_contra)
    with col8:
        st.metric("Aproveitamento", f"{aproveitamento:.1f}%")
    
    # =========================================================================
    # GRÁFICOS
    # =========================================================================
    st.divider()
    
    tab_graf1, tab_graf2 = st.tabs(["📈 Evolução de Gols", "📊 Distribuição de Resultados"])
    
    with tab_graf1:
        df_evolucao = pd.DataFrame([
            {"Jogo": i+1, "Gols Marcados": j.gols_pro, "Gols Sofridos": j.gols_contra}
            for i, j in enumerate(st.session_state.jogos)
        ])
        
        fig = px.line(
            df_evolucao, x="Jogo", y=["Gols Marcados", "Gols Sofridos"],
            markers=True,
            title="Evolução de Gols por Jogo",
            color_discrete_map={"Gols Marcados": "#1f77b4", "Gols Sofridos": "#ff4b4b"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_graf2:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Vitórias', 'Empates', 'Derrotas'],
            values=[vitorias, empates, derrotas],
            hole=.3,
            marker_colors=['#1f77b4', '#ffa600', '#ff4b4b']
        )])
        fig_pie.update_layout(title="Distribuição de Resultados", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # =========================================================================
    # TABELA DE JOGOS
    # =========================================================================
    st.divider()
    st.subheader("📋 Histórico de Jogos")
    
    df_jogos = pd.DataFrame([
        {
            "Data": j.data.strftime("%d/%m/%Y"),
            "Adversário": j.contexto.nome,
            "Categoria": j.categoria,
            "Placar": f"{j.gols_pro} x {j.gols_contra}",
            "Resultado": j.resultado,
            "Formação": j.formacao_usada,
            "Índice": f"{indice_desenvolvimento(j):.1f}"
        }
        for j in st.session_state.jogos
    ])
    
    st.dataframe(
        df_jogos,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Resultado": st.column_config.Column(
                "Resultado",
                help="Resultado da partida"
            )
        }
    )

def pagina_historico_adversarios():
    """Página com histórico de adversários"""
    st.header("📋 Histórico de Adversários")
    
    gerenciador = st.session_state.gerenciador_adv
    
    if not gerenciador.adversarios:
        st.warning("Nenhum adversário cadastrado ainda.")
        return
    
    # =========================================================================
    # TABELA DE ADVERSÁRIOS
    # =========================================================================
    dados_adv = []
    for adv in gerenciador.adversarios.values():
        dados_adv.append({
            "Adversário": adv.nome,
            "Nível": f"{'⭐' * adv.nivel}",
            "Estilo": adv.estilo,
            "Formação": adv.formacao_base,
            "Jogos": adv.vezes_jogado,
            "Vitórias": adv.vitorias,
            "Empates": adv.empates,
            "Derrotas": adv.derrotas,
            "Aproveitamento": f"{adv.aproveitamento:.1f}%",
            "Último Jogo": adv.ultimo_jogo or "-"
        })
    
    df_adv = pd.DataFrame(dados_adv)
    st.dataframe(df_adv, use_container_width=True, hide_index=True)
    
    # =========================================================================
    # GRÁFICO DE DESEMPENHO
    # =========================================================================
    st.divider()
    st.subheader("📊 Desempenho por Adversário")
    
    fig = go.Figure()
    for adv in gerenciador.adversarios.values():
        if adv.vezes_jogado > 0:
            fig.add_trace(go.Bar(
                name=adv.nome,
                x=['Vitórias', 'Empates', 'Derrotas'],
                y=[adv.vitorias, adv.empates, adv.derrotas]
            ))
    
    if fig.data:
        fig.update_layout(
            barmode='group',
            height=400,
            title="Confrontos Diretos"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # EDIÇÃO DE ADVERSÁRIOS
    # =========================================================================
    st.divider()
    st.subheader("✏️ Editar Adversário")
    
    nome_editar = st.selectbox(
        "Selecione o adversário:",
        ["Selecione..."] + gerenciador.listar_nomes()
    )
    
    if nome_editar != "Selecione...":
        adv = gerenciador.buscar_por_nome(nome_editar)
        if adv:
            with st.form("editar_adv"):
                novo_nome = st.text_input("Nome:", adv.nome)
                novo_nivel = st.slider("Nível (1-5):", 1, 5, adv.nivel)
                novo_estilo = st.selectbox(
                    "Estilo:",
                    ["Posse", "Transição", "Direto", "Defensivo"],
                    index=["Posse", "Transição", "Direto", "Defensivo"].index(adv.estilo)
                )
                nova_formacao = st.text_input("Formação:", adv.formacao_base)
                novas_obs = st.text_area("Observações:", adv.observacoes)
                
                if st.form_submit_button("Atualizar Adversário", type="primary"):
                    adv.nome = novo_nome
                    adv.nivel = novo_nivel
                    adv.estilo = novo_estilo
                    adv.formacao_base = nova_formacao
                    adv.observacoes = novas_obs
                    gerenciador.salvar()
                    st.success("Adversário atualizado!")
                    st.rerun()

def pagina_configurar_modelos():
    """Página de configuração dos modelos de jogo"""
    st.header("⚙️ Configurar Modelos de Jogo")
    
    st.info("Defina os modelos de jogo que sua equipe utiliza para análise tática.")
    
    for i, modelo in enumerate(st.session_state.modelos):
        with st.expander(f"📋 {modelo.nome}"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome:", modelo.nome, key=f"nome_{i}")
            with col2:
                nova_prioridade = st.slider(
                    "Prioridade (1-5):",
                    1, 5, modelo.prioridade,
                    key=f"prio_{i}"
                )
            nova_descricao = st.text_area("Descrição:", modelo.descricao or "", key=f"desc_{i}")
            
            if st.button("Atualizar", key=f"up_{i}"):
                st.session_state.modelos[i] = ModeloJogo(
                    nome=novo_nome,
                    prioridade=nova_prioridade,
                    descricao=nova_descricao
                )
                st.success("Modelo atualizado!")
    
    if st.button("➕ Adicionar Novo Modelo", use_container_width=True):
        st.session_state.modelos.append(
            ModeloJogo("Novo Modelo", 3, "Descrição do modelo")
        )
        st.rerun()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Função principal do aplicativo"""
    
    # Inicializar sessão
    inicializar_sessao()
    
    # Título principal com nome do clube
    st.title(f"⚽ {st.session_state.nome_clube}")
    st.markdown("*Análise técnica para categorias de base*")
    st.divider()
    
    # Menu lateral
    menu = sidebar_menu()
    
    # Rotear para a página selecionada
    if menu == "📝 Registrar Jogo":
        pagina_registrar_jogo()
    elif menu == "📊 Análise do Jogo":
        pagina_analise_jogo()
    elif menu == "📈 Resumo da Temporada":
        pagina_resumo_temporada()
    elif menu == "📋 Histórico de Adversários":
        pagina_historico_adversarios()
    elif menu == "⚙️ Configurar Modelos":
        pagina_configurar_modelos()

if __name__ == "__main__":
    main()
