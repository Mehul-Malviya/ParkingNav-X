import React, { useEffect, useState } from 'react'
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'
import { api } from '../api'

const COMPARE_METRICS = [
  { key: 'avg_search_time_min', label: 'Avg Search Time (min)' },
  { key: 'avg_wait_time_min',   label: 'Avg Wait Time (min)' },
  { key: 'avg_gate_queue',      label: 'Avg Gate Queue' },
  { key: 'overflow_events',     label: 'Overflow Events' },
]

const STRATEGY_LABELS = {
  B1: 'B1 First Available',
  B2: 'B2 Nearest Available',
  B3: 'B3 Prediction Only',
  P: 'ParkingNav-X',
}

const STRATEGY_COLORS = {
  B1: '#94a3b8',
  B2: '#60a5fa',
  B3: '#a78bfa',
  P: '#10b981',
}

export default function ScenarioControls() {
  const [scenarios, setScenarios] = useState([])
  const [strategies, setStrategies] = useState([])
  const [selectedScenario, setSelectedScenario] = useState('')
  const [selectedStrategy, setSelectedStrategy] = useState('P')
  const [simResult, setSimResult] = useState(null)
  const [compareResult, setCompareResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [comparing, setComparing] = useState(false)
  const [simError, setSimError] = useState('')
  const [compareError, setCompareError] = useState('')
  const [compareMetric, setCompareMetric] = useState('avg_search_time_min')

  useEffect(() => {
    Promise.all([api.getScenarios(), api.getStrategies()]).then(([sRes, stRes]) => {
      const scens = sRes.data.scenarios || []
      setScenarios(scens)
      if (scens.length > 0) setSelectedScenario(scens[0])
      setStrategies(stRes.data.strategies || [])
    }).catch(e => {
      setSimError(`Could not load scenarios/strategies: ${e.message}`)
    })
  }, [])

  const runSimulation = async () => {
    setLoading(true)
    setSimResult(null)
    setSimError('')
    try {
      const res = await api.simulate(selectedScenario, selectedStrategy)
      setSimResult(res.data)
    } catch (e) {
      setSimError(`Simulation failed: ${e.response?.data?.detail || e.message}`)
    } finally {
      setLoading(false)
    }
  }

  const runComparison = async () => {
    setComparing(true)
    setCompareResult(null)
    setCompareError('')
    try {
      const res = await api.compareStrategies(selectedScenario)
      setCompareResult(res.data)
    } catch (e) {
      setCompareError(`Comparison failed: ${e.response?.data?.detail || e.message}`)
    } finally {
      setComparing(false)
    }
  }

  // Build comparison chart: one bar per strategy for the selected metric
  const activeCmpMeta = COMPARE_METRICS.find(m => m.key === compareMetric) || COMPARE_METRICS[0]
  const chartData = compareResult
    ? ['B1', 'B2', 'B3', 'P'].map(code => ({
        strategy: code,
        value: compareResult.comparison?.[code]?.[activeCmpMeta.key] ?? null,
      }))
    : []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-gray-800">Scenario Controls</h2>
        <p className="text-sm text-gray-500">Run parking simulations and compare strategies head-to-head</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scenario</label>
            <select
              value={selectedScenario}
              onChange={e => setSelectedScenario(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {scenarios.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Strategy</label>
            <select
              value={selectedStrategy}
              onChange={e => setSelectedStrategy(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {strategies.map(s => (
                <option key={s.code} value={s.code}>{s.code} — {s.name}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex gap-3">
            <button
              onClick={runSimulation}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '⏳ Running...' : '▶ Run Simulation'}
            </button>
            <button
              onClick={runComparison}
              disabled={comparing}
              className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50"
            >
              {comparing ? '⏳ Comparing...' : '⚖️ Compare All Strategies'}
            </button>
          </div>
          {(loading || comparing) && (
            <p className="text-xs text-amber-600 font-medium">
              ⏳ Running on free hosting — this takes 60–90 seconds, please wait…
            </p>
          )}
          {simError && (
            <div role="alert" className="p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">
              {simError}
            </div>
          )}
          {compareError && (
            <div role="alert" className="p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">
              {compareError}
            </div>
          )}
        </div>
      </div>

      {/* Single sim result */}
      {simResult && (
        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Simulation Result — {simResult.scenario} / {simResult.strategy}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              ['Total Vehicles', simResult.vehicles],
              ['Parked', simResult.metrics?.parked_vehicles],
              ['Overflow Events', simResult.metrics?.overflow_events],
              ['Avg Search Time', simResult.metrics?.avg_search_time_min != null ? `${simResult.metrics.avg_search_time_min} min` : 'N/A'],
              ['Avg Wait Time', simResult.metrics?.avg_wait_time_min != null ? `${simResult.metrics.avg_wait_time_min} min` : 'N/A'],
              ['Avg Gate Queue', simResult.metrics?.avg_gate_queue ?? 'N/A'],
              ['Peak Gate Queue', simResult.metrics?.peak_gate_queue ?? 'N/A'],
              ['Run ID', simResult.run_id],
            ].map(([label, value]) => (
              <div key={label} className="p-3 bg-gray-50 rounded border border-gray-200">
                <div className="text-xs text-gray-500">{label}</div>
                <div className="text-lg font-bold text-gray-800">{value ?? 'N/A'}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comparison chart */}
      {compareResult && (
        <div className="bg-white rounded-lg shadow p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-1">
            Strategy Comparison — {compareResult.scenario}
          </h3>
          <div className="mb-3 flex items-center gap-2">
            <label className="text-xs font-medium text-gray-600">Metric:</label>
            <select
              value={compareMetric}
              onChange={e => setCompareMetric(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-xs"
            >
              {COMPARE_METRICS.map(m => <option key={m.key} value={m.key}>{m.label}</option>)}
            </select>
            <span className="text-xs text-gray-400">lower is better ↓</span>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="strategy" tick={{ fontSize: 13, fontWeight: 600 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => [v?.toFixed ? v.toFixed(3) : v, activeCmpMeta.label]} />
              <Bar dataKey="value" name={activeCmpMeta.label} radius={[4, 4, 0, 0]}>
                {chartData.map(entry => (
                  <Cell key={entry.strategy} fill={STRATEGY_COLORS[entry.strategy]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Table */}
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-gray-500">Strategy</th>
                  <th className="text-right py-2 px-3 text-gray-500">Search Time</th>
                  <th className="text-right py-2 px-3 text-gray-500">Wait Time</th>
                  <th className="text-right py-2 px-3 text-gray-500">Avg Queue</th>
                  <th className="text-right py-2 px-3 text-gray-500">Overflow</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(compareResult.comparison || {}).map(([code, m]) => (
                  <tr key={code} className={`border-b ${code === 'P' ? 'bg-green-50 font-semibold' : ''}`}>
                    <td className="py-2 px-3">{STRATEGY_LABELS[code] || code}</td>
                    <td className="text-right py-2 px-3">{m.avg_search_time_min ?? '—'}</td>
                    <td className="text-right py-2 px-3">{m.avg_wait_time_min ?? '—'}</td>
                    <td className="text-right py-2 px-3">{m.avg_gate_queue ?? '—'}</td>
                    <td className="text-right py-2 px-3">{m.overflow_events ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
