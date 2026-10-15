/* Pharmaceutical Commercial Analytics — interactive dashboard (vanilla JS + SVG)
   Data: window.PHARMA (data.js) — real Kaggle POS volumes; EUR derived from the
   documented price/margin assumptions. No external libraries, no network calls. */
(function () {
  "use strict";
  var D = window.PHARMA;
  if (!D) return;

  var CAT = D.cats, NC = CAT.length;
  var DATES = D.dates, YEARS = D.years, DOWS = D.dows;
  var WDNAMES = D.weekDays, ND = DATES.length;
  var MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var YEARPAL = ["#bcd9e8", "#9dc3e6", "#6fa8dc", "#4a93c4", "#2e8b9a", "#1f6e7d"];
  var CATPAL = ["#2e8b9a", "#1f6e7d", "#4fa6b4", "#78bfc9", "#1f3864",
                "#a3d4db", "#c7e5ea", "#8fc4ce"];

  var state = { page: "overview", year: "", cat: "", dow: "", metric: "rev" };

  var M = {
    rev:    { label: "Est. Revenue",      fmt: eur,  val: function (u, c) { return u * CAT[c].price; } },
    profit: { label: "Est. Gross Profit", fmt: eur,  val: function (u, c) { return u * CAT[c].price * CAT[c].margin; } },
    units:  { label: "Units Sold",        fmt: ufmt, val: function (u) { return u; } }
  };

  /* ------------------------------------------------------------ formatters */
  function eur(v) {
    v = Math.round(Math.abs(v));
    var s = v >= 1e6 ? (v / 1e6).toFixed(2) + "M"
          : v >= 1e3 ? (v / 1e3).toFixed(2) + "K" : String(v);
    return "\u20AC" + s;
  }
  function gridFmt(v) {
    return v === 0 ? "0"
         : Math.abs(v) >= 1e6 ? (v / 1e6).toFixed(1) + "M"
         : Math.abs(v) >= 1e3 ? Math.round(v / 1e3) + "K" : String(Math.round(v));
  }
  function seur(v) { return v < 0 ? "\u2212" + eur(v) : "+" + eur(v); }
  function ufmt(v) {
    return v >= 1e6 ? (v / 1e6).toFixed(1) + "M"
         : v >= 1e4 ? (v / 1e3).toFixed(1) + "K"
         : Math.round(v).toLocaleString("en-US");
  }
  function pct(v) { return (v * 100).toFixed(1) + "%"; }
  function spct(v) { return (v < 0 ? "\u2212" : "+") + Math.abs(v * 100).toFixed(1) + "%"; }
  function int(v) { return Math.round(v).toLocaleString("en-US"); }
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    return e;
  }
  function NS(tag, attrs, txt) {
    var e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (txt !== undefined) e.textContent = txt;
    return e;
  }
  function titleOf(node, t) { node.appendChild(NS("title", {}, t)); return node; }

  /* ------------------------------------------------------------ compute */
  var R; // computed aggregates for current filter state

  function compute() {
    var catSel = state.cat ? CAT.findIndex(function (c) { return c.name === state.cat; }) : -1;
    var yearSel = state.year === "" ? null : +state.year;
    var dowSel = state.dow === "" ? null : +state.dow;

    var tot = { rev: 0, profit: 0, units: 0 };
    var byCatAll = [];   // year+weekday filter only (tables always show all categories)
    var i;
    for (i = 0; i < NC; i++) byCatAll.push({ rev: 0, profit: 0, units: 0 });
    var byYear = {}, byDow = [], monthTot = [], monthSet = [], ym = {};
    for (i = 0; i < 7; i++) byDow.push({ rev: 0, profit: 0, units: 0 });
    for (i = 0; i < 12; i++) { monthTot.push(0); monthSet.push({}); }
    var maxD = -1, daySet = {}, rows = D.rows, nRows = rows.length;

    for (i = 0; i < nRows; i++) {
      var r = rows[i], d = r[0], c = r[1], u = r[2];
      if (yearSel !== null && YEARS[d] !== yearSel) continue;
      if (dowSel !== null && DOWS[d] !== dowSel) continue;
      var rev = u * CAT[c].price, prof = rev * CAT[c].margin;
      var a = byCatAll[c];
      a.rev += rev; a.profit += prof; a.units += u;
      if (catSel !== -1 && c !== catSel) continue;
      tot.rev += rev; tot.profit += prof; tot.units += u;
      var y = YEARS[d];
      if (!byYear[y]) byYear[y] = { rev: 0, profit: 0, units: 0 };
      byYear[y].rev += rev; byYear[y].profit += prof; byYear[y].units += u;
      var wd = DOWS[d];
      byDow[wd].rev += rev; byDow[wd].profit += prof; byDow[wd].units += u;
      var m = +DATES[d].slice(5, 7);
      monthTot[m - 1] += rev; monthSet[m - 1][y] = 1;
      var ymKey = y + "-" + (m < 10 ? "0" + m : m);
      ym[ymKey] = (ym[ymKey] || 0) + rev;
      if (d > maxD) maxD = d;
      daySet[d] = 1;
    }

    // focus year / like-for-like windows (partial-year aware)
    var maxDate = maxD >= 0 ? DATES[maxD] : DATES[ND - 1];
    var focus = yearSel !== null ? yearSel : +maxDate.slice(0, 4);
    var prior = focus - 1;
    var winEnd = maxDate;                                   // e.g. 2019-10-08
    var priStart = prior + "-01-01";
    var priEnd = prior + winEnd.slice(4);                   // same window, year before
    var curStart = focus + "-01-01";

    // pass B: like-for-like sums + per-category LFL + trend months (no year/cat filter on catLFL)
    var cur = { rev: 0, profit: 0, units: 0 }, pri = { rev: 0, profit: 0, units: 0 };
    var catCur = [], catPri = [];
    for (i = 0; i < NC; i++) { catCur.push(0); catPri.push(0); }
    var trend = {};
    trend[focus] = []; trend[prior] = [];
    for (i = 0; i < 12; i++) { trend[focus].push(0); trend[prior].push(0); }

    for (i = 0; i < nRows; i++) {
      var r2 = rows[i], d2 = r2[0], c2 = r2[1], u2 = r2[2];
      if (dowSel !== null && DOWS[d2] !== dowSel) continue;
      var ds = DATES[d2], rev2 = u2 * CAT[c2].price, prof2 = rev2 * CAT[c2].margin;
      var inCur = ds >= curStart && ds <= winEnd;
      var inPri = ds >= priStart && ds <= priEnd;
      if (inCur) catCur[c2] += rev2;
      if (inPri) catPri[c2] += rev2;
      if (catSel !== -1 && c2 !== catSel) continue;
      if (inCur) { cur.rev += rev2; cur.profit += prof2; cur.units += u2; }
      if (inPri) { pri.rev += rev2; pri.profit += prof2; pri.units += u2; }
      var yy = YEARS[d2];
      if (yy === focus || yy === prior) {
        trend[yy][+ds.slice(5, 7) - 1] += rev2;
      }
    }

    // seasonality index (revenue, average per occurrence of each month)
    var mCount = [], countAll = 0;
    for (i = 0; i < 12; i++) { mCount.push(Object.keys(monthSet[i]).length); countAll += mCount[i]; }
    var avgMonth = countAll ? tot.rev / countAll : 0;
    var season = [];
    for (i = 0; i < 12; i++) {
      season.push(avgMonth && mCount[i] ? (monthTot[i] / mCount[i]) / avgMonth : 0);
    }

    // quarters for focus/prior from trend months
    function qsum(arr) {
      return [arr[0] + arr[1] + arr[2], arr[3] + arr[4] + arr[5],
              arr[6] + arr[7] + arr[8], arr[9] + arr[10] + arr[11]];
    }
    var hasPrior = pri.rev > 0;

    R = {
      tot: tot, byCatAll: byCatAll, byYear: byYear, byDow: byDow,
      monthTot: monthTot, season: season, ym: ym, maxDate: maxDate,
      days: Object.keys(daySet).length,
      focus: focus, prior: prior, winEnd: winEnd, hasPrior: hasPrior,
      cur: cur, pri: pri, catCur: catCur, catPri: catPri,
      trend: trend, qFocus: qsum(trend[focus]), qPrior: qsum(trend[prior]),
      catSel: catSel, yearSel: yearSel, dowSel: dowSel,
      lfl: hasPrior ? { rev: cur.rev / pri.rev - 1,
                        profit: cur.profit / pri.profit - 1,
                        units: cur.units / pri.units - 1 } : null,
      margLfl: (cur.rev && pri.rev)
        ? (cur.profit / cur.rev - pri.profit / pri.rev) * 100 : null
    };
  }

  /* ------------------------------------------------------------ chart helpers */
  function svgHost(host) {
    host.innerHTML = "";
    var w = Math.max(host.clientWidth || 320, 240);
    var h = Math.max(host.clientHeight || 260, 160);
    var s = NS("svg", { viewBox: "0 0 " + w + " " + h, width: "100%",
                        height: "100%", preserveAspectRatio: "xMidYMid meet" });
    host.appendChild(s);
    return { s: s, w: w, h: h };
  }
  function empty(host, msg) {
    host.innerHTML = "";
    var d = el("div", "muted", msg || "No data for this selection");
    d.style.cssText = "display:flex;height:100%;align-items:center;justify-content:center;";
    host.appendChild(d);
  }
  function niceMax(v) {
    if (v <= 0) return 1;
    var step = Math.pow(10, Math.floor(Math.log10(v / 4)));
    [1, 2, 2.5, 5, 10].some(function (m) { if (step * m >= v / 4) { step *= m; return true; } return false; });
    return step * 4;
  }
  function legend(s, w, items, y) {
    var x = w - 8;
    for (var i = items.length - 1; i >= 0; i--) {
      var t = NS("text", { "font-size": 10.5, fill: "#5a7684",
                           "text-anchor": "end", y: y }, items[i].label);
      s.appendChild(t);
      var tw = (items[i].label.length + 1) * 6.2;
      x -= tw;
      s.appendChild(NS("rect", { x: x + 4, y: y - 8, width: 9, height: 9, rx: 2,
                                 fill: items[i].color }));
      x -= 18;
    }
  }

  /* horizontal bars (categories / weekdays) */
  function hbar(host, items, opts) {
    opts = opts || {};
    if (!items.length) return empty(host);
    var g = svgHost(host), s = g.s;
    var L = opts.labelW || 116, Rm = 62, T = 4, B = 4;
    var plotW = g.w - L - Rm, rowH = (g.h - T - B) / items.length;
    var barH = Math.min(Math.max(rowH * 0.6, 10), 22);
    var max = Math.max.apply(null, items.map(function (d) { return d.value; })) || 1;
    items.forEach(function (d, i) {
      var y = T + i * rowH + rowH / 2;
      s.appendChild(NS("text", { x: L - 8, y: y + 3.5, "text-anchor": "end",
        "font-size": 11.5, fill: d.selected ? "#1f3864" : "#4b5b68",
        "font-weight": d.selected ? 700 : 400 }, d.label));
      s.appendChild(NS("rect", { x: L, y: y - barH / 2, width: plotW, height: barH,
                                 rx: 3, fill: "#f2f7f9" }));
      var bw = Math.max((d.value / max) * plotW, d.value > 0 ? 2 : 0);
      var bar = NS("rect", { x: L, y: y - barH / 2, width: bw, height: barH, rx: 3,
        fill: d.color || "#2e8b9a", cursor: opts.onClick ? "pointer" : "default" });
      if (d.selected) { bar.setAttribute("stroke", "#1f3864"); bar.setAttribute("stroke-width", 1.5); }
      titleOf(bar, d.label + " \u2014 " + (opts.vfmt || eur)(d.value));
      if (opts.onClick) bar.addEventListener("click", function () { opts.onClick(d.key); });
      s.appendChild(bar);
      s.appendChild(NS("text", { x: L + bw + 6, y: y + 3.5, "font-size": 10.5,
        "font-weight": 700, fill: "#33445a",
        cursor: opts.onClick ? "pointer" : "default" }, (opts.vfmt || eur)(d.value)));
    });
  }

  /* grouped vertical bars with optional value labels / reference line */
  function vbars(host, labels, series, opts) {
    opts = opts || {};
    var total = series.reduce(function (a, se) { return a + se.values.length; }, 0);
    if (!total) return empty(host);
    var g = svgHost(host), s = g.s;
    var L = 52, Rm = 10, T = opts.vlabels ? 24 : 14, B = 26;
    var plotW = g.w - L - Rm, plotH = g.h - T - B;
    var all = [];
    series.forEach(function (se) { se.values.forEach(function (v) { all.push(v); }); });
    if (opts.refLine !== undefined) all.push(opts.refLine);
    var yMax = niceMax(Math.max.apply(null, all) * 1.08);
    var yv = function (v) { return T + plotH - (v / yMax) * plotH; };
    // gridlines
    for (var i = 0; i <= 4; i++) {
      var gv = yMax * i / 4, gy = yv(gv);
      s.appendChild(NS("line", { x1: L, y1: gy, x2: g.w - Rm, y2: gy,
                                 stroke: "#edf2f5", "stroke-width": 1 }));
      s.appendChild(NS("text", { x: L - 6, y: gy + 3, "text-anchor": "end",
        "font-size": 9.5, fill: "#8aa2ae" }, (opts.yfmt || gridFmt)(gv)));
    }
    var n = labels.length, groupW = plotW / n;
    var barW = Math.min(groupW * 0.62 / series.length, 30);
    labels.forEach(function (lab, li) {
      var gx = L + li * groupW;
      var gx0 = gx + (groupW - barW * series.length) / 2;
      series.forEach(function (se, si) {
        var v = se.values[li];
        var x = gx0 + si * barW;
        var y = yv(v), h0 = T + plotH - y;
        var col = (se.colors && se.colors[li]) || se.color;
        var bar = NS("rect", { x: x + 1, y: y, width: barW - 2, height: Math.max(h0, 0.5),
          rx: 2, fill: col, cursor: opts.onClick ? "pointer" : "default" });
        titleOf(bar, lab + (se.name ? " \u00b7 " + se.name : "") + " \u2014 " +
                     (opts.vfmt || eur)(v));
        if (opts.onClick) bar.addEventListener("click", function () { opts.onClick(li); });
        s.appendChild(bar);
        if (opts.vlabels && series.length <= 2) {
          s.appendChild(NS("text", { x: x + barW / 2, y: y - 5, "text-anchor": "middle",
            "font-size": 9, "font-weight": 700, fill: "#5a7684",
            cursor: opts.onClick ? "pointer" : "default" },
            (opts.vfmt || eur)(v)));
        }
      });
      s.appendChild(NS("text", { x: gx + groupW / 2, y: g.h - 9, "text-anchor": "middle",
        "font-size": 10.5, fill: "#4b5b68" }, lab));
    });
    if (opts.refLine !== undefined) {
      var ry = yv(opts.refLine);
      s.appendChild(NS("line", { x1: L, y1: ry, x2: g.w - Rm, y2: ry,
        stroke: "#8fa3ad", "stroke-width": 1.2, "stroke-dasharray": "4 3" }));
      s.appendChild(NS("text", { x: g.w - Rm, y: ry - 4, "text-anchor": "end",
        "font-size": 9.5, fill: "#7d8f99" }, opts.refLabel || ""));
    }
    if (series.length > 1 && legend) {
      legend(s, g.w, series.map(function (se) { return { label: se.name, color: se.color }; }), 10);
    }
  }

  /* donut with right-hand legend */
  function donut(host, slices, opts) {
    opts = opts || {};
    var vals = slices.filter(function (d) { return d.value > 0; });
    if (!vals.length) return empty(host);
    var g = svgHost(host), s = g.s;
    var total = vals.reduce(function (a, d) { return a + d.value; }, 0);
    var cx = Math.min(g.w * 0.30, g.h / 2 + 10), cy = g.h / 2;
    var rad = Math.min(g.h - 36, g.w * 0.52) / 2;
    var inner = rad * 0.62, ang = -Math.PI / 2, gap = 0.022;
    vals.forEach(function (d) {
      var a0 = ang, a1 = ang + (d.value / total) * Math.PI * 2;
      ang = a1;
      var big = (a1 - a0) > Math.PI ? 1 : 0;
      var p0x = cx + rad * Math.cos(a0 + gap / 2), p0y = cy + rad * Math.sin(a0 + gap / 2);
      var p1x = cx + rad * Math.cos(a1 - gap / 2), p1y = cy + rad * Math.sin(a1 - gap / 2);
      var q1x = cx + inner * Math.cos(a1 - gap / 2), q1y = cy + inner * Math.sin(a1 - gap / 2);
      var q0x = cx + inner * Math.cos(a0 + gap / 2), q0y = cy + inner * Math.sin(a0 + gap / 2);
      var path = NS("path", { d: "M" + p0x + " " + p0y +
        "A" + rad + " " + rad + " 0 " + big + " 1 " + p1x + " " + p1y +
        "L" + q1x + " " + q1y +
        "A" + inner + " " + inner + " 0 " + big + " 0 " + q0x + " " + q0y + "Z",
        fill: d.color, stroke: "#fff", "stroke-width": 1.5,
        cursor: opts.onClick ? "pointer" : "default" });
      titleOf(path, d.label + " \u2014 " + eur(d.value) + " (" + pct(d.value / total) + ")");
      if (opts.onClick) path.addEventListener("click", function () { opts.onClick(d.key); });
      s.appendChild(path);
    });
    s.appendChild(NS("text", { x: cx, y: cy - 2, "text-anchor": "middle",
      "font-size": 15, "font-weight": 700, fill: "#1f3864" },
      opts.centerValue || eur(total)));
    s.appendChild(NS("text", { x: cx, y: cy + 14, "text-anchor": "middle",
      "font-size": 9.5, fill: "#8aa2ae" }, opts.centerLabel || "total"));
    // legend rows
    var lx = cx + rad + 22, ly = 18;
    vals.forEach(function (d) {
      s.appendChild(NS("rect", { x: lx, y: ly - 9, width: 10, height: 10, rx: 2, fill: d.color }));
      s.appendChild(NS("text", { x: lx + 16, y: ly, "font-size": 11, fill: "#4b5b68" }, d.label));
      s.appendChild(NS("text", { x: g.w - 6, y: ly, "text-anchor": "end", "font-size": 11,
        "font-weight": 700, fill: "#33445a" }, eur(d.value)));
      s.appendChild(NS("text", { x: g.w - 6, y: ly + 12, "text-anchor": "end", "font-size": 9.5,
        fill: "#8aa2ae" }, pct(d.value / total)));
      ly += 28;
    });
  }

  /* year-vs-year monthly line with variance labels (reference signature chart) */
  function lineTrend(host, months, A, B, opts) {
    opts = opts || {};
    var g = svgHost(host), s = g.s;
    var L = 50, Rm = 12, T = 40, Bm = 24;
    var plotW = g.w - L - Rm, plotH = g.h - T - Bm;
    var all = B.slice();
    if (A) all = all.concat(A);
    var lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var pad = (hi - lo) * 0.18 || hi * 0.1 || 1;
    lo = Math.max(0, lo - pad); hi = hi + pad;
    var xv = function (i) { return L + (plotW / 12) * (i + 0.5); };
    var yv = function (v) { return T + plotH - ((v - lo) / (hi - lo)) * plotH; };
    for (var i = 0; i <= 4; i++) {
      var gv = lo + (hi - lo) * i / 4, gy = yv(gv);
      s.appendChild(NS("line", { x1: L, y1: gy, x2: g.w - Rm, y2: gy,
                                 stroke: "#edf2f5", "stroke-width": 1 }));
      s.appendChild(NS("text", { x: L - 6, y: gy + 3, "text-anchor": "end",
        "font-size": 9.5, fill: "#8aa2ae" }, gridFmt(gv)));
    }
    // average reference line
    var avg = opts.avg || 0;
    if (avg > lo && avg < hi) {
      var ay = yv(avg);
      s.appendChild(NS("line", { x1: L, y1: ay, x2: g.w - Rm, y2: ay,
        stroke: "#b9c4cc", "stroke-width": 1.2, "stroke-dasharray": "3 3" }));
      s.appendChild(NS("text", { x: L + 4, y: ay - 4, "font-size": 9.5, fill: "#7d8f99" },
        "Avg: " + eur(avg)));
    }
    // prior-year dashed line + stems + variance labels
    if (A) {
      s.appendChild(NS("polyline", { points: A.map(function (v, i) { return xv(i) + "," + yv(v); }).join(" "),
        fill: "none", stroke: "#9dc3e6", "stroke-width": 2, "stroke-dasharray": "5 4" }));
      A.forEach(function (v, i) {
        s.appendChild(NS("circle", { cx: xv(i), cy: yv(v), r: 2.6,
                                     fill: "#fff", stroke: "#9dc3e6", "stroke-width": 1.5 }));
      });
    }
    B.forEach(function (v, i) {
      var x = xv(i);
      if (A) {
        var up = v >= A[i];
        s.appendChild(NS("line", { x1: x, y1: yv(A[i]), x2: x, y2: yv(v),
          stroke: up ? "#1e9e5a" : "#c0392b", "stroke-width": 5, opacity: 0.14 }));
        var lbl = seur(v - A[i]);
        var ly = yv(v) - 9;
        if (ly < T + 8) ly = yv(v) + 16;
        s.appendChild(NS("text", { x: x, y: ly, "text-anchor": "middle", "font-size": 9.5,
          "font-weight": 700, fill: up ? "#1e9e5a" : "#c0392b" }, lbl));
      }
    });
    // current-year solid line
    s.appendChild(NS("polyline", { points: B.map(function (v, i) { return xv(i) + "," + yv(v); }).join(" "),
      fill: "none", stroke: "#2e8b9a", "stroke-width": 2.4 }));
    B.forEach(function (v, i) {
      var c = NS("circle", { cx: xv(i), cy: yv(v), r: 3.4, fill: "#fff",
                             stroke: "#2e8b9a", "stroke-width": 2 });
      titleOf(c, months[i] + " " + eur(v) + (A ? "  (prior " + eur(A[i]) + ")" : ""));
      s.appendChild(c);
      s.appendChild(NS("text", { x: xv(i), y: g.h - 8, "text-anchor": "middle",
        "font-size": 10.5, fill: "#4b5b68" }, months[i]));
    });
    var lg = [{ label: String(opts.focus) + (opts.focusPartial ? " (partial)" : ""), color: "#2e8b9a" }];
    if (A) lg.unshift({ label: String(opts.prior), color: "#9dc3e6" });
    legend(s, g.w, lg, 12);
  }

  /* long 72-month line with area */
  function lineLong(host, labels, values) {
    var g = svgHost(host), s = g.s;
    var L = 50, Rm = 12, T = 14, Bm = 24;
    var plotW = g.w - L - Rm, plotH = g.h - T - Bm;
    var hi = niceMax(Math.max.apply(null, values) * 1.06) || 1;
    var xv = function (i) { return L + (plotW / (values.length - 1)) * i; };
    var yv = function (v) { return T + plotH - (v / hi) * plotH; };
    for (var i = 0; i <= 4; i++) {
      var gv = hi * i / 4, gy = yv(gv);
      s.appendChild(NS("line", { x1: L, y1: gy, x2: g.w - Rm, y2: gy,
                                 stroke: "#edf2f5", "stroke-width": 1 }));
      s.appendChild(NS("text", { x: L - 6, y: gy + 3, "text-anchor": "end",
        "font-size": 9.5, fill: "#8aa2ae" }, gridFmt(gv)));
    }
    var pts = values.map(function (v, i) { return xv(i) + "," + yv(v); }).join(" ");
    s.appendChild(NS("polygon", { points: L + "," + (T + plotH) + " " + pts + " " +
      xv(values.length - 1) + "," + (T + plotH), fill: "rgba(46,139,154,.12)" }));
    s.appendChild(NS("polyline", { points: pts, fill: "none", stroke: "#2e8b9a",
                                   "stroke-width": 1.8 }));
    var avg = values.reduce(function (a, b) { return a + b; }, 0) / values.length;
    var ay = yv(avg);
    s.appendChild(NS("line", { x1: L, y1: ay, x2: g.w - Rm, y2: ay, stroke: "#b9c4cc",
      "stroke-width": 1.1, "stroke-dasharray": "3 3" }));
    s.appendChild(NS("text", { x: L + 4, y: ay - 4, "font-size": 9, fill: "#7d8f99" },
      "Avg: " + eur(avg)));
    // year bands + hover targets
    var lastYear = "";
    labels.forEach(function (lab, i) {
      var y = lab.slice(0, 4);
      if (y !== lastYear) {
        lastYear = y;
        if (i > 0) s.appendChild(NS("line", { x1: xv(i), y1: T, x2: xv(i), y2: T + plotH,
          stroke: "#dfe9ee", "stroke-width": 1 }));
        s.appendChild(NS("text", { x: xv(i) + 2, y: g.h - 8, "font-size": 10,
                                   fill: "#5a7684", "font-weight": 700 }, y));
      }
      var hit = NS("rect", { x: xv(i) - plotW / (values.length * 2), y: T,
        width: plotW / values.length, height: plotH, fill: "transparent" });
      titleOf(hit, lab + " \u2014 " + eur(values[i]));
      s.appendChild(hit);
    });
  }

  /* diverging bars (LFL growth) */
  function divBar(host, items, onClick) {
    var vals = items.filter(function (d) { return d.value !== null; });
    if (!vals.length) return empty(host);
    var g = svgHost(host), s = g.s;
    var L = 116, Rm = 54, T = 4, B = 4;
    var plotW = g.w - L - Rm, rowH = (g.h - T - B) / items.length;
    var barH = Math.min(Math.max(rowH * 0.6, 10), 20);
    var mags = vals.map(function (d) { return Math.abs(d.value); });
    var max = Math.max.apply(null, mags) || 0.01;
    var zero = L + plotW / 2; // center
    s.appendChild(NS("line", { x1: zero, y1: T, x2: zero, y2: g.h - B,
                               stroke: "#c9dce4", "stroke-width": 1 }));
    items.forEach(function (d, i) {
      var y = T + i * rowH + rowH / 2;
      s.appendChild(NS("text", { x: L - 8, y: y + 3.5, "text-anchor": "end", "font-size": 11.5,
        fill: d.selected ? "#1f3864" : "#4b5b68",
        "font-weight": d.selected ? 700 : 400 }, d.label));
      if (d.value === null) {
        s.appendChild(NS("text", { x: zero + 6, y: y + 3.5, "font-size": 10.5,
                                   fill: "#8aa2ae" }, "no prior data"));
        return;
      }
      var bw = (Math.abs(d.value) / max) * (plotW / 2);
      var up = d.value >= 0;
      var bar = NS("rect", { x: up ? zero : zero - bw, y: y - barH / 2,
        width: Math.max(bw, 1), height: barH, rx: 3,
        fill: up ? "#1e9e5a" : "#c0392b", opacity: d.selected ? 1 : 0.82,
        cursor: onClick ? "pointer" : "default" });
      titleOf(bar, d.label + " \u2014 " + spct(d.value) + " like-for-like");
      if (onClick) bar.addEventListener("click", function () { onClick(d.key); });
      s.appendChild(bar);
      s.appendChild(NS("text", { x: up ? zero + bw + 6 : zero - bw - 6, y: y + 3.5,
        "text-anchor": up ? "start" : "end", "font-size": 10.5, "font-weight": 700,
        fill: up ? "#1e9e5a" : "#c0392b" }, spct(d.value)));
    });
  }

  /* two-bar share comparison (units vs revenue) */
  function shareBars(host, items) {
    if (!items.length) return empty(host);
    var g = svgHost(host), s = g.s;
    var L = 116, Rm = 44, T = 22, B = 4;
    var plotW = g.w - L - Rm, rowH = (g.h - T - B) / items.length;
    var barH = Math.min(rowH * 0.30, 9);
    var max = 0;
    items.forEach(function (d) { max = Math.max(max, d.a, d.b); });
    max = max || 1;
    legend(s, g.w, [{ label: "units share", color: "#9dc3e6" },
                    { label: "revenue share", color: "#2e8b9a" }], 12);
    items.forEach(function (d, i) {
      var y = T + i * rowH + rowH / 2;
      s.appendChild(NS("text", { x: L - 8, y: y + 3.5, "text-anchor": "end", "font-size": 11,
        fill: d.selected ? "#1f3864" : "#4b5b68",
        "font-weight": d.selected ? 700 : 400 }, d.label));
      var w1 = (d.a / max) * plotW, w2 = (d.b / max) * plotW;
      s.appendChild(NS("rect", { x: L, y: y - barH - 1.5, width: Math.max(w1, 1),
                                 height: barH, rx: 2, fill: "#9dc3e6" }));
      s.appendChild(NS("text", { x: L + w1 + 5, y: y - 2, "font-size": 9, fill: "#7d8f99" }, pct(d.a)));
      s.appendChild(NS("rect", { x: L, y: y + 1.5, width: Math.max(w2, 1),
                                 height: barH, rx: 2, fill: "#2e8b9a" }));
      s.appendChild(NS("text", { x: L + w2 + 5, y: y + 10, "font-size": 9, "font-weight": 700,
                                 fill: "#33445a" }, pct(d.b)));
    });
  }

  /* table builder */
  function table(host, headers, rows) {
    host.innerHTML = "";
    var t = el("table"), thead = el("thead"), tr = el("tr");
    headers.forEach(function (h) { tr.appendChild(el("th", null, h)); });
    thead.appendChild(tr); t.appendChild(thead);
    var tb = el("tbody");
    rows.forEach(function (row) {
      var r = el("tr", row.cls || "");
      row.cells.forEach(function (c) {
        var td = el("td", c.cls || "");
        if (c.html !== undefined) td.innerHTML = c.html; else td.textContent = c.v;
        if (c.grad !== undefined) {
          td.classList.add("bar-cell");
          td.style.backgroundImage = "linear-gradient(90deg,#dceef3 " + c.grad + "%,rgba(0,0,0,0) 0)";
        }
        r.appendChild(td);
      });
      if (row.onClick) r.addEventListener("click", row.onClick);
      tb.appendChild(r);
    });
    t.appendChild(tb);
    host.appendChild(t);
  }

  /* ------------------------------------------------------------ heatmap */
  var heatBuilt = false;
  function renderHeatmap() {
    if (heatBuilt) return;
    heatBuilt = true;
    var host = $("heatmap");
    host.innerHTML = "";
    var grid = el("div", "hm-grid");
    grid.appendChild(el("div"));
    D.hours.forEach(function (h) { grid.appendChild(el("div", "hm-h", h % 2 === 0 ? String(h) : "")); });
    var max = 0;
    D.hourAvg.forEach(function (row) { row.forEach(function (v) { max = Math.max(max, v); }); });
    max = max || 1;
    D.weekDays.forEach(function (wd, w) {
      grid.appendChild(el("div", "hm-r", wd));
      D.hourAvg[w].forEach(function (v, h) {
        var t = v / max;
        var c = el("div", "hm-cell",
                   v >= 0.5 ? v.toFixed(1) : "");
        var rr = Math.round(255 + (46 - 255) * t);
        var gg = Math.round(255 + (139 - 255) * t);
        var bb = Math.round(255 + (154 - 255) * t);
        c.style.background = "rgb(" + rr + "," + gg + "," + bb + ")";
        c.style.color = t > 0.55 ? "#fff" : "#33445a";
        c.title = wd + " " + h + ":00 \u2014 avg " + v.toFixed(1) + " units";
        grid.appendChild(c);
      });
    });
    host.appendChild(grid);
    var lgd = el("div", "hm-legend");
    lgd.appendChild(el("span", null, "0"));
    lgd.appendChild(el("div", "hm-ramp"));
    lgd.appendChild(el("span", null, max.toFixed(1) + " avg units / hour"));
    lgd.appendChild(el("span", null, "\u00b7 peak \u2192 evening, Saturday"));
    host.appendChild(lgd);
  }

  /* ------------------------------------------------------------ KPI cards */
  function setChip(id, val, ctxId, ctxText, fmt) {
    var chip = $(id);
    chip.className = "chip" + (val === null ? "" : val >= 0 ? " up" : " down");
    chip.textContent = val === null ? "\u2014" : (fmt || spct)(val);
    chip.title = val === null ? "No comparable prior period"
      : "Like-for-like: 1 Jan\u2013" + R.winEnd.slice(8) + " vs same period of " + R.prior;
    $(ctxId).textContent = ctxText;
  }
  function renderKPIs() {
    $("kRev").textContent = eur(R.tot.rev);
    $("kProf").textContent = eur(R.tot.profit);
    $("kMarg").textContent = R.tot.rev ? pct(R.tot.profit / R.tot.rev) : "\u2014";
    $("kUnits").textContent = ufmt(R.tot.units);
    var winLabel = !R.hasPrior ? "no prior year \u2014 baseline"
      : R.winEnd.slice(5, 7) === "12" ? "vs " + R.prior + " \u00b7 full year"
      : "LFL vs " + R.prior + " (1 Jan\u2013" + (+R.winEnd.slice(8)) + " " +
        MN[+R.winEnd.slice(5, 7) - 1] + ")";
    setChip("kRevChip", R.lfl ? R.lfl.rev : null, "kRevCtx", winLabel);
    setChip("kProfChip", R.lfl ? R.lfl.profit : null, "kProfCtx", "est. from assumed margins");
    setChip("kMargChip", R.margLfl, "kMargCtx", "blended assumed category rates",
      function (v) { return (v < 0 ? "\u2212" : "+") + Math.abs(v).toFixed(1) + " pp"; });
    setChip("kUnitsChip", R.lfl ? R.lfl.units : null, "kUnitsCtx",
      R.days ? "avg " + int(R.tot.units / R.days) + " / trading day" : "");
  }

  /* ------------------------------------------------------------ pages */
  function catItems(field) {
    return CAT.map(function (c, i) {
      return { label: c.name, key: c.name, value: R.byCatAll[i][field],
               selected: state.cat === c.name,
               color: state.cat === c.name ? "#1f3864" : undefined };
    }).sort(function (a, b) { return b.value - a.value; });
  }

  function renderOverview() {
    var mk = state.metric, mf = M[mk];
    $("ovCatTitle").textContent = mf.label + " by Category";
    $("ovYearTitle").innerHTML = mf.label + " by Year" +
      (state.year ? "" : " <em>2019 = partial year (to 8 Oct)</em>");
    $("ovDowTitle").textContent = mf.label + " by Weekday";
    $("ovMixTitle").textContent = "Est. Revenue Mix by Category";

    var items = catItems(mk);
    if (items.every(function (d) { return d.value <= 0; })) empty($("chOvCat"), "No data for this selection");
    else hbar($("chOvCat"), items, { vfmt: mf.fmt, labelW: 118, onClick: toggleCat });

    var years = Object.keys(R.byYear).sort();
    if (!years.length) empty($("chOvYear"));
    else vbars($("chOvYear"), years,
      [{ name: mf.label, color: "#2e8b9a",
         values: years.map(function (y) { return R.byYear[y][mk]; }),
         colors: years.map(function (y) { return state.year === y ? "#1f3864" : "#2e8b9a"; }) }],
      { vfmt: mf.fmt, vlabels: true, onClick: function (li) { toggleYear(years[li]); } });

    var mix = CAT.map(function (c, i) {
      return { label: c.name, key: c.name, value: R.byCatAll[i].rev, color: CATPAL[i % CATPAL.length] };
    }).sort(function (a, b) { return b.value - a.value; });
    donut($("chOvMix"), mix, { onClick: toggleCat });

    var wdItems = WDNAMES.map(function (w, i) {
      return { label: w.slice(0, 3), key: i, value: R.byDow[i][mk],
               selected: state.dow === String(i),
               color: state.dow === String(i) ? "#1f3864" : undefined };
    });
    vbars($("chOvDow"), wdItems.map(function (d) { return d.label; }),
      [{ name: mf.label, color: "#2e8b9a", values: wdItems.map(function (d) { return d.value; }),
         colors: wdItems.map(function (d) { return d.selected ? "#1f3864" : "#2e8b9a"; }) }],
      { vfmt: mf.fmt, vlabels: true, onClick: function (li) { toggleDow(li); } });

    // category performance table
    var totU = 0, totRv = 0, totPf = 0;
    R.byCatAll.forEach(function (a) { totU += a.units; totRv += a.rev; totPf += a.profit; });
    var avgPf = totPf / NC;
    var maxRv = Math.max.apply(null, R.byCatAll.map(function (a) { return a.rev; })) || 1;
    var rows = CAT.map(function (c, i) {
      return { name: c.name, i: i, a: R.byCatAll[i],
               lfl: R.catPri[i] > 0 ? R.catCur[i] / R.catPri[i] - 1 : null };
    }).sort(function (a, b) { return b.a.rev - a.a.rev; });
    var trows = rows.map(function (d) {
      var good = d.a.profit >= avgPf;
      return {
        cls: state.cat === d.name ? "sel" : "",
        onClick: function () { toggleCat(d.name); },
        cells: [
          { v: d.name },
          { v: int(d.a.units) },
          { v: eur(d.a.rev), grad: (d.a.rev / maxRv * 100).toFixed(1) },
          { v: eur(d.a.profit) },
          { v: d.lfl === null ? "\u2014" : spct(d.lfl),
            cls: d.lfl === null ? "muted" : d.lfl >= 0 ? "up" : "down" },
          { html: '<span class="flag ' + (good ? "good" : "bad") + '">' +
                  (good ? "Outperforming" : "Below Average") + "</span>" }
        ]
      };
    });
    trows.push({ cls: "total", cells: [
      { v: "TOTAL (8 categories)" }, { v: int(totU) }, { v: eur(totRv) }, { v: eur(totPf) },
      { v: R.lfl ? spct(R.lfl.rev) : "\u2014", cls: R.lfl ? (R.lfl.rev >= 0 ? "up" : "down") : "" },
      { v: "" }
    ] });
    table($("tblCats"),
      ["Category", "Units", "Est. Revenue", "Est. Gross Profit", "LFL YoY", "Flag"], trows);
  }

  function renderTime() {
    var partial = R.winEnd.slice(5, 7) !== "12";
    $("trendTitle").innerHTML = "Revenue Trend &amp; Variance \u2014 " + R.focus + " vs " + R.prior +
      (partial ? " <em>" + R.focus + " to " + R.winEnd + " (like-for-like window)</em>" : "");
    var Bm = R.trend[R.focus], Am = R.hasPrior ? R.trend[R.prior] : null;
    // truncate at the last month with data (2019 is partial: no misleading drop to zero)
    var lastM = 0;
    Bm.forEach(function (v, i) { if (v > 0) lastM = i; });
    var Bt = Bm.slice(0, lastM + 1);
    var At = Am ? Am.slice(0, lastM + 1) : null;
    var Msub = MN.slice(0, lastM + 1);
    if (Bt.every(function (v) { return v === 0; })) empty($("chTrend"));
    else lineTrend($("chTrend"), Msub, At, Bt,
      { focus: R.focus, prior: R.prior, focusPartial: partial,
        avg: Bt.reduce(function (a, b) { return a + b; }, 0) / Bt.length });

    // seasonality index bars
    var seasonItems = R.season;
    if (seasonItems.every(function (v) { return !v; })) empty($("chSeason"));
    else vbars($("chSeason"), MN,
      [{ name: "index", color: "#2e8b9a", values: seasonItems,
         colors: seasonItems.map(function (v) { return v >= 1 ? "#2e8b9a" : "#9dc3e6"; }) }],
      { yfmt: function (v) { return v.toFixed(2); }, vfmt: function (v) { return v.toFixed(2); },
        refLine: 1, refLabel: "avg month", vlabels: true });

    renderHeatmap();

    // quarterly focus vs prior
    $("qTitle").innerHTML = "Quarterly Revenue \u2014 " + R.focus +
      (R.hasPrior ? " vs " + R.prior : "") +
      (partial ? " <em>partial year</em>" : "");
    var qs = [{ name: String(R.focus), color: "#2e8b9a", values: R.qFocus }];
    if (R.hasPrior) qs.unshift({ name: String(R.prior), color: "#9dc3e6", values: R.qPrior });
    vbars($("chQuarter"), ["Q1", "Q2", "Q3", "Q4"], qs, { vlabels: true });

    // long monthly trend
    var keys = Object.keys(R.ym).sort();
    $("longTitle").innerHTML = "Monthly Revenue Trend <em>" +
      (keys.length ? keys[0] + " \u2014 " + keys[keys.length - 1] : "") + "</em>";
    if (!keys.length) empty($("chLong"));
    else lineLong($("chLong"), keys, keys.map(function (k) { return R.ym[k]; }));
  }

  function renderCats() {
    var totU = 0, totRv = 0, totPf = 0;
    R.byCatAll.forEach(function (a) { totU += a.units; totRv += a.rev; totPf += a.profit; });
    var avgPf = totPf / NC;
    var maxRv = Math.max.apply(null, R.byCatAll.map(function (a) { return a.rev; })) || 1;

    var growth = CAT.map(function (c, i) {
      return { label: c.name, key: c.name,
               value: R.catPri[i] > 0 ? R.catCur[i] / R.catPri[i] - 1 : null,
               selected: state.cat === c.name };
    }).sort(function (a, b) {
      return (b.value === null ? -9 : b.value) - (a.value === null ? -9 : a.value);
    });
    divBar($("chGrowth"), growth, toggleCat);

    var byRev = CAT.map(function (c, i) { return { name: c.name, i: i }; })
      .sort(function (a, b) { return R.byCatAll[b.i].rev - R.byCatAll[a.i].rev; });
    var rows = byRev.map(function (d, rank) {
      var a = R.byCatAll[d.i], good = a.profit >= avgPf;
      var lfl = R.catPri[d.i] > 0 ? R.catCur[d.i] / R.catPri[d.i] - 1 : null;
      return {
        cls: state.cat === d.name ? "sel" : "",
        onClick: (function (nm) { return function () { toggleCat(nm); }; })(d.name),
        cells: [
          { html: '<span class="atc">' + CAT[d.i].code + "</span>" + d.name },
          { v: int(a.units) },
          { v: eur(a.rev), grad: (a.rev / maxRv * 100).toFixed(1) },
          { v: pct(a.rev / (totRv || 1)) },
          { v: pct(a.rev ? a.profit / a.rev : 0) },
          { v: lfl === null ? "\u2014" : spct(lfl), cls: lfl === null ? "muted" : lfl >= 0 ? "up" : "down" },
          { v: String(rank + 1) },
          { html: '<span class="flag ' + (good ? "good" : "bad") + '">' +
                  (good ? "Outperforming" : "Below Average") + "</span>" }
        ]
      };
    });
    rows.push({ cls: "total", cells: [
      { v: "TOTAL" }, { v: int(totU) }, { v: eur(totRv) }, { v: "100.0%" },
      { v: pct(totRv ? totPf / totRv : 0) },
      { v: R.lfl ? spct(R.lfl.rev) : "\u2014", cls: R.lfl ? (R.lfl.rev >= 0 ? "up" : "down") : "" },
      { v: "" }, { v: "" }
    ] });
    table($("tblDetail"),
      ["Category", "Units", "Est. Revenue", "Share", "Margin", "LFL YoY", "Rank", "Flag"], rows);

    // assumptions table (static)
    table($("tblAssump"), ["Category", "\u20ac/unit", "Margin"], CAT.map(function (c, i) {
      return { cells: [
        { html: '<span class="atc">' + c.code + "</span>" + c.name },
        { v: "\u20ac" + c.price.toFixed(2) },
        { v: pct(c.margin) }
      ] };
    }));

    // units vs revenue share
    shareBars($("chShare"), CAT.map(function (c, i) {
      return { label: c.name, selected: state.cat === c.name,
               a: R.byCatAll[i].units / (totU || 1),
               b: R.byCatAll[i].rev / (totRv || 1) };
    }));

    // therapy areas
    table($("tblTherapy"), ["ATC", "Therapy area"], CAT.map(function (c) {
      return { cells: [
        { html: '<span class="atc">' + c.code + "</span>" },
        { html: '<span class="muted" style="font-size:11px">' + c.desc + "</span>" }
      ] };
    }));
  }

  /* ------------------------------------------------------------ interactions */
  function toggleCat(name) {
    state.cat = state.cat === name ? "" : name;
    render();
  }
  function toggleYear(y) {
    state.year = state.year === y ? "" : y;
    render();
  }
  function toggleDow(i) {
    state.dow = state.dow === String(i) ? "" : String(i);
    render();
  }
  function resetAll() {
    state.year = ""; state.cat = ""; state.dow = ""; state.metric = "rev";
    render();
  }
  function syncControls() {
    $("sCat").value = state.cat;
    $("sYear").value = state.year;
    $("sDow").value = state.dow;
    var seg = $("segMetric").querySelectorAll("button");
    seg.forEach(function (b) { b.classList.toggle("on", b.dataset.m === state.metric); });
  }
  function render() {
    compute();
    syncControls();
    renderKPIs();
    if (state.page === "overview") renderOverview();
    else if (state.page === "time") renderTime();
    else renderCats();
  }

  /* ------------------------------------------------------------ boot */
  function boot() {
    // slicers
    var sCat = $("sCat");
    sCat.appendChild(new Option("All categories", ""));
    CAT.forEach(function (c) { sCat.appendChild(new Option(c.name + " (" + c.code + ")", c.name)); });
    var sYear = $("sYear");
    sYear.appendChild(new Option("All years", ""));
    Array.from(new Set(YEARS)).sort().forEach(function (y) {
      sYear.appendChild(new Option(String(y) + (y === 2019 ? " (partial)" : ""), String(y)));
    });
    var sDow = $("sDow");
    sDow.appendChild(new Option("All weekdays", ""));
    WDNAMES.forEach(function (w, i) { sDow.appendChild(new Option(w, String(i))); });

    sCat.addEventListener("change", function () { state.cat = sCat.value; render(); });
    sYear.addEventListener("change", function () { state.year = sYear.value; render(); });
    sDow.addEventListener("change", function () { state.dow = sDow.value; render(); });
    $("resetBtn").addEventListener("click", resetAll);
    $("resetBtn2").addEventListener("click", resetAll);

    // metric segmented control
    $("segMetric").addEventListener("click", function (e) {
      var b = e.target.closest("button");
      if (!b) return;
      state.metric = b.dataset.m;
      render();
    });

    // page nav
    var subs = {
      overview: "Commercial overview \u2014 real POS data 2014\u20132019, \u20ac figures estimated",
      time: "Year, month, weekday & trading-hour patterns \u2014 2019 is like-for-like vs 2018",
      cats: "ATC category performance, growth, assumptions & therapy areas"
    };
    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.page = btn.dataset.page;
        document.querySelectorAll(".nav-btn").forEach(function (b) {
          b.classList.toggle("active", b === btn);
        });
        document.querySelectorAll(".page").forEach(function (p) {
          p.classList.toggle("hidden", p.id !== "page-" + state.page);
        });
        $("pageSub").textContent = subs[state.page];
        render();
      });
    });

    // responsive re-render
    var rt;
    window.addEventListener("resize", function () {
      clearTimeout(rt);
      rt = setTimeout(render, 180);
    });

    render();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
