import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Analisador Futebol Formação",
    page_icon="⚽",
    layout="wide"
)

# Inicializar dados na sessão
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'nome_time' not in st.session_state:
    st.session_state.nome_time = ""

# Título principal
st.title("⚽ Analisador de Futebol de Formação")
st.markdown("---")

# Sidebar para configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Nome do time
    nome_time = st.text_input("Nome do seu time:", value=st.session_state.nome_time)
    if nome_time:
        st.session_state.nome_time = nome_time
    
    st.markdown("---")
    
    # Menu de navegação
    menu = st.radio(
        "📱 Menu",
        ["📝 Registrar Jogo", 
         "📊 Análise do Último Jogo",
         "📈 Resumo da Temporada",
         "💾 Salvar/Carregar Dados"]
    )
    
    st.markdown("---")
    if st.session_state.historico:
        st.info(f"📊 Total de jogos: {len(st.session_state.historico)}")

# FUNÇÃO: Registrar Jogo
def registrar_jogo():
    st.header("📝 Registrar Novo Jogo")
    
    with st.form("form_jogo"):
        col1, col2 = st.columns(2)
        
        with col1:
            data = st.date_input("Data do jogo:", datetime.now())
            local = st.text_input("Local do jogo:")
            
        with col2:
            adversario = st.text_input("Time adversário:")
        
        st.markdown("### 🏆 Placar")
        col3, col4 = st.columns(2)
        with col3:
            gols_meu = st.number_input(f"Gols do seu time:", min_value=0, value=0, key="gols_meu")
        with col4:
            gols_adv = st.number_input(f"Gols do adversário:", min_value=0, value=0, key="gols_adv")
        
        st.markdown("### ⚽ Estatísticas de Ataque")
        col5, col6, col7 = st.columns(3)
        with col5:
            finalizacoes_meu = st.number_input(f"Finalizações seu time:", min_value=0, key="final_meu")
            finalizacoes_adv = st.number_input(f"Finalizações adversário:", min_value=0, key="final_adv")
        with col6:
            defesas_meu = st.number_input(f"Defesas do seu goleiro:", min_value=0, key="def_meu")
            defesas_adv = st.number_input(f"Defesas goleiro adversário:", min_value=0, key="def_adv")
        with col7:
            escanteios_meu = st.number_input(f"Escanteios a favor:", min_value=0, key="esc_meu")
            escanteios_adv = st.number_input(f"Escanteios contra:", min_value=0, key="esc_adv")
        
        st.markdown("### 🟨 Disciplina")
        col8, col9 = st.columns(2)
        with col8:
            amarelos_meu = st.number_input(f"Cartões amarelos seu time:", min_value=0, key="am_meu")
            vermelhos_meu = st.number_input(f"Cartões vermelhos seu time:", min_value=0, key="verm_meu")
        with col9:
            amarelos_adv = st.number_input(f"Cartões amarelos adversário:", min_value=0, key="am_adv")
            vermelhos_adv = st.number_input(f"Cartões vermelhos adversário:", min_value=0, key="verm_adv")
        
        st.markdown("### 👥 Formação Tática")
        col10, col11 = st.columns(2)
        with col10:
            formacao_meu = st.text_input(f"Formação do seu time:", value="4-4-2", key="form_meu")
        with col11:
            formacao_adv = st.text_input(f"Formação do adversário:", value="4-4-2", key="form_adv")
        
        st.markdown("### 📝 Impressões do Jogo (1 a 5)")
        col12, col13, col14, col15, col16 = st.columns(5)
        with col12:
            posse = st.slider("Posse (1=adv, 5=seu)", 1, 5, 3, key="posse")
        with col13:
            criatividade = st.slider("Criatividade", 1, 5, 3, key="cria")
        with col14:
            defesa = st.slider("Defesa", 1, 5, 3, key="def")
        with col15:
            contra_ataque = st.slider("Contra-ataque", 1, 5, 3, key="contra")
        with col16:
            bola_parada = st.slider("Bola parada", 1, 5, 3, key="bola")
        
        # Botão de submit DENTRO do form
        submitted = st.form_submit_button("✅ Salvar Jogo")
        
        if submitted:
            # Criar dicionário com os dados
            novo_jogo = {
                'data': data.strftime("%d/%m/%Y"),
                'local': local,
                'adversario': adversario,
                'gols_meu': gols_meu,
                'gols_adv': gols_adv,
                'ataque': {
                    'finalizacoes_meu': finalizacoes_meu,
                    'finalizacoes_adv': finalizacoes_adv,
                    'defesas_goleiro_meu': defesas_meu,
                    'defesas_goleiro_adv': defesas_adv,
                    'escanteios_meu': escanteios_meu,
                    'escanteios_adv': escanteios_adv,
                },
                'disciplina': {
                    'cartoes_amarelos_meu': amarelos_meu,
                    'cartoes_amarelos_adv': amarelos_adv,
                    'cartoes_vermelhos_meu': vermelhos_meu,
                    'cartoes_vermelhos_adv': vermelhos_adv,
                },
                'formacao_meu': formacao_meu,
                'formacao_adv': formacao_adv,
                'impressoes': {
                    'posse_bola': posse,
                    'criatividade': criatividade,
                    'defesa': defesa,
                    'contra_ataques': contra_ataque,
                    'bola_parada': bola_parada
                }
            }
            
            # Adicionar ao histórico
            st.session_state.historico.append(novo_jogo)
            st.success("✅ Jogo registrado com sucesso!")

