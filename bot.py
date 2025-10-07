import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse, parse_qs

# --- CONFIGURAÇÕES ---
BASE_URL = "https://gatotoons.online"

# Lista de URLs de cada obra a ser monitorada
URLS_DAS_OBRAS = [
    "https://gatotoons.online/obra.php?slug=espinhos-de-calor",
    "https://gatotoons.online/obra.php?slug=quando-a-filha-da-bruxa-acaba-com-a-maldi-o-do-protagonista-masculino",
    "https://gatotoons.online/obra.php?slug=meu-corpo-foi-possu-do-por-algu-m",
    "https://gatotoons.online/obra.php?slug=conquistando-masmorras-com-copiar-e-colar",
    "https://gatotoons.online/obra.php?slug=caminhante-do-reino-espiritual",
    "https://gatotoons.online/obra.php?slug=regress-o-da-espada-destruidora",
    "https://gatotoons.online/obra.php?slug=para-meu-rude-homem-com-m-ltiplas-personalidades",
    "https://gatotoons.online/obra.php?slug=invocador-solit-rio-de-n-vel-sss",
    "https://gatotoons.online/obra.php?slug=poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias",
    "https://gatotoons.online/obra.php?slug=o-suporte-faz-tudo",
    "https://gatotoons.online/obra.php?slug=eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente-",
    "https://gatotoons.online/obra.php?slug=depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas"
]

# Mapeamento de Obras: Configure os cargos e canais de destino aqui.
OBRA_ROLE_MAP = {
    "invocador-solit-rio-de-n-vel-sss": { "id": "1415075549877112953", "nome": "Invocador Solitário de Nível SSS", "canal_destino": "CANAL_PRINCIPAL" },
    "poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias": { "id": "1415075423674433587", "nome": "Poderes Perdidos Restaurados", "canal_destino": "CANAL_PRINCIPAL" },
    "conquistando-masmorras-com-copiar-e-colar": { "id": "1415075300412231830", "nome": "Conquistando Masmorras", "canal_destino": "CANAL_PRINCIPAL" },
    "eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente-": { "id": "1415075156187025539", "nome": "Invencibilidade Passiva", "canal_destino": "CANAL_PRINCIPAL" },
    "depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas": { "id": "1415073241399300227", "nome": "Login 30 Dias", "canal_destino": "CANAL_PRINCIPAL" },
    "o-suporte-faz-tudo": { "id": "1416800403835720014", "nome": "O Suporte Faz Tudo", "canal_destino": "CANAL_PRINCIPAL" },
    "caminhante-do-reino-espiritual": { "id": "1418317864359690262", "nome": "Caminhante do Reino Espiritual", "canal_destino": "CANAL_PRINCIPAL" },
    "a-99a-vida-do-aventureiro-mais-fraco-o-caminho-mais-rapido-do-mais-fraco-ao-mais-forte": { "id": "1418318233936597183", "nome": "99ª Vida do Aventureiro Mais Fraco", "canal_destino": "CANAL_PRINCIPAL" },
    "regress-o-da-espada-destruidora": { "id": "ID_DO_CARGO_AQUI", "nome": "Regressão da Espada Destruidora", "canal_destino": "CANAL_PRINCIPAL" },

    # --- Obras de Parceiros (formato de texto simples, anúncio individual) ---
    "espinhos-de-calor": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Espinhos de Calor", "canal_destino": "CANAL_SECUNDARIO" },
    "meu-corpo-foi-possu-do-por-algu-m": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Meu Corpo foi Possuído por Alguém", "canal_destino": "CANAL_SECUNDARIO" },
    "o-sr-empregada-do-caf-clover": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "O Sr. Empregada do Café Clover", "canal_destino": "CANAL_SECUNDARIO" },
    "para-meu-rude-homem-com-m-ltiplas-personalidades": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Para meu Rude Homem com Múltiplas Personalidades", "canal_destino": "CANAL_SECUNDARIO" },
    "quando-a-filha-da-bruxa-acaba-com-a-maldi-o-do-protagonista-masculino": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Quando a Filha da Bruxa acaba com a Maldição do Protagonista Masculino", "canal_destino": "CANAL_SECUNDARIO" }
}

