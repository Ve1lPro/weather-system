console.log("最新 main.js 已加载");

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(await r.text());
  return await r.json();
}

function selectedValues(sel) {
  return Array.from(sel.selectedOptions).map(o => o.value);
}

function buildLineOption(payload) {
  const series = payload.series || [];
  const label = payload.label || "";

  return {
    tooltip: { trigger: "axis" },
    legend: { data: series.map(s => s.city) },
    xAxis: { type: "time" },
    yAxis: { type: "value", name: label },
    series: series.map(s => ({
      name: s.city,
      type: "line",
      smooth: true,
      showSymbol: false,
      data: s.data
    }))
  };
}

function buildHeatOption(payload) {
  const labels = payload.labels || [];
  const heat = payload.matrix || [];

  return {
    tooltip: {
      formatter: (p) => {
        const x = labels[p.value[0]];
        const y = labels[p.value[1]];
        const v = p.value[2];
        return `${y} vs ${x}<br/>相关系数：${v}`;
      }
    },
    grid: { top: 30, left: 80, right: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: labels,
      splitArea: { show: true }
    },
    yAxis: {
      type: "category",
      data: labels,
      splitArea: { show: true }
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 10
    },
    series: [{
      type: "heatmap",
      data: heat,
      label: { show: true }
    }]
  };
}

