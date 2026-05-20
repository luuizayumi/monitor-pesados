import urllib.request
import urllib.error
import sqlite3
import os
import hashlib
from datetime import datetime
import re

print("🚛 INICIANDO MONITOR DE MERCADO PESADO...")

# Lista dos portais
PORTAIS = [
    ("Automotive Business", "https://automotivebusiness.com.br/category/caminhoes/"),
    ("AutoData", "https://www.autodata.com.br/pesados/"),
    ("Frota News", "https://frotanews.com.br/categoria/caminhoes/"),
    ("Estradão", "https://estradao.estadao.com.br/caminhoes/"),
    ("Quatro Rodas", "https://quatrorodas.abril.com.br/noticias/mercado"),
    ("Fenabrave", "https://www.fenabrave.org.br/noticias"),
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
            links.append((texto, link))
    return links

def eh_relevante(texto):
    palavras = ['caminhão', 'caminhao', 'ônibus', 'onibus', 'pesado', 'frota', 
                'carga', 'scania', 'volvo', 'mercedes', 'venda', 'mercado']
    return any(p in texto.lower() for p in palavras)

# Criar banco de dados
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/noticias.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS noticias (
        id TEXT PRIMARY KEY,
        titulo TEXT,
        link TEXT,
        fonte TEXT,
        data_coleta TEXT
    )
''')
conn.commit()

todas = []
for nome, url in PORTAIS:
    print(f"\n🔍 {nome}...")
    html = buscar_pagina(url)
    if html:
        links = extrair_links(html, url)
        relevantes = [l for l in links if eh_relevante(l[0])]
        for titulo, link in relevantes[:10]:
            id_hash = hashlib.md5(f"{titulo}{link}".encode()).hexdigest()
            todas.append((id_hash, titulo, link, nome, datetime.now().isoformat()))
        print(f"   ✅ {len(relevantes)} notícias encontradas")
    else:
        print(f"   ❌ Falha ao acessar")

# Salvar no banco
novas = 0
for n in todas:
    try:
        conn.execute('INSERT OR IGNORE INTO noticias VALUES (?, ?, ?, ?, ?)', n)
        if conn.total_changes > 0:
            novas += 1
    except:
        pass

conn.commit()
conn.close()

print(f"\n📊 RESULTADO: {len(todas)} encontradas, {novas} novas notícias!")

# Mostrar resultados
if novas > 0:
    print("\n📰 ÚLTIMAS NOTÍCIAS:")
    conn = sqlite3.connect('data/noticias.db')
    cursor = conn.execute("SELECT titulo, fonte FROM noticias ORDER BY data_coleta DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"   • [{row[1]}] {row[0][:70]}...")
    conn.close()

print("\n✅ Finalizado!")
