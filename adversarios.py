# adversarios.py
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class Adversario:
    """Classe para armazenar dados de um adversário"""
    id: str
    nome: str
    nivel: int  # 1-5
    estilo: str
    formacao_base: str
    observacoes: str = ""
    vezes_jogado: int = 0
    ultimo_jogo: Optional[str] = None
    vitorias: int = 0
    empates: int = 0
    derrotas: int = 0
    
    @property
    def aproveitamento(self):
        total = self.vitorias + self.empates + self.derrotas
        if total == 0:
            return 0
        return ((self.vitorias * 3 + self.empates) / (total * 3)) * 100


class GerenciadorAdversarios:
    """Gerencia a lista de adversários"""
    
    def __init__(self, arquivo: str = "adversarios.json"):
        self.arquivo = arquivo
        self.adversarios = self.carregar()
    
    def carregar(self) -> Dict[str, Adversario]:
        """Carrega adversários do arquivo JSON"""
        if not os.path.exists(self.arquivo):
            return {}
        
        try:
            with open(self.arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            
            adversarios = {}
            for d in dados:
                adv = Adversario(**d)
                adversarios[adv.id] = adv
            return adversarios
        except:
            return {}
    
    def salvar(self):
        """Salva adversários no arquivo JSON"""
        try:
            dados = [asdict(adv) for adv in self.adversarios.values()]
            with open(self.arquivo, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
    
    def adicionar(self, nome: str, nivel: int, estilo: str, 
                  formacao: str, observacoes: str = "") -> Adversario:
        """Adiciona um novo adversário"""
        from utils import gerar_id
        
        # Verificar se já existe com esse nome
        for adv in self.adversarios.values():
            if adv.nome.lower() == nome.lower():
                return adv  # Retorna o existente
        
        # Criar novo
        novo = Adversario(
            id=gerar_id(),
            nome=nome,
            nivel=nivel,
            estilo=estilo,
            formacao_base=formacao,
            observacoes=observacoes
        )
        
        self.adversarios[novo.id] = novo
        self.salvar()
        return novo
    
    def buscar_por_nome(self, nome: str) -> Optional[Adversario]:
        """Busca adversário pelo nome"""
        for adv in self.adversarios.values():
            if adv.nome.lower() == nome.lower():
                return adv
        return None
    
    def listar_nomes(self) -> List[str]:
        """Retorna lista de nomes para autocomplete"""
        return [adv.nome for adv in self.adversarios.values()]
    
    def atualizar_estatisticas(self, nome: str, gols_pro: int, gols_contra: int):
        """Atualiza estatísticas após um jogo"""
        adv = self.buscar_por_nome(nome)
        if adv:
            adv.vezes_jogado += 1
            adv.ultimo_jogo = datetime.now().strftime("%d/%m/%Y")
            
            if gols_pro > gols_contra:
                adv.vitorias += 1
            elif gols_pro < gols_contra:
                adv.derrotas += 1
            else:
                adv.empates += 1
            
            self.salvar()