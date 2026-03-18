from datetime import datetime
import random
import string


def gerar_id() -> str:
    """Gera um ID único para o jogo"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{timestamp}_{random_str}"


def formatar_data(data: datetime) -> str:
    """Formata data para exibição"""
    return data.strftime("%d/%m/%Y %H:%M")


def calcular_idade(data_nascimento: datetime) -> int:
    """Calcula idade baseado na data de nascimento"""
    hoje = datetime.now()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )