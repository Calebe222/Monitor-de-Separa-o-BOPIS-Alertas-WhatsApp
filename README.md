Monitor de Separação BOPIS — Alertas WhatsApp
Script em Python para execução agendada (Databricks) responsável por monitorar pedidos do tipo BOPIS (Buy Online, Pick Up In Store)
pendentes de separação nas lojas físicas, consultar a disponibilidade de estoque local e despachar alertas formatados para grupos operacionais
de WhatsApp via webhook do n8n.
📌 Visão Geral da Arquitetura
O fluxo opera em duas etapas sequenciais:
[ Agendamento / Cron ]
 │
 ▼
┌──────────────────────────────┐
│ 1. Filtro de Turno e Lojas │ ──> Valida horário local, dia útil, fim de semana
└──────────────┬───────────────┘ e feriados nacionais/estaduais por centro.
 │
 ▼ (Lojas Abertas)
┌──────────────────────────────┐
│ 2. Coleta & Processamento │ ──> Autentica na API local da loja (srvservicos{sigla}).
└──────────────┬───────────────┘ ──> Filtra pedidos: origin="BOPIS", status="PEN", order_type="OUT".
 │ ──> Consulta estoque físico de cada SKU pendente.
 │ ──> Calcula tempo decorrido desde a abertura/pedido.
 ▼
┌──────────────────────────────┐
│ 3. Notificação via n8n │ ──> Dispara payload JSON com o texto formatado para o
└──────────────────────────────┘ ID do grupo de WhatsApp correspondente.
⚙️ Pré-requisitos e Dependências
• Python 3.8+
• Bibliotecas: requests, pytz, urllib3
• Databricks Secret Scope:
o Scope: Bopis_webhook
o Key: token_auth_bopiss
• Conectividade de rede interna resolvida para os domínios locais: srvservicos{sigla}.bemol.local
🛠️ Configurações
1. Calendário de Feriados (FERIADOS)
Dicionário contendo datas no formato MM-DD. Avalia feriados nacionais e feriados estaduais específicos baseados no primeiro dígito do centro:
• 1xx ou 5xx: Amazonas (AM)
• 7xx: Roraima (RR)
• 2xx: Rondônia (RO)
• 4xx: Acre (AC)
2. Dicionário de Lojas (CONFIG_LOJAS)
Estrutura:
Python
"sigla": ["Centro", "Seg-Sex", "Sábado", "Domingo", "Feriado", "ID-GRUPO-WHATSAPP"]
• Horários: Intervalos no formato HH:MM-HH:MM ou "FECHADO".
• Identificador de Grupo: ID JID do WhatsApp (ex: 120363406750381181@g.us ou sufixo -group).
📋 Regra de Negócio de Filtragem
Um pedido gera alerta apenas se cumprir todos os seguintes requisitos simultaneamente:
Campo API Valor
Esperado Descrição
origin BOPIS Pedido originado no e-commerce para retirada em
loja.
status PEN Pedido pendente de separação.
order_type OUT Saída de mercadoria para o cliente.
📲 Formato do Alerta Gerado
Plaintext
 Alerta de Pedidos BOPIS Pendentes - LOJA 701
 Total de Itens Pendentes: 1
──────────────────
1. NOME CLIENTE
 SKU: 123456 | EAN: 7891234567890 | DESCRICAO DO ITEM
 Qtd: 1 | Estoq.: 5 | Pendente: 1h15m
 Pedido: 100234567
──────────────────
 Atualizado às: 26/10/2026 13:00
