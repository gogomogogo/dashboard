"""차트 모듈: 스크롤 줌 선 차트와 로고 히트맵(d3)."""
import pandas as pd
import plotly.graph_objects as go

TEXT = "#8b93a1"
GRID = "rgba(139,147,161,0.18)"

# 기간별 색상 범위(±%): 이 값 이상이면 가장 진한 색
COLOR_RANGE = {"1D": 3, "1W": 6, "1M": 10, "YTD": 30}


# ---------------------------------------------------------------- 선 차트
# x축을 스크롤로 줌/드래그로 이동하면, 보이는 구간에 맞춰 각 패널의 y축을 자동으로 다시 맞춘다.
# layout.meta.fixed 에 적힌 y축(예: RSI 0~100)은 건드리지 않는다.
_AUTOSCALE_JS = """
var gd = document.getElementById('{plot_id}');
var FIXED = (gd.layout.meta && gd.layout.meta.fixed) || [];
function toMs(v) { return new Date(String(v).replace(' ', 'T')).getTime(); }
var cache = gd.data.map(function (tr) { return Array.from(tr.x, toMs); });
var minX = Math.min.apply(null, cache.map(function (c) { return c[0]; }));
var maxX = Math.max.apply(null, cache.map(function (c) { return c[c.length - 1]; }));
var DAY = 86400000;
function iso(ms) { return new Date(ms).toISOString().slice(0, 10); }
function fitY() {
  var xr = gd._fullLayout.xaxis.range;
  if (!xr) return;
  var x0 = toMs(xr[0]), x1 = toMs(xr[1]), box = {};
  // 데이터 범위 밖으로 너무 멀리 줌아웃/이동하지 않게 고정
  var span = x1 - x0, lo0 = minX - 3 * DAY, hi0 = maxX + Math.max(3 * DAY, span * 0.02);
  if (x0 < lo0 || x1 > hi0) {
    if (span >= hi0 - lo0) { x0 = lo0; x1 = hi0; }
    else if (x0 < lo0) { x0 = lo0; x1 = lo0 + span; }
    else { x1 = hi0; x0 = hi0 - span; }
    Plotly.relayout(gd, {'xaxis.range': [iso(x0), iso(x1)]});
    return;
  }
  gd.data.forEach(function (tr, k) {
    if (tr.visible === false || tr.visible === 'legendonly') return;
    var ax = 'yaxis' + (tr.yaxis ? tr.yaxis.slice(1) : '');
    if (FIXED.indexOf(ax) >= 0) return;
    var xs = cache[k], hi = tr.high || tr.y, lo = tr.low || tr.y;
    var b = box[ax] || (box[ax] = [Infinity, -Infinity, tr.type === 'bar']);
    if (tr.type === 'bar') b[2] = true;
    for (var i = 0; i < xs.length; i++) {
      if (xs[i] >= x0 && xs[i] <= x1) {
        var l = lo[i], h = hi[i];
        if (l !== null && isFinite(l) && l < b[0]) b[0] = l;
        if (h !== null && isFinite(h) && h > b[1]) b[1] = h;
      }
    }
  });
  var upd = {};
  for (var ax in box) {
    var lo = box[ax][0], hi = box[ax][1];
    if (lo === Infinity) continue;
    if (box[ax][2]) { lo = Math.min(lo, 0); hi = Math.max(hi, 0); }
    var pad = (hi - lo) * 0.06 || Math.abs(hi) * 0.05 || 1;
    upd[ax + '.range'] = [box[ax][2] && lo === 0 ? 0 : lo - pad, hi + pad];
  }
  if (Object.keys(upd).length) Plotly.relayout(gd, upd);
}
gd.on('plotly_relayout', function (ev) {
  for (var k in ev) { if (k.indexOf('xaxis') === 0) { fitY(); return; } }
});
gd.on('plotly_restyle', fitY);
fitY();
"""

_CONFIG = {
    "scrollZoom": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["select2d", "lasso2d", "zoomIn2d", "zoomOut2d"],
}