MEMORIA_ARQUIVO = "lancados.json"
WEBHOOK_URLS = {
    "CANAL_PRINCIPAL": os.environ.get('DISCORD_WEBHOOK_CANAL_PRINCIPAL'),
    "CANAL_SECUNDARIO": os.environ.get('DISCORD_WEBHOOK_CANAL_SECUNDARIO')
}
HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' }

# --- FUNÇÕES DO ROBÔ ---

def carregar_memoria():
    try:
        with open(MEMORIA_ARQUIVO, 'r') as f: return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError): return set()

def salvar_memoria(memoria_atualizada):
    with open(MEMORIA_ARQUIVO, 'w') as f: json.dump(list(memoria_atualizada), f, indent=4)

def format_chapter_number(num_float):
    return str(int(num_float)) if num_float.is_integer() else str(num_float)

def enviar_anuncio_discord(titulo, capitulo, link_capitulo, imagem_obra, role_id, webhook_url, is_vip=False):
    if not webhook_url: return
    
    description = f"Um novo capítulo já está disponível!\n\n**Leia agora:** [Clique aqui]({link_capitulo})"
    if is_vip:
        description += "\n\n🔔 **Obra VIP:** Disponível para todos em 24 horas!"

    embed = {"title": f"🔥 {titulo} - {capitulo} 🔥", "description": description, "url": link_capitulo, "color": 5814783, "thumbnail": {"url": imagem_obra}}
    payload = {"username": "Anunciador Gato Toons", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "embeds": [embed]}
    if role_id and isinstance(role_id, str) and role_id.isdigit(): payload["content"] = f"<@&{role_id}>"
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Único) enviado: {titulo} - {capitulo}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio único: {e}")

def enviar_anuncio_massivo(titulo, novos_capitulos, imagem_obra, role_id, webhook_url, is_vip=False):
    if not webhook_url: return
    capitulos_ordenados = sorted(novos_capitulos, key=lambda x: x[0])
    primeiro_cap_num = format_chapter_number(capitulos_ordenados[0][0])
    ultimo_cap_num = format_chapter_number(capitulos_ordenados[-1][0])
    link_ultimo_capitulo = capitulos_ordenados[-1][1]
    titulo_anuncio = f"Capítulos {primeiro_cap_num} ao {ultimo_cap_num}"
    
    description = f"Vários capítulos novos disponíveis!\n\n**Leia o último capítulo:** [Clique aqui]({link_ultimo_capitulo})"
    if is_vip:
        description += "\n\n🔔 **Obra VIP:** Disponível para todos em 24 horas!"

    embed = {"title": f"🔥 {titulo} - {titulo_anuncio} 🔥", "description": description, "url": link_ultimo_capitulo, "color": 5814783, "thumbnail": {"url": imagem_obra}}
    payload = {"username": "Anunciador Gato Toons", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "embeds": [embed]}
    if role_id and isinstance(role_id, str) and role_id.isdigit(): payload["content"] = f"<@&{role_id}>"
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Massa) enviado: {titulo} - {titulo_anuncio}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio em massa: {e}")

def enviar_anuncio_parceiro(nome_obra, link_capitulo, scan_role_id, webhook_url):
    if not webhook_url: return
    mensagem = f"🎉 **Novo Lançamento de Parceiro!** 🎉\n\n<@&{scan_role_id}> acaba de lançar um novo capítulo de **{nome_obra}**!\n\n**Leia agora:** {link_capitulo}"
    payload = {"username": "Anunciador de Parcerias", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "content": mensagem}
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Parceiro) enviado: {nome_obra}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio de parceiro: {e}")

