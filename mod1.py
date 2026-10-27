import pytz
from datetime import datetime

# 1. FERIADOS 2026
FERIADOS = {
    "NACIONAL": ["01-01", "04-03", "04-21", "05-01", "06-04", "09-07", "10-12", "11-02", "11-15", "11-20", "12-25"],
    "AM": ["09-05", "12-08"], 
    "RR": ["07-09", "10-05"], 
    "RO": ["01-04", "10-02"], 
    "AC": ["01-23", "06-15", "08-06", "09-05", "11-17"], 
}

# 2. CONFIGURAÇÃO DAS LOJAS (Demorou para fazer isso)
# Estrutura: "sigla": ["Centro", "Seg-Sex", "Sábado", "Domingo", "Feriado", "ID-GRUPO DO WHATSAPP"]
CONFIG_LOJAS = {
    # --- MANAUS ---
    "cam": ["118", "08:00-20:30", "08:00-20:30", "08:00-14:00", "08:00-16:00", "120363407450392088-group"], # Camapuã
    "tqt": ["500", "08:00-20:30", "08:00-20:30", "08:00-14:00", "08:00-19:00", "120363430607491070-group"], # Torquato
    "rbr": ["401", "11:00-23:00", "11:00-23:00", "14:00-22:00", "14:00-22:00", "120363407485751002-group"], # Rio Branco Shopping
    "gvg": ["705", "08:00-19:00", "08:00-19:00", "08:00-13:00", "08:00-13:00", "120363427681885977-group"], # Getúlio Vargas
    "bvb": ["701", "10:00-22:00", "10:00-22:00", "13:00-22:00", "12:00-22:00", "120363406750381181-group"], # 701 - Boa Vista Pátio
    "ata": ["702", "08:00-20:00", "08:00-20:00", "08:00-13:00", "08:00-16:00", "120363430801985644-group"], # Ataíde Teive
    #"ita": ["510", "08:00-19:00", "08:00-19:00", "08:30-12:30", "08:00-13:00", "grupo da 510"], # Itacoatiara
    #"mac": ["520", "08:00-19:00", "08:00-18:00", "08:00-12:00", "08:00-12:00", "grupo da 520"], # Manacapuru
    #"pf":  ["530", "08:00-19:00", "08:00-17:00", "08:00-12:00", "08:00-12:00", "grupo da 530"], # Pres. Figueiredo
    #"pin": ["590", "08:00-19:00", "08:00-19:00", "08:00-12:00", "08:00-12:00", "grupo da 590"], # 590 - Parintins
    #"ciz": ["591", "08:00-19:00", "08:00-19:00", "08:00-12:00", "08:00-12:00", "grupo da 591"], # 591 - Coari
}

def obter_lojas_ativas():
    tz = pytz.timezone("America/Manaus")
    agora = datetime.now(tz)
    hoje_md = agora.strftime("%m-%d")
    dia_semana_num = agora.weekday()
    dia_semana_nome = agora.strftime("%A")
    hora_atual = agora.strftime("%H:%M")
    
    print(f"🕒 Agora: {hora_atual} | Dia: {dia_semana_nome}")

    lojas_para_processar = []

    for sigla, info in CONFIG_LOJAS.items():
        centro = info[0]
        estado = "AM" if centro.startswith(("1", "5")) else \
                 "RR" if centro.startswith("7") else \
                 "RO" if centro.startswith("2") else \
                 "AC" if centro.startswith("4") else "OUTRO"

        eh_feriado = hoje_md in FERIADOS["NACIONAL"] or (estado in FERIADOS and hoje_md in FERIADOS[estado])

        if eh_feriado:
            regra_horario = info[4] # Posição do Feriado
            tipo_dia = f"Feriado ({estado})"
        elif dia_semana_num <= 4:
            regra_horario = info[1] # Seg-Sex
            tipo_dia = "Seg-Sex"
        elif dia_semana_num == 5:
            regra_horario = info[2] # Sábado
            tipo_dia = "Sábado"
        else:
            regra_horario = info[3] # Domingo
            tipo_dia = "Domingo"

        if regra_horario == "FECHADO":
            print(f"😴 Loja {centro} não abre hoje (Motivo: {tipo_dia}).")
            continue

        h_abre, h_fecha = regra_horario.split('-')
        
        if h_abre <= hora_atual <= h_fecha:
            lojas_para_processar.append({
                "sigla": sigla, 
                "centro": centro, 
                "whatsapp_group": info[5], # ID do Grupo na posição 5
                "regra_atual": regra_horario
            })
        else:
            print(f"💤 Loja {centro} fora do horário (Hoje {tipo_dia}: {regra_horario})")
            
    return lojas_para_processar

# Execução do Log
lojas_ativas = obter_lojas_ativas()
