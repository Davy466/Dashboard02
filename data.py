import pandas as pd
from datetime import datetime, timedelta

CARRIERS = ["RotaMax", "ViaCargo", "FlashLog"]

REGION_COORDS = {
    "Sudeste": (-22.90, -43.20),
    "Sul": (-25.43, -49.27),
    "Nordeste": (-8.05, -34.88),
    "Norte": (-3.10, -60.02),
    "Centro-Oeste": (-15.78, -47.93),
}

BASE = [
    (301,"RotaMax","Sudeste",3,7),
    (302,"ViaCargo","Sul",5,5),
    (303,"FlashLog","Nordeste",4,9),
    (304,"RotaMax","Norte",6,4),
    (305,"ViaCargo","Centro-Oeste",2,6),
    (306,"FlashLog","Sul",5,12),
    (307,"RotaMax","Sul",6,9),
    (308,"ViaCargo","Sudeste",3,4),
    (309,"FlashLog","Norte",5,5),
    (310,"ViaCargo","Nordeste",4,8),
]

CATEGORIES = [
    "Eletrônicos",
    "Alimentos",
    "Medicamentos",
    "Industrial",
    "Vestuário",
    "Construção",
    "Automotivo",
    "Tecnologia",
    "Químicos",
    "Diversos",
]

VALUES = [
    1850,
    4200,
    9650,
    3100,
    14800,
    6700,
    5300,
    2600,
    8900,
    11200,
]

WEIGHTS = [
    12.4,
    8.6,
    15.3,
    22.1,
    7.8,
    31.2,
    18.7,
    5.4,
    13.9,
    20.6,
]

def generate_orders(n=10):

    now = datetime.now()
    rows = []

    for i, item in enumerate(BASE):

        pedido, carrier, region, prazo, real = item

        created = now - timedelta(days=20-i)

        expected = created + timedelta(days=prazo)

        delivered = created + timedelta(days=real)

        status = "Atrasado" if real > prazo else "Entregue"

        lat, lon = REGION_COORDS[region]

        rows.append({
            "id": f"PED-{pedido}",
            "id_entrega": pedido,
            "carrier": carrier,
            "transportadora": carrier,
            "status": status,
            "origin_city": region,
            "dest_city": region,
            "regiao": region,
            "origin_lat": lat,
            "origin_lon": lon,
            "dest_lat": lat+0.3,
            "dest_lon": lon+0.3,
            "category": CATEGORIES[i],
            "weight_kg": WEIGHTS[i],
            "value_brl": VALUES[i],
            "created_at": created,
            "expected_at": expected,
            "delivered_at": delivered,
            "sla_days": prazo,
            "prazo_dias": prazo,
            "dias_reais": real,
        })

    return pd.DataFrame(rows)


def generate_daily_metrics(days=30):

    now = datetime.now()

    rows=[]

    for i in range(days):

        d=(now-timedelta(days=days-i-1)).date()

        rows.append({
            "date":d,
            "delivered":18+(i%4),
            "delayed":5+(i%3),
            "in_transit":7+(i%2),
            "revenue":25000+i*650
        })

    return pd.DataFrame(rows)


def generate_alerts(df):

    alerts=[]

    atrasados=df[df["status"]=="Atrasado"]

    for _,r in atrasados.iterrows():

        alerts.append({
            "level":"danger",
            "icon":"🚨",
            "message":f"{r['id']} atrasado ({r['dias_reais']} dias para prazo de {r['prazo_dias']})"
        })

    return alerts


def carrier_performance(df):

    perf=[]

    for carrier in CARRIERS:

        sub=df[df["carrier"]==carrier]

        total=len(sub)

        entregues=len(sub[sub["status"]=="Entregue"])

        atrasados=len(sub[sub["status"]=="Atrasado"])

        perf.append({
            "carrier":carrier,
            "total":total,
            "delivered":entregues,
            "delayed":atrasados,
            "on_time_rate":round(entregues/total*100,1) if total else 0,
            "delay_rate":round(atrasados/total*100,1) if total else 0,
            "avg_value":round(sub["value_brl"].mean(),2) if total else 0,
        })

    return pd.DataFrame(perf)
