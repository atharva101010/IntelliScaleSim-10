import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Login from '../components/Auth/Login'
import Register from '../components/Auth/Register'
import ForgotPassword from '../components/Auth/ForgotPassword'
import ResetPassword from '../components/Auth/ResetPassword'
import VerifyEmail from '../components/Auth/VerifyEmail'
import { useAuth } from '../hooks/useAuth'
import React from 'react'
import AppShell from '../components/layout/AppShell'
import DashboardLayout from '../components/layout/DashboardLayout'
import StudentDashboard from '../pages/StudentDashboard'
import TeacherDashboard from '../pages/TeacherDashboard'
import AdminDashboard from '../pages/AdminDashboard'

const Protected: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

const RoleGate: React.FC<{ role: 'student'|'teacher'|'admin', children: React.ReactNode }> = ({ role, children }) => {
  const { user } = useAuth()
  if (user?.role !== role) return <Navigate to="/" replace />
  return <>{children}</>
}

const RoleRedirect: React.FC = () => {
  const { user } = useAuth()
  if (user?.role === 'teacher') return <Navigate to="/teacher" replace />
  if (user?.role === 'admin') return <Navigate to="/admin" replace />
  return <Navigate to="/student" replace />
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />
    <Route path="/reset-password" element={<ResetPassword />} />
    <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/" element={<Protected><RoleRedirect /></Protected>} />
          <Route path="/student" element={<Protected><RoleGate role="student"><DashboardLayout><StudentDashboard /></DashboardLayout></RoleGate></Protected>} />
          <Route path="/teacher" element={<Protected><RoleGate role="teacher"><DashboardLayout><TeacherDashboard /></DashboardLayout></RoleGate></Protected>} />
          <Route path="/admin" element={<Protected><RoleGate role="admin"><DashboardLayout><AdminDashboard /></DashboardLayout></RoleGate></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
