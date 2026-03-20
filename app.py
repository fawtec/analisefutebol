"""
Analisador de Futebol de Formação
Uma aplicação Streamlit para análise técnica de partidas de futebol de base
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional

# Importações locais
from adversarios import GerenciadorAdversarios
from firebase_config import FirebaseManager
from models import (
    EstatisticasTime, EstatisticasJogo, ContextoAdversario,
    AvaliacaoFase, AvaliacaoModelo, Jogo, ModeloJogo
)
from analytics import (
    indice_desenvolvimento, calcular_metricas_jogo, calcular_dominio
)
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

# CSS personalizado
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
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# =============================================================================

def inicializar_sessao():
    """Inicializa todas as variáveis de sessão necessárias"""
    
    # Nome do clube
    if "nome_clube" not in st.session_state:
        st.session_state.nome_clube = "Meu Time"
    
    # Firebase
    if "firebase" not in st.session_state:
        st.session_state.firebase = FirebaseManager()
    
    # Gerenciador de adversários
    if "gerenciador_adv" not in st.session_state:
        st.session_state.gerenciador_adv = GerenciadorAdversarios()
    
    # Carregar jogos do Firebase
    if "jogos" not in st.session_state:
        with st.spinner("Carregando dados do Firebase..."):
            st.session_state.jogos = st.session_state.firebase.carregar_jogos()
            if not st.session_state.jogos:
                st.session_state.jogos = []

    # Modelos de jogo
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
    """Renderiza o menu lateral"""
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/football2.png", width=80)
        
        # Nome do clube
        nome_clube = st.text_input(
            "🏆 Nome do Clube:",
            value=st.session_state.nome_clube,
            key="input_nome_clube"
        )
        if nome_clube != st.session_state.nome_clube:
            st.session_state.nome_clube = nome_clube
        
        st.markdown(f"### {st.session_state.nome_clube}")
        st.divider()
        
        # Menu
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
        
        # Botão salvar no Firebase
        if st.button("💾 Salvar no Firebase", use_container_width=True):
            with st.spinner("Salvando dados na nuvem..."):
                for jogo in st.session_state.jogos:
                    st.session_state.firebase.salvar_jogo(jogo)
                st.session_state.firebase.salvar_adversarios(
                    st.session_state.gerenciador_adv.adversarios
                )
                st.success("✅ Dados salvos no Firebase!")
    
    return menu

# =============================================================================
# PÁGINA DE ANÁLISE DO JOGO
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
    
    # Cálculo das métricas
    metricas = calcular_metricas_jogo(jogo)
    
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
    
    # Placar
    st.subheader(f"⚔️ {jogo.data.strftime('%d/%m/%Y')} - {jogo.contexto.nome}")
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown(f"# 🏆 {jogo.gols_pro} x {jogo.gols_contra}")
        if jogo.resultado == "Vitória":
            st.success(f"### {jogo.resultado}!")
        elif jogo.resultado == "Derrota":
            st.error(f"### {jogo.resultado}")
        else:
            st.warning(f"### {jogo.resultado}")
    
    st.divider()
    
    # Métricas principais
    st.subheader("📊 PORCENTAGENS DE DOMÍNIO DO JOGO")
    
    metricas_meu = {
        'Posse de Bola': posse_meu,
        'Finalizações': perc_finalizacoes_meu,
        'Precisão de Finalizações': precisao_meu,
        'Taxa de Acerto de Passes': taxa_passe_meu,
        'Eficiência Ofensiva': eficiencia_meu,
    }
    
    metricas_adv = {
        'Posse de Bola': posse_adv,
        'Finalizações': perc_finalizacoes_adv,
        'Precisão de Finalizações': precisao_adv,
        'Taxa de Acerto de Passes': taxa_passe_adv,
        'Eficiência Ofensiva': eficiencia_adv,
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 🏠 {st.session_state.nome_clube} (SEU TIME)")
        for chave, valor in metricas_meu.items():
            st.metric(chave, f"{valor:.1f}%")
        st.caption(f"📊 {jogo.estatisticas.meu_time.finalizacoes} finalizações, {jogo.estatisticas.meu_time.passes_certos} passes")
    
    with col2:
        st.markdown(f"### ✈️ {jogo.contexto.nome} (ADVERSÁRIO)")
        for chave, valor in metricas_adv.items():
            st.metric(chave, f"{valor:.1f}%")
        st.caption(f"📊 {jogo.estatisticas.adversario.finalizacoes} finalizações, {jogo.estatisticas.adversario.passes_certos} passes")
    
    st.divider()
    
    # Gráfico
    categorias = list(metricas_meu.keys())
    valores_meu = list(metricas_meu.values())
    valores_adv = list(metricas_adv.values())
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name=st.session_state.nome_clube, x=categorias, y=valores_meu, marker_color='#1f77b4', text=[f'{v:.1f}%' for v in valores_meu], textposition='auto'))
    fig.add_trace(go.Bar(name='Adversário', x=categorias, y=valores_adv, marker_color='#ff4b4b', text=[f'{v:.1f}%' for v in valores_adv], textposition='auto'))
    fig.update_layout(title="Comparação de Desempenho", barmode='group', yaxis_title="Porcentagem (%)", yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PÁGINA DE REGISTRO DE JOGO (SIMPLIFICADA)
# =============================================================================

def pagina_registrar_jogo():
    """Página de registro de novo jogo"""
    st.header("📝 Registrar Novo Jogo")
    st.info("Esta é uma versão simplificada. Registre seus jogos aqui.")
    st.warning("Em breve você poderá registrar todos os dados do jogo!")

# =============================================================================
# PÁGINA DE RESUMO DA TEMPORADA
# =============================================================================

def pagina_resumo_temporada():
    """Página com resumo estatístico da temporada"""
    st.header("📈 Resumo da Temporada")
    
    if not st.session_state.jogos:
        st.warning("Nenhum jogo registrado ainda.")
        return
    
    total_jogos = len(st.session_state.jogos)
    vitorias = sum(1 for j in st.session_state.jogos if j.resultado == "Vitória")
    empates = sum(1 for j in st.session_state.jogos if j.resultado == "Empate")
    derrotas = sum(1 for j in st.session_state.jogos if j.resultado == "Derrota")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jogos", total_jogos)
    col2.metric("Vitórias", vitorias)
    col3.metric("Empates", empates)
    col4.metric("Derrotas", derrotas)
    
    st.success("Resumo da temporada carregado com sucesso!")

# =============================================================================
# PÁGINA DE HISTÓRICO DE ADVERSÁRIOS
# =============================================================================

def pagina_historico_adversarios():
    """Página com histórico de adversários"""
    st.header("📋 Histórico de Adversários")
    st.info("Histórico de adversários será exibido aqui.")
    st.warning("Em breve você verá todos os adversários cadastrados!")

# =============================================================================
# PÁGINA DE CONFIGURAR MODELOS
# =============================================================================

def pagina_configurar_modelos():
    """Página de configuração dos modelos de jogo"""
    st.header("⚙️ Configurar Modelos de Jogo")
    st.info("Configure os modelos de jogo aqui.")
    st.warning("Em breve você poderá criar, editar e excluir modelos!")

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Função principal do aplicativo"""
    
    inicializar_sessao()
    
    st.title(f"⚽ {st.session_state.nome_clube}")
    st.markdown("*Análise técnica para categorias de base*")
    st.divider()
    
    menu = sidebar_menu()
    
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
