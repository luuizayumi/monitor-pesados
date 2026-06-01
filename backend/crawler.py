import urllib.request
import urllib.error
import urllib.parse
import hashlib
import json
import os
from datetime import datetime, timedelta
import re
import time

print("🚛 CRAWLER - MERCADO PESADO v7 (FOCO EM VOLUME VENDIDO)")
print("=" * 50)

MAX_NOTICIAS_POR_PORTAL = 25
MAX_TOTAL_NOTICIAS = 5000

# Portais normais
PORTAIS = [
    ("ABVE", "https://abve.org.br/"),
    ("Automotive Business", "https://automotivebusiness.com.br/"),
    ("AutoData", "https://www.autodata.com.br/"),
    ("Frota News", "https://frotanews.com.br/"),
    ("Estradão", "https://estradao.estadao.com.br/caminhoes/"),
    ("Quatro Rodas", "https://quatrorodas.abril.com.br/noticias/mercado/"),
    ("Truck & Bus", "https://truckebus.com.br/"),
    ("Balcão Automotivo", "https://www.balcaoautomotivo.com/"),
]

# =====================================================
# KEYWORDS FOCADAS EM VOLUME VENDIDO
# =====================================================
KEYWORDS_GOOGLE = [
    "vendas de caminhões Brasil",
    "caminhões vendidos Brasil",
    "market share caminhões Brasil",
    "participação de mercado caminhões",
    "ranking caminhões mais vendidos",
    "Anfavea vendas caminhões",
    "Fenabrave vendas caminhões",
    "volume de vendas caminhões",
    "vendas de ônibus Brasil",
    "ônibus vendidos Brasil",
    "market share ônibus Brasil",
    "ranking ônibus mais vendidos",
    "caminhão elétrico vendas Brasil",
    "ônibus elétrico vendas Brasil",
    "BYD vendas caminhão elétrico",
    "Scania vendas Brasil",
    "Volvo caminhões vendas Brasil",
    "Mercedes-Benz vendas caminhões",
    "Volkswagen caminhões vendas Brasil",
    "Iveco vendas Brasil",
    "DAF caminhões vendas",
    "MAN caminhões vendas",
]

# =====================================================
# BUSCA NO GOOGLE NEWS
# =====================================================
DIAS_BUSCA = 30

def buscar_google_news(keyword, data_inicio, data_fim):
    """Busca notícias no Google News por período"""
    noticias = []
    
    inicio = data_inicio.strftime("%Y-%m-%d")
    fim = data_fim.strftime("%Y-%m-%d")
    
    query = f"{keyword} after:{inicio} before:{fim}"
    query_encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={query_encoded}&hl=pt-BR&gl=BR&ceid=BR:pt"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            conteudo = r.read().decode('utf-8', errors='ignore')
            
            itens = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>', conteudo, re.DOTALL)
            
            for titulo, link, data_pub in itens[:15]:
                titulo = re.sub(r'<[^>]+>', '', titulo).strip()
                titulo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo)
                
                try:
                    from email.utils import parsedate_to_datetime
                    data_obj = parsedate_to_datetime(data_pub)
                    data_iso = data_obj.isoformat()
                except:
                    data_iso = datetime.now().isoformat()
                
                if titulo and len(titulo) > 25:
                    if any(p in titulo.lower() for p in [
                        'venda', 'vendido', 'comercializado', 'mil', 'unidade',
                        'cresceu', 'caiu', 'aumento', 'participação',
                        'market share', 'ranking', 'lider'
                    ]):
                        noticias.append({
                            'titulo': titulo[:350],
                            'link': link,
                            'fonte': 'Google News',
                            'data_coleta': data_iso
                        })
            
            if noticias:
                print(f"      ✅ {len(noticias)} notícias")
            
    except Exception as e:
        print(f"      ⚠️ Erro: {e}")
    
    return noticias

