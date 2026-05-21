import urllib.request
import urllib.error
import hashlib
import json
import os
from datetime import datetime, timedelta
import re

print("🚛 INICIANDO CRAWLER (com Google News)...")

# =====================================================
# CONFIGURAÇÕES
# =====================================================
DIAS_RETROATIVOS = 30  # Buscar notícias dos últimos 30 dias (pega maio inteiro)
KEYWORDS_GOOGLE = [
    "caminhões pesados Brasil",
    "mercado de caminhões 2026",
    "ônibus Brasil notícias",
    "veículos pesados frota",
    "venda de caminhões 2026",
    "Scania Brasil caminhões",
    "Volvo caminhões Brasil",
    "Mercedes-Benz caminhões",
    "Volkswagen caminhões",
    "MAN Latin America",
]

# Lista dos portais
PORTAIS = [
    ("ABVE", "https://abve.org.br/"),
    ("Automotive Business", "https://automotivebusiness.com.br/"),
    ("AutoData", "https://www.autodata.com.br/"),
    ("Frota News", "https://frotanews.com.br/"),
    ("Estradão", "https://estradao.estadao.com.br/"),
    ("Quatro Rodas Mercado", "https://quatrorodas.abril.com.br/noticias/mercado/"),
]

def buscar_pagina(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"   Erro: {e}")
        return None

def extrair_links(html, base_url):
    links = []
    padrao = r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    for match in re.finditer(padrao, html, re.IGNORECASE | re.DOTALL):
        link = match.group(1)
        texto = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        texto = ' '.join(texto.split())
        if texto and len(texto) > 20:
            if not link.startswith(('http://', 'https://')):
                if link.startswith('/'):
                    base = re.match(r'(https?://[^/]+)', base_url)
                    if base:
                        link = base.group(1) + link
                else:
                    link = base_url.rstrip('/') + '/' + link.lstrip('/')
            if not link.startswith(('javascript:', 'mailto:', '#')):
                links.append((texto, link))
    return links

def eh_relevante(texto):
    palavras = ['caminhão', 'caminhao', 'ônibus', 'onibus', 'pesado', 'frota', 
                'carga', 'scania', 'volvo', 'mercedes', 'venda', 'mercado',
                'volkswagen', 'man', 'pesados', 'caminhões', 'veiculo', 'automotivo',
                'produção', 'producao', 'importação', 'exportacao', 'eletrico']
    return any(p in texto.lower() for p in palavras)

# =====================================================
# GOOGLE NEWS - Busca histórica por data
# =====================================================
def buscar_google_news(keyword, data_inicio, data_fim):
    """Busca notícias no Google News por período"""
    noticias = []
    
    inicio = data_inicio.strftime("%Y-%m-%d")
    fim = data_fim.strftime("%Y-%m-%d")
    
    # Monta a URL de busca do Google News em RSS
    query = f"{keyword} after:{inicio} before:{fim}"
    url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=pt-BR&gl=BR&ceid=BR:pt"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            conteudo = r.read().decode('utf-8', errors='ignore')
            
            # Extrai itens do RSS do Google News
            itens = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>', conteudo, re.DOTALL)
            
            for titulo, link, data_pub in itens[:10]:
                # Limpa o título (remove CDATA e tags HTML)
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                titulo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo)
                
                # Converte data do RSS para ISO
                try:
                    from email.utils import parsedate_to_datetime
                    data_obj = parsedate_to_datetime(data_pub)
                    data_iso = data_obj.isoformat()
                except:
                    data_iso = datetime.now().isoformat()
                
                if titulo and len(titulo) > 20:
                    noticias.append({
                        'titulo': titulo[:300],
                        'link': link,
                        'fonte': f"Google News",
                        'data_coleta': data_iso
                    })
            
            if noticias:
                print(f"      ✅ {len(noticias)} notícias")
            
    except Exception as e:
        print(f"      ❌ Erro: {e}")
    
    return noticias

def buscar_noticias_historicas():
    """Busca notícias dos últimos DIAS_RETROATIVOS dias"""
    todas_noticias = []
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=DIAS_RETROATIVOS)
    
    print(f"\n🌐 Buscando Google News (últimos {DIAS_RETROATIVOS} dias)...")
    
    for keyword in KEYWORDS_GOOGLE:
        print(f"   🔍 Pesquisando: {keyword}")
        noticias = buscar_google_news(keyword, data_inicio, hoje)
        todas_noticias.extend(noticias)
    
    return todas_noticias

# =====================================================
# FUNÇÕES PRINCIPAIS
# =====================================================
def carregar_noticias_existentes():
    if os.path.exists('noticias.json'):
        with open('noticias.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_noticias(noticias):
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

# =====================================================
# EXECUÇÃO PRINCIPAL
# =====================================================
def executar_crawler():
    todas_noticias = carregar_noticias_existentes()
    ids_existentes = {n['id'] for n in todas_noticias}
    novas_noticias = []
    
    # ===== 1. PORTAIS NORMAIS =====
    print("\n📰 Buscando notícias nos portais...")
    for nome, url in PORTAIS:
        print(f"\n🔍 {nome}...")
        html = buscar_pagina(url)
        if html:
            links = extrair_links(html, url)
            relevantes = [l for l in links if eh_relevante(l[0])]
            
            for titulo, link in relevantes[:10]:
                id_hash = hashlib.md5(f"{titulo}{link}".encode()).hexdigest()
                if id_hash not in ids_existentes:
                    novas_noticias.append({
                        'id': id_hash,
                        'titulo': titulo,
                        'link': link,
                        'fonte': nome,
                        'data_coleta': datetime.now().isoformat()
                    })
                    ids_existentes.add(id_hash)
            print(f"   ✅ {len(relevantes)} links")
        else:
            print(f"   ❌ Falha ao acessar")
    
    # ===== 2. GOOGLE NEWS (HISTÓRICO) =====
    google_noticias = buscar_noticias_historicas()
    
    for n in google_noticias:
        id_hash = hashlib.md5(f"{n['titulo']}{n['link']}".encode()).hexdigest()
        if id_hash not in ids_existentes:
            novas_noticias.append({
                'id': id_hash,
                'titulo': n['titulo'],
                'link': n['link'],
                'fonte': n['fonte'],
                'data_coleta': n['data_coleta']
            })
            ids_existentes.add(id_hash)
    
    # ===== 3. SALVAR =====
    todas_noticias = novas_noticias + todas_noticias
    todas_noticias = todas_noticias[:1000]  # Limita a 1000 notícias
    salvar_noticias(todas_noticias)
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"   🔗 Portais: {len([n for n in novas_noticias if 'Google' not in n['fonte']])} novas")
    print(f"   🌐 Google News: {len([n for n in novas_noticias if 'Google' in n['fonte']])} novas")
    print(f"   ✨ Total de novas notícias: {len(novas_noticias)}")
    print(f"   📰 Total acumulado: {len(todas_noticias)}")

if __name__ == "__main__":
    print("=" * 50)
    print("🚛 MONITOR DE MERCADO PESADO")
    print(f"📍 Buscando notícias dos últimos {DIAS_RETROATIVOS} dias no Google News")
    print("=" * 50)
    executar_crawler()
    print("\n✅ Finalizado!")
