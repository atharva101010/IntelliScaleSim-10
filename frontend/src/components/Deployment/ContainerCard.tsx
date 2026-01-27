import { Container } from '../../utils/api'
import { format, formatDistanceToNow } from 'date-fns'

interface ContainerCardProps {
    container: Container
    onStart: (id: number) => void
    onStop: (id: number) => void
    onDelete: (id: number) => void
    onViewDetails: (id: number) => void
}

const statusColors = {
    running: 'bg-emerald-100 text-emerald-800',
    stopped: 'bg-slate-100 text-slate-700',
    pending: 'bg-amber-100 text-amber-800',
    error: 'bg-red-100 text-red-800',
}

export default function ContainerCard({
    container,
    onStart,
    onStop,
    onDelete,
    onViewDetails,
}: ContainerCardProps) {
    const getRelativeTime = (dateStr: string) => {
        try {
            return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
        } catch {
            return 'Unknown'
        }
    }

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-5">
            <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                    <h3 className="text-lg font-bold text-slate-900">{container.name}</h3>
                    <p className="text-sm text-slate-600 font-mono mt-1">{container.image}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColors[container.status]}`}>
                    {container.status}
                </span>
            </div>

            <div className="space-y-2 mb-4">
                {container.port && (
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">Port:</span>
                        <span className="font-semibold text-slate-900">{container.port}</span>
                    </div>
                )}
                {container.localhost_url && (
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">URL:</span>
                        <a
                            href={container.localhost_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold text-rose-600 hover:text-rose-700 hover:underline"
                        >
                            {container.localhost_url}
                        </a>
                    </div>
                )}
                <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Created:</span>
                    <span className="font-medium text-slate-900">{getRelativeTime(container.created_at)}</span>
                </div>
            </div>

            <div className="flex gap-2">
                <button
                    onClick={() => onViewDetails(container.id)}
                    className="flex-1 px-3 py-2 bg-slate-100 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-200 transition"
                >
                    Details
                </button>

                {container.status === 'running' ? (
                    <button
                        onClick={() => onStop(container.id)}
                        className="px-3 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 transition"
                    >
                        Stop
                    </button>
                ) : container.status === 'stopped' ? (
                    <button
                        onClick={() => onStart(container.id)}
                        className="px-3 py-2 bg-emerald-500 text-white text-sm font-medium rounded-lg hover:bg-emerald-600 transition"
                    >
                        Start
                    </button>
                ) : null}

                <button
                    onClick={() => onDelete(container.id)}
                    className="px-3 py-2 bg-red-500 text-white text-sm font-medium rounded-lg hover:bg-red-600 transition"
                    title="Delete container"
                >
                    Delete
                </button>
            </div>
        </div>
    )
}
