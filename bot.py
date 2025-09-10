import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CONFIGURAÇÕES ---
SITE_URL = "https://gatotoons.online/"
MEMORIA_ARQUIVO = "lancados.json"
# A URL do Webhook será pega de uma "variável secreta" para segurança
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# --- FUNÇÕES DO ROBÔ ---

def carregar_lancados_da_memoria():
    """Carrega a lista de links já anunciados da nossa memória (o arquivo .json)."""
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def salvar_lancados_na_memoria(links_anunciados):
    """Salva a lista atualizada de links na nossa memória."""
    with open(MEMORIA_ARQUIVO, 'w') as f:
        json.dump(list(links_anunciados), f, indent=4)

def enviar_anuncio_discord(titulo, capitulo, link_obra, imagem_obra):
    """Monta e envia a mensagem de anúncio para o Discord."""
    if not WEBHOOK_URL:
        print("ERRO: A URL do Webhook não foi encontrada! Configure a variável secreta.")
        return

    # Monta uma mensagem bonita usando o formato "Embed" do Discord
    embed = {
        "title": f"🔥 {titulo} - {capitulo} 🔥",
        "description": "Um novo capítulo já está disponível no site!\n\n**Leia agora:**",
        "url": f"https://gatotoons.online{link_obra}",
        "color": 15158332, # Uma cor avermelhada/rosada
        "image": {
            "url": f"https://gatotoons.online{imagem_obra}"
        }
    }

    payload = {
        "username": "Anunciador Gato Toons",
        "avatar_url": "https://i.imgur.com/uB1Q1a2.png", # Um avatar de gatinho
        "embeds": [embed]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status() # Lança um erro se o status não for 2xx
        print(f"Anúncio enviado com sucesso para: {titulo} - {capitulo}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio para o Discord: {e}")

def main():
    """A função principal que orquestra todo o trabalho."""
    print("Iniciando verificação de lançamentos...")
    
    # 1. Carrega a memória do robô
    links_ja_anunciados = carregar_lancados_da_memoria()
    
    # 2. Visita o site e pega o HTML
    try:
        response = requests.get(SITE_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar o site: {e}")
        return

    # 3. Usa o BeautifulSoup para "ler" o HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 4. Encontra todos os cards na seção "Lançamentos Recentes"
    lancamentos_recentes = soup.select('main a.group')
    
    novos_capitulos_encontrados = []

    # 5. Analisa cada card encontrado
    for card in lancamentos_recentes:
        link = card['href']
        
        # Se o link ainda não foi anunciado, extrai as informações
        if link not in links_ja_anunciados:
            titulo_tag = card.select_one('h3')
            capitulo_tag = card.select_one('span')
            imagem_tag = card.select_one('img')

            if all([titulo_tag, capitulo_tag, imagem_tag]):
                novo_capitulo = {
                    "titulo": titulo_tag.text.strip(),
                    "capitulo": capitulo_tag.text.strip(),
                    "link": link,
                    "imagem": imagem_tag['src']
                }
                novos_capitulos_encontrados.append(novo_capitulo)

    # 6. Anuncia os capítulos novos na ordem correta (do mais antigo para o mais novo)
    if novos_capitulos_encontrados:
        print(f"Encontrados {len(novos_capitulos_encontrados)} novos capítulos. Anunciando...")
        for capitulo in reversed(novos_capitulos_encontrados):
            enviar_anuncio_discord(capitulo['titulo'], capitulo['capitulo'], capitulo['link'], capitulo['imagem'])
            links_ja_anunciados.add(capitulo['link'])
            time.sleep(1) # Uma pequena pausa para não sobrecarregar o Discord

        # 7. Salva a nova memória atualizada
        salvar_lancados_na_memoria(links_ja_anunciados)
    else:
        print("Nenhum novo capítulo encontrado.")

if __name__ == "__main__":
    main()