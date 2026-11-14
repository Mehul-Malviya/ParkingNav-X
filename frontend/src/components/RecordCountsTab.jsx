import React, { useEffect, useState } from 'react'
import { api, getWriteKey, setWriteKey } from '../api'

const nowLocal = () => {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

function StatCard({ label, value, sub, color = 'text-gray-800' }) {
  return (
    <div className="text-center p-3 bg-white rounded border">
      <div className={`text-xl font-bold ${color}`}>{value ?? '—'}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

function Section({ title, badge, children }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        {badge && <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">{badge}</span>}
      </div>
      {children}
    </div>
  )
}

export default function RecordCountsTab() {
  const [summary, setSummary] = useState(null)
  const [summaryError, setSummaryError] = useState('')

  // Manual count form state
  const [lots, setLots] = useState([])
  const [lotId, setLotId] = useState('')
  const [occupied, setOccupied] = useState('')
  const [when, setWhen] = useState(nowLocal())
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const [key, setKey] = useState(getWriteKey())
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    api.getDataSummary()
      .then(r => setSummary(r.data))
      .catch(() => setSummaryError('Could not load dataset summary — is the backend running?'))

    api.getCampus().then(r => {
      const l = r.data.parking_lots ?? []
      setLots(l)
      if (l.length) setLotId(l[0].id)
    }).catch(() => {})
  }, [])

  const lot = lots.find(l => l.id === lotId)
  const cap = lot?.usable_capacity

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api.recordObservation({ timestamp: when, lot_id: lotId, occupied_spaces: Number(occupied), source: 'manual' })
      setStatus({ ok: true, text: `Saved: ${lot?.name} — ${occupied} of ${cap} spaces at ${when.replace('T', ' ')}.` })
      setOccupied('')
      setWhen(nowLocal())
      // Refresh summary
      api.getDataSummary().then(r => setSummary(r.data)).catch(() => {})
    } catch (err) {
      setStatus({ ok: false, text: err.response?.status === 401 ? 'Wrong or missing access key.' : (err.response?.data?.detail || 'Could not save the count.') })
    } finally { setBusy(false) }
  }

  const retrain = async () => {
    setBusy(true)
    try {
      const r = (await api.retrainPredictor()).data
      setStatus({ ok: true, text: r.real_lots?.length ? `Forecast refitted on real data for ${r.real_lots.length} lot(s).` : 'Forecast refitted. All lots still use synthetic data (need 1 week of readings).' })
    } catch { setStatus({ ok: false, text: 'Retraining failed.' }) }
    finally { setBusy(false) }
  }

  const obs = summary?.occupancy_history
  const cfg = summary?.campus_config
  const syn = summary?.synthetic_training_data
  const sim = summary?.simulation_runs
  const exp = summary?.experiment_results

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-800">Dataset Overview &amp; Record Counts</h2>
        <p className="text-sm text-gray-500">Live record counts from the database. All figures fetched from backend — none are hardcoded.</p>
      </div>

      {summaryError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">{summaryError}</div>
      )}

      {/* Occupancy History */}
      {obs && (
        <Section title="Parking Occupancy History" badge={`${obs.total.toLocaleString()} records`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <StatCard label="Total Records" value={obs.total.toLocaleString()} color="text-blue-700" />
            <StatCard label="Real / Manual" value={obs.real_manual.toLocaleString()} color="text-green-700"
              sub="source ≠ simulation/synthetic" />
            <StatCard label="Simulated / Synthetic" value={obs.simulated_synthetic.toLocaleString()} color="text-orange-600" />
            <StatCard label="Null Values" value={obs.null_values} color={obs.null_values > 0 ? 'text-red-600' : 'text-gray-500'} />
          </div>
          <div className="text-xs text-gray-500 space-y-0.5">
            <div><span className="font-medium">Source:</span> {obs.source}</div>
            {obs.date_range?.from && <div><span className="font-medium">Date range:</span> {obs.date_range.from?.slice(0,16)} → {obs.date_range.to?.slice(0,16)}</div>}
            <div><span className="font-medium">Data quality:</span> {obs.null_values === 0 ? '✅ No null occupied_spaces values' : `⚠️ ${obs.null_values} null values`}</div>
          </div>
        </Section>
      )}

      {/* Campus Configuration */}
      {cfg && (
        <Section title="Campus Configuration" badge="OSM-calibrated">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <StatCard label="Parking Lots" value={cfg.parking_lots} color="text-blue-700" />
            <StatCard label="Gates" value={cfg.gates} />
            <StatCard label="Road Segments" value={cfg.roads} />
            <StatCard label="Destinations" value={cfg.destinations} />
          </div>
          <div className="text-xs text-gray-500 space-y-0.5">
            <div><span className="font-medium">Source:</span> {cfg.source}</div>
            <div><span className="font-medium">Generation:</span> {cfg.generation}</div>
          </div>
        </Section>
      )}

      {/* Synthetic Training Data */}
      {syn && (
        <Section title="Synthetic Training Data" badge="Calibrated model">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
            <StatCard label="Training Rows" value={syn.rows.toLocaleString()} color="text-purple-700" />
            <StatCard label="Last Generated" value={syn.last_generated?.slice(0,16) ?? 'unknown'} />
            <StatCard label="Data Source" value="Synthetic" color="text-orange-600" sub="Clearly labelled" />
          </div>
          <div className="text-xs text-gray-500 space-y-0.5">
            <div><span className="font-medium">Method:</span> {syn.source}</div>
            <div><span className="font-medium">Code:</span> {syn.generation}</div>
            <div><span className="font-medium">Note:</span> {syn.note}</div>
          </div>
        </Section>
      )}

      {/* Simulations & Experiments */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sim && (
          <Section title="Simulation Runs">
            <StatCard label="Total Runs" value={sim.total} color="text-blue-700" sub={sim.source} />
          </Section>
        )}
        {exp && (
          <Section title="Experiment Results">
            <StatCard label="Result Records" value={exp.total_runs} color="text-green-700" sub={exp.source} />
          </Section>
        )}
      </div>

      {/* Data Integrity */}
      {summary?.data_integrity && (
        <Section title="Data Integrity Checks">
          <div className="space-y-1 text-xs">
            {Object.entries(summary.data_integrity).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2">
                <span>{v ? '✅' : '❌'}</span>
                <span className="text-gray-600">{k.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Manual Count Entry — collapsible */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <button onClick={() => setShowForm(f => !f)}
          className="w-full flex items-center justify-between p-4 text-sm font-semibold text-gray-700 hover:bg-gray-50">
          <span>📝 Submit a Manual Parking Count</span>
          <span className="text-gray-400">{showForm ? '▲' : '▼'}</span>
        </button>
        {showForm && (
          <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
            <p className="text-xs text-gray-500">Count the vehicles in a lot and submit. A count adjusts that lot's forecast for 30 minutes and trains the model once a lot has a week of readings.</p>
            <form onSubmit={submit} className="space-y-3">
              <label className="block text-sm">
                <span className="text-gray-600">Parking lot</span>
                <select value={lotId} onChange={e => setLotId(e.target.value)} className="mt-1 w-full border border-gray-300 rounded px-2 py-1.5">
                  {lots.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-gray-600">Vehicles parked now{cap ? ` (0–${cap})` : ''}</span>
                <input type="number" min="0" max={cap} required value={occupied} onChange={e => setOccupied(e.target.value)} className="mt-1 w-full border border-gray-300 rounded px-2 py-1.5" />
              </label>
              <label className="block text-sm">
                <span className="text-gray-600">Time of count</span>
                <input type="datetime-local" required value={when} onChange={e => setWhen(e.target.value)} className="mt-1 w-full border border-gray-300 rounded px-2 py-1.5" />
              </label>
              <label className="block text-sm">
                <span className="text-gray-600">Access key <span className="text-gray-400">(if required)</span></span>
                <input type="password" value={key} autoComplete="off" onChange={e => { setKey(e.target.value); setWriteKey(e.target.value) }} className="mt-1 w-full border border-gray-300 rounded px-2 py-1.5" />
              </label>
              <div className="flex gap-2">
                <button type="submit" disabled={busy || !lotId} className="bg-vitap-blue text-white text-sm px-4 py-2 rounded disabled:opacity-50">Save count</button>
                <button type="button" onClick={retrain} disabled={busy} className="border border-gray-300 text-gray-700 text-sm px-4 py-2 rounded disabled:opacity-50">Refit forecast</button>
              </div>
            </form>
            {status && (
              <div className={`text-sm rounded p-3 border ${status.ok ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                {status.text}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
