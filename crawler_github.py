import urllib.request
import urllib.error
import hashlib
import json
import os
from datetime import datetime
import re

print("🚛 INICIANDO CRAWLER (Filtro Contextual)...")

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

# ✅ PALAVRAS QUE INDICAM VEÍCULOS PESADOS (pelo menos uma é obrigatória)
PALAVRAS_PESADO = [
    'caminhão', 'caminhao', 'caminhões', 'caminhoes',
    'ônibus', 'onibus', 'pesado', 'pesados',
    'frota', 'carga', 'logística', 'logistica',
    'transportadora', 'entregas', 'distribuição', 'distribuicao',
    'caminhoneiro', 'treminhão', 'bitrem', 'rodotrem',
    'carreta', 'carretas', 'baú', 'baús', 'graneleiro',
    'cavalo mecânico', 'cavalo mecanico', 'semirreboque',
    'implemento rodoviário', 'implementos rodoviários',
]

# 🚫 PALAVRAS QUE BLOQUEIAM (se aparecer, a notícia é descartada)
PALAVRAS_BLOQUEIO = [
    # Carros e SUVs
    'carro', 'carros', 'sedan', 'hatch', 'suv', 'pick-up', 'pickup', 'picape',
    'esportivo', 'crossover', 'conversível', 'conversivel', 'cupê', 'coupe',
    'hatchback', 'perua', 'station wagon', 'minivan', 'minivan',
    'utilitário', 'utilitario', 'off-road', 'offroad',
    
    # Motos
    'moto', 'motocicleta', 'motovelocidade', 'speed', 'motoqueiro',
    'motogp', 'superbike', 'motocross', 'ciclomotor', 'scooter',
    'motoneta', 'motard', 'custom', 'naked', 'trail', 'big trail',
    
    # Marcas que são predominantemente leves (bloqueio total)
    'king', 'dolphin', 'seal', 'yuan plus', 'song', 'han', 'tang',  # BYD carros
    'tera', 'gol', 'golf', 'polo', 'virtus', 'saveiro', 'fox', 'up',  # VW carros
    'ka', 'fiesta', 'fusion', 'focus', 'ecosport',  # Ford carros
    'mobi', 'argo', 'cronos', 'pulse', 'fastback',  # Fiat carros
    'onix', 'prisma', 'cruze', 'spin', 'tracker',  # GM carros
    'hb20', 'creta', 'santa fé', 'sonata', 'i30',  # Hyundai carros
    'corolla', 'civic', 'city', 'fit', 'hr-v', 'cr-v',  # Honda/Toyota carros
    
    # Modelos de picapes leves (não pesadas)
    'strada', 'toro', 'rampage', 'maui', 'montana', 'saveiro',
    
    # Termos de competição
    'fórmula', 'formula', 'indy', 'stock car', 'automobilismo', 'piloto',
    'grande prêmio', 'grande premio', 'gp', 'corrida', 'pista',
]

def buscar_pagina(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"   Erro: {e}")
        return None

def noticia_eh_pesada(texto):
    """Verifica se a notícia é sobre veículos pesados"""
    texto_lower = texto.lower()
    
    # 🚫 BLOQUEIO PRIORITÁRIO: se tem palavra de carro/moto, rejeita
    for bloqueio in PALAVRAS_BLOQUEIO:
        if bloqueio in texto_lower:
            return False
    
    # ✅ REJEITA se NÃO tem NENHUMA palavra de pesado
    for pesado in PALAVRAS_PESADO:
        if pesado in texto_lower:
            return True
    
    return False

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
                if noticia_eh_pesada(texto):
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
print("🎯 Filtro contextual: apenas veículos PESADOS")
print("   (caminhões, ônibus, frotas, carga, logística)")
print("🚫 Bloqueio: carros, SUVs, picapes leves, motos")
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
        print(f"   ✅ {len(links)} notícias sobre veículos pesados")
        
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
print(f"   ✨ Novas notícias sobre PESADOS: {len(novas_noticias)}")
print(f"   📰 Total acumulado: {len(todas_noticias)}")
print("=" * 50)
print("✅ Finalizado!")
