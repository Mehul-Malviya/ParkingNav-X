import axios from 'axios'

// Use direct backend URL in production to avoid Netlify's 26s proxy timeout on long simulation runs
const BASE = import.meta.env.VITE_API_BASE
  ? `${import.meta.env.VITE_API_BASE}`
  : '/api'

// Render's free tier sleeps when idle and takes ~50s to wake; the host proxy answers 502/503/504 meanwhile.
// Retry idempotent GETs while it wakes and tell the UI (window 'api-waking' event) so it can show a banner.
const WAKE_STATUS = [502, 503, 504]
const sleep = (ms) => new Promise(r => setTimeout(r, ms))
let waking = false
const setWaking = (v) => {
  if (waking === v) return
  waking = v
  try { window.dispatchEvent(new CustomEvent('api-waking', { detail: v })) } catch { /* non-browser */ }
}
axios.interceptors.response.use(
  (res) => { setWaking(false); return res },
  async (err) => {
    const cfg = err.config
    const wakingUp = !err.response || WAKE_STATUS.includes(err.response.status)
    if (cfg && wakingUp && (cfg.method || 'get').toLowerCase() === 'get' && (cfg.__retries || 0) < 12) {
      cfg.__retries = (cfg.__retries || 0) + 1
      setWaking(true)
      await sleep(5000)
      return axios(cfg)
    }
    setWaking(false)
    throw err
  },
)

// Write key for a live deployment (PARKINGNAV_API_KEY on the server); kept for this browser tab only.
export const getWriteKey = () => { try { return sessionStorage.getItem('writeKey') || '' } catch { return '' } }
export const setWriteKey = (k) => { try { sessionStorage.setItem('writeKey', k) } catch { /* private mode */ } }
const keyHeader = () => (getWriteKey() ? { headers: { 'X-API-Key': getWriteKey() } } : {})

export const api = {
  // Info
  getRoot:           () => axios.get(`${BASE}/`),

  // Campus
  getCampus:         () => axios.get(`${BASE}/campus`),
  getCampusGraph:    () => axios.get(`${BASE}/campus/graph`),
  getEvents:         () => axios.get(`${BASE}/events`),

  // Simulation
  getScenarios:      () => axios.get(`${BASE}/scenarios`),
  getStrategies:     () => axios.get(`${BASE}/strategies`),
  simulate:          (scenario, strategy) =>
    axios.post(`${BASE}/simulate`, { scenario, strategy }),
  // Starts a background comparison and polls until done (a full comparison
  // outlasts the host's request timeout, so it can't be a single request).
  compareStrategies: async (scenario) => {
    await axios.post(`${BASE}/compare/${scenario}/start`)
    const deadline = Date.now() + 20 * 60 * 1000
    while (Date.now() < deadline) {
      await new Promise(r => setTimeout(r, 4000))
      let res
      try {
        res = await axios.get(`${BASE}/compare/${scenario}/status`)
      } catch (e) {
        if (e.response?.status === 502 || e.response?.status === 503 || !e.response) continue // host waking/busy
        throw e
      }
      if (res.data.status === 'done') return res
      if (res.data.status === 'error') {
        const err = new Error(res.data.error || 'Comparison failed')
        err.response = { data: { detail: res.data.error } }
        throw err
      }
    }
    throw new Error('Comparison timed out')
  },

  // Prediction
  predictOccupancy:  (lot_id, horizon_minutes = 15) =>
    axios.get(`${BASE}/predict/occupancy`, { params: { lot_id, horizon_minutes } }),
  predictAll:        (horizon_minutes = 15, as_of = null) =>
    axios.get(`${BASE}/predict/all`, { params: { horizon_minutes, ...(as_of ? { as_of } : {}) } }),

  // Real occupancy counts
  recordObservation: (obs) => axios.post(`${BASE}/observations`, obs, keyHeader()),
  retrainPredictor:  () => axios.post(`${BASE}/predict/retrain`, null, keyHeader()),

  // Risk
  getRiskCurrent:    () => axios.get(`${BASE}/risk/current`),
  getRiskForecast:   (horizon = 15, as_of = null) =>
    axios.get(`${BASE}/risk/forecast`, { params: { horizon, ...(as_of ? { as_of } : {}) } }),

  // Optimization
  optimize:          (scenario = 'E1_normal_day', weight_profile = 'P1') =>
    axios.post(`${BASE}/optimize`, { scenario, weight_profile }),
  getRecommendations: () => axios.get(`${BASE}/recommendations`),
  getOptimizeProfiles: () => axios.get(`${BASE}/optimize/profiles`),

  // Data quality
  getDataSummary:     () => axios.get(`${BASE}/data/summary`),
  getModelMetrics:    () => axios.get(`${BASE}/predict/model-metrics`),

  // Routing
  getRoute:          (origin, destination, mode = 'drive') =>
    axios.get(`${BASE}/route`, { params: { origin, destination, mode } }),
  findParking:       (destination_id, gate_id = 'vitap-gate-main') =>
    axios.get(`${BASE}/find_parking`, { params: { destination_id, gate_id } }),

  // Experiments
  getExperimentResults: (scenario, strategy, limit = 200) =>
    axios.get(`${BASE}/experiments/results`, { params: { scenario, strategy, limit } }),
  getExperimentSummary: () => axios.get(`${BASE}/experiments/summary`),
  runExperiment: (scenario, strategies, seeds) =>
    axios.post(`${BASE}/experiments/run`, { scenario, strategies, seeds }),
}
