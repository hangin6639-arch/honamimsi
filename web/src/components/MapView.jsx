// W1 — 입지 지도: Leaflet + siting.geojson, 셀 클릭 시 점수 분해 팝업
import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const COLORS = ["#fff3d1", "#ffe08a", "#ffcd4a", "#e6a817", "#b8770a"];

function colorFor(score) {
  if (score >= 80) return COLORS[4];
  if (score >= 65) return COLORS[3];
  if (score >= 50) return COLORS[2];
  if (score >= 35) return COLORS[1];
  return COLORS[0];
}

function scoreBar(label, v) {
  return `${label} <span style="float:right">${v}</span>
    <div class="bar"><i style="width:${Math.min(v, 100)}%"></i></div>`;
}

function onEachFeature(feature, layer) {
  const p = feature.properties;
  layer.bindPopup(
    `<div class="popup-score">
      <b>${p.name}</b> <span style="float:right">종합 ${p.total_score} (${p.rank}위)</span>
      <div style="margin-top:8px">
        ${scoreBar("잉여전력 접근", p.surplus_score)}
        ${scoreBar("상권 밀도", p.commerce_score)}
        ${scoreBar("교통 접근성", p.access_score)}
      </div>
      도보권 가맹점 ${p.merchant_count}곳 · 충전기 ${p.charger_count}기(추정)
    </div>`
  );
  layer.on({
    mouseover: (e) => e.target.setStyle({ weight: 3, fillOpacity: 0.75 }),
    mouseout: (e) => e.target.setStyle({ weight: 1.5, fillOpacity: 0.55 }),
  });
}

export default function MapView({ siting }) {
  return (
    <div className="card">
      <h2>W1 · 충전 거점 입지 적합도</h2>
      <p className="desc">
        제주 상가업소 5.7만 개 기반 보로노이 셀 · 적합도 = 잉여전력 접근 50% + 상권 밀도 30% + 교통 접근성 20%
      </p>
      <div className="map-wrap">
        <MapContainer center={[33.42, 126.55]} zoom={10} scrollWheelZoom>
          <TileLayer
            attribution='&copy; OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <GeoJSON
            data={siting}
            style={(f) => ({
              color: "#8a6510",
              weight: 1.5,
              fillColor: colorFor(f.properties.total_score),
              fillOpacity: 0.55,
            })}
            onEachFeature={onEachFeature}
          />
        </MapContainer>
      </div>
      <div className="legend">
        적합도:
        {["~35", "35~50", "50~65", "65~80", "80~"].map((r, i) => (
          <span key={r}>
            <span className="swatch" style={{ background: COLORS[i] }} />
            {r}
          </span>
        ))}
        <span style={{ marginLeft: "auto" }}>셀 클릭 → 점수 분해</span>
      </div>
    </div>
  );
}
