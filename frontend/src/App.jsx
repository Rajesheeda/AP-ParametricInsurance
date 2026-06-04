import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend, ReferenceLine, AreaChart, Area
} from 'recharts';
import { 
  Map, CloudSun, ShieldAlert, Award, FileText, CheckCircle, 
  AlertTriangle, Upload, RefreshCw, Layers, Clock, MapPin, Calendar
} from 'lucide-react';

const API_BASE = "http://localhost:8000/api/v1";

const STATIC_COORDS = {
  "Adoni-1": { x: 120, y: 180 },
  "Adoni-2": { x: 140, y: 190 },
  "Alur": { x: 60, y: 240 },
  "Aspari": { x: 100, y: 260 },
  "C. Belagal": { x: 190, y: 130 },
  "Chippagiri": { x: 80, y: 300 },
  "Devanakonda": { x: 140, y: 280 },
  "Gonegandla": { x: 180, y: 210 },
  "Gudur": { x: 230, y: 180 },
  "Halaharvi": { x: 40, y: 290 },
  "Holagunda": { x: 30, y: 200 },
  "Kallur": { x: 260, y: 150 },
  "Kodumur": { x: 220, y: 240 },
  "Kosigi": { x: 70, y: 120 },
  "Kowthalam": { x: 50, y: 160 },
  "Krishnagiri": { x: 190, y: 300 },
  "Kurnool Rural": { x: 280, y: 120 },
  "Kurnool Urban": { x: 290, y: 100 },
  "Maddikera": { x: 90, y: 340 },
  "Mantralayam": { x: 110, y: 100 },
  "Nandavaram": { x: 150, y: 140 },
  "Orvakal": { x: 300, y: 200 },
  "Pattikonda": { x: 130, y: 330 },
  "Pedda Kadubur": { x: 130, y: 220 },
  "Tuggali": { x: 140, y: 370 },
  "Veldurthy": { x: 240, y: 320 },
  "Yemmiganur": { x: 180, y: 170 }
};

const MANDAL_IDS = {
  "Adoni-1": "KNL_001", "Adoni-2": "KNL_002", "Alur": "KNL_003", "Aspari": "KNL_004", 
  "C. Belagal": "KNL_005", "Chippagiri": "KNL_006", "Devanakonda": "KNL_007", 
  "Gonegandla": "KNL_008", "Gudur": "KNL_009", "Halaharvi": "KNL_010", 
  "Holagunda": "KNL_011", "Kallur": "KNL_012", "Kodumur": "KNL_013", 
  "Kosigi": "KNL_014", "Kowthalam": "KNL_015", "Krishnagiri": "KNL_016", 
  "Kurnool Rural": "KNL_017", "Kurnool Urban": "KNL_018", "Maddikera": "KNL_019", 
  "Mantralayam": "KNL_020", "Nandavaram": "KNL_021", "Orvakal": "KNL_022", 
  "Pattikonda": "KNL_023", "Pedda Kadubur": "KNL_024", "Tuggali": "KNL_025", 
  "Veldurthy": "KNL_026", "Yemmiganur": "KNL_027"
};

