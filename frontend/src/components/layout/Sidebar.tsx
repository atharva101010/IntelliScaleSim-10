import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

function Item({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `block px-4 py-2 rounded-lg text-sm font-medium ${isActive ? 'bg-rose-100 text-rose-800' : 'text-slate-700 hover:bg-slate-100'}`
      }
      end
    >
      {label}
    </NavLink>
  )
}

export default function Sidebar() {
  const { user } = useAuth()
  const role = user?.role || 'student'

  return (
    <aside className="w-64 border-r border-slate-200 bg-white/70 backdrop-blur p-4 hidden md:block">
      <div className="mb-6">
        <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-rose-500 text-white font-semibold">IS</div>
        <div className="mt-2 text-xs text-slate-500">Signed in as</div>
        <div className="text-sm font-semibold capitalize">{role}</div>
      </div>
      <nav className="space-y-1">
        {role === 'student' && (
          <>
            <Item to="/student" label="Overview" />
            <Item to="/student/deployments" label="Deployments" />
            <Item to="/student/monitoring" label="Monitoring" />
            <Item to="/student/autoscaling" label="Auto-Scaling" />
            <Item to="/student/loadtest" label="Load Testing" />
            <Item to="/student/guides" label="Deployment Guides" />
            <Item to="/student/profile" label="Profile" />
          </>
        )}
        {role === 'teacher' && (
          <>
            <Item to="/teacher" label="Overview" />
            <Item to="/teacher/deployments" label="Deployments" />
            <Item to="/teacher/monitoring" label="Monitoring" />
            <Item to="/teacher/guides" label="Deployment Guides" />
            <Item to="/teacher/classes" label="Classes" />
            <Item to="/teacher/profile" label="Profile" />
          </>
        )}
        {role === 'admin' && (
          <>
            <Item to="/admin" label="Overview" />
            <Item to="/admin/deployments" label="Deployments" />
            <Item to="/admin/monitoring" label="Monitoring" />
            <Item to="/admin/loadtest" label="Load Testing" />
            <Item to="/admin/guides" label="Deployment Guides" />
            <Item to="/admin/users" label="Users" />
            <Item to="/admin/systems" label="Systems" />
            <Item to="/admin/settings" label="Settings" />
          </>
        )}
      </nav>
    </aside>
  )
}
