import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Trash2, Save, AlertCircle, ArrowRightLeft, LogOut } from 'lucide-react'

export default function Movements() {
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [loading, setLoading] = useState(false)
    const [successMsg, setSuccessMsg] = useState('')
    const [errorMsg, setErrorMsg] = useState('')

    const [type, setType] = useState('TRASLADO') // 'TRASLADO' | 'SALIDA'

    const [formData, setFormData] = useState({
        fecha: new Date().toISOString().split('T')[0],
        observaciones: '',
        // Traslado
        origen_id: 1,
        destino_id: 2,
        // Salida
        tipo_salida: 'VENTA',
        destino_salida: '',
        items: []
    })

    useEffect(() => {
        Promise.all([
            api.getProducts(),
            fetch('http://localhost:8000/api/warehouses').then(r => r.json())
        ]).then(([prods, whs]) => {
            setProducts(prods)
            setWarehouses(whs)
        }).catch(console.error)
    }, [])

    const addItem = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { pid: '', cantidad: 1, almacen_id: 1 }]
        })
    }

    const updateItem = (index, field, value) => {
        const newItems = [...formData.items]
        newItems[index][field] = value
        setFormData({ ...formData, items: newItems })
    }

    const removeItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index)
        setFormData({ ...formData, items: newItems })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        setErrorMsg('')
        setSuccessMsg('')

        try {
            if (formData.items.length === 0) throw new Error("Debe agregar items")
            if (type === 'TRASLADO' && formData.origen_id == formData.destino_id) throw new Error("Origen y Destino deben ser diferentes")

            const payload = {
                type,
                fecha: formData.fecha,
                observaciones: formData.observaciones,
                items: formData.items.map(i => ({
                    pid: parseInt(i.pid),
                    cantidad: parseFloat(i.cantidad),
                    almacen_id: type === 'SALIDA' ? parseInt(i.almacen_id) : undefined
                }))
            }

            if (type === 'TRASLADO') {
                payload.origen_id = parseInt(formData.origen_id)
                payload.destino_id = parseInt(formData.destino_id)
            } else {
                payload.tipo_salida = formData.tipo_salida
                payload.destino = formData.destino_salida
            }

            const res = await api.registerMovement(payload)
            setSuccessMsg(`✅ ${type} registrado: ${res.msg}`)
            setFormData({ ...formData, items: [], observaciones: '' })
        } catch (err) {
            setErrorMsg(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-slate-800">Movimientos de Almacén</h2>
                <div className="flex bg-slate-100 p-1 rounded-lg">
                    <button
                        onClick={() => setType('TRASLADO')}
                        className={`flex items-center px-4 py-2 rounded-md font-medium transition-all ${type === 'TRASLADO' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500'}`}
                    >
                        <ArrowRightLeft className="w-4 h-4 mr-2" /> Traslado
                    </button>
                    <button
                        onClick={() => setType('SALIDA')}
                        className={`flex items-center px-4 py-2 rounded-md font-medium transition-all ${type === 'SALIDA' ? 'bg-orange-500 text-white shadow-sm' : 'text-slate-500'}`}
                    >
                        <LogOut className="w-4 h-4 mr-2" /> Salida
                    </button>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Header */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Fecha</label>
                        <input
                            type="date"
                            className="w-full p-2 border border-slate-200 rounded-lg"
                            value={formData.fecha}
                            onChange={e => setFormData({ ...formData, fecha: e.target.value })}
                        />
                    </div>

                    {type === 'TRASLADO' ? (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Almacén Origen</label>
                                <select
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.origen_id}
                                    onChange={e => setFormData({ ...formData, origen_id: e.target.value })}
                                >
                                    {warehouses.map(w => <option key={w.id} value={w.id}>{w.nombre}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Almacén Destino</label>
                                <select
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.destino_id}
                                    onChange={e => setFormData({ ...formData, destino_id: e.target.value })}
                                >
                                    {warehouses.map(w => <option key={w.id} value={w.id}>{w.nombre}</option>)}
                                </select>
                            </div>
                        </>
                    ) : (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Tipo Salida</label>
                                <select
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.tipo_salida}
                                    onChange={e => setFormData({ ...formData, tipo_salida: e.target.value })}
                                >
                                    <option value="VENTA">Venta</option>
                                    <option value="MERMA">Merma / Deterioro</option>
                                    <option value="CONSUMO">Consumo Interno</option>
                                    <option value="AJUSTE">Ajuste Inventario</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Destino / Cliente</label>
                                <input
                                    type="text"
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.destino_salida}
                                    onChange={e => setFormData({ ...formData, destino_salida: e.target.value })}
                                />
                            </div>
                        </>
                    )}

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-slate-700 mb-1">Observaciones</label>
                        <input
                            type="text"
                            className="w-full p-2 border border-slate-200 rounded-lg"
                            value={formData.observaciones}
                            onChange={e => setFormData({ ...formData, observaciones: e.target.value })}
                        />
                    </div>
                </div>

                {/* Items */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold text-slate-800">Items a Mover</h3>
                        <button type="button" onClick={addItem} className="flex items-center text-blue-600 font-medium">
                            <Plus className="w-4 h-4 mr-1" /> Agregar
                        </button>
                    </div>

                    <div className="space-y-3">
                        {formData.items.map((item, idx) => (
                            <div key={idx} className="flex gap-3 items-end border-b border-slate-50 pb-3">
                                <div className="flex-1">
                                    <label className="text-xs text-slate-500">Producto</label>
                                    <select
                                        className="w-full p-2 border border-slate-200 rounded-lg text-sm"
                                        value={item.pid}
                                        onChange={e => updateItem(idx, 'pid', e.target.value)}
                                    >
                                        <option value="">Seleccionar...</option>
                                        {products.map(p => (
                                            <option key={p.id} value={p.id}>{p.nombre}</option>
                                        ))}
                                    </select>
                                </div>
                                {type === 'SALIDA' && (
                                    <div className="w-1/4">
                                        <label className="text-xs text-slate-500">Desde Almacén</label>
                                        <select
                                            className="w-full p-2 border border-slate-200 rounded-lg text-sm"
                                            value={item.almacen_id}
                                            onChange={e => updateItem(idx, 'almacen_id', e.target.value)}
                                        >
                                            {warehouses.map(w => <option key={w.id} value={w.id}>{w.nombre}</option>)}
                                        </select>
                                    </div>
                                )}
                                <div className="w-24">
                                    <label className="text-xs text-slate-500">Cantidad</label>
                                    <input
                                        type="number" min="0.01" step="0.01"
                                        className="w-full p-2 border border-slate-200 rounded-lg text-sm text-right"
                                        value={item.cantidad}
                                        onChange={e => updateItem(idx, 'cantidad', e.target.value)}
                                    />
                                </div>
                                <button type="button" onClick={() => removeItem(idx)} className="pb-2 text-red-400 hover:text-red-600">
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Messages */}
                {errorMsg && (
                    <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center">
                        <AlertCircle className="w-5 h-5 mr-2" />
                        {errorMsg}
                    </div>
                )}
                {successMsg && (
                    <div className="bg-green-50 text-green-600 p-4 rounded-lg flex items-center font-medium">
                        <Save className="w-5 h-5 mr-2" />
                        {successMsg}
                    </div>
                )}

                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={loading}
                        className={`px-6 py-3 bg-slate-800 text-white rounded-xl shadow-lg hover:bg-slate-900 transition-all ${loading ? 'opacity-70' : ''}`}
                    >
                        {loading ? 'Procesando...' : `Registrar ${type.toLowerCase()}`}
                    </button>
                </div>
            </form>
        </div>
    )
}
