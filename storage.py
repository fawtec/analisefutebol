import json
import os
from typing import List
from models import Jogo, jogo_para_dict, dict_para_jogo


def salvar_jogos(jogos: List[Jogo], arquivo: str = "dados.json") -> bool:
    """
    Salva a lista de jogos em um arquivo JSON
    """
    try:
        dados = [jogo_para_dict(j) for j in jogos]
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False


def carregar_jogos(arquivo: str = "dados.json") -> List[Jogo]:
    """
    Carrega a lista de jogos de um arquivo JSON
    """
    if not os.path.exists(arquivo):
        return []
    
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        jogos = []
        for d in dados:
            try:
                jogo = dict_para_jogo(d)
                jogos.append(jogo)
            except Exception as e:
                print(f"Erro ao carregar jogo: {e}")
                continue
        
        return jogos
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return []


def exportar_relatorio(jogos: List[Jogo], formato: str = "json") -> str:
    """
    Exporta os dados em formato específico (futura implementação)
    """
    if formato == "json":
        return json.dumps([jogo_para_dict(j) for j in jogos], indent=2)
    # Futuro: CSV, Excel, etc.
    return ""