def buscar_noticias_historicas():
    """Busca notícias dos últimos DIAS_BUSCA dias"""
    todas_noticias = []
    hoje = datetime.now()
    data_inicio = hoje - timedelta(days=DIAS_BUSCA)
    
    print(f"\n🌐 Buscando Google News (últimos {DIAS_BUSCA} dias)...")
    print(f"   🎯 Foco: VOLUME VENDIDO (quantidades, rankings, market share)")
    
    for idx, keyword in enumerate(KEYWORDS_GOOGLE):
        print(f"   🔍 [{idx+1}/{len(KEYWORDS_GOOGLE)}] {keyword}")
        noticias = buscar_google_news(keyword, data_inicio, hoje)
        todas_noticias.extend(noticias)
        time.sleep(0.5)
    
    return todas_noticias

# =====================================================
# CLASSIFICAÇÃO POR MONTADORA
# =====================================================
MONTADORAS = {
    "Scania": ['scania'],
    "Volvo": ['volvo'],
    "Mercedes-Benz": ['mercedes', 'mercedes-benz'],
    "Volkswagen": ['volkswagen', 'vwco'],
    "Iveco": ['iveco'],
    "DAF": ['daf'],
    "MAN": ['man'],
    "Foton": ['foton'],
    "BYD": ['byd caminhão', 'byd ônibus'],
    "JAC": ['jac'],
    "XCMG": ['xcmg'],
    "Sany": ['sany'],
    "Shacman": ['shacman'],
    "Agrale": ['agrale'],
    "Eletra": ['eletra'],
    "Marcopolo": ['marcopolo'],
}

TEMAS = {
    "Vendas": ['venda', 'vendido', 'mil', 'unidade', 'cresceu', 'ranking', 'market share'],
    "Elétricos": ['elétrico', 'eletrico', 'bateria', 'recarga', 'eletrificação'],
    "Lançamentos": ['lança', 'novo', 'estreia', 'lançamento'],
    "Tecnologia": ['tecnologia', 'inovação', 'digital', 'ia'],
}

MODELOS_CARROS = [
    'byd king', 'byd dolphin', 'byd seal', 'vw tera', 'vw polo', 'vw gol',
    'fiat toro', 'fiat mobi', 'hyundai creta', 'toyota corolla', 'honda civic',
    'chevrolet onix', 'jeep renegade'
]

PALAVRAS_CARROS = ['carro', 'sedan', 'hatch', 'suv', 'picape', 'pickup']

def titulo_eh_valido(titulo):
    if len(titulo) < 30:
        return False
    return True

def noticia_eh_pesada(titulo):
    texto_lower = titulo.lower()
    for modelo in MODELOS_CARROS:
        if modelo in texto_lower:
            return False
    for palavra in PALAVRAS_CARROS:
        if palavra in texto_lower:
            return False
    palavras_pesadas = [
        'caminhão', 'caminhao', 'ônibus', 'onibus', 'pesado', 'frota',
        'scania', 'volvo', 'mercedes', 'iveco', 'daf', 'man', 'foton',
        'venda', 'vendido', 'ranking', 'market share'
    ]
    for palavra in palavras_pesadas:
        if palavra in texto_lower:
            return True
    return False

def classificar_destaque(titulo, temas):
    texto = (titulo + ' ' + ' '.join(temas)).lower()
    is_eletrico = any(p in texto for p in ['elétrico', 'eletrico', 'bateria'])
    is_vendas = any(p in texto for p in ['venda', 'vendido', 'mil', 'ranking', 'market share'])
    if is_eletrico and is_vendas:
        return 'ambos'
    if is_eletrico:
        return 'eletrico'
    if is_vendas:
        return 'vendas'
    return 'normal'

def classificar_noticia(texto):
    texto_lower = texto.lower()
    
    montadora = "Geral"
    for nome, palavras in MONTADORAS.items():
        for palavra in palavras:
            if palavra in texto_lower:
                montadora = nome
                break
        if montadora != "Geral":
            break
    
    temas = []
    for tema, palavras in TEMAS.items():
        for palavra in palavras:
            if palavra in texto_lower:
                temas.append(tema)
                break
    
    if not temas:
        temas = ["Geral"]
    
    return montadora, temas

def buscar_pagina(url):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
        return None

