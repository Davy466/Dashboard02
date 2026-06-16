# LogísticaIQ — Dashboard de Monitoramento Logístico

Dashboard inteligente para monitoramento logístico em tempo real, construído com Streamlit.

## Run & Operate

- `cd streamlit-app && streamlit run app.py` — rodar o dashboard (porta 8000)
- `pnpm --filter @workspace/api-server run dev` — rodar o servidor API (porta 5000)
- `pnpm run typecheck` — typecheck completo de todos os pacotes
- `pnpm run build` — typecheck + build de todos os pacotes
- `pnpm --filter @workspace/api-spec run codegen` — regenerar API hooks e Zod schemas
- `pnpm --filter @workspace/db run push` — aplicar mudanças no schema do DB (apenas dev)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- **Dashboard:** Python 3.11, Streamlit, Pandas, Plotly, NumPy, Faker
- **API:** pnpm workspaces, Node.js 24, TypeScript 5.9, Express 5
- **DB:** PostgreSQL + Drizzle ORM
- **Validação:** Zod (`zod/v4`), `drizzle-zod`
- **Build:** esbuild (CJS bundle)

## Where things live

- `streamlit-app/app.py` — aplicação principal do dashboard
- `streamlit-app/data.py` — geração de dados simulados (pedidos, métricas, alertas)
- `streamlit-app/.streamlit/config.toml` — configuração do servidor Streamlit
- `lib/api-spec/openapi.yaml` — contrato da API (source of truth)

## Product

Dashboard inteligente de monitoramento logístico com:
- KPIs em tempo real (pedidos totais, em trânsito, entregues, atrasados, valor total)
- Alertas ativos para pedidos atrasados e cargas de alto valor
- Gráfico de tendências de entregas (30 dias)
- Distribuição de status por donut chart
- Mapa de rotas ativas com pontos de origem/destino e linhas de rota
- Desempenho por transportadora (taxa no prazo vs. atrasos)
- Volume por categoria de produto
- Receita operacional diária
- Tabela de pedidos com busca e ordenação
- Filtros por transportadora, status e período

## Architecture decisions

- Dashboard usa dados simulados (Faker + NumPy) — pronto para conectar a banco real
- Mapas feitos com Plotly `scatter_geo` (sem necessidade de token Mapbox)
- Cache de dados com `@st.cache_data(ttl=60)` para melhor performance
- Streamlit configurado sem `waitForPort` no workflow para evitar timeout do health check

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Configurar workflow sem `waitForPort` — o Replit health check faz timeout antes do Streamlit estar pronto para servir requisições HTTP quando `waitForPort` é usado
- Não usar pydeck (requer token Mapbox) — usar `plotly.graph_objects.Scattergeo` para mapas

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
