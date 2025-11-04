import React from 'react'
import Header from './Header'
import { useLocation } from 'react-router-dom'

const AppShell: React.FC<{ children: React.ReactNode }>= ({ children }) => {
  const location = useLocation()
  const isAuth = location.pathname === '/login' || location.pathname === '/register'
  const bgClass = isAuth
    ? 'bg-rose-50'
    : 'bg-gradient-to-br from-slate-50 via-white to-slate-100'
  const mainBase = "mx-auto max-w-6xl px-4 sm:px-6 lg:px-8"
  const mainLayout = isAuth ? `${mainBase} min-h-[calc(100vh-56px)] grid place-items-center` : `${mainBase} py-10`
  return (
    <div className={`min-h-screen ${bgClass} text-slate-900`}>
      <Header />
      <main className={mainLayout}>
        {children}
      </main>
    </div>
  )
}

export default AppShell
