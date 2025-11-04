import requests
import json
import os
import time
from urllib.parse import urljoin

# --- CONFIGURAÇÕES ---
BASE_URL = "https://gatotoons.online"
API_ENDPOINT = "https://gatotoons.online/api/obras/detalhes.php?slug="

# MUDANÇA AQUI: Lista de slugs corrigida e completa.
SLUGS_DAS_OBRAS = [
    "espinhos-de-calor",
    "quando-a-filha-da-bruxa-acaba-com-a-maldi-o-do-protagonista-masculino",
    "meu-corpo-foi-possu-do-por-algu-m",
    "conquistando-masmorras-com-copiar-e-colar",
    "caminhante-do-reino-espiritual",
    "regress-o-da-espada-destruidora",
    "para-meu-rude-homem-com-m-ltiplas-personalidades",
    "invocador-solit-rio-de-n-vel-sss",
    "poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias",
    "o-suporte-faz-tudo",
    "eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente-",
    "depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas",
    "a-99-vida-do-aventureiro-mais-fraco-o-caminho-mais-r-pido-do-mais-fraco-ao-mais-forte", # <--- Corrigido
    "o-sr-empregada-do-caf-clover", # <--- Adicionado
    "sobrevivendo-como-uma-empregada-em-um-jogo-de-terror-18",
    "eu-n-o-te-salvei-para-ser-pedida-em-casamento",
    "quebrador-de-defesa",
    "apenas-um-imortal",
    "her-is-dem-nios-e-vil-es"
]

OBRA_ROLE_MAP = {
    "invocador-solit-rio-de-n-vel-sss": { "id": "1415075549877112953", "nome": "Invocador Solitário de Nível SSS", "canal_destino": "CANAL_PRINCIPAL" },
    "poderes-perdidos-restaurados-desbloqueando-uma-nova-habilidade-todos-os-dias": { "id": "1415075423674433587", "nome": "Poderes Perdidos Restaurados", "canal_destino": "CANAL_PRINCIPAL" },
    "conquistando-masmorras-com-copiar-e-colar": { "id": "1415075300412231830", "nome": "Conquistando Masmorras", "canal_destino": "CANAL_PRINCIPAL" },
    "eu-confio-na-minha-invencibilidade-para-causar-toneladas-de-dano-passivamente-": { "id": "1415075156187025539", "nome": "Invencibilidade Passiva", "canal_destino": "CANAL_PRINCIPAL" },
    "depois-de-fazer-login-por-30-dias-posso-aniquilar-estrelas": { "id": "1415073241399300227", "nome": "Login 30 Dias", "canal_destino": "CANAL_PRINCIPAL" },
    "o-suporte-faz-tudo": { "id": "1416800403835720014", "nome": "O Suporte Faz Tudo", "canal_destino": "CANAL_PRINCIPAL" },
    "caminhante-do-reino-espiritual": { "id": "1418317864359690262", "nome": "Caminhante do Reino Espiritual", "canal_destino": "CANAL_PRINCIPAL" },
    "quebrador-de-defesa": { "id": "1435415847962148935", "nome": "Quebrador de Defesa", "canal_destino": "CANAL_PRINCIPAL" },
    "her-is-dem-nios-e-vil-es": { "id": "1435415600145895424", "nome": "Heróis, Demônios e Vilões", "canal_destino": "CANAL_PRINCIPAL" },
    "apenas-um-imortal": { "id": "1435415171769303090", "nome": "Apenas Um Imortal", "canal_destino": "CANAL_PRINCIPAL" },
    # MUDANÇA AQUI: Slug corrigido para corresponder à lista.
    "a-99-vida-do-aventureiro-mais-fraco-o-caminho-mais-r-pido-do-mais-fraco-ao-mais-forte": { "id": "1418318233936597183", "nome": "99ª Vida do Aventureiro Mais Fraco", "canal_destino": "CANAL_PRINCIPAL" },
    "regress-o-da-espada-destruidora": { "id": "1425128273444081807", "nome": "Regressão da Espada Destruidora", "canal_destino": "CANAL_PRINCIPAL" },
    "espinhos-de-calor": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Espinhos de Calor", "canal_destino": "CANAL_SECUNDARIO" },
    "meu-corpo-foi-possu-do-por-algu-m": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Meu Corpo foi Possuído por Alguém", "canal_destino": "CANAL_SECUNDARIO" },
    "o-sr-empregada-do-caf-clover": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "O Sr. Empregada do Café Clover", "canal_destino": "CANAL_SECUNDARIO" },
    "eu-n-o-te-salvei-para-ser-pedida-em-casamento": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Eu não te Salvei para ser Pedida em Casamento", "canal_destino": "CANAL_SECUNDARIO" },
    "para-meu-rude-homem-com-m-ltiplas-personalidades": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Para meu Rude Homem com Múltiplas Personalidades", "canal_destino": "CANAL_SECUNDARIO" },
    "quando-a-filha-da-bruxa-acaba-com-a-maldi-o-do-protagonista-masculino": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Quando a Filha da Bruxa acaba com a Maldição do Protagonista Masculino", "canal_destino": "CANAL_SECUNDARIO" },
    "sobrevivendo-como-uma-empregada-em-um-jogo-de-terror-18": { "parceiro": True, "scan_role_id": "1425119898023104604", "nome": "Sobrevivendo como uma Empregada em um Jogo de Terror +18", "canal_destino": "CANAL_SECUNDARIO" }

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

