import React from 'react'
import Sidebar from './Sidebar'

const DashboardLayout: React.FC<{ children: React.ReactNode }>= ({ children }) => {
  return (
    <div className="min-h-[calc(100vh-64px)] flex">
      <Sidebar />
      <main className="flex-1 p-6 bg-gradient-to-b from-white/80 to-slate-50/60">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

export default DashboardLayout
