import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CONFIGURAÇÕES ---
URLS_DAS_OBRAS = [
    "https://gatotoons.online/obra/invocador-solitario-de-nivel-sss",
    "https://gatotoons.online/obra/poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias",
    "https://gatotoons.online/obra/conquistando-masmorras-com-copiar-e-colar",
    "https://gatotoons.online/obra/eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente",
    "https://gatotoons.online/obra/depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas"
]
MEMORIA_ARQUIVO = "lancados.json"
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# --- FUNÇÕES DO ROBÔ ---

def carregar_memoria():
    """Carrega o set com os links dos capítulos já conhecidos."""
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def salvar_memoria(memoria_atualizada):
    """Salva a memória atualizada no arquivo."""
    with open(MEMORIA_ARQUIVO, 'w') as f:
        json.dump(list(memoria_atualizada), f, indent=4)

def enviar_anuncio_discord(titulo, capitulo, link_capitulo, imagem_obra):
    """Monta e envia a mensagem de anúncio para o Discord."""
    if not WEBHOOK_URL:
        print("ERRO: A URL do Webhook não foi configurada!")
        return

    embed = {
        "title": f"🔥 {titulo} - {capitulo} 🔥",
        "description": "Um novo capítulo já está disponível no site!\n\n**Leia agora:**",
        "url": link_capitulo,
        "color": 5814783,
        "image": { "url": f"https://gatotoons.online{imagem_obra}" }
    }
    payload = {
        "username": "Anunciador Gato Toons",
        "avatar_url": "https://i.imgur.com/uB1Q1a2.png",
        "embeds": [embed]
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Anúncio enviado: {titulo} - {capitulo}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio para o Discord: {e}")

def main():
    """Função principal que orquestra todo o trabalho."""
    print("Iniciando verificação de lançamentos...")
    
    memoria_de_lancamentos = carregar_memoria()
    primeira_execucao = not memoria_de_lancamentos

    if primeira_execucao:
        print("PRIMEIRA EXECUÇÃO DETECTADA: Populando a memória inicial sem anunciar...")
    
    novos_links_encontrados = set()

    for url_obra in URLS_DAS_OBRAS:
        print(f"\nVerificando obra: {url_obra.split('/')[-1]}")
        try:
            response = requests.get(url_obra)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro ao acessar a página da obra: {e}")
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extrai informações gerais da obra
        titulo_obra = soup.select_one('h1').text.strip()
        imagem_obra = soup.select_one('aside img')['src']
        
        # Encontra TODOS os links de capítulos na página
        todos_os_capitulos_tags = soup.select('section h2:-soup-contains("Capítulos") + div a')
        
        if not todos_os_capitulos_tags:
            print("  -> Não foi possível encontrar a lista de capítulos nesta página.")
            continue

        for cap_tag in todos_os_capitulos_tags:
            link_capitulo = cap_tag['href']
            
            # Se o link do capítulo não está na memória, é novo!
            if link_capitulo not in memoria_de_lancamentos:
                
                if primeira_execucao:
                    # No modo "Primeira Vez", apenas guardamos o link
                    novos_links_encontrados.add(link_capitulo)
                else:
                    # No modo "Normal", anunciamos e depois guardamos
                    print(f"  -> NOVO CAPÍTULO DETECTADO! Link: {link_capitulo}")
                    
                    numero_capitulo = cap_tag.select_one('span').text.strip()
                    link_completo = f"https://gatotoons.online{link_capitulo}"
                    
                    enviar_anuncio_discord(titulo_obra, numero_capitulo, link_completo, imagem_obra)
                    novos_links_encontrados.add(link_capitulo)
                    time.sleep(2) # Pausa entre anúncios

    if novos_links_encontrados:
        # Adiciona os novos links à memória existente e salva
        memoria_final = memoria_de_lancamentos.union(novos_links_encontrados)
        salvar_memoria(memoria_final)
        if primeira_execucao:
            print(f"\nMemória inicial populada com {len(novos_links_encontrados)} capítulos. Nenhum anúncio foi enviado.")
        else:
            print(f"\nMemória atualizada com {len(novos_links_encontrados)} novo(s) capítulo(s).")
    else:
        print("\nNenhum novo capítulo encontrado.")

    print("\nVerificação concluída.")

if __name__ == "__main__":
    main()
