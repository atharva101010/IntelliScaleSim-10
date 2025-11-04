import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../utils/api'

export type Role = 'student' | 'teacher' | 'admin'

export type AuthUser = {
  id?: string
  email?: string
  role?: Role
}

export type AuthContextValue = {
  token: string | null
  user: AuthUser | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, role: Role) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function decodeJwt(token: string): any | null {
  try {
    const [, payload] = token.split('.')
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(decodeURIComponent(escape(json)))
  } catch {
    return null
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('iss_token'))
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    if (token) {
      localStorage.setItem('iss_token', token)
      const decoded = decodeJwt(token)
      setUser({ id: decoded?.sub, email: decoded?.email, role: decoded?.role })
    } else {
      localStorage.removeItem('iss_token')
      setUser(null)
    }
  }, [token])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password)
    setToken(res.access_token)
  }, [])

  const register = useCallback(async (name: string, email: string, password: string, role: Role) => {
    // Register only. Do not auto-login; user must verify email first.
    await api.register(name, email, password, role)
  }, [])

  const logout = useCallback(() => setToken(null), [])

  const value = useMemo(() => ({ token, user, login, register, logout }), [token, user, login, register, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
