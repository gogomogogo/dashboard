"""차트 모듈: 스크롤 줌 선 차트와 로고 히트맵(d3)."""
import pandas as pd
import plotly.graph_objects as go

TEXT = "#8b93a1"
GRID = "rgba(139,147,161,0.18)"

# 기간별 색상 범위(±%): 이 값 이상이면 가장 진한 색
COLOR_RANGE = {"1D": 3, "1W": 6, "1M": 10, "YTD": 30}


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


# ---------------------------------------------------------------- 로고 히트맵 (d3)
_HEATMAP_TEMPLATE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
html,body{margin:0;padding:0;background:transparent;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
#bar{height:30px;display:flex;align-items:center;gap:10px;color:#8b93a1;font-size:13px}
#back{display:none;cursor:pointer;border:1px solid rgba(139,147,161,.4);background:transparent;
  color:inherit;border-radius:6px;padding:3px 10px;font-size:12px}
#back:hover{background:rgba(139,147,161,.15)}
#map{position:relative}
.sector{position:absolute;box-sizing:border-box}
.shead{position:absolute;left:0;right:0;top:0;height:20px;padding:0 6px;box-sizing:border-box;
  font-size:12px;font-weight:600;color:#c9ced6;background:#262931;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;line-height:20px;cursor:pointer}
.shead:hover{background:#30343e}
.cell{position:absolute;box-sizing:border-box;border:1px solid #1b1d22;overflow:hidden;
  display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;
  text-shadow:0 1px 2px rgba(0,0,0,.45);line-height:1.08;cursor:default}
.cell:hover{outline:2px solid #fff;outline-offset:-2px;z-index:2}
.cell img{border-radius:20%;background:#fff;object-fit:contain;margin-bottom:3px}
.cell .t{font-weight:700}
.cell .r{opacity:.92}
#tip{position:fixed;pointer-events:none;display:none;z-index:10;background:#16181d;color:#e6e8eb;
  border:1px solid #3a3f4b;border-radius:8px;padding:8px 10px;font-size:12px;line-height:1.5;
  box-shadow:0 4px 14px rgba(0,0,0,.35);max-width:260px}
#tip b{font-size:14px}
</style></head><body>
<div id="bar"><button id="back">← 전체 보기</button><span id="crumb"></span></div>
<div id="map"></div><div id="tip"></div>
<script>
const DATA = __DATA__;
const RANGE = __RANGE__;
const HEIGHT = __HEIGHT__;
const LOGOS = [
  t => `https://financialmodelingprep.com/image-stock/${t}.png`,
  t => `https://assets.parqet.com/logos/symbol/${t}?format=png`,
];
const color = d3.scaleLinear().domain([-RANGE, 0, RANGE])
  .range(["#c0392b", "#3d4250", "#1e8e4e"]).clamp(true);
const fmtPct = v => (v >= 0 ? "+" : "") + v.toFixed(2) + "%";
const fmtCap = v => v >= 1e12 ? "$" + (v / 1e12).toFixed(2) + "T" : "$" + (v / 1e9).toFixed(1) + "B";

// 섹터 > 종목 계층
const sectors = d3.groups(DATA, d => d.s).map(([s, kids]) => ({ name: s, children: kids }));
const tree = { name: "S&P 500", children: sectors };
let focus = null;  // null = 전체, 아니면 섹터명

const map = document.getElementById("map"), tip = document.getElementById("tip");
const back = document.getElementById("back"), crumb = document.getElementById("crumb");
back.onclick = () => { focus = null; render(); };

function weighted(nodes) {
  const cap = d3.sum(nodes, d => d.c);
  return d3.sum(nodes, d => d.r * d.c) / cap;
}

function render() {
  const W = map.clientWidth || document.body.clientWidth, H = HEIGHT - 30;
  map.style.height = H + "px";
  map.innerHTML = "";
  const src = focus ? { name: "S&P 500", children: sectors.filter(s => s.name === focus) } : tree;
  const root = d3.hierarchy(src).sum(d => d.c).sort((a, b) => b.value - a.value);
  d3.treemap().size([W, H]).paddingTop(d => d.depth === 1 ? 20 : 0)
    .paddingInner(d => d.depth === 0 ? 3 : 0).round(true)
    .tile(d3.treemapSquarify.ratio(1.2))(root);

  back.style.display = focus ? "inline-block" : "none";
  crumb.textContent = focus
    ? `${focus}  ${fmtPct(weighted(sectors.find(s => s.name === focus).children))}`
    : `S&P 500 (시총 가중 ${fmtPct(weighted(DATA))}) · 섹터 이름을 클릭하면 확대됩니다`;

  for (const sec of root.children || []) {
    const el = document.createElement("div");
    el.className = "sector";
    Object.assign(el.style, { left: sec.x0 + "px", top: sec.y0 + "px",
      width: sec.x1 - sec.x0 + "px", height: sec.y1 - sec.y0 + "px" });
    const head = document.createElement("div");
    head.className = "shead";
    head.textContent = `${sec.data.name}  ${fmtPct(weighted(sec.data.children))}`;
    head.onclick = () => { focus = focus ? null : sec.data.name; render(); };
    el.appendChild(head);
    map.appendChild(el);

    for (const leaf of sec.leaves()) {
      const d = leaf.data, w = leaf.x1 - leaf.x0, h = leaf.y1 - leaf.y0;
      const c = document.createElement("div");
      c.className = "cell";
      Object.assign(c.style, { left: leaf.x0 + "px", top: leaf.y0 + "px",
        width: w + "px", height: h + "px", background: color(d.r) });

      // 글자 크기: 박스 크기에 비례, 티커 길이로 폭 제한
      const side = Math.min(w, h);
      const fs = Math.max(0, Math.min(side * 0.24, (w - 6) / (d.t.length * 0.66), 34));
      if (fs >= 8) {
        const showLogo = side >= 56 && h >= fs * 2.4 + 24;
        if (showLogo) {
          const img = document.createElement("img");
          const sz = Math.min(side * 0.32, 64);
          img.width = img.height = sz;
          let i = 0;
          img.src = LOGOS[i](d.t);
          img.onerror = () => { i++; if (i < LOGOS.length) img.src = LOGOS[i](d.t); else img.remove(); };
          c.appendChild(img);
        }
        const t = document.createElement("div");
        t.className = "t"; t.style.fontSize = fs + "px"; t.textContent = d.t;
        c.appendChild(t);
        if (h >= fs * 2.1) {
          const r = document.createElement("div");
          r.className = "r"; r.style.fontSize = Math.max(8, fs * 0.62) + "px"; r.textContent = fmtPct(d.r);
          c.appendChild(r);
        }
      }
      c.onmousemove = e => {
        tip.style.display = "block";
        tip.innerHTML = `<b>${d.t}</b> ${d.n}<br>${d.s}<br>등락률 ${fmtPct(d.r)}<br>시가총액 ${fmtCap(d.c)}`;
        const x = e.clientX + 14, y = e.clientY + 14;
        tip.style.left = Math.min(x, window.innerWidth - tip.offsetWidth - 6) + "px";
        tip.style.top = Math.min(y, window.innerHeight - tip.offsetHeight - 6) + "px";
      };
      c.onmouseleave = () => { tip.style.display = "none"; };
      el.parentNode.appendChild(c);
    }
  }
}
render();
let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(render, 150); });
</script></body></html>"""


def heatmap_html(df: pd.DataFrame, period: str, height: int = 760) -> str:
    """로고가 들어간 S&P 500 히트맵 HTML. df 열: ticker, name, sector, market_cap, ret"""
    import json

    df = df.dropna(subset=["market_cap", "ret"])
    df = df[df["market_cap"] > 0]
    records = [
        {"t": r.ticker, "n": r.name, "s": r.sector, "c": float(r.market_cap), "r": round(float(r.ret), 3)}
        for r in df.itertuples()
    ]
    return (
        _HEATMAP_TEMPLATE.replace("__DATA__", json.dumps(records, ensure_ascii=False))
        .replace("__RANGE__", str(COLOR_RANGE.get(period, 3)))
        .replace("__HEIGHT__", str(height))
    )
