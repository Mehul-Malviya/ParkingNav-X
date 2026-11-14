import React, { useEffect, useState } from 'react'
import ForecastBasis from './ForecastBasis'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
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

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

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

  const lotIds = predictions.map(p => p.lot_id)

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

      {/* Risk Scores */}
      {risks && (
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Risk Dashboard at +{horizon} minutes</h3>

          {/* Network summary row */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: 'Network Risk', value: risks.network_risk?.score ?? 0, sev: risks.network_risk?.severity },
              { label: 'Gate Queue', value: Math.max(...Object.values(risks.gate_queue_risk ?? {}).map(r => r.score), 0), sev: Object.values(risks.gate_queue_risk ?? {})[0]?.severity },
              { label: 'Avg Fill Pressure', value: Object.values(risks.predicted_fill_rates ?? {}).reduce((a,b)=>a+b,0) / Math.max(Object.values(risks.predicted_fill_rates ?? {}).length,1), sev: null },
            ].map(({ label, value, sev }) => {
              const pct = Math.round(value * 100)
              const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f97316' : pct >= 20 ? '#eab308' : '#22c55e'
              return (
                <div key={label} className="border rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-500 mb-1">{label}</div>
                  <div className="text-2xl font-bold" style={{ color }}>{pct}%</div>
                  {sev && <div className="text-xs mt-1" style={{ color }}>{sev}</div>}
                </div>
              )
            })}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Lot capacity pressure — uses predicted fill rates for real variation */}
            <div className="p-3 border rounded-lg">
              <div className="text-sm font-semibold mb-3">Lot Capacity Pressure</div>
              <div className="space-y-3">
                {risks.predicted_fill_rates && Object.entries(risks.predicted_fill_rates).map(([lotId, fill]) => {
                  const pct = Math.round(fill * 100)
                  const color = pct >= 90 ? '#ef4444' : pct >= 70 ? '#f97316' : pct >= 40 ? '#eab308' : '#22c55e'
                  const label = pct >= 90 ? 'CRITICAL' : pct >= 70 ? 'HIGH' : pct >= 40 ? 'MEDIUM' : 'LOW'
                  const headroom = 90 - pct
                  return (
                    <div key={lotId}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium text-gray-700">{LOT_NAMES[lotId] || lotId}</span>
                        <span className="font-semibold" style={{ color }}>{pct}% full · {headroom > 0 ? `${headroom}% to alert` : 'OVER THRESHOLD'}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden relative">
                        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
                        {/* 70% warn line */}
                        <div className="absolute top-0 bottom-0 w-px bg-orange-400 opacity-60" style={{ left: '70%' }} />
                        {/* 90% alert line */}
                        <div className="absolute top-0 bottom-0 w-px bg-red-500 opacity-60" style={{ left: '90%' }} />
                      </div>
                      <div className="flex justify-between text-gray-300 text-xs mt-0.5">
                        <span>0%</span><span style={{marginLeft:'65%'}}>70⚠</span><span>90🚨</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Gate Queue Risk */}
            <div className="p-3 border rounded-lg">
              <div className="text-sm font-semibold mb-3">Gate Queue Risk</div>
              <div className="space-y-3">
                {risks.gate_queue_risk && Object.entries(risks.gate_queue_risk).map(([gateId, r]) => {
                  const pct = Math.round(r.score * 100)
                  const color = r.severity === 'CRITICAL' ? '#ef4444' : r.severity === 'HIGH' ? '#f97316' : r.severity === 'MEDIUM' ? '#eab308' : '#22c55e'
                  const label = gateId.replace('vitap-gate-', '').replace(/-/g, ' ')
                  const estWait = Math.round(r.score * 8 * 60) // seconds
                  return (
                    <div key={gateId}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium text-gray-700 capitalize">{label} Gate</span>
                        <span className="font-semibold" style={{ color }}>
                          {r.severity} · est. {estWait}s wait
                        </span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${Math.max(pct, 3)}%`, backgroundColor: color }} />
                      </div>
                      <div className="text-xs text-gray-400 text-right mt-0.5">{pct}% congestion index</div>
                    </div>
                  )
                })}
              </div>

              <div className="text-sm font-semibold mb-3 mt-4">Search Time Risk by Lot</div>
              <div className="space-y-3">
                {risks.predicted_fill_rates && Object.entries(risks.predicted_fill_rates).map(([lotId, fill]) => {
                  const pct = Math.round(fill * 100)
                  // search time grows non-linearly with fill
                  const searchSec = Math.round(30 + (fill ** 2) * 240)
                  const color = pct >= 70 ? '#ef4444' : pct >= 50 ? '#f97316' : pct >= 30 ? '#eab308' : '#22c55e'
                  return (
                    <div key={lotId}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium text-gray-700">{LOT_NAMES[lotId] || lotId}</span>
                        <span className="font-semibold" style={{ color }}>~{searchSec}s avg search</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${Math.min(pct + 5, 100)}%`, backgroundColor: color }} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
