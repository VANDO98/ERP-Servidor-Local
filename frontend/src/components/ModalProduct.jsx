import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { X, Save, Plus } from 'lucide-react'
import ModalCategory from './ModalCategory'

export default function ModalProduct({ isOpen, onClose, onProductSaved }) {
    const [formData, setFormData] = useState({
        nombre: '',
        codigo_sku: '',
        categoria_id: '',
        unidad_medida: 'UN',
        precio_venta: '',
        costo_promedio: '',
        stock_minimo: 5
    })
    const [categories, setCategories] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false)

    useEffect(() => {
        if (isOpen) {
            fetchCategories()
            setFormData({
                nombre: '',
                codigo_sku: '',
                categoria_id: '',
                unidad_medida: 'UN',
                precio_venta: '',
                costo_promedio: '',
                stock_minimo: 5
            })
            setError('')
        }
    }, [isOpen])

    const fetchCategories = async () => {
        try {
            const data = await api.getCategories()
            setCategories(data)
        } catch (err) {
            console.error(err)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError('')

        try {
            if (!formData.nombre) throw new Error("El nombre es obligatorio")

            const payload = {
                ...formData,
                categoria_id: formData.categoria_id ? parseInt(formData.categoria_id) : null,
                precio_venta: parseFloat(formData.precio_venta || 0),
                costo_promedio: parseFloat(formData.costo_promedio || 0),
                stock_minimo: parseFloat(formData.stock_minimo || 0)
            }

            const res = await fetch('http://localhost:8000/api/products', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const data = await res.json()
            if (!res.ok) throw new Error(data.detail || "Error al guardar")

            onProductSaved()
            onClose()
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <ModalCategory
                isOpen={isCategoryModalOpen}
                onClose={() => setIsCategoryModalOpen(false)}
                onCategorySaved={fetchCategories}
            />

            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-slate-800">Nuevo Producto</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
                        <X size={24} />
                    </button>
                </div>

                {error && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Código SKU</label>
                            <input
                                type="text"
                                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                value={formData.codigo_sku}
                                onChange={e => setFormData({ ...formData, codigo_sku: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Unidad Medida</label>
                            <select
                                className="w-full p-2 border border-slate-300 rounded-lg"
                                value={formData.unidad_medida}
                                onChange={e => setFormData({ ...formData, unidad_medida: e.target.value })}
                            >
                                <option value="UN">UN - Unidad</option>
                                <option value="KG">KG - Kilogramos</option>
                                <option value="LT">LT - Litros</option>
                                <option value="MT">MT - Metros</option>
                                <option value="CJ">CJ - Caja</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Nombre del Producto *</label>
                        <input
                            type="text"
                            required
                            className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            value={formData.nombre}
                            onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Categoría</label>
                        <div className="flex gap-2">
                            <select
                                className="w-full p-2 border border-slate-300 rounded-lg"
                                value={formData.categoria_id}
                                onChange={e => setFormData({ ...formData, categoria_id: e.target.value })}
                            >
                                <option value="">Seleccionar...</option>
                                {categories.map(c => (
                                    <option key={c.id} value={c.id}>{c.nombre}</option>
                                ))}
                            </select>
                            <button
                                type="button"
                                onClick={() => setIsCategoryModalOpen(true)}
                                className="p-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors"
                                title="Nueva Categoría"
                            >
                                <Plus size={20} />
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-500 mb-1">Precio Venta</label>
                            <input
                                type="number"
                                step="0.01"
                                className="w-full p-2 border border-slate-300 rounded-lg"
                                value={formData.precio_venta}
                                onChange={e => setFormData({ ...formData, precio_venta: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-500 mb-1">Costo Prom.</label>
                            <input
                                type="number"
                                step="0.01"
                                className="w-full p-2 border border-slate-300 rounded-lg"
                                value={formData.costo_promedio}
                                onChange={e => setFormData({ ...formData, costo_promedio: e.target.value })}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-500 mb-1">Stock Min.</label>
                            <input
                                type="number"
                                step="1"
                                className="w-full p-2 border border-slate-300 rounded-lg"
                                value={formData.stock_minimo}
                                onChange={e => setFormData({ ...formData, stock_minimo: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                        >
                            <Save size={18} className="mr-2" />
                            {loading ? 'Guardando...' : 'Guardar Producto'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