async function init() {
  const citiesSel = document.getElementById("cities");
  const metricSel = document.getElementById("metric");
  const corrSel = document.getElementById("corrCity");
  const limitSel = document.getElementById("limit");
  const btn = document.getElementById("refresh");

  const lineHint = document.getElementById("lineHint");
  const heatHint = document.getElementById("heatHint");

  const kpiMae = document.getElementById("kpiMae");
  const kpiRmse = document.getElementById("kpiRmse");
  const kpiMaeHint = document.getElementById("kpiMaeHint");
  const kpiRmseHint = document.getElementById("kpiRmseHint");

  const dataCount = document.getElementById("dataCount");
  const dataStatus = document.getElementById("dataStatus");
  const currentCity = document.getElementById("currentCity");
  const lastRefresh = document.getElementById("lastRefresh");

  const rankHotCity = document.getElementById("rankHotCity");
  const rankHotValue = document.getElementById("rankHotValue");
  const rankColdCity = document.getElementById("rankColdCity");
  const rankColdValue = document.getElementById("rankColdValue");
  const rankHumCity = document.getElementById("rankHumCity");
  const rankHumValue = document.getElementById("rankHumValue");
  const analysisCityCard = document.getElementById("analysisCityCard");

  const avgTemp = document.getElementById("avgTemp");
  const avgTempHint = document.getElementById("avgTempHint");
  const maxTemp = document.getElementById("maxTemp");
  const minTempHint = document.getElementById("minTempHint");
  const trendLabel = document.getElementById("trendLabel");
  const trendHint = document.getElementById("trendHint");
  const avgHumidity = document.getElementById("avgHumidity");
  const summaryCityHint = document.getElementById("summaryCityHint");

  const lineChart = echarts.init(document.getElementById("chartLine"));
  const heatChart = echarts.init(document.getElementById("chartHeat"));

  const cities = await getJSON("/api/cities");

  citiesSel.innerHTML = "";
  corrSel.innerHTML = "";

  for (const c of cities.cities) {
    const o1 = document.createElement("option");
    o1.value = c.name;
    o1.textContent = c.name;
    citiesSel.appendChild(o1);

    const o2 = document.createElement("option");
    o2.value = c.name;
    o2.textContent = c.name;
    corrSel.appendChild(o2);
  }

  const defaultCity = window.DEFAULT_CITY || (cities.cities[0] ? cities.cities[0].name : "");

  for (const opt of citiesSel.options) {
    if (opt.value === defaultCity) opt.selected = true;
  }
  corrSel.value = defaultCity;
  currentCity.textContent = defaultCity;
  analysisCityCard.textContent = defaultCity;

  async function refreshLine() {
    const picked = selectedValues(citiesSel);
    if (picked.length === 0) {
      alert("请至少选择一个城市");
      return null;
    }

    const metric = metricSel.value;
    const limit = limitSel.value;

    const payloadLine = await getJSON(
      `/api/series?cities=${encodeURIComponent(picked.join(","))}` +
      `&metric=${encodeURIComponent(metric)}` +
      `&limit=${encodeURIComponent(limit)}`
    );

    lineChart.setOption(buildLineOption(payloadLine), true);

    const series = payloadLine.series || [];
    let count = 0;
    let lastTime = "-";

    if (series.length > 0 && series[0].data.length > 0) {
      count = series[0].data.length;
      lastTime = series[0].data[series[0].data.length - 1][0];
    }

    dataCount.textContent = count;
    dataStatus.textContent = `最新时间：${lastTime}`;
    lineHint.textContent = `当前展示城市：${picked.join("、")} ｜ 指标：${metricSel.options[metricSel.selectedIndex].text}`;

    return payloadLine;
  }

  async function refreshCorrAndEval() {
    const city = corrSel.value;
    const limit = limitSel.value;
    currentCity.textContent = city;
    analysisCityCard.textContent = city;
    heatHint.textContent = `当前分析城市：${city}`;

    try {
      const ev = await getJSON(`/api/eval?city=${encodeURIComponent(city)}&limit=${encodeURIComponent(limit)}`);
      kpiMae.textContent = ev.mae;
      kpiRmse.textContent = ev.rmse;
      kpiMaeHint.textContent = `训练${ev.train_size} / 测试${ev.test_size}`;
      kpiRmseHint.textContent = `训练${ev.train_size} / 测试${ev.test_size}`;
    } catch (e) {
      kpiMae.textContent = "-";
      kpiRmse.textContent = "-";
      kpiMaeHint.textContent = "数据不足或评估失败";
      kpiRmseHint.textContent = "数据不足或评估失败";
    }

    try {
      const payloadHeat = await getJSON(`/api/corr?city=${encodeURIComponent(city)}&limit=${encodeURIComponent(limit)}`);
      heatChart.setOption(buildHeatOption(payloadHeat), true);
    } catch (e) {
      heatChart.clear();
      heatChart.setOption({
        title: { text: "暂无相关性数据", left: "center" }
      });
    }
  }


  async function refreshSummary() {
    const city = corrSel.value;
    const limit = limitSel.value;

    try {
      const summary = await getJSON(`/api/summary?city=${encodeURIComponent(city)}&limit=${encodeURIComponent(limit)}`);
      avgTemp.textContent = summary.avg_temp ?? "-";
      avgTempHint.textContent = `数据量：${summary.total_records} 条 ｜ 最新温度：${summary.latest_temp ?? "-"} ℃`;
      maxTemp.textContent = summary.max_temp ?? "-";
      minTempHint.textContent = `最低温：${summary.min_temp ?? "-"} ℃`;
      trendLabel.textContent = summary.trend_label || "-";
      trendHint.textContent = summary.trend_delta === null ? "根据最近 6 个时间点判断" : `近 6 个点均值变化：${summary.trend_delta} ℃`;
      avgHumidity.textContent = summary.avg_humidity ?? "-";
      summaryCityHint.textContent = `当前统计城市：${summary.city}`;
    } catch (e) {
      console.error("refreshSummary error:", e);
      avgTemp.textContent = "-";
      avgTempHint.textContent = "暂无统计数据";
      maxTemp.textContent = "-";
      minTempHint.textContent = "最低温：-";
      trendLabel.textContent = "-";
      trendHint.textContent = "趋势判断失败";
      avgHumidity.textContent = "-";
      summaryCityHint.textContent = "当前统计城市：-";
    }
  }

  async function refreshRank() {
    try {
      const rank = await getJSON("/api/rank");

      if (rank.highest_temp) {
        rankHotCity.textContent = rank.highest_temp.city;
        rankHotValue.textContent = `${rank.highest_temp.temp_c} ℃`;
      } else {
        rankHotCity.textContent = "-";
        rankHotValue.textContent = "暂无数据";
      }

      if (rank.lowest_temp) {
        rankColdCity.textContent = rank.lowest_temp.city;
        rankColdValue.textContent = `${rank.lowest_temp.temp_c} ℃`;
      } else {
        rankColdCity.textContent = "-";
        rankColdValue.textContent = "暂无数据";
      }

      if (rank.highest_humidity) {
        rankHumCity.textContent = rank.highest_humidity.city;
        rankHumValue.textContent = `${rank.highest_humidity.humidity} %`;
      } else {
        rankHumCity.textContent = "-";
        rankHumValue.textContent = "暂无数据";
      }
    } catch (e) {
      console.error("refreshRank error:", e);
      rankHotCity.textContent = "-";
      rankHotValue.textContent = "暂无数据";
      rankColdCity.textContent = "-";
      rankColdValue.textContent = "暂无数据";
      rankHumCity.textContent = "-";
      rankHumValue.textContent = "暂无数据";
    }
  }

  async function refreshAll() {
    btn.disabled = true;
    btn.textContent = "刷新中...";

    try {
      await refreshLine();
      await refreshCorrAndEval();
      await refreshSummary();
      await refreshRank();
      lastRefresh.textContent = `最后刷新：${new Date().toLocaleString()}`;
    } catch (e) {
      console.error(e);
      alert("刷新失败：\n" + e.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "刷新图表";
    }
  }

  btn.addEventListener("click", refreshAll);
  metricSel.addEventListener("change", refreshLine);
  citiesSel.addEventListener("change", refreshLine);
  corrSel.addEventListener("change", async () => {
    await refreshCorrAndEval();
    await refreshSummary();
  });
  limitSel.addEventListener("change", refreshAll);

  await refreshAll();

  window.addEventListener("resize", () => {
    lineChart.resize();
    heatChart.resize();
  });
}

init().catch(err => {
  console.error(err);
  alert("页面加载失败：\n" + err.message);
});