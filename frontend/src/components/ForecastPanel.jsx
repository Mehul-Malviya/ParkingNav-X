import React, { useEffect, useState } from 'react'
import ForecastBasis from './ForecastBasis'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'
import { api } from '../api'

const LOT_NAMES = {
  'vitap-lot-academic-main':  'Academic Block',
  'vitap-lot-hostel':         'Hostel Zone',
  'vitap-lot-admin-visitor':  'Admin/Visitor',
  'vitap-lot-sports':         'Sports Complex',
  'vitap-lot-overflow':       'Overflow',
}


function RiskBadge({ score, severity }) {
  const cls = severity === 'CRITICAL' ? 'bg-red-100 text-red-800 border-red-300' :
              severity === 'HIGH'     ? 'bg-orange-100 text-orange-800 border-orange-300' :
              severity === 'MEDIUM'   ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                                       'bg-green-100 text-green-800 border-green-300'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-semibold ${cls}`}>
      {severity} ({(score * 100).toFixed(0)}%)
    </span>
  )
}

export default function ForecastPanel() {
  const [predictions, setPredictions] = useState([])
  const [risks, setRisks] = useState(null)
  const [basis, setBasis] = useState(null)
  const [modelMetrics, setModelMetrics] = useState(null)
  const [horizon, setHorizon] = useState(15)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = async () => {
    setLoading(true)
    setError('')

    try {
      const [predResult, riskResult] = await Promise.allSettled([
        api.predictAll(horizon),
        api.getRiskForecast(horizon),
      ])

      const errors = []

      if (predResult.status === 'fulfilled') {
        setPredictions(predResult.value.data.predictions ?? [])
        setBasis(predResult.value.data.forecast_basis ?? null)
      } else {
        setPredictions([])
        errors.push(
          `Predictions: ${
            predResult.reason.response?.data?.detail ||
            predResult.reason.message ||
            'Request failed'
          }`
        )
      }

      if (riskResult.status === 'fulfilled') {
        // API wraps risk data under a "risks" key
        const d = riskResult.value.data
        setRisks(d.risks ?? d)
      } else {
        setRisks(null)
        errors.push(
          `Risk forecast: ${
            riskResult.reason.response?.data?.detail ||
            riskResult.reason.message ||
            'Request failed'
          }`
        )
      }

      if (errors.length > 0) {
        setError(errors.join(' | '))
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Fetch model metrics once (not on every horizon change — evaluation is expensive)
    api.getModelMetrics()
      .then(r => setModelMetrics(r.data))
      .catch(() => { /* optional — panel still works without */ })
  }, [])

  useEffect(() => {
    fetchData()
    // The forecast follows the campus clock, so refresh it periodically.
    const id = setInterval(fetchData, 60000)
    return () => clearInterval(id)
  }, [horizon])

  // Prepare bar chart data
  const barData = predictions.map(p => ({
    name: LOT_NAMES[p.lot_id] || p.lot_id,
    fill_rate: Math.round(p.predicted_fill_rate * 100),
    lower: Math.round(p.lower_90 * 100),
    upper: Math.round(p.upper_90 * 100),
    alert: p.proactive_alert,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Forecast & Risk Panel</h2>
          {error && (
            <div
              role="alert"
              className="p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm"
            >
              {error}
              <button
                type="button"
                onClick={fetchData}
                className="ml-3 underline font-semibold"
              >
                Retry
              </button>
            </div>
          )}
          <p className="text-sm text-gray-500">Occupancy predictions with 90% conformal intervals + multi-dimensional risk scores</p>
          <ForecastBasis basis={basis} />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Horizon:</label>
          <select
            value={horizon}
            onChange={e => setHorizon(Number(e.target.value))}
            className="border border-gray-300 rounded px-2 py-1 text-sm"
          >
            {[15, 30, 60].map(h => <option key={h} value={h}>{h} min</option>)}
          </select>
          <button onClick={fetchData} className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
            Refresh
          </button>
        </div>
      </div>

      {/* Prediction Bar Chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Predicted Occupancy at +{horizon} minutes (with 90% CI)
        </h3>
        {loading ? (
          <div className="h-48 flex items-center justify-center text-gray-400">Loading predictions...</div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={v => `${v}%`} />
              <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '90% Alert', fill: '#ef4444', fontSize: 11 }} />
              <ReferenceLine y={70} stroke="#f97316" strokeDasharray="4 4" label={{ value: '70% Warn', fill: '#f97316', fontSize: 11 }} />
              <Bar dataKey="fill_rate" name="Predicted fill" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="upper" name="Upper 90% CI" fill="#93c5fd" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Prediction Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {predictions.map((p, i) => (
          <div key={p.lot_id} className={`p-3 rounded-lg border text-center ${
            p.proactive_alert ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'
          }`}>
            <div className="text-xs font-medium text-gray-500 mb-1">{LOT_NAMES[p.lot_id] || p.lot_id}</div>
            <div className={`text-2xl font-bold ${
              p.predicted_fill_rate >= 0.90 ? 'text-red-600' :
              p.predicted_fill_rate >= 0.70 ? 'text-orange-500' : 'text-green-600'
            }`}>
              {(p.predicted_fill_rate * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-400">
              [{(p.lower_90 * 100).toFixed(0)}%–{(p.upper_90 * 100).toFixed(0)}%]
            </div>
            {p.proactive_alert && (
              <div className="mt-1 text-xs text-red-600 font-bold">⚠️ PROACTIVE ALERT</div>
            )}
          </div>
        ))}
      </div>

      {/* Model Accuracy Card */}
      {modelMetrics?.summary && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Model Accuracy — {modelMetrics.model}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'MAE (fill rate)', value: modelMetrics.summary.mae != null ? modelMetrics.summary.mae.toFixed(4) : '—', sub: 'mean abs error', color: 'text-blue-700' },
              { label: 'RMSE', value: modelMetrics.summary.rmse != null ? modelMetrics.summary.rmse.toFixed(4) : '—', sub: 'root mean sq error', color: 'text-indigo-700' },
              { label: 'R²', value: modelMetrics.summary.r2 != null ? modelMetrics.summary.r2.toFixed(3) : '—', sub: 'coefficient of determination', color: modelMetrics.summary.r2 >= 0.8 ? 'text-green-700' : 'text-orange-600' },
              { label: '90% CI Coverage', value: modelMetrics.summary.coverage_90 != null ? `${(modelMetrics.summary.coverage_90 * 100).toFixed(1)}%` : '—', sub: 'conformal intervals', color: 'text-teal-700' },
            ].map(({ label, value, sub, color }) => (
              <div key={label} className="text-center p-3 border rounded-lg">
                <div className={`text-xl font-bold ${color}`}>{value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{label}</div>
                <div className="text-xs text-gray-400">{sub}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-400 mt-2">
            Averaged across {modelMetrics.summary.n_lots} lots · {modelMetrics.horizon_minutes}-min horizon · evaluated on 15% held-out test split
          </div>
        </div>
      )}

      {/* Risk Dashboard */}
      {risks && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Risk Dashboard at +{horizon} minutes</h3>

          {/* Network KPI row */}
          {(() => {
            const lm = risks.lot_metrics ?? {}
            const fills = Object.values(lm).map(m => m.fill_forecast ?? 0)
            const avgFill = fills.length ? fills.reduce((a,b)=>a+b,0)/fills.length : 0
            const rising = Object.values(lm).filter(m => m.trend === 'rising').length
            const netPct = Math.round((risks.network_risk?.score ?? 0) * 100)
            const netColor = netPct >= 75 ? '#ef4444' : netPct >= 50 ? '#f97316' : netPct >= 25 ? '#eab308' : '#22c55e'
            return (
              <div className="grid grid-cols-4 gap-3 mb-5">
                <div className="border rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">Network Risk</div>
                  <div className="text-2xl font-bold" style={{color: netColor}}>{netPct}%</div>
                  <div className="text-xs mt-1" style={{color: netColor}}>{risks.network_risk?.severity}</div>
                </div>
                <div className="border rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">Avg Fill</div>
                  <div className="text-2xl font-bold text-blue-600">{Math.round(avgFill*100)}%</div>
                  <div className="text-xs text-gray-400 mt-1">across {fills.length} lots</div>
                </div>
                <div className="border rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">Lots Rising</div>
                  <div className="text-2xl font-bold text-orange-500">{rising}</div>
                  <div className="text-xs text-gray-400 mt-1">of {fills.length} filling</div>
                </div>
                <div className="border rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">Gate Wait</div>
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.max(...Object.values(risks.gate_queue_risk ?? {}).map(g => g.est_wait_seconds ?? 0), 0)}s
                  </div>
                  <div className="text-xs text-gray-400 mt-1">max est. wait</div>
                </div>
              </div>
            )
          })()}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Lot-by-lot capacity panel */}
            <div className="p-3 border rounded-lg">
              <div className="text-sm font-semibold mb-3">Lot Capacity &amp; Fill Trend</div>
              <div className="space-y-4">
                {risks.lot_metrics && Object.entries(risks.lot_metrics).map(([lotId, m]) => {
                  const pct = Math.round(m.fill_forecast * 100)
                  const color = pct >= 90 ? '#ef4444' : pct >= 70 ? '#f97316' : pct >= 40 ? '#eab308' : '#22c55e'
                  const trendIcon = m.trend === 'rising' ? '↑' : m.trend === 'falling' ? '↓' : '→'
                  const trendColor = m.trend === 'rising' ? '#f97316' : m.trend === 'falling' ? '#22c55e' : '#6b7280'
                  return (
                    <div key={lotId}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium text-gray-700">{LOT_NAMES[lotId] || lotId}</span>
                        <span className="flex items-center gap-1">
                          <span style={{color: trendColor}} className="font-bold">{trendIcon} {Math.abs(m.fill_velocity_pct_per_min).toFixed(2)}%/min</span>
                          <span className="font-semibold ml-1" style={{color}}>{pct}%</span>
                        </span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                        <div className="h-full rounded-full transition-all" style={{width:`${pct}%`, backgroundColor: color}} />
                        <div className="absolute top-0 bottom-0 w-px bg-orange-400 opacity-70" style={{left:'70%'}} />
                        <div className="absolute top-0 bottom-0 w-px bg-red-500 opacity-70" style={{left:'90%'}} />
                      </div>
                      <div className="flex justify-between text-xs mt-1 text-gray-400">
                        <span>{m.spaces_free} spaces free</span>
                        {m.time_to_warn_minutes != null
                          ? <span className="text-orange-500 font-medium">⚠ fills to 70% in {m.time_to_warn_minutes}m</span>
                          : m.time_to_alert_minutes != null
                            ? <span className="text-red-500 font-medium">🚨 hits 90% in {m.time_to_alert_minutes}m</span>
                            : <span>{m.pct_to_warn}% below warning</span>}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Gate + Search panel */}
            <div className="p-3 border rounded-lg space-y-4">
              <div>
                <div className="text-sm font-semibold mb-3">Gate Queue Forecast</div>
                <div className="space-y-3">
                  {risks.gate_queue_risk && Object.entries(risks.gate_queue_risk).map(([gateId, g]) => {
                    const pct = Math.round((g.score ?? 0) * 100)
                    const color = g.severity === 'CRITICAL' ? '#ef4444' : g.severity === 'HIGH' ? '#f97316' : g.severity === 'MEDIUM' ? '#eab308' : '#22c55e'
                    const name = gateId.replace('vitap-gate-','').replace(/-/g,' ')
                    return (
                      <div key={gateId}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium text-gray-700 capitalize">{name} Gate</span>
                          <span style={{color}} className="font-semibold">
                            ~{g.est_wait_seconds ?? 0}s wait · {g.est_queue_vehicles ?? 0} vehicles
                          </span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{width:`${Math.max(pct,3)}%`, backgroundColor: color}} />
                        </div>
                        <div className="text-xs text-gray-400 text-right mt-0.5">{pct}% congestion index</div>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div>
                <div className="text-sm font-semibold mb-3">Estimated Search Time by Lot</div>
                <div className="space-y-3">
                  {risks.lot_metrics && Object.entries(risks.lot_metrics).map(([lotId, m]) => {
                    const sec = m.est_search_seconds ?? 30
                    const color = sec >= 180 ? '#ef4444' : sec >= 90 ? '#f97316' : sec >= 60 ? '#eab308' : '#22c55e'
                    const barPct = Math.min(Math.round(sec / 3), 100)
                    return (
                      <div key={lotId}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="font-medium text-gray-700">{LOT_NAMES[lotId] || lotId}</span>
                          <span style={{color}} className="font-semibold">~{sec}s avg</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{width:`${Math.max(barPct,3)}%`, backgroundColor: color}} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
