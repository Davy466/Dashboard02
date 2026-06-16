import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data import generate_orders, generate_daily_metrics, generate_alerts, carrier_performance

st.set_page_config(
    page_title="LogísticaIQ — Atividade",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚚 LogísticaIQ")
    st.caption("Dashboard da atividade logística")
    st.divider()

    st.subheader("Filtros")
    selected_carriers = st.multiselect(
        "Transportadoras",
        options=["RotaMax", "ViaCargo", "FlashLog"],
        default=["RotaMax", "ViaCargo", "FlashLog"],
    )

    selected_statuses = st.multiselect(
        "Status",
        options=["Entregue", "Atrasado", "Em Trânsito", "Aguardando Coleta", "Devolvido"],
        default=["Entregue", "Atrasado", "Em Trânsito", "Aguardando Coleta", "Devolvido"],
    )

    date_range = st.slider("Período (dias atrás)", min_value=1, max_value=30, value=30)

    st.divider()
    st.caption(f"🕐 Atualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    orders = generate_orders(10)
    daily = generate_daily_metrics(30)
    return orders, daily

orders_raw, daily_df = load_data()

orders_raw["created_at"] = pd.to_datetime(orders_raw["created_at"], errors="coerce")
orders_raw["expected_at"] = pd.to_datetime(orders_raw["expected_at"], errors="coerce")

cutoff = datetime.now() - timedelta(days=date_range)
orders = orders_raw[
    (orders_raw["carrier"].isin(selected_carriers)) &
    (orders_raw["status"].isin(selected_statuses)) &
    (orders_raw["created_at"] >= cutoff)
].copy()

if orders.empty:
    st.warning("Nenhum pedido encontrado com os filtros atuais.")
    st.stop()

alerts = generate_alerts(orders_raw)
carrier_perf = carrier_performance(orders)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📦 Dashboard de Monitoramento Logístico")
st.caption(f"Exibindo {len(orders)} pedidos | Dados fixos da atividade")

# ── KPI Cards ────────────────────────────────────────────────────────────────
total = len(orders)
entregues = len(orders[orders["status"] == "Entregue"])
atrasados = len(orders[orders["status"] == "Atrasado"])
em_transito = len(orders[orders["status"] == "Em Trânsito"])
aguardando = len(orders[orders["status"] == "Aguardando Coleta"])
devolvidos = len(orders[orders["status"] == "Devolvido"])

taxa_no_prazo = round((entregues / total) * 100, 1) if total else 0
taxa_atraso = round((atrasados / total) * 100, 1) if total else 0
valor_total = orders["value_brl"].sum()
peso_medio = orders["weight_kg"].mean() if total else 0
ticket_medio = orders["value_brl"].mean() if total else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 Total de Pedidos", f"{total}")
with col2:
    st.metric("✅ Entregues", f"{entregues}", delta=f"{taxa_no_prazo}% no prazo")
with col3:
    st.metric("⏰ Atrasados", f"{atrasados}", delta=f"{taxa_atraso}% do total", delta_color="inverse")
with col4:
    st.metric("⚖️ Peso Médio", f"{peso_medio:.1f} kg")
with col5:
    st.metric("💰 Valor Total", format_brl(valor_total))

st.divider()

# ── Alerts ───────────────────────────────────────────────────────────────────
with st.expander(f"🔔 Alertas Ativos ({len(alerts)})", expanded=True):
    for alert in alerts:
        if alert["level"] == "danger":
            st.error(f"{alert['icon']} {alert['message']}")
        elif alert["level"] == "warning":
            st.warning(f"{alert['icon']} {alert['message']}")
        else:
            st.info(f"{alert['icon']} {alert['message']}")

# ── Trend + Status ──────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Tendência de Entregas (30 dias)")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df["delivered"],
        name="Entregues", mode="lines+markers",
        line=dict(width=2),
        fill="tozeroy"
    ))
    fig_trend.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df["in_transit"],
        name="Em Trânsito", mode="lines+markers",
        line=dict(width=2),
    ))
    fig_trend.add_trace(go.Scatter(
        x=daily_df["date"], y=daily_df["delayed"],
        name="Atrasados", mode="lines+markers",
        line=dict(width=2, dash="dot"),
    ))
    fig_trend.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🥧 Distribuição por Status")
    status_counts = orders["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_pie = px.pie(status_counts, names="status", values="count", hole=0.5)
    fig_pie.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Mapa / Regiões ───────────────────────────────────────────────────────────
st.subheader("🗺️ Mapa de Rotas e Concentração por Região")

all_points = pd.concat([
    orders[["origin_lat", "origin_lon", "carrier", "status", "id"]].rename(
        columns={"origin_lat": "lat", "origin_lon": "lon"}
    ).assign(tipo="Origem"),
    orders[["dest_lat", "dest_lon", "carrier", "status", "id"]].rename(
        columns={"dest_lat": "lat", "dest_lon": "lon"}
    ).assign(tipo="Destino"),
], ignore_index=True)

fig_map = px.scatter_geo(
    all_points,
    lat="lat",
    lon="lon",
    color="tipo",
    color_discrete_map={"Origem": "#3b82f6", "Destino": "#22c55e"},
    hover_data={"carrier": True, "status": True, "id": True},
    scope="south america",
    title="",
)
fig_map.update_layout(
    height=480,
    margin=dict(l=0, r=0, t=10, b=0),
    geo=dict(
        bgcolor="rgba(0,0,0,0)",
        showframe=False,
        showcoastlines=True,
        showland=True,
        showcountries=True,
        lataxis_range=[-35, 6],
        lonaxis_range=[-75, -30],
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Desempenho ───────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 Desempenho por Transportadora")
    fig_carrier = go.Figure()
    fig_carrier.add_trace(go.Bar(
        x=carrier_perf["carrier"],
        y=carrier_perf["on_time_rate"],
        name="% No Prazo",
        text=[f"{v}%" for v in carrier_perf["on_time_rate"]],
        textposition="outside",
    ))
    fig_carrier.add_trace(go.Bar(
        x=carrier_perf["carrier"],
        y=carrier_perf["delay_rate"],
        name="% Atrasos",
        text=[f"{v}%" for v in carrier_perf["delay_rate"]],
        textposition="outside",
    ))
    fig_carrier.update_layout(
        barmode="group",
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="Taxa (%)", range=[0, 115]),
    )
    st.plotly_chart(fig_carrier, use_container_width=True)

with col_b:
    st.subheader("📊 Volume por Região")
    regiao_counts = pd.concat([orders["origin_city"], orders["dest_city"]], ignore_index=True).value_counts().reset_index()
    regiao_counts.columns = ["regiao", "count"]

    fig_regiao = px.bar(
        regiao_counts,
        x="count",
        y="regiao",
        orientation="h",
        labels={"count": "Pedidos", "regiao": ""},
    )
    fig_regiao.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Pedidos",
        yaxis_title="",
    )
    st.plotly_chart(fig_regiao, use_container_width=True)

st.divider()

# ── Receita ─────────────────────────────────────────────────────────────────
st.subheader("💵 Receita Operacional Diária (R$)")
avg_rev = daily_df["revenue"].mean()

fig_rev = go.Figure(go.Bar(
    x=daily_df["date"],
    y=daily_df["revenue"],
    name="Receita",
))
fig_rev.add_hline(
    y=avg_rev,
    line_dash="dot",
    annotation_text=f"Média {format_brl(avg_rev)}",
    annotation_position="top right"
)
fig_rev.update_layout(
    height=280,
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    hovermode="x",
)
st.plotly_chart(fig_rev, use_container_width=True)

st.divider()

# ── Tabela ──────────────────────────────────────────────────────────────────
st.subheader("🗒️ Listagem de Pedidos")

col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    search = st.text_input("🔍 Buscar por ID, Origem ou Destino", placeholder="Ex: PED-301, Sudeste...")
with col_s2:
    sort_col = st.selectbox("Ordenar por", ["created_at", "value_brl", "weight_kg"], index=0)

display_df = orders.copy().sort_values(sort_col, ascending=False)

if search:
    mask = (
        display_df["id"].astype(str).str.contains(search, case=False, na=False) |
        display_df["origin_city"].astype(str).str.contains(search, case=False, na=False) |
        display_df["dest_city"].astype(str).str.contains(search, case=False, na=False)
    )
    display_df = display_df[mask]

display_df["created_at_fmt"] = pd.to_datetime(display_df["created_at"]).dt.strftime("%d/%m/%Y %H:%M")
display_df["expected_at_fmt"] = pd.to_datetime(display_df["expected_at"]).dt.strftime("%d/%m/%Y")
display_df["value_fmt"] = display_df["value_brl"].apply(format_brl)
display_df["weight_fmt"] = display_df["weight_kg"].apply(lambda x: f"{x:.1f} kg")

table_data = display_df[[
    "id", "status", "carrier", "origin_city", "dest_city",
    "category", "weight_fmt", "value_fmt", "created_at_fmt", "expected_at_fmt"
]].rename(columns={
    "id": "Pedido",
    "status": "Status",
    "carrier": "Transportadora",
    "origin_city": "Região Origem",
    "dest_city": "Região Destino",
    "category": "Categoria",
    "weight_fmt": "Peso",
    "value_fmt": "Valor",
    "created_at_fmt": "Criado em",
    "expected_at_fmt": "Previsão",
})

st.dataframe(table_data, use_container_width=True, height=380)
st.caption(f"Exibindo até {len(display_df)} pedidos filtrados")

# ── KPIs finais ──────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    st.metric("⏳ Aguardando Coleta", aguardando)
with col_f2:
    st.metric("🧾 Ticket Médio", format_brl(ticket_medio))
with col_f3:
    st.metric("🔄 Taxa de Devolução", f"{(devolvidos / total * 100):.1f}%" if total > 0 else "0%")
with col_f4:
    best_carrier = carrier_perf.loc[carrier_perf["on_time_rate"].idxmax(), "carrier"] if len(carrier_perf) > 0 else "—"
    st.metric("🥇 Melhor Transportadora", best_carrier)
