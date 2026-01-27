import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import axios from 'axios'

interface ScalingPolicy {
    id: number
    container_id: number
    enabled: boolean
    scale_up_cpu_threshold: number
    scale_up_memory_threshold: number
    scale_down_cpu_threshold: number
    scale_down_memory_threshold: number
    min_replicas: number
    max_replicas: number
    cooldown_period: number
    evaluation_period: number
    load_balancer_enabled: boolean
    load_balancer_port: number | null
    created_at: string
    last_scaled_at: string | null
}

interface ScalingEvent {
    id: number
    policy_id: number
    container_id: number
    action: string
    trigger_metric: string
    metric_value: number
    replica_count_before: number
    replica_count_after: number
    created_at: string
}

interface Container {
    id: number
    name: string
    status: string
}

export default function AutoScaling() {
    const { token } = useAuth()
    const [policies, setPolicies] = useState<ScalingPolicy[]>([])
    const [events, setEvents] = useState<ScalingEvent[]>([])
    const [containers, setContainers] = useState<Container[]>([])
    const [loading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false)

    // Form state
    const [formData, setFormData] = useState({
        container_id: '',
        scale_up_cpu_threshold: 80,
        scale_up_memory_threshold: 80,
        scale_down_cpu_threshold: 30,
        scale_down_memory_threshold: 30,
        min_replicas: 1,
        max_replicas: 8,
        cooldown_period: 300,
        evaluation_period: 60,
        load_balancer_enabled: true,
        load_balancer_port: ''
    })

    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

    useEffect(() => {
        fetchPolicies()
        fetchEvents()
        fetchContainers()
    }, [])

    const fetchContainers = async () => {
        try {
            console.log('Fetching containers from:', `${API_BASE}/containers`)
            const res = await axios.get(`${API_BASE}/containers`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            console.log('Containers API response:', res.data)
            console.log('Is array?', Array.isArray(res.data))
            console.log('Length:', res.data?.length)

            // Handle both array and object responses
            let containerList: Container[] = []
            if (Array.isArray(res.data)) {
                containerList = res.data
            } else if (res.data && typeof res.data === 'object') {
                // Maybe it's wrapped in an object like { containers: [...] }
                containerList = res.data.containers || Object.values(res.data)
            }

            console.log('Final container list:', containerList)
            setContainers(containerList)
        } catch (error) {
            console.error('Error fetching containers:', error)
            setContainers([]) // Set empty array on error
        }
    }

    const fetchPolicies = async () => {
        try {
            const res = await axios.get(`${API_BASE}/autoscaling/policies`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setPolicies(res.data)
        } catch (error) {
            console.error('Error fetching policies:', error)
        } finally {
            setLoading(false)
        }
    }

    const fetchEvents = async () => {
        try {
            const res = await axios.get(`${API_BASE}/autoscaling/events?limit=10`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            setEvents(res.data)
        } catch (error) {
            console.error('Error fetching events:', error)
        }
    }

    const createPolicy = async (e: React.FormEvent) => {
        e.preventDefault()

        try {
            const payload = {
                ...formData,
                container_id: parseInt(formData.container_id),
                load_balancer_port: formData.load_balancer_port ? parseInt(formData.load_balancer_port) : null
            }

            await axios.post(`${API_BASE}/autoscaling/policies`, payload, {
                headers: { Authorization: `Bearer ${token}` }
            })

            setShowModal(false)
            fetchPolicies()
            fetchContainers()

            // Reset form
            setFormData({
                container_id: '',
                scale_up_cpu_threshold: 80,
                scale_up_memory_threshold: 80,
                scale_down_cpu_threshold: 30,
                scale_down_memory_threshold: 30,
                min_replicas: 1,
                max_replicas: 8,
                cooldown_period: 300,
                evaluation_period: 60,
                load_balancer_enabled: true,
                load_balancer_port: ''
            })
        } catch (error: any) {
            console.error('Error creating policy:', error)
            alert(error.response?.data?.detail || 'Failed to create policy')
        }
    }

    const togglePolicy = async (policyId: number) => {
        try {
            await axios.post(
                `${API_BASE}/autoscaling/policies/${policyId}/toggle`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
            )
            fetchPolicies()
        } catch (error) {
            console.error('Error toggling policy:', error)
        }
    }

    const deletePolicy = async (policyId: number) => {
        if (!confirm('Are you sure you want to delete this policy?')) return

        try {
            await axios.delete(`${API_BASE}/autoscaling/policies/${policyId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            fetchPolicies()
            fetchContainers()
        } catch (error) {
            console.error('Error deleting policy:', error)
        }
    }

    if (loading) {
        return <div className="p-8">Loading...</div>
    }

    return (
        <div className="p-8">
            <div className="mb-8 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Auto-Scaling</h1>
                    <p className="text-slate-600 mt-2">Manage container auto-scaling policies</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-rose-500 text-white px-4 py-2 rounded-lg hover:bg-rose-600 font-medium"
                >
                    + Create Policy
                </button>
            </div>

            {/* Active Policies */}
            <div className="bg-white rounded-lg shadow p-6 mb-8">
                <h2 className="text-xl font-semibold mb-4">Active Policies</h2>

                {policies.length === 0 ? (
                    <p className="text-slate-500">No auto-scaling policies configured</p>
                ) : (
                    <div className="space-y-4">
                        {policies.map((policy) => (
                            <div key={policy.id} className="border rounded-lg p-4">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h3 className="font-semibold">Policy #{policy.id}</h3>
                                        <p className="text-sm text-slate-500">Container ID: {policy.container_id}</p>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => togglePolicy(policy.id)}
                                            className={`px-4 py-2 rounded-lg text-sm font-medium ${policy.enabled
                                                ? 'bg-green-100 text-green-800'
                                                : 'bg-gray-100 text-gray-800'
                                                }`}
                                        >
                                            {policy.enabled ? 'Enabled' : 'Disabled'}
                                        </button>
                                        <button
                                            onClick={() => deletePolicy(policy.id)}
                                            className="px-4 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-800 hover:bg-red-200"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                        <p className="text-slate-500">Scale Up CPU</p>
                                        <p className="font-semibold">{policy.scale_up_cpu_threshold}%</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Scale Up Memory</p>
                                        <p className="font-semibold">{policy.scale_up_memory_threshold}%</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Scale Down CPU</p>
                                        <p className="font-semibold">{policy.scale_down_cpu_threshold}%</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Scale Down Memory</p>
                                        <p className="font-semibold">{policy.scale_down_memory_threshold}%</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Min Replicas</p>
                                        <p className="font-semibold">{policy.min_replicas}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Max Replicas</p>
                                        <p className="font-semibold">{policy.max_replicas}</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Cooldown</p>
                                        <p className="font-semibold">{policy.cooldown_period}s</p>
                                    </div>
                                    <div>
                                        <p className="text-slate-500">Evaluation</p>
                                        <p className="font-semibold">{policy.evaluation_period}s</p>
                                    </div>
                                </div>

                                {policy.last_scaled_at && (
                                    <p className="mt-3 text-sm text-slate-500">
                                        Last scaled: {new Date(policy.last_scaled_at).toLocaleString()}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Recent Scaling Events */}
            <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4">Recent Scaling Events</h2>

                {events.length === 0 ? (
                    <p className="text-slate-500">No scaling events yet</p>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left py-2 px-4">Time</th>
                                    <th className="text-left py-2 px-4">Action</th>
                                    <th className="text-left py-2 px-4">Trigger</th>
                                    <th className="text-left py-2 px-4">Value</th>
                                    <th className="text-left py-2 px-4">Replicas</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.map((event) => (
                                    <tr key={event.id} className="border-b hover:bg-slate-50">
                                        <td className="py-2 px-4 text-sm">
                                            {new Date(event.created_at).toLocaleString()}
                                        </td>
                                        <td className="py-2 px-4">
                                            <span
                                                className={`px-2 py-1 rounded text-sm ${event.action === 'scale_up'
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-blue-100 text-blue-800'
                                                    }`}
                                            >
                                                {event.action}
                                            </span>
                                        </td>
                                        <td className="py-2 px-4 text-sm capitalize">{event.trigger_metric}</td>
                                        <td className="py-2 px-4 text-sm">{event.metric_value.toFixed(1)}%</td>
                                        <td className="py-2 px-4 text-sm">
                                            {event.replica_count_before} → {event.replica_count_after}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Create Policy Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4" style={{ zIndex: 9999 }}>
                    <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                        <div className="p-6">
                            <h2 className="text-2xl font-bold mb-4">Create Auto-Scaling Policy</h2>

                            <form onSubmit={createPolicy} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Container</label>
                                    <select
                                        required
                                        value={formData.container_id}
                                        onChange={(e) => setFormData({ ...formData, container_id: e.target.value })}
                                        className="w-full border rounded-lg px-3 py-2 bg-white"
                                    >
                                        <option value="">Select a container</option>
                                        {containers.map((container) => (
                                            <option key={container.id} value={container.id}>
                                                {container.name} (ID: {container.id})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Scale Up CPU Threshold (%)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={formData.scale_up_cpu_threshold}
                                            onChange={(e) => setFormData({ ...formData, scale_up_cpu_threshold: parseFloat(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Scale Up Memory Threshold (%)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={formData.scale_up_memory_threshold}
                                            onChange={(e) => setFormData({ ...formData, scale_up_memory_threshold: parseFloat(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Scale Down CPU Threshold (%)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={formData.scale_down_cpu_threshold}
                                            onChange={(e) => setFormData({ ...formData, scale_down_cpu_threshold: parseFloat(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Scale Down Memory Threshold (%)</label>
                                        <input
                                            type="number"
                                            min="0"
                                            max="100"
                                            value={formData.scale_down_memory_threshold}
                                            onChange={(e) => setFormData({ ...formData, scale_down_memory_threshold: parseFloat(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Min Replicas (1-8)</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="8"
                                            value={formData.min_replicas}
                                            onChange={(e) => setFormData({ ...formData, min_replicas: parseInt(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Max Replicas (1-8)</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="8"
                                            value={formData.max_replicas}
                                            onChange={(e) => setFormData({ ...formData, max_replicas: parseInt(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Cooldown Period (seconds)</label>
                                        <input
                                            type="number"
                                            min="60"
                                            value={formData.cooldown_period}
                                            onChange={(e) => setFormData({ ...formData, cooldown_period: parseInt(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Evaluation Period (seconds)</label>
                                        <input
                                            type="number"
                                            min="30"
                                            value={formData.evaluation_period}
                                            onChange={(e) => setFormData({ ...formData, evaluation_period: parseInt(e.target.value) })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="lb_enabled"
                                        checked={formData.load_balancer_enabled}
                                        onChange={(e) => setFormData({ ...formData, load_balancer_enabled: e.target.checked })}
                                        className="rounded"
                                    />
                                    <label htmlFor="lb_enabled" className="text-sm font-medium">Enable Load Balancer</label>
                                </div>

                                {formData.load_balancer_enabled && (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">Load Balancer Port (optional)</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="65535"
                                            value={formData.load_balancer_port}
                                            onChange={(e) => setFormData({ ...formData, load_balancer_port: e.target.value })}
                                            className="w-full border rounded-lg px-3 py-2 bg-white"
                                            placeholder="Leave empty for auto-assign"
                                        />
                                    </div>
                                )}

                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="submit"
                                        className="flex-1 bg-rose-500 text-white py-2 rounded-lg hover:bg-rose-600 font-medium"
                                    >
                                        Create Policy
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowModal(false)}
                                        className="flex-1 bg-gray-200 text-gray-800 py-2 rounded-lg hover:bg-gray-300 font-medium"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
