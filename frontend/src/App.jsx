import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { Toaster } from 'react-hot-toast'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Products from './pages/Products'
import Purchase from './pages/Purchase'
import Movements from './pages/Movements'
import Orders from './pages/Orders'
import DataManagement from './pages/DataManagement'
import Users from './pages/Users'
import DeliveryGuides from './pages/DeliveryGuides'

function App() {
    return (
        <AuthProvider>
            <Toaster position="top-right" />
            <Routes>
                {/* Public Route */}
                <Route path="/login" element={<Login />} />

                {/* Protected Routes */}
                <Route element={<ProtectedRoute />}>
                    <Route element={<Layout />}>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/inventory" element={<Inventory />} />
                        <Route path="/orders" element={<Orders />} />
                        <Route path="/guides" element={<DeliveryGuides />} />
                        <Route path="/products" element={<Products />} />
                        <Route path="/purchase" element={<Purchase />} />
                        <Route path="/movements" element={<Movements />} />
                        <Route path="/data" element={<DataManagement />} />

                        {/* Admin Only Route */}
                        <Route element={<ProtectedRoute adminOnly={true} />}>
                            <Route path="/users" element={<Users />} />
                        </Route>
                    </Route>
                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
        </AuthProvider>
    )
}

export default App
