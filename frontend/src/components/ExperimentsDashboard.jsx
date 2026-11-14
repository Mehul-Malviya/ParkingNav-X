import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'
import { api } from '../api'

const STRATEGIES = ['B1', 'B2', 'B3', 'P']
const STRATEGY_COLORS = { B1: '#94a3b8', B2: '#60a5fa', B3: '#a78bfa', P: '#10b981' }
const METRICS = [
  { key: 'avg_search_time_min', label: 'Avg Search Time (min)', lower: true },
  { key: 'avg_wait_time_min',   label: 'Avg Wait Time (min)',   lower: true },
  { key: 'avg_gate_queue',      label: 'Avg Gate Queue',        lower: true },
  { key: 'overflow_events',     label: 'Overflow Events',       lower: true },
]

export default function ExperimentsDashboard() {
  const [results, setResults] = useState({})
  const [statSummary, setStatSummary] = useState(null)
const [loading, setLoading] = useState(false)
const [scenarios, setScenarios] = useState([])
const [selectedScenario, setSelectedScenario] = useState('')
const [selectedMetric, setSelectedMetric] = useState('avg_search_time_min')
const [progress, setProgress] = useState([])
const [scenarioError, setScenarioError] = useState('')

useEffect(() => {
  const loadScenarios = async () => {
    try {
      setScenarioError('')

      const res = await api.getScenarios()
      const availableScenarios = res.data.scenarios ?? []

      setScenarios(availableScenarios)

      if (availableScenarios.length > 0) {
        setSelectedScenario(current =>
          availableScenarios.includes(current)
            ? current
            : availableScenarios[0]
        )
      } else {
        setScenarioError('The API returned no scenarios.')
      }
    } catch (error) {
      setScenarioError(
        error.response?.data?.detail ||
        error.message ||
        'Failed to load scenarios.'
      )
    }
  }

  loadScenarios()
}, [])

  const runExperiments = async () => {
  if (scenarios.length === 0) {
    setProgress(['No scenarios are available to run.'])
    return
  }

  setLoading(true)
  setProgress([])
  setResults({})
  setStatSummary(null)

  const newResults = {}

  try {
    for (const scenario of scenarios) {
      try {
        const res = await api.compareStrategies(scenario)
        const comparison = res.data?.comparison

        if (!comparison) {
          throw new Error('No comparison data returned')
        }

        newResults[scenario] = comparison
        setResults({ ...newResults })
        setProgress(p => [...p, `✓ ${scenario}`])
      } catch (error) {
        setProgress(p => [
          ...p,
          `✗ ${scenario}: ${
            error.response?.data?.detail ||
            error.message ||
            'Request failed'
          }`,
        ])
      }
    }
    // Fetch statistical summary (std dev + 95% CI) after experiments complete
    try {
      const sumRes = await api.getExperimentSummary()
      // Backend returns { "scenario|strategy": { scenario, strategy, n, metrics: { metric: {mean,std,ci95,n} } } }
      // Keep keyed by "scenario|strategy" so each table cell gets the correct per-combination stats
      setStatSummary(sumRes.data || {})
    } catch { /* summary is optional — table still shows mean values */ }
  } finally {
    setLoading(false)
  }
}

  // Build chart data: one bar per strategy for the selected metric only
  const scenarioData = results[selectedScenario] || {}
  const activeMeta = METRICS.find(m => m.key === selectedMetric) || METRICS[0]
  const chartData = STRATEGIES.map(s => ({
    strategy: s,
    value: scenarioData[s]?.[activeMeta.key] ?? null,
  }))

  // Summary table: all scenarios × all strategies
  const hasResults = Object.keys(results).length > 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-800">Experiments Dashboard</h2>
          <p className="text-sm text-gray-500">
            Compare available scenarios across the supported strategies.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={runExperiments}
            disabled={loading}
            className="px-4 py-2 bg-vitap-blue text-white rounded-md text-sm font-medium hover:bg-blue-800 disabled:opacity-50"
          >
            {loading ? '⏳ Running Experiments...' : '🔬 Run All Experiments'}
          </button>
          {loading && (
            <p className="text-xs text-amber-600 font-medium">
              ⏳ Running on free hosting — this takes 2–3 minutes, please wait…
            </p>
          )}
        </div>
      </div>

      {/* Progress log */}
      {progress.length > 0 && (
        <div className="bg-gray-900 text-green-400 rounded-lg p-3 text-xs font-mono space-y-0.5 max-h-32 overflow-y-auto">
          {progress.map((line, i) => <div key={i}>{line}</div>)}
          {loading && <div className="animate-pulse">Running...</div>}
        </div>
      )}

      {/* Controls */}
      {hasResults && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex gap-4 items-center flex-wrap">
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">Scenario</label>
              <select
                value={selectedScenario}
                onChange={e => setSelectedScenario(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {scenarioError && (
                  <p className="text-sm text-red-600" role="alert">
                    {scenarioError}
                  </p>
                )}
                {scenarios
                  .filter(s => results[s])
                  .map(s => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, ' ')}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">Primary Metric</label>
              <select
                value={selectedMetric}
                onChange={e => setSelectedMetric(e.target.value)}
                className="border border-gray-300 rounded px-2 py-1 text-sm"
              >
                {METRICS.map(m => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
          </div>
        </div>
      )}

      {hasResults && (
        <>
          {/* Strategy Comparison Bar Chart — one bar per strategy for the selected metric */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">
              Strategy Comparison — {selectedScenario.replace(/_/g, ' ')}
            </h3>
            <p className="text-xs text-gray-400 mb-3">
              {activeMeta.label} · {activeMeta.lower ? 'lower is better ↓' : 'higher is better ↑'}
            </p>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="strategy" tick={{ fontSize: 13, fontWeight: 600 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => [v?.toFixed ? v.toFixed(3) : v, activeMeta.label]} />
                <Bar dataKey="value" name={activeMeta.label} radius={[4, 4, 0, 0]}>
                  {chartData.map(entry => (
                    <Cell key={entry.strategy} fill={STRATEGY_COLORS[entry.strategy]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Table (all scenarios) */}
          <div className="bg-white rounded-lg shadow p-4 overflow-x-auto">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700">Results Summary Table</h3>
              {statSummary && (
                <span className="text-xs text-gray-400 italic">σ = std dev · ±margin = 95% CI half-width</span>
              )}
            </div>
            <table className="min-w-full text-xs">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-2 px-3 text-gray-500">Scenario</th>
                  <th className="text-left py-2 px-3 text-gray-500">Strategy</th>
                  <th className="text-right py-2 px-3 text-gray-500">Search (min)</th>
                  {statSummary && <th className="text-right py-2 px-3 text-gray-400">σ / 95% CI</th>}
                  <th className="text-right py-2 px-3 text-gray-500">Wait (min)</th>
                  {statSummary && <th className="text-right py-2 px-3 text-gray-400">σ / 95% CI</th>}
                  <th className="text-right py-2 px-3 text-gray-500">Avg Queue</th>
                  <th className="text-right py-2 px-3 text-gray-500">Overflow</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(results).flatMap(([scenario, stratMap]) =>
                  STRATEGIES.map((s, si) => {
                    const m = stratMap[s] || {}
                    const isParkingNav = s === 'P'
                    // statSummary shape: { "scenario|strategy": { metrics: { metric: {mean,std,ci95,n} } } }
                    const ss = statSummary?.[`${scenario}|${s}`]
                    const fmtCI = (metric) => {
                      const d = ss?.metrics?.[metric]
                      if (!d) return '—'
                      const std = typeof d.std === 'number' ? d.std.toFixed(3) : '?'
                      // ci95 is a half-width margin: mean ± ci95
                      const margin = typeof d.ci95 === 'number' ? d.ci95.toFixed(3) : '?'
                      return <span className="text-gray-400 leading-tight">σ={std}<br/>±{margin}</span>
                    }
                    return (
                      <tr key={`${scenario}-${s}`} className={`border-b ${isParkingNav ? 'bg-green-50 font-semibold' : ''} ${si === 0 ? 'border-t-2 border-gray-300' : ''}`}>
                        <td className="py-1.5 px-3 text-gray-600">{si === 0 ? scenario.replace(/_/g, ' ') : ''}</td>
                        <td className="py-1.5 px-3">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${isParkingNav ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'}`}>{s}</span>
                        </td>
                        <td className="text-right py-1.5 px-3">{m.avg_search_time_min ?? '—'}</td>
                        {statSummary && <td className="text-right py-1.5 px-3 leading-tight">{fmtCI('avg_search_time_min')}</td>}
                        <td className="text-right py-1.5 px-3">{m.avg_wait_time_min ?? '—'}</td>
                        {statSummary && <td className="text-right py-1.5 px-3 leading-tight">{fmtCI('avg_wait_time_min')}</td>}
                        <td className="text-right py-1.5 px-3">{m.avg_gate_queue ?? '—'}</td>
                        <td className="text-right py-1.5 px-3">{m.overflow_events ?? '—'}</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!hasResults && !loading && (
        <div className="text-center py-20 bg-white rounded-lg shadow">
          <div className="text-4xl mb-3">🔬</div>

          <div className="text-gray-600">
            {scenarios.length > 0
              ? 'Run the experiments to view actual strategy comparisons.'
              : 'Waiting for available scenarios from the API.'}
          </div>

          <div className="text-xs text-gray-400 mt-2">
            Missing experiment results are not treated as zero.
          </div>
        </div>
      )}
    </div>
  )
}
