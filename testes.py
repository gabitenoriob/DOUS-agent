#Conferir se as tabelas estão sendo extraidas corretamente
# e se o CSV e XLSX estão sendo salvos corretamente.
from datetime import datetime
import re


def validate_name(name):
    """Valida se o nome não é numérico e não está vazio."""
    if isinstance(name, str) and not name.isdigit() and name.strip():
        return name
    else:
        print(f"Nome inválido: {name}")
        return None
def validate_cnes(cnes):
    """Valida se o CNES tem exatamente 7 dígitos numéricos."""
    if isinstance(cnes, str) and cnes.isdigit() and len(cnes) == 7:
        return cnes
    else:
        print(f"CNES inválido: {cnes}")
        return None
def validate_date(date_str):
    """Valida se a data está no formato dd/mm/yyyy."""
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return date_str
    except ValueError:
        print(f"Data inválida: {date_str}")
        return None
    
def validate_cpf(cpf):
    """Valida se o CPF tem exatamente 11 dígitos numéricos."""
    if isinstance(cpf, str) and cpf.isdigit() and len(cpf) == 11:
        return True
    else:
        print(f"CPF inválido: {cpf}")
        return False
    
def validate_cnpj(cnpj):
    """Valida se o CNPJ tem 14 dígitos ou está no formato XX.XXX.XXX/0001-XX"""
    print(f"CNPJ sendo validado....: {cnpj}")
    if not isinstance(cnpj, str):
        return False

    cnpj = cnpj.strip()
    
    # CNPJ só com números
    if cnpj.isdigit() and len(cnpj) == 14:
        return cnpj

    # CNPJ formatado
    pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
    if re.match(pattern, cnpj):
        return cnpj

    print(f"CNPJ inválido: {cnpj}")
    return None

def validate_municipio(municipio):
    """Valida se o município não é numérico e não está vazio."""
    if isinstance(municipio, str) and not municipio.isdigit() and municipio.strip():
        return municipio
    else:
        print(f"Município inválido: {municipio}")
        return None
def validate_uf(uf):
    """Valida se a UF tem exatamente 2 letras."""
    if isinstance(uf, str) and len(uf) == 2 and uf.isalpha():
        return uf.upper()
    else:
        print(f"UF inválida: {uf}")
        return None

def validate_ibge(ibge):
    """Valida se o código IBGE tem exatamente 6 dígitos numéricos."""
    if isinstance(ibge, str) and ibge.isdigit() and len(ibge) == 6:
        return ibge
    else:
        print(f"IBGE inválido: {ibge}")
        return None


