"""
Configuração do Firebase Firestore
Gerencia a conexão e operações com o banco de dados online
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import Jogo, ContextoAdversario, EstatisticasJogo, EstatisticasTime, AvaliacaoModelo, AvaliacaoFase


class FirebaseManager:
    """Gerencia todas as operações com o Firebase Firestore"""
    
    def __init__(self):
        self.db = None
        self.inicializar()
    
    def inicializar(self):
        """Inicializa a conexão com o Firebase usando secrets do Streamlit"""
        try:
            # Verificar se já foi inicializado
            if not firebase_admin._apps:
                # Verificar se as secrets existem
                if "firebase" not in st.secrets:
                    st.error("🔴 Configuração do Firebase não encontrada. Adicione as secrets no Streamlit Cloud.")
                    return
                
                # Carregar credenciais das secrets
                firebase_creds = {
                    "type": st.secrets["firebase"]["type"],
                    "project_id": st.secrets["firebase"]["project_id"],
                    "private_key_id": st.secrets["firebase"]["private_key_id"],
                    "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
                    "client_email": st.secrets["firebase"]["client_email"],
                    "client_id": st.secrets["firebase"]["client_id"],
                    "auth_uri": st.secrets["firebase"]["auth_uri"],
                    "token_uri": st.secrets["firebase"]["token_uri"],
                    "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                    "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
                    "universe_domain": st.secrets["firebase"].get("universe_domain", "googleapis.com")
                }
                
                cred = credentials.Certificate(firebase_creds)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Conectado ao Firebase com sucesso!")
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar com Firebase: {str(e)}")
            self.db = None
    
    def salvar_jogo(self, jogo: Jogo) -> bool:
        """Salva um jogo no Firestore"""
        try:
            if not self.db:
                return False
            
            # Converter jogo para dicionário
            jogo_dict = {
                'id': jogo.id,
                'data': jogo.data.isoformat(),
                'categoria': jogo.categoria,
                'local': jogo.local,
                'formacao_usada': jogo.formacao_usada,
                'gols_pro': jogo.gols_pro,
                'gols_contra': jogo.gols_contra,
                'resultado': jogo.resultado,
                'timestamp': datetime.now(),
                'contexto': {
                    'nome': jogo.contexto.nome,
                    'nivel': jogo.contexto.nivel,
                    'estilo': jogo.contexto.estilo,
                    'formacao_base': jogo.contexto.formacao_base,
                    'observacoes': jogo.contexto.observacoes or ""
                },
                'estatisticas': {
                    'meu_time': {
                        'gols': jogo.estatisticas.meu_time.gols,
                        'finalizacoes': jogo.estatisticas.meu_time.finalizacoes,
                        'finalizacoes_no_alvo': jogo.estatisticas.meu_time.finalizacoes_no_alvo,
                        'escanteios': jogo.estatisticas.meu_time.escanteios,
                        'passes_certos': jogo.estatisticas.meu_time.passes_certos,
                        'passes_errados': jogo.estatisticas.meu_time.passes_errados,
                        'defesas_goleiro': jogo.estatisticas.meu_time.defesas_goleiro,
                        'desarmes': jogo.estatisticas.meu_time.desarmes,
                        'faltas': jogo.estatisticas.meu_time.faltas,
                        'cartoes_amarelos': jogo.estatisticas.meu_time.cartoes_amarelos,
                        'cartoes_vermelhos': jogo.estatisticas.meu_time.cartoes_vermelhos
                    },
                    'adversario': {
                        'gols': jogo.estatisticas.adversario.gols,
                        'finalizacoes': jogo.estatisticas.adversario.finalizacoes,
                        'finalizacoes_no_alvo': jogo.estatisticas.adversario.finalizacoes_no_alvo,
                        'escanteios': jogo.estatisticas.adversario.escanteios,
                        'passes_certos': jogo.estatisticas.adversario.passes_certos,
                        'passes_errados': jogo.estatisticas.adversario.passes_errados,
                        'defesas_goleiro': jogo.estatisticas.adversario.defesas_goleiro,
                        'desarmes': jogo.estatisticas.adversario.desarmes,
                        'faltas': jogo.estatisticas.adversario.faltas,
                        'cartoes_amarelos': jogo.estatisticas.adversario.cartoes_amarelos,
                        'cartoes_vermelhos': jogo.estatisticas.adversario.cartoes_vermelhos
                    }
                },
                'avaliacao_modelo': {
                    'fases': [
                        {
                            'nome_fase': fase.nome_fase,
                            'cumprimento_modelo': fase.cumprimento_modelo,
                            'eficacia': fase.eficacia,
                            'observacoes': fase.observacoes or ""
                        }
                        for fase in jogo.avaliacao_modelo.fases
                    ],
                    'media_cumprimento': jogo.avaliacao_modelo.media_cumprimento,
                    'media_eficacia': jogo.avaliacao_modelo.media_eficacia
                }
            }
            
            # Salvar no Firestore
            self.db.collection('jogos').document(jogo.id).set(jogo_dict)
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar jogo: {str(e)}")
            return False
    
    def carregar_jogos(self) -> List[Jogo]:
        """Carrega todos os jogos do Firestore"""
        try:
            if not self.db:
                return []
            
            from models import Jogo, ContextoAdversario, EstatisticasTime, EstatisticasJogo, AvaliacaoModelo, AvaliacaoFase
            from utils import gerar_id
            
            jogos_ref = self.db.collection('jogos').order_by('data', direction=firestore.Query.DESCENDING)
            jogos_docs = jogos_ref.stream()
            
            jogos = []
            for doc in jogos_docs:
                dados = doc.to_dict()
                try:
                    # Criar contexto
                    contexto = ContextoAdversario(
                        nome=dados['contexto']['nome'],
                        nivel=dados['contexto']['nivel'],
                        estilo=dados['contexto']['estilo'],
                        formacao_base=dados['contexto']['formacao_base'],
                        observacoes=dados['contexto'].get('observacoes', "")
                    )
                    
                    # Criar estatísticas do meu time
                    meu_time = EstatisticasTime(
                        gols=dados['estatisticas']['meu_time']['gols'],
                        finalizacoes=dados['estatisticas']['meu_time']['finalizacoes'],
                        finalizacoes_no_alvo=dados['estatisticas']['meu_time']['finalizacoes_no_alvo'],
                        escanteios=dados['estatisticas']['meu_time']['escanteios'],
                        passes_certos=dados['estatisticas']['meu_time']['passes_certos'],
                        passes_errados=dados['estatisticas']['meu_time']['passes_errados'],
                        defesas_goleiro=dados['estatisticas']['meu_time']['defesas_goleiro'],
                        desarmes=dados['estatisticas']['meu_time']['desarmes'],
                        faltas=dados['estatisticas']['meu_time']['faltas'],
                        cartoes_amarelos=dados['estatisticas']['meu_time']['cartoes_amarelos'],
                        cartoes_vermelhos=dados['estatisticas']['meu_time']['cartoes_vermelhos']
                    )
                    
                    # Criar estatísticas do adversário
                    adversario_time = EstatisticasTime(
                        gols=dados['estatisticas']['adversario']['gols'],
                        finalizacoes=dados['estatisticas']['adversario']['finalizacoes'],
                        finalizacoes_no_alvo=dados['estatisticas']['adversario']['finalizacoes_no_alvo'],
                        escanteios=dados['estatisticas']['adversario']['escanteios'],
                        passes_certos=dados['estatisticas']['adversario']['passes_certos'],
                        passes_errados=dados['estatisticas']['adversario']['passes_errados'],
                        defesas_goleiro=dados['estatisticas']['adversario']['defesas_goleiro'],
                        desarmes=dados['estatisticas']['adversario']['desarmes'],
                        faltas=dados['estatisticas']['adversario']['faltas'],
                        cartoes_amarelos=dados['estatisticas']['adversario']['cartoes_amarelos'],
                        cartoes_vermelhos=dados['estatisticas']['adversario']['cartoes_vermelhos']
                    )
                    
                    # Criar estatísticas do jogo
                    estatisticas = EstatisticasJogo(
                        meu_time=meu_time,
                        adversario=adversario_time
                    )
                    
                    # Criar avaliação
                    fases = []
                    for fase_dict in dados['avaliacao_modelo']['fases']:
                        fases.append(AvaliacaoFase(
                            nome_fase=fase_dict['nome_fase'],
                            cumprimento_modelo=fase_dict['cumprimento_modelo'],
                            eficacia=fase_dict['eficacia'],
                            observacoes=fase_dict.get('observacoes', "")
                        ))
                    
                    avaliacao = AvaliacaoModelo(fases=fases)
                    
                    # Criar jogo
                    jogo = Jogo(
                        id=dados.get('id', gerar_id()),
                        data=datetime.fromisoformat(dados['data']),
                        categoria=dados['categoria'],
                        local=dados['local'],
                        contexto=contexto,
                        formacao_usada=dados['formacao_usada'],
                        gols_pro=dados['gols_pro'],
                        gols_contra=dados['gols_contra'],
                        estatisticas=estatisticas,
                        avaliacao_modelo=avaliacao
                    )
                    
                    jogos.append(jogo)
                    
                except Exception as e:
                    print(f"Erro ao carregar jogo: {e}")
                    continue
            
            return jogos
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar jogos: {str(e)}")
            return []
    
    def salvar_adversarios(self, adversarios_dict: Dict) -> bool:
        """Salva todos os adversários no Firestore"""
        try:
            if not self.db:
                return False
            
            batch = self.db.batch()
            
            for adv_id, adv in adversarios_dict.items():
                # Converter para dicionário
                if hasattr(adv, '__dict__'):
                    adv_dict = adv.__dict__
                else:
                    adv_dict = adv
                
                # Adicionar timestamp
                adv_dict['ultima_atualizacao'] = datetime.now()
                
                # Salvar no batch
                doc_ref = self.db.collection('adversarios').document(adv_id)
                batch.set(doc_ref, adv_dict)
            
            # Executar batch
            batch.commit()
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar adversários: {str(e)}")
            return False
    
    def carregar_adversarios(self) -> Dict:
        """Carrega todos os adversários do Firestore"""
        try:
            if not self.db:
                return {}
            
            adv_ref = self.db.collection('adversarios').stream()
            adversarios = {}
            
            for doc in adv_ref:
                adversarios[doc.id] = doc.to_dict()
            
            return adversarios
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar adversários: {str(e)}")
            return {}
    
    def salvar_modelos(self, modelos: List) -> bool:
        """Salva os modelos de jogo no Firestore"""
        try:
            if not self.db:
                return False
            
            # Converter modelos para dicionário
            modelos_dict = []
            for modelo in modelos:
                modelos_dict.append({
                    'nome': modelo.nome,
                    'prioridade': modelo.prioridade,
                    'descricao': modelo.descricao or ""
                })
            
            # Salvar como um único documento
            self.db.collection('configuracoes').document('modelos').set({
                'lista': modelos_dict,
                'atualizado_em': datetime.now()
            })
            
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar modelos: {str(e)}")
            return False
    
    def carregar_modelos(self) -> Optional[List]:
        """Carrega os modelos de jogo do Firestore"""
        try:
            if not self.db:
                return None
            
            doc = self.db.collection('configuracoes').document('modelos').get()
            
            if doc.exists:
                return doc.to_dict().get('lista', [])
            return None
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar modelos: {str(e)}")
            return None