import pandas as pd
from datetime import datetime, timedelta

CARRIERS = ["RotaMax", "ViaCargo", "FlashLog"]

def generate_orders(n=10):
    base = [
        [301, "RotaMax",   "Sudeste",     3,  7],
        [302, "ViaCargo",  "Sul",         5,  5],
        [303, "FlashLog",  "Nordeste",    4,  9],
        [304, "RotaMax",   "Norte",       6,  4],
        [305, "ViaCargo",  "Centro-Oeste",2,  6],
        [306, "FlashLog",  "Sul",         5, 12],
        [307, "RotaMax",   "Sul",         6,  9],
        [308, "ViaCargo",  "Sudeste",     3,  4],
        [309, "FlashLog",  "Norte",       5,  5],
        [310, "ViaCargo",  "Nordeste",    4,  8],
    ]

    now = datetime.now()
    rows = []

    for i, (id_entrega, carrier, regiao, prazo_dias, dias_reais) in enumerate(base):
        atraso = dias_reais > prazo_dias
        status = "Atrasado" if atraso else "Entregue"

        created_at = now - timedelta(days=15 - i)
        expected_at = created_at + timedelta(days=prazo_dias)
        delivered_at = created_at + timedelta(days=dias_reais)

        rows.append({
            "id": f"PED-{id_entrega}",
            "id_entrega": id_entrega,
            "status": status,
            "carrier": carrier,
            "transportadora": carrier,
            "regiao": regiao,
            "origin_city": regiao,
            "dest_city": regiao,
            "origin_lat": -15.0 + i * 0.1,
            "origin_lon": -47.0 + i * 0.1,
            "dest_lat": -16.0 + i * 0.1,
            "dest_lon": -48.0 + i * 0.1,
            "category": "Geral",
            "weight_kg": 10 + i,
            "value_brl": 1000 + i * 100,
            "created_at": created_at,
            "expected_at": expected_at,
            "delivered_at": delivered_at,
            "sla_days": prazo_dias,
            "prazo_dias": prazo_dias,
            "dias_reais": dias_reais,
        })

    return pd.DataFrame(rows)

def generate_daily_metrics(days=30):
    now = datetime.now()
    rows = []
    for d in range(days):
        date = (now - timedelta(days=days - d - 1)).date()
        rows.append({
            "date": date,
            "delivered": 5,
            "delayed": 2,
            "in_transit": 3,
            "revenue": 1000 + d * 50,
        })
    return pd.DataFrame(rows)

def generate_alerts(orders_df):
    alerts = []
    delayed = orders_df[orders_df["status"] == "Atrasado"]

    for _, row in delayed.iterrows():
        alerts.append({
            "level": "danger",
            "icon": "🚨",
            "message": f"Pedido **{row['id']}** ({row['regiao']}) atrasado via {row['carrier']}",
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

        perf.append({
            "carrier": carrier,
            "total": total,
            "delivered": delivered,
            "delayed": delayed,
            "on_time_rate": round(on_time_rate, 1),
            "delay_rate": round(delay_rate, 1),
            "avg_value": round(sub["value_brl"].mean(), 2) if total > 0 else 0,
        })

    return pd.DataFrame(perf)
