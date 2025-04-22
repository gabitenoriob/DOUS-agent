import pandas as pd

# Nome do arquivo CSV e do arquivo XLS
csv_file = 'portarias.csv'
xls_file = 'portarias.xls'

# Ler o CSV, ignorando linhas problemáticas
df = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig')

# Salvar como XLSX
df.to_excel('dfs.xlsx', index=False, engine='openpyxl')

print(f'Arquivo salvo como dfs.xlsx')