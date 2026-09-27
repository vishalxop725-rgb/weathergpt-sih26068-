import { Fragment, useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Tooltip,
} from "react-leaflet";

// Leaflet's own stylesheet. Without this line the map tiles look scrambled.
import "leaflet/dist/leaflet.css";
import "./WeatherMap.css";

// =====================================================
// CONSTANTS
// =====================================================

const CITIES_API_URL = "http://127.0.0.1:8000/api/weather/cities";

// South-west and north-east corners that frame India
const INDIA_BOUNDS = [
  [11.5, 71.5],
  [30.5, 89.5],
];

const LAYERS = [
  { id: "temperature", label: "🌡️ Temperature" },
  { id: "rain", label: "🌧️ Rain" },
  { id: "wind", label: "💨 Wind" },
  { id: "alerts", label: "⚠️ Alerts" },
];

const LEVEL_ORDER = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 };

const LEVEL_COLOR = {
  GREEN: "#3aa675",
  YELLOW: "#f0b429",
  ORANGE: "#e8833a",
  RED: "#d64545",
};

// Legend entries shown under the map for each layer
const LEGENDS = {
  temperature: [
    { color: "#2878c8", text: "Below 25°C" },
    { color: "#3aa675", text: "25–34°C" },
    { color: "#f0b429", text: "35–37°C" },
    { color: "#e8833a", text: "38–39°C" },
    { color: "#d64545", text: "40°C and above" },
  ],
  rain: [
    { color: "#9bb0c7", text: "No rain now" },
    { color: "#5aa9e6", text: "Under 5 mm" },
    { color: "#2878c8", text: "5–19 mm" },
    { color: "#1b4f8a", text: "20 mm and above" },
  ],
  wind: [
    { color: "#3aa675", text: "Under 20 km/h" },
    { color: "#f0b429", text: "20–39 km/h" },
    { color: "#e8833a", text: "40–59 km/h" },
    { color: "#d64545", text: "60 km/h and above" },
  ],
  alerts: [
    { color: LEVEL_COLOR.GREEN, text: "Green" },
    { color: LEVEL_COLOR.YELLOW, text: "Yellow" },
    { color: LEVEL_COLOR.ORANGE, text: "Orange" },
    { color: LEVEL_COLOR.RED, text: "Red" },
  ],
};

// =====================================================
// HELPERS
// =====================================================

function temperatureColor(t) {
  if (t >= 40) return "#d64545";
  if (t >= 38) return "#e8833a";
  if (t >= 35) return "#f0b429";
  if (t >= 25) return "#3aa675";
  return "#2878c8";
}

function rainColor(mm) {
  if (mm >= 20) return "#1b4f8a";
  if (mm >= 5) return "#2878c8";
  if (mm > 0) return "#5aa9e6";
  return "#9bb0c7";
}

function windColor(kmh) {
  if (kmh >= 60) return "#d64545";
  if (kmh >= 40) return "#e8833a";
  if (kmh >= 20) return "#f0b429";
  return "#3aa675";
}

