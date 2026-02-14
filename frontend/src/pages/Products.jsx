import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { Search, Plus } from 'lucide-react'

export default function Products() {
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState('')

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const data = await api.getProducts()
                setProducts(data)
            } catch (error) {
                console.error("Error fetching products:", error)
            } finally {
                setLoading(false)
            }
        }
        fetchProducts()
    }, [])

    const filteredProducts = products.filter(p =>
        p.nombre?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.codigo_sku?.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800">Productos</h2>
                    <p className="text-slate-500">Gestión maestra de artículos</p>
                </div>
                <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
                    <Plus className="w-5 h-5 mr-1" />
                    Nuevo Producto
                </button>
            </div>

            {/* Toolbar */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
                <div className="relative w-full md:w-96">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="Buscar por nombre o SKU..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* Grid */}
            {loading ? (
                <div className="text-center py-12 text-slate-400">Cargando productos...</div>
            ) : (
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-slate-600">
                            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-100">
                                <tr>
                                    <th className="px-6 py-4">SKU</th>
                                    <th className="px-6 py-4">Nombre</th>
                                    <th className="px-6 py-4">Categoría</th>
                                    <th className="px-6 py-4 text-center">U.M.</th>
                                    <th className="px-6 py-4 text-right">Stock Global</th>
                                    <th className="px-6 py-4 text-right">Costo Prom.</th>
                                    <th className="px-6 py-4 text-center">Estado</th> # Added Status
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {filteredProducts.map((p) => (
                                    <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-slate-500">{p.codigo_sku}</td>
                                        <td className="px-6 py-4 font-medium text-slate-900">{p.nombre}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded-md text-xs">
                                                {p.categoria_nombre || 'Sin Cat'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-center">{p.unidad_medida}</td>
                                        <td className={`px-6 py-4 text-right font-medium ${p.stock_actual < p.stock_minimo ? 'text-red-500' : 'text-slate-700'}`}>
                                            {p.stock_actual?.toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 text-right">S/ {p.costo_promedio?.toFixed(2)}</td>
                                        <td className="px-6 py-4 text-center">
                                            {p.stock_actual < p.stock_minimo ? (
                                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                    Bajo Stock
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    Normal
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
