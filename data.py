import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# 1. TRANSPORTADORAS REAIS DA SUA TABELA
CARRIERS = ["RotaMax", "ViaCargo", "FlashLog"]
STATUSES = ["Em Trânsito", "Entregue", "Atrasado", "Aguardando Coleta", "Devolvido"]
STATUS_WEIGHTS = [0.35, 0.40, 0.12, 0.10, 0.03]

# 2. REGIÕES DA TABELA MAPEADAS COM COORDENADAS CENTRAIS PARA O MAPA NÃO QUEBRAR
ORIGINS = [
    ("Sudeste", -21.7642, -43.3496),
    ("Sul", -27.5954, -48.5480),
    ("Nordeste", -8.0476, -34.8770),
    ("Norte", -3.1190, -60.0217),
    ("Centro-Oeste", -15.7801, -47.9292),
]

DESTINATIONS = [
    ("Sudeste", -22.9099, -47.0626),
    ("Sul", -25.4297, -49.2711),
    ("Nordeste", -5.7945, -35.2110),
    ("Norte", -1.4558, -48.4902),
    ("Centro-Oeste", -16.6869, -49.2648),
]

PRODUCT_CATEGORIES = ["Geral", "Especial"]

def generate_orders(n=200):
    now = datetime.now()
    rows = []
    for i in range(n):
        origin = random.choice(ORIGINS)
        dest = random.choice(DESTINATIONS)
        status = random.choices(STATUSES, STATUS_WEIGHTS)[0]
        carrier = random.choice(CARRIERS)
        days_ago = random.randint(0, 30)
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        # Ajustando prazos para ficarem parecidos com os da tabela (entre 2 e 6 dias)
        sla_days = random.randint(2, 6)
        expected = created + timedelta(days=sla_days)
        
        if status == "Entregue":
            # Simula algumas entregas dentro e outras fora do prazo
            delivered = created + timedelta(days=random.randint(1, sla_days + 3))
        else:
            delivered = None
            
        weight = round(random.uniform(0.5, 50.0), 2)
        value = round(random.uniform(50, 5000), 2)
        lat_noise = random.uniform(-1, 1)
        lon_noise = random.uniform(-1, 1)
        rows.append({
            "id": f"PED-{10000 + i}",
            "status": status,
            "carrier": carrier,
            "origin_city": origin[0],
            "origin_lat": origin[1] + lat_noise * 0.1,
            "origin_lon": origin[2] + lon_noise * 0.1,
            "dest_city": dest[0],
            "dest_lat": dest[1] + lat_noise * 0.1,
            "dest_lon": dest[2] + lon_noise * 0.1,
            "category": random.choice(PRODUCT_CATEGORIES),
            "weight_kg": weight,
            "value_brl": value,
            "created_at": created,
            "expected_at": expected,
            "delivered_at": delivered,
            "sla_days": sla_days,
        })
    return pd.DataFrame(rows)

def generate_daily_metrics(days=30):
    now = datetime.now()
    rows = []
    base_delivered = 80
    base_delayed = 15
    for d in range(days):
        date = (now - timedelta(days=days - d - 1)).date()
        delivered = max(0, int(base_delivered + np.random.normal(0, 10)))
        delayed = max(0, int(base_delayed + np.random.normal(0, 4)))
        in_transit = max(0, int(delivered * 0.6 + np.random.normal(0, 5)))
        rows.append({
            "date": date,
            "delivered": delivered,
            "delayed": delayed,
            "in_transit": in_transit,
            "revenue": round((delivered * random.uniform(150, 300)), 2),
        })
    return pd.DataFrame(rows)

def generate_alerts(orders_df):
    alerts = []
    delayed = orders_df[orders_df["status"] == "Atrasado"]
    for _, row in delayed.head(5).iterrows():
        alerts.append({
            "level": "danger",
            "icon": "🚨",
            "message": f"Pedido **{row['id']}** ({row['origin_city']} → {row['dest_city']}) atrasado via {row['carrier']}",
        })
    high_value = orders_df[(orders_df["status"] == "Em Trânsito") & (orders_df["value_brl"] > 3000)]
    for _, row in high_value.head(3).iterrows():
        alerts.append({
            "level": "warning",
            "icon": "⚠️",
            "message": f"Carga de alto valor R$ {row['value_brl']:,.2f} em trânsito — Pedido **{row['id']}**",
        })
    alerts.append({
        "level": "info",
        "icon": "ℹ️",
        "message": "Relatório semanal de desempenho disponível para download",
    })
    return alerts

def carrier_performance(orders_df):
    perf = []
    for carrier in CARRIERS:
        sub = orders_df[orders_df["carrier"] == carrier]
        total = len(sub)
        delivered = len(sub[sub["status"] == "Entregue"])
        delayed = len(sub[sub["status"] == "Atrasado"])
        on_time_rate = (delivered / total * 100) if total > 0 else 0
        delay_rate = (delayed / total * 100) if total > 0 else 0
        avg_value = sub["value_brl"].mean() if total > 0 else 0
        perf.append({
            "carrier": carrier,
            "total": total,
            "delivered": delivered,
            "delayed": delayed,
            "on_time_rate": round(on_time_rate, 1),
            "delay_rate": round(delay_rate, 1),
            "avg_value": round(avg_value, 2),
        })
    return pd.DataFrame(perf)
