from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sqlite3
from datetime import datetime
import os

app = FastAPI(title="Monitor Mercado Pesado API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect('data/noticias.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return {"mensagem": "API do Monitor de Mercado Pesado", "status": "online"}

@app.get("/noticias")
def get_noticias(limite: int = 50, fonte: str = None):
    conn = get_db()
    if fonte:
        query = "SELECT * FROM noticias WHERE fonte = ? ORDER BY data_coleta DESC LIMIT ?"
        noticias = conn.execute(query, (fonte, limite)).fetchall()
    else:
        query = "SELECT * FROM noticias ORDER BY data_coleta DESC LIMIT ?"
        noticias = conn.execute(query, (limite,)).fetchall()
    conn.close()
    return [dict(n) for n in noticias]

@app.get("/noticias/ultimas")
def get_ultimas(limite: int = 10):
    conn = get_db()
    noticias = conn.execute("""
        SELECT * FROM noticias 
        ORDER BY data_coleta DESC 
        LIMIT ?
    """, (limite,)).fetchall()
    conn.close()
    return [dict(n) for n in noticias]

@app.get("/portais")
def get_portais():
    conn = get_db()
    portais = conn.execute("""
        SELECT fonte, COUNT(*) as total 
        FROM noticias 
        GROUP BY fonte 
        ORDER BY total DESC
    """).fetchall()
    conn.close()
    return [dict(p) for p in portais]

@app.get("/stats")
def get_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM noticias").fetchone()[0]
    hoje = conn.execute("""
        SELECT COUNT(*) FROM noticias 
        WHERE date(data_coleta) = date('now')
    """).fetchone()[0]
    conn.close()
    return {"total": total, "hoje": hoje, "ultima_atualizacao": datetime.now().isoformat()}

# Rota para servir o front-end diretamente
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monitor Mercado Pesado</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; }
            .header { background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; padding: 1.5rem 2rem; }
            .header h1 { font-size: 1.8rem; }
            .header p { opacity: 0.8; margin-top: 0.5rem; }
            .stats { display: flex; gap: 1rem; margin-top: 1rem; flex-wrap: wrap; }
            .stat-card { background: rgba(255,255,255,0.1); padding: 0.5rem 1rem; border-radius: 8px; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .filters { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
            .filter-btn { padding: 0.5rem 1rem; border: none; background: white; border-radius: 20px; cursor: pointer; transition: all 0.3s; }
            .filter-btn:hover, .filter-btn.active { background: #16213e; color: white; }
            .noticia-card { background: white; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: transform 0.2s; border-left: 4px solid #e94560; }
            .noticia-card:hover { transform: translateX(5px); }
            .noticia-fonte { display: inline-block; padding: 0.2rem 0.8rem; background: #e0e0e0; border-radius: 20px; font-size: 0.75rem; font-weight: bold; margin-bottom: 0.5rem; }
            .noticia-titulo { font-size: 1.1rem; color: #1a1a2e; text-decoration: none; display: block; margin-bottom: 0.5rem; font-weight: 500; }
            .noticia-titulo:hover { color: #e94560; }
            .noticia-data { font-size: 0.75rem; color: #666; }
            .loading { text-align: center; padding: 2rem; }
            .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #e94560; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚛 Monitor de Mercado Pesado</h1>
            <p>Brasil & América Latina - Notícias em tempo real do setor de caminhões e ônibus</p>
            <div class="stats" id="stats">
                <div class="stat-card">📊 Carregando...</div>
            </div>
        </div>
        <div class="container">
            <div class="filters" id="filters">
                <button class="filter-btn active" data-fonte="todos">📰 Todos</button>
            </div>
            <div id="noticias">
                <div class="loading"><div class="spinner"></div><p>Carregando notícias...</p></div>
            </div>
        </div>
        <script>
            let fonteAtual = 'todos';
            
            async function carregarStats() {
                const res = await fetch('/stats');
                const stats = await res.json();
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">📰 Total: ${stats.total}</div>
                    <div class="stat-card">📅 Hoje: ${stats.hoje}</div>
                    <div class="stat-card">⏰ Última atualização: ${new Date(stats.ultima_atualizacao).toLocaleTimeString()}</div>
                `;
            }
            
            async function carregarPortais() {
                const res = await fetch('/portais');
                const portais = await res.json();
                const filtersDiv = document.getElementById('filters');
                filtersDiv.innerHTML = '<button class="filter-btn active" data-fonte="todos">📰 Todos</button>';
                portais.forEach(p => {
                    const btn = document.createElement('button');
                    btn.className = 'filter-btn';
                    btn.dataset.fonte = p.fonte;
                    btn.textContent = `${p.fonte} (${p.total})`;
                    btn.onclick = () => filtrar(p.fonte);
                    filtersDiv.appendChild(btn);
                });
            }
            
            async function carregarNoticias(fonte = 'todos') {
                document.getElementById('noticias').innerHTML = '<div class="loading"><div class="spinner"></div><p>Carregando...</p></div>';
                let url = fonte === 'todos' ? '/noticias?limite=50' : `/noticias?fonte=${encodeURIComponent(fonte)}&limite=50`;
                const res = await fetch(url);
                const noticias = await res.json();
                renderizarNoticias(noticias);
            }
            
            function renderizarNoticias(noticias) {
                if (noticias.length === 0) {
                    document.getElementById('noticias').innerHTML = '<div style="text-align:center;padding:2rem;">Nenhuma notícia encontrada</div>';
                    return;
                }
                document.getElementById('noticias').innerHTML = noticias.map(n => `
                    <div class="noticia-card">
                        <span class="noticia-fonte">${n.fonte}</span>
                        <a href="${n.link}" target="_blank" class="noticia-titulo">${n.titulo}</a>
                        <div class="noticia-data">📅 ${new Date(n.data_coleta).toLocaleString('pt-BR')}</div>
                    </div>
                `).join('');
            }
            
            function filtrar(fonte) {
                fonteAtual = fonte;
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.dataset.fonte === fonte) btn.classList.add('active');
                });
                carregarNoticias(fonte);
            }
            
            async function atualizarTudo() {
                await carregarStats();
                await carregarPortais();
                await carregarNoticias(fonteAtual);
            }
            
            atualizarTudo();
            setInterval(atualizarTudo, 30000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)