from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import json

# =========================
# MODELO DE JOGO (DNA FIXO)
# =========================

@dataclass
class ModeloJogo:
    """Define o modelo de jogo do time (filosofia de jogo)"""
    nome: str  # "Posse de Bola", "Contra-ataque", "Pressão Alta", etc.
    prioridade: int  # 1-5 (1 = baixa, 5 = alta)
    descricao: Optional[str] = None
    
    def __post_init__(self):
        if not 1 <= self.prioridade <= 5:
            raise ValueError("Prioridade deve ser entre 1 e 5")


# =========================
# CONTEXTO DO ADVERSÁRIO
# =========================

@dataclass
class ContextoAdversario:
    """Informações sobre o adversário"""
    nome: str
    nivel: int  # 1-5 (1 = fraco, 5 = forte)
    estilo: str  # "Posse", "Transição", "Direto", "Defensivo"
    formacao_base: str  # "4-4-2", "4-3-3", etc.
    observacoes: Optional[str] = None
    
    def __post_init__(self):
        if not 1 <= self.nivel <= 5:
            raise ValueError("Nível deve ser entre 1 e 5")


# =========================
# ESTATÍSTICAS DO TIME
# =========================

@dataclass
class EstatisticasTime:
    """Estatísticas de um time em uma partida"""
    # Ataque
    gols: int = 0
    finalizacoes: int = 0
    finalizacoes_no_alvo: int = 0
    escanteios: int = 0
    impedimentos: int = 0
    
    # Posse e passes (sem campo de posse - será calculado)
    passes_certos: int = 0
    passes_errados: int = 0
    
    # Defesa
    defesas_goleiro: int = 0
    desarmes: int = 0
    interceptacoes: int = 0
    
    # Disciplina
    faltas: int = 0
    cartoes_amarelos: int = 0
    cartoes_vermelhos: int = 0
    
    def __post_init__(self):
        if self.finalizacoes_no_alvo > self.finalizacoes:
            raise ValueError("Finalizações no alvo não podem ser maiores que total")
    
    @property
    def total_passes(self):
        return self.passes_certos + self.passes_errados
    
    @property
    def taxa_acerto_passe(self):
        if self.total_passes == 0:
            return 0.0
        return (self.passes_certos / self.total_passes) * 100


# =========================
# ESTATÍSTICAS COMPLETAS DO JOGO
# =========================

@dataclass
class EstatisticasJogo:
    """Estatísticas completas do jogo (ambos os times)"""
    meu_time: EstatisticasTime
    adversario: EstatisticasTime
    
    # Método para calcular posse baseada nos passes
    def calcular_posse_bola(self):
        """Calcula a porcentagem de posse baseada nos passes de cada time"""
        passes_meu = self.meu_time.passes_certos + self.meu_time.passes_errados
        passes_adv = self.adversario.passes_certos + self.adversario.passes_errados
        total_passes = passes_meu + passes_adv
        
        if total_passes == 0:
            return 50.0  # Se não houver passes, considera 50%
        
        posse_meu = (passes_meu / total_passes) * 100
        return round(posse_meu, 1)


# =========================
# AVALIAÇÃO POR FASE DO JOGO
# =========================

@dataclass
class AvaliacaoFase:
    """Avaliação de uma fase específica do jogo"""
    nome_fase: str  # "Ofensiva", "Defensiva", "Transição", "Bola Parada"
    cumprimento_modelo: int  # 1-5 (quanto seguiu o planejado)
    eficacia: int  # 1-5 (resultado prático)
    observacoes: Optional[str] = None
    
    def __post_init__(self):
        if not 1 <= self.cumprimento_modelo <= 5:
            raise ValueError("Cumprimento deve ser entre 1 e 5")
        if not 1 <= self.eficacia <= 5:
            raise ValueError("Eficácia deve ser entre 1 e 5")


@dataclass
class AvaliacaoModelo:
    """Avaliação completa do modelo de jogo"""
    fases: List[AvaliacaoFase]
    
    def __post_init__(self):
        if not self.fases:
            raise ValueError("Pelo menos uma fase deve ser avaliada")
    
    @property
    def media_cumprimento(self):
        return sum(f.cumprimento_modelo for f in self.fases) / len(self.fases)
    
    @property
    def media_eficacia(self):
        return sum(f.eficacia for f in self.fases) / len(self.fases)


# =========================
# ENTIDADE PRINCIPAL - JOGO
# =========================

@dataclass
class Jogo:
    """Representa um jogo completo com todas as informações"""
    data: datetime
    categoria: str  # "Sub-15", "Sub-17", "Sub-20", "Profissional"
    local: str
    contexto: ContextoAdversario
    formacao_usada: str
    estatisticas: EstatisticasJogo
    avaliacao_modelo: AvaliacaoModelo
    gols_pro: int = 0
    gols_contra: int = 0
    id: Optional[str] = None
    
    def __post_init__(self):
        # Garantir que gols estão consistentes com estatísticas
        if self.estatisticas.meu_time.gols != self.gols_pro:
            self.estatisticas.meu_time.gols = self.gols_pro
        if self.estatisticas.adversario.gols != self.gols_contra:
            self.estatisticas.adversario.gols = self.gols_contra
    
    @property
    def resultado(self):
        if self.gols_pro > self.gols_contra:
            return "Vitória"
        elif self.gols_pro < self.gols_contra:
            return "Derrota"
        else:
            return "Empate"
    
    @property
    def saldo_gols(self):
        return self.gols_pro - self.gols_contra


# =========================
# FUNÇÃO PARA CONVERSÃO
# =========================

def jogo_para_dict(jogo: Jogo) -> dict:
    """Converte objeto Jogo para dicionário (para salvar em JSON)"""
    d = asdict(jogo)
    # Converte datetime para string
    d['data'] = jogo.data.isoformat()
    return d


def dict_para_jogo(d: dict) -> Jogo:
    """Converte dicionário para objeto Jogo (para carregar do JSON)"""
    # Converte string de volta para datetime
    d['data'] = datetime.fromisoformat(d['data'])
    
    # Reconstrói objetos aninhados
    d['contexto'] = ContextoAdversario(**d['contexto'])
    
    # Reconstrói estatísticas
    d['estatisticas'] = EstatisticasJogo(
        meu_time=EstatisticasTime(**d['estatisticas']['meu_time']),
        adversario=EstatisticasTime(**d['estatisticas']['adversario'])
    )
    
    # Reconstrói avaliação
    fases = [AvaliacaoFase(**f) for f in d['avaliacao_modelo']['fases']]
    d['avaliacao_modelo'] = AvaliacaoModelo(fases=fases)
    
    return Jogo(**d)