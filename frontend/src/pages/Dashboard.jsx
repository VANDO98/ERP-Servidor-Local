import React, { useEffect, useState } from 'react'
import { Calendar, TrendingUp, Package, AlertTriangle, DollarSign, ShoppingCart, Activity, AlertCircle, BarChart2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, AreaChart, Area } from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1'];

export default function Dashboard() {
    const [period, setPeriod] = useState('month') // 'week' | 'month' | 'year' | 'all' | 'custom'
    const [startDate, setStartDate] = useState(() => {
        const d = new Date()
        d.setDate(d.getDate() - 30)
        return d.toISOString().split('T')[0]
    })
    const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])
    const [selectedAlert, setSelectedAlert] = useState(null)
    const [dashData, setDashData] = useState(null)
    const [loading, setLoading] = useState(true)

    const setPeriodPreset = (preset) => {
        setPeriod(preset)
        const today = new Date()
        let start = new Date()

        switch (preset) {
            case 'week':
                start.setDate(today.getDate() - 7)
                break
            case 'month':
                start.setDate(today.getDate() - 30)
                break
            case 'year':
                start.setFullYear(today.getFullYear() - 1)
                break
            case 'all':
                start = new Date('2020-01-01')
                break
            default:
                break
        }

        if (preset !== 'custom') {
            setStartDate(start.toISOString().split('T')[0])
            setEndDate(today.toISOString().split('T')[0])
        }
    }

    const fetchData = async () => {
        setLoading(true)
        try {
            const res = await fetch(`http://localhost:8000/api/dashboard/complete?start_date=${startDate}&end_date=${endDate}`)
            if (!res.ok) throw new Error('Error en respuesta del servidor')
            const data = await res.json()
            setDashData(data)
        } catch (error) {
            console.error('Error fetching dashboard:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [startDate, endDate])

    const AlertModal = ({ alert, onClose }) => {
        if (!alert) return null

        // Helper to render content based on alert type
        const renderItem = (item, type) => {
            if (type === 'sin_stock') {
                return (
                    <div className="flex justify-between items-center w-full">
                        <div>
                            <p className="font-bold text-slate-800">{item.nombre}</p>
                            <p className="text-xs text-slate-500">Min: {item.min} {item.um}</p>
                        </div>
                        <div className="text-right">
                            <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-bold">
                                {item.stock} {item.um}
                            </span>
                        </div>
                    </div>
                )
            }
            if (type === 'sin_movimiento') {
                return (
                    <div className="flex justify-between items-center w-full">
                        <p className="font-medium text-slate-800">{item.nombre}</p>
                        <p className="text-xs text-slate-500">Último mov: {item.ultimo_movimiento}</p>
                    </div>
                )
            }
            if (type === 'compras_grandes') {
                return (
                    <div className="w-full">
                        <div className="flex justify-between text-sm">
                            <span className="font-bold text-slate-700">{item.proveedor}</span>
                            <span className="font-bold text-blue-600">S/ {item.monto?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-500 mt-1">
                            <span>{item.documento}</span>
                            <span>{item.fecha}</span>
                        </div>
                    </div>
                )
            }
            if (type === 'facturas_duplicadas') {
                return (
                    <div className="w-full">
                        <div className="flex justify-between text-sm">
                            <span className="font-bold text-slate-700">{item.proveedor}</span>
                            <span className="font-bold text-purple-600">S/ {item.monto?.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-500 mt-1">
                            <span>{item.fecha}</span>
                            <span>{item.cantidad} registros</span>
                        </div>
                    </div>
                )
            }
            return <span className="text-sm text-slate-700">{JSON.stringify(item)}</span>
        }

        const colorClasses = {
            red: 'bg-red-50 text-red-700 border-red-100',
            yellow: 'bg-yellow-50 text-yellow-700 border-yellow-100',
            blue: 'bg-blue-50 text-blue-700 border-blue-100',
            purple: 'bg-purple-50 text-purple-700 border-purple-100'
        }

        const headerClass = colorClasses[alert.color] || 'bg-slate-50 text-slate-800'

        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
                <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200" onClick={e => e.stopPropagation()}>
                    <div className={`px-6 py-4 border-b flex justify-between items-center ${headerClass}`}>
                        <h3 className="font-bold text-lg flex items-center gap-2">
                            {alert.icon}
                            {alert.title}
                        </h3>
                        <button onClick={onClose} className="p-1 hover:bg-white/20 rounded-full transition-colors">
                            <Activity size={18} />
                        </button>
                    </div>
                    <div className="p-0 max-h-[60vh] overflow-y-auto bg-slate-50/50">
                        {alert.items && alert.items.length > 0 ? (
                            <ul className="divide-y divide-slate-100">
                                {alert.items.map((item, idx) => (
                                    <li key={idx} className="px-6 py-3 hover:bg-white transition-colors border-l-4 border-transparent hover:border-l-blue-500 bg-white mb-1 shadow-sm mx-2 first:mt-2 rounded my-1">
                                        {renderItem(item, alert.type)}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <div className="p-8 text-center text-slate-400">
                                No hay elementos para mostrar en esta alerta.
                            </div>
                        )}
                    </div>
                    <div className="bg-white px-6 py-3 border-t border-slate-100 text-right">
                        <button onClick={onClose} className="px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-900 font-medium text-sm transition-colors">
                            Cerrar
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    if (loading || !dashData) {
        return (
            <div className="flex flex-col items-center justify-center h-96 text-slate-400">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                Cargando métricas...
            </div>
        )
    }

    const kpis = dashData?.kpis || {}
    const stockCritico = dashData?.stock_critico || []
    const rotacion = dashData?.rotacion || []
    const topProviders = dashData?.top_providers || []
    const categories = dashData?.categories || []
    const evolution = dashData?.evolution || []
    const alertas = dashData?.alertas || {}

    // Prepare data for Recharts - Safe Mapping
    const evolutionData = Array.isArray(evolution) ? evolution.map(e => {
        try {
            if (!e.Fecha) return { name: 'N/A', monto: 0 };
            const d = new Date(e.Fecha);
            if (isNaN(d.getTime())) return { name: 'Fecha Inválida', monto: 0 };

            return {
                name: d.toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' }),
                monto: Number(e.Monto) || 0
            };
        } catch (err) {
            return { name: 'Error', monto: 0 };
        }
    }) : [];

    const categoryData = Array.isArray(categories) ? categories.map(c => ({
        name: c.Categoria || 'Sin Categoría',
        value: Number(c.Monto) || 0
    })) : [];

    // Prepare Rotation Data (Top 5)
    const topRotationData = Array.isArray(rotacion)
        ? rotacion
            .filter(r => r.Tipo === 'Alta Rotación')
            .slice(0, 5)
            .map(r => ({
                name: r.Producto || 'Producto',
                value: Number(r.TotalSalidas) || 0
            }))
        : [];

    const KPICard = ({ title, value, subtext, icon: Icon, colorClass, bgClass, tooltip }) => (
        <div
            title={tooltip}
            className={`cursor-pointer rounded-xl shadow-sm p-6 border border-slate-100 transition-all hover:shadow-md ${bgClass || 'bg-white'}`}
        >
            <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-slate-500">{title}</p>
                <div className={`p-2 rounded-lg ${colorClass.replace('text-', 'bg-').replace('600', '100').replace('500', '100')}`}>
                    <Icon className={colorClass} size={20} />
                </div>
            </div>
            <h3 className="text-2xl font-bold text-slate-800">{value}</h3>
            {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
        </div>
    )

    return (
        <div className="space-y-6 pb-8">

            {/* Header with Period Filter */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-xl shadow-sm border border-slate-100">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        <Activity className="text-blue-600" /> Dashboard General
                    </h2>
                    <p className="text-slate-500 text-sm mt-1">
                        Resumen del {new Date(startDate).toLocaleDateString('es-PE', { dateStyle: 'long' })} al {new Date(endDate).toLocaleDateString('es-PE', { dateStyle: 'long' })}
                    </p>
                </div>

                {/* Period Selector */}
                <div className="flex flex-wrap items-center gap-2">
                    {['week', 'month', 'year', 'all'].map(p => (
                        <button
                            key={p}
                            onClick={() => setPeriodPreset(p)}
                            className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${period === p ? 'bg-blue-600 text-white shadow-sm' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}
                        >
                            {p === 'week' ? 'Semana' : p === 'month' ? 'Mes' : p === 'year' ? 'Año' : 'Todo'}
                        </button>
                    ))}
                    <div className="flex items-center gap-2 bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => { setStartDate(e.target.value); setPeriod('custom') }}
                            className="text-sm bg-transparent border-none focus:outline-none text-slate-700 font-medium"
                        />
                        <span className="text-slate-400">→</span>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => { setEndDate(e.target.value); setPeriod('custom') }}
                            className="text-sm bg-transparent border-none focus:outline-none text-slate-700 font-medium"
                        />
                    </div>
                </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <KPICard
                    title="Compras Totales"
                    value={`S/ ${kpis.compras_monto?.toLocaleString('es-PE', { minimumFractionDigits: 2 }) || '0.00'}`}
                    subtext={`${kpis.compras_docs || 0} documentos registrados`}
                    icon={ShoppingCart}
                    colorClass="text-orange-500"
                />
                <KPICard
                    title="Salidas Totales"
                    value={`S/ ${kpis.salidas_monto?.toLocaleString('es-PE', { minimumFractionDigits: 2 }) || '0.00'}`}
                    subtext="Valorizado (FIFO)"
                    icon={TrendingUp}
                    colorClass="text-blue-500"
                />
                <KPICard
                    title="Inventario (FIFO)"
                    value={`S/ ${kpis.valor_inventario?.toLocaleString('es-PE', { minimumFractionDigits: 2 }) || '0.00'}`}
                    subtext="Valorización actual"
                    icon={Package}
                    colorClass="text-emerald-500"
                />
                <KPICard
                    title="Alertas Stock"
                    value={alertas.sin_stock?.count || 0}
                    subtext="Productos agotados"
                    icon={AlertTriangle}
                    colorClass="text-red-500"
                    bgClass={alertas.sin_stock?.count > 0 ? "bg-red-50" : "bg-white"}
                    tooltip={alertas.sin_stock?.items?.length > 0 ? "Productos Agotados:\n" + alertas.sin_stock.items.join('\n') : "Sin alertas"}
                />
                <KPICard
                    title="T.C. Referencial"
                    value={`S/ ${kpis.tc?.toFixed(3) || '3.850'}`}
                    subtext="Tipo de Cambio SUNAT"
                    icon={DollarSign}
                    colorClass="text-purple-500"
                />
            </div>

            {/* Evolution Chart (Full Width) */}
            <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <TrendingUp size={18} className="text-blue-500" /> Evolución de Compras
                </h3>
                {evolutionData.length > 0 ? (
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={evolutionData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorMonto" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis
                                    dataKey="name"
                                    fontSize={12}
                                    tickMargin={10}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <YAxis
                                    fontSize={12}
                                    axisLine={false}
                                    tickLine={false}
                                    tickFormatter={(value) => `S/${(value / 1000).toFixed(0)}k`}
                                />
                                <Tooltip
                                    formatter={(value) => `S/ ${value.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`}
                                    contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />
                                <Area type="monotone" dataKey="monto" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorMonto)" name="Monto Compra" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="h-72 flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-lg">
                        <TrendingUp size={48} className="mb-4 text-slate-300" />
                        <p>Sin historial de compras en este periodo</p>
                    </div>
                )}
            </div>

            {/* Analysis Row: Categories & Rotation */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Gasto por Categoría - Pie Chart */}
                <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                    <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                        <Package size={18} className="text-purple-500" /> Gasto por Categoría
                    </h3>
                    {categories.length > 0 ? (
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={categoryData}
                                        cx="40%"
                                        cy="50%"
                                        innerRadius={70}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {categoryData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} strokeWidth={0} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        formatter={(value) => `S/ ${value.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`}
                                        contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Legend
                                        layout="vertical"
                                        verticalAlign="middle"
                                        align="right"
                                        wrapperStyle={{ paddingLeft: "10px" }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-lg">
                            <Package size={48} className="mb-4 text-slate-300" />
                            <p>Sin datos de categorías</p>
                        </div>
                    )}
                </div>

                {/* Alta Rotación - Bar Chart */}
                <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                    <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                        <BarChart2 size={18} className="text-emerald-500" /> Alta Rotación (Top 5)
                    </h3>
                    {topRotationData.length > 0 ? (
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={topRotationData}
                                    layout="vertical"
                                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                                    <XAxis type="number" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis
                                        dataKey="name"
                                        type="category"
                                        width={100}
                                        fontSize={11}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip
                                        cursor={{ fill: '#f8fafc' }}
                                        contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="value" fill="#10b981" radius={[0, 4, 4, 0]} barSize={32} name="Total Salidas" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="h-80 flex flex-col items-center justify-center text-slate-400 bg-slate-50 rounded-lg">
                            <BarChart2 size={48} className="mb-4 text-slate-300" />
                            <p>Sin datos de rotación</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Tables Row: Stock & Providers */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Stock Crítico & Rotación */}
                <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                    <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <AlertTriangle size={18} className="text-orange-500" /> Stock Crítico (Top 15)
                    </h3>
                    <div className="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                        {stockCritico.length > 0 ? (
                            stockCritico.slice(0, 15).map((item, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 hover:bg-white border border-slate-100 hover:border-blue-100 rounded-lg transition-colors group">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${item.Estado === 'Sin Stock' ? 'bg-red-500' : item.Estado === 'Crítico' ? 'bg-orange-500' : item.Estado === 'Bajo' ? 'bg-yellow-400' : 'bg-green-500'}`}></div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-700 group-hover:text-blue-600 transition-colors">{item.Producto}</p>
                                            <div className="flex items-center gap-2 mt-0.5">
                                                <span className={`text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wide font-bold ${item.Estado === 'Sin Stock' ? 'bg-red-100 text-red-700' : item.Estado === 'Crítico' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                                    {item.Estado}
                                                </span>
                                                <span className="text-xs text-slate-400">Min: {item.StockMinimo}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="block text-sm font-bold text-slate-700">{item.Stock?.toFixed(2)}</span>
                                        <span className="text-xs text-slate-400">{item.UM}</span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                                <span className="text-2xl mb-2">✅</span>
                                <p>Inventario Saludable</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Top Proveedores */}
                <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                    <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <ShoppingCart size={18} className="text-emerald-500" /> Top Proveedores
                    </h3>
                    <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
                        {topProviders.length > 0 ? (
                            topProviders.slice(0, 6).map((prov, idx) => {
                                const total = topProviders.reduce((sum, p) => sum + (p.Monto || 0), 0)
                                const pct = total > 0 ? (prov.Monto / total * 100) : 0
                                return (
                                    <div key={idx} className="relative pt-1">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-sm font-medium text-slate-700 truncate w-2/3" title={prov.Proveedor}>{prov.Proveedor}</span>
                                            <span className="text-sm font-bold text-slate-800">S/ {prov.Monto?.toLocaleString('es-PE', { minimumFractionDigits: 0 })}</span>
                                        </div>
                                        <div className="overflow-hidden h-2 mb-1 text-xs flex rounded bg-slate-100">
                                            <div style={{ width: `${pct}%` }} className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"></div>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-xs text-slate-400">{pct.toFixed(1)}% del total</span>
                                        </div>
                                    </div>
                                )
                            })
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 text-slate-400">
                                <ShoppingCart size={48} className="mb-4 text-slate-300" />
                                <p>Sin datos de proveedores</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Alertas Críticas Section */}
            <div>
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <AlertCircle size={20} className="text-red-500" /> Alertas Críticas
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div
                        onClick={() => setSelectedAlert({
                            type: 'sin_stock',
                            title: 'Productos Sin Stock',
                            items: dashData.alertas.sin_stock?.items,
                            color: 'red',
                            icon: <AlertCircle size={24} className="text-red-600" />
                        })}
                        className="p-4 bg-red-50 rounded-xl border border-red-100 cursor-pointer hover:shadow-md transition-all hover:scale-[1.02] active:scale-95"
                    >
                        <p className="text-sm text-red-600 font-bold mb-1 flex items-center justify-between">
                            Sin Stock <AlertCircle size={14} />
                        </p>
                        <p className="text-2xl font-bold text-red-700">{dashData.alertas.sin_stock?.count || 0}</p>
                    </div>

                    <div
                        onClick={() => setSelectedAlert({
                            type: 'sin_movimiento',
                            title: 'Sin Movimiento (+90 días)',
                            items: dashData.alertas.sin_movimiento?.items,
                            color: 'yellow',
                            icon: <AlertTriangle size={24} className="text-yellow-600" />
                        })}
                        className="p-4 bg-yellow-50 rounded-xl border border-yellow-100 cursor-pointer hover:shadow-md transition-all hover:scale-[1.02] active:scale-95"
                    >
                        <p className="text-sm text-yellow-600 font-bold mb-1 flex items-center justify-between">
                            Sin Movimiento <AlertCircle size={14} />
                        </p>
                        <p className="text-2xl font-bold text-yellow-700">{dashData.alertas.sin_movimiento?.count || 0}</p>
                    </div>

                    <div
                        onClick={() => setSelectedAlert({
                            type: 'compras_grandes',
                            title: 'Compras Grandes (Recientes)',
                            items: dashData.alertas.compras_grandes?.items,
                            color: 'blue',
                            icon: <DollarSign size={24} className="text-blue-600" />
                        })}
                        className="p-4 bg-blue-50 rounded-xl border border-blue-100 cursor-pointer hover:shadow-md transition-all hover:scale-[1.02] active:scale-95"
                    >
                        <p className="text-sm text-blue-600 font-bold mb-1 flex items-center justify-between">
                            Compras Grandes <AlertCircle size={14} />
                        </p>
                        <p className="text-2xl font-bold text-blue-700">{dashData.alertas.compras_grandes?.count || 0}</p>
                    </div>

                    <div
                        onClick={() => setSelectedAlert({
                            type: 'facturas_duplicadas',
                            title: 'Posibles Duplicados',
                            items: dashData.alertas.facturas_duplicadas?.items,
                            color: 'purple',
                            icon: <Activity size={24} className="text-purple-600" />
                        })}
                        className="p-4 bg-purple-50 rounded-xl border border-purple-100 cursor-pointer hover:shadow-md transition-all hover:scale-[1.02] active:scale-95"
                    >
                        <p className="text-sm text-purple-600 font-bold mb-1 flex items-center justify-between">
                            Posibles Duplicados <AlertCircle size={14} />
                        </p>
                        <p className="text-2xl font-bold text-purple-700">{dashData.alertas.facturas_duplicadas?.count || 0}</p>
                    </div>
                </div>
            </div>

            {selectedAlert && <AlertModal alert={selectedAlert} onClose={() => setSelectedAlert(null)} />}
        </div>
    )
}
