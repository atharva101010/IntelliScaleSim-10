import { useState, useEffect } from 'react'
import { monitoring, ContainerStats, MonitoringOverview } from '../utils/api'

export default function Monitoring() {
    const [overview, setOverview] = useState<MonitoringOverview | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchData = async () => {
        try {
            console.log('Fetching monitoring data...')
            const data = await monitoring.getOverview()
            console.log('Monitoring data received:', data)
            setOverview(data)
            setError(null)
        } catch (err: any) {
            console.error('Error fetching monitoring data:', err)
            console.error('Error message:', err?.message)
            console.error('Error response:', err?.response)

            // Set error message for display
            setError(err?.message || 'Failed to fetch monitoring data')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()

        // Auto-refresh every 3 seconds
        const interval = setInterval(fetchData, 3000)

        return () => clearInterval(interval)
    }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-96">
                <div className="text-center">
                    <div className="inline-block w-12 h-12 border-4 border-rose-200 border-t-rose-600 rounded-full animate-spin"></div>
                    <p className="mt-4 text-slate-600">Loading metrics...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{error}</p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">📊 Real-Time Monitoring</h1>
                    <p className="text-slate-600 mt-1">Live container metrics and resource usage</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span>Live (updates every 3s)</span>
                    </div>
                    <a
                        href="http://localhost:3000/d/intelliscalesim-containers/intelliscalesim-container-monitoring?orgId=1&refresh=5s"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-pink-500 text-white font-semibold rounded-lg shadow-md hover:from-orange-600 hover:to-pink-600 transition-all duration-200 hover:shadow-lg"
                    >
                        <span>📊</span>
                        <span>View in Grafana</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                    </a>
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <OverviewCard
                    title="Total Containers"
                    value={overview?.total_containers || 0}
                    icon="📦"
                    color="blue"
                />
                <OverviewCard
                    title="Running"
                    value={overview?.running_containers || 0}
                    icon="✅"
                    color="green"
                />
                <OverviewCard
                    title="Total CPU Usage"
                    value={`${overview?.total_cpu_percent.toFixed(1) || 0}%`}
                    icon="⚡"
                    color="purple"
                />
                <OverviewCard
                    title="Total Memory"
                    value={`${overview?.total_memory_usage_mb.toFixed(0) || 0} MB`}
                    icon="💾"
                    color="orange"
                />
            </div>

            {/* Container Metrics */}
            {overview?.containers_stats && overview.containers_stats.length > 0 ? (
                <div className="space-y-4">
                    <h2 className="text-xl font-bold text-slate-800">Container Metrics</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {overview.containers_stats.map((stats) => (
                            <ContainerMetricsCard key={stats.id} stats={stats} />
                        ))}
                    </div>
                </div>
            ) : (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-12 text-center">
                    <div className="text-6xl mb-4">🚀</div>
                    <h3 className="text-xl font-semibold text-slate-700 mb-2">No Running Containers</h3>
                    <p className="text-slate-600">Deploy a container to see real-time metrics</p>
                </div>
            )}
        </div>
    )
}

function OverviewCard({ title, value, icon, color }: { title: string; value: string | number; icon: string; color: string }) {
    const colorClasses = {
        blue: 'from-blue-500 to-blue-600',
        green: 'from-green-500 to-green-600',
        purple: 'from-purple-500 to-purple-600',
        orange: 'from-orange-500 to-orange-600',
    }[color]

    return (
        <div className={`bg-gradient-to-br ${colorClasses} rounded-xl p-6 text-white shadow-lg`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-3xl">{icon}</span>
                <div className="text-right">
                    <div className="text-3xl font-bold">{value}</div>
                </div>
            </div>
            <div className="text-sm opacity-90">{title}</div>
        </div>
    )
}

function ContainerMetricsCard({ stats }: { stats: ContainerStats }) {
    const getCPUColor = (percent: number) => {
        if (percent >= 80) return 'bg-red-500'
        if (percent >= 50) return 'bg-yellow-500'
        return 'bg-green-500'
    }

    const getMemoryColor = (percent: number) => {
        if (percent >= 80) return 'bg-red-500'
        if (percent >= 50) return 'bg-yellow-500'
        return 'bg-green-500'
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h3 className="text-lg font-bold text-slate-800">{stats.name}</h3>
                    <p className="text-sm text-slate-500 font-mono">{stats.container_id?.substring(0, 12)}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                    {stats.status}
                </span>
            </div>

            <div className="space-y-4">
                {/* CPU Usage */}
                <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                        <span className="font-medium text-slate-700">⚡ CPU Usage</span>
                        <span className="font-bold text-slate-900">{stats.cpu_percent.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${getCPUColor(stats.cpu_percent)}`}
                            style={{ width: `${Math.min(stats.cpu_percent, 100)}%` }}
                        />
                    </div>
                </div>

                {/* Memory Usage */}
                <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                        <span className="font-medium text-slate-700">💾 Memory Usage</span>
                        <span className="font-bold text-slate-900">
                            {stats.memory_usage_mb.toFixed(0)} MB / {stats.memory_limit_mb.toFixed(0)} MB
                            ({stats.memory_percent.toFixed(1)}%)
                        </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${getMemoryColor(stats.memory_percent)}`}
                            style={{ width: `${Math.min(stats.memory_percent, 100)}%` }}
                        />
                    </div>
                </div>

                {/* Network Stats */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
                    <div>
                        <div className="text-xs text-slate-500 mb-1">📥 Network RX</div>
                        <div className="font-semibold text-slate-800">{stats.network_rx_mb.toFixed(2)} MB</div>
                    </div>
                    <div>
                        <div className="text-xs text-slate-500 mb-1">📤 Network TX</div>
                        <div className="font-semibold text-slate-800">{stats.network_tx_mb.toFixed(2)} MB</div>
                    </div>
                </div>
            </div>

            <div className="mt-3 text-xs text-slate-400">
                Last updated: {new Date(stats.timestamp).toLocaleTimeString()}
            </div>
        </div>
    )
}
