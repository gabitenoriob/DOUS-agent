import os
import time
import requests
import zipfile
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import ssl
import certifi
import urllib3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Defina o caminho do ChromeDriver manualmente
caminho_chromedriver = "C:/Users/gabrielabtn/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# Configurar o serviço do ChromeDriver
service = Service(caminho_chromedriver)
driver = webdriver.Chrome(service=service)

# Teste abrindo uma página
driver.get("https://www.google.com")




# Mapeamento dos meses em português
MESES_PORTUGUES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def baixar_dou(ano, mes, diretorio_destino):
    """
    Baixa e extrai todos os arquivos XML do Diário Oficial da União (DOU) para um ano e mês específicos.

    Args:
        ano (int): O ano desejado (ex: 2024).
        mes (int): O mês desejado (1 a 12).
        diretorio_destino (str): O diretório onde os arquivos serão salvos.
    """
    if mes not in MESES_PORTUGUES:
        print("Mês inválido. Use um número de 1 a 12.")
        return

    mes_extenso = MESES_PORTUGUES[mes]

    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)

    # Configurar o Selenium para usar o Chrome WebDriver
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    #options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Acessar a página principal
        mes_extenso_codificado = urllib.parse.quote(mes_extenso, safe="")
        url_base = f"https://www.in.gov.br/acesso-a-informacao/dados-abertos/base-de-dados?ano={ano}&mes={mes_extenso_codificado}"
        try:
            driver.get(url_base)
            print(f"Acessando: {url_base}")  # Depuração: veja se a URL está correta
        except Exception as e:
            print(f"Erro ao carregar a página: {e}")
            input("Pressione Enter para fechar...")
            driver.quit()
            return


        # Esperar carregar o seletor de ano e selecionar o ano correto
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ano-dados")))
            print("Seletor de ano encontrado.")
        except Exception as e:
            print(f"Erro ao encontrar seletor de ano: {e}")
            input("Pressione Enter para fechar...")
            driver.quit()
            return

        Select(driver.find_element(By.ID, "ano-dados")).select_by_visible_text(str(ano))

        # Esperar o seletor do mês carregar e selecionar o mês correto
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mes-dados")))
            print("Seletor de mês encontrado.")
        except Exception as e:
            print(f"Erro ao encontrar seletor de mês: {e}")
            input("Pressione Enter para fechar o navegador...")
            driver.quit()
            return

        Select(driver.find_element(By.ID, "mes-dados")).select_by_visible_text(mes_extenso)

        # Esperar carregar a lista de links
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".dados-abertos-lista a")))
        links_zip = driver.find_elements(By.CSS_SELECTOR, ".dados-abertos-lista a")

        if not links_zip:
            print(f"Nenhum arquivo ZIP encontrado para {mes_extenso}/{ano}.")
            input("Pressione Enter para fechar o navegador...")
            time.sleep(10)
            driver.quit()
            return

        for link in links_zip:
            url_zip = link.get_attribute("href")
            if not url_zip.endswith(".zip"):  # Garante que é um link válido
                continue

            nome_arquivo = os.path.join(diretorio_destino, os.path.basename(url_zip.split("?")[0]))  # Remove parâmetros da URL

            try:
                resposta_zip = requests.get(url_zip, stream=True)
                resposta_zip.raise_for_status()

                with open(nome_arquivo, "wb") as arquivo_zip:
                    for chunk in resposta_zip.iter_content(chunk_size=8192):
                        arquivo_zip.write(chunk)

                print(f"Arquivo baixado: {nome_arquivo}")

                # Extração dos arquivos XML dentro do ZIP
                extrair_arquivos_zip(nome_arquivo, diretorio_destino)

            except requests.exceptions.RequestException as e:
                print(f"Erro ao baixar {url_zip}: {e}")

    except Exception as e:
        print(f"Erro ao acessar a página: {e}")

    finally:
        driver.quit()

def extrair_arquivos_zip(arquivo_zip, diretorio_destino):
    """
    Extrai os arquivos XML de um arquivo ZIP para um diretório específico.

    Args:
        arquivo_zip (str): Caminho do arquivo ZIP.
        diretorio_destino (str): Diretório onde os XMLs serão extraídos.
    """
    try:
        with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
            zip_ref.extractall(diretorio_destino)
        print(f"Arquivos extraídos para: {diretorio_destino}")
    except zipfile.BadZipFile:
        print(f"Erro ao extrair {arquivo_zip}: Arquivo ZIP corrompido.")

ano_desejado = 2023
mes_desejado = 11
diretorio_saida = f"dou_{ano_desejado}_{MESES_PORTUGUES[mes_desejado]}"

baixar_dou(ano_desejado, mes_desejado, diretorio_saida)
