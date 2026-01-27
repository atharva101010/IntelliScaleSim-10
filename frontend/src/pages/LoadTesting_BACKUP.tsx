import { useState, useEffect } from 'react'
import { api } from '../utils/api'

interface Container {
    id: number
    name: string
    status: string
    localhost_url?: string | null
    port?: number | null
}

interface LoadTestConfig {
    containerId: number | null
    totalRequests: number
    concurrency: number
    durationSeconds: number
}

interface LoadTestStatus {
    id: number
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
    progress_percent: number
    requests_completed: number
    requests_failed: number
    requests_sent: number
    avg_response_time_ms?: number
    peak_cpu_percent?: number
    peak_memory_mb?: number
}

interface LiveMetric {
    timestamp: string
    cpu: number
    memory: number
    completed: number
    failed: number
    progress: number
    active: number
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

    // Store active test ID in sessionStorage to persist across navigation
    const ACTIVE_TEST_KEY = 'active_load_test_id'

    // Fetch running containers
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

    // Check if there's a running test when component mounts
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
                    // Only restore if test is still running or pending
                    if (data.status === 'running' || data.status === 'pending') {
                        console.log('Restoring running test:', data)
                        setIsRunning(true)
                        setCurrentTest(data)
                        // Reconnect to SSE
                        setupSSE(parseInt(testId))
                        pollTestStatus(parseInt(testId))
                    } else {
                        // Test completed while we were away
                        sessionStorage.removeItem(ACTIVE_TEST_KEY)
                    }
                }
            } catch (error) {
                console.error('Failed to restore running test:', error)
                sessionStorage.removeItem(ACTIVE_TEST_KEY)
            }
        }
    }

    // Validate configuration
    const validateConfig = (): boolean => {
        const newErrors: Record<string, string> = {}

        if (!config.containerId) {
            newErrors.container = 'Please select a container'
        }

        if (config.totalRequests > 1000) {
            newErrors.requests = 'Maximum requests allowed: 1000'
        }

        if (config.concurrency > 50) {
            newErrors.concurrency = 'Concurrency cannot exceed: 50'
        }

        if (config.durationSeconds > 300) {
            newErrors.duration = 'Duration cannot exceed 5 minutes (300 seconds)'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    // Start load test
    const startLoadTest = async () => {
        console.log('Start Load Test button clicked!')
        console.log('Config:', config)

        if (!validateConfig()) {
            console.log('Validation failed')
            return
        }

        console.log('Validation passed, starting test...')

        try {
            const token = localStorage.getItem('token')
            console.log('Token:', token ? 'Present' : 'Missing')

            const requestBody = {
                container_id: config.containerId,
                total_requests: config.totalRequests,
                concurrency: config.concurrency,
                duration_seconds: config.durationSeconds
            }
            console.log('Request body:', requestBody)

            const response = await fetch('/api/loadtest/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(requestBody)
            })

            console.log('Response status:', response.status)
            console.log('Response ok:', response.ok)

            if (!response.ok) {
                const error = await response.json()
                console.error('Error response:', error)

                // Better error messages
                if (response.status === 401) {
                    alert('Authentication failed. Please log out and log in again.')
                } else {
                    alert(error.detail || 'Failed to start load test')
                }
                return
            }

            const data = await response.json()
            console.log('Success! Test started:', data)
            setIsRunning(true)

            // Save test ID to sessionStorage to persist across navigation
            sessionStorage.setItem(ACTIVE_TEST_KEY, data.id.toString())

            // Start polling for status and setup SSE
            pollTestStatus(data.id)
            setupSSE(data.id)

        } catch (error: any) {
            console.error('Load test error:', error)
            alert(error.message || 'An unexpected error occurred')
        }
    }

    // Poll test status
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
                    // Clear sessionStorage when test finishes
                    sessionStorage.removeItem(ACTIVE_TEST_KEY)
                }
            } catch (error) {
                console.error('Failed to fetch test status:', error)
            }
        }, 2000)
    }

    // Setup Server-Sent Events for live metrics
    const setupSSE = (testId: number) => {
        const token = localStorage.getItem('token')
        const es = new EventSource(`/api/loadtest/${testId}/metrics/stream?token=${token}`)

        es.addEventListener('metric', (event) => {
            const metric: LiveMetric = JSON.parse(event.data)
            setLiveMetrics(prev => [...prev.slice(-29), metric])
        })

        es.addEventListener('complete', () => {
            es.close()
            setIsRunning(false)
        })

        es.onerror = () => {
            es.close()
            setEventSource(null)
        }

        setEventSource(es)
    }

    // Cleanup SSE on unmount
    useEffect(() => {
        return () => {
            if (eventSource) {
                eventSource.close()
            }
        }
    }, [eventSource])

    const selectedContainer = containers.find(c => c.id === config.containerId)

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <h1 className="text-3xl font-bold text-slate-900 mb-8">Load Testing</h1>

            {!isRunning ? (
                // Configuration Form
                <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                    <h2 className="text-xl font-semibold text-slate-900 mb-6">Configure Load Test</h2>

                    {/* Container Selection */}
                    <div className="mb-6">
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Select Application
                        </label>
                        <select
                            value={config.containerId || ''}
                            onChange={(e) => setConfig({ ...config, containerId: parseInt(e.target.value) })}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                        >
                            <option value="">Choose a running container...</option>
                            {containers.map(container => (
                                <option key={container.id} value={container.id}>
                                    {container.name} - {container.localhost_url || `localhost:${container.port}`}
                                </option>
                            ))}
                        </select>
                        {errors.container && <p className="text-red-600 text-sm mt-1">{errors.container}</p>}
                    </div>

                    {/* Number of Requests */}
                    <div className="mb-6">
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Number of Requests
                        </label>
                        <div className="flex gap-4 items-center mb-2">
                            <input
                                type="number"
                                min="1"
                                max="1000"
                                value={config.totalRequests}
                                onChange={(e) => setConfig({ ...config, totalRequests: Math.max(1, Math.min(1000, parseInt(e.target.value) || 1)) })}
                                className="w-32 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                            />
                            <input
                                type="range"
                                min="1"
                                max="1000"
                                step="10"
                                value={config.totalRequests}
                                onChange={(e) => setConfig({ ...config, totalRequests: parseInt(e.target.value) })}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-500"
                            />
                        </div>
                        <div className="flex justify-between text-xs text-slate-500">
                            <span>1</span>
                            <span>1000</span>
                        </div>
                        {errors.requests && <p className="text-red-600 text-sm mt-1">{errors.requests}</p>}
                    </div>

                    {/* Concurrency Level */}
                    <div className="mb-6">
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Concurrency Level
                        </label>
                        <div className="flex gap-4 items-center mb-2">
                            <input
                                type="number"
                                min="1"
                                max="50"
                                value={config.concurrency}
                                onChange={(e) => setConfig({ ...config, concurrency: Math.max(1, Math.min(50, parseInt(e.target.value) || 1)) })}
                                className="w-32 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                            />
                            <input
                                type="range"
                                min="1"
                                max="50"
                                value={config.concurrency}
                                onChange={(e) => setConfig({ ...config, concurrency: parseInt(e.target.value) })}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-500"
                            />
                        </div>
                        <div className="flex justify-between text-xs text-slate-500">
                            <span>1</span>
                            <span>50</span>
                        </div>
                        {errors.concurrency && <p className="text-red-600 text-sm mt-1">{errors.concurrency}</p>}
                    </div>

                    {/* Test Duration */}
                    <div className="mb-6">
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Test Duration (seconds)
                        </label>
                        <div className="flex gap-4 items-center mb-2">
                            <input
                                type="number"
                                min="10"
                                max="300"
                                value={config.durationSeconds}
                                onChange={(e) => setConfig({ ...config, durationSeconds: Math.max(10, Math.min(300, parseInt(e.target.value) || 10)) })}
                                className="w-32 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                            />
                            <input
                                type="range"
                                min="10"
                                max="300"
                                value={config.durationSeconds}
                                onChange={(e) => setConfig({ ...config, durationSeconds: parseInt(e.target.value) })}
                                className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-rose-500"
                            />
                        </div>
                        <div className="flex justify-between text-xs text-slate-500">
                            <span>10s</span>
                            <span>300s (5 min)</span>
                        </div>
                        {errors.duration && <p className="text-red-600 text-sm mt-1">{errors.duration}</p>}
                    </div>

                    {/* Start Button */}
                    <button
                        onClick={startLoadTest}
                        disabled={!config.containerId}
                        className="w-full bg-rose-500 text-white py-3 px-6 rounded-lg font-semibold hover:bg-rose-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                    >
                        Start Load Test
                    </button>
                </div>
            ) : (
                // Live Dashboard
                <div className="space-y-6">
                    {/* Progress Bar */}
                    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                        <h2 className="text-xl font-semibold text-slate-900 mb-4">Test Progress</h2>
                        <div className="mb-2">
                            <div className="flex justify-between text-sm text-slate-600 mb-2">
                                <span>Progress</span>
                                <span className="font-semibold">{Math.round(currentTest?.progress_percent || 0)}%</span>
                            </div>
                            <div className="w-full bg-slate-200 rounded-full h-4">
                                <div
                                    className="bg-gradient-to-r from-rose-500 to-pink-500 h-4 rounded-full transition-all duration-300"
                                    style={{ width: `${currentTest?.progress_percent || 0}%` }}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-3 gap-4 mt-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-slate-900">{currentTest?.requests_completed || 0}</div>
                                <div className="text-sm text-slate-600">Completed</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-red-600">{currentTest?.requests_failed || 0}</div>
                                <div className="text-sm text-slate-600">Failed</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                    {liveMetrics[liveMetrics.length - 1]?.active || 0}
                                </div>
                                <div className="text-sm text-slate-600">Active</div>
                            </div>
                        </div>
                    </div>

                    {/* CPU & Memory Graphs */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">CPU Usage</h3>
                            <div className="h-48 flex items-end space-x-1">
                                {liveMetrics.slice(-20).map((metric, idx) => (
                                    <div
                                        key={idx}
                                        className="flex-1 bg-gradient-to-t from-rose-500 to-pink-400 rounded-t"
                                        style={{ height: `${(metric.cpu / 100) * 100}%` }}
                                    />
                                ))}
                            </div>
                            <div className="text-center mt-2 text-sm text-slate-600">
                                Current: {liveMetrics[liveMetrics.length - 1]?.cpu.toFixed(1) || 0}%
                            </div>
                        </div>

                        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">Memory Usage</h3>
                            <div className="h-48 flex items-end space-x-1">
                                {liveMetrics.slice(-20).map((metric, idx) => (
                                    <div
                                        key={idx}
                                        className="flex-1 bg-gradient-to-t from-blue-500 to-cyan-400 rounded-t"
                                        style={{ height: `${(metric.memory / 500) * 100}%` }}
                                    />
                                ))}
                            </div>
                            <div className="text-center mt-2 text-sm text-slate-600">
                                Current: {liveMetrics[liveMetrics.length - 1]?.memory.toFixed(0) || 0} MB
                            </div>
                        </div>
                    </div>

                    {/* Results (shown when complete) */}
                    {currentTest?.status === 'completed' && (
                        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
                            <h2 className="text-xl font-semibold text-slate-900 mb-6">Test Results</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Total Requests</div>
                                    <div className="text-2xl font-bold text-slate-900">{currentTest.requests_sent}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Completed</div>
                                    <div className="text-2xl font-bold text-green-600">{currentTest.requests_completed}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Failed</div>
                                    <div className="text-2xl font-bold text-red-600">{currentTest.requests_failed}</div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Avg Response Time</div>
                                    <div className="text-2xl font-bold text-blue-600">
                                        {currentTest.avg_response_time_ms?.toFixed(0) || 0}ms
                                    </div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Peak CPU</div>
                                    <div className="text-2xl font-bold text-orange-600">
                                        {currentTest.peak_cpu_percent?.toFixed(1) || 0}%
                                    </div>
                                </div>
                                <div>
                                    <div className="text-sm text-slate-600 mb-1">Peak Memory</div>
                                    <div className="text-2xl font-bold text-purple-600">
                                        {currentTest.peak_memory_mb?.toFixed(0) || 0} MB
                                    </div>
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    setIsRunning(false)
                                    setCurrentTest(null)
                                    setLiveMetrics([])
                                }}
                                className="mt-6 w-full bg-rose-500 text-white py-2 px-4 rounded-lg font-semibold hover:bg-rose-600"
                            >
                                Run Another Test
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
