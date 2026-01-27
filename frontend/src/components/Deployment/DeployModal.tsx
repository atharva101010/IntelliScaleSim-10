import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api, DeployContainerRequest } from '../../utils/api'
import { useAuth } from '../../hooks/useAuth'

interface DeployModalProps {
    isOpen: boolean
    onClose: () => void
    onSuccess: () => void
}

const COMMON_IMAGES = [
    { value: 'nginx:latest', label: 'Nginx (latest)' },
    { value: 'nginx:alpine', label: 'Nginx (alpine)' },
    { value: 'redis:latest', label: 'Redis (latest)' },
    { value: 'redis:alpine', label: 'Redis (alpine)' },
    { value: 'postgres:latest', label: 'PostgreSQL (latest)' },
    { value: 'postgres:16-alpine', label: 'PostgreSQL 16 (alpine)' },
    { value: 'mongo:latest', label: 'MongoDB (latest)' },
    { value: 'mysql:latest', label: 'MySQL (latest)' },
    { value: 'node:latest', label: 'Node.js (latest)' },
    { value: 'node:20-alpine', label: 'Node.js 20 (alpine)' },
    { value: 'python:latest', label: 'Python (latest)' },
    { value: 'python:3.11-slim', label: 'Python 3.11 (slim)' },
]

