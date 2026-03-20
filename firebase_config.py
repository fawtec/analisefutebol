"""
Configuracao do Firebase Firestore.
Gerencia conexao e operacoes com o banco de dados online.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore

from models import (
    AvaliacaoFase,
    AvaliacaoModelo,
    ContextoAdversario,
    EstatisticasJogo,
    EstatisticasTime,
    Jogo,
)


class FirebaseManager:
    """Gerencia todas as operacoes com o Firebase Firestore."""

    def __init__(self):
        self.db = None
        self.erro_conexao: Optional[str] = None
        self.inicializar()

    def _criar_credencial(self):
        """Monta a credencial a partir do Streamlit secrets ou do JSON local."""
        if "firebase" in st.secrets:
            firebase_creds = {
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
                "universe_domain": st.secrets["firebase"].get("universe_domain", "googleapis.com"),
            }
            return credentials.Certificate(firebase_creds)

        arquivos_credenciais = sorted(Path(".").glob("*firebase-adminsdk*.json"))
        if arquivos_credenciais:
            return credentials.Certificate(str(arquivos_credenciais[0]))

        raise FileNotFoundError(
            "Configuracao do Firebase nao encontrada em `secrets.toml` nem em arquivo JSON local."
        )

    def inicializar(self):
        """Inicializa a conexao com o Firebase."""
        try:
            if not firebase_admin._apps:
                cred = self._criar_credencial()
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            self.erro_conexao = None

        except Exception as e:
            self.erro_conexao = str(e)
            self.db = None
            st.error(f"Erro ao conectar com Firebase: {e}")

    def salvar_jogo(self, jogo: Jogo) -> bool:
        """Salva um jogo no Firestore."""
        try:
            if not self.db:
                return False

            jogo_dict = {
                "id": jogo.id,
                "data": jogo.data.isoformat(),
                "categoria": jogo.categoria,
                "local": jogo.local,
                "formacao_usada": jogo.formacao_usada,
                "gols_pro": jogo.gols_pro,
                "gols_contra": jogo.gols_contra,
                "resultado": jogo.resultado,
                "timestamp": datetime.now(),
                "contexto": {
                    "nome": jogo.contexto.nome,
                    "nivel": jogo.contexto.nivel,
                    "estilo": jogo.contexto.estilo,
                    "formacao_base": jogo.contexto.formacao_base,
                    "observacoes": jogo.contexto.observacoes or "",
                },
                "estatisticas": {
                    "meu_time": {
                        "gols": jogo.estatisticas.meu_time.gols,
                        "finalizacoes": jogo.estatisticas.meu_time.finalizacoes,
                        "finalizacoes_no_alvo": jogo.estatisticas.meu_time.finalizacoes_no_alvo,
                        "escanteios": jogo.estatisticas.meu_time.escanteios,
                        "passes_certos": jogo.estatisticas.meu_time.passes_certos,
                        "passes_errados": jogo.estatisticas.meu_time.passes_errados,
                        "defesas_goleiro": jogo.estatisticas.meu_time.defesas_goleiro,
                        "desarmes": jogo.estatisticas.meu_time.desarmes,
                        "faltas": jogo.estatisticas.meu_time.faltas,
                        "cartoes_amarelos": jogo.estatisticas.meu_time.cartoes_amarelos,
                        "cartoes_vermelhos": jogo.estatisticas.meu_time.cartoes_vermelhos,
                    },
                    "adversario": {
                        "gols": jogo.estatisticas.adversario.gols,
                        "finalizacoes": jogo.estatisticas.adversario.finalizacoes,
                        "finalizacoes_no_alvo": jogo.estatisticas.adversario.finalizacoes_no_alvo,
                        "escanteios": jogo.estatisticas.adversario.escanteios,
                        "passes_certos": jogo.estatisticas.adversario.passes_certos,
                        "passes_errados": jogo.estatisticas.adversario.passes_errados,
                        "defesas_goleiro": jogo.estatisticas.adversario.defesas_goleiro,
                        "desarmes": jogo.estatisticas.adversario.desarmes,
                        "faltas": jogo.estatisticas.adversario.faltas,
                        "cartoes_amarelos": jogo.estatisticas.adversario.cartoes_amarelos,
                        "cartoes_vermelhos": jogo.estatisticas.adversario.cartoes_vermelhos,
                    },
                },
                "avaliacao_modelo": {
                    "fases": [
                        {
                            "nome_fase": fase.nome_fase,
                            "cumprimento_modelo": fase.cumprimento_modelo,
                            "eficacia": fase.eficacia,
                            "observacoes": fase.observacoes or "",
                        }
                        for fase in jogo.avaliacao_modelo.fases
                    ],
                    "media_cumprimento": jogo.avaliacao_modelo.media_cumprimento,
                    "media_eficacia": jogo.avaliacao_modelo.media_eficacia,
                },
            }

            self.db.collection("jogos").document(jogo.id).set(jogo_dict)
            return True

        except Exception as e:
            st.error(f"Erro ao salvar jogo: {e}")
            return False

    def carregar_jogos(self) -> List[Jogo]:
        """Carrega todos os jogos do Firestore."""
        try:
            if not self.db:
                return []

            from utils import gerar_id

            jogos_ref = self.db.collection("jogos").order_by(
                "data", direction=firestore.Query.DESCENDING
            )

            jogos = []
            for doc in jogos_ref.stream():
                dados = doc.to_dict()

                try:
                    contexto = ContextoAdversario(
                        nome=dados["contexto"]["nome"],
                        nivel=dados["contexto"]["nivel"],
                        estilo=dados["contexto"]["estilo"],
                        formacao_base=dados["contexto"]["formacao_base"],
                        observacoes=dados["contexto"].get("observacoes", ""),
                    )

                    meu_time = EstatisticasTime(
                        gols=dados["estatisticas"]["meu_time"]["gols"],
                        finalizacoes=dados["estatisticas"]["meu_time"]["finalizacoes"],
                        finalizacoes_no_alvo=dados["estatisticas"]["meu_time"]["finalizacoes_no_alvo"],
                        escanteios=dados["estatisticas"]["meu_time"]["escanteios"],
                        passes_certos=dados["estatisticas"]["meu_time"]["passes_certos"],
                        passes_errados=dados["estatisticas"]["meu_time"]["passes_errados"],
                        defesas_goleiro=dados["estatisticas"]["meu_time"]["defesas_goleiro"],
                        desarmes=dados["estatisticas"]["meu_time"]["desarmes"],
                        faltas=dados["estatisticas"]["meu_time"]["faltas"],
                        cartoes_amarelos=dados["estatisticas"]["meu_time"]["cartoes_amarelos"],
                        cartoes_vermelhos=dados["estatisticas"]["meu_time"]["cartoes_vermelhos"],
                    )

                    adversario_time = EstatisticasTime(
                        gols=dados["estatisticas"]["adversario"]["gols"],
                        finalizacoes=dados["estatisticas"]["adversario"]["finalizacoes"],
                        finalizacoes_no_alvo=dados["estatisticas"]["adversario"]["finalizacoes_no_alvo"],
                        escanteios=dados["estatisticas"]["adversario"]["escanteios"],
                        passes_certos=dados["estatisticas"]["adversario"]["passes_certos"],
                        passes_errados=dados["estatisticas"]["adversario"]["passes_errados"],
                        defesas_goleiro=dados["estatisticas"]["adversario"]["defesas_goleiro"],
                        desarmes=dados["estatisticas"]["adversario"]["desarmes"],
                        faltas=dados["estatisticas"]["adversario"]["faltas"],
                        cartoes_amarelos=dados["estatisticas"]["adversario"]["cartoes_amarelos"],
                        cartoes_vermelhos=dados["estatisticas"]["adversario"]["cartoes_vermelhos"],
                    )

                    estatisticas = EstatisticasJogo(
                        meu_time=meu_time,
                        adversario=adversario_time,
                    )

                    fases = [
                        AvaliacaoFase(
                            nome_fase=fase["nome_fase"],
                            cumprimento_modelo=fase["cumprimento_modelo"],
                            eficacia=fase["eficacia"],
                            observacoes=fase.get("observacoes", ""),
                        )
                        for fase in dados["avaliacao_modelo"]["fases"]
                    ]

                    avaliacao = AvaliacaoModelo(fases=fases)

                    jogo = Jogo(
                        id=dados.get("id", gerar_id()),
                        data=datetime.fromisoformat(dados["data"]),
                        categoria=dados["categoria"],
                        local=dados["local"],
                        contexto=contexto,
                        formacao_usada=dados["formacao_usada"],
                        gols_pro=dados["gols_pro"],
                        gols_contra=dados["gols_contra"],
                        estatisticas=estatisticas,
                        avaliacao_modelo=avaliacao,
                    )
                    jogos.append(jogo)

                except Exception as e:
                    print(f"Erro ao carregar jogo {doc.id}: {e}")

            return jogos

        except Exception as e:
            st.error(f"Erro ao carregar jogos: {e}")
            return []

    def salvar_adversarios(self, adversarios_dict: Dict) -> bool:
        """Salva todos os adversarios no Firestore."""
        try:
            if not self.db:
                return False

            batch = self.db.batch()

            for adv_id, adv in adversarios_dict.items():
                if hasattr(adv, "__dict__"):
                    adv_dict = dict(adv.__dict__)
                else:
                    adv_dict = dict(adv)

                adv_dict["ultima_atualizacao"] = datetime.now()
                doc_ref = self.db.collection("adversarios").document(adv_id)
                batch.set(doc_ref, adv_dict)

            batch.commit()
            return True

        except Exception as e:
            st.error(f"Erro ao salvar adversarios: {e}")
            return False

    def carregar_adversarios(self) -> Dict:
        """Carrega todos os adversarios do Firestore."""
        try:
            if not self.db:
                return {}

            adversarios = {}
            for doc in self.db.collection("adversarios").stream():
                adversarios[doc.id] = doc.to_dict()

            return adversarios

        except Exception as e:
            st.error(f"Erro ao carregar adversarios: {e}")
            return {}

    def salvar_modelos(self, modelos: List) -> bool:
        """Salva os modelos de jogo no Firestore."""
        try:
            if not self.db:
                return False

            modelos_dict = [
                {
                    "nome": modelo.nome,
                    "prioridade": modelo.prioridade,
                    "descricao": modelo.descricao or "",
                }
                for modelo in modelos
            ]

            self.db.collection("configuracoes").document("modelos").set(
                {
                    "lista": modelos_dict,
                    "atualizado_em": datetime.now(),
                }
            )

            return True

        except Exception as e:
            st.error(f"Erro ao salvar modelos: {e}")
            return False

    def carregar_modelos(self) -> Optional[List]:
        """Carrega os modelos de jogo do Firestore."""
        try:
            if not self.db:
                return None

            doc = self.db.collection("configuracoes").document("modelos").get()
            if doc.exists:
                return doc.to_dict().get("lista", [])

            return None

        except Exception as e:
            st.error(f"Erro ao carregar modelos: {e}")
            return None