# FUNÇÃO: Análise do Último Jogo
def analisar_ultimo_jogo():
    st.header("📊 Análise do Último Jogo")
    
    if not st.session_state.historico:
        st.warning("⚠️ Nenhum jogo registrado ainda!")
        return
    
    ultimo_jogo = st.session_state.historico[-1]
    
    # Informações básicas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Data", ultimo_jogo['data'])
    with col2:
        st.metric("Local", ultimo_jogo['local'])
    with col3:
        st.metric("Adversário", ultimo_jogo['adversario'])
    
    # Placar
    st.markdown("### 🏆 Placar Final")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(st.session_state.nome_time, ultimo_jogo['gols_meu'])
    with col5:
        if ultimo_jogo['gols_meu'] > ultimo_jogo['gols_adv']:
            st.success("✅ VITÓRIA")
        elif ultimo_jogo['gols_meu'] < ultimo_jogo['gols_adv']:
            st.error("❌ DERROTA")
        else:
            st.warning("⚖️ EMPATE")
    with col6:
        st.metric(ultimo_jogo['adversario'], ultimo_jogo['gols_adv'])
    
    # Formações
    col7, col8 = st.columns(2)
    with col7:
        st.info(f"📋 Formação {st.session_state.nome_time}: **{ultimo_jogo['formacao_meu']}**")
    with col8:
        st.info(f"📋 Formação {ultimo_jogo['adversario']}: **{ultimo_jogo['formacao_adv']}**")
    
    # Estatísticas em colunas
    st.markdown("### ⚽ Estatísticas da Partida")
    
    ataque = ultimo_jogo['ataque']
    col9, col10, col11 = st.columns(3)
    
    with col9:
        total_finalizacoes = ataque['finalizacoes_meu'] + ataque['finalizacoes_adv']
        if total_finalizacoes > 0:
            perc_meu = (ataque['finalizacoes_meu'] / total_finalizacoes) * 100
            st.metric("Finalizações", 
                     f"{ataque['finalizacoes_meu']} x {ataque['finalizacoes_adv']}",
                     f"{perc_meu:.1f}% seu time")
    
    with col10:
        st.metric("Defesas", 
                 f"{ataque['defesas_goleiro_meu']} x {ataque['defesas_goleiro_adv']}")
    
    with col11:
        st.metric("Escanteios", 
                 f"{ataque['escanteios_meu']} x {ataque['escanteios_adv']}")
    
    # Eficiência ofensiva
    if ataque['finalizacoes_meu'] > 0:
        eficiencia = (ultimo_jogo['gols_meu'] / ataque['finalizacoes_meu']) * 100
        st.metric("🎯 Eficiência Ofensiva", f"{eficiencia:.1f}%")
    
    # Disciplina
    st.markdown("### 🟨 Disciplina")
    disc = ultimo_jogo['disciplina']
    col12, col13 = st.columns(2)
    with col12:
        st.metric("Cartões Amarelos", 
                 f"{disc['cartoes_amarelos_meu']} x {disc['cartoes_amarelos_adv']}")
    with col13:
        st.metric("Cartões Vermelhos", 
                 f"{disc['cartoes_vermelhos_meu']} x {disc['cartoes_vermelhos_adv']}")
    
    # Impressões
    st.markdown("### 📊 Impressões do Jogo")
    imp = ultimo_jogo['impressoes']
    
    # Gráfico de radar das impressões
    categorias = ['Posse', 'Criatividade', 'Defesa', 'Contra-ataque', 'Bola Parada']
    valores = [imp['posse_bola'], imp['criatividade'], imp['defesa'], 
               imp['contra_ataques'], imp['bola_parada']]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself',
        name=st.session_state.nome_time
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )),
        showlegend=False,
        title="Desempenho por Categoria"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Média
    media = sum(valores) / len(valores)
    if media >= 4:
        st.success(f"📈 Média de desempenho: {media:.1f}/5 - EXCELENTE!")
    elif media >= 3:
        st.info(f"📈 Média de desempenho: {media:.1f}/5 - BOM")
    else:
        st.warning(f"📈 Média de desempenho: {media:.1f}/5 - PRECISA MELHORAR")