function formatDay(dateString) {
  const date = new Date(`${dateString}T00:00:00`);

  return date.toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

// Finds the most serious alert level in an alert list
function getHighestLevel(alerts) {
  let highest = "GREEN";

  (alerts || []).forEach((alert) => {
    if ((LEVEL_ORDER[alert.level] ?? 0) > LEVEL_ORDER[highest]) {
      highest = alert.level;
    }
  });

  return highest;
}

function cityLevel(city) {
  return city.highest_alert_level || getHighestLevel(city.alerts);
}

// What one city's marker shows for the selected layer
function getMarkerInfo(city, layer) {
  const current = city.current;

  if (layer === "alerts") {
    const level = cityLevel(city);

    return { color: LEVEL_COLOR[level], label: level };
  }

  if (!current) {
    return { color: "#9bb0c7", label: "--" };
  }

  if (layer === "temperature") {
    return {
      color: temperatureColor(current.temperature),
      label: `${Math.round(current.temperature)}°C`,
    };
  }

  if (layer === "rain") {
    return {
      color: rainColor(current.precipitation),
      label: `${current.precipitation} mm`,
    };
  }

  return {
    color: windColor(current.wind_speed),
    label: `${Math.round(current.wind_speed)} km/h`,
  };
}

// =====================================================
// COMPONENT
// =====================================================

function WeatherMap({ weatherData, alertsData }) {
  const [layer, setLayer] = useState("temperature");
  const [selectedName, setSelectedName] = useState("Delhi");

  // Multi-city data from /api/weather/cities
  const [citiesData, setCitiesData] = useState(null);
  const [citiesLoading, setCitiesLoading] = useState(true);
  const [citiesError, setCitiesError] = useState(false);

  useEffect(() => {
    async function loadCities() {
      try {
        setCitiesLoading(true);
        setCitiesError(false);

        const response = await fetch(CITIES_API_URL);

        if (!response.ok) {
          throw new Error("Cities request failed");
        }

        const data = await response.json();

        if (!data.success || !data.cities?.length) {
          throw new Error("City data unavailable");
        }

        setCitiesData(data);
      } catch (error) {
        console.error("Cities error:", error);
        setCitiesError(true);
      } finally {
        setCitiesLoading(false);
      }
    }

    loadCities();
  }, []);

  // ---- Which cities do we draw? ----
  // Normally the 8 cities from the backend. If that request
  // fails, fall back to Delhi only, using the data App.jsx
  // already loaded.

  const fallbackCities = weatherData?.current
    ? [
        {
          name: "Delhi",
          state: "Delhi",
          latitude: 28.6139,
          longitude: 77.209,
          current: weatherData.current,
          forecast: weatherData.forecast,
          alerts: alertsData?.alerts || [],
        },
      ]
    : [];

  const usingFallback = !citiesData?.cities?.length;

  const cities = usingFallback ? fallbackCities : citiesData.cities;

  const selected =
    cities.find((city) => city.name === selectedName) || cities[0];

  const current = selected?.current;
  const forecast = selected?.forecast;
  const selectedAlerts = selected?.alerts || [];

  // ---- Peak rain in the selected city's forecast ----
  let peakRain = null;

  if (forecast?.precipitation?.length) {
    const maxValue = Math.max(...forecast.precipitation);

    if (maxValue > 0) {
      const index = forecast.precipitation.indexOf(maxValue);

      peakRain = {
        amount: maxValue,
        date: forecast.dates[index],
      };
    }
  }

  const updatedTime = citiesData?.fetched_at
    ? new Date(citiesData.fetched_at).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  // =====================================================
  // SIDE PANEL CONTENT (changes with the layer)
  // =====================================================

  function renderPanel() {
    if (citiesLoading && !selected) {
      return <p className="wm-muted">Loading weather data...</p>;
    }

    if (!selected) {
      return (
        <p className="wm-muted">
          Weather data unavailable. Check that the backend is
          running.
        </p>
      );
    }

    // ---------- TEMPERATURE ----------
    if (layer === "temperature") {
      return (
        <>
          <div className="wm-big">
            {Math.round(current.temperature)}°C
          </div>

          <p className="wm-muted">
            Feels like {Math.round(current.apparent_temperature)}°C
            · Humidity {Math.round(current.humidity)}%
          </p>

          <div className="wm-subtitle">Daily high / low</div>

          <div className="wm-list">
            {forecast?.dates?.map((date, i) => (
              <div className="wm-row" key={date}>
                <span>{formatDay(date)}</span>
                <strong>
                  {Math.round(forecast.max_temperature[i])}° /{" "}
                  {Math.round(forecast.min_temperature[i])}°
                </strong>
              </div>
            ))}
          </div>
        </>
      );
    }

    // ---------- RAIN ----------
    if (layer === "rain") {
      return (
        <>
          <div className="wm-big">{current.precipitation} mm</div>

          <p className="wm-muted">Rain right now</p>

          {peakRain ? (
            <p className="wm-note-rain">
              Heaviest forecast day: {peakRain.amount} mm on{" "}
              {formatDay(peakRain.date)}
            </p>
          ) : (
            <p className="wm-muted">
              No rain forecast in the next 7 days.
            </p>
          )}

          <div className="wm-subtitle">Forecast rainfall</div>

          <div className="wm-list">
            {forecast?.dates?.map((date, i) => {
              const mm = forecast.precipitation[i];
              const width = Math.min(100, (mm / 50) * 100);

              return (
                <div className="wm-row wm-row-bar" key={date}>
                  <span>{formatDay(date)}</span>

                  <div className="wm-bar-track">
                    <div
                      className="wm-bar-fill"
                      style={{
                        width: `${width}%`,
                        background: rainColor(mm),
                      }}
                    />
                  </div>

                  <strong>{mm} mm</strong>
                </div>
              );
            })}
          </div>
        </>
      );
    }

    // ---------- WIND ----------
    if (layer === "wind") {
      return (
        <>
          <div className="wm-big">
            {Math.round(current.wind_speed)} km/h
          </div>

          <p className="wm-muted">Current wind speed at 10 m</p>

          <p className="wm-muted">
            Wind forecasts are not loaded yet. Only the current
            wind speed is shown.
          </p>
        </>
      );
    }

    // ---------- ALERTS ----------
    return (
      <>
        <div className="wm-warning">
          WeatherGPT-generated alerts based on Open-Meteo
          forecast data. Not official government or IMD
          warnings.
        </div>

        <div className="wm-list">
          {selectedAlerts.map((alert, i) => (
            <div
              className="wm-alert"
              key={`${alert.time}-${i}`}
              style={{
                borderLeftColor: LEVEL_COLOR[alert.level],
              }}
            >
              <strong>
                {alert.level} · {alert.title}
              </strong>

              <span>{alert.time}</span>

              <p>{alert.description}</p>
            </div>
          ))}
        </div>
      </>
    );
  }

  // =====================================================
  // RENDER
  // =====================================================

  return (
    <div className="wm-container">
      {/* ---------- Layer buttons + data label ---------- */}

      <div className="wm-toolbar">
        <div className="wm-layers">
          {LAYERS.map((item) => (
            <button
              key={item.id}
              className={
                layer === item.id
                  ? "wm-layer-button wm-active"
                  : "wm-layer-button"
              }
              onClick={() => setLayer(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <span className="wm-source">
          Weather data: Open-Meteo
          {updatedTime ? ` · updated ${updatedTime}` : ""}
        </span>
      </div>

      {/* ---------- City chips ---------- */}

      {cities.length > 0 && (
        <div className="wm-cities">
          {cities.map((city) => (
            <button
              key={city.name}
              className={
                selected?.name === city.name
                  ? "wm-chip wm-active"
                  : "wm-chip"
              }
              onClick={() => setSelectedName(city.name)}
            >
              <i
                className="wm-dot"
                style={{
                  background: LEVEL_COLOR[cityLevel(city)],
                }}
              />
              {city.name}
            </button>
          ))}
        </div>
      )}

      {/* ---------- Map + side panel ---------- */}

      <div className="wm-layout">
        <div className="wm-map-wrap">
          <MapContainer
            bounds={INDIA_BOUNDS}
            boundsOptions={{ padding: [20, 20] }}
            scrollWheelZoom={true}
            className="wm-map"
          >
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {cities.map((city) => {
              const info = getMarkerInfo(city, layer);
              const isSelected = selected?.name === city.name;
              const position = [city.latitude, city.longitude];

              return (
                <Fragment key={`${city.name}-${layer}`}>
                  {/* Coloured circle with the value inside */}
                  <CircleMarker
                    center={position}
                    radius={24}
                    pathOptions={{
                      color: isSelected ? "#172033" : "#ffffff",
                      weight: isSelected ? 4 : 3,
                      fillColor: info.color,
                      fillOpacity: 0.88,
                    }}
                    eventHandlers={{
                      click: () => setSelectedName(city.name),
                    }}
                  >
                    <Tooltip
                      permanent
                      direction="center"
                      className="wm-marker-label"
                    >
                      {info.label}
                    </Tooltip>
                  </CircleMarker>

                  {/* Invisible point that only carries the city name */}
                  <CircleMarker
                    center={position}
                    radius={1}
                    interactive={false}
                    pathOptions={{ opacity: 0, fillOpacity: 0 }}
                  >
                    <Tooltip
                      permanent
                      direction="bottom"
                      offset={[0, 28]}
                      className="wm-city-label"
                    >
                      {city.name}
                    </Tooltip>
                  </CircleMarker>
                </Fragment>
              );
            })}
          </MapContainer>
        </div>

        <aside className="wm-panel">
          <div className="wm-panel-title">
            📍 {selected ? selected.name : "No data"}
            <span>
              {LAYERS.find((item) => item.id === layer)?.label}
            </span>
          </div>

          {renderPanel()}
        </aside>
      </div>

      {/* ---------- Legend ---------- */}

      <div className="wm-legend">
        {LEGENDS[layer].map((item) => (
          <span key={item.text}>
            <i style={{ background: item.color }} />
            {item.text}
          </span>
        ))}
      </div>

      <p className="wm-footnote">
        {usingFallback
          ? citiesLoading
            ? "Loading city data..."
            : citiesError
            ? "Multi-city data is unavailable, so only Delhi is shown. Check that the backend is running and restart it if you just updated main.py. "
            : ""
          : `${cities.length} cities. `}
        Map tiles © OpenStreetMap contributors. Alert colours are
        WeatherGPT-generated from Open-Meteo forecasts, not
        official warnings.
      </p>
    </div>
  );
}

export default WeatherMap;