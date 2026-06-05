import React, { useState } from "react";
import "./styles/global.css";

import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import Screen1_Overview from "./components/Screen1_Overview";
import Screen2_Insurance from "./components/Screen2_Insurance";
import Screen3_Photo from "./components/Screen3_Photo";

import { DEFAULT_SEASON } from "./utils/constants";

export default function App() {
  const [activeScreen,   setActiveScreen]   = useState("overview");
  const [season,         setSeason]         = useState(DEFAULT_SEASON);
  const [selectedMandal, setSelectedMandal] = useState("KNL_001");

  return (
    <div className="app-shell">
      <Sidebar
        activeScreen={activeScreen}
        onNavigate={setActiveScreen}
      />
      <div className="main-area">
        <TopBar
          activeScreen={activeScreen}
          season={season}
          onSeasonChange={setSeason}
        />
        <div className="screen-content">
          {activeScreen === "overview" && (
            <Screen1_Overview
              season={season}
              selectedMandal={selectedMandal}
              onMandalSelect={setSelectedMandal}
            />
          )}
          {activeScreen === "insurance" && (
            <Screen2_Insurance
              season={season}
              selectedMandal={selectedMandal}
            />
          )}
          {activeScreen === "photo" && (
            <Screen3_Photo
              season={season}
              selectedMandal={selectedMandal}
            />
          )}
        </div>
      </div>
    </div>
  );
}
