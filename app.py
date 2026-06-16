import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data import generate_orders, generate_daily_metrics, generate_alerts, carrier_performance

st.set_page_config(
    page_title="LogísticaIQ — Monitoramento",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
        options=["Em Trânsito", "Entregue", "Atrasado", "Aguardando Coleta", "Devolvido"],
        default=["Em Trânsito", "Entregue", "Atrasado", "Aguardando Coleta", "Devolvido"],
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

cutoff = datetime.now() - timedelta(days=date_range)
orders = orders_raw[
    (orders_raw["carrier"].isin(selected_carriers)) &
    (orders_raw["status"].isin(selected_statuses)) &
    (pd.to_datetime(orders_raw["created_at"]) >= cutoff)
].copy()

if orders.empty:
    st.warning("Nenhum pedido encontrado com os filtros atuais.")
    st.stop()

alerts = generate_alerts(orders_raw)
carrier_perf = carrier_performance(orders)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📦 Dashboard de Monitoramento Logístico")
st.caption(f"Exibindo {len(orders)} pedidos | Período: últimos {date_range} dias")

# ── KPI Cards ────────────────────────────────────────────────────────────────
total = len(orders)
in_transit = len(orders[orders["status"] == "Em Trânsito"])
delivered = len(orders[orders["status"] == "Entregue"])
delayed = len(orders[orders["status"] == "Atrasado"])
awaiting = len(orders[orders["status"] == "Aguardando Coleta"])
returned = len(orders[orders["status"] == "Devolvido"])
on_time_pct = round((delivered / total * 100), 1) if total > 0 else 0
total_value = orders["value_brl"].sum()
avg_weight = orders["weight_kg"].mean() if total > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📦 Total de Pedidos", f"{total}")
with col2:
    st.metric("🚛 Em Trânsito", f"{in_transit}")
with col3:
    st.metric("✅ Entregues", f"{delivered}", delta=f"{on_time_pct}% no prazo")
with col4:
    st.metric("⏰ Atrasados", f"{delayed}")
with col5:
    st.metric("💰 Valor Total", f"R$ {total_value:,.2f}")

st.divider()

# ── Alerts ────────────────────────────────────────────────────────────────────
with st.expander(f"🔔 Alertas Ativos ({len(alerts)})", expanded=True):
    for alert in alerts:
        if alert["level"] == "danger":
            st.error(f"{alert['icon']} {alert['message']}")
        elif alert["level"] == "warning":
            st.warning(f"{alert['icon']} {alert['message']}")
        else:
            st.info(f"{alert['icon']} {alert['message']}")

# ── Trend + Donut ─────────────────────────────────────────────────────────────
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

    color_map = {
        "Em Trânsito": "#3b82f6",
        "Entregue": "#22c55e",
        "Atrasado": "#ef4444",
        "Aguardando Coleta": "#f59e0b",
        "Devolvido": "#8b5cf6",
    }
    colors = [color_map.get(s, "#94a3b8") for s in status_counts["status"]]

    fig_pie = go.Figure(go.Pie(
        labels=status_counts["status"],
        values=status_counts["count"],
        marker_colors=colors,
        hole=0.5,
        textinfo="percent+label",
        textfont_size=11,
    ))
    fig_pie.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Map of Active Routes ──────────────────────────────────────────────────────
st.subheader("🗺️ Mapa de Rotas e Concentração por Região")

tab_map1, tab_map2 = st.tabs(["Pontos de Origem/Destino", "Rotas em Trânsito"])

with tab_map1:
    all_points = pd.concat([
        orders[["origin_lat", "origin_lon", "carrier", "status", "id"]].rename(
            columns={"origin_lat": "lat", "origin_lon": "lon"}
        ).assign(tipo="Origem"),
        orders[["dest_lat", "dest_lon", "carrier", "status", "id"]].rename(
            columns={"dest_lat": "lat", "dest_lon": "lon"}
        ).assign(tipo="Destino"),
    ])

    fig_scatter = px.scatter_geo(
        all_points,
        lat="lat",
        lon="lon",
        color="tipo",
        color_discrete_map={"Origem": "#3b82f6", "Destino": "#22c55e"},
        hover_data={"carrier": True, "status": True, "id": True},
        scope="south america",
        title="",
    )
    fig_scatter.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#475569",
            showland=True,
            landcolor="#1e293b",
            showocean=True,
            oceancolor="#0f172a",
            showcountries=True,
            countrycolor="#334155",
            lataxis_range=[-35, 6],
            lonaxis_range=[-75, -30],
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab_map2:
    transit = orders[orders["status"] == "Em Trânsito"].head(60).copy()
    fig_lines = go.Figure()

    for _, row in transit.iterrows():
        fig_lines.add_trace(go.Scattergeo(
            lon=[row["origin_lon"], row["dest_lon"]],
            lat=[row["origin_lat"], row["dest_lat"]],
            mode="lines",
            line=dict(width=1),
            showlegend=False,
            hoverinfo="skip",
        ))

    if not transit.empty:
        fig_lines.add_trace(go.Scattergeo(
            lon=transit["origin_lon"].tolist(),
            lat=transit["origin_lat"].tolist(),
            mode="markers",
            marker=dict(size=6, opacity=0.9),
            name="Origem",
            text=transit["origin_city"],
        ))
        fig_lines.add_trace(go.Scattergeo(
            lon=transit["dest_lon"].tolist(),
            lat=transit["dest_lat"].tolist(),
            mode="markers",
            marker=dict(size=6, opacity=0.9),
            name="Destino",
            text=transit["dest_city"],
        ))

    fig_lines.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#475569",
            showland=True,
            landcolor="#1e293b",
            showocean=True,
            oceancolor="#0f172a",
            showcountries=True,
            countrycolor="#334155",
            lataxis_range=[-35, 6],
            lonaxis_range=[-75, -30],
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.05),
    )
    st.plotly_chart(fig_lines, use_container_width=True)

