import urllib.request
import urllib.error
import sqlite3
import os
import hashlib
from datetime import datetime
import re

class MonitorPesados:
    def __init__(self, db_path=None):
        # Usa /tmp no Render (diretório gravável)
        if db_path is None:
            db_dir = '/tmp/monitor_data'
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'noticias.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS noticias (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                link TEXT,
                fonte TEXT,
                data_publicacao TEXT,
                data_coleta TEXT,
                resumo TEXT,
                lida INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        print(f"📦 Banco de dados inicializado em {self.db_path}")
    
    def buscar_pagina(self, url):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"   Erro: {e}")
            return None
    
    def extrair_links(self, html, base_url):
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
    
    def extrair_data(self, html):
        padroes = [
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2} de \w+ de \d{4})',
        ]
        for padrao in padroes:
            match = re.search(padrao, html)
            if match:
                return match.group(1)
        return datetime.now().strftime('%d/%m/%Y')
    
    def eh_relevante(self, texto):
        palavras = ['caminhão', 'caminhao', 'ônibus', 'onibus', 'pesado', 'frota', 
                    'carga', 'scania', 'volvo', 'mercedes', 'venda', 'mercado',
                    'volkswagen', 'man', 'pesados', 'caminhões', 'veiculo', 'automotivo',
                    'produção', 'producao', 'frota', 'venda', 'importação', 'exportacao',
                    'eletrico', 'hibrido', 'caminhoneiro', 'transportadora']
        texto_lower = texto.lower()
        return any(p in texto_lower for p in palavras)
    
    def executar(self):
        portais = [
            ("Anfavea", "https://anfavea.com.br/"),
            ("Fenabrave", "https://www.fenabrave.org.br/"),
            ("Sindipeças", "https://www.sindipecas.org.br/"),
            ("ABVE", "https://abve.org.br/"),
            ("Automotive Business", "https://automotivebusiness.com.br/"),
            ("AutoData", "https://www.autodata.com.br/"),
            ("Frota News", "https://frotanews.com.br/"),
            ("Truck & Bus", "https://truckebus.com.br/"),
            ("Novo Varejo", "https://novovarejoautomotivo.com.br/"),
            ("Balcão Automotivo", "https://www.balcaoautomotivo.com/"),
            ("Estradão", "https://estradao.estadao.com.br/"),
            ("Quatro Rodas Mercado", "https://quatrorodas.abril.com.br/noticias/mercado/"),
            ("Senatran Frota de Veículos", "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2025"),
            ("MDIC", "https://www.gov.br/mdic/pt-br"),
            ("Comex Stat", "https://comexstat.mdic.gov.br/"),
            ("IBGE", "https://www.ibge.gov.br/"),
        ]
        
        todas_noticias = []
        
        for nome, url in portais:
            print(f"\n🔍 {nome}...")
            html = self.buscar_pagina(url)
            if html:
                links = self.extrair_links(html, url)
                
                if nome in ['Senatran Frota de Veículos', 'MDIC', 'Comex Stat', 'IBGE', 'Anfavea', 'Fenabrave']:
                    noticias_para_pegar = links[:15]
                else:
                    noticias_para_pegar = [l for l in links if self.eh_relevante(l[0])]
                
                for titulo, link in noticias_para_pegar[:10]:
                    id_hash = hashlib.md5(f"{titulo}{link}".encode()).hexdigest()
                    todas_noticias.append({
                        'id': id_hash,
                        'titulo': titulo[:300],
                        'link': link,
                        'fonte': nome,
                        'data_publicacao': datetime.now().strftime('%d/%m/%Y'),
                        'data_coleta': datetime.now().isoformat(),
                        'resumo': titulo[:150]
                    })
                print(f"   ✅ {len(noticias_para_pegar)} links encontrados")
            else:
                print(f"   ❌ Falha ao acessar")
        
        conn = sqlite3.connect(self.db_path)
        novas = 0
        
        for n in todas_noticias:
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO noticias 
                    (id, titulo, link, fonte, data_publicacao, data_coleta, resumo) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (n['id'], n['titulo'], n['link'], n['fonte'], 
                      n['data_publicacao'], n['data_coleta'], n['resumo']))
                if conn.total_changes > 0:
                    novas += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   🔗 Total de links encontrados: {len(todas_noticias)}")
        print(f"   ✨ Links novos salvos: {novas}")
        return novas

if __name__ == "__main__":
    print("=" * 50)
    print("🚛 MONITOR DE MERCADO PESADO - BRASIL & AMÉRICA LATINA")
    print("=" * 50)
    print(f"📅 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("📰 Coletando notícias de 16 portais...")
    print("-" * 50)
    
    monitor = MonitorPesados()
    monitor.executar()
    
    print("-" * 50)
    print(f"🏁 Finalizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
