import { useEffect, useMemo, useRef, useState } from 'react'

type Analysis = {
  impacted_symbols: string[]
  direction: string
  confidence: number
  horizon: string
  rationale: string[]
  tags: string[]
  entities: string[]
  topics: string[]
  scoring: Record<string, unknown>
}

type NewsItem = {
  id: number
  source: string
  url: string
  title: string
  summary?: string
  published_at?: string
  fetched_at: string
  language?: string
  analysis?: Analysis
}

type SourceStatus = {
  ok: boolean
  last_fetch?: string
  error?: string | null
}

const directionColor: Record<string, string> = {
  bullish: 'text-emerald-400',
  bearish: 'text-rose-400',
  mixed: 'text-amber-400',
  uncertain: 'text-slate-300',
}

export default function App() {
  const [items, setItems] = useState<NewsItem[]>([])
  const [selected, setSelected] = useState<NewsItem | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [paused, setPaused] = useState(false)
  const [symbolFilter, setSymbolFilter] = useState('')
  const [minConfidence, setMinConfidence] = useState(0)
  const [sourceFilter, setSourceFilter] = useState('')
  const [sources, setSources] = useState<string[]>([])
  const [status, setStatus] = useState<Record<string, SourceStatus>>({})
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/news')
      .then((res) => res.json())
      .then((data: NewsItem[]) => {
        setItems(data)
        if (data.length > 0) {
          setSelected(data[0])
        }
      })
    fetch('/api/sources')
      .then((res) => res.json())
      .then((data) => setSources(data.map((source: { name: string }) => source.name)))
    const eventSource = new EventSource('/api/stream')
    eventSource.onmessage = (event) => {
      const parsed: NewsItem = JSON.parse(event.data)
      setItems((prev) => [parsed, ...prev].slice(0, 200))
      if (!paused) {
        setSelected(parsed)
      }
    }
    return () => eventSource.close()
  }, [paused])

  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = 0
    }
  }, [items, autoScroll])

  useEffect(() => {
    const interval = setInterval(() => {
      fetch('/api/sources/status')
        .then((res) => res.json())
        .then((data) => setStatus(data))
        .catch(() => null)
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const analysis = item.analysis
      if (!analysis) return false
      if (symbolFilter && !analysis.impacted_symbols.includes(symbolFilter)) return false
      if (sourceFilter && item.source !== sourceFilter) return false
      if (analysis.confidence < minConfidence) return false
      return true
    })
  }, [items, symbolFilter, sourceFilter, minConfidence])

  const heatmap = useMemo(() => {
    const summary: Record<string, number> = {}
    const cutoff = Date.now() - 60 * 60 * 1000
    items.forEach((item) => {
      if (!item.analysis) return
      const time = new Date(item.fetched_at).getTime()
      if (time < cutoff) return
      item.analysis.impacted_symbols.forEach((symbol) => {
        const delta = item.analysis?.direction === 'bullish' ? 1 : item.analysis?.direction === 'bearish' ? -1 : 0
        summary[symbol] = (summary[symbol] ?? 0) + delta
      })
    })
    return summary
  }, [items])

  return (
    <div className="min-h-screen p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Forex News Impact Tracker</h1>
          <p className="text-slate-400">Live macro, FX, commodities, and crypto impact signals.</p>
        </div>
        <div className="flex gap-3 items-center">
          <button
            className="px-3 py-2 rounded bg-slate-800"
            onClick={() => setAutoScroll((prev) => !prev)}
          >
            Auto-scroll: {autoScroll ? 'On' : 'Off'}
          </button>
          <button
            className="px-3 py-2 rounded bg-slate-800"
            onClick={() => setPaused((prev) => !prev)}
          >
            {paused ? 'Resume' : 'Pause'}
          </button>
        </div>
      </header>

      <section className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-2 bg-slate-900 rounded p-4 space-y-3">
          <h2 className="font-semibold">Filters</h2>
          <div className="space-y-2">
            <label className="text-xs text-slate-400">Symbol</label>
            <input
              className="w-full px-2 py-1 rounded bg-slate-800"
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              placeholder="XAU/USD"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-slate-400">Source</label>
            <select
              className="w-full px-2 py-1 rounded bg-slate-800"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
            >
              <option value="">All</option>
              {sources.map((source) => (
                <option key={source} value={source}>
                  {source}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs text-slate-400">Min confidence</label>
            <input
              className="w-full"
              type="range"
              min={0}
              max={100}
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
            />
            <div className="text-xs text-slate-300">{minConfidence}</div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 bg-slate-900 rounded p-4">
          <h2 className="font-semibold mb-3">Live Feed</h2>
          <div ref={feedRef} className="h-[420px] overflow-y-auto space-y-3 pr-2">
            {filteredItems.map((item) => (
              <button
                key={item.id}
                className={`w-full text-left p-3 rounded bg-slate-800 hover:bg-slate-700 ${selected?.id === item.id ? 'ring-2 ring-emerald-400' : ''}`}
                onClick={() => setSelected(item)}
              >
                <div className="flex justify-between text-xs text-slate-400">
                  <span>{item.source}</span>
                  <span>{new Date(item.fetched_at).toLocaleTimeString()}</span>
                </div>
                <div className="font-medium mt-1">{item.title}</div>
                <div className="text-xs text-slate-400">{item.analysis?.impacted_symbols.join(', ')}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-6 bg-slate-900 rounded p-4">
          <h2 className="font-semibold mb-3">Impact Cards</h2>
          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
            {filteredItems.map((item) => (
              <div key={`card-${item.id}`} className="p-4 rounded bg-slate-800">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-lg font-semibold">{item.title}</div>
                    <div className="text-xs text-slate-400">{item.source}</div>
                  </div>
                  <div className={`text-sm font-semibold ${directionColor[item.analysis?.direction ?? 'uncertain']}`}>
                    {item.analysis?.direction ?? 'uncertain'}
                  </div>
                </div>
                <div className="mt-2 text-sm text-slate-300">{item.summary}</div>
                <div className="mt-3 grid grid-cols-3 gap-3 text-xs">
                  <div>
                    <div className="text-slate-400">Symbols</div>
                    <div>{item.analysis?.impacted_symbols.join(', ')}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Confidence</div>
                    <div>{item.analysis?.confidence}</div>
                  </div>
                  <div>
                    <div className="text-slate-400">Horizon</div>
                    <div>{item.analysis?.horizon}</div>
                  </div>
                </div>
                <div className="mt-3 text-xs text-slate-400">Tags: {item.analysis?.tags.join(', ')}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4 bg-slate-900 rounded p-4">
          <h2 className="font-semibold mb-2">Source Status</h2>
          <div className="space-y-2 text-sm">
            {Object.entries(status).length === 0 && <div className="text-slate-400">Awaiting updates...</div>}
            {Object.entries(status).map(([id, statusItem]) => (
              <div key={id} className="flex justify-between">
                <div>
                  <div>Source #{id}</div>
                  <div className="text-xs text-slate-400">{statusItem.last_fetch ?? 'n/a'}</div>
                </div>
                <span className={statusItem.ok ? 'text-emerald-400' : 'text-rose-400'}>
                  {statusItem.ok ? 'ok' : 'failing'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 bg-slate-900 rounded p-4">
          <h2 className="font-semibold mb-2">Heatmap (last 60m)</h2>
          <div className="space-y-2 text-sm">
            {Object.entries(heatmap).map(([symbol, score]) => (
              <div key={symbol} className="flex justify-between">
                <span>{symbol}</span>
                <span className={score > 0 ? 'text-emerald-400' : score < 0 ? 'text-rose-400' : 'text-slate-300'}>
                  {score}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 bg-slate-900 rounded p-4">
          <h2 className="font-semibold mb-2">Explainability</h2>
          {selected ? (
            <div className="space-y-3 text-sm">
              <div>
                <div className="text-slate-400">Entities</div>
                <div>{selected.analysis?.entities.join(', ') || 'n/a'}</div>
              </div>
              <div>
                <div className="text-slate-400">Topics</div>
                <div>{selected.analysis?.topics.join(', ') || 'n/a'}</div>
              </div>
              <div>
                <div className="text-slate-400">Scoring breakdown</div>
                <pre className="text-xs bg-slate-800 p-2 rounded overflow-auto">
                  {JSON.stringify(selected.analysis?.scoring, null, 2)}
                </pre>
              </div>
              <div>
                <div className="text-slate-400">Rationale</div>
                <ul className="list-disc ml-4">
                  {selected.analysis?.rationale.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-slate-400">Select an item to see details.</div>
          )}
        </div>
      </section>
    </div>
  )
}
