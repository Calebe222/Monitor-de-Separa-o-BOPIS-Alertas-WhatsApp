import requests
import urllib3
import json
from datetime import datetime
import pytz

# Desativa avisos de certificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# CONFIGURAÇÕES DE SEGURANÇA (Secrets do Databricks)
# URL corrigida (espaço removido de 'LOJA-geral')
WEBHOOK_N8N = "https://bemol.app.n8n.cloud/webhook/566d9113-725b-LOJA-geral-9dafhj09e-1e083ef81f60"

# Busca o token diretamente do scope 'Bopis_webhook' e chave 'token_auth_bopiss'
TOKEN_VAL = dbutils.secrets.get(scope="Bopis_webhook", key="token_auth_bopiss")
TOKEN_AUTH = f"Bearer {TOKEN_VAL}"

def executar_automacao_bopis():
    if 'lojas_ativas' not in globals() or not lojas_ativas:
        print("🛑 Erro: Variável 'lojas_ativas' não encontrada.")
        return

    fuso = pytz.timezone("America/Manaus")
    agora = datetime.now(fuso)

    for loja in lojas_ativas:
        sigla = loja['sigla']
        centro = loja['centro']
        grupo_id = loja['whatsapp_group']
        regra_horario = loja['regra_atual']
        hora_abertura_str = regra_horario.split('-')[0]
        
        api_url = f"https://srvservicos{sigla}.bemol.local/api"
        print(f"\n--- 📡 Processando Centro {centro} ---")
        
        try:
            res_auth = requests.post(f"{api_url}/token/", json={"username": "painel", "password": "painel"}, verify=False, timeout=10)
            token = res_auth.json()["access"]
            headers = {"Authorization": f"Bearer {token}"}

            res_pedidos = requests.get(f"{api_url}/separation/", headers=headers, verify=False, timeout=15)
            dados_brutos = res_pedidos.json()
            if not isinstance(dados_brutos, list): dados_brutos = [dados_brutos]
            
            print(f"DEBUG: {centro} - Recebidos: {len(dados_brutos)}")

            pedidos_filtrados = []
            for p in dados_brutos:
                origin = str(p.get("origin", "")).upper()
                status = str(p.get("status", "")).upper()
                o_type = str(p.get("order_type", "")).upper()
                
                print(f"DEBUG {centro}: Pedido {p.get('bol_order_number')} | O:{origin} S:{status} T:{o_type}")
                
                if (origin == "BOPIS" and status == "PEN" and o_type == "OUT"):
                    # Lógica de tempo
                    data_str = p.get("last_updated") or f"{p.get('date')}T{p.get('hour')}-04:00"
                    dt_pedido = datetime.fromisoformat(data_str.replace("Z", "-04:00"))
                    if dt_pedido.tzinfo is None: dt_pedido = fuso.localize(dt_pedido)
                    
                    dt_abertura = agora.replace(hour=int(hora_abertura_str[:2]), minute=int(hora_abertura_str[3:]), second=0, microsecond=0)
                    diff = agora - max(dt_pedido, dt_abertura)
                    total_minutos = int(diff.total_seconds() / 60)
                    p["tempo_pendente"] = f"{total_minutos//60}h{total_minutos%60}m" if total_minutos >= 60 else f"{total_minutos}m"
                    
                    res_est = requests.get(f"{api_url}/product/{p.get('id_product')}/stock/", headers=headers, verify=False, timeout=5)
                    p["estoque_fisico"] = res_est.json().get("available", 0) if res_est.status_code == 200 else "N/D"
                    pedidos_filtrados.append(p)

            if not pedidos_filtrados:
                print(f"✅ Centro {centro}: Tudo em dia.")
                continue

            # Montagem da Mensagem
            mensagem = f"🚨 Alerta de Pedidos BOPIS Pendentes - LOJA {centro} 🚨\n\n"
            mensagem += f"📦 Total de Itens Pendentes: {len(pedidos_filtrados)}\n"
            mensagem += "──────────────────\n"

            for i, p in enumerate(pedidos_filtrados):
                nomes = (p.get("customer_name") or "CLIENTE").split(' ')
                cliente_fmt = f"{nomes[0]} {nomes[1]}" if len(nomes) > 1 else nomes[0]
                
                numero_pedido = p.get("bol_order_number", "N/A")
                quantidade = p.get("quantity", "1")
                ean = p.get("ean", "N/A")
                
                mensagem += f"{i+1}. 👤 {cliente_fmt.upper()}\n"
                mensagem += f"🔢 SKU: {p.get('id_product')} | EAN: {ean} | 🛒 {p.get('description', 'N/A').upper()}\n"
                mensagem += f"📦 Qtd: {quantidade} | Estoq.: {p.get('estoque_fisico')} | ⏰ Pendente: {p.get('tempo_pendente')}\n"
                mensagem += f"📝 Pedido: {numero_pedido}\n\n" 

            mensagem += "──────────────────\n"
            mensagem += f"📅 Atualizado às: {agora.strftime('%d/%m/%Y %H:%M')}"

            # Envio para o n8n
            requests.post(
                WEBHOOK_N8N, 
                json={"message": mensagem, "whatsapp_group": grupo_id}, 
                headers={"Authorization": TOKEN_AUTH}, 
                verify=False
            )
            print(f"🚀 Centro {centro}: Enviado.")

        except Exception as e:
            print(f"❌ Erro em {centro}: {str(e)}")

# Execução
executar_automacao_bopis()
