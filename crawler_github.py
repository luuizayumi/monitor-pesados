import urllib.request
import urllib.error
import hashlib
import json
import os
from datetime import datetime
import re

print("🚛 INICIANDO CRAWLER...")

# Lista dos portais especializados em mercado pesado
PORTAIS = [
    ("ABVE", "https://abve.org.br/"),
    ("Automotive Business", "https://automotivebusiness.com.br/"),
    ("AutoData", "https://www.autodata.com.br/"),
    ("Frota News", "https://frotanews.com.br/"),
    ("Estradão - Jornal do Carro", "https://estradao.estadao.com.br/caminhoes/"),
    ("Quatro Rodas Mercado", "https://quatrorodas.abril.com.br/noticias/mercado/"),
    ("Truck & Bus", "https://truckebus.com.br/"),
    ("Balcão Automotivo", "https://www.balcaoautomotivo.com/"),
]

def buscar_pagina(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
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
                # Filtra por palavras-chave do setor pesado (COMPLETO)
                if any(p in texto.lower() for p in [
                    # Categorias gerais
                    'caminhão', 'caminhao', 'ônibus', 'onibus', 'pesado', 'pesados',
                    'frota', 'carga', 'venda', 'mercado', 'veiculo', 'automotivo',
                    
                    # Marcas de caminhões (tradicionais)
                    'volkswagen', 'vw', 'vwco', 'mercedes', 'mercedes-benz', 'mercedes benz',
                    'volvo', 'scania', 'iveco', 'daf', 'man', 'foton', 'jac', 'ford', 
                    'agrale', 'ram', 'hyundai',
                    
                    # Marcas de ônibus (tradicionais)
                    'volksbus', 'marcopolo', 'busscar', 'caio', 'neobus', 'comil',
                    
                    # Termos do setor (tradicionais)
                    'anfavea', 'fenabrave', 'emplacamentos', 'licenciamentos', 'renavam',
                    
                    # Marcas de caminhões elétricos
                    'byd', 'e-delivery', 'edelivery', 'eactros', 'fm electric', 'e-transit',
                    'etransit', 'e-daily', 'edaily', 'iev1200t', 'iev1800t', 'iblue',
                    'eon etruck', 'xcmg', 'tevx', 'higer',
                    
                    # Marcas de ônibus elétricos
                    'eletra', 'e-bus', 'ebus', 'eotro', 'd9w', 'd11a', 'attivi integral',
                    'a12br', 'a18br', 'e500u', 'e-millennium', 'emillennium', 'e-volksbus',
                    
                    # Termos de eletrificação
                    'caminhão elétrico', 'caminhao eletrico', 'ônibus elétrico',
                    'onibus eletrico', 'veículo elétrico', 'veiculo eletrico',
                    'mobilidade elétrica', 'mobilidade eletrica', 'frota elétrica',
                    'frota eletrica', 'transição energética', 'bateria blade',
                    'bateria de lítio', 'infraestrutura de recarga', 'recarga rápida',
                    'emissão zero', 'zero emissão', 'carbono neutro', 'eletrificação',
                    'eletrificacao', 'veículo elétrico pesado', 'veiculo eletrico pesado',
                    
                    # Termos específicos ônibus elétricos
                    'ônibus elétrico urbano', 'onibus eletrico urbano',
                    'ônibus elétrico articulado', 'onibus eletrico articulado',
                    'troleybus', 'trolebus', 'eletrobus'
                ]):
                    links.append((texto, link))
    return links

def carregar_noticias_existentes():
    if os.path.exists('noticias.json'):
        with open('noticias.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_noticias(noticias):
    with open('noticias.json', 'w', encoding='utf-8') as f:
        json.dump(noticias, f, ensure_ascii=False, indent=2)

# Executar
print("=" * 50)
print("🚛 MONITOR DE MERCADO PESADO")
print("=" * 50)

todas_noticias = carregar_noticias_existentes()
ids_existentes = {n['id'] for n in todas_noticias}
novas_noticias = []

for nome, url in PORTAIS:
    print(f"\n🔍 {nome}...")
    print(f"   URL: {url}")
    html = buscar_pagina(url)
    if html:
        links = extrair_links(html, url)
        print(f"   ✅ {len(links)} links encontrados")
        
        for titulo, link in links[:15]:
            id_hash = hashlib.md5(f"{titulo}{link}".encode()).hexdigest()
            if id_hash not in ids_existentes:
                novas_noticias.append({
                    'id': id_hash,
                    'titulo': titulo[:300],
                    'link': link,
                    'fonte': nome,
                    'data_coleta': datetime.now().isoformat()
                })
                ids_existentes.add(id_hash)
    else:
        print(f"   ❌ Falha ao acessar")

# Salvar
todas_noticias = novas_noticias + todas_noticias
todas_noticias = todas_noticias[:1000]
salvar_noticias(todas_noticias)

print("\n" + "=" * 50)
print("📊 RESULTADO FINAL")
print("=" * 50)
print(f"   ✨ Novas notícias: {len(novas_noticias)}")
print(f"   📰 Total acumulado: {len(todas_noticias)}")
print("=" * 50)
print("✅ Finalizado!")