def format_chapter_for_title(num_float):
    int_part = int(num_float)
    padded_part = str(int_part).zfill(3)
    return f"Capítulo {int_part} - {padded_part}"

def enviar_anuncio_discord(titulo_obra, capitulo_formatado, link_capitulo, role_id, webhook_url, is_vip=False):
    if not webhook_url: return
    titulo_embed = f"🔥 {titulo_obra} - {capitulo_formatado} 🔥"
    description = f"Um novo capítulo já está disponível no site!\n\n**Leia agora:** [Clique aqui]({link_capitulo})"
    if is_vip: description += "\n\n🔔 **Obra Vip** — disponível para todos em **2 dias**!"
    embed = {"title": titulo_embed, "description": description, "url": link_capitulo, "color": 3447003}
    payload = {"username": "Anunciador Gato Toons", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "embeds": [embed]}
    if role_id and isinstance(role_id, str) and role_id.isdigit(): payload["content"] = f"<@&{role_id}>"
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Único) enviado: {titulo_obra} - {capitulo_formatado}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio único: {e}")

def enviar_anuncio_massivo(titulo_obra, novos_capitulos, obra_slug, role_id, webhook_url, is_vip=False):
    if not webhook_url: return
    capitulos_ordenados = sorted(novos_capitulos, key=lambda x: x[0])
    primeiro_cap_num = format_chapter_number(capitulos_ordenados[0][0])
    ultimo_cap_num = format_chapter_number(capitulos_ordenados[-1][0])
    link_da_obra = f"{BASE_URL}/obra.php?slug={obra_slug}"
    titulo_anuncio = f"Capítulos {primeiro_cap_num} ao {ultimo_cap_num}"
    titulo_embed = f"🔥 {titulo_obra} - {titulo_anuncio} 🔥"
    description = f"Vários capítulos novos disponíveis no site!\n\n**Confira na página da obra:** [Clique aqui]({link_da_obra})"
    if is_vip: description += "\n\n🔔 **Obra Vip** — disponível para todos em **2 dias**!"
    embed = {"title": titulo_embed, "description": description, "url": link_da_obra, "color": 3447003}
    payload = {"username": "Anunciador Gato Toons", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "embeds": [embed]}
    if role_id and isinstance(role_id, str) and role_id.isdigit(): payload["content"] = f"<@&{role_id}>"
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Massa) enviado: {titulo_obra} - {titulo_anuncio}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio em massa: {e}")

def enviar_anuncio_parceiro(nome_obra, num_capitulo, link_capitulo, scan_role_id, webhook_url):
    if not webhook_url: return
    capitulo_str = format_chapter_number(num_capitulo)
    mensagem = f"<@&{scan_role_id}> acaba de lançar o capítulo **{capitulo_str}** de **{nome_obra}**!\n\n**Leia agora:** {link_capitulo}\n🎉 Novo Lançamento de Parceiro! 🎉"
    payload = {"username": "Anunciador de Parcerias", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "content": mensagem}
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Parceiro Único) enviado: {nome_obra} Cap {capitulo_str}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio de parceiro: {e}")

def enviar_anuncio_parceiro_massivo(nome_obra, novos_capitulos, obra_slug, scan_role_id, webhook_url):
    if not webhook_url: return
    capitulos_ordenados = sorted(novos_capitulos, key=lambda x: x[0])
    primeiro_cap_num = format_chapter_number(capitulos_ordenados[0][0])
    ultimo_cap_num = format_chapter_number(capitulos_ordenados[-1][0])
    link_da_obra = f"{BASE_URL}/obra.php?slug={obra_slug}"
    mensagem = f"<@&{scan_role_id}> Postados os capítulos **{primeiro_cap_num}** ao **{ultimo_cap_num}** de **{nome_obra}**!\n\n**Confira na página da obra:** {link_da_obra}\n🎉 Novo Lançamento de Parceiro! 🎉"
    payload = {"username": "Anunciador de Parcerias", "avatar_url": "https://i.imgur.com/cgZ6dRC.jpeg", "content": mensagem}
    try:
        requests.post(webhook_url, json=payload, timeout=10).raise_for_status()
        print(f"Anúncio (Parceiro em Massa) enviado: {nome_obra} Caps {primeiro_cap_num}-{ultimo_cap_num}")
    except requests.exceptions.RequestException as e: print(f"Erro ao enviar anúncio de parceiro em massa: {e}")

