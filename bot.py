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

OBRA_ROLE_MAP = {
    "invocador-solitario-de-nivel-sss": "1415075549877112953",
    "poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias": "1415075423674433587",
    "conquistando-masmorras-com-copiar-e-colar": "1415075300412231830",
    "eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente": "1415075156187025539",
    "depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas": "1415073241399300227"
}

MEMORIA_ARQUIVO = "lancados.json"
WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- FUNÇÕES DO ROBÔ ---

def carregar_memoria():
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def salvar_memoria(memoria_atualizada):
    with open(MEMORIA_ARQUIVO, 'w') as f:
        json.dump(list(memoria_atualizada), f, indent=4)

def enviar_anuncio_discord(titulo, capitulo, link_capitulo, imagem_obra, role_id):
    """Monta e envia a mensagem de anúncio, agora com o ID do cargo."""
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

    # Adiciona a menção do cargo APENAS se o ID for válido
    # Verificamos se role_id não é None e se é uma string de dígitos
    if role_id and isinstance(role_id, str) and role_id.isdigit():
        payload["content"] = f"<@&{role_id}>"
    else:
        print(f"AVISO: ID de cargo inválido ou não encontrado para a obra '{titulo}'. Enviando sem menção.")

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Anúncio enviado: {titulo} - {capitulo}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio para o Discord: {e}")
        # Para depuração, vamos imprimir o que tentamos enviar
        print("Payload que causou o erro:", json.dumps(payload, indent=2))

def main():
    print("Iniciando verificação de lançamentos...")
    
    memoria_de_lancamentos = carregar_memoria()
    primeira_execucao = not memoria_de_lancamentos

    if primeira_execucao:
        print("PRIMEIRA EXECUÇÃO DETECTADA: Populando a memória inicial sem anunciar...")
    
    novos_links_encontrados = set()

    for url_obra in URLS_DAS_OBRAS:
        print(f"\nVerificando obra: {url_obra.split('/')[-1]}")
        try:
            response = requests.get(url_obra, headers=HEADERS, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro ao acessar a página da obra: {e}")
            continue
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        titulo_obra_tag = soup.select_one('h1')
        imagem_obra_tag = soup.select_one('aside img')
        
        if not all([titulo_obra_tag, imagem_obra_tag]):
            print("  -> Não foi possível encontrar título ou imagem da obra.")
            continue
            
        titulo_obra = titulo_obra_tag.text.strip()
        imagem_obra = imagem_obra_tag['src']
        
        todos_os_capitulos_tags = soup.select('section h2:-soup-contains("Capítulos") + div a')
        
        if not todos_os_capitulos_tags:
            print("  -> Não foi possível encontrar a lista de capítulos nesta página.")
            continue

        for cap_tag in todos_os_capitulos_tags:
            link_capitulo = cap_tag['href']
            
            if link_capitulo not in memoria_de_lancamentos:
                
                if primeira_execucao:
                    novos_links_encontrados.add(link_capitulo)
                else:
                    print(f"  -> NOVO CAPÍTULO DETECTADO! Link: {link_capitulo}")
                    
                    numero_capitulo_tag = cap_tag.select_one('span')
                    if not numero_capitulo_tag: continue
                    
                    numero_capitulo = numero_capitulo_tag.text.strip()
                    link_completo = f"https://gatotoons.online{link_capitulo}"
                    
                    # Procura o ID do cargo no nosso mapa
                    obra_slug = url_obra.split('/')[-1]
                    role_id_para_mencionar = OBRA_ROLE_MAP.get(obra_slug)
                    
                    enviar_anuncio_discord(titulo_obra, numero_capitulo, link_completo, imagem_obra, role_id_para_mencionar)
                    novos_links_encontrados.add(link_capitulo)
                    time.sleep(2)

    if novos_links_encontrados:
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
