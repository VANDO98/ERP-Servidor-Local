import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { ArrowUpDown, Search, Filter } from 'lucide-react'
import ExportButton from '../components/ExportButton'

export default function Inventory() {
    const [view, setView] = useState('summary') // 'summary' | 'detailed' | 'kardex'
    const [inventory, setInventory] = useState([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')

    // Kardex state
    const [products, setProducts] = useState([])
    const [selectedProduct, setSelectedProduct] = useState('')
    const [kardexData, setKardexData] = useState([])

    // Warehouse state
    const [warehouses, setWarehouses] = useState([])
    const [selectedWarehouse, setSelectedWarehouse] = useState('all')

    useEffect(() => {
        fetchWarehouses()
    }, [])

    const fetchWarehouses = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/warehouses')
            const data = await res.json()
            setWarehouses(data)
        } catch (error) {
            console.error('Error fetching warehouses:', error)
        }
    }

    const fetchData = async () => {
        setLoading(true)
        try {
            if (view === 'summary') {
                const res = await api.getInventoryFifo(true)
                setInventory(res.items)
            } else if (view === 'detailed') {
                const data = await api.getInventoryDetailed()
                setInventory(data)
            } else if (view === 'kardex') {
                const prods = await api.getProducts()
                setProducts(prods)
            }
        } catch (error) {
            console.error("Error fetching inventory:", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [view])

    const fetchKardex = async (productId) => {
        try {
            const response = await fetch(`http://localhost:8000/api/inventory/kardex/${productId}`)
            const data = await response.json()
            setKardexData(data)
        } catch (error) {
            console.error('Error fetching kardex:', error)
        }
    }

    useEffect(() => {
        if (selectedProduct && view === 'kardex') {
            fetchKardex(selectedProduct)
        }
    }, [selectedProduct])

    const filteredData = inventory.filter(item => {
        const term = searchTerm.toLowerCase()
        const name = view === 'summary' ? item.name : item.Producto
        const sku = view === 'summary' ? item.sku : item.Codigo

        const matchesTerm = name?.toLowerCase().includes(term) || sku?.toLowerCase().includes(term)
        const matchesWarehouse = view !== 'detailed' || selectedWarehouse === 'all' || item.Almacen === selectedWarehouse

        return matchesTerm && matchesWarehouse
    })

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Inventario</h2>
                    <p className="text-slate-500">Gestión de existencias y valorización</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex space-x-2 border-b border-slate-200">
                <button
                    onClick={() => setView('summary')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'summary' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    💰 Resumen Valorizado (FIFO)
                </button>
                <button
                    onClick={() => setView('detailed')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'detailed' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    📦 Por Almacén (Detallado)
                </button>
                <button
                    onClick={() => setView('kardex')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'kardex' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    📜 Kardex por Producto
                </button>
            </div>

            {/* Summary & Detailed Views */}
            {(view === 'summary' || view === 'detailed') && (
                <>
                    <div className="flex gap-4 mb-4 items-center">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="text"
                                placeholder="Buscar por código o nombre..."
                                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        {view === 'detailed' && (
                            <select
                                className="p-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                value={selectedWarehouse}
                                onChange={(e) => setSelectedWarehouse(e.target.value)}
                            >
                                <option value="all">Todos los Almacenes</option>
                                {warehouses.map(w => (
                                    <option key={w.id} value={w.nombre}>{w.nombre}</option>
                                ))}
                            </select>
                        )}
                        <ExportButton
                            data={filteredData}
                            filename={`inventario_${view}`}
                        />
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                        {loading ? (
                            <div className="p-8 text-center text-slate-400">Cargando...</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-700 font-semibold">
                                        <tr>
                                            {view === 'summary' ? (
                                                <>
                                                    <th className="px-6 py-4">Código</th>
                                                    <th className="px-6 py-4">Producto</th>
                                                    <th className="px-6 py-4">Categoría</th>
                                                    <th className="px-6 py-4 text-center">U.M.</th>
                                                    <th className="px-6 py-4 text-right">Stock</th>
                                                    <th className="px-6 py-4 text-right">Costo Unit. (Ref)</th>
                                                    <th className="px-6 py-4 text-right">Valor Total (FIFO)</th>
                                                    <th className="px-6 py-4 text-center">Estado</th>
                                                </>
                                            ) : (
                                                <>
                                                    <th className="px-6 py-4">Código</th>
                                                    <th className="px-6 py-4">Producto</th>
                                                    <th className="px-6 py-4">Almacén</th>
                                                    <th className="px-6 py-4 text-right">Stock</th>
                                                    <th className="px-6 py-4 text-right">Costo (FIFO)</th>
                                                    <th className="px-6 py-4 text-right">Valor Total</th>
                                                </>
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {filteredData.length > 0 ? (
                                            filteredData.map((item, idx) => (
                                                <tr key={idx} className="hover:bg-slate-50">
                                                    {view === 'summary' ? (
                                                        <>
                                                            <td className="px-6 py-4 font-mono text-xs">{item.sku || 'N/A'}</td>
                                                            <td className="px-6 py-4 font-medium text-slate-800">{item.producto}</td>
                                                            <td className="px-6 py-4 text-slate-600">{item.categoria}</td>
                                                            <td className="px-6 py-4 text-center text-slate-600">{item.unidad}</td>
                                                            <td className="px-6 py-4 text-right font-medium">{item.stock}</td>
                                                            <td className="px-6 py-4 text-right text-slate-600">
                                                                S/ {parseFloat(item.costo_unitario || 0).toFixed(2)}
                                                            </td>
                                                            <td className="px-6 py-4 text-right font-bold text-blue-600">
                                                                S/ {parseFloat(item.valor_total || 0).toFixed(2)}
                                                            </td>
                                                            <td className="px-6 py-4 text-center">
                                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${item.estado === 'Normal'
                                                                    ? 'bg-emerald-100 text-emerald-700'
                                                                    : 'bg-amber-100 text-amber-700'
                                                                    }`}>
                                                                    {item.estado}
                                                                </span>
                                                            </td>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <td className="px-6 py-4 font-mono text-xs">{item.Codigo || 'N/A'}</td>
                                                            <td className="px-6 py-4">{item.Producto}</td>
                                                            <td className="px-6 py-4">{item.Almacen}</td>
                                                            <td className="px-6 py-4 text-right">{(item.Stock || 0).toFixed(2)}</td>
                                                            <td className="px-6 py-4 text-right">S/ {(item.CostoUnitFIFO || 0).toFixed(2)}</td>
                                                            <td className="px-6 py-4 text-right font-medium text-green-600">S/ {(item.ValorTotal || 0).toFixed(2)}</td>
                                                        </>
                                                    )}
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={view === 'summary' ? 7 : 6} className="px-6 py-8 text-center text-slate-400">
                                                    No hay datos disponibles
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Kardex View */}
            {view === 'kardex' && (
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <div className="flex gap-4 items-end">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Seleccione un producto para ver su historial
                                </label>
                                <select
                                    className="w-full p-3 border border-slate-200 rounded-lg"
                                    value={selectedProduct}
                                    onChange={(e) => setSelectedProduct(e.target.value)}
                                >
                                    <option value="">Seleccionar...</option>
                                    {products.map(p => (
                                        <option key={p.id} value={p.id}>
                                            {p.codigo_sku} | {p.nombre}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            {kardexData.length > 0 && <ExportButton data={kardexData} filename={`kardex_producto_${selectedProduct}`} />}
                        </div>
                    </div>

                    {selectedProduct && (
                        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-700 font-semibold">
                                        <tr>
                                            <th className="px-6 py-4">Fecha</th>
                                            <th className="px-6 py-4">Tipo</th>
                                            <th className="px-6 py-4">Documento</th>
                                            <th className="px-6 py-4 text-right">Entradas</th>
                                            <th className="px-6 py-4 text-right">Salidas</th>
                                            <th className="px-6 py-4 text-right">Saldo</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {kardexData.length > 0 ? (
                                            kardexData.map((k, idx) => (
                                                <tr key={idx} className="hover:bg-slate-50">
                                                    <td className="px-6 py-4">{k.Fecha}</td>
                                                    <td className="px-6 py-4">
                                                        <span className={`px-2 py-1 text-xs rounded ${k.TipoMovimiento === 'COMPRA' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                                            {k.TipoMovimiento}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 font-mono text-xs">{k.Documento}</td>
                                                    <td className="px-6 py-4 text-right">{k.Entradas?.toFixed(2)}</td>
                                                    <td className="px-6 py-4 text-right">{k.Salidas?.toFixed(2)}</td>
                                                    <td className="px-6 py-4 text-right font-medium">{k.Saldo?.toFixed(2)}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="6" className="px-6 py-8 text-center text-slate-400">
                                                    No hay movimientos registrados para este producto
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {kardexData.length > 0 && (
                                <div className="bg-slate-50 px-6 py-4 border-t border-slate-100">
                                    <div className="grid grid-cols-3 gap-4">
                                        <div>
                                            <p className="text-xs text-slate-500 mb-1">Entradas Totales</p>
                                            <p className="text-lg font-bold text-green-600">
                                                {kardexData.reduce((sum, k) => sum + (k.Entradas || 0), 0).toFixed(2)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-slate-500 mb-1">Salidas Totales</p>
                                            <p className="text-lg font-bold text-red-600">
                                                {kardexData.reduce((sum, k) => sum + (k.Salidas || 0), 0).toFixed(2)}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-slate-500 mb-1">Stock Actual</p>
                                            <p className="text-lg font-bold text-blue-600">
                                                {kardexData.length > 0 ? kardexData[kardexData.length - 1].Saldo?.toFixed(2) : '0.00'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
