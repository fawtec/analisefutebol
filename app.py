"""
Analisador de Futebol de Formação
Uma aplicação Streamlit para análise técnica de partidas de futebol de base
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any

# Importações locais
from adversarios import GerenciadorAdversarios, Adversario
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

def modelos_padrao():
    """Retorna a lista padrÃ£o de modelos de jogo."""
    return [
        ModeloJogo("Posse de Bola", 5, "Controle do jogo com passes curtos"),
        ModeloJogo("Contra-ataque", 3, "Explorar velocidade nos contra-golpes"),
        ModeloJogo("PressÃ£o Alta", 4, "Marcar subindo, recuperar bola rÃ¡pido"),
        ModeloJogo("TransiÃ§Ã£o RÃ¡pida", 4, "SaÃ­da rÃ¡pida ao ataque apÃ³s recuperaÃ§Ã£o"),
    ]


def carregar_modelos_sessao():
    """Carrega modelos do Firebase e usa fallback local quando necessÃ¡rio."""
    modelos_salvos = st.session_state.firebase.carregar_modelos()
    if not modelos_salvos:
        return modelos_padrao()

    modelos = []
    for modelo in modelos_salvos:
        if isinstance(modelo, ModeloJogo):
            modelos.append(modelo)
            continue

        modelos.append(
            ModeloJogo(
                modelo["nome"],
                modelo["prioridade"],
                modelo.get("descricao") or None
            )
        )

    return modelos or modelos_padrao()


def carregar_adversarios_sessao():
    """Carrega adversÃ¡rios do Firebase e faz fallback para o arquivo local."""
    gerenciador = GerenciadorAdversarios()
    adversarios_firebase = st.session_state.firebase.carregar_adversarios()

    if not adversarios_firebase:
        return gerenciador

    campos_validos = set(Adversario.__dataclass_fields__.keys())
    adversarios_convertidos = {}

    for adv_id, dados in adversarios_firebase.items():
        if isinstance(dados, Adversario):
            adversarios_convertidos[adv_id] = dados
            continue

        dados_limpos = {
            chave: valor for chave, valor in dados.items()
            if chave in campos_validos
        }
        dados_limpos.setdefault("id", adv_id)
        adversarios_convertidos[adv_id] = Adversario(**dados_limpos)

    gerenciador.adversarios = adversarios_convertidos
    return gerenciador


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
    if "adversarios_sincronizados" not in st.session_state:
        st.session_state.gerenciador_adv = carregar_adversarios_sessao()
        st.session_state.adversarios_sincronizados = True
    
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
    if "modelos_sincronizados" not in st.session_state:
        st.session_state.modelos = carregar_modelos_sessao()
        st.session_state.modelos_sincronizados = True

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
                st.session_state.firebase.salvar_modelos(st.session_state.modelos)
                st.success("✅ Dados salvos no Firebase!")
    
    return menu

def renderizar_placar_destaque(gols_marcados: int, gols_sofridos: int, resultado: str):
    """Renderiza o placar em destaque"""
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
    """Renderiza as métricas de um time de forma organizada (sem deltas)"""
    estilo_card = "metric-card" + ("" if is_meu_time else " metric-card-adversario")
    icone = "🏠" if is_meu_time else "✈️"
    
    with st.container():
        st.markdown(f"<div class='{estilo_card}'>", unsafe_allow_html=True)
        st.markdown(f"### {icone} {titulo}")
        st.divider()
        
        for chave, valor in metricas.items():
            st.metric(label=chave, value=f"{valor:.1f}%")
        
        st.caption(
            f"📊 {numeros_absolutos.get('finalizacoes', 0)} finalizações, "
            f"{numeros_absolutos.get('passes_certos', 0)} passes certos, "
            f"{numeros_absolutos.get('defesas', 0)} defesas"
        )
        st.markdown("</div>", unsafe_allow_html=True)

def renderizar_grafico_comparativo(metricas_meu: Dict, metricas_adv: Dict):
    """Renderiza gráfico de comparação entre os times"""
    categorias = list(metricas_meu.keys())
    valores_meu = list(metricas_meu.values())
    valores_adv = list(metricas_adv.values())
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=st.session_state.nome_clube,
        x=categorias,
        y=valores_meu,
        marker_color='#1f77b4',
        text=[f'{v:.1f}%' for v in valores_meu],
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        name='Adversário',
        x=categorias,
        y=valores_adv,
        marker_color='#ff4b4b',
        text=[f'{v:.1f}%' for v in valores_adv],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="📊 Comparação de Desempenho",
        barmode='group',
        yaxis_title="Porcentagem (%)",
        yaxis_range=[0, 100],
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PÁGINA: REGISTRAR JOGO
# =============================================================================

def pagina_registrar_jogo():
    """Página de registro de novo jogo"""
    st.header("📝 Registrar Novo Jogo")
    
    with st.form("form_jogo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Informações Básicas")
            data = st.date_input("Data do jogo:", datetime.now())
            local = st.text_input("Local:", "Estádio")
            categoria = st.selectbox("Categoria:", ["Sub-15", "Sub-17", "Sub-20", "Profissional"])
            
            st.subheader("🆚 Adversário")
            adversario_nome = st.text_input("Nome do adversário:")
            adversario_nivel = st.slider("Nível do adversário:", 1, 5, 3)
            adversario_estilo = st.selectbox("Estilo do adversário:", ["Posse", "Transição", "Direto", "Defensivo"])
            adversario_formacao = st.text_input("Formação do adversário:", "4-4-2")
            adversario_obs = st.text_area("Observações:", "")
        
        with col2:
            st.subheader("⚽ Placar")
            gols_pro = st.number_input("Gols Marcados:", 0, 20, 0)
            gols_contra = st.number_input("Gols Sofridos:", 0, 20, 0)
            
            st.subheader("📋 Formação")
            formacao_usada = st.text_input("Formação do seu time:", "4-3-3")
        
        st.divider()
        
        # Dados do seu time
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
        
        st.divider()
        
        # Dados do adversário
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
        
        st.divider()
        
        # Avaliação
        st.subheader("📝 Avaliação do Modelo de Jogo")
        modelo_escolhido = st.selectbox("Modelo utilizado:", [m.nome for m in st.session_state.modelos])
        
        col13, col14, col15, col16 = st.columns(4)
        with col13:
            cumprimento_of = st.slider("Cumprimento Ofensivo:", 1, 5, 3)
        with col14:
            eficacia_of = st.slider("Eficácia Ofensiva:", 1, 5, 3)
        with col15:
            cumprimento_def = st.slider("Cumprimento Defensivo:", 1, 5, 3)
        with col16:
            eficacia_def = st.slider("Eficácia Defensiva:", 1, 5, 3)
        
        submitted = st.form_submit_button("✅ Registrar Jogo", use_container_width=True, type="primary")
        
        if submitted:
            try:
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
                
                estatisticas = EstatisticasJogo(meu_time=meu_time, adversario=adversario_time)
                
                contexto = ContextoAdversario(
                    nome=adversario_nome,
                    nivel=adversario_nivel,
                    estilo=adversario_estilo,
                    formacao_base=adversario_formacao,
                    observacoes=adversario_obs
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
                
                st.session_state.jogos.append(jogo)
                st.session_state.firebase.salvar_jogo(jogo)
                
                # Atualizar cadastro consolidado do adversário
                adversario_existente = st.session_state.gerenciador_adv.buscar_por_nome(adversario_nome)

                if adversario_existente:
                    adversario_existente.nome = adversario_nome.strip()
                    adversario_existente.nivel = adversario_nivel
                    adversario_existente.estilo = adversario_estilo
                    adversario_existente.formacao_base = adversario_formacao
                    adversario_existente.observacoes = adversario_obs
                    adversario_existente.vezes_jogado += 1
                    adversario_existente.ultimo_jogo = datetime.now().strftime("%d/%m/%Y")

                    if gols_pro > gols_contra:
                        adversario_existente.vitorias += 1
                    elif gols_pro == gols_contra:
                        adversario_existente.empates += 1
                    else:
                        adversario_existente.derrotas += 1
                else:
                    adv_id = gerar_id()
                    novo_adv = Adversario(
                        id=adv_id,
                        nome=adversario_nome.strip(),
                        nivel=adversario_nivel,
                        estilo=adversario_estilo,
                        formacao_base=adversario_formacao,
                        observacoes=adversario_obs,
                        vezes_jogado=1,
                        vitorias=1 if gols_pro > gols_contra else 0,
                        empates=1 if gols_pro == gols_contra else 0,
                        derrotas=1 if gols_pro < gols_contra else 0,
                        ultimo_jogo=datetime.now().strftime("%d/%m/%Y")
                    )
                    st.session_state.gerenciador_adv.adversarios[adv_id] = novo_adv

                st.session_state.gerenciador_adv.salvar()
                st.session_state.firebase.salvar_adversarios(st.session_state.gerenciador_adv.adversarios)
                
                st.success("✅ Jogo registrado com sucesso!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Erro ao registrar: {str(e)}")

# =============================================================================
# PÁGINA: ANÁLISE DO JOGO
# =============================================================================

def pagina_analise_jogo():
    """Página de análise detalhada do jogo"""
    st.header("📊 Análise do Jogo")
    
    if not st.session_state.jogos:
        st.warning("Nenhum jogo registrado ainda.")
        st.info("💡 Vá em '📝 Registrar Jogo' para começar!")
        return
    
    jogos_lista = [f"{j.data.strftime('%d/%m/%Y')} - {j.contexto.nome} ({j.categoria})" for j in st.session_state.jogos]
    idx = st.selectbox("Selecione o jogo para análise:", range(len(jogos_lista)), format_func=lambda x: jogos_lista[x])
    jogo = st.session_state.jogos[idx]
    
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
    
    st.subheader(f"⚔️ {jogo.data.strftime('%d/%m/%Y')} - {jogo.contexto.nome}")
    renderizar_placar_destaque(jogo.gols_pro, jogo.gols_contra, jogo.resultado)
    st.divider()
    
    st.subheader("📊 PORCENTAGENS DE DOMÍNIO DO JOGO")
    
    metricas_meu_dict = {
        'Posse de Bola': posse_meu,
        'Finalizações': perc_finalizacoes_meu,
        'Precisão de Finalizações': precisao_meu,
        'Taxa de Acerto de Passes': taxa_passe_meu,
        'Eficiência Ofensiva': eficiencia_meu,
    }
    
    metricas_adv_dict = {
        'Posse de Bola': posse_adv,
        'Finalizações': perc_finalizacoes_adv,
        'Precisão de Finalizações': precisao_adv,
        'Taxa de Acerto de Passes': taxa_passe_adv,
        'Eficiência Ofensiva': eficiencia_adv,
    }
    
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
    
    col_esquerda, col_direita = st.columns(2)
    with col_esquerda:
        renderizar_metricas_time(f"{st.session_state.nome_clube} (SEU TIME)", metricas_meu_dict, numeros_meu, is_meu_time=True)
    with col_direita:
        renderizar_metricas_time(f"{jogo.contexto.nome} (ADVERSÁRIO)", metricas_adv_dict, numeros_adv, is_meu_time=False)
    
    st.divider()
    renderizar_grafico_comparativo(metricas_meu_dict, metricas_adv_dict)
    st.divider()
    
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
            "Indicador": ["Posse de Bola", "Finalizações", "Precisão de Finalizações", "Taxa de Acerto de Passes", "Eficiência Ofensiva"],
            st.session_state.nome_clube: [f"{posse_meu:.1f}%", f"{perc_finalizacoes_meu:.1f}%", f"{precisao_meu:.1f}%", f"{taxa_passe_meu:.1f}%", f"{eficiencia_meu:.1f}%"],
            jogo.contexto.nome: [f"{posse_adv:.1f}%", f"{perc_finalizacoes_adv:.1f}%", f"{precisao_adv:.1f}%", f"{taxa_passe_adv:.1f}%", f"{eficiencia_adv:.1f}%"],
            "Diferença": [f"{posse_meu - posse_adv:+.1f}%", f"{perc_finalizacoes_meu - perc_finalizacoes_adv:+.1f}%", f"{precisao_meu - precisao_adv:+.1f}%", f"{taxa_passe_meu - taxa_passe_adv:+.1f}%", f"{eficiencia_meu - eficiencia_adv:+.1f}%"]
        })
        st.dataframe(df_percentuais, use_container_width=True, hide_index=True)
    
    with tab3:
        dominios = calcular_dominio(posse_meu, perc_finalizacoes_meu, precisao_meu, taxa_passe_meu, eficiencia_meu, posse_adv, perc_finalizacoes_adv, precisao_adv, taxa_passe_adv, eficiencia_adv)
        if dominios:
            st.success(f"✅ {st.session_state.nome_clube} DOMINOU: {', '.join(dominios)}")
        else:
            dominios_adv = calcular_dominio(posse_adv, perc_finalizacoes_adv, precisao_adv, taxa_passe_adv, eficiencia_adv, posse_meu, perc_finalizacoes_meu, precisao_meu, taxa_passe_meu, eficiencia_meu)
            if dominios_adv:
                st.warning(f"⚠️ {jogo.contexto.nome} DOMINOU: {', '.join(dominios_adv)}")
            else:
                st.info("⚖️ JOGO EQUILIBRADO")
    
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
# PÁGINA: RESUMO DA TEMPORADA
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
    gols_pro = sum(j.gols_pro for j in st.session_state.jogos)
    gols_contra = sum(j.gols_contra for j in st.session_state.jogos)
    aproveitamento = ((vitorias * 3 + empates) / (total_jogos * 3)) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jogos", total_jogos)
    col2.metric("Vitórias", vitorias)
    col3.metric("Empates", empates)
    col4.metric("Derrotas", derrotas)
    
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Gols Marcados", gols_pro)
    col6.metric("Gols Sofridos", gols_contra)
    col7.metric("Saldo", gols_pro - gols_contra)
    col8.metric("Aproveitamento", f"{aproveitamento:.1f}%")
    
    st.divider()
    tab_graf1, tab_graf2 = st.tabs(["📈 Evolução de Gols", "📊 Distribuição de Resultados"])
    
    with tab_graf1:
        df_evolucao = pd.DataFrame([{"Jogo": i+1, "Gols Marcados": j.gols_pro, "Gols Sofridos": j.gols_contra} for i, j in enumerate(st.session_state.jogos)])
        fig = px.line(df_evolucao, x="Jogo", y=["Gols Marcados", "Gols Sofridos"], markers=True, title="Evolução de Gols por Jogo", color_discrete_map={"Gols Marcados": "#1f77b4", "Gols Sofridos": "#ff4b4b"})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab_graf2:
        fig_pie = go.Figure(data=[go.Pie(labels=['Vitórias', 'Empates', 'Derrotas'], values=[vitorias, empates, derrotas], hole=.3, marker_colors=['#1f77b4', '#ffa600', '#ff4b4b'])])
        fig_pie.update_layout(title="Distribuição de Resultados", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    st.subheader("📋 Histórico de Jogos")
    df_jogos = pd.DataFrame([{"Data": j.data.strftime("%d/%m/%Y"), "Adversário": j.contexto.nome, "Categoria": j.categoria, "Placar": f"{j.gols_pro} x {j.gols_contra}", "Resultado": j.resultado, "Formação": j.formacao_usada, "Índice": f"{indice_desenvolvimento(j):.1f}"} for j in st.session_state.jogos])
    st.dataframe(df_jogos, use_container_width=True, hide_index=True)

# =============================================================================
# PÁGINA: HISTÓRICO DE ADVERSÁRIOS
# =============================================================================

def pagina_historico_adversarios():
    """Página com histórico de adversários"""
    st.header("📋 Histórico de Adversários")
    
    gerenciador = st.session_state.gerenciador_adv
    
    if not gerenciador.adversarios:
        st.warning("Nenhum adversário cadastrado ainda.")
        return
    
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
    
    st.divider()
    st.subheader("📊 Desempenho por Adversário")
    
    fig = go.Figure()
    for adv in gerenciador.adversarios.values():
        if adv.vezes_jogado > 0:
            fig.add_trace(go.Bar(name=adv.nome, x=['Vitórias', 'Empates', 'Derrotas'], y=[adv.vitorias, adv.empates, adv.derrotas]))
    
    if fig.data:
        fig.update_layout(barmode='group', height=400, title="Confrontos Diretos")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    st.subheader("✏️ Editar Adversário")
    nome_editar = st.selectbox("Selecione o adversário:", ["Selecione..."] + gerenciador.listar_nomes())
    
    if nome_editar != "Selecione...":
        adv = gerenciador.buscar_por_nome(nome_editar)
        if adv:
            with st.form("editar_adv"):
                novo_nome = st.text_input("Nome:", adv.nome)
                novo_nivel = st.slider("Nível (1-5):", 1, 5, adv.nivel)
                novo_estilo = st.selectbox("Estilo:", ["Posse", "Transição", "Direto", "Defensivo"], index=["Posse", "Transição", "Direto", "Defensivo"].index(adv.estilo))
                nova_formacao = st.text_input("Formação:", adv.formacao_base)
                novas_obs = st.text_area("Observações:", adv.observacoes)
                
                if st.form_submit_button("Atualizar Adversário", type="primary"):
                    adv.nome = novo_nome
                    adv.nivel = novo_nivel
                    adv.estilo = novo_estilo
                    adv.formacao_base = nova_formacao
                    adv.observacoes = novas_obs
                    gerenciador.salvar()
                    st.session_state.firebase.salvar_adversarios(gerenciador.adversarios)
                    st.success("Adversário atualizado!")
                    st.rerun()

# =============================================================================
# PÁGINA: CONFIGURAR MODELOS
# =============================================================================

def pagina_configurar_modelos():
    """Página de configuração dos modelos de jogo"""
    st.header("⚙️ Configurar Modelos de Jogo")
    st.info("Defina os modelos de jogo que sua equipe utiliza para análise tática.")
    
    tab_listar, tab_adicionar = st.tabs(["📋 Modelos Existentes", "➕ Adicionar Novo"])
    
    with tab_listar:
        if not st.session_state.modelos:
            st.warning("Nenhum modelo cadastrado ainda.")
        else:
            for i, modelo in enumerate(st.session_state.modelos):
                with st.expander(f"📋 {modelo.nome} (Prioridade: {modelo.prioridade}/5)"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        novo_nome = st.text_input("Nome:", modelo.nome, key=f"nome_{i}")
                        nova_prioridade = st.slider("Prioridade (1-5):", 1, 5, modelo.prioridade, key=f"prio_{i}")
                        nova_descricao = st.text_area("Descrição:", modelo.descricao or "", key=f"desc_{i}")
                    with col2:
                        st.markdown("### Ações")
                        if st.button("🔄 Atualizar", key=f"up_{i}", use_container_width=True):
                            st.session_state.modelos[i] = ModeloJogo(novo_nome, nova_prioridade, nova_descricao)
                            st.session_state.firebase.salvar_modelos(st.session_state.modelos)
                            st.success("Modelo atualizado!")
                            st.rerun()
                        st.markdown("---")
                        if st.button("🗑️ Excluir", key=f"del_{i}", use_container_width=True, type="secondary"):
                            st.session_state[f"confirm_del_{i}"] = True
                        if st.session_state.get(f"confirm_del_{i}", False):
                            st.warning(f"Tem certeza que deseja excluir '{modelo.nome}'?")
                            col_conf1, col_conf2 = st.columns(2)
                            with col_conf1:
                                if st.button("✅ Sim", key=f"conf_sim_{i}", use_container_width=True):
                                    st.session_state.modelos.pop(i)
                                    st.session_state.firebase.salvar_modelos(st.session_state.modelos)
                                    st.session_state[f"confirm_del_{i}"] = False
                                    st.success("Modelo excluído!")
                                    st.rerun()
                            with col_conf2:
                                if st.button("❌ Não", key=f"conf_nao_{i}", use_container_width=True):
                                    st.session_state[f"confirm_del_{i}"] = False
                                    st.rerun()
    
    with tab_adicionar:
        st.subheader("➕ Adicionar Novo Modelo")
        with st.form("form_novo_modelo"):
            novo_nome = st.text_input("Nome do modelo:", placeholder="Ex: Posse de Bola")
            nova_prioridade = st.slider("Prioridade:", 1, 5, 3)
            nova_descricao = st.text_area("Descrição:", placeholder="Descreva as características deste modelo...")
            if st.form_submit_button("✅ Criar Modelo", use_container_width=True, type="primary"):
                if novo_nome:
                    st.session_state.modelos.append(ModeloJogo(novo_nome, nova_prioridade, nova_descricao))
                    st.session_state.firebase.salvar_modelos(st.session_state.modelos)
                    st.success(f"Modelo '{novo_nome}' criado com sucesso!")
                    st.rerun()
                else:
                    st.error("Por favor, insira um nome para o modelo.")

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
