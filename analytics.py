"""
Módulo de análise e cálculos estatísticos
"""

from typing import Dict, Tuple, List
from models import Jogo


def calcular_metricas_jogo(jogo: Jogo) -> Dict:
    """
    Calcula todas as métricas percentuais do jogo
    """
    # Passes
    passes_meu = jogo.estatisticas.meu_time.total_passes
    passes_adv = jogo.estatisticas.adversario.total_passes
    total_passes = passes_meu + passes_adv
    
    posse_meu = (passes_meu / total_passes * 100) if total_passes > 0 else 50
    posse_adv = (passes_adv / total_passes * 100) if total_passes > 0 else 50
    
    # Taxa de passes
    taxa_passe_meu = (jogo.estatisticas.meu_time.passes_certos / passes_meu * 100) if passes_meu > 0 else 0
    taxa_passe_adv = (jogo.estatisticas.adversario.passes_certos / passes_adv * 100) if passes_adv > 0 else 0
    
    # Finalizações
    total_finalizacoes = jogo.estatisticas.meu_time.finalizacoes + jogo.estatisticas.adversario.finalizacoes
    perc_finalizacoes_meu = (jogo.estatisticas.meu_time.finalizacoes / total_finalizacoes * 100) if total_finalizacoes > 0 else 50
    perc_finalizacoes_adv = (jogo.estatisticas.adversario.finalizacoes / total_finalizacoes * 100) if total_finalizacoes > 0 else 50
    
    # Precisão
    precisao_meu = (jogo.estatisticas.meu_time.finalizacoes_no_alvo / jogo.estatisticas.meu_time.finalizacoes * 100) if jogo.estatisticas.meu_time.finalizacoes > 0 else 0
    precisao_adv = (jogo.estatisticas.adversario.finalizacoes_no_alvo / jogo.estatisticas.adversario.finalizacoes * 100) if jogo.estatisticas.adversario.finalizacoes > 0 else 0
    
    # Eficiência
    eficiencia_meu = (jogo.gols_pro / jogo.estatisticas.meu_time.finalizacoes * 100) if jogo.estatisticas.meu_time.finalizacoes > 0 else 0
    eficiencia_adv = (jogo.gols_contra / jogo.estatisticas.adversario.finalizacoes * 100) if jogo.estatisticas.adversario.finalizacoes > 0 else 0
    
    return {
        'posse': {'meu_time': posse_meu, 'adversario': posse_adv},
        'passes': {'meu_time': taxa_passe_meu, 'adversario': taxa_passe_adv},
        'finalizacoes': {'meu_time': perc_finalizacoes_meu, 'adversario': perc_finalizacoes_adv},
        'precisao': {'meu_time': precisao_meu, 'adversario': precisao_adv},
        'eficiencia': {'meu_time': eficiencia_meu, 'adversario': eficiencia_adv}
    }


def indice_desenvolvimento(jogo: Jogo) -> float:
    """
    Calcula o índice de desenvolvimento do time
    """
    metricas = calcular_metricas_jogo(jogo)
    
    posse_score = metricas['posse']['meu_time']
    passe_score = metricas['passes']['meu_time']
    modelo_score = jogo.avaliacao_modelo.media_cumprimento * 20
    
    return round(
        posse_score * 0.3 +
        passe_score * 0.3 +
        modelo_score * 0.4,
        1
    )


def calcular_dominio(
    posse_m, final_m, precisao_m, passes_m, eficiencia_m,
    posse_a, final_a, precisao_a, passes_a, eficiencia_a
) -> List[str]:
    """
    Calcula quais aspectos o time dominou
    """
    dominios = []
    
    if posse_m > 55:
        dominios.append("Posse de Bola")
    if final_m > 55:
        dominios.append("Finalizações")
    if precisao_m > precisao_a + 10:
        dominios.append("Precisão")
    if passes_m > passes_a + 5:
        dominios.append("Passes")
    if eficiencia_m > eficiencia_a + 10:
        dominios.append("Eficiência Ofensiva")
    
    return dominios