def _range_buttons(short: bool = True):
    buttons = [
        dict(count=1, label="1M", step="month", stepmode="backward"),
        dict(count=6, label="6M", step="month", stepmode="backward"),
        dict(count=1, label="1Y", step="year", stepmode="backward"),
        dict(count=5, label="5Y", step="year", stepmode="backward"),
        dict(step="all", label="전체"),
    ]
    return dict(
        buttons=buttons,
        bgcolor="rgba(139,147,161,0.12)",
        activecolor="rgba(139,147,161,0.35)",
        font=dict(color=TEXT),
        x=0,
        y=1.0,
        yanchor="bottom",
    )


def _to_html(fig, height: int) -> str:
    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=True,
        config=_CONFIG,
        post_script=_AUTOSCALE_JS,
        default_width="100%",
        default_height=f"{height}px",
    )
    style = "<style>html,body{margin:0;padding:0;background:transparent;overflow:hidden}</style>"
    return html.replace("<head>", "<head>" + style, 1)


def _base_layout(fig, height: int):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=58, t=36, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=11),
        dragmode="pan",
    )


def line_chart_html(
    s: pd.Series,
    color: str,
    unit: str = "",
    decimals: int = 2,
    zero_line: bool = False,
    initial_days: int = 365,
    height: int = 340,
) -> str:
    """단순 선 차트를 HTML로 반환."""
    s = s.dropna()
    fig = go.Figure(
        go.Scatter(
            x=s.index.strftime("%Y-%m-%d").tolist(),
            y=[round(float(v), 6) for v in s.values],
            mode="lines",
            line=dict(color=color, width=1.6),
            hovertemplate=f"%{{x}}<br>%{{y:,.{decimals}f}}{unit}<extra></extra>",
        )
    )
    if zero_line:
        fig.add_hline(y=0, line=dict(color=TEXT, width=1, dash="dot"))

    end = s.index[-1]
    start = max(s.index[0], end - pd.Timedelta(days=initial_days))
    _base_layout(fig, height)
    fig.update_layout(
        hovermode="x",
        showlegend=False,
        xaxis=dict(
            range=[start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")],
            gridcolor=GRID,
            showspikes=True,
            spikemode="across",
            spikethickness=1,
            spikecolor=TEXT,
            rangeselector=_range_buttons(),
        ),
        # y축은 사용자가 직접 조작하지 않고 JS가 보이는 구간에 맞춰 조정
        yaxis=dict(gridcolor=GRID, fixedrange=True, zeroline=False, side="right"),
    )
    return _to_html(fig, height)


# ---------------------------------------------------------------- 캔들 차트
UP, DOWN = "#1e8e4e", "#c0392b"
MA_COLORS = ["#e0a43a", "#3fa7d6", "#9b7fe6", "#e5604d", "#5cc9a7", "#d17fb5"]


def candle_chart_html(
    df: pd.DataFrame,
    ticker: str,
    show: set,
    ma_periods=(20, 60, 120),
    bb=(20, 2.0),
    rsi_period: int = 14,
    macd_params=(12, 26, 9),
    interval: str = "1d",
) -> str:
    """캔들 + 선택 지표. show: {"거래량", "이동평균선", "볼린저밴드", "RSI", "MACD"}"""
    from plotly.subplots import make_subplots
    import indicators as ind

    close = df["Close"]
    x = df.index.strftime("%Y-%m-%d").tolist()
    r = lambda s: [None if pd.isna(v) else round(float(v), 4) for v in s]

    lower = [k for k in ("거래량", "RSI", "MACD") if k in show]
    weights = [3.2] + [1.0] * len(lower)
    fig = make_subplots(
        rows=1 + len(lower), cols=1, shared_xaxes=True, vertical_spacing=0.025,
        row_heights=[w / sum(weights) for w in weights],
    )

    fig.add_trace(go.Candlestick(
        x=x, open=r(df["Open"]), high=r(df["High"]), low=r(df["Low"]), close=r(close),
        name=ticker, increasing=dict(line=dict(color=UP, width=1), fillcolor=UP),
        decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=DOWN), showlegend=False,
    ), row=1, col=1)

    if "볼린저밴드" in show:
        mid, up, lo = ind.bollinger(close, bb[0], bb[1])
        band = dict(color="rgba(139,147,161,0.7)", width=1)
        fig.add_trace(go.Scatter(x=x, y=r(up), name=f"BB 상단", line=band, hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=r(lo), name=f"BB 하단", line=band, fill="tonexty",
                                 fillcolor="rgba(139,147,161,0.08)", hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=r(mid), name=f"BB 중심({bb[0]})",
                                 line=dict(color="rgba(139,147,161,0.9)", width=1, dash="dot")), row=1, col=1)

    if "이동평균선" in show:
        for i, (p, s) in enumerate(ind.moving_averages(close, ma_periods).items()):
            fig.add_trace(go.Scatter(x=x, y=r(s), name=f"MA{p}",
                                     line=dict(color=MA_COLORS[i % len(MA_COLORS)], width=1.3)), row=1, col=1)

    def panel_title(n, text):
        fig.add_annotation(text=text, xref="paper", yref=f"y{n} domain", x=0.005, y=0.98,
                           xanchor="left", yanchor="top", showarrow=False,
                           bgcolor="rgba(139,147,161,0.15)", borderpad=2,
                           font=dict(size=11, color=TEXT))

    row, fixed = 2, []
    up_day = (close >= df["Open"]).tolist()
    if "거래량" in show:
        fig.add_trace(go.Bar(x=x, y=df["Volume"].astype(float).tolist(), name="거래량",
                             marker=dict(color=[UP if u else DOWN for u in up_day], opacity=0.7),
                             showlegend=False), row=row, col=1)
        panel_title(row, "거래량")
        row += 1
    if "RSI" in show:
        fig.add_trace(go.Scatter(x=x, y=r(ind.rsi(close, rsi_period)), name=f"RSI({rsi_period})",
                                 line=dict(color="#9b7fe6", width=1.3), showlegend=False), row=row, col=1)
        for lvl in (30, 70):
            fig.add_hline(y=lvl, line=dict(color=TEXT, width=1, dash="dot"), row=row, col=1)
        fig.update_yaxes(range=[0, 100], tickvals=[30, 50, 70], tickformat="d", row=row, col=1)
        panel_title(row, f"RSI({rsi_period})")
        fixed.append("yaxis" + ("" if row == 1 else str(row)))
        row += 1
    if "MACD" in show:
        line, sig, osc = ind.macd(close, *macd_params)
        fig.add_trace(go.Bar(x=x, y=r(osc), name="오실레이터", showlegend=False,
                             marker=dict(color=[UP if (v or 0) >= 0 else DOWN for v in r(osc)], opacity=0.75)),
                      row=row, col=1)
        fig.add_trace(go.Scatter(x=x, y=r(line), name="MACD", showlegend=False,
                                 line=dict(color="#3fa7d6", width=1.2)), row=row, col=1)
        fig.add_trace(go.Scatter(x=x, y=r(sig), name="시그널", showlegend=False,
                                 line=dict(color="#e0a43a", width=1.2)), row=row, col=1)
        panel_title(row, f"MACD({macd_params[0]},{macd_params[1]},{macd_params[2]})  파랑 MACD · 주황 시그널 · 막대 오실레이터")

    height = 520 + 140 * len(lower)
    _base_layout(fig, height)
    days = {"1d": 183, "1wk": 365 * 3, "1mo": 365 * 10}[interval]
    end = df.index[-1]
    start = max(df.index[0], end - pd.Timedelta(days=days))
    fig.update_layout(
        hovermode="x unified",
        meta=dict(fixed=fixed),
        legend=dict(orientation="h", x=0.2, xanchor="left", y=1.0, yanchor="bottom", traceorder="normal",
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        bargap=0.15,
    )
    fig.update_xaxes(gridcolor=GRID, rangeslider_visible=False, showspikes=True,
                     spikemode="across", spikethickness=1, spikecolor=TEXT,
                     range=[start.strftime("%Y-%m-%d"), (end + pd.Timedelta(days=2)).strftime("%Y-%m-%d")])
    fig.update_xaxes(rangeselector=_range_buttons(), row=1, col=1)
    fig.update_yaxes(gridcolor=GRID, fixedrange=True, zeroline=False, side="right",
                     hoverformat=",.2f")
    if interval == "1d":
        # 주말과 휴장일 공백 제거
        all_days = pd.bdate_range(df.index[0], df.index[-1])
        holidays = all_days.difference(df.index).strftime("%Y-%m-%d").tolist()
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(values=holidays)])
    return _to_html(fig, height), height


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
.cell{cursor:pointer}.cell:hover{outline:2px solid #fff;outline-offset:-2px;z-index:2}
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
        tip.innerHTML = `<b>${d.t}</b> ${d.n}<br>${d.s}<br>등락률 ${fmtPct(d.r)}<br>시가총액 ${fmtCap(d.c)}<br><span style="opacity:.6">클릭하면 종목 분석을 엽니다</span>`;
        const x = e.clientX + 14, y = e.clientY + 14;
        tip.style.left = Math.min(x, window.innerWidth - tip.offsetWidth - 6) + "px";
        tip.style.top = Math.min(y, window.innerHeight - tip.offsetHeight - 6) + "px";
      };
      c.onmouseleave = () => { tip.style.display = "none"; };
      c.onclick = () => {
        try { window.open(window.parent.location.origin + "/stock?ticker=" + encodeURIComponent(d.t), "_blank"); } catch (e) {}
      };
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


