import pandas as pd
from datetime import datetime, timedelta

CARRIERS = ["RotaMax", "ViaCargo", "FlashLog"]

REGION_COORDS = {
    "Sudeste": (-22.9, -43.2),
    "Sul": (-25.4, -49.3),
    "Nordeste": (-8.0, -34.9),
    "Norte": (-3.1, -60.0),
    "Centro-Oeste": (-15.8, -47.9),
}

# id, transportadora, origem, destino, categoria, peso, valor, prazo_dias, dias_reais
BASE_ORDERS = [
    (301, "RotaMax",   "Sudeste",      "Sul",          "Eletrônicos", 12.5,  1480.00, 3, 2),
    (302, "ViaCargo",  "Sul",          "Sudeste",      "Alimentos",    8.2,  3120.00, 5, 6),
    (303, "FlashLog",  "Nordeste",     "Centro-Oeste", "Especial",    16.8,  7600.00, 4, 4),
    (304, "RotaMax",   "Norte",        "Nordeste",     "Construção",   6.4,   950.00,  6, 10),
    (305, "ViaCargo",  "Centro-Oeste", "Sul",          "Medicamentos", 10.1, 18500.00, 2, 2),
    (306, "FlashLog",  "Sul",          "Sudeste",      "Vestuário",    14.3,  2240.00, 5, 8),
    (307, "RotaMax",   "Sul",          "Norte",        "Industrial",    9.7,  4100.00, 6, 5),
    (308, "ViaCargo",  "Sudeste",      "Nordeste",     "Alimentos",     7.5,   670.00,  3, 3),
    (309, "FlashLog",  "Norte",        "Centro-Oeste", "Especial",     11.9, 12900.00, 5, 7),
    (310, "ViaCargo",  "Nordeste",     "Sul",          "Eletrônicos",   13.6,  5400.00, 4, 4),
]

def generate_orders(n=10):
    now = datetime.now()
    rows = []
    total = min(n, len(BASE_ORDERS))

    for i in range(total):
        order_id, carrier, origin, dest, category, weight, value, prazo_dias, dias_reais = BASE_ORDERS[i]

        created_at = now - timedelta(days=14 - i)
        expected_at = created_at + timedelta(days=prazo_dias)
        delivered_at = created_at + timedelta(days=dias_reais)

        status = "Atrasado" if dias_reais > prazo_dias else "Entregue"

        origin_lat, origin_lon = REGION_COORDS.get(origin, (-15.0, -47.0))
        dest_lat, dest_lon = REGION_COORDS.get(dest, (-16.0, -48.0))

        # leve variação para não empilhar os pontos no mapa
        lat_shift = (i % 3 - 1) * 0.25
        lon_shift = (i % 4 - 1.5) * 0.25

        rows.append({
            "id": f"PED-{order_id}",
            "id_entrega": order_id,
            "status": status,
            "carrier": carrier,
            "transportadora": carrier,
            "origin_city": origin,
            "dest_city": dest,
            "regiao": origin,
            "origin_lat": origin_lat + lat_shift,
            "origin_lon": origin_lon + lon_shift,
            "dest_lat": dest_lat - lat_shift,
            "dest_lon": dest_lon - lon_shift,
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

    for d in range(days):
        date = (now - timedelta(days=days - d - 1)).date()

        delivered = 18 + (d % 6)
        delayed = 2 + (d % 4)
        in_transit = 5 + ((d + 2) % 5)
        revenue = 12000 + (d * 320) + ((d % 7) * 150)

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

    high_value = orders_df[orders_df["value_brl"] >= 10000]
    for _, row in high_value.head(3).iterrows():
        alerts.append({
            "level": "warning",
            "icon": "⚠️",
            "message": f"Carga de alto valor {row['id']} no valor de {row['value_brl']:,.2f}",
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
        avg_weight = sub["weight_kg"].mean() if total > 0 else 0

        perf.append({
            "carrier": carrier,
            "total": total,
            "delivered": delivered,
            "delayed": delayed,
            "on_time_rate": round(on_time_rate, 1),
            "delay_rate": round(delay_rate, 1),
            "avg_value": round(avg_value, 2),
            "avg_weight": round(avg_weight, 2),
        })

    return pd.DataFrame(perf)
