import axios from "axios";
import { API_BASE } from "./constants";

const apiClient = axios.create({ baseURL: API_BASE });

const call = async (fn) => {
  try {
    const res = await fn();
    return { data: res.data, error: null };
  } catch (err) {
    return { data: null, error: err?.response?.data?.detail ?? err.message ?? "Request failed" };
  }
};

export const getDistrictOverview = (season) =>
  call(() => apiClient.get("/district/overview", { params: { season } }));

export const getDistrictMandals = (season) =>
  call(() => apiClient.get("/district/mandals", { params: { season } }));

export const getSatelliteTimeseries = (mandalId, season) =>
  call(() => apiClient.get("/district/satellite-timeseries", { params: { mandal_id: mandalId, season } }));

export const getPipelineStatus = (season) =>
  call(() => apiClient.get("/district/pipeline-status", { params: { season } }));

export const postParametricCalculate = (payload) =>
  call(() => apiClient.post("/parametric/calculate", payload));

export const postParametricSimulate = (payload) =>
  call(() => apiClient.post("/parametric/simulate", payload));

export const getBacktestResults = (crop) =>
  call(() => apiClient.get("/parametric/backtest/results", { params: crop ? { crop } : {} }));

export const getPremiumTable = () =>
  call(() => apiClient.get("/insurance/premium-table"));

export const postPhotoAssess = (formData) =>
  call(() => apiClient.post("/photo/assess", formData, { headers: { "Content-Type": "multipart/form-data" } }));

export const postPhotoFeedback = (payload) =>
  call(() => apiClient.post("/photo/feedback", payload));

export const getWeightHistory = (mandalId) =>
  call(() => apiClient.get("/photo/weight-history", { params: { mandal_id: mandalId } }));

export const getEvidenceLog = (mandalId, season) =>
  call(() => apiClient.get("/photo/evidence-log", { params: { mandal_id: mandalId, season } }));

export const getMetaMandals = () =>
  call(() => apiClient.get("/meta/mandals"));

export const getMetaCrops = () =>
  call(() => apiClient.get("/meta/crops"));

export const getDistrictRecommendations = (season, crop = "Cotton") =>
  call(() => apiClient.get("/district/recommendations", { params: { season, crop } }));
