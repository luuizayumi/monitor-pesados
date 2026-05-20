import sqlite3
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MESMO CAMINHO DO CRAWLER
DB_DIR = "/tmp/monitor_data"
DB_PATH = os.path.join(DB_DIR, "noticias.db")

def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return {"mensagem": "Monitor Mercado Pesado API", "status": "online"}

@app.get("/noticias")
def get_noticias():
    try:
        conn = get_db()
        noticias = conn.execute("SELECT * FROM noticias ORDER BY data_coleta DESC LIMIT 100").fetchall()
        conn.close()
        return [dict(n) for n in noticias]
    except Exception as e:
        return {"erro": str(e), "mensagem": "Nenhuma notícia ainda"}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monitor Mercado Pesado</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f0f2f5; }
            h1 { color: #1a472a; }
            .card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ff6b35; }
            .fonte { color: #666; font-size: 12px; }
            a { color: #1a472a; text-decoration: none; }
            a:hover { color: #ff6b35; }
            .loading { text-align: center; padding: 50px; color: #666; }
        </style>
    </head>
    <body>
        <h1>🚛 Monitor de Mercado Pesado</h1>
        <p>Brasil & América Latina - Notícias do setor de caminhões e ônibus</p>
        <div id="noticias" class="loading">Carregando notícias...</div>
        <script>
            fetch('/noticias')
                .then(r => r.json())
                .then(dados => {
                    if (dados.erro || dados.length === 0) {
                        document.getElementById('noticias').innerHTML = '<p>⏳ Nenhuma notícia ainda. Aguarde o crawler rodar.</p>';
                    } else {
                        document.getElementById('noticias').innerHTML = dados.map(n => `
                            <div class="card">
                                <div class="fonte">📌 ${n.fonte || 'Fonte'}</div>
                                <a href="${n.link}" target="_blank">${n.titulo || 'Sem título'}</a>
                                <div class="fonte">📅 ${new Date(n.data_coleta).toLocaleString()}</div>
                            </div>
                        `).join('');
                    }
                })
                .catch(() => {
                    document.getElementById('noticias').innerHTML = '<p>❌ Erro ao carregar.</p>';
                });
        </script>
    </body>
    </html>
    """
    
