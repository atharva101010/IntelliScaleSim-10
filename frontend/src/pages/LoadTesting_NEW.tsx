import { useState, useEffect } from 'react'
import api from '../services/api'

interface Container {
    id: number
    name: string
    localhost_url?: string
    port?: number
}

interface LoadTestConfig {
    containerId: number | null
    totalRequests: number
    concurrency: number
    durationSeconds: number
}

interface LoadTestStatus {
    id: number
    status: string
    requests_sent?: number
    requests_completed?: number
    requests_failed?: number
}

interface LiveMetric {
    timestamp: string
    cpu_percent: number
    memory_mb: number
    requests_completed: number
    requests_failed: number
}

export default function LoadTesting() {
    const [containers, setContainers] = useState<Container[]>([])
    const [config, setConfig] = useState<LoadTestConfig>({
        containerId: null,
        totalRequests: 100,
        concurrency: 10,
        durationSeconds: 30
    })
    const [errors, setErrors] = useState<Record<string, string>>({})
    const [isRunning, setIsRunning] = useState(false)
    const [currentTest, setCurrentTest] = useState<LoadTestStatus | null>(null)
    const [liveMetrics, setLiveMetrics] = useState<LiveMetric[]>([])
    const [eventSource, setEventSource] = useState<EventSource | null>(null)

    const ACTIVE_TEST_KEY = 'active_load_test_id'

    useEffect(() => {
        fetchContainers()
        checkForRunningTest()
    }, [])

    const fetchContainers = async () => {
        try {
            const response = await api.listContainers('running')
            setContainers(response.containers || [])
        } catch (error) {
            console.error('Failed to fetch containers:', error)
        }
    }

    const checkForRunningTest = async () => {
        const testId = sessionStorage.getItem(ACTIVE_TEST_KEY)
        if (testId) {
            try {
                const token = localStorage.getItem('token')
                const response = await fetch(`/api/loadtest/${testId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                })

                if (response.ok) {
                    const data = await response.json()
                    if (data.status === 'running' || data.status === 'pending') {
                        setIsRunning(true)
                        setCurrentTest(data)
                        setupSSE(parseInt(testId))
                        pollTestStatus(parseInt(testId))
                    } else {
                        sessionStorage.removeItem(ACTIVE_TEST_KEY)
                    }
                }
            } catch (error) {
                console.error('Failed to restore running test:', error)
                sessionStorage.removeItem(ACTIVE_TEST_KEY)
            }
        }
    }

    const validateConfig = (): boolean => {
        const newErrors: Record<string, string> = {}
        if (!config.containerId) newErrors.container = 'Please select a container'
        if (config.totalRequests > 1000) newErrors.requests = 'Maximum 1000 requests'
        if (config.concurrency > 50) newErrors.concurrency = 'Maximum 50 concurrent'
        if (config.durationSeconds > 300) newErrors.duration = 'Maximum 300 seconds'
        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const startLoadTest = async () => {
        if (!validateConfig()) return

        try {
            const token = localStorage.getItem('token')
            const response = await fetch('/api/loadtest/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    container_id: config.containerId,
                    total_requests: config.totalRequests,
                    concurrency: config.concurrency,
                    duration_seconds: config.durationSeconds
                })
            })

            if (!response.ok) {
                const error = await response.json()
                alert(error.detail || 'Failed to start load test')
                return
            }

            const data = await response.json()
            setIsRunning(true)
            sessionStorage.setItem(ACTIVE_TEST_KEY, data.id.toString())
            pollTestStatus(data.id)
            setupSSE(data.id)
        } catch (error: any) {
            alert(error.message || 'An unexpected error occurred')
        }
    }

    const pollTestStatus = async (testId: number) => {
        const interval = setInterval(async () => {
            try {
                const token = localStorage.getItem('token')
                const response = await fetch(`/api/loadtest/${testId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                const data = await response.json()
                setCurrentTest(data)
                if (['completed', 'failed', 'cancelled'].includes(data.status)) {
                    clearInterval(interval)
                    setIsRunning(false)
                    sessionStorage.removeItem(ACTIVE_TEST_KEY)
                }
            } catch (error) {
                console.error('Failed to fetch test status:', error)
            }
        }, 2000)
    }

    const setupSSE = (testId: number) => {
        const token = localStorage.getItem('token')
        const es = new EventSource(`/api/loadtest/${testId}/metrics/stream?token=${token}`)
        es.onmessage = (event) => {
            const metric = JSON.parse(event.data)
            setLiveMetrics(prev => [...prev.slice(-50), metric])
        }
        setEventSource(es)
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 p-8">
            <div className="max-w-5xl mx-auto">
                {/* Premium Header */}
                <div className="mb-10">
                    <div className="flex items-center gap-4 mb-3">
                        <div className="w-14 h-14 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/30">
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-5xl font-black bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 bg-clip-text text-transparent">
                                Load Testing
                            </h1>
                            <p className="text-slate-600 text-lg mt-1">Simulate real-world traffic & measure performance</p>
                        </div>
                    </div>
                </div>

                {!isRunning ? (
                    <div className="bg-white rounded-[2rem] shadow-2xl border border-slate-200/60 p-10 backdrop-blur-xl">
                        {/* Card Header */}
                        <div className="flex items-center gap-4 mb-10 pb-6 border-b-2 border-slate-100">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                                </svg>
                            </div>
                            <h2 className="text-3xl font-bold text-slate-800">Configure Test Parameters</h2>
                        </div>

                        {/* Select Application */}
                        <div className="mb-10">
                            <label className="flex items-center gap-2 text-base font-bold text-slate-700 mb-4">
                                <svg className="w-6 h-6 text-violet-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                                </svg>
                                Target Application
                            </label>
                            <select
                                value={config.containerId || ''}
                                onChange={(e) => setConfig({ ...config, containerId: parseInt(e.target.value) })}
                                className="w-full px-6 py-4 text-lg border-2 border-slate-200 rounded-2xl focus:ring-4 focus:ring-violet-500/30 focus:border-violet-500 transition-all bg-gradient-to-br from-white to-slate-50 hover:border-slate-300 font-medium shadow-sm"
                            >
                                <option value="">Choose a running container...</option>
                                {containers.map(c => (
                                    <option key={c.id} value={c.id}>
                                        🚀 {c.name} - {c.localhost_url || `localhost:${c.port}`}
                                    </option>
                                ))}
                            </select>
                            {errors.container && <p className="text-red-600 text-sm mt-2 flex items-center gap-1 font-medium">⚠️ {errors.container}</p>}
                        </div>

                        {/* Number of Requests */}
                        <div className="mb-10">
                            <label className="flex items-center gap-2 text-base font-bold text-slate-700 mb-4">
                                <svg className="w-6 h-6 text-fuchsia-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                                </svg>
                                Total Requests
                            </label>
                            <div className="flex gap-6 items-center">
                                <input
                                    type="number"
                                    min="1"
                                    max="1000"
                                    value={config.totalRequests}
                                    onChange={(e) => setConfig({ ...config, totalRequests: Math.max(1, Math.min(1000, parseInt(e.target.value) || 1)) })}
                                    className="w-40 px-6 py-4 text-2xl font-bold border-2 border-fuchsia-200 rounded-2xl focus:ring-4 focus:ring-fuchsia-500/30 focus:border-fuchsia-500 transition-all bg-gradient-to-br from-white to-fuchsia-50 text-center shadow-sm"
                                />
                                <div className="flex-1">
                                    <input
                                        type="range"
                                        min="1"
                                        max="1000"
                                        step="10"
                                        value={config.totalRequests}
                                        onChange={(e) => setConfig({ ...config, totalRequests: parseInt(e.target.value) })}
                                        className="w-full h-4 rounded-full cursor-pointer appearance-none"
                                        style={{
                                            background: `linear-gradient(to right, #d946ef 0%, #d946ef ${(config.totalRequests / 1000) * 100}%, #e2e8f0 ${(config.totalRequests / 1000) * 100}%, #e2e8f0 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between mt-2 text-sm font-semibold text-slate-500">
                                        <span>1</span>
                                        <span className="text-fuchsia-600 text-base">🎯 {config.totalRequests} requests</span>
                                        <span>1000</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Concurrency Level */}
                        <div className="mb-10">
                            <label className="flex items-center gap-2 text-base font-bold text-slate-700 mb-4">
                                <svg className="w-6 h-6 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                Concurrency Level
                            </label>
                            <div className="flex gap-6 items-center">
                                <input
                                    type="number"
                                    min="1"
                                    max="50"
                                    value={config.concurrency}
                                    onChange={(e) => setConfig({ ...config, concurrency: Math.max(1, Math.min(50, parseInt(e.target.value) || 1)) })}
                                    className="w-40 px-6 py-4 text-2xl font-bold border-2 border-cyan-200 rounded-2xl focus:ring-4 focus:ring-cyan-500/30 focus:border-cyan-500 transition-all bg-gradient-to-br from-white to-cyan-50 text-center shadow-sm"
                                />
                                <div className="flex-1">
                                    <input
                                        type="range"
                                        min="1"
                                        max="50"
                                        value={config.concurrency}
                                        onChange={(e) => setConfig({ ...config, concurrency: parseInt(e.target.value) })}
                                        className="w-full h-4 rounded-full cursor-pointer appearance-none"
                                        style={{
                                            background: `linear-gradient(to right, #06b6d4 0%, #06b6d4 ${(config.concurrency / 50) * 100}%, #e2e8f0 ${(config.concurrency / 50) * 100}%, #e2e8f0 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between mt-2 text-sm font-semibold text-slate-500">
                                        <span>1</span>
                                        <span className="text-cyan-600 text-base">⚡ {config.concurrency} concurrent</span>
                                        <span>50</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Test Duration */}
                        <div className="mb-10">
                            <label className="flex items-center gap-2 text-base font-bold text-slate-700 mb-4">
                                <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Test Duration
                            </label>
                            <div className="flex gap-6 items-center">
                                <input
                                    type="number"
                                    min="10"
                                    max="300"
                                    value={config.durationSeconds}
                                    onChange={(e) => setConfig({ ...config, durationSeconds: Math.max(10, Math.min(300, parseInt(e.target.value) || 10)) })}
                                    className="w-40 px-6 py-4 text-2xl font-bold border-2 border-amber-200 rounded-2xl focus:ring-4 focus:ring-amber-500/30 focus:border-amber-500 transition-all bg-gradient-to-br from-white to-amber-50 text-center shadow-sm"
                                />
                                <div className="flex-1">
                                    <input
                                        type="range"
                                        min="10"
                                        max="300"
                                        value={config.durationSeconds}
                                        onChange={(e) => setConfig({ ...config, durationSeconds: parseInt(e.target.value) })}
                                        className="w-full h-4 rounded-full cursor-pointer appearance-none"
                                        style={{
                                            background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${(config.durationSeconds / 300) * 100}%, #e2e8f0 ${(config.durationSeconds / 300) * 100}%, #e2e8f0 100%)`
                                        }}
                                    />
                                    <div className="flex justify-between mt-2 text-sm font-semibold text-slate-500">
                                        <span>10s</span>
                                        <span className="text-amber-600 text-base">⏱️ {config.durationSeconds}s ({Math.floor(config.durationSeconds / 60)}m {config.durationSeconds % 60}s)</span>
                                        <span>300s</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Start Button */}
                        <button
                            onClick={startLoadTest}
                            disabled={!config.containerId}
                            className="w-full bg-gradient-to-r from-violet-600 via-fuchsia-600 to-pink-600 hover:from-violet-700 hover:via-fuchsia-700 hover:to-pink-700 text-white py-5 px-8 rounded-2xl font-black text-xl shadow-2xl shadow-fuchsia-500/40 hover:shadow-fuchsia-500/60 disabled:from-slate-300 disabled:to-slate-400 disabled:shadow-none disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3"
                        >
                            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Start Load Test
                        </button>
                    </div>
                ) : (
                    <div className="bg-white rounded-3xl shadow-xl p-8">
                        <h2 className="text-2xl font-bold mb-4">Test Running...</h2>
                        <p>Status: {currentTest?.status}</p>
                        <p>Requests sent: {currentTest?.requests_sent}</p>
                        <p>Completed: {currentTest?.requests_completed}</p>
                        <p>Failed: {currentTest?.requests_failed}</p>
                    </div>
                )}
            </div>
        </div>
    )
}
