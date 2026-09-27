import { useState, useEffect, useRef } from "react";
import "./App.css";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

// ============================================================
// LEAFLET MARKER ICON FIX
// ============================================================

const defaultIcon = L.icon({
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

// ============================================================
// API BASE URL
// ============================================================

const API_BASE_URL = "https://weathergpt-sih26068-production-136b.up.railway.app";

// ============================================================
// CHAT LOCATIONS
// ============================================================

const LOCATION_OPTIONS = [
  "Delhi",
  "Mumbai",
  "Kolkata",
  "Chennai",
  "Bengaluru",
  "Hyderabad",
  "Ahmedabad",
  "Pune",
];

// ============================================================
// ADVISORY SECTORS
// ============================================================

const ADVISORY_SECTOR_META = {
  agriculture: { icon: "🌾", label: "Agriculture" },
  aviation: { icon: "✈️", label: "Aviation" },
  marine: { icon: "🚢", label: "Marine" },
  urban: { icon: "🏙️", label: "Urban" },
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

function getWeatherIcon(code) {
  if (code === 0) return "☀️";
  if (code >= 1 && code <= 3) return "🌤️";
  if (code >= 45 && code <= 48) return "🌫️";
  if (code >= 51 && code <= 67) return "🌧️";
  if (code >= 71 && code <= 77) return "❄️";
  if (code >= 80 && code <= 82) return "🌦️";
  if (code >= 95) return "⛈️";
  return "🌤️";
}

function getWeatherDescription(code) {
  if (code === 0) return "Clear Sky";
  if (code <= 3) return "Partly Cloudy";
  if (code <= 48) return "Foggy";
  if (code <= 67) return "Rain";
  if (code <= 77) return "Snow";
  if (code <= 82) return "Rain Showers";
  return "Thunderstorm";
}

function getWeatherTheme(code) {
  if (code === 0) return "clear";
  if (code >= 1 && code <= 3) return "cloudy";
  if (code >= 45 && code <= 48) return "fog";
  if (code >= 51 && code <= 67) return "rain";
  if (code >= 71 && code <= 77) return "snow";
  if (code >= 80 && code <= 82) return "rain";
  if (code >= 95) return "storm";
  return "default";
}

function getAlertClass(level) {
  const normalized = String(level || "")
    .toUpperCase()
    .trim();

  if (normalized === "RED") return "alert-red";
  if (normalized === "ORANGE") return "alert-orange";
  if (normalized === "YELLOW") return "alert-yellow";

  return "alert-green";
}

function getAlertEmoji(level) {
  const normalized = String(level || "")
    .toUpperCase()
    .trim();

  if (normalized === "RED") return "🔴";
  if (normalized === "ORANGE") return "🟠";
  if (normalized === "YELLOW") return "🟡";

  return "🟢";
}

function formatDate(dateString) {
  if (!dateString) return "";

  try {
    return new Date(
      dateString + "T12:00:00"
    ).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
}

function formatShortDate(dateString) {
  if (!dateString) return "";

  try {
    return new Date(
      dateString + "T12:00:00"
    ).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
    });
  } catch {
    return dateString;
  }
}

// ============================================================
// TEMPERATURE CHART
// ============================================================

function TemperatureChart({
  dates = [],
  maxTemperatures = [],
  meanTemperatures = [],
  minTemperatures = [],
}) {
  if (!dates.length) {
    return <div className="chart-placeholder">📈</div>;
  }

  const width = 760;
  const height = 300;
  const paddingLeft = 48;
  const paddingRight = 20;
  const paddingTop = 24;
  const paddingBottom = 42;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const allValues = [
    ...maxTemperatures,
    ...meanTemperatures,
    ...minTemperatures,
  ].filter(
    (value) =>
      typeof value === "number" && Number.isFinite(value)
  );

  if (!allValues.length) {
    return <div className="chart-placeholder">📈</div>;
  }

  const minValue = Math.floor(Math.min(...allValues) - 2);
  const maxValue = Math.ceil(Math.max(...allValues) + 2);
  const range = maxValue - minValue || 1;

  const getX = (index) => {
    if (dates.length === 1) {
      return paddingLeft + chartWidth / 2;
    }

    return (
      paddingLeft +
      (index / (dates.length - 1)) * chartWidth
    );
  };

  const getY = (value) =>
    paddingTop +
    ((maxValue - value) / range) * chartHeight;

  const createPoints = (values) =>
    values
      .map((value, index) => {
        if (
          typeof value !== "number" ||
          !Number.isFinite(value)
        ) {
          return null;
        }

        return `${getX(index)},${getY(value)}`;
      })
      .filter(Boolean)
      .join(" ");

  const maxPoints = createPoints(maxTemperatures);
  const meanPoints = createPoints(meanTemperatures);
  const minPoints = createPoints(minTemperatures);

  const gridValues = [
    maxValue,
    Math.round(maxValue - range * 0.25),
    Math.round(maxValue - range * 0.5),
    Math.round(maxValue - range * 0.75),
    minValue,
  ];

  const labelIndexes = [];
  const step = Math.max(1, Math.ceil(dates.length / 7));

  for (let index = 0; index < dates.length; index += step) {
    labelIndexes.push(index);
  }

  if (
    dates.length > 1 &&
    labelIndexes[labelIndexes.length - 1] !== dates.length - 1
  ) {
    labelIndexes.push(dates.length - 1);
  }

  return (
    <div className="temperature-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        role="img"
        aria-label="Historical temperature trend"
      >
        {gridValues.map((value, index) => {
          const y = getY(value);

          return (
            <g key={index}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
              />

              <text
                x="8"
                y={y + 4}
                fontSize="11"
                fill="#64748b"
              >
                {value}°
              </text>
            </g>
          );
        })}

        {maxPoints && (
          <polyline
            points={maxPoints}
            fill="none"
            stroke="#ef4444"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {meanPoints && (
          <polyline
            points={meanPoints}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {minPoints && (
          <polyline
            points={minPoints}
            fill="none"
            stroke="#22c55e"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {labelIndexes.map((index) => (
          <text
            key={index}
            x={getX(index)}
            y={height - 12}
            textAnchor="middle"
            fontSize="10"
            fill="#64748b"
          >
            {formatShortDate(dates[index])}
          </text>
        ))}
      </svg>

      <div
        style={{
          display: "flex",
          gap: "18px",
          justifyContent: "center",
          flexWrap: "wrap",
          marginTop: "8px",
          fontSize: "12px",
        }}
      >
        <span>🔴 Maximum</span>
        <span>🔵 Mean</span>
        <span>🟢 Minimum</span>
      </div>
    </div>
  );
}

// ============================================================
// RAINFALL CHART
// ============================================================

function RainfallChart({
  dates = [],
  precipitation = [],
}) {
  if (!dates.length) {
    return <div className="chart-placeholder">📊</div>;
  }

  const width = 760;
  const height = 280;
  const paddingLeft = 48;
  const paddingRight = 20;
  const paddingTop = 24;
  const paddingBottom = 48;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const values = precipitation.map((value) =>
    typeof value === "number" ? value : 0
  );

  const maxRain = Math.max(...values, 1);

  const barWidth =
    dates.length > 0
      ? Math.max(
          3,
          Math.min(
            18,
            (chartWidth / dates.length) * 0.65
          )
        )
      : 8;

  const labelStep = Math.max(
    1,
    Math.ceil(dates.length / 7)
  );

  return (
    <div className="rainfall-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        role="img"
        aria-label="Historical rainfall trend"
      >
        <line
          x1={paddingLeft}
          y1={paddingTop + chartHeight}
          x2={width - paddingRight}
          y2={paddingTop + chartHeight}
          stroke="#cbd5e1"
          strokeWidth="1"
        />

        {values.map((value, index) => {
          const slotWidth =
            chartWidth / Math.max(dates.length, 1);

          const x =
            paddingLeft +
            index * slotWidth +
            (slotWidth - barWidth) / 2;

          const barHeight =
            (value / maxRain) * chartHeight;

          const y =
            paddingTop +
            chartHeight -
            barHeight;

          return (
            <rect
              key={index}
              x={x}
              y={y}
              width={barWidth}
              height={Math.max(barHeight, 1)}
              rx="2"
              fill="#3b82f6"
              opacity="0.75"
            />
          );
        })}

        {[0, 0.5, 1].map((ratio, index) => {
          const value = maxRain * ratio;

          const y =
            paddingTop +
            chartHeight -
            chartHeight * ratio;

          return (
            <g key={index}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
              />

              <text
                x="8"
                y={y + 4}
                fontSize="11"
                fill="#64748b"
              >
                {value.toFixed(0)} mm
              </text>
            </g>
          );
        })}

        {dates.map((date, index) => {
          if (
            index % labelStep !== 0 &&
            index !== dates.length - 1
          ) {
            return null;
          }

          const slotWidth =
            chartWidth / Math.max(dates.length, 1);

          const x =
            paddingLeft +
            index * slotWidth +
            slotWidth / 2;

          return (
            <text
              key={date}
              x={x}
              y={height - 14}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {formatShortDate(date)}
            </text>
          );
        })}
      </svg>
    </div>
  );
}

// ============================================================
// CLIMATE STATISTICS
// ============================================================

function calculateClimateStats(climate) {
  if (!climate?.daily) {
    return null;
  }

  const mean = climate.daily.mean_temperature || [];
  const max = climate.daily.max_temperature || [];
  const min = climate.daily.min_temperature || [];
  const rainfall = climate.daily.precipitation || [];

  const validMean = mean.filter(
    (value) => typeof value === "number"
  );

  const validMax = max.filter(
    (value) => typeof value === "number"
  );

  const validMin = min.filter(
    (value) => typeof value === "number"
  );

  const validRain = rainfall.filter(
    (value) => typeof value === "number"
  );

  const average = validMean.length
    ? validMean.reduce((sum, value) => sum + value, 0) /
      validMean.length
    : 0;

  const highest = validMax.length
    ? Math.max(...validMax)
    : 0;

  const lowest = validMin.length
    ? Math.min(...validMin)
    : 0;

  const totalRain = validRain.length
    ? validRain.reduce((sum, value) => sum + value, 0)
    : 0;

  return {
    average,
    highest,
    lowest,
    totalRain,
  };
}

// ============================================================
// MAIN APP
// ============================================================

function App() {
  const [page, setPage] = useState("dashboard");

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  // ==========================================================
  // CHAT LOCATION + SESSION
  // ==========================================================

  const [chatLocation, setChatLocation] = useState("Delhi");
  const [customLocation, setCustomLocation] = useState("");
  const [showLocationPicker, setShowLocationPicker] = useState(false);

  const [chatLoading, setChatLoading] = useState(false);

  const sessionIdRef = useRef(
    `weathergpt-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 10)}`
  );

  // ==========================================================
  // VOICE INTERACTION
  // ==========================================================

  const [isListening, setIsListening] = useState(false);
  const [speechLanguage, setSpeechLanguage] = useState("en-IN");
  const [voiceSupported, setVoiceSupported] = useState(true);
  const [speakingMessageIndex, setSpeakingMessageIndex] =
    useState(null);

  const voiceRecognitionRef = useRef(null);
  const voiceSessionActiveRef = useRef(false);
  const voiceTranscriptRef = useRef("");

  // ==========================================================
  // WEATHER
  // ==========================================================

  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(true);
  const [weatherError, setWeatherError] = useState(false);
  const [showForecastDetails, setShowForecastDetails] =
    useState(false);

  // ==========================================================
  // ALERTS
  // ==========================================================

  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertsError, setAlertsError] = useState(false);

  // ==========================================================
  // CLIMATE
  // ==========================================================

  const [climate, setClimate] = useState(null);
  const [climateLoading, setClimateLoading] = useState(false);
  const [climateError, setClimateError] = useState(false);

  // ==========================================================
  // ADVISORY
  // ==========================================================

  const [advisory, setAdvisory] = useState(null);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [advisoryError, setAdvisoryError] = useState(false);
  const [selectedSector, setSelectedSector] = useState(null);

  // ==========================================================
  // MAP
  // ==========================================================

  const [cities, setCities] = useState([]);
  const [citiesLoading, setCitiesLoading] = useState(false);
  const [citiesError, setCitiesError] = useState(false);

  // ==========================================================
  // FETCH WEATHER
  // ==========================================================

  useEffect(() => {
    async function fetchWeather() {
      try {
        setWeatherLoading(true);
        setWeatherError(false);

        const response = await fetch(
          `${API_BASE_URL}/api/weather`
        );

        if (!response.ok) {
          throw new Error("Weather request failed");
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(
            data.error || "Weather API failed"
          );
        }

        setWeather(data.current || null);
        setForecast(data.forecast || null);
        setWeatherLoading(false);
      } catch (error) {
        console.error("Weather fetch error:", error);
        setWeatherError(true);
        setWeatherLoading(false);
      }
    }

    fetchWeather();
  }, []);

  // ==========================================================
  // FETCH ALERTS
  // ==========================================================

  async function fetchAlerts() {
    try {
      setAlertsLoading(true);
      setAlertsError(false);

      const response = await fetch(
        `${API_BASE_URL}/api/alerts`
      );

      if (!response.ok) {
        throw new Error("Alerts request failed");
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error || "Alerts API failed"
        );
      }

      setAlerts(
        Array.isArray(data.alerts)
          ? data.alerts
          : []
      );

      setAlertsLoading(false);
    } catch (error) {
      console.error("Alerts fetch error:", error);
      setAlerts([]);
      setAlertsError(true);
      setAlertsLoading(false);
    }
  }

  useEffect(() => {
    fetchAlerts();
  }, []);

  // ==========================================================
  // FETCH CLIMATE
  // ==========================================================

  useEffect(() => {
    if (page !== "climate") {
      return;
    }

    async function fetchClimate() {
      try {
        setClimateLoading(true);
        setClimateError(false);

        const response = await fetch(
          `${API_BASE_URL}/api/climate`
        );

        if (!response.ok) {
          throw new Error("Climate request failed");
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(
            data.error || "Climate API failed"
          );
        }

        setClimate(data);
        setClimateLoading(false);
      } catch (error) {
        console.error("Climate fetch error:", error);
        setClimateError(true);
        setClimateLoading(false);
      }
    }

    fetchClimate();
  }, [page]);

  // ==========================================================
  // FETCH ADVISORY
  // ==========================================================

  useEffect(() => {
    if (page !== "advisory") {
      return;
    }

    async function fetchAdvisory() {
      try {
        setAdvisoryLoading(true);
        setAdvisoryError(false);

        const response = await fetch(
          `${API_BASE_URL}/api/advisory?location=${encodeURIComponent(
            chatLocation
          )}`
        );

        if (!response.ok) {
          throw new Error("Advisory request failed");
        }

        const data = await response.json();

        if (!data.success) {
          throw new Error(
            data.error || "Advisory API failed"
          );
        }

        setAdvisory(data);
        setAdvisoryLoading(false);
      } catch (error) {
        console.error("Advisory fetch error:", error);
        setAdvisoryError(true);
        setAdvisoryLoading(false);
      }
    }

    fetchAdvisory();
  }, [page, chatLocation]);

  // ==========================================================
  // FETCH CITY WEATHER FOR MAP
  // ==========================================================

  useEffect(() => {
    if (page !== "map") {
      return;
    }

    async function fetchCities() {
      try {
        setCitiesLoading(true);
        setCitiesError(false);

        const response = await fetch(
          `${API_BASE_URL}/api/weather/cities`
        );

        if (!response.ok) {
          throw new Error(
            "City weather request failed"
          );
        }

        const data = await response.json();

        if (Array.isArray(data)) {
          setCities(data);
        } else if (Array.isArray(data.cities)) {
          setCities(data.cities);
        } else {
          setCities([]);
        }

        setCitiesLoading(false);
      } catch (error) {
        console.error(
          "City weather fetch error:",
          error
        );

        setCitiesError(true);
        setCitiesLoading(false);
      }
    }

    fetchCities();
  }, [page]);

  // ==========================================================
  // VOICE INPUT
  // ==========================================================

  function startVoiceInput() {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setVoiceSupported(false);
      return;
    }

    if (isListening) {
      stopVoiceInput();
      return;
    }

    voiceSessionActiveRef.current = true;
    voiceTranscriptRef.current = "";

    let restartTimer = null;
    let isStarting = false;

    const createRecognition = () => {
      if (!voiceSessionActiveRef.current) {
        return;
      }

      if (isStarting) {
        return;
      }

      isStarting = true;

      const recognition = new SpeechRecognition();
      voiceRecognitionRef.current = recognition;

      recognition.lang = speechLanguage;
      recognition.interimResults = true;
      recognition.continuous = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        isStarting = false;
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        let finalTranscript =
          voiceTranscriptRef.current;

        let interimTranscript = "";

        for (
          let i = event.resultIndex;
          i < event.results.length;
          i += 1
        ) {
          const result = event.results[i];
          const transcript =
            result?.[0]?.transcript || "";

          if (result.isFinal) {
            finalTranscript += `${transcript} `;
          } else {
            interimTranscript += transcript;
          }
        }

        voiceTranscriptRef.current =
          finalTranscript.trim();

        const displayTranscript = [
          voiceTranscriptRef.current,
          interimTranscript.trim(),
        ]
          .filter(Boolean)
          .join(" ");

        if (displayTranscript) {
          setMessage(displayTranscript);
        }
      };

      recognition.onerror = (event) => {
        console.error(
          "Voice recognition error:",
          event.error
        );

        if (
          event.error === "not-allowed" ||
          event.error === "service-not-allowed" ||
          event.error === "audio-capture"
        ) {
          voiceSessionActiveRef.current = false;
          setIsListening(false);
          setVoiceSupported(false);
        }
      };

      recognition.onend = () => {
        isStarting = false;

        if (voiceSessionActiveRef.current) {
          setIsListening(true);

          if (restartTimer) {
            clearTimeout(restartTimer);
          }

          restartTimer = setTimeout(() => {
            restartTimer = null;

            if (voiceSessionActiveRef.current) {
              createRecognition();
            }
          }, 250);

          return;
        }

        setIsListening(false);

        if (voiceRecognitionRef.current === recognition) {
          voiceRecognitionRef.current = null;
        }

        const transcript =
          voiceTranscriptRef.current.trim();

        if (transcript) {
          setMessage("");
          sendMessage(transcript);
        }

        voiceTranscriptRef.current = "";
      };

      try {
        recognition.start();
      } catch (error) {
        isStarting = false;

        console.error(
          "Could not start voice recognition:",
          error
        );

        if (voiceSessionActiveRef.current) {
          if (restartTimer) {
            clearTimeout(restartTimer);
          }

          restartTimer = setTimeout(() => {
            restartTimer = null;

            if (voiceSessionActiveRef.current) {
              createRecognition();
            }
          }, 350);
        }
      }
    };

    createRecognition();
  }

  function stopVoiceInput() {
    voiceSessionActiveRef.current = false;

    const recognition =
      voiceRecognitionRef.current;

    if (recognition) {
      try {
        recognition.stop();
      } catch (error) {
        console.error(
          "Could not stop voice recognition:",
          error
        );

        setIsListening(false);

        const transcript =
          voiceTranscriptRef.current.trim();

        if (transcript) {
          setMessage("");
          sendMessage(transcript);
        }

        voiceTranscriptRef.current = "";
        voiceRecognitionRef.current = null;
      }
    } else {
      setIsListening(false);

      const transcript =
        voiceTranscriptRef.current.trim();

      if (transcript) {
        setMessage("");
        sendMessage(transcript);
      }

      voiceTranscriptRef.current = "";
    }
  }

  // ==========================================================
  // VOICE OUTPUT
  // ==========================================================

  function speakText(text, index = null) {
    if (!window.speechSynthesis) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance =
      new SpeechSynthesisUtterance(text);

    utterance.lang = speechLanguage;
    utterance.rate = 0.95;
    utterance.pitch = 1;

    utterance.onstart = () => {
      setSpeakingMessageIndex(index);
    };

    utterance.onend = () => {
      setSpeakingMessageIndex(null);
    };

    utterance.onerror = () => {
      setSpeakingMessageIndex(null);
    };

    window.speechSynthesis.speak(utterance);
  }

  // ==========================================================
  // CHAT LOCATION
  // ==========================================================

  function applyCustomLocation() {
    const value = customLocation.trim();

    if (!value) {
      return;
    }

    setChatLocation(value);
    setCustomLocation("");
    setShowLocationPicker(false);
  }

  function selectLocation(location) {
    setChatLocation(location);
    setShowLocationPicker(false);
  }

  // ==========================================================
  // CHAT
  // ==========================================================

  async function sendMessage(messageOverride = null) {
    const userMessage =
      (messageOverride ?? message).trim();

    if (!userMessage || chatLoading) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: userMessage,
        location: chatLocation,
      },
    ]);

    setMessage("");
    setChatLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userMessage,
            location: chatLocation,
            session_id: sessionIdRef.current,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          "Chat request failed"
        );
      }

      const data = await response.json();

      const reply =
        data.reply ||
        data.response ||
        "No response received.";

      if (data.session_id) {
        sessionIdRef.current =
          data.session_id;
      }

      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: reply,
          location: chatLocation,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text:
            "Could not connect to the WeatherGPT backend.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  // ==========================================================
  // CLEAR CHAT
  // ==========================================================

  async function clearChat() {
    try {
      await fetch(
        `${API_BASE_URL}/api/chat/clear`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionIdRef.current,
          }),
        }
      );
    } catch (error) {
      console.error(
        "Could not clear backend chat memory:",
        error
      );
    }

    setMessages([]);
    setMessage("");

    sessionIdRef.current =
      `weathergpt-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 10)}`;
  }

  function askSuggestion(question) {
    setMessage(question);
  }

  // ==========================================================
  // WEATHER SUMMARY
  // ==========================================================

  const currentTemperature =
    weather?.temperature;

  const apparentTemperature =
    weather?.apparent_temperature;

  const humidity =
    weather?.humidity;

  const windSpeed =
    weather?.wind_speed;

  const weatherCode =
    weather?.weather_code;

  // ==========================================================
  // CLIMATE DATA
  // ==========================================================

  const climateStats =
    calculateClimateStats(climate);

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div
      className="app"
      data-weather={
        weatherLoading || weatherError
          ? "default"
          : getWeatherTheme(weatherCode)
      }
    >

      {/* ================================================== */}
      {/* TOP BAR */}
      {/* ================================================== */}

      <header className="topbar">

        <div className="logo">
          <span>☁️</span>

          <div>
            <h2>WeatherGPT</h2>

            <p>
              AI Weather Intelligence
            </p>
          </div>
        </div>

        <div className="top-actions">

          <button
            onClick={() =>
              setSpeechLanguage(
                speechLanguage === "en-IN"
                  ? "hi-IN"
                  : "en-IN"
              )
            }
          >
            🌐{" "}
            {speechLanguage === "en-IN"
              ? "English"
              : "Hindi"}
          </button>

          <button
            onClick={() => {
              setPage("chat");
              setShowLocationPicker(
                !showLocationPicker
              );
            }}
          >
            📍 {chatLocation}
          </button>

        </div>

      </header>

      {/* ================================================== */}
      {/* LOCATION PICKER */}
      {/* ================================================== */}

      {showLocationPicker && (
        <div
          style={{
            maxWidth: "1200px",
            margin: "12px auto 0",
            padding: "14px 18px",
            background: "white",
            border: "1px solid #e2e8f0",
            borderRadius: "14px",
            boxShadow:
              "0 8px 25px rgba(15,23,42,0.08)",
            position: "relative",
            zIndex: 20,
          }}
        >

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "12px",
              flexWrap: "wrap",
            }}
          >

            <div>
              <strong>
                📍 WeatherGPT chat location
              </strong>

              <p
                style={{
                  margin: "4px 0 0",
                  fontSize: "12px",
                  color: "#64748b",
                }}
              >
                Choose a city or enter any
                location supported by the
                weather backend.
              </p>
            </div>

            <div
              style={{
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
              }}
            >

              {LOCATION_OPTIONS.map(
                (location) => (
                  <button
                    key={location}
                    onClick={() =>
                      selectLocation(location)
                    }
                    style={{
                      border:
                        location === chatLocation
                          ? "1px solid #2563eb"
                          : "1px solid #e2e8f0",
                      background:
                        location === chatLocation
                          ? "#eff6ff"
                          : "white",
                      color:
                        location === chatLocation
                          ? "#1d4ed8"
                          : "#334155",
                      borderRadius: "9px",
                      padding:
                        "7px 10px",
                      cursor: "pointer",
                      fontSize: "12px",
                    }}
                  >
                    {location}
                  </button>
                )
              )}

            </div>

          </div>

          <div
            style={{
              display: "flex",
              gap: "8px",
              marginTop: "12px",
              maxWidth: "500px",
            }}
          >

            <input
              value={customLocation}
              onChange={(e) =>
                setCustomLocation(
                  e.target.value
                )
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  applyCustomLocation();
                }
              }}
              placeholder="Or enter a location, e.g. Jaipur"
              style={{
                flex: 1,
                border:
                  "1px solid #e2e8f0",
                borderRadius: "9px",
                padding: "9px 11px",
                outline: "none",
              }}
            />

            <button
              onClick={applyCustomLocation}
              style={{
                border: "none",
                background: "#2563eb",
                color: "white",
                borderRadius: "9px",
                padding: "9px 14px",
                cursor: "pointer",
              }}
            >
              Use Location
            </button>

          </div>

        </div>
      )}

      {/* ================================================== */}
      {/* NAVIGATION */}
      {/* ================================================== */}

      <nav className="navigation">

        <button
          className={
            page === "dashboard"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("dashboard")
          }
        >
          🏠 Dashboard
        </button>

        <button
          className={
            page === "chat"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("chat")
          }
        >
          🤖 WeatherGPT
        </button>

        <button
          className={
            page === "alerts"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("alerts")
          }
        >
          ⚠️ Alerts
        </button>

        <button
          className={
            page === "map"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("map")
          }
        >
          🗺️ Map
        </button>

        <button
          className={
            page === "climate"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("climate")
          }
        >
          📊 Climate
        </button>

        <button
          className={
            page === "advisory"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("advisory")
          }
        >
          🌾 Advisory
        </button>

      </nav>

      {/* ================================================== */}
      {/* DASHBOARD */}
      {/* ================================================== */}

      {page === "dashboard" && (
        <main className="dashboard">

          <section className="welcome">

            <div>

              <p className="small-text">
                WEATHER INTELLIGENCE
              </p>

              <h1>
                Weather intelligence,{" "}
                <span>
                  simplified.
                </span>
              </h1>

              <p>
                Ask WeatherGPT about
                forecasts, alerts,
                climate and
                location-based
                weather information.
              </p>

            </div>

            <div className="weather-main">

              <div className="weather-icon">
                {weatherLoading
                  ? "🌤️"
                  : weatherError
                  ? "❓"
                  : getWeatherIcon(
                      weatherCode
                    )}
              </div>

              <div>

                <strong>
                  {weatherLoading
                    ? "..."
                    : weatherError
                    ? "--"
                    : `${currentTemperature}°C`}
                </strong>

                <p>
                  {weatherLoading
                    ? "Loading weather..."
                    : weatherError
                    ? "Weather unavailable"
                    : getWeatherDescription(
                        weatherCode
                      )}
                </p>

                <small
                  style={{
                    color: "#64748b",
                  }}
                >
                  📍 Delhi
                </small>

              </div>

            </div>

          </section>

          <section className="stats">

            <div className="stat-card">
              <p>Feels Like</p>

              <h2>
                {weatherLoading
                  ? "..."
                  : weatherError
                  ? "--"
                  : `${apparentTemperature}°C`}
              </h2>

              <span>
                Real-time data
              </span>
            </div>

            <div className="stat-card">
              <p>Humidity</p>

              <h2>
                {weatherLoading
                  ? "..."
                  : weatherError
                  ? "--"
                  : `${humidity}%`}
              </h2>

              <span>
                Current humidity
              </span>
            </div>

            <div className="stat-card">
              <p>Wind</p>

              <h2>
                {weatherLoading
                  ? "..."
                  : weatherError
                  ? "--"
                  : `${windSpeed} km/h`}
              </h2>

              <span>
                Current wind speed
              </span>
            </div>

            <div className="stat-card">
              <p>Precipitation</p>

              <h2>
                {weatherLoading
                  ? "..."
                  : weatherError
                  ? "--"
                  : `${weather?.precipitation ?? 0} mm`}
              </h2>

              <span>
                Current rainfall
              </span>
            </div>

          </section>

          <section className="content-grid">

            <div className="forecast-card">

              <div className="card-header">

                <div>
                  <h2>
                    7-Day Forecast
                  </h2>

                  <p>
                    Daily weather conditions
                  </p>
                </div>

                <button
                  onClick={() =>
                    setShowForecastDetails(
                      !showForecastDetails
                    )
                  }
                >
                  {showForecastDetails
                    ? "Hide Details ↑"
                    : "View Details →"}
                </button>

              </div>

              <div className="forecast">

                {forecast?.dates?.map(
                  (date, index) => {

                    const day =
                      new Date(
                        date + "T12:00:00"
                      ).toLocaleDateString(
                        "en-IN",
                        {
                          weekday: "short",
                        }
                      );

                    const code =
                      forecast.weather_code[
                        index
                      ];

                    const maxTemp =
                      Math.round(
                        forecast.max_temperature[
                          index
                        ]
                      );

                    const minTemp =
                      Math.round(
                        forecast.min_temperature[
                          index
                        ]
                      );

                    return (
                      <div key={date}>

                        <span>
                          {index === 0
                            ? "Today"
                            : day}
                        </span>

                        <b>
                          {getWeatherIcon(
                            code
                          )}
                        </b>

                        <strong>
                          {maxTemp}° /{" "}
                          {minTemp}°
                        </strong>

                      </div>
                    );
                  }
                )}

                {!forecast &&
                  !weatherError && (
                    <div>
                      <span>Loading</span>
                      <b>🌤️</b>
                      <strong>...</strong>
                    </div>
                  )}

              </div>

              {showForecastDetails &&
                forecast?.dates && (
                  <div className="forecast-details">

                    {forecast.dates.map(
                      (date, index) => {

                        const day =
                          new Date(
                            date + "T12:00:00"
                          ).toLocaleDateString(
                            "en-IN",
                            {
                              weekday:
                                "long",
                              day: "numeric",
                              month: "short",
                            }
                          );

                        const code =
                          forecast.weather_code[
                            index
                          ];

                        return (
                          <div
                            className="forecast-detail-row"
                            key={date}
                          >

                            <div className="detail-day">
                              <strong>
                                {index === 0
                                  ? "Today"
                                  : day}
                              </strong>
                            </div>

                            <div className="detail-icon">
                              {getWeatherIcon(
                                code
                              )}
                            </div>

                            <div className="detail-temp">
                              <span>
                                High
                              </span>

                              <strong>
                                {Math.round(
                                  forecast
                                    .max_temperature[
                                    index
                                  ]
                                )}
                                °C
                              </strong>
                            </div>

                            <div className="detail-temp">
                              <span>
                                Low
                              </span>

                              <strong>
                                {Math.round(
                                  forecast
                                    .min_temperature[
                                    index
                                  ]
                                )}
                                °C
                              </strong>
                            </div>

                          </div>
                        );
                      }
                    )}

                  </div>
                )}

            </div>

            <div className="alert-card">

              <div className="card-header">

                <div>
                  <h2>
                    Weather Alerts
                  </h2>

                  <p>
                    Live WeatherGPT analysis
                  </p>
                </div>

                <span className="alert-badge">
                  LIVE
                </span>

              </div>

              {alertsLoading && (
                <div className="alert">
                  <div className="alert-symbol">
                    ⏳
                  </div>

                  <div>
                    <h3>
                      Checking weather alerts
                    </h3>

                    <p>
                      WeatherGPT is analyzing
                      the latest forecast data.
                    </p>
                  </div>
                </div>
              )}

              {!alertsLoading &&
                alertsError && (
                  <div className="alert">
                    <div className="alert-symbol">
                      ⚠️
                    </div>

                    <div>
                      <h3>
                        Alerts unavailable
                      </h3>

                      <p>
                        Could not connect to
                        the weather alert service.
                      </p>
                    </div>
                  </div>
                )}

              {!alertsLoading &&
                !alertsError &&
                alerts.length === 0 && (
                  <div className="alert">
                    <div className="alert-symbol">
                      🟢
                    </div>

                    <div>
                      <h3>
                        No significant alerts
                      </h3>

                      <p>
                        No significant weather
                        conditions currently
                        meet WeatherGPT's
                        alert thresholds.
                      </p>
                    </div>
                  </div>
                )}

              {!alertsLoading &&
                !alertsError &&
                alerts.length > 0 && (
                  <div className="alert">
                    <div className="alert-symbol">
                      {getAlertEmoji(
                        alerts[0].level
                      )}
                    </div>

                    <div>
                      <h3>
                        {alerts[0].title}
                      </h3>

                      <p>
                        {alerts[0].description}
                      </p>
                    </div>
                  </div>
                )}

              <button
                className="explain-button"
                onClick={() =>
                  setPage("alerts")
                }
              >
                View All Alerts →
              </button>

            </div>

          </section>

          <section className="chat-card">

            <div className="chat-icon">
              🤖
            </div>

            <div className="chat-content">

              <p className="small-text">
                WEATHERGPT AI
              </p>

              <h2>
                Ask anything about the weather
              </h2>

              <p>
                Current chat location:{" "}
                <strong>
                  {chatLocation}
                </strong>
                . Ask questions about
                forecasts, alerts, climate
                or weather conditions.
              </p>

            </div>

            <button
              className="chat-button"
              onClick={() =>
                setPage("chat")
              }
            >
              Open WeatherGPT →
            </button>

          </section>

        </main>
      )}

      {/* ================================================== */}
      {/* CHAT */}
      {/* ================================================== */}

      {page === "chat" && (
        <section className="chat-page">

          <div className="chat-header">

            <div>

              <p className="small-text">
                WEATHERGPT AI
              </p>

              <h1>
                How can I help with the weather?
              </h1>

              <p>
                Ask about forecasts,
                weather alerts, climate
                and location-based conditions.
              </p>

              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  marginTop: "10px",
                  padding: "7px 11px",
                  borderRadius: "999px",
                  background: "#eff6ff",
                  color: "#1d4ed8",
                  fontSize: "12px",
                  fontWeight: 600,
                }}
              >
                📍 Chat location: {chatLocation}
              </div>

            </div>

            <div className="ai-status">
              ● AI ONLINE
            </div>

          </div>

          {/* CHAT CONTROLS */}

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: "8px",
              marginBottom: "12px",
              flexWrap: "wrap",
            }}
          >

            <button
              onClick={() =>
                setShowLocationPicker(
                  !showLocationPicker
                )
              }
              style={{
                border:
                  "1px solid #e2e8f0",
                background: "white",
                borderRadius: "9px",
                padding: "8px 12px",
                cursor: "pointer",
                color: "#334155",
                fontSize: "12px",
              }}
            >
              📍 Change Location
            </button>

            <button
              onClick={clearChat}
              disabled={
                chatLoading ||
                messages.length === 0
              }
              style={{
                border:
                  "1px solid #fecaca",
                background:
                  messages.length === 0
                    ? "#f8fafc"
                    : "#fff5f5",
                color:
                  messages.length === 0
                    ? "#94a3b8"
                    : "#dc2626",
                borderRadius: "9px",
                padding: "8px 12px",
                cursor:
                  messages.length === 0
                    ? "not-allowed"
                    : "pointer",
                fontSize: "12px",
              }}
            >
              🗑️ Clear Chat
            </button>

          </div>

          {/* SUGGESTIONS */}

          <div className="suggestions">

            <button
              onClick={() =>
                askSuggestion(
                  "Will it rain tomorrow?"
                )
              }
            >
              🌧️ Will it rain tomorrow?
            </button>

            <button
              onClick={() =>
                askSuggestion(
                  "What is today's temperature?"
                )
              }
            >
              🌡️ Today's temperature
            </button>

            <button
              onClick={() =>
                askSuggestion(
                  "Are there any weather alerts?"
                )
              }
            >
              ⚠️ Weather alerts
            </button>

            <button
              onClick={() =>
                askSuggestion(
                  "Give me farming weather advice"
                )
              }
            >
              🌾 Farming weather advice
            </button>

          </div>

          {/* CHAT WINDOW */}

          <div className="chat-window">

            {messages.length === 0 && (
              <div className="bot-message">

                <div className="message-avatar">
                  🤖
                </div>

                <div>
                  <strong>
                    WeatherGPT
                  </strong>

                  <p>
                    Hello! Ask me anything
                    about the weather in{" "}
                    <strong>
                      {chatLocation}
                    </strong>
                    . You can ask about
                    forecasts, alerts, climate
                    information or weather
                    conditions for another
                    location.
                  </p>
                </div>

              </div>
            )}

            {messages.map(
              (msg, index) => (
                <div
                  key={index}
                  className={
                    msg.type === "user"
                      ? "user-message"
                      : "bot-message"
                  }
                >

                  <div className="message-avatar">
                    {msg.type === "user"
                      ? "👤"
                      : "🤖"}
                  </div>

                  <div>

                    <strong>
                      {msg.type === "user"
                        ? "You"
                        : "WeatherGPT"}
                    </strong>

                    {msg.location && (
                      <div
                        style={{
                          fontSize: "10px",
                          color: "#94a3b8",
                          marginTop: "2px",
                        }}
                      >
                        📍 {msg.location}
                      </div>
                    )}

                    <p>
                      {msg.text}
                    </p>

                    {msg.type === "bot" && (
                      <button
                        onClick={() =>
                          speakText(
                            msg.text,
                            index
                          )
                        }
                        title="Read this answer aloud"
                        style={{
                          marginTop: "6px",
                          border: "none",
                          background:
                            "transparent",
                          cursor: "pointer",
                          padding: "2px 4px",
                          fontSize: "15px",
                        }}
                      >
                        {speakingMessageIndex ===
                        index
                          ? "🔊"
                          : "🔈"}
                      </button>
                    )}

                  </div>

                </div>
              )
            )}

            {chatLoading && (
              <div className="bot-message">

                <div className="message-avatar">
                  🤖
                </div>

                <div>

                  <strong>
                    WeatherGPT
                  </strong>

                  <p
                    style={{
                      color: "#64748b",
                    }}
                  >
                    <span>Thinking</span>
                    <span> • </span>
                    <span>Weather data is being analyzed...</span>
                  </p>

                </div>

              </div>
            )}

          </div>

          {/* CHAT INPUT */}

          <div className="chat-input-area">

            <input
              type="text"
              value={message}
              disabled={chatLoading}
              onChange={(e) =>
                setMessage(
                  e.target.value
                )
              }
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey
                ) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder={
                chatLoading
                  ? "WeatherGPT is thinking..."
                  : `Ask about the weather in ${chatLocation}...`
              }
            />

            <select
              value={speechLanguage}
              disabled={chatLoading}
              onChange={(e) =>
                setSpeechLanguage(
                  e.target.value
                )
              }
              aria-label="Voice language"
              style={{
                border:
                  "1px solid #e2e8f0",
                borderRadius: "10px",
                padding: "8px",
                background: "white",
                color: "#334155",
                fontSize: "12px",
              }}
            >
              <option value="en-IN">
                🇮🇳 English
              </option>

              <option value="hi-IN">
                🇮🇳 Hindi
              </option>
            </select>

            <button
              onClick={startVoiceInput}
              disabled={
                !voiceSupported ||
                chatLoading
              }
              title={
                voiceSupported
                  ? isListening
                    ? "Stop voice input and send the question"
                    : "Speak to WeatherGPT"
                  : "Voice recognition is not supported in this browser"
              }
              style={{
                minWidth: "44px",
                background:
                  isListening
                    ? "#fee2e2"
                    : "white",
                border:
                  "1px solid #e2e8f0",
                borderRadius: "10px",
                cursor:
                  voiceSupported &&
                  !chatLoading
                    ? "pointer"
                    : "not-allowed",
                opacity:
                  voiceSupported &&
                  !chatLoading
                    ? 1
                    : 0.55,
              }}
            >
              {isListening
                ? "⏹️"
                : "🎤"}
            </button>

            <button
              className="send-button"
              disabled={
                chatLoading ||
                !message.trim()
              }
              onClick={() =>
                sendMessage()
              }
            >
              ➤
            </button>

          </div>

          <div
            style={{
              marginTop: "10px",
              fontSize: "12px",
              color: "#64748b",
            }}
          >
            {isListening
              ? "🎙️ Listening... You can speak for longer. Press ⏹️ when you finish."
              : voiceSupported
              ? `🎤 Voice mode: speak your full question, then press ⏹️ to send it. Current location: ${chatLocation}.`
              : "⚠️ Voice input is not supported by this browser. Try Chrome or Edge."}
          </div>

          <p className="demo-note">
            LIVE WEATHER DATA • WeatherGPT
            uses the FastAPI backend,
            Gemini/Gemma AI and Open-Meteo
            weather data.
          </p>

        </section>
      )}

      {/* ================================================== */}
      {/* ALERTS */}
      {/* ================================================== */}

      {page === "alerts" && (
        <section className="feature-page">

          <div className="feature-heading">

            <span>⚠️</span>

            <div>

              <p className="small-text">
                SAFETY & WARNINGS
              </p>

              <h1>
                Weather Alerts
              </h1>

              <p>
                Monitor weather conditions
                and understand recommended
                precautions.
              </p>

            </div>

          </div>

          {alertsLoading && (
            <div className="alert-large">

              <div className="alert-level">
                ⏳ CHECKING
              </div>

              <h2>
                Checking current weather
                conditions
              </h2>

              <p>
                WeatherGPT is retrieving the
                latest forecast data and
                evaluating configured weather
                alert thresholds.
              </p>

            </div>
          )}

          {!alertsLoading &&
            alertsError && (
              <div className="alert-large">

                <div className="alert-level">
                  ⚠️ UNAVAILABLE
                </div>

                <h2>
                  Weather alerts could not be loaded
                </h2>

                <p>
                  The WeatherGPT backend could
                  not be reached. Make sure the
                  FastAPI server is running.
                </p>

                <button
                  className="explain-button"
                  onClick={fetchAlerts}
                >
                  Retry →
                </button>

              </div>
            )}

          {!alertsLoading &&
            !alertsError &&
            alerts.length === 0 && (
              <div className="alert-large">

                <div className="alert-level">
                  🟢 GREEN
                </div>

                <h2>
                  No significant weather alert
                </h2>

                <p>
                  No current or forecast
                  weather condition has
                  crossed WeatherGPT's
                  configured alert thresholds
                  for Delhi.
                </p>

                <div
                  style={{
                    marginTop: "18px",
                    padding: "14px",
                    borderRadius: "12px",
                    background: "#f8fafc",
                    color: "#64748b",
                    fontSize: "13px",
                  }}
                >
                  Source: Open-Meteo
                  <br />
                  WeatherGPT-generated
                  analysis — not an official
                  government warning.
                </div>

              </div>
            )}

          {!alertsLoading &&
            !alertsError &&
            alerts.length > 0 && (
              <div
                style={{
                  display: "grid",
                  gap: "18px",
                }}
              >

                {alerts.map(
                  (alert, index) => {

                    const level =
                      String(
                        alert.level ||
                          "GREEN"
                      ).toUpperCase();

                    return (
                      <div
                        className={`alert-large ${getAlertClass(
                          level
                        )}`}
                        key={`${alert.title}-${index}`}
                      >

                        <div className="alert-level">
                          {getAlertEmoji(level)}{" "}
                          {level}
                        </div>

                        <h2>
                          {alert.title ||
                            "Weather Alert"}
                        </h2>

                        <p>
                          {alert.description ||
                            "Weather conditions require attention."}
                        </p>

                        <div
                          style={{
                            display: "grid",
                            gap: "8px",
                            marginTop: "16px",
                          }}
                        >

                          {alert.location && (
                            <div>
                              <strong>
                                📍 Location:
                              </strong>{" "}
                              {alert.location}
                            </div>
                          )}

                          {alert.time && (
                            <div>
                              <strong>
                                🕐 Time:
                              </strong>{" "}
                              {alert.time}
                            </div>
                          )}

                          {alert.source && (
                            <div>
                              <strong>
                                📊 Source:
                              </strong>{" "}
                              {alert.source}
                            </div>
                          )}

                        </div>

                        {Array.isArray(
                          alert.precautions
                        ) &&
                          alert.precautions.length >
                            0 && (
                            <div
                              style={{
                                marginTop:
                                  "18px",
                              }}
                            >

                              <h3>
                                Recommended precautions
                              </h3>

                              <ul
                                style={{
                                  paddingLeft:
                                    "20px",
                                }}
                              >

                                {alert.precautions.map(
                                  (
                                    precaution,
                                    precautionIndex
                                  ) => (
                                    <li
                                      key={
                                        precautionIndex
                                      }
                                      style={{
                                        marginBottom:
                                          "6px",
                                      }}
                                    >
                                      {precaution}
                                    </li>
                                  )
                                )}

                              </ul>

                            </div>
                          )}

                        <div
                          style={{
                            marginTop: "18px",
                            padding: "12px 14px",
                            borderRadius: "10px",
                            background:
                              "rgba(255,255,255,0.65)",
                            fontSize: "12px",
                            color: "#475569",
                          }}
                        >
                          ⚠️ WeatherGPT-generated
                          analysis based on
                          available weather data.
                          This is not an official
                          government warning.
                        </div>

                      </div>
                    );
                  }
                )}

              </div>
            )}

        </section>
      )}

      {/* ================================================== */}
      {/* MAP */}
      {/* ================================================== */}

      {page === "map" && (
        <section className="feature-page">

          <div className="feature-heading">

            <span>🗺️</span>

            <div>

              <p className="small-text">
                GIS WEATHER VIEW
              </p>

              <h1>
                Interactive Weather Map
              </h1>

              <p>
                Explore weather conditions
                by location.
              </p>

            </div>

          </div>

          <div
            className="map-frame"
            style={{
              borderRadius: "18px",
              overflow: "hidden",
              border: "1px solid #e5e7eb",
              position: "relative",
            }}
          >

            <MapContainer
              center={[
                28.6139,
                77.209,
              ]}
              zoom={10}
              scrollWheelZoom={true}
              style={{
                height: "100%",
                width: "100%",
              }}
            >

              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <Marker
                position={[
                  28.6139,
                  77.209,
                ]}
              >
                <Popup>

                  <strong>
                    Delhi
                  </strong>

                  <br />

                  WeatherGPT monitoring
                  location.

                  <br />

                  Live weather data from
                  Open-Meteo.

                </Popup>
              </Marker>

              {cities.map(
                (city, index) => {

                  const latitude =
                    city.latitude ??
                    city.lat;

                  const longitude =
                    city.longitude ??
                    city.lon ??
                    city.lng;

                  if (
                    typeof latitude !==
                      "number" ||
                    typeof longitude !==
                      "number"
                  ) {
                    return null;
                  }

                  return (
                    <Marker
                      key={
                        city.name ||
                        index
                      }
                      position={[
                        latitude,
                        longitude,
                      ]}
                    >

                      <Popup>

                        <strong>
                          {city.name ||
                            "Location"}
                        </strong>

                        <br />

                        Temperature:{" "}
                        {city.temperature ??
                          city.current_temperature ??
                          "--"}
                        °C

                        <br />

                        Humidity:{" "}
                        {city.humidity ??
                          "--"}
                        %

                      </Popup>

                    </Marker>
                  );
                }
              )}

            </MapContainer>

            {citiesLoading && (
              <div
                style={{
                  position: "absolute",
                  top: "14px",
                  right: "14px",
                  zIndex: 1000,
                  background: "white",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  boxShadow:
                    "0 2px 8px rgba(0,0,0,0.15)",
                  fontSize: "12px",
                }}
              >
                Loading city weather...
              </div>
            )}

          </div>

          <div
            style={{
              marginTop: "14px",
              padding: "14px 16px",
              background: "#f8fafc",
              borderRadius: "12px",
              color: "#64748b",
              fontSize: "12px",
            }}
          >
            🗺️ Map data uses OpenStreetMap
            for geographic visualization.
            Weather information is supplied
            by WeatherGPT's weather backend.
          </div>

        </section>
      )}

      {/* ================================================== */}
      {/* CLIMATE */}
      {/* ================================================== */}

      {page === "climate" && (
        <section className="feature-page">

          <div className="feature-heading">

            <span>📊</span>

            <div>

              <p className="small-text">
                CLIMATE INTELLIGENCE
              </p>

              <h1>
                Climate Analysis
              </h1>

              <p>
                Explore the last 30 days
                of historical weather and
                climate trends for Delhi.
              </p>

            </div>

          </div>

          {climateLoading && (
            <div className="climate-card">

              <h2>
                Loading climate data...
              </h2>

              <p>
                Retrieving historical weather
                information from the backend.
              </p>

            </div>
          )}

          {climateError && (
            <div className="climate-card">

              <h2>
                Climate data unavailable
              </h2>

              <p>
                Could not retrieve historical
                climate data from the backend.
              </p>

            </div>
          )}

          {!climateLoading &&
            !climateError &&
            climate && (
              <>

                {climateStats && (
                  <div className="stats">

                    <div className="stat-card">
                      <p>
                        30-Day Average
                      </p>

                      <h2>
                        {climateStats.average.toFixed(
                          1
                        )}
                        °C
                      </h2>

                      <span>
                        Mean temperature
                      </span>
                    </div>

                    <div className="stat-card">
                      <p>Highest</p>

                      <h2>
                        {climateStats.highest.toFixed(
                          1
                        )}
                        °C
                      </h2>

                      <span>
                        Maximum recorded
                      </span>
                    </div>

                    <div className="stat-card">
                      <p>Lowest</p>

                      <h2>
                        {climateStats.lowest.toFixed(
                          1
                        )}
                        °C
                      </h2>

                      <span>
                        Minimum recorded
                      </span>
                    </div>

                    <div className="stat-card">
                      <p>
                        Total Rainfall
                      </p>

                      <h2>
                        {climateStats.totalRain.toFixed(
                          1
                        )}{" "}
                        mm
                      </h2>

                      <span>
                        Daily precipitation
                      </span>
                    </div>

                  </div>
                )}

                <div className="climate-card">

                  <span>🌡️</span>

                  <h2>
                    Temperature Trend
                  </h2>

                  <p>
                    Daily maximum, mean and
                    minimum temperature
                  </p>

                  <TemperatureChart
                    dates={
                      climate.daily
                        ?.dates || []
                    }
                    maxTemperatures={
                      climate.daily
                        ?.max_temperature ||
                      []
                    }
                    meanTemperatures={
                      climate.daily
                        ?.mean_temperature ||
                      []
                    }
                    minTemperatures={
                      climate.daily
                        ?.min_temperature ||
                      []
                    }
                  />

                </div>

                <div className="climate-card">

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(180px, 1fr))",
                      gap: "20px",
                    }}
                  >

                    <div>
                      <p className="small-text">
                        ANALYSIS PERIOD
                      </p>

                      <strong>
                        {climate.period?.start ||
                          "—"}{" "}
                        →{" "}
                        {climate.period?.end ||
                          "—"}
                      </strong>
                    </div>

                    <div>
                      <p className="small-text">
                        LOCATION
                      </p>

                      <strong>
                        📍{" "}
                        {climate.location ||
                          "Delhi"}
                      </strong>
                    </div>

                    <div>
                      <p className="small-text">
                        DATA SOURCE
                      </p>

                      <strong>
                        Open-Meteo
                      </strong>
                    </div>

                  </div>

                  <p
                    style={{
                      marginTop: "18px",
                      fontSize: "12px",
                    }}
                  >
                    Historical weather data is
                    provided through the
                    Open-Meteo Historical
                    Weather API. This climate
                    analysis is informational
                    and is not an official
                    government warning or
                    forecast.
                  </p>

                </div>

                <div className="climate-card">

                  <span>🌧️</span>

                  <h2>
                    Rainfall Trend
                  </h2>

                  <p>
                    Daily precipitation over
                    the selected historical
                    period
                  </p>

                  <p className="small-text">
                    Daily precipitation in
                    millimetres (mm)
                  </p>

                  <RainfallChart
                    dates={
                      climate.daily
                        ?.dates || []
                    }
                    precipitation={
                      climate.daily
                        ?.precipitation ||
                      []
                    }
                  />

                </div>

              </>
            )}

        </section>
      )}

      {/* ================================================== */}
      {/* ADVISORY */}
      {/* ================================================== */}

      {page === "advisory" && (
        <section className="feature-page">

          <div className="feature-heading">

            <span>🌾</span>

            <div>

              <p className="small-text">
                DECISION SUPPORT
              </p>

              <h1>
                Weather Advisory
              </h1>

              <p>
                Sector-specific weather
                guidance for{" "}
                <strong>
                  {chatLocation}
                </strong>
                , generated from live
                forecast data.
              </p>

            </div>

          </div>

          {advisoryLoading && (
            <div className="climate-card">

              <h2>
                Loading advisory data...
              </h2>

              <p>
                Analyzing current conditions
                for {chatLocation}.
              </p>

            </div>
          )}

          {!advisoryLoading &&
            advisoryError && (
              <div className="climate-card">

                <h2>
                  Advisory data unavailable
                </h2>

                <p>
                  Could not retrieve advisory
                  analysis from the backend.
                </p>

              </div>
            )}

          {!advisoryLoading &&
            !advisoryError &&
            advisory?.sectors && (
              <>

                <div className="advisory-grid">

                  {Object.entries(
                    ADVISORY_SECTOR_META
                  ).map(([key, meta]) => {

                    const sector =
                      advisory.sectors[key];

                    const level =
                      sector?.risk_level ||
                      "GREEN";

                    return (
                      <button
                        key={key}
                        className={`advisory-card ${getAlertClass(
                          level
                        )}`}
                        onClick={() =>
                          setSelectedSector(
                            selectedSector ===
                              key
                              ? null
                              : key
                          )
                        }
                      >

                        <span>
                          {meta.icon}
                        </span>

                        <h2>
                          {sector?.title ||
                            meta.label}
                        </h2>

                        <p>
                          {sector?.summary ||
                            "No data available."}
                        </p>

                        <div
                          style={{
                            marginTop: "10px",
                            fontSize: "12px",
                            fontWeight: 600,
                          }}
                        >
                          {getAlertEmoji(
                            level
                          )}{" "}
                          {level}
                        </div>

                      </button>
                    );
                  })}

                </div>

                {selectedSector &&
                  advisory.sectors[
                    selectedSector
                  ] && (
                    <div
                      className="climate-card"
                      style={{
                        marginTop: "18px",
                      }}
                    >

                      <h2>
                        {
                          ADVISORY_SECTOR_META[
                            selectedSector
                          ].icon
                        }{" "}
                        {
                          advisory.sectors[
                            selectedSector
                          ].title
                        }{" "}
                        — Recommendations
                      </h2>

                      <ul
                        style={{
                          paddingLeft: "20px",
                          marginTop: "12px",
                        }}
                      >

                        {(
                          advisory.sectors[
                            selectedSector
                          ].recommendations ||
                          []
                        ).map(
                          (rec, index) => (
                            <li
                              key={index}
                              style={{
                                marginBottom:
                                  "6px",
                              }}
                            >
                              {rec}
                            </li>
                          )
                        )}

                      </ul>

                    </div>
                  )}

              </>
            )}

        </section>
      )}

    </div>
  );
}

export default App;