def main():
    print("Iniciando verificação de lançamentos via API...")
    memoria_de_lancamentos = carregar_memoria()
    primeira_execucao = not memoria_de_lancamentos
    if primeira_execucao: print("PRIMEIRA EXECUÇÃO: Populando memória inicial...")
    
    novos_links_encontrados = set()

    for obra_slug in SLUGS_DAS_OBRAS:
        role_info = OBRA_ROLE_MAP.get(obra_slug)
        if not role_info:
            print(f"\nAVISO: Obra com slug '{obra_slug}' não encontrada no OBRA_ROLE_MAP. Pulando.")
            continue

        print(f"\nVerificando obra: {role_info.get('nome', 'Desconhecida')}")
        try:
            api_url = f"{API_ENDPOINT}{obra_slug}"
            response = requests.get(api_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            data = response.json()
            if not data.get('success'):
                print(f"  -> API retornou erro para a obra: {data.get('message', 'Erro desconhecido')}")
                continue
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"  -> Erro ao acessar ou decodificar API da obra: {e}")
            continue
        
        obra_details = data.get('obra', {})
        capitulos_api = data.get('capitulos', [])
        if not capitulos_api:
            print("  -> Nenhum capítulo encontrado na resposta da API.")
            continue

        novos_capitulos_da_obra = [] 
        for cap in capitulos_api:
            try:
                numero_cap = float(cap.get('numero_capitulo'))
                link_cap = f"{BASE_URL}/leitura.php?obra={obra_slug}&cap={cap.get('numero_capitulo')}"
                if link_cap not in memoria_de_lancamentos:
                    is_obra_vip = obra_details.get('is_vip', 0) == 1
                    novos_capitulos_da_obra.append((numero_cap, link_cap, is_obra_vip))
            except (ValueError, TypeError, AttributeError):
                print(f"  -> Aviso: Dados de capítulo inválidos na API: {cap}")

        if not novos_capitulos_da_obra: continue
        
        links_para_salvar = [link for _, link, _ in novos_capitulos_da_obra]
        novos_links_encontrados.update(links_para_salvar)

        if primeira_execucao: continue

        print(f"  -> DETECTADO(S) {len(novos_capitulos_da_obra)} NOVO(S) CAPÍTULO(S)!")
        destino = role_info.get("canal_destino")
        webhook_para_usar = WEBHOOK_URLS.get(destino)

        if role_info.get("parceiro"):
            if len(novos_capitulos_da_obra) == 1:
                numero, link, _ = novos_capitulos_da_obra[0]
                enviar_anuncio_parceiro(role_info.get("nome"), numero, link, role_info.get("scan_role_id"), webhook_para_usar)
            else:
                enviar_anuncio_parceiro_massivo(role_info.get("nome"), novos_capitulos_da_obra, obra_slug, role_info.get("scan_role_id"), webhook_para_usar)
        else:
            if len(novos_capitulos_da_obra) == 1:
                numero, link, is_vip = novos_capitulos_da_obra[0]
                capitulo_formatado = format_chapter_for_title(numero)
                enviar_anuncio_discord(role_info.get("nome"), capitulo_formatado, link, role_info.get("id"), webhook_para_usar, is_vip=is_vip)
            else:
                anuncio_e_vip = any(cap[2] for cap in novos_capitulos_da_obra)
                enviar_anuncio_massivo(role_info.get("nome"), novos_capitulos_da_obra, obra_slug, role_info.get("id"), webhook_para_usar, is_vip=anuncio_e_vip)
        
        time.sleep(2)

    if novos_links_encontrados:
        memoria_final = memoria_de_lancamentos.union(novos_links_encontrados)
        salvar_memoria(memoria_final)
        if primeira_execucao: print(f"\nMemória inicial populada com {len(novos_links_encontrados)} capítulos.")
        else: print(f"\nMemória atualizada com {len(novos_links_encontrados)} novo(s) capítulo(s).")
    else:
        print("\nNenhum novo capítulo encontrado.")
    
    print("\nVerificação concluída.")

if __name__ == "__main__":
    main()