# FUNÇÃO: Resumo da Temporada
def resumo_temporada():
    st.header("📈 Resumo da Temporada")
    
    if not st.session_state.historico:
        st.warning("⚠️ Nenhum jogo registrado ainda!")
        return
    
    total_jogos = len(st.session_state.historico)
    vitorias = sum(1 for j in st.session_state.historico if j['gols_meu'] > j['gols_adv'])
    empates = sum(1 for j in st.session_state.historico if j['gols_meu'] == j['gols_adv'])
    derrotas = sum(1 for j in st.session_state.historico if j['gols_meu'] < j['gols_adv'])
    
    gols_pro = sum(j['gols_meu'] for j in st.session_state.historico)
    gols_contra = sum(j['gols_adv'] for j in st.session_state.historico)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Jogos", total_jogos)
    with col2:
        st.metric("Vitórias", vitorias)
    with col3:
        st.metric("Empates", empates)
    with col4:
        st.metric("Derrotas", derrotas)
    
    # Aproveitamento
    if total_jogos > 0:
        aproveitamento = ((vitorias * 3 + empates) / (total_jogos * 3)) * 100
        st.metric("📊 Aproveitamento", f"{aproveitamento:.1f}%")
    
    # Gols
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("⚽ Gols Marcados", gols_pro)
    with col6:
        st.metric("🥅 Gols Sofridos", gols_contra)
    with col7:
        st.metric("📊 Saldo de Gols", gols_pro - gols_contra)
    
    # Gráfico de evolução dos gols
    dados_grafico = []
    for i, jogo in enumerate(st.session_state.historico, 1):
        dados_grafico.append({
            'Jogo': i,
            'Data': jogo['data'],
            'Adversário': jogo['adversario'],
            'Gols Meu Time': jogo['gols_meu'],
            'Gols Adversário': jogo['gols_adv']
        })
    
    df = pd.DataFrame(dados_grafico)
    
    fig = px.line(df, x='Jogo', y=['Gols Meu Time', 'Gols Adversário'],
                  title="Evolução de Gols por Jogo",
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de jogos
    st.markdown("### 📋 Histórico de Jogos")
    
    # Preparar dados para tabela
    tabela = []
    for jogo in st.session_state.historico:
        resultado = "🏆" if jogo['gols_meu'] > jogo['gols_adv'] else "😞" if jogo['gols_meu'] < jogo['gols_adv'] else "🤝"
        tabela.append({
            'Data': jogo['data'],
            'Adversário': jogo['adversario'],
            'Placar': f"{jogo['gols_meu']} x {jogo['gols_adv']}",
            'Resultado': resultado,
            'Formação': jogo['formacao_meu']
        })
    
    df_tabela = pd.DataFrame(tabela)
    st.dataframe(df_tabela, use_container_width=True)

# FUNÇÃO: Salvar/Carregar Dados
def gerenciar_dados():
    st.header("💾 Gerenciar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💾 Salvar Dados")
        if st.button("💾 Salvar em arquivo JSON"):
            if st.session_state.historico:
                nome_arquivo = f"dados_{st.session_state.nome_time.replace(' ', '_')}.json"
                
                dados_completos = {
                    'time': st.session_state.nome_time,
                    'historico': st.session_state.historico
                }
                
                with open(nome_arquivo, 'w', encoding='utf-8') as f:
                    json.dump(dados_completos, f, ensure_ascii=False, indent=2)
                
                st.success(f"✅ Dados salvos em {nome_arquivo}")
                
                # Mostrar caminho
                caminho = os.path.abspath(nome_arquivo)
                st.info(f"📁 Arquivo salvo em: {caminho}")
            else:
                st.warning("⚠️ Nenhum dado para salvar!")
    
    with col2:
        st.subheader("📂 Carregar Dados")
        arquivo = st.file_uploader("Escolha um arquivo JSON", type=['json'])
        
        if arquivo is not None:
            try:
                dados_carregados = json.load(arquivo)
                st.session_state.nome_time = dados_carregados['time']
                st.session_state.historico = dados_carregados['historico']
                st.success(f"✅ Dados carregados - Time: {dados_carregados['time']}")
                st.info(f"📊 Total de jogos: {len(dados_carregados['historico'])}")
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo: {e}")

# ROTEAMENTO DO MENU
if menu == "📝 Registrar Jogo":
    registrar_jogo()
elif menu == "📊 Análise do Último Jogo":
    analisar_ultimo_jogo()
elif menu == "📈 Resumo da Temporada":
    resumo_temporada()
elif menu == "💾 Salvar/Carregar Dados":
    gerenciar_dados()