function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [selectedMandal, setSelectedMandal] = useState("Alur");
  const [selectedYear, setSelectedYear] = useState(2023); // maps to Kharif_2023 or Kharif_2020
  
  // Loaded State
  const [mandals, setMandals] = useState({});
  const [districtOverview, setDistrictOverview] = useState(null);
  const [selectedMandalData, setSelectedMandalData] = useState(null);
  const [timeseriesData, setTimeseriesData] = useState([]);
  const [pipelineData, setPipelineData] = useState(null);
  
  // Screen 2 States
  const [scenarioCrop, setScenarioCrop] = useState("Groundnut");
  const [scenarioPeril, setScenarioPeril] = useState("Drought");
  const [rainfallDeficit, setRainfallDeficit] = useState(60);
  const [consecutiveDryDays, setConsecutiveDryDays] = useState(22);
  const [temperature, setTemperature] = useState(43.0);
  const [payoutResult, setPayoutResult] = useState(null);
  const [backtestData, setBacktestData] = useState(null);
  const [premiumTable, setPremiumTable] = useState([]);
  
  // Screen 3 States
  const [uploadedPhoto, setUploadedPhoto] = useState(null);
  const [photoPayload, setPhotoPayload] = useState({
    crop_name: "Groundnut",
    claimed_mandal_id: "KNL_003", // Alur default
    claimed_disaster_date: "2023-09-12",
    latitude: 15.4289,
    longitude: 78.0098
  });
  const [metadataStrip, setMetadataStrip] = useState(false);
  const [photoshopMock, setPhotoshopMock] = useState(false);
  const [photoResult, setPhotoResult] = useState(null);
  const [evidenceLogs, setEvidenceLogs] = useState([]);
  const [weightHistory, setWeightHistory] = useState([]);
  
  const [isRoadmapOpen, setIsRoadmapOpen] = useState(false);
  const [countdown, setCountdown] = useState("23h 41m 15s");

  const season = selectedYear === 2023 ? "Kharif_2023" : "Kharif_2020";
  const selectedMandalId = MANDAL_IDS[selectedMandal] || "KNL_003";

  // 1. Initial Load and year/season switches
  useEffect(() => {
    // Load Header district overview summary
    fetch(`${API_BASE}/district/overview?season=${season}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) setDistrictOverview(resObj.data);
      })
      .catch(err => console.error("Error loading district overview:", err));

    // Load mandals list details (VCI, SPI, anomaly status)
    fetch(`${API_BASE}/district/mandals?season=${season}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success && resObj.data && resObj.data.mandals) {
          const dict = {};
          resObj.data.mandals.forEach(m => {
            const coords = STATIC_COORDS[m.mandal_name] || { x: 150, y: 150 };
            dict[m.mandal_name] = { ...m, ...coords };
          });
          setMandals(dict);
        }
      })
      .catch(err => console.error("Error loading mandals map list:", err));

    // Load 72h pipeline status
    fetch(`${API_BASE}/district/pipeline-status?season=${season}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) setPipelineData(resObj.data);
      })
      .catch(err => console.error("Error loading pipeline stages:", err));
  }, [selectedYear]);

  // 2. Fetch specific mandal details (Screen 1 curves + Screen 3 weight plots)
  useEffect(() => {
    if (!selectedMandal) return;
    
    // Load VCI NDVI curves
    fetch(`${API_BASE}/district/satellite-timeseries?mandal_id=${selectedMandalId}&season=${season}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success && resObj.data) setTimeseriesData(resObj.data.timeseries);
      })
      .catch(err => console.error("Error loading VCI trend series:", err));

    // Load claim evidence log
    fetch(`${API_BASE}/photo/evidence-log?mandal_id=${selectedMandalId}&season=${season}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success && resObj.data) setEvidenceLogs(resObj.data.evidence);
      })
      .catch(err => console.error("Error loading evidence log table:", err));

    // Load weight shifts history (RLHF)
    fetch(`${API_BASE}/photo/weight-history?mandal_id=${selectedMandalId}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success && resObj.data) setWeightHistory(resObj.data.weight_history);
      })
      .catch(err => console.error("Error loading weights history:", err));
  }, [selectedMandal, selectedYear]);

  // Sync mandal details sidebar card state
  useEffect(() => {
    if (mandals[selectedMandal]) {
      setSelectedMandalData(mandals[selectedMandal]);
    }
  }, [selectedMandal, mandals]);

  // 3. Screen 2: Risk Scenario Engine calculations
  useEffect(() => {
    // Calculate live payout metrics
    const payload = {
      crop: scenarioCrop,
      peril: scenarioPeril,
      mandal_id: selectedMandalId,
      season: season,
      sowing_date: selectedYear === 2023 ? "2023-07-01" : "2020-07-01",
      disaster_date: selectedYear === 2023 ? "2023-09-12" : "2020-09-12",
      weather_inputs: {
        rainfall_deficit_pct: parseFloat(rainfallDeficit),
        consecutive_dry_days: parseInt(consecutiveDryDays),
        max_temp_celsius: parseFloat(temperature),
        spi_value: calculateMockSpi(rainfallDeficit)
      }
    };

    fetch(`${API_BASE}/parametric/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) setPayoutResult(resObj.data);
      })
      .catch(err => console.error("Error calculating scenario:", err));

    // Load Backtesting validation outcomes
    fetch(`${API_BASE}/backtest/results?crop=${scenarioCrop}`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) setBacktestData(resObj.data);
      })
      .catch(err => console.error("Error loading backtest:", err));

    // Load full premium table metadata
    fetch(`${API_BASE}/insurance/premium-table`)
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) setPremiumTable(resObj.data.table);
      })
      .catch(err => console.error("Error loading premium tables:", err));
  }, [scenarioCrop, scenarioPeril, selectedMandal, rainfallDeficit, consecutiveDryDays, temperature, selectedYear]);

  // Helper calculation for mock SPI sliders
  const calculateMockSpi = (deficit) => {
    // Deficit of 60% approx SPI of -1.8
    const val = 80.0 * (1.0 - deficit/100.0);
    const mean = 80.0;
    const std = 22.0;
    return parseFloat(((val - mean)/std).toFixed(2));
  };

  // 4. Screen 3: Submit field photo to assessments API
  const handlePhotoUploadSubmit = () => {
    const formData = new FormData();
    formData.append("claimed_mandal_id", photoPayload.claimed_mandal_id);
    formData.append("claimed_crop", photoPayload.crop_name);
    formData.append("claimed_disaster_date", photoPayload.claimed_disaster_date);

    // Metadata checks simulated files
    const fileName = photoshopMock ? "field_crop_photoshop.jpg" : "field_crop_gps.jpg";
    const blob = new Blob(["mock_data"], { type: "image/jpeg" });
    
    // Simulate stripped coordinates if "Strip EXIF" toggled
    if (metadataStrip) {
      formData.append("image", new File([blob], "field_crop_stripped.jpg", { type: "image/jpeg" }));
    } else {
      formData.append("image", new File([blob], fileName, { type: "image/jpeg" }));
      // Optional coordinates params inside payload or EXIF simulation
    }

    fetch(`${API_BASE}/photo/assess`, {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success && resObj.data) {
          setPhotoResult(resObj.data);
          
          // Refresh logs
          fetch(`${API_BASE}/photo/evidence-log?mandal_id=${selectedMandalId}&season=${season}`)
            .then(r => r.json())
            .then(ro => { if (ro.success) setEvidenceLogs(ro.data.evidence); });
        }
      })
      .catch(err => console.error("Error analyzing crop photo:", err));
  };

  // VRO Submit Review feedback logs Agree/Dispute
  const handleVroFeedbackSubmit = (type) => {
    const activeAssessmentId = evidenceLogs.length > 0 ? evidenceLogs[0].submission_id : "ASS_20230914_001";
    
    const payload = {
      mandal_id: selectedMandalId,
      assessment_id: activeAssessmentId,
      feedback_type: type, // "AGREE_SATELLITE" or "DISPUTE_SATELLITE"
      vro_id: "VRO_KNL_042",
      note: type === "DISPUTE_SATELLITE" ? "Satellite showed moderate damage but actual field is total loss" : "VRO verified"
    };

    fetch(`${API_BASE}/photo/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(resObj => {
        if (resObj.success) {
          // Reload weight history & logs
          fetch(`${API_BASE}/photo/weight-history?mandal_id=${selectedMandalId}`)
            .then(r => r.json())
            .then(ro => { if (ro.success) setWeightHistory(ro.data.weight_history); });

          fetch(`${API_BASE}/photo/evidence-log?mandal_id=${selectedMandalId}&season=${season}`)
            .then(r => r.json())
            .then(ro => { if (ro.success) setEvidenceLogs(ro.data.evidence); });
        }
      })
      .catch(err => console.error("Error submitting feedback:", err));
  };

  // Hexagon coords helper for map drawing
  const getHexPoints = (cx, cy, r) => {
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle_deg = 60 * i - 30;
      const angle_rad = (Math.PI / 180) * angle_deg;
      points.push(`${cx + r * Math.cos(angle_rad)},${cy + r * Math.sin(angle_rad)}`);
    }
    return points.join(' ');
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header Summary Section */}
      <header className="glass-card m-6 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Layers className="text-[#388e3c]" size={32} />
            <h1 className="text-2xl font-bold tracking-tight">AP-CropGuard</h1>
          </div>
          <p className="text-sm text-[#a3b8b0] mt-1">
            State-Level Agricultural Monitoring Control Room | Government of Andhra Pradesh
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-[#121a17] border border-[rgba(46,125,50,0.2)] px-4 py-2 rounded-lg flex items-center gap-2">
            <Calendar className="text-[#388e3c]" size={16} />
            <span className="text-xs text-[#a3b8b0] font-semibold">Season Target:</span>
            <select 
              value={selectedYear} 
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="bg-transparent text-sm text-[#f1f8f5] font-bold border-none focus:outline-none cursor-pointer"
            >
              <option value={2023}>Kharif 2023 (Drought event)</option>
              <option value={2020}>Kharif 2020 (Normal season)</option>
            </select>
          </div>
          
          <button 
            onClick={() => setIsRoadmapOpen(true)}
            className="bg-[#388e3c] text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#2e7d32] transition flex items-center gap-2"
          >
            <Award size={16} />
            Scale-Up Roadmap
          </button>
        </div>
      </header>

      {/* Screen Headers District Overview Banner */}
      {districtOverview && (
        <section className="mx-6 mb-6 grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="glass-card p-4 text-center">
            <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">Affected Mandals</p>
            <p className="text-lg font-bold text-[#f1f8f5] mt-1">{districtOverview.mandals_affected} / {districtOverview.total_mandals}</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">Breached Threshold (43%)</p>
            <p className={`text-lg font-bold mt-1 ${districtOverview.mandals_above_threshold > 0 ? "text-[#d32f2f]" : "text-[#388e3c]"}`}>
              {districtOverview.mandals_above_threshold} Mandals
            </p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">Affected Crop Area</p>
            <p className="text-lg font-bold text-[#f1f8f5] mt-1">{(districtOverview.total_affected_area_ha / 1000).toFixed(1)}k Ha</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">District Average SPI</p>
            <p className={`text-lg font-bold mt-1 ${districtOverview.spi_district_average < 0 ? "text-[#f57c00]" : "text-[#388e3c]"}`}>
              {districtOverview.spi_district_average}
            </p>
          </div>
          <div className="glass-card p-4 text-center col-span-2 md:col-span-1">
            <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">APSDMA Alert Level</p>
            <p className={`text-lg font-bold mt-1 ${districtOverview.alert_level === "SEVERE" ? "text-[#d32f2f] alert-pulse" : "text-[#388e3c]"}`}>
              {districtOverview.alert_level}
            </p>
          </div>
        </section>
      )}

      {/* Navigation tabs */}
      <nav className="flex border-b border-[rgba(46,125,50,0.2)] mx-6 px-4 gap-2">
        <button 
          onClick={() => setActiveTab("overview")} 
          className={`nav-tab ${activeTab === "overview" ? "active" : ""}`}
        >
          <Map size={18} />
          District Overview
        </button>
        
        <button 
          onClick={() => setActiveTab("parametric")} 
          className={`nav-tab ${activeTab === "parametric" ? "active" : ""}`}
        >
          <CloudSun size={18} />
          Parametric Engine
        </button>
        
        <button 
          onClick={() => setActiveTab("validation")} 
          className={`nav-tab ${activeTab === "validation" ? "active" : ""}`}
        >
          <ShieldAlert size={18} />
          Photo Validation
        </button>
      </nav>

      {/* Screens Panels */}
      <main className="flex-1">
        {activeTab === "overview" && (
          <div className="dashboard-grid">
            {/* Screen 1 Col A: Custom SVG Kurnool Map */}
            <section className="glass-card col-span-12 lg:col-span-6 flex flex-col">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-lg font-bold">Kurnool Mandal-Level Grid Map</h2>
                  <p className="text-xs text-[#a3b8b0]">Click a mandal below to inspect NDVI time-series</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 bg-[#DC2626] rounded-full"></span> Extreme</span>
                  <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 bg-[#EA580C] rounded-full"></span> Severe</span>
                  <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 bg-[#CA8A04] rounded-full"></span> Moderate</span>
                  <span className="flex items-center gap-1 text-xs"><span className="w-3 h-3 bg-[#16A34A] rounded-full"></span> Normal</span>
                </div>
              </div>
              
              <div className="flex-1 flex justify-center items-center bg-[#070b09] rounded-xl border border-[rgba(46,125,50,0.1)] p-4 min-h-[450px] relative">
                <svg viewBox="0 0 350 450" className="w-full max-w-[340px] h-auto">
                  {Object.keys(mandals).map((name) => {
                    const m = mandals[name];
                    const isSelected = selectedMandal === name;
                    return (
                      <g key={m.mandal_id} onClick={() => setSelectedMandal(name)}>
                        <polygon
                          points={getHexPoints(m.x, m.y, 22)}
                          fill={m.map_color}
                          fillOpacity={isSelected ? 0.95 : 0.55}
                          className="mandal-polygon"
                          stroke={isSelected ? "#f1f8f5" : "rgba(46, 125, 50, 0.4)"}
                          strokeWidth={isSelected ? 3.0 : 1.5}
                        />
                        <text x={m.x} y={m.y + 3} className="mandal-label">
                          {name.substring(0, 5)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
                
                {/* 43% Loss Threshold Indicator (Universal placement) */}
                <div className="absolute top-4 left-4 bg-black/60 border border-[rgba(46,125,50,0.3)] px-3 py-1_5 rounded-lg flex items-center gap-1.5">
                  <ShieldAlert size={14} className="text-[#d32f2f]" />
                  <span className="text-xs font-bold text-[#f1f8f5]">E-Relief Threshold: 43%</span>
                </div>
              </div>
            </section>

            {/* Screen 1 Col B: Telemetry Curves + 72-Hour Pipeline */}
            <section className="col-span-12 lg:col-span-6 flex flex-col gap-6">
              {/* Mandal sidebar detail card */}
              {selectedMandalData && (
                <div className="glass-card flex flex-col md:flex-row justify-between gap-6">
                  <div>
                    <div className="flex items-center gap-2">
                      <MapPin className="text-[#388e3c]" size={18} />
                      <h3 className="text-xl font-bold">{selectedMandalData.mandal_name} Mandal</h3>
                    </div>
                    <p className="text-xs text-[#a3b8b0] mt-1">
                      SPI Category: <strong>{selectedMandalData.spi_category.replace("_", " ")}</strong> | Dominant Crop: <strong>{selectedMandalData.dominant_crop}</strong>
                    </p>
                    
                    <div className="grid grid-cols-3 gap-4 mt-6">
                      <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg">
                        <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">VCI Index</p>
                        <p className="text-md font-bold mt-1 text-[#f1f8f5]">{selectedMandalData.vci}%</p>
                      </div>
                      <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg">
                        <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">SPI Z-Score</p>
                        <p className="text-md font-bold mt-1 text-[#f1f8f5]">{selectedMandalData.spi_value}</p>
                      </div>
                      <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg">
                        <p className="text-[10px] text-[#a3b8b0] uppercase tracking-wider">Estimated Loss</p>
                        <p className={`text-md font-bold mt-1 ${selectedMandalData.estimated_loss_pct > 43.0 ? "text-[#d32f2f]" : "text-[#388e3c]"}`}>
                          {selectedMandalData.estimated_loss_pct}%
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* 43% Threshold Breach notification */}
                  <div className={`glass-card p-6 flex flex-col justify-center items-center text-center max-w-[200px] flex-1 ${
                    selectedMandalData.threshold_breached ? "border-[#d32f2f] alert-pulse" : "border-[#388e3c]"
                  }`}>
                    <ShieldAlert size={32} className={selectedMandalData.threshold_breached ? "text-[#d32f2f]" : "text-[#388e3c]"} />
                    <p className="text-xs text-[#a3b8b0] mt-3">43% Loss Threshold</p>
                    <p className="text-lg font-bold mt-1">
                      {selectedMandalData.threshold_breached ? "BREACHED" : "COMPLIANT"}
                    </p>
                    <p className="text-[10px] text-[#text-muted] mt-1">
                      {selectedMandalData.threshold_breached ? "Payout Eligible" : "Zero Payout"}
                    </p>
                  </div>
                </div>
              )}

              {/* NDVI Satellite curves with normal historical baseline band */}
              <div className="glass-card flex-1">
                <h3 className="text-sm font-bold mb-4">NASA MODIS NDVI Tracking vs. Historical Normal Baseline</h3>
                <div className="h-[200px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeseriesData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="week" stroke="#a3b8b0" fontSize={10} />
                      <YAxis stroke="#a3b8b0" fontSize={10} domain={[0.1, 0.9]} />
                      <Tooltip contentStyle={{ backgroundColor: "#121a17", borderColor: "rgba(46,125,50,0.3)" }} />
                      <Legend verticalAlign="top" height={36} iconSize={12} iconType="circle" />
                      <Line type="monotone" dataKey="ndvi" stroke="#388e3c" strokeWidth={2.5} name="Current NDVI" activeDot={{ r: 6 }} />
                      <Line type="monotone" dataKey="ndwi" stroke="#0288d1" strokeWidth={1.5} name="Current NDWI" />
                      {/* Standard historical mean line */}
                      <ReferenceLine y={0.55} stroke="#a3b8b0" strokeDasharray="4 4" label={{ value: "Historical Normal Mean", fill: "#a3b8b0", fontSize: 9 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* 72-Hour Rapid Relief Pipeline stages */}
              {pipelineData && (
                <div className="glass-card">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <Clock className="text-[#388e3c]" size={18} />
                      <h3 className="text-sm font-bold">72-Hour Automated Assessment Pipeline ({pipelineData.event_name})</h3>
                    </div>
                    <span className="text-xs bg-[#d32f2f]/20 text-[#d32f2f] border border-[#d32f2f]/30 px-2 py-0_5 rounded font-bold">
                      {countdown} Remaining
                    </span>
                  </div>
                  
                  <div className="flex flex-col md:flex-row gap-2 justify-between mt-2">
                    {pipelineData.pipeline_stages.map((stage) => (
                      <div key={stage.stage_id} className={`bg-[#121a17] border-l-2 p-2_5 rounded flex-1 ${
                        stage.status === "COMPLETE" ? "border-[#388e3c]" : "border-[rgba(255,255,255,0.15)] opacity-50"
                      }`}>
                        <p className="text-[10px] text-[#a3b8b0]">T+{stage.hours_from_event}h: {stage.status}</p>
                        <p className="text-xs font-bold mt-0.5">{stage.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === "parametric" && (
          <div className="dashboard-grid">
            {/* Screen 2 Col A: Sliders Peril control */}
            <section className="glass-card col-span-12 lg:col-span-5 flex flex-col gap-6">
              <div>
                <h2 className="text-lg font-bold">Risk Scenario Engine</h2>
                <p className="text-xs text-[#a3b8b0]">Dynamically adjust sliders to simulate weather anomalies</p>
              </div>

              <div className="flex flex-col gap-4">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs font-bold text-[#a3b8b0] block mb-2">Target Crop</label>
                    <select 
                      value={scenarioCrop} 
                      onChange={(e) => setScenarioCrop(e.target.value)}
                      className="w-full bg-[#121a17] border border-[rgba(46,125,50,0.2)] p-2_5 rounded-lg text-sm text-[#f1f8f5] focus:outline-none"
                    >
                      <option value="Groundnut">Groundnut</option>
                      <option value="Cotton">Cotton</option>
                      <option value="Redgram">Redgram</option>
                      <option value="Jowar">Jowar</option>
                      <option value="Sunflower">Sunflower</option>
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="text-xs font-bold text-[#a3b8b0] block mb-2">Weather Peril</label>
                    <select 
                      value={scenarioPeril} 
                      onChange={(e) => setScenarioPeril(e.target.value)}
                      className="w-full bg-[#121a17] border border-[rgba(46,125,50,0.2)] p-2_5 rounded-lg text-sm text-[#f1f8f5] focus:outline-none"
                    >
                      <option value="Drought">Drought</option>
                      <option value="DrySpell">Consecutive Dry Spell</option>
                      <option value="Heatwave">Heatwave / Thermal Stress</option>
                    </select>
                  </div>
                </div>

                <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-4 rounded-lg">
                  <div className="flex justify-between items-center text-sm mb-1">
                    <span className="font-semibold">Rainfall Deficit (%)</span>
                    <span className="font-bold text-[#388e3c]">{rainfallDeficit}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="100" 
                    value={rainfallDeficit}
                    onChange={(e) => setRainfallDeficit(e.target.value)}
                    className="slider-custom"
                  />
                  <p className="text-[10px] text-[#text-muted]">Deficit rainfall percentage vs regional monsoon norms</p>
                </div>

                <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-4 rounded-lg">
                  <div className="flex justify-between items-center text-sm mb-1">
                    <span className="font-semibold">Consecutive Dry Days</span>
                    <span className="font-bold text-[#388e3c]">{consecutiveDryDays} Days</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="45" 
                    value={consecutiveDryDays}
                    onChange={(e) => setConsecutiveDryDays(e.target.value)}
                    className="slider-custom"
                  />
                  <p className="text-[10px] text-[#text-muted]">Dry rainless days at flowering and pegging stages</p>
                </div>

                <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-4 rounded-lg">
                  <div className="flex justify-between items-center text-sm mb-1">
                    <span className="font-semibold">Max Daily Temperature (°C)</span>
                    <span className="font-bold text-[#388e3c]">{temperature}°C</span>
                  </div>
                  <input 
                    type="range" 
                    min="25" 
                    max="50" 
                    step="0.5"
                    value={temperature}
                    onChange={(e) => setTemperature(e.target.value)}
                    className="slider-custom"
                  />
                  <p className="text-[10px] text-[#text-muted]">Triggers temperature risk load if max exceeds 42.0°C</p>
                </div>
              </div>
            </section>

            {/* Screen 2 Col B: Payout charts, Backtests, and Policy sheets */}
            <section className="col-span-12 lg:col-span-7 flex flex-col gap-6">
              {/* Actuarial policy sheet card */}
              {payoutResult && payoutResult.term_sheet && (
                <div className="glass-card">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <FileText className="text-[#388e3c]" size={18} />
                      <h3 className="text-sm font-bold">Actuarial Term Sheet: {scenarioCrop} ({selectedMandal})</h3>
                    </div>
                    <span className="text-xs bg-[#121a17] px-3 py-1 border border-[rgba(46,125,50,0.3)] rounded text-[#a3b8b0]">
                      Sowing Anchor: <strong>July 1</strong> | DAS: <strong>{payoutResult.das_at_event} ({payoutResult.crop_stage})</strong>
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-4 rounded-lg">
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Sum Insured</p>
                      <p className="text-md font-bold mt-0.5">₹{payoutResult.term_sheet.sum_insured_per_ha.toLocaleString()}/Ha</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Consensus Loss %</p>
                      <p className={`text-md font-bold mt-0.5 ${payoutResult.final_loss_pct > 43.0 ? "text-[#d32f2f]" : "text-[#388e3c]"}`}>
                        {payoutResult.final_loss_pct}%
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Payout Triggered</p>
                      <p className="text-md font-bold mt-0.5">{payoutResult.threshold_43_breached ? "YES" : "NO"}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Estimated Payout</p>
                      <p className="text-md font-bold text-[#f57c00] mt-0.5">₹{payoutResult.term_sheet.current_estimated_payout_per_ha.toLocaleString()}/Ha</p>
                    </div>
                  </div>
                  
                  <div className="flex flex-col md:flex-row gap-6 mt-4 justify-between items-start md:items-center">
                    <div>
                      <p className="text-xs text-[#a3b8b0]">
                        Proposed Actuarial Premium for next season: <strong>₹{payoutResult.term_sheet.premium_per_ha.toLocaleString()} / Ha</strong> ({payoutResult.term_sheet.premium_rate_pct}%)
                      </p>
                      <p className="text-[10px] text-[#text-muted] mt-0.5">actuarial formulas include stage weight coefficient of {payoutResult.kc_multiplier}x during Flowering.</p>
                    </div>
                    <button 
                      onClick={() => window.print()}
                      className="bg-transparent hover:bg-[rgba(46,125,50,0.15)] border border-[rgba(46,125,50,0.3)] text-[#f1f8f5] px-4 py-2 rounded-lg text-xs font-semibold transition"
                    >
                      Print Policy Sheet
                    </button>
                  </div>
                </div>
              )}

              {/* Area Payout curve chart with vertical 43% line */}
              {payoutResult && payoutResult.payout_curve && (
                <div className="glass-card">
                  <h3 className="text-sm font-bold mb-4">Parametric Payout Curve vs. Estimated Crop Loss %</h3>
                  <div className="h-[180px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={payoutResult.payout_curve}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="loss_pct" stroke="#a3b8b0" fontSize={10} label={{ value: "Crop Loss %", position: "insideBottom", offset: -2, fill: "#a3b8b0" }} />
                        <YAxis stroke="#a3b8b0" fontSize={10} label={{ value: "Payout (₹/Ha)", angle: -90, position: "insideLeft", fill: "#a3b8b0" }} />
                        <Tooltip />
                        {/* 43% universal threshold line */}
                        <ReferenceLine x={43} stroke="#d32f2f" strokeWidth={2} strokeDasharray="3 3" label={{ value: "43% Threshold", fill: "#d32f2f", position: "top", fontSize: 9 }} />
                        <ReferenceLine x={payoutResult.final_loss_pct} stroke="#f57c00" strokeWidth={2} label={{ value: `Loss: ${payoutResult.final_loss_pct}%`, fill: "#f57c00", position: "top", fontSize: 9 }} />
                        <Area type="monotone" dataKey="payout_per_ha" stroke="#388e3c" fill="var(--color-green-glow)" strokeWidth={2} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* NCIP Backtesting Panel */}
              <div className="glass-card">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-sm font-bold">Historical Model Back-Testing Sandbox</h3>
                    <p className="text-[10px] text-[#a3b8b0]">Pearson Correlation validation against actual government expenditure</p>
                  </div>
                  {backtestData && (
                    <div className="bg-[#388e3c]/20 border border-[#388e3c]/30 text-[#388e3c] px-3 py-1 rounded text-xs font-bold">
                      Correlation: {backtestData.overall_correlation} (Pearson) | {backtestData.meets_target ? "PASS (>= 75% target met)" : "VALIDATING"}
                    </div>
                  )}
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[rgba(46,125,50,0.15)] text-[#a3b8b0]">
                        <th className="py-2.5 font-bold">Year</th>
                        <th className="py-2.5 font-bold">Peril / Event</th>
                        <th className="py-2.5 font-bold">Description</th>
                        <th className="py-2.5 font-bold">Model Payout</th>
                        <th className="py-2.5 font-bold">NCIP Actual Payout</th>
                        <th className="py-2.5 font-bold">Variance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {backtestData && backtestData.events.map((ev) => {
                        const diff = ev.model_predicted_payout_per_ha - ev.actual_govt_payout_per_ha;
                        return (
                          <tr key={ev.event_id} className="border-b border-[rgba(46,125,50,0.08)]">
                            <td className="py-2 font-semibold text-[#f1f8f5]">{ev.year}</td>
                            <td className="py-2 text-[#a3b8b0] font-bold">{ev.peril}</td>
                            <td className="py-2 text-[#a3b8b0]">{ev.description}</td>
                            <td className="py-2 font-bold text-[#f1f8f5]">₹{ev.model_predicted_payout_per_ha.toLocaleString()}</td>
                            <td className="py-2 text-[#a3b8b0]">₹{ev.actual_govt_payout_per_ha.toLocaleString()}</td>
                            <td className={`py-2 font-bold ${ev.variance_pct <= 10.0 ? "text-[#388e3c]" : "text-[#f57c00]"}`}>
                              {ev.variance_pct}% ({ev.model_assessment})
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                {backtestData && (
                  <p className="text-[9px] text-[#text-muted] mt-3 text-right">
                    Source: {backtestData.data_source}
                  </p>
                )}
              </div>
            </section>
          </div>
        )}

        {activeTab === "validation" && (
          <div className="dashboard-grid">
            {/* Screen 3 Col A: Panel 3A Ground photo upload + EXIF validations */}
            <section className="glass-card col-span-12 lg:col-span-6 flex flex-col gap-6">
              <div>
                <h2 className="text-lg font-bold">Panel 3A: Photo Assessment (Ground Truth)</h2>
                <p className="text-xs text-[#a3b8b0]">Upload field photo to run ML diagnostics & EXIF checks</p>
              </div>

              <div className="bg-[#121a17] border border-[rgba(46,125,50,0.2)] p-4 rounded-xl flex flex-col gap-4">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs font-bold text-[#a3b8b0] block mb-2">Crop Sown</label>
                    <select 
                      value={photoPayload.crop_name} 
                      onChange={(e) => setPhotoPayload({ ...photoPayload, crop_name: e.target.value })}
                      className="w-full bg-[#0a0f0d] border border-[rgba(46,125,50,0.15)] p-2 rounded text-sm text-[#f1f8f5] focus:outline-none"
                    >
                      <option value="Groundnut">Groundnut</option>
                      <option value="Cotton">Cotton</option>
                      <option value="Redgram">Redgram</option>
                    </select>
                  </div>
                  <div className="flex-1">
                    <label className="text-xs font-bold text-[#a3b8b0] block mb-2">Claim Mandal</label>
                    <select 
                      value={photoPayload.claimed_mandal_id} 
                      onChange={(e) => setPhotoPayload({ ...photoPayload, claimed_mandal_id: e.target.value })}
                      className="w-full bg-[#0a0f0d] border border-[rgba(46,125,50,0.15)] p-2 rounded text-sm text-[#f1f8f5] focus:outline-none"
                    >
                      {Object.keys(mandals).map(n => <option key={MANDAL_IDS[n]} value={MANDAL_IDS[n]}>{n}</option>)}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <label className="bg-[#0a0f0d] border border-[rgba(46,125,50,0.15)] p-3 rounded text-center cursor-pointer flex flex-col items-center justify-center gap-1.5 hover:bg-[#121a17] transition">
                    <Upload size={18} className="text-[#388e3c]" />
                    <span className="text-[10px] font-semibold text-[#a3b8b0]">Choose Image</span>
                    <input 
                      type="file" 
                      accept="image/*"
                      onChange={(e) => setUploadedPhoto(e.target.files[0] ? e.target.files[0].name : "crop_image.jpg")}
                      className="hidden" 
                    />
                  </label>
                  
                  <button 
                    onClick={() => setMetadataStrip(!metadataStrip)}
                    className={`border p-3 rounded text-center cursor-pointer flex flex-col items-center justify-center gap-1.5 transition ${
                      metadataStrip ? "bg-[#f57c00]/10 border-[#f57c00] text-[#f57c00]" : "bg-[#0a0f0d] border-[rgba(46,125,50,0.15)] text-[#a3b8b0]"
                    }`}
                  >
                    <MapPin size={18} />
                    <span className="text-[10px] font-semibold">Strip EXIF</span>
                  </button>
                  
                  <button 
                    onClick={() => setPhotoshopMock(!photoshopMock)}
                    className={`border p-3 rounded text-center cursor-pointer flex flex-col items-center justify-center gap-1.5 transition ${
                      photoshopMock ? "bg-[#d32f2f]/10 border-[#d32f2f] text-[#d32f2f]" : "bg-[#0a0f0d] border-[rgba(46,125,50,0.15)] text-[#a3b8b0]"
                    }`}
                  >
                    <Layers size={18} />
                    <span className="text-[10px] font-semibold">Photoshop Tag</span>
                  </button>
                </div>
                
                {uploadedPhoto && (
                  <p className="text-xs text-[#388e3c] font-semibold flex items-center gap-1">
                    <CheckCircle size={14} /> Selected image: {uploadedPhoto}
                  </p>
                )}

                <button 
                  onClick={handlePhotoUploadSubmit}
                  className="w-full bg-[#388e3c] text-white py-3 rounded-lg text-sm font-bold hover:bg-[#2e7d32] transition flex items-center justify-center gap-2 mt-2"
                >
                  <RefreshCw size={16} />
                  Analyze Photo & Run Verification
                </button>
              </div>

              {/* Claude Vision output parameters */}
              {photoResult && photoResult.assessment && (
                <div className="glass-card flex-1">
                  <h3 className="text-sm font-bold mb-4">Claude Vision / Fallback Classifier Output</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg">
                      <p className="text-[10px] text-[#a3b8b0]">Classification Status</p>
                      <p className="text-md font-bold mt-0.5 text-[#f1f8f5]">{photoResult.assessment.damage_class}</p>
                    </div>
                    <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg">
                      <p className="text-[10px] text-[#a3b8b0]">Confidence Score</p>
                      <p className="text-md font-bold mt-0.5 text-[#388e3c]">{(photoResult.assessment.confidence_score * 100).toFixed(0)}%</p>
                    </div>
                    <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg col-span-2">
                      <p className="text-[10px] text-[#a3b8b0]">Identified Pathology</p>
                      <p className="text-sm font-bold mt-0.5 text-[#f57c00]">
                        {photoResult.assessment.disease_details[0].name} (Severity: {photoResult.assessment.disease_details[0].severity})
                      </p>
                    </div>
                    <div className="bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-3 rounded-lg col-span-2">
                      <p className="text-[10px] text-[#a3b8b0]">Agronomic Protective Advice</p>
                      <p className="text-xs text-[#a3b8b0] mt-1">{photoResult.assessment.disease_details[0].agronomic_advice}</p>
                    </div>
                  </div>
                  <p className="text-[9px] text-[#text-muted] mt-3 text-right">Source: {photoResult.assessment.analysis_source}</p>
                </div>
              )}
            </section>

            {/* Screen 3 Col B: Panel 3B Claim evidence log consensus and RLHF charts */}
            <section className="col-span-12 lg:col-span-6 flex flex-col gap-6">
              {/* EXIF metadata checklist logs */}
              {photoResult && photoResult.fraud_check && (
                <div className="glass-card">
                  <h3 className="text-sm font-bold mb-4">EXIF Anti-Fraud Check Results</h3>
                  <div className="flex flex-col gap-2">
                    {/* Geofence check logging */}
                    <div className={`flex items-start gap-2 text-xs bg-[#121a17] p-2_5 rounded border border-[rgba(46,125,50,0.1)] ${
                      photoResult.fraud_check.geofence_check.status === "PASS" ? "text-[#a3b8b0]" : "text-[#f57c00] font-semibold"
                    }`}>
                      {photoResult.fraud_check.geofence_check.status === "PASS" ? (
                        <CheckCircle size={14} className="text-[#388e3c]" />
                      ) : (
                        <AlertTriangle size={14} className="text-[#f57c00]" />
                      )}
                      <span>
                        Geofence check: {photoResult.fraud_check.geofence_check.status} (EXIF Lat: {photoResult.fraud_check.geofence_check.exif_lat}, Lon: {photoResult.fraud_check.geofence_check.exif_lon})
                      </span>
                    </div>
                    {/* Temporal check logging */}
                    <div className="flex items-start gap-2 text-xs bg-[#121a17] p-2_5 rounded border border-[rgba(46,125,50,0.1)] text-[#a3b8b0]">
                      <CheckCircle size={14} className="text-[#388e3c]" />
                      <span>EXIF Timestamp check: {photoResult.fraud_check.temporal_check.status} (Captured: {photoResult.fraud_check.temporal_check.photo_timestamp.substring(0, 10)})</span>
                    </div>
                    {/* Edit signature checklist */}
                    <div className={`flex items-start gap-2 text-xs bg-[#121a17] p-2_5 rounded border border-[rgba(46,125,50,0.1)] ${
                      photoResult.fraud_check.edit_signature_check.status === "PASS" ? "text-[#a3b8b0]" : "text-[#d32f2f] font-bold"
                    }`}>
                      {photoResult.fraud_check.edit_signature_check.status === "PASS" ? (
                        <CheckCircle size={14} className="text-[#388e3c]" />
                      ) : (
                        <ShieldAlert size={14} className="text-[#d32f2f]" />
                      )}
                      <span>
                        Software Edit Check: {photoResult.fraud_check.edit_signature_check.status} 
                        {photoResult.fraud_check.edit_signature_check.editor_detected && ` (${photoResult.fraud_check.edit_signature_check.editor_detected})`}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Bayesian Consensus Engine */}
              <div className="glass-card">
                <h3 className="text-sm font-bold mb-4">Consensus Loss Engine (VCI + Ground Truth)</h3>
                {photoResult ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#121a17] border border-[rgba(46,125,50,0.15)] p-4 rounded-lg text-center">
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Satellite Loss</p>
                      <p className="text-sm font-bold mt-0.5">{photoResult.satellite_loss_percent}%</p>
                      <p className="text-[9px] text-[#text-muted]">Weight: {photoResult.weights_applied.W_sat}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Ground Loss</p>
                      <p className="text-sm font-bold mt-0.5">{photoResult.assessment.estimated_photo_loss_pct}%</p>
                      <p className="text-[9px] text-[#text-muted]">Weight: {photoResult.weights_applied.W_photo}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Consensus Loss</p>
                      <p className={`text-sm font-bold mt-0.5 ${photoResult.final_consensus_loss > 43.0 ? "text-[#d32f2f]" : "text-[#388e3c]"}`}>
                        {photoResult.final_consensus_loss}%
                      </p>
                      <p className="text-[9px] text-[#text-muted]">(43% Threshold Check)</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#a3b8b0]">Payout Settled</p>
                      <p className="text-sm font-bold mt-0.5 text-[#f57c00]">{photoResult.payout_threshold_crossed}</p>
                      <p className="text-[9px] text-[#text-muted]">(Relief Authorized)</p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-[#121a17] border border-[rgba(46,125,50,0.1)] p-6 rounded-lg text-center text-[#a3b8b0] text-xs">
                    Please submit a photo assessment to run Bayesian Consensus fusion.
                  </div>
                )}
                
                {/* VRO disputes agree loop */}
                {photoResult && (
                  <div className="flex gap-4 mt-4 items-center">
                    <span className="text-xs text-[#a3b8b0] font-semibold">Audit VCI Trigger:</span>
                    <button 
                      onClick={() => handleVroFeedbackSubmit("AGREE_SATELLITE")}
                      className="bg-transparent hover:bg-[#388e3c]/20 border border-[#388e3c]/40 text-[#388e3c] px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5"
                    >
                      <CheckCircle size={14} />
                      Agree (Increase VCI Weight)
                    </button>
                    <button 
                      onClick={() => handleVroFeedbackSubmit("DISPUTE_SATELLITE")}
                      className="bg-transparent hover:bg-[#d32f2f]/20 border border-[#d32f2f]/40 text-[#d32f2f] px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5"
                    >
                      <ShieldAlert size={14} />
                      Dispute (Increase Photo Weight)
                    </button>
                  </div>
                )}
              </div>

              {/* Weight shifts adaptive chart (RLHF) */}
              <div className="glass-card">
                <h3 className="text-sm font-bold mb-4">RLHF Engine: Weight Shifts (Mandal: {selectedMandal})</h3>
                <div className="h-[150px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={weightHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="entry" stroke="#a3b8b0" fontSize={10} label={{ value: "Audit Updates count", position: "insideBottom", offset: -2, fill: "#a3b8b0" }} />
                      <YAxis stroke="#a3b8b0" fontSize={10} domain={[0.0, 1.0]} />
                      <Tooltip />
                      <Legend verticalAlign="top" iconSize={10} iconType="circle" />
                      <Line type="monotone" dataKey="w_satellite" stroke="#0288d1" strokeWidth={2} name="VCI (Satellite) weight" />
                      <Line type="monotone" dataKey="w_photo" stroke="#f57c00" strokeWidth={2} name="Ground (Photo) weight" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Evidence log table */}
              <div className="glass-card flex-1">
                <h3 className="text-sm font-bold mb-4">Mandal Evidence Log</h3>
                <div className="max-h-[150px] overflow-y-auto flex flex-col gap-2">
                  {evidenceLogs.length > 0 ? (
                    evidenceLogs.map((log) => (
                      <div key={log.submission_id} className="bg-[#121a17] border border-[rgba(46,125,50,0.1)] p-2_5 rounded text-xs flex justify-between items-center">
                        <div>
                          <p className="font-semibold text-[#f1f8f5]">{log.crop} - {log.damage_class}</p>
                          <p className="text-[10px] text-[#text-muted] mt-0.5">Submitted at: {log.submitted_at.substring(0, 19).replace("T", " ")}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-[#f57c00]">Consensus Loss: {log.final_consensus_loss_pct}%</p>
                          <p className="text-[9px] text-[#a3b8b0]">VRO Action: {log.vro_feedback}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-[#a3b8b0] text-center p-4">No active evidence logs found for this mandal.</p>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}
      </main>

      {/* Scale Up Modal */}
      {isRoadmapOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-6 z-50">
          <div className="glass-card max-w-[500px] w-full border-[#388e3c] flex flex-col gap-6 relative">
            <div>
              <h2 className="text-xl font-bold">AP-CropGuard Scale-Up Roadmap</h2>
              <p className="text-xs text-[#a3b8b0]">Approved roll-out structure for Andhra Pradesh</p>
            </div>
            
            <div className="flex flex-col gap-4 text-xs">
              <div className="bg-[#121a17] border-l-2 border-[#388e3c] p-3 rounded">
                <h4 className="font-bold text-[#f1f8f5]">Phase 1: Kurnool pilot (Current)</h4>
                <p className="text-[#a3b8b0] mt-1">Covering 27 mandals, dryland agriculture focus, testing groundtruth accuracy against 2 lakh farmers base.</p>
              </div>
              
              <div className="bg-[#121a17] border-l-2 border-[#0288d1] p-3 rounded">
                <h4 className="font-bold text-[#f1f8f5]">Phase 2: Rayalaseema expansion (Months 3 - 6)</h4>
                <p className="text-[#a3b8b0] mt-1">Rollout to Anantapur, Chittoor, Kadapa. Integrating localized automatic weather station (AWS) feeds.</p>
              </div>
              
              <div className="bg-[#121a17] border-l-2 border-[#f57c00] p-3 rounded">
                <h4 className="font-bold text-[#f1f8f5]">Phase 3: Statewide Integration (Months 6 - 12)</h4>
                <p className="text-[#a3b8b0] mt-1">Full rollout across all 26 AP districts. Complete API sync with e-Crop portal and PMFBY portal database.</p>
              </div>
            </div>
            
            <button 
              onClick={() => setIsRoadmapOpen(false)}
              className="bg-[#388e3c] hover:bg-[#2e7d32] text-white py-2 rounded text-sm font-bold transition w-full"
            >
              Close Roadmap
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
