import urllib.request
import urllib.error
import hashlib
import json
import os
from datetime import datetime
import re

print("🚛 INICIANDO CRAWLER...")

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
                'carga', 'scania', 'volvo', 'mercedes', 'venda', 'mercado']
    return any(p in texto.lower() for p in palavras)

def carregar_noticias_existentes():
    if os.path.exists('noticias.json'):
        with open('noticias.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_noticias(noticias):
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

# Executar
todas_noticias = carregar_noticias_existentes()
ids_existentes = {n['id'] for n in todas_noticias}
novas_noticias = []

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

todas_noticias = novas_noticias + todas_noticias
todas_noticias = todas_noticias[:500]
salvar_noticias(todas_noticias)

print(f"\n📊 RESULTADO: {len(novas_noticias)} novas notícias!")
print(f"📰 Total: {len(todas_noticias)} notícias")