# ---------------------------------------------------------------- 섹터 흐름
SECTOR_COLORS = {
    "XLK": "#3f7be0", "XLC": "#9b7fe6", "XLY": "#e5604d", "XLF": "#1e8e4e", "XLV": "#5cc9a7",
    "XLI": "#e0a43a", "XLE": "#8d6e4f", "XLB": "#d17fb5", "XLP": "#7a9cc6", "XLU": "#b5b84a",
    "XLRE": "#c98b5e",
}


def sector_chart(pct: pd.DataFrame, names: dict, n_lead: int = 3, height: int = 460) -> go.Figure:
    """기준일 0% 대비 섹터 ETF 등락률을 겹쳐 그린다. 상위 n_lead개(주도 섹터)는 굵고 진하게."""
    last = pct.iloc[-1].dropna().sort_values(ascending=False)
    leaders = set(last.index[:n_lead])
    x = pct.index.strftime("%Y-%m-%d").tolist()
    fig = go.Figure()

    # 주도 섹터를 마지막에 그려 다른 선 위에 오게 하고, 호버 목록은 등락률 순서로
    order = [t for t in last.index if t not in leaders][::-1] + [t for t in last.index if t in leaders][::-1]
    for t in order:
        lead = t in leaders
        label = f"{names.get(t, t)}({t})"
        fig.add_trace(go.Scatter(
            x=x, y=[round(float(v), 2) for v in pct[t].values], mode="lines", name=label,
            line=dict(color=SECTOR_COLORS.get(t, TEXT), width=3.2 if lead else 1.4),
            opacity=1.0 if lead else 0.45,
            hovertemplate=f"{label} %{{y:+.2f}}%<extra></extra>",
            legendrank=list(last.index).index(t),
        ))

    # 선 끝 라벨: 겹치지 않게 위아래로 벌려서 배치
    span = max(1e-6, float(pct.max().max() - pct.min().min()))
    gap = span * 0.055
    ys = []
    for t in last.index:  # 위에서부터
        y = float(last[t])
        if ys and ys[-1][1] - y < gap:
            y = ys[-1][1] - gap
        ys.append((t, y))
    for t, y in ys:
        lead = t in leaders
        fig.add_annotation(
            x=x[-1], y=y, xanchor="left", yanchor="middle", showarrow=False, xshift=6,
            text=f"{'<b>' if lead else ''}{names.get(t, t)}({t}) {last[t]:+.1f}%{'</b>' if lead else ''}",
            font=dict(size=12 if lead else 11, color=SECTOR_COLORS.get(t, TEXT)),
            opacity=1.0 if lead else 0.75,
        )

    lo = min(float(pct.min().min()), min(y for _, y in ys))
    hi = max(float(pct.max().max()), max(y for _, y in ys))
    pad = (hi - lo) * 0.05 or 1
    fig.add_hline(y=0, line=dict(color=TEXT, width=1, dash="dot"))
    fig.update_layout(
        height=height,
        margin=dict(l=52, r=215, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=11),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(gridcolor=GRID, showspikes=True, spikemode="across", spikethickness=1, spikecolor=TEXT,
                   range=[x[0], x[-1]], fixedrange=True),
        yaxis=dict(gridcolor=GRID, ticksuffix="%", zeroline=False, side="left", range=[lo - pad, hi + pad],
                   fixedrange=True),
    )
    return fig
