export default function StudentDashboard() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold">Student Dashboard</h2>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
          <h3 className="font-semibold mb-2">At a glance</h3>
          <ul className="text-sm text-slate-600 list-disc pl-5">
            <li>Upcoming assignments</li>
            <li>Recent activity</li>
            <li>Simulation runs</li>
          </ul>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white/80 p-4 shadow-sm">
          <h3 className="font-semibold mb-2">Shortcuts</h3>
          <ul className="text-sm text-slate-600 list-disc pl-5">
            <li>Start new simulation</li>
            <li>Join course</li>
            <li>View grades</li>
          </ul>
        </section>
      </div>
    </div>
  )
}
