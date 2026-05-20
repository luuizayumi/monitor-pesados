import time
from datetime import datetime
import sqlite3
from crawler_completo import MonitorPesados

def executar_crawler():
    """Executa o crawler e salva notícias"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Executando crawler...")
    try:
        monitor = MonitorPesados()
        novas = monitor.executar()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Finalizado! {novas} novas notícias.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Erro: {e}")

def mostrar_status():
    """Mostra estatísticas do banco"""
    try:
        conn = sqlite3.connect('data/noticias.db')
        total = conn.execute("SELECT COUNT(*) FROM noticias").fetchone()[0]
        print(f"📊 Total de notícias no banco: {total}")
        conn.close()
    except:
        print("📊 Banco de dados ainda não criado")

if __name__ == "__main__":
    print("=" * 50)
    print("🚛 MONITOR AUTOMÁTICO - MERCADO PESADO")
    print("=" * 50)
    print("⏰ Agendamento:")
    print("   🔄 Crawler: a cada 30 minutos")
    print("   🔴 Pressione Ctrl+C para parar")
    print("=" * 50)
    
    # Executa uma vez ao iniciar
    executar_crawler()
    mostrar_status()
    
    # Controle do tempo
    ultimo_crawler = time.time()
    
    while True:
        try:
            agora = time.time()
            
            # Verifica se passaram 30 minutos (1800 segundos)
            if agora - ultimo_crawler >= 1800:
                executar_crawler()
                mostrar_status()
                ultimo_crawler = agora
            
            time.sleep(60)  # Verifica a cada 60 segundos
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor parado pelo usuário.")
            break
        