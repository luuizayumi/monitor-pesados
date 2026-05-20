import time
from datetime import datetime
import sqlite3
from crawler_completo import MonitorPesados
from email_notifier import EmailNotifier

def executar_crawler():
    """Executa o crawler e salva notícias"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Executando crawler...")
    monitor = MonitorPesados()
    novas = monitor.executar()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Finalizado! {novas} novas notícias.")
    return novas

def enviar_email_diario():
    """Envia email com as notícias do dia"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📧 Enviando relatório diário...")
    notifier = EmailNotifier()
    notifier.enviar_email()

def mostrar_status():
    """Mostra estatísticas do banco"""
    conn = sqlite3.connect('data/noticias.db')
    total = conn.execute("SELECT COUNT(*) FROM noticias").fetchone()[0]
    print(f"📊 Total de notícias no banco: {total}")
    conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🚛 MONITOR AUTOMÁTICO - MERCADO PESADO")
    print("=" * 50)
    print("⏰ Agendamento:")
    print("   🔄 Crawler: a cada 30 minutos")
    print("   📧 Email diário: 08:00 da manhã")
    print("   🔴 Pressione Ctrl+C para parar")
    print("=" * 50)
    
    # Executa uma vez ao iniciar
    executar_crawler()
    mostrar_status()
    
    # Variáveis para controle do agendamento
    ultimo_crawler = time.time()
    ultimo_email = None
    
    while True:
        try:
            agora = time.time()
            
            # Verifica se passaram 30 minutos (1800 segundos)
            if agora - ultimo_crawler >= 1800:
                executar_crawler()
                ultimo_crawler = agora
            
            # Verifica se é 08:00 e ainda não enviou email hoje
            hora_atual = datetime.now().strftime('%H:%M')
            data_hoje = datetime.now().strftime('%Y-%m-%d')
            
            if hora_atual == "08:00" and ultimo_email != data_hoje:
                enviar_email_diario()
                ultimo_email = data_hoje
            
            time.sleep(60)  # Verifica a cada 60 segundos
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor parado pelo usuário.")
            break
        