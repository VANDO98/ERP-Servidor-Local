import React, { useState, useEffect } from 'react'
import { LayoutDashboard, Package, ShoppingCart, Truck, Boxes, Menu, X, Settings, LogOut, ClipboardList, Database, Users as UsersIcon, ScrollText, Sun, Moon } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Outlet } from 'react-router-dom'

const SidebarItem = ({ icon: Icon, label, active, onClick, hasSubmenu, isOpen }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center justify-between px-4 py-3 rounded-lg transition-colors duration-200 ${active
            ? 'bg-blue-600 text-white shadow-md'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white'
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

    const [companyConfig, setCompanyConfig] = useState(null)

    // Dark Mode State
    const [darkMode, setDarkMode] = useState(() => {
        return localStorage.getItem('theme') === 'dark' ||
            (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
    });

    useEffect(() => {
        fetch('/company_config.json')
            .then(res => res.json())
            .then(data => setCompanyConfig(data))
            .catch(err => console.error("Error loading config:", err))
    }, [])

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [darkMode]);

    const toggleDarkMode = () => setDarkMode(!darkMode);

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
        { id: 'guides', label: 'Guías de Remisión', icon: ScrollText },
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

    const [isUserMenuOpen, setUserMenuOpen] = useState(false)

    const toggleUserMenu = () => {
        setUserMenuOpen(!isUserMenuOpen)
    }

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-900 overflow-hidden transition-colors duration-300">
            <aside
                className={`${isSidebarOpen ? 'w-64' : 'w-20'
                    } bg-slate-900 dark:bg-slate-950 flex-shrink-0 transition-all duration-300 ease-in-out flex flex-col z-20 shadow-xl`}
            >
                <div className="h-16 flex items-center justify-center border-b border-slate-800 dark:border-slate-800 px-4">
                    {isSidebarOpen ? (
                        <div className="flex items-center gap-2 w-full">
                            {companyConfig?.company?.logo_url && (
                                <img
                                    src={companyConfig.company.logo_url}
                                    alt="Logo"
                                    className="h-8 w-8 object-contain"
                                    onError={(e) => { e.target.style.display = 'none' }}
                                />
                            )}
                            <h1 className="text-sm font-bold text-white tracking-wide truncate" title={companyConfig?.company?.name}>
                                {companyConfig?.company?.name || 'ERP SYSTEM'}
                            </h1>
                        </div>
                    ) : (
                        companyConfig?.company?.logo_url ? (
                            <img
                                src={companyConfig.company.logo_url}
                                alt="Logo"
                                className="h-8 w-8 object-contain"
                            />
                        ) : (
                            <Boxes className="text-blue-500" />
                        )
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
                </nav>

                {/* Footer Actions (Dark Mode + Logout) */}
                <div className="p-3 border-t border-slate-800 dark:border-slate-800 space-y-2">
                    <button
                        onClick={toggleDarkMode}
                        className="w-full flex items-center justify-between px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-yellow-400 transition-colors duration-200"
                        title={darkMode ? "Modo Claro" : "Modo Oscuro"}
                    >
                        <div className="flex items-center space-x-3">
                            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
                            {isSidebarOpen && <span className="font-medium text-sm">{darkMode ? "Modo Claro" : "Modo Oscuro"}</span>}
                        </div>
                    </button>
                    {/* Logout in Sidebar for Mobile/Quick Access if sidebar open */}
                    {isSidebarOpen && (
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center justify-between px-4 py-3 rounded-lg text-slate-400 hover:bg-red-900/20 hover:text-red-400 transition-colors duration-200"
                        >
                            <div className="flex items-center space-x-3">
                                <LogOut size={20} />
                                <span className="font-medium text-sm">Cerrar Sesión</span>
                            </div>
                        </button>
                    )}
                </div>
            </aside>

            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <header className="h-16 bg-white dark:bg-slate-800 shadow-sm flex items-center justify-between px-6 z-10 transition-colors duration-300">
                    <button
                        onClick={() => setSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-200"
                    >
                        <Menu size={24} />
                    </button>

                    <div className="relative">
                        <button
                            onClick={toggleUserMenu}
                            className="flex items-center space-x-4 hover:bg-slate-50 dark:hover:bg-slate-700 p-2 rounded-lg transition-colors"
                        >
                            <div className="text-right hidden md:block">
                                <div className="text-sm font-bold text-slate-700 dark:text-slate-200">{user?.username || 'Usuario'}</div>
                                <div className="text-xs text-slate-500 dark:text-slate-400 capitalize">{user?.role || 'User'}</div>
                            </div>
                            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-700 dark:text-blue-300 font-bold text-lg border-2 border-white dark:border-slate-600 shadow-sm">
                                {user?.username?.charAt(0).toUpperCase() || 'U'}
                            </div>
                        </button>

                        {/* User Dropdown */}
                        {isUserMenuOpen && (
                            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-100 dark:border-slate-700 py-2 animate-in fade-in slide-in-from-top-2 z-50">
                                <div className="px-4 py-2 border-b border-slate-50 dark:border-slate-700 mb-2">
                                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Configuración</p>
                                </div>

                                {configItems.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => {
                                            handleNavigate(item.id)
                                            setUserMenuOpen(false)
                                        }}
                                        className="w-full text-left px-4 py-2.5 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 hover:text-blue-600 dark:hover:text-blue-400 flex items-center space-x-2 transition-colors"
                                    >
                                        <item.icon size={16} />
                                        <span>{item.label}</span>
                                    </button>
                                ))}

                                <div className="border-t border-slate-50 dark:border-slate-700 my-2"></div>

                                <button
                                    onClick={handleLogout}
                                    className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-2 transition-colors"
                                >
                                    <LogOut size={16} />
                                    <span>Cerrar Sesión</span>
                                </button>
                            </div>
                        )}
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-6 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-300">
                    <div className="max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    )
}
