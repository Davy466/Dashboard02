import pandas as pd
from datetime import datetime, timedelta

CARRIERS = ["RotaMax", "ViaCargo", "FlashLog"]

# Base fixa com os 10 pedidos da atividade
BASE_ORDERS = [
    # id, transportadora, origem, destino, categoria, peso, valor, prazo_dias, dias_reais
    (301, "RotaMax",   "Sudeste",      "Sul",          "Geral",   12.5, 1450.00, 3, 7),
    (302, "ViaCargo",  "Sul",          "Sudeste",      "Geral",    8.2,  980.00,  5, 5),
    (303, "FlashLog",  "Nordeste",     "Centro-Oeste", "Especial", 16.8, 2300.00, 4, 9),
    (304, "RotaMax",   "Norte",        "Nordeste",     "Geral",    6.4,  760.00,  6, 4),
    (305, "ViaCargo",  "Centro-Oeste", "Sul",          "Especial", 10.1, 1750.00, 2, 6),
    (306, "FlashLog",  "Sul",          "Sudeste",      "Geral",    14.3, 1980.00, 5, 12),
    (307, "RotaMax",   "Sul",          "Norte",        "Especial",  9.7, 1120.00, 6, 9),
    (308, "ViaCargo",  "Sudeste",      "Nordeste",     "Geral",     7.5,  840.00,  3, 4),
    (309, "FlashLog",  "Norte",        "Centro-Oeste", "Especial",  11.9, 1560.00, 5, 5),
    (310, "ViaCargo",  "Nordeste",     "Sul",          "Geral",     13.6, 2100.00, 4, 8),
]

def generate_orders(n=10):
    now = datetime.now()
    rows = []

    total = min(n, len(BASE_ORDERS))

    for i in range(total):
        order_id, carrier, origin, dest, category, weight, value, prazo_dias, dias_reais = BASE_ORDERS[i]

        created_at = now - timedelta(days=15 - i)
        expected_at = created_at + timedelta(days=prazo_dias)
        delivered_at = created_at + timedelta(days=dias_reais)

        status = "Atrasado" if dias_reais > prazo_dias else "Entregue"

        # Coordenadas aproximadas por região para o mapa não quebrar
        region_coords = {
            "Sudeste": (-22.9, -43.2),
            "Sul": (-25.4, -49.3),
            "Nordeste": (-8.0, -34.9),
            "Norte": (-3.1, -60.0),
            "Centro-Oeste": (-15.8, -47.9),
        }

        origin_lat, origin_lon = region_coords.get(origin, (-15.0, -47.0))
        dest_lat, dest_lon = region_coords.get(dest, (-16.0, -48.0))

        rows.append({
            "id": f"PED-{order_id}",
            "id_entrega": order_id,
            "status": status,
            "carrier": carrier,
            "transportadora": carrier,
            "origin_city": origin,
            "dest_city": dest,
            "regiao": origin,
            "origin_lat": origin_lat,
            "origin_lon": origin_lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon,
            "category": category,
            "weight_kg": weight,
            "value_brl": value,
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

    # Série estável para o gráfico não ficar vazio
    for d in range(days):
        date = (now - timedelta(days=days - d - 1)).date()

        delivered = 8 + (d % 5)
        delayed = 1 + (d % 3)
        in_transit = 2 + (d % 4)
        revenue = 900 + (d * 45)

        rows.append({
            "date": date,
            "delivered": delivered,
            "delayed": delayed,
            "in_transit": in_transit,
            "revenue": revenue,
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

    high_value = orders_df[orders_df["value_brl"] > 1800]
    for _, row in high_value.head(3).iterrows():
        alerts.append({
            "level": "warning",
            "icon": "⚠️",
            "message": f"Carga de alto valor R$ {row['value_brl']:,.2f} — Pedido **{row['id']}**",
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