def extrair_links(html, base_url):
    links = []
    padrao = r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
    
    for match in re.finditer(padrao, html, re.IGNORECASE | re.DOTALL):
        link = match.group(1)
        texto = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        texto = ' '.join(texto.split())
        
        if texto and len(texto) > 25:
            if not link.startswith(('http://', 'https://')):
                if link.startswith('/'):
                    base = re.match(r'(https?://[^/]+)', base_url)
                    if base:
                        link = base.group(1) + link
                else:
                    link = base_url.rstrip('/') + '/' + link.lstrip('/')
            
            if not link.startswith(('javascript:', 'mailto:', '#')):
                if titulo_eh_valido(texto) and noticia_eh_pesada(texto):
                    montadora, temas = classificar_noticia(texto)
                    destaque = classificar_destaque(texto, temas)
                    links.append({
                        'titulo': texto[:350],
                        'link': link,
                        'montadora': montadora,
                        'temas': temas,
                        'destaque': destaque
                    })
    return links

def carregar_noticias():
    # Tenta carregar da raiz do projeto
    if os.path.exists('noticias.json'):
        with open('noticias.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_noticias(noticias):
    # Salva na raiz do projeto
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)
    print(f"   💾 Notícias salvas em noticias.json")

def executar():
    print("Buscando notícias...")
    print("🎯 FOCO PRINCIPAL: VOLUME VENDIDO (quantidades, rankings, market share)")
    print("-" * 40)
    
    todas_noticias = carregar_noticias()
    ids_existentes = {n['id'] for n in todas_noticias}
    novas_noticias = []
    
    # 1. PORTAIS NORMAIS
    print("\n📰 Buscando portais...")
    for nome, url in PORTAIS:
        print(f"\n🔍 {nome}...")
        html = buscar_pagina(url)
        
        if html:
            links = extrair_links(html, url)
            print(f"   ✅ {len(links)} notícias")
            
            for item in links[:MAX_NOTICIAS_POR_PORTAL]:
                id_hash = hashlib.md5(f"{item['titulo']}{item['link']}".encode()).hexdigest()
                
                if id_hash not in ids_existentes:
                    novas_noticias.append({
                        'id': id_hash,
                        'titulo': item['titulo'],
                        'link': item['link'],
                        'fonte': nome,
                        'montadora': item['montadora'],
                        'temas': item['temas'],
                        'destaque': item['destaque'],
                        'data_coleta': datetime.now().isoformat()
                    })
                    ids_existentes.add(id_hash)
        else:
            print(f"   ❌ Falha")
        
        time.sleep(1)
    
    # 2. GOOGLE NEWS
    google_noticias = buscar_noticias_historicas()
    
    for item in google_noticias:
        id_hash = hashlib.md5(f"{item['titulo']}{item['link']}".encode()).hexdigest()
        
        if id_hash not in ids_existentes:
            montadora, temas = classificar_noticia(item['titulo'])
            destaque = classificar_destaque(item['titulo'], temas)
            novas_noticias.append({
                'id': id_hash,
                'titulo': item['titulo'],
                'link': item['link'],
                'fonte': item['fonte'],
                'montadora': montadora,
                'temas': temas,
                'destaque': destaque,
                'data_coleta': item['data_coleta']
            })
            ids_existentes.add(id_hash)
    
    # Salvar
    if novas_noticias:
        todas_noticias = novas_noticias + todas_noticias
        todas_noticias = todas_noticias[:MAX_TOTAL_NOTICIAS]
        salvar_noticias(todas_noticias)
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO FINAL")
    print("=" * 50)
    print(f"   ✨ Portais: {len([n for n in novas_noticias if n['fonte'] != 'Google News'])} novas")
    print(f"   🌐 Google News: {len([n for n in novas_noticias if n['fonte'] == 'Google News'])} novas")
    print(f"   📰 Total de novas: {len(novas_noticias)}")
    print(f"   📚 Total acumulado: {len(todas_noticias)}")
    print("=" * 50)
    print("✅ Finalizado!")

if __name__ == "__main__":
    executar()