def main():
    print("Iniciando verificação de lançamentos...")
    memoria_de_lancamentos = carregar_memoria()
    primeira_execucao = not memoria_de_lancamentos
    if primeira_execucao:
        print("PRIMEIRA EXECUÇÃO: Populando memória inicial...")
    
    novos_links_encontrados = set()

    for url_obra in URLS_DAS_OBRAS:
        try:
            parsed_url = urlparse(url_obra)
            obra_slug = parse_qs(parsed_url.query)['slug'][0]
        except (KeyError, IndexError):
            print(f"\nAVISO: Não foi possível extrair o slug da URL: {url_obra}. Pulando.")
            continue
            
        role_info = OBRA_ROLE_MAP.get(obra_slug)
        if not role_info:
            print(f"\nAVISO: Obra com slug '{obra_slug}' não encontrada no OBRA_ROLE_MAP. Pulando.")
            continue

        print(f"\nVerificando obra: {role_info.get('nome', 'Desconhecida')}")

        try:
            response = requests.get(url_obra, headers=HEADERS, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro ao acessar a página da obra: {e}")
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        capitulos_list_container = soup.select_one("#capitulos-list")
        if not capitulos_list_container:
            print("  -> Não foi possível encontrar a lista de capítulos (ID #capitulos-list).")
            continue
            
        todos_os_capitulos_tags = capitulos_list_container.select("a.list-group-item")
        
        # Lista para armazenar tuplas: (numero, link, is_vip_bool)
        novos_capitulos_da_obra = [] 
        for cap_tag in todos_os_capitulos_tags:
            badge_novo = cap_tag.select_one("span.badge.bg-success")
            badge_vip = cap_tag.select_one("span.badge.bg-warning")

            if not (badge_novo or badge_vip):
                continue

            link_completo = urljoin(BASE_URL, cap_tag['href'])
            if link_completo not in memoria_de_lancamentos:
                try:
                    num_str = cap_tag.find('span').text.strip().lower().replace('capítulo ', '')
                    numero_cap = float(num_str)
                    is_vip = badge_vip is not None
                    novos_capitulos_da_obra.append((numero_cap, link_completo, is_vip))
                except (ValueError, AttributeError):
                    print(f"  -> Aviso: Não foi possível extrair número do capítulo do link: {link_completo}")

        if not novos_capitulos_da_obra: continue
        
        links_para_salvar = [link for _, link, _ in novos_capitulos_da_obra]
        novos_links_encontrados.update(links_para_salvar)

        if primeira_execucao: continue

        print(f"  -> DETECTADO(S) {len(novos_capitulos_da_obra)} NOVO(S) CAPÍTULO(S)!")
        destino = role_info.get("canal_destino")
        webhook_para_usar = WEBHOOK_URLS.get(destino)

        if role_info.get("parceiro"):
            # Parceiros são anunciados individualmente
            for _, link, _ in novos_capitulos_da_obra:
                enviar_anuncio_parceiro(role_info.get("nome"), link, role_info.get("scan_role_id"), webhook_para_usar)
                time.sleep(1)
        else:
            imagem_obra_tag = soup.select_one(".obra-header img")
            imagem_obra = urljoin(BASE_URL, imagem_obra_tag['src']) if imagem_obra_tag else ""
            
            if len(novos_capitulos_da_obra) == 1:
                numero, link, is_vip = novos_capitulos_da_obra[0]
                capitulo_str = f"Capítulo {format_chapter_number(numero)}"
                enviar_anuncio_discord(role_info.get("nome"), capitulo_str, link, imagem_obra, role_info.get("id"), webhook_para_usar, is_vip=is_vip)
            else:
                # Se qualquer um dos capítulos no lote for VIP, o anúncio todo é marcado como VIP
                anuncio_e_vip = any(cap[2] for cap in novos_capitulos_da_obra)
                enviar_anuncio_massivo(role_info.get("nome"), novos_capitulos_da_obra, imagem_obra, role_info.get("id"), webhook_para_usar, is_vip=anuncio_e_vip)
        
        time.sleep(2)

    if novos_links_encontrados:
        memoria_final = memoria_de_lancamentos.union(novos_links_encontrados)
        salvar_memoria(memoria_final)
        if primeira_execucao:
            print(f"\nMemória inicial populada com {len(novos_links_encontrados)} capítulos.")
        else:
            print(f"\nMemória atualizada com {len(novos_links_encontrados)} novo(s) capítulo(s).")
    else:
        print("\nNenhum novo capítulo encontrado.")
    
    print("\nVerificação concluída.")

if __name__ == "__main__":
    main()