st.divider()

# ── Carrier Performance + Category ───────────────────────────────────────────
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
    st.subheader("📊 Volume por Categoria de Produto")
    cat_counts = orders["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]

    fig_cat = px.bar(
        cat_counts,
        x="count",
        y="category",
        orientation="h",
        labels={"count": "Pedidos", "category": ""},
    )
    fig_cat.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Pedidos",
        yaxis_title="",
    )
    st.plotly_chart(fig_cat, use_container_width=True)

st.divider()

# ── Revenue + Carrier Volume ──────────────────────────────────────────────────
col_r1, col_r2 = st.columns(2)

with col_r1:
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
        annotation_text=f"Média R$ {avg_rev:,.0f}",
        annotation_position="top right"
    )
    fig_rev.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with col_r2:
    st.subheader("🚚 Volume por Transportadora")
    fig_vol = px.pie(
        carrier_perf,
        values="total",
        names="carrier",
        hole=0.4,
    )
    fig_vol.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.1),
    )
    st.plotly_chart(fig_vol, use_container_width=True)

st.divider()

# ── Orders Table ──────────────────────────────────────────────────────────────
st.subheader("🗒️ Listagem de Pedidos")

col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    search = st.text_input(
        "🔍 Buscar por ID, Origem ou Destino",
        placeholder="Ex: PED-301, Sudeste..."
    )
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
display_df["value_fmt"] = display_df["value_brl"].apply(lambda x: f"R$ {x:,.2f}")
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
}).head(100)

st.dataframe(table_data, use_container_width=True, height=380)
st.caption(f"Exibindo até 100 de {len(display_df)} pedidos filtrados")

# ── Bottom KPIs ───────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    st.metric("⏳ Aguardando Coleta", awaiting)
with col_f2:
    st.metric("⚖️ Peso Médio", f"{avg_weight:.1f} kg")
with col_f3:
    st.metric("🔄 Taxa de Devolução", f"{(returned/total*100):.1f}%" if total > 0 else "0%")
with col_f4:
    best_carrier = carrier_perf.loc[carrier_perf["on_time_rate"].idxmax(), "carrier"] if len(carrier_perf) > 0 else "—"
    st.metric("🥇 Melhor Transportadora", best_carrier)
