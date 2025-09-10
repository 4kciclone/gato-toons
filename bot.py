import requests
from bs4 import BeautifulSoup
import json
import os
import time

# --- CONFIGURAÇÕES ---
# A lista de obras que nosso robô vai vigiar
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
    """Carrega o dicionário com o último capítulo anunciado de cada obra."""
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def salvar_memoria(memoria_atualizada):
    """Salva a memória atualizada no arquivo."""
    with open(MEMORIA_ARQUIVO, 'w') as f:
        json.dump(memoria_atualizada, f, indent=4)

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
    houve_atualizacao = False

    # Itera sobre cada obra da nossa lista
    for url_obra in URLS_DAS_OBRAS:
        print(f"\nVerificando obra: {url_obra.split('/')[-1]}")
        try:
            response = requests.get(url_obra)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro ao acessar a página da obra: {e}")
            continue # Pula para a próxima obra
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontra o link do capítulo mais recente na página
        capitulo_mais_recente_tag = soup.select_one('section h2:-soup-contains("Capítulos") + div a')
        
        if not capitulo_mais_recente_tag:
            print("  -> Não foi possível encontrar a lista de capítulos nesta página.")
            continue

        link_capitulo_atual = capitulo_mais_recente_tag['href']
        
        # Compara com o que temos na memória
        ultimo_link_conhecido = memoria_de_lancamentos.get(url_obra)

        if link_capitulo_atual != ultimo_link_conhecido:
            print(f"  -> NOVO CAPÍTULO DETECTADO! Link: {link_capitulo_atual}")
            houve_atualizacao = True
            
            # Extrai as outras informações para o anúncio
            titulo_obra = soup.select_one('h1').text.strip()
            numero_capitulo = capitulo_mais_recente_tag.select_one('span').text.strip()
            imagem_obra = soup.select_one('aside img')['src']

            # Envia o anúncio
            link_completo_capitulo = f"https://gatotoons.online{link_capitulo_atual}"
            enviar_anuncio_discord(titulo_obra, numero_capitulo, link_completo_capitulo, imagem_obra)
            
            # Atualiza a memória com o link do novo capítulo
            memoria_de_lancamentos[url_obra] = link_capitulo_atual
            
            time.sleep(1) # Pausa para não sobrecarregar o Discord
        else:
            print("  -> Sem novidades.")

    # Se houve qualquer atualização, salva o novo estado da memória
    if houve_atualizacao:
        print("\nSalvando memória atualizada...")
        salvar_memoria(memoria_de_lancamentos)

    print("\nVerificação concluída.")

if __name__ == "__main__":
    main()