export default function DeployModal({ isOpen, onClose, onSuccess }: DeployModalProps) {
    const { user } = useAuth()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [localImages, setLocalImages] = useState<string[]>([])


    const [formData, setFormData] = useState<DeployContainerRequest>({
        name: '',
        deployment_type: 'dockerhub',  // 'dockerhub' or 'github'

        // Docker Hub fields
        image: 'nginx:latest',
        docker_username: undefined,
        docker_password: undefined,

        // GitHub fields
        source_url: undefined,
        github_branch: 'main',
        git_token: undefined,
        dockerfile_path: undefined,

        // Common fields
        port: undefined,
        cpu_limit: 500,
        memory_limit: 512,
        environment_vars: {},
    })

    // Removed environment variables state - using Docker credentials instead

    // Fetch local Docker images when modal opens
    useEffect(() => {
        if (isOpen) {
            fetch('/api/containers/docker/images', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.images) {
                        setLocalImages(data.images)
                    }
                })
                .catch(err => console.error('Failed to fetch local images:', err))
        }
    }, [isOpen])

    if (!isOpen) return null

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            console.log('Deploying container with data:', formData)
            const result = await api.deployContainer(formData)
            console.log('Deployment successful:', result)
            onSuccess()
            onClose()
            // Reset form
            setFormData({
                name: '',
                deployment_type: 'dockerhub',
                image: 'nginx:latest',
                port: undefined,
                cpu_limit: 500,
                memory_limit: 512,
                environment_vars: {},
            })
        } catch (err: any) {
            console.error('Deployment error:', err)
            const errorMsg = err?.message || 'Failed to deploy container'
            setError(`Error: ${errorMsg}`)
        } finally {
            setLoading(false)
        }
    }



    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4"
                onClick={(e) => e.stopPropagation()}>
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-2xl font-bold text-slate-900">Deploy New Container</h2>
                    <p className="text-sm text-slate-600 mt-1">Configure and deploy a simulated container</p>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    {/* Helpful Guide Banner */}
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                            <div className="flex-shrink-0">
                                <span className="text-2xl">📚</span>
                            </div>
                            <div className="flex-1">
                                <h3 className="text-sm font-semibold text-blue-900 mb-1">
                                    Need help getting started?
                                </h3>
                                <p className="text-sm text-blue-800 mb-2">
                                    Check out our comprehensive deployment guides for step-by-step instructions
                                </p>
                                <Link
                                    to={`/${user?.role || 'student'}/guides`}
                                    onClick={onClose}
                                    className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 hover:underline transition"
                                >
                                    <span>📖 View Deployment Guides</span>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </Link>
                            </div>
                        </div>
                    </div>

                    {/* Deployment Source Selector */}
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Deployment Source *
                        </label>
                        <select
                            value={formData.deployment_type}
                            onChange={(e) => setFormData({ ...formData, deployment_type: e.target.value as 'dockerhub' | 'github' })}
                            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                            required
                        >
                            <option value="dockerhub">🐳 Docker Hub / Local Image</option>
                            <option value="github">🐙 GitHub Repository</option>
                        </select>
                        <p className="text-xs text-slate-500 mt-1">
                            {formData.deployment_type === 'dockerhub'
                                ? 'Deploy from Docker Hub or local Docker Desktop images'
                                : 'Clone GitHub repo, build from Dockerfile, and deploy'}
                        </p>
                    </div>

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Container Name *
                        </label>
                        <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                            placeholder="my-container"
                            required
                            pattern="[a-zA-Z0-9_-]+"
                            title="Only alphanumeric, hyphens, and underscores allowed"
                        />
                    </div>

                    {formData.deployment_type === 'dockerhub' ? (
                        <>
                            {/* Docker Hub/Local Image Fields */}
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">
                                    Container Image *
                                </label>
                                <input
                                    type="text"
                                    list="docker-images-list"
                                    value={formData.image || ''}
                                    onChange={(e) => setFormData({ ...formData, image: e.target.value })}
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                    placeholder="nginx:latest or your-image:tag"
                                    required
                                />
                                <datalist id="docker-images-list">
                                    {COMMON_IMAGES.map((img) => (
                                        <option key={img.value} value={img.value}>{img.label}</option>
                                    ))}
                                    {localImages.map((img) => (
                                        <option key={img} value={img}>Local: {img}</option>
                                    ))}
                                </datalist>
                                <p className="text-xs text-slate-500 mt-1">
                                    Type to search or enter your custom image name from Docker Desktop
                                </p>
                            </div>
                        </>
                    ) : (
                        <>
                            {/* GitHub Repository Fields */}
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-2">
                                    GitHub Repository URL *
                                </label>
                                <input
                                    type="url"
                                    value={formData.source_url || ''}
                                    onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                    placeholder="https://github.com/username/repository"
                                    required
                                />
                                <p className="text-xs text-slate-500 mt-1">
                                    🔗 Full GitHub repository URL (public or private)
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-600 mb-1">
                                        Branch
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.github_branch || 'main'}
                                        onChange={(e) => setFormData({ ...formData, github_branch: e.target.value })}
                                        className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                        placeholder="main"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-600 mb-1">
                                        Dockerfile Path (optional)
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.dockerfile_path || ''}
                                        onChange={(e) => setFormData({ ...formData, dockerfile_path: e.target.value || undefined })}
                                        className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                        placeholder="Dockerfile"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-600 mb-1">
                                    GitHub Token (for private repos)
                                </label>
                                <input
                                    type="password"
                                    value={formData.git_token || ''}
                                    onChange={(e) => setFormData({ ...formData, git_token: e.target.value || undefined })}
                                    className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                    placeholder="ghp_xxxxxxxxxxxx"
                                />
                                <p className="text-xs text-slate-400 mt-1">
                                    💡 Personal Access Token from GitHub Settings → Developer settings
                                </p>
                            </div>
                        </>
                    )}

                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                            Port (optional, 1024-65535)
                        </label>
                        <input
                            type="number"
                            value={formData.port || ''}
                            onChange={(e) => setFormData({ ...formData, port: e.target.value ? parseInt(e.target.value) : undefined })}
                            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                            placeholder="8080"
                            min="1024"
                            max="65535"
                        />
                    </div>

                    {/* Docker Registry Credentials for Private Docker Hub Images */}
                    {formData.deployment_type === 'dockerhub' && (
                        <div className="border-t pt-4 mt-2">
                            <h3 className="text-sm font-semibold text-slate-700 mb-3">
                                🔐 Docker Registry Credentials (Optional)
                            </h3>
                            <p className="text-xs text-slate-500 mb-3">
                                Provide credentials if deploying a private image from Docker Hub or a private registry
                            </p>

                            <div className="space-y-3">
                                <div>
                                    <label className="block text-sm font-medium text-slate-600 mb-1">
                                        Username
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.docker_username || ''}
                                        onChange={(e) => setFormData({ ...formData, docker_username: e.target.value || undefined })}
                                        placeholder="dockerhub-username"
                                        className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-600 mb-1">
                                        Access Token / Password
                                    </label>
                                    <input
                                        type="password"
                                        value={formData.docker_password || ''}
                                        onChange={(e) => setFormData({ ...formData, docker_password: e.target.value || undefined })}
                                        placeholder="Access token or password"
                                        className="w-full px-4 py-2.5 rounded-lg border border-slate-300 bg-white text-slate-900 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/20 outline-none transition"
                                    />
                                    <p className="text-xs text-slate-400 mt-1">
                                        💡 For Docker Hub, use an access token instead of your password for better security
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-2.5 border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition"
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-2.5 bg-rose-500 text-white font-semibold rounded-lg hover:bg-rose-600 transition disabled:opacity-50"
                        >
                            {loading ? 'Deploying...' : 'Deploy Container'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
