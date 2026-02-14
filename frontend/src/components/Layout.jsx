import React, { useState } from 'react'
import { LayoutDashboard, Package, ShoppingCart, Truck, Boxes, Menu, X, Settings, LogOut, ClipboardList, Database, Users as UsersIcon } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Outlet } from 'react-router-dom'

const SidebarItem = ({ icon: Icon, label, active, onClick, hasSubmenu, isOpen }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors duration-200 ${active
            ? 'bg-blue-600 text-white shadow-md'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
    >
        <div className="flex items-center space-x-3">
            <Icon size={20} />
            <span className="font-medium">{label}</span>
        </div>
        {hasSubmenu && (
            <div className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
                <svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor">
                    <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                </svg>
            </div>
        )}
    </button>
)

export default function Layout() {
    const [isSidebarOpen, setSidebarOpen] = useState(true)
    const [openSubmenu, setOpenSubmenu] = useState(null)
    const navigate = useNavigate()
    const location = useLocation()
    const { user, logout } = useAuth()

    // Determine active ID from path
    const currentPath = location.pathname.substring(1) || 'dashboard'

    const handleNavigate = (id) => {
        navigate(`/${id}`)
    }

    const toggleSubmenu = (id) => {
        setOpenSubmenu(openSubmenu === id ? null : id)
        if (!isSidebarOpen) setSidebarOpen(true)
    }

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'inventory', label: 'Inventario', icon: Package },
        { id: 'orders', label: 'Ordenes de Compra', icon: ClipboardList },
        { id: 'purchase', label: 'Compras', icon: ShoppingCart },
        { id: 'movements', label: 'Movimientos', icon: Truck },
        { id: 'products', label: 'Productos', icon: Boxes },
    ]

    const configItems = [
        { id: 'data', label: 'Carga Masiva', icon: Database },
        ...(user?.role === 'admin' ? [{ id: 'users', label: 'Usuarios', icon: UsersIcon }] : []),
    ]

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <div className="flex h-screen bg-slate-50 overflow-hidden">
            <aside
                className={`${isSidebarOpen ? 'w-64' : 'w-20'
                    } bg-slate-900 flex-shrink-0 transition-all duration-300 ease-in-out flex flex-col z-20`}
            >
                <div className="h-16 flex items-center justify-center border-b border-slate-800">
                    {isSidebarOpen ? (
                        <h1 className="text-xl font-bold text-white tracking-wider">ERP</h1>
                    ) : (
                        <Boxes className="text-blue-500" />
                    )}
                </div>

                <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto custom-scrollbar">
                    {menuItems.map((item) => (
                        <SidebarItem
                            key={item.id}
                            icon={item.icon}
                            label={isSidebarOpen ? item.label : ''}
                            active={currentPath === item.id}
                            onClick={() => handleNavigate(item.id)}
                        />
                    ))}

                    {/* Configuration Dropdown */}
                    <div>
                        <SidebarItem
                            icon={Settings}
                            label={isSidebarOpen ? "Configuración" : ""}
                            active={configItems.some(i => i.id === currentPath)}
                            onClick={() => toggleSubmenu('config')}
                            hasSubmenu={true}
                            isOpen={openSubmenu === 'config'}
                        />
                        <div className={`overflow-hidden transition-all duration-300 ${openSubmenu === 'config' ? 'max-h-40 opacity-100 mt-2' : 'max-h-0 opacity-0'}`}>
                            {configItems.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => handleNavigate(item.id)}
                                    className={`w-full flex items-center space-x-3 px-4 py-2 pl-12 rounded-lg transition-colors duration-200 text-sm ${currentPath === item.id
                                            ? 'text-blue-400 font-medium'
                                            : 'text-slate-500 hover:text-slate-300'
                                        }`}
                                >
                                    <item.icon size={16} />
                                    {isSidebarOpen && <span>{item.label}</span>}
                                </button>
                            ))}
                        </div>
                    </div>
                </nav>

                <div className="p-3 border-t border-slate-800">
                    <SidebarItem icon={LogOut} label={isSidebarOpen ? "Salir" : ""} onClick={handleLogout} />
                </div>
            </aside>

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header className="h-16 bg-white shadow-sm flex items-center justify-between px-6 z-10">
                    <button
                        onClick={() => setSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded hover:bg-slate-100 text-slate-600"
                    >
                        <Menu size={24} />
                    </button>
                    <div className="flex items-center space-x-4">
                        <div className="text-sm text-slate-500">Hola, <span className="font-bold text-slate-700">{user?.username || 'Usuario'}</span></div>
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-sm">
                            {user?.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-6">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    )
}
