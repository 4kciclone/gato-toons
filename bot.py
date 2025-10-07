import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin

# --- CONFIGURAÇÕES ---
HOME_URL = "https://gatotoons.online/index.php"

# Mapeamento de Obras: Configure os cargos e canais de destino aqui.
OBRA_ROLE_MAP = {
   "invocador-solit-rio-de-n-vel-sss": {
        "id": "1415075549877112953",
        "nome": "Invocador Solitário de Nível SSS",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias": {
        "id": "1415075423674433587",
        "nome": "Poderes Perdidos Restaurados",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "conquistando-masmorras-com-copiar-e-colar": {
        "id": "1415075300412231830",
        "nome": "Conquistando Masmorras",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente-": {
        "id": "1415075156187025539",
        "nome": "Invencibilidade Passiva",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas": {
        "id": "1415073241399300227",
        "nome": "Login 30 Dias",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "o-suporte-faz-tudo": {
        "id": "1416800403835720014",
        "nome": "O Suporte Faz Tudo",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "caminhante-do-reino-espiritual": {
        "id": "1418317864359690262",
        "nome": "Caminhante do Reino Espiritual",
        "canal_destino": "CANAL_PRINCIPAL"
    },
    "a-99a-vida-do-aventureiro-mais-fraco-o-caminho-mais-rapido-do-mais-fraco-ao-mais-forte": {
        "id": "1418318233936597183",
        "nome": "99ª Vida do Aventureiro Mais Fraco",
        "canal_destino": "CANAL_PRINCIPAL"
    },

    # --- Obras de Parceiros (formato de texto simples, anúncio individual) ---
    "espinhos-de-calor": {
        "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Espinhos de Calor", "canal_destino": "CANAL_SECUNDARIO"
    },
    "meu-corpo-foi-possu-do-por-algu-m": {
        "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Meu Corpo foi Possuído por Alguém", "canal_destino": "CANAL_SECUNDARIO"
    },
    "o-sr-empregada-do-caf-clover": {
        "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "O Sr. Empregada do Café Clover", "canal_destino": "CANAL_SECUNDARIO"
    },
    "para-meu-rude-homem-com-m-ltiplas-personalidades": {
        "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Para meu Rude Homem com Múltiplas Personalidades", "canal_destino": "CANAL_SECUNDARIO"
    },
    "quando-a-filha-da-bruxa-acaba-com-a-maldi-o-do-protagonista-masculino": {
        "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Quando a Filha da Bruxa acaba com a Maldição do Protagonista Masculino", "canal_destino": "CANAL_SECUNDARIO"
    }
}

MEMORIA_ARQUIVO = "lancados.json"

WEBHOOK_URLS = {
    "CANAL_PRINCIPAL": os.environ.get('DISCORD_WEBHOOK_CANAL_PRINCIPAL'),
    "CANAL_SECUNDARIO": os.environ.get('DISCORD_WEBHOOK_CANAL_SECUNDARIO')
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- FUNÇÕES DO ROBÔ ---

def carregar_memoria():
    """Carrega os links dos capítulos já anunciados do arquivo JSON."""
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def salvar_memoria(memoria_atualizada):
    """Salva o conjunto atualizado de links no arquivo JSON."""
    with open(MEMORIA_ARQUIVO, 'w') as f:
        json.dump(list(memoria_atualizada), f, indent=4)

def format_chapter_number(num_float):
    """Converte um float para string, removendo '.0' desnecessário."""
    return str(int(num_float)) if num_float.is_integer() else str(num_float)

def enviar_anuncio_discord(titulo, capitulo, link_capitulo, imagem_obra, role_id, webhook_url):
    """Envia o anúncio padrão com embed para um único capítulo de obra principal."""
    if not webhook_url:
        print(f"ERRO: Webhook não configurado para '{titulo}'.")
        return

    embed = {
        "title": f"🔥 {titulo} - {capitulo} 🔥",
        "description": f"Um novo capítulo já está disponível!\n\n**Leia agora:** [Clique aqui]({link_capitulo})",
        "url": link_capitulo,
        "color": 5814783,
        "thumbnail": {"url": imagem_obra}
    }
    payload = {
        "username": "Anunciador Gato Toons",
        "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg",
        "embeds": [embed]
    }
    if role_id and isinstance(role_id, str) and role_id.isdigit():
        payload["content"] = f"<@&{role_id}>"

    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Único) enviado: {titulo} - {capitulo}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio único: {e}")

def enviar_anuncio_massivo(titulo, novos_capitulos, imagem_obra, role_id, webhook_url):
    """Envia um anúncio único para múltiplos capítulos de uma obra principal."""
    if not webhook_url:
        print(f"ERRO: Webhook não configurado para '{titulo}'.")
        return
    
    capitulos_ordenados = sorted(novos_capitulos, key=lambda x: x[0])
    primeiro_cap_num = format_chapter_number(capitulos_ordenados[0][0])
    ultimo_cap_num = format_chapter_number(capitulos_ordenados[-1][0])
    link_ultimo_capitulo = capitulos_ordenados[-1][1]

    titulo_anuncio = f"Capítulos {primeiro_cap_num} ao {ultimo_cap_num}"
    
    embed = {
        "title": f"🔥 {titulo} - {titulo_anuncio} 🔥",
        "description": f"Vários capítulos novos disponíveis!\n\n**Leia o último capítulo:** [Clique aqui]({link_ultimo_capitulo})",
        "url": link_ultimo_capitulo,
        "color": 5814783,
        "thumbnail": {"url": imagem_obra}
    }
    payload = {
        "username": "Anunciador Gato Toons",
        "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg",
        "embeds": [embed]
    }
    if role_id and isinstance(role_id, str) and role_id.isdigit():
        payload["content"] = f"<@&{role_id}>"

    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Massa) enviado: {titulo} - {titulo_anuncio}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio em massa: {e}")

def enviar_anuncio_parceiro(nome_obra, link_capitulo, scan_role_id, webhook_url):
    """Envia um anúncio simples em texto para obras de parceiros."""
    if not webhook_url:
        print(f"ERRO: Webhook não configurado para a obra parceira '{nome_obra}'.")
        return

    mensagem = (
        f"🎉 **Novo Lançamento de Parceiro!** 🎉\n\n"
        f"<@&{scan_role_id}> acaba de lançar um novo capítulo de **{nome_obra}**!\n\n"
        f"**Leia agora:** {link_capitulo}"
    )
    payload = {
        "username": "Anunciador de Parcerias",
        "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg",
        "content": mensagem
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Parceiro) enviado: {nome_obra}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar anúncio de parceiro: {e}")

def main():
    print("Iniciando verificação de lançamentos...")
    memoria_de_lancamentos = carregar_memoria()
    primeira_execucao = not memoria_de_lancamentos
    if primeira_execucao:
        print("PRIMEIRA EXECUÇÃO: Populando memória inicial sem enviar anúncios...")
    
    novos_links_encontrados = set()

    try:
        response = requests.get(HOME_URL, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Erro fatal ao acessar a página principal: {e}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    secao_atualizados = soup.select_one("#lista-obras-atualizadas")
    if not secao_atualizados:
        print("Não foi possível encontrar a seção 'Recentemente Atualizados'. Verificação abortada.")
        return

    todos_os_cards = secao_atualizados.select(".obra-item")
    print(f"Encontrados {len(todos_os_cards)} cards de obras na seção de atualizados.")

    for obra_card in todos_os_cards:
        # Lista para agrupar capítulos novos de uma mesma obra
        novos_capitulos_da_obra = [] 

        # Extrai o 'slug' da obra para identificá-la no mapa
        obra_link_tag = obra_card.select_one("a")
        obra_slug = ""
        if obra_link_tag and 'href' in obra_link_tag.attrs:
            try:
                obra_slug = obra_link_tag['href'].split('slug=')[-1]
            except IndexError:
                continue
        
        if not obra_slug: continue
        role_info = OBRA_ROLE_MAP.get(obra_slug)
        if not role_info: continue

        print(f"\nVerificando obra: {role_info.get('nome', 'Desconhecida')}")
        
        # Itera sobre todos os capítulos listados no card
        for cap_tag in obra_card.select("ul.chapter-info a.chapter-entry"):
            # Procura pelo selo "NOVO" para identificar um lançamento
            if not cap_tag.select_one("span.badge.bg-success"):
                continue

            link_completo = urljoin(HOME_URL, cap_tag['href'])

            if link_completo not in memoria_de_lancamentos:
                try:
                    # Extrai o número do capítulo para ordenação e formatação
                    num_str = cap_tag.select_one('span.text-truncate').text.strip().lower().replace('cap ', '')
                    numero_cap = float(num_str)
                    novos_capitulos_da_obra.append((numero_cap, link_completo))
                except (ValueError, AttributeError):
                    print(f"  -> Aviso: Não foi possível extrair o número do capítulo do link: {link_completo}")

        # Se não encontrou capítulos novos para esta obra, vai para a próxima
        if not novos_capitulos_da_obra:
            continue

        # Adiciona todos os links encontrados à memória para não anunciar de novo
        links_para_salvar = [link for _, link in novos_capitulos_da_obra]
        novos_links_encontrados.update(links_para_salvar)

        # Na primeira execução, o script apenas salva os links na memória e não anuncia
        if primeira_execucao:
            continue

        print(f"  -> DETECTADO(S) {len(novos_capitulos_da_obra)} NOVO(S) CAPÍTULO(S)!")

        # Decide qual tipo de anúncio fazer
        destino = role_info.get("canal_destino")
        webhook_para_usar = WEBHOOK_URLS.get(destino)

        if role_info.get("parceiro"):
            # Para parceiros, anuncia cada capítulo individualmente para dar visibilidade
            for _, link in novos_capitulos_da_obra:
                enviar_anuncio_parceiro(role_info.get("nome"), link, role_info.get("scan_role_id"), webhook_para_usar)
                time.sleep(1)
        else:
            # Para obras principais, decide entre anúncio único ou em massa
            imagem_obra_tag = obra_card.select_one('img.card-img-top')
            imagem_obra = urljoin(HOME_URL, imagem_obra_tag['src']) if imagem_obra_tag else ""
            
            if len(novos_capitulos_da_obra) == 1:
                numero, link = novos_capitulos_da_obra[0]
                capitulo_str = f"Capítulo {format_chapter_number(numero)}"
                enviar_anuncio_discord(role_info.get("nome"), capitulo_str, link, imagem_obra, role_info.get("id"), webhook_para_usar)
            else:
                enviar_anuncio_massivo(role_info.get("nome"), novos_capitulos_da_obra, imagem_obra, role_info.get("id"), webhook_para_usar)
        
        time.sleep(2) # Pausa entre o processamento de obras diferentes

    # Salva todos os novos links encontrados na memória de uma só vez
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
