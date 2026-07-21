// M3 — 꿀 지갑: 쿠폰·주차권 + 가맹점/충전소 지도(siting.geojson 재사용)
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const COUPONS = [
  { ic: "☕", name: "제주 카페 아메리카노 1+1", meta: "꿀 500 · 도보권 가맹점", },
  { ic: "🅿️", name: "제주시청 공영주차 2시간권", meta: "꿀 800 · V2G 참여자 전용" },
  { ic: "🍊", name: "감귤 초콜릿 20% 할인", meta: "꿀 300 · 상권 제휴" },
  { ic: "⚡", name: "급속충전 3,000원 할인권", meta: "꿀 1,000 · 전 충전소" },
];

export default function Wallet({ siting, history }) {
  const honey = Math.round(history.reduce((a, b) => a + b.won, 0) / 100);
  const stations = siting.features.map((f) => f.properties);

  return (
    <>
      <div className="app-top">
        <span className="jar">🍯</span>
        <div>
          <h1>꿀 지갑</h1>
          <div className="copy">모은 꿀로 지역에서 쓰세요</div>
        </div>
      </div>

      <div className="hero">
        <div className="t">내 꿀</div>
        <div className="big">🍯 {honey.toLocaleString()} 꿀</div>
        <div className="msg">참여 100원 = 1꿀 · 지역 가맹점에서 현금처럼</div>
      </div>

      <div className="sec">
        <h2>쿠폰 · 주차권</h2>
        {COUPONS.map((c) => (
          <div className="coupon" key={c.name}>
            <span className="ic">{c.ic}</span>
            <div>
              <div className="name">{c.name}</div>
              <div className="meta">{c.meta}</div>
            </div>
            <button className="use">교환</button>
          </div>
        ))}
      </div>

      <div className="sec">
        <h2>가맹점 · 충전소 지도</h2>
        <div className="map-wrap">
          <MapContainer center={[33.42, 126.55]} zoom={9} scrollWheelZoom={false}>
            <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {stations.map((p) => (
              <CircleMarker
                key={p.cell_id}
                center={[p.station_lat, p.station_lon]}
                radius={7 + Math.min(p.merchant_count / 400, 6)}
                pathOptions={{ color: "#c47f17", fillColor: "#ffcd4a", fillOpacity: 0.85 }}
              >
                <Popup>
                  <b>{p.name}</b>
                  <br />가맹점 {p.merchant_count}곳 · 충전기 {p.charger_count}기
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
        <div className="chart-note">원 크기 = 도보권 가맹점 수 · 입지 분석(siting) 데이터 재사용</div>
      </div>
    </>
  );
}
