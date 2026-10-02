"""차트 모듈: S&P 500 트리맵 히트맵과 스크롤 줌 선 차트."""
import pandas as pd
import plotly.graph_objects as go

TEXT = "#8b93a1"
GRID = "rgba(139,147,161,0.18)"

# 기간별 색상 범위(±%): 이 값 이상이면 가장 진한 색
COLOR_RANGE = {"1D": 3, "1W": 6, "1M": 10, "YTD": 30}


# ---------------------------------------------------------------- 히트맵
def sp500_treemap(df: pd.DataFrame, period: str) -> go.Figure:
    """df 열: ticker, name, sector, market_cap, ret"""
    df = df.dropna(subset=["market_cap", "ret"])
    df = df[df["market_cap"] > 0]

    ids, labels, parents, values, colors, custom = [], [], [], [], [], []

    def add(id_, label, parent, value, ret, name):
        ids.append(id_)
        labels.append(label)
        parents.append(parent)
        values.append(value)
        colors.append(ret)
        custom.append([ret, name, value / 1e9])

    root = "S&P 500"
    total = df["market_cap"].sum()
    add(root, root, "", total, (df["ret"] * df["market_cap"]).sum() / total, "")

    for sector, g in df.groupby("sector"):
        cap = g["market_cap"].sum()
        add(sector, sector, root, cap, (g["ret"] * g["market_cap"]).sum() / cap, "")
        for r in g.itertuples():
            add(r.ticker, r.ticker, sector, r.market_cap, r.ret, r.name)

    rng = COLOR_RANGE.get(period, 3)
    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            customdata=custom,
            marker=dict(
                colors=colors,
                colorscale=[[0, "#c0392b"], [0.5, "#3d4250"], [1, "#1e8e4e"]],
                cmin=-rng,
                cmax=rng,
                cmid=0,
                line=dict(width=1, color="#1b1d22"),
                showscale=False,
            ),
            texttemplate="<b>%{label}</b><br>%{customdata[0]:+.2f}%",
            textposition="middle center",
            textfont=dict(color="white"),
            hovertemplate=(
                "<b>%{label}</b> %{customdata[1]}<br>"
                "등락률 %{customdata[0]:+.2f}%<br>"
                "시가총액 $%{customdata[2]:,.1f}B<extra></extra>"
            ),
            pathbar=dict(visible=True),
            tiling=dict(pad=1),
        )
    )
    fig.update_layout(
        height=680,
        margin=dict(l=0, r=0, t=28, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        uniformtext=dict(minsize=9, mode="hide"),
    )
    return fig


# ---------------------------------------------------------------- 선 차트
# x축을 스크롤로 줌/드래그로 이동하면, 보이는 구간에 맞춰 y축을 자동으로 다시 맞춘다.
_AUTOSCALE_JS = """
var gd = document.getElementById('{plot_id}');
function toMs(v) { return new Date(String(v).replace(' ', 'T')).getTime(); }
var cache = gd.data.map(function (tr) { return Array.from(tr.x, toMs); });
function fitY() {
  var xr = gd._fullLayout.xaxis.range;
  if (!xr) return;
  var x0 = toMs(xr[0]), x1 = toMs(xr[1]), lo = Infinity, hi = -Infinity;
  gd.data.forEach(function (tr, k) {
    var xs = cache[k], ys = tr.y;
    for (var i = 0; i < xs.length; i++) {
      if (xs[i] >= x0 && xs[i] <= x1) {
        var v = ys[i];
        if (v !== null && isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; }
      }
    }
  });
  if (lo === Infinity) return;
  var pad = (hi - lo) * 0.08 || Math.abs(hi) * 0.05 || 1;
  Plotly.relayout(gd, {'yaxis.range': [lo - pad, hi + pad]});
}
gd.on('plotly_relayout', function (ev) {
  for (var k in ev) { if (k.indexOf('xaxis') === 0) { fitY(); return; } }
});
fitY();
"""


def line_chart_html(
    s: pd.Series,
    color: str,
    unit: str = "",
    decimals: int = 2,
    zero_line: bool = False,
    initial_days: int = 365,
    height: int = 340,
) -> str:
    """단순 선 차트를 HTML로 반환 (st.components.v1.html로 렌더링)."""
    s = s.dropna()
    x = s.index.strftime("%Y-%m-%d").tolist()
    y = [round(float(v), 6) for v in s.values]

    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(color=color, width=1.6),
            hovertemplate=f"%{{x}}<br>%{{y:,.{decimals}f}}{unit}<extra></extra>",
        )
    )
    if zero_line:
        fig.add_hline(y=0, line=dict(color=TEXT, width=1, dash="dot"))

    end = s.index[-1]
    start = max(s.index[0], end - pd.Timedelta(days=initial_days))
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=11),
        dragmode="pan",
        hovermode="x",
        showlegend=False,
        xaxis=dict(
            range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")],
            gridcolor=GRID,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor=TEXT,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="전체"),
                ],
                bgcolor="rgba(139,147,161,0.12)",
                activecolor="rgba(139,147,161,0.35)",
                font=dict(color=TEXT),
                x=0,
                y=1.0,
                yanchor="bottom",
            ),
        ),
        # y축은 사용자가 직접 조작하지 않고 JS가 보이는 구간에 맞춰 조정
        yaxis=dict(gridcolor=GRID, fixedrange=True, zeroline=False, side="right"),
    )
    fig.update_layout(margin=dict(t=36))

    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config={"scrollZoom": True, "displaylogo": False, "responsive": True,
                "modeBarButtonsToRemove": ["select2d", "lasso2d", "zoomIn2d", "zoomOut2d"]},
        post_script=_AUTOSCALE_JS,
        default_width="100%",
        default_height=f"{height}px",
    )
    style = "<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}</style>"
    return html.replace("<head>", "<head>" + style, 1)
