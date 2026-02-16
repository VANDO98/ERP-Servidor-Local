import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Search, FileText, Calendar, Truck, Check, RefreshCw } from 'lucide-react'
import ExportButton from '../components/ExportButton'

export default function DeliveryGuides() {
    const [activeTab, setActiveTab] = useState('list') // 'list' | 'create'
    const [guides, setGuides] = useState([])
    const [orders, setOrders] = useState([]) // Approved OCs
    const [products, setProducts] = useState([]) // All Products for manual entry
    const [loading, setLoading] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')

    // Form Data
    const [selectedOcId, setSelectedOcId] = useState('')
    const [formData, setFormData] = useState({
        proveedor_id: '',
        oc_id: '',
        numero_guia: '',
        fecha_recepcion: new Date().toISOString().split('T')[0],
        items: [], // { pid, cantidad, almacen_id }
        observaciones: ''
    })

    const [ocDetails, setOcDetails] = useState(null)
    const [selectedGuide, setSelectedGuide] = useState(null)
    const [providers, setProviders] = useState([]) // For manual entry

    useEffect(() => {
        fetchGuides()
        fetchProducts()
        fetchProviders()
    }, [])

    const fetchProviders = async () => {
        try {
            const res = await api.getProviders()
            setProviders(res)
        } catch (error) {
            console.error("Error fetching providers:", error)
        }
    }

    // Refresh orders whenever we switch to Create tab
    useEffect(() => {
        if (activeTab === 'create') {
            fetchApprovedOrders()
        }
    }, [activeTab])

    const fetchProducts = async () => {
        try {
            const res = await api.getProducts()
            setProducts(res)
        } catch (error) {
            console.error("Error fetching products:", error)
        }
    }

    const fetchGuides = async () => {
        setLoading(true)
        try {
            const data = await api.getGuides()
            console.log("Guides loaded:", data)
            setGuides(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Error fetching guides:", error)
            alert("Error al cargar las guías")
        } finally {
            setLoading(false)
        }
    }

    const fetchApprovedOrders = async () => {
        try {
            console.log("Fetching pending orders...")
            const data = await api.getPendingOrders()
            console.log("Pending orders loaded:", data)
            setOrders(Array.isArray(data) ? data : [])
        } catch (error) {
            console.error("Error fetching orders:", error)
            alert("Error al cargar órdenes pendientes")
        }
    }

    const handleOcSelect = async (e) => {
        const oid = e.target.value
        setSelectedOcId(oid)

        if (!oid) {
            setOcDetails(null)
            setFormData(prev => ({ ...prev, items: [], oc_id: '' }))
            return
        }

        if (oid === 'manual') {
            setOcDetails(null)
            setFormData(prev => ({ ...prev, oc_id: '', items: [] }))
            return
        }

        try {
            // Fetch OC Details AND Balance via new endpoint
            const data = await api.getOrderBalance(oid)

            if (data.fully_completed) {
                alert("Esta Orden de Compra ya ha sido entregada en su totalidad.")
            }

            setOcDetails(data)

            // Pre-fill form with PENDING quantities
            const selectedOrder = orders.find(o => o.id == oid)
            setFormData(prev => ({
                ...prev,
                proveedor_id: selectedOrder?.proveedor_id || '',
                oc_id: oid,
                items: data.items.map(i => ({
                    pid: i.pid || i.producto_id, // Ensure we get ID
                    producto: i.producto,
                    um: i.um,
                    cantidad_solicitada: i.cantidad_solicitada || i.cantidad,
                    cantidad_recibida: 0,
                    cantidad_pendiente: i.cantidad_pendiente,
                    cantidad: i.cantidad_pendiente, // Default to remaining
                    almacen_id: 1 // Default to Main Warehouse
                }))
            }))
        } catch (error) {
            console.error("Error fetching OC details:", error)
            alert("Error al cargar detalles de la OC")
        }
    }

    const handleItemChange = (index, field, value) => {
        const newItems = [...formData.items]
        if (field === 'cantidad') {
            const val = parseFloat(value) || 0
            newItems[index][field] = val
        } else {
            newItems[index][field] = value
        }
        setFormData({ ...formData, items: newItems })
    }

    // Manual Items Management
    const addManualItem = () => {
        setFormData(prev => ({
            ...prev,
            items: [...prev.items, { pid: '', cantidad: 1, almacen_id: 1, um: 'UN' }]
        }))
    }

    const removeManualItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index)
        setFormData(prev => ({ ...prev, items: newItems }))
    }

    const updateManualItem = (index, field, value) => {
        const newItems = [...formData.items]
        newItems[index][field] = value

        if (field === 'pid') {
            const prod = products.find(p => p.id == value)
            if (prod) {
                newItems[index].um = prod.unidad_medida || 'UN'
                newItems[index].producto = prod.nombre
            }
        }
        setFormData({ ...formData, items: newItems })
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        try {
            const payload = {
                ...formData,
                items: formData.items
                    .filter(i => i.cantidad > 0)
                    .map(i => ({
                        pid: parseInt(i.pid),
                        cantidad: parseFloat(i.cantidad),
                        almacen_id: parseInt(i.almacen_id || 1)
                    }))
            }

            if (payload.items.length === 0) {
                throw new Error("Debe ingresar al menos una cantidad válida mayor a 0")
            }

            const result = await api.createGuide(payload)

            alert("Guía registrada correctamente")
            fetchGuides()
            setActiveTab('list') // Switch back to list
            setFormData({
                proveedor_id: '',
                oc_id: '',
                numero_guia: '',
                fecha_recepcion: new Date().toISOString().split('T')[0],
                items: [],
                observaciones: ''
            })
            setSelectedOcId('')
            setOcDetails(null)

        } catch (error) {
            alert(error.message)
        } finally {
            setLoading(false)
        }
    }

    const handleViewDetail = async (gid) => {
        try {
            const data = await api.getGuide(gid)
            setSelectedGuide(data)
        } catch (error) {
            console.error(error)
            alert("Error al cargar detalle de guía")
        }
    }

    const filteredGuides = guides.filter(g =>
        (g.numero_guia || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (g.proveedor || '').toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800">Guías de Remisión</h1>
                    <p className="text-slate-500">Gestión de recepción de mercadería</p>
                </div>
                {/* Refresh Button */}
                <button onClick={fetchGuides} className="text-slate-400 hover:text-blue-600 p-2" title="Recargar">
                    <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
                </button>
            </div>

            {/* TABS */}
            <div className="flex border-b border-slate-200">
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${activeTab === 'list'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                    onClick={() => setActiveTab('list')}
                >
                    Listado de Guías
                </button>
                <button
                    className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${activeTab === 'create'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                    onClick={() => setActiveTab('create')}
                >
                    Registrar Recepción
                </button>
            </div>

            {/* TAB CONTENT: LIST */}
            {activeTab === 'list' && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="p-4 border-b border-slate-100 flex justify-between items-center gap-4">
                        <div className="relative flex-1 max-w-md">
                            <Search className="absolute left-3 top-2.5 text-slate-400" size={20} />
                            <input
                                type="text"
                                placeholder="Buscar guía o proveedor..."
                                className="pl-10 pr-4 py-2 w-full border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-100 focus:border-blue-400 outline-none transition-all"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>
                        <ExportButton data={guides} filename="guias_remision" />
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-100">
                                <tr>
                                    <th className="px-6 py-4">Fecha Recepción</th>
                                    <th className="px-6 py-4">N° Guía</th>
                                    <th className="px-6 py-4">Proveedor</th>
                                    <th className="px-6 py-4">OC Ref</th>
                                    <th className="px-6 py-4 text-center">Items</th>
                                    <th className="px-6 py-4 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {filteredGuides.map((g, idx) => (
                                    <tr key={idx} className="hover:bg-slate-50">
                                        <td className="px-6 py-4">{g.fecha || g.fecha_recepcion}</td>
                                        <td className="px-6 py-4 font-mono font-medium">{g.numero_guia}</td>
                                        <td className="px-6 py-4">{g.proveedor_nombre || g.proveedor}</td>
                                        <td className="px-6 py-4 text-blue-600">
                                            {g.oc_id ? (
                                                <a href={`/purchase?ocId=${g.oc_id}&guideId=${g.id}`} className="hover:underline flex items-center gap-1">
                                                    OC-{String(g.oc_id).padStart(6, '0')} <Truck size={14} />
                                                </a>
                                            ) : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-center">{g.items_count}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => handleViewDetail(g.id)}
                                                className="text-slate-400 hover:text-blue-600"
                                                title="Ver Detalle"
                                            >
                                                <FileText size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {filteredGuides.length === 0 && (
                                    <tr><td colSpan="6" className="px-6 py-8 text-center text-slate-400">No hay guías registradas</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* TAB CONTENT: CREATE */}
            {activeTab === 'create' && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 max-w-4xl mx-auto">
                    <h2 className="text-xl font-bold text-slate-700 mb-6 pb-2 border-b border-slate-100">Nueva Guía de Remisión</h2>

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Seleccionar Orden de Compra *</label>
                                <select
                                    required
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={selectedOcId}
                                    onChange={handleOcSelect}
                                >
                                    <option value="">-- Seleccionar OC --</option>
                                    <option value="manual" className="font-bold text-blue-600">-- RECEPCIÓN DIRECTA (SIN OC) --</option>
                                    {orders.map(o => (
                                        <option key={o.id} value={o.id}>
                                            OC-{String(o.id).padStart(6, '0')} | {o.proveedor_nombre} | {o.fecha}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Provider Select for Manual Entry */}
                            {selectedOcId === 'manual' && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Proveedor *</label>
                                    <select
                                        required
                                        className="w-full p-2 border border-slate-200 rounded-lg"
                                        value={formData.proveedor_id}
                                        onChange={e => setFormData({ ...formData, proveedor_id: e.target.value })}
                                    >
                                        <option value="">-- Seleccionar Proveedor --</option>
                                        {providers.map(p => (
                                            <option key={p.id} value={p.id}>{p.razon_social}</option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Número de Guía *</label>
                                <input
                                    required
                                    type="text"
                                    placeholder="001-000123"
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.numero_guia}
                                    onChange={e => setFormData({ ...formData, numero_guia: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Fecha de Recepción *</label>
                                <input
                                    required
                                    type="date"
                                    className="w-full p-2 border border-slate-200 rounded-lg"
                                    value={formData.fecha_recepcion}
                                    onChange={e => setFormData({ ...formData, fecha_recepcion: e.target.value })}
                                />
                            </div>
                        </div>

                        {(ocDetails || selectedOcId === 'manual') && (
                            <div className="mt-8">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-semibold text-slate-700">Items a Recibir</h3>
                                    {selectedOcId === 'manual' && (
                                        <button type="button" onClick={addManualItem} className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 font-medium">
                                            <Plus size={16} /> Agregar Producto
                                        </button>
                                    )}
                                </div>
                                <div className="border border-slate-200 rounded-lg overflow-hidden">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-slate-50 text-slate-600">
                                            <tr>
                                                <th className="px-4 py-2">Producto</th>
                                                <th className="px-4 py-2 text-center">U.M.</th>
                                                {selectedOcId !== 'manual' && (
                                                    <>
                                                        <th className="px-4 py-2 text-right">Solicitado</th>
                                                        <th className="px-4 py-2 text-right">Recibido</th>
                                                        <th className="px-4 py-2 text-right">Pendiente</th>
                                                    </>
                                                )}
                                                <th className="px-4 py-2 text-right w-32">A Recibir</th>
                                                {selectedOcId === 'manual' && <th className="px-4 py-2 w-10"></th>}
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {formData.items.map((item, idx) => (
                                                <tr key={idx} className={item.cantidad_pendiente === 0 && selectedOcId !== 'manual' ? "bg-slate-50 opacity-50" : ""}>
                                                    <td className="px-4 py-2">
                                                        {selectedOcId === 'manual' ? (
                                                            <select
                                                                className="w-full p-1 border border-slate-200 rounded"
                                                                value={item.pid}
                                                                onChange={e => updateManualItem(idx, 'pid', e.target.value)}
                                                                required
                                                            >
                                                                <option value="">Seleccionar...</option>
                                                                {products.map(p => (
                                                                    <option key={p.id} value={p.id}>{p.nombre}</option>
                                                                ))}
                                                            </select>
                                                        ) : (
                                                            item.producto
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-2 text-center text-slate-500">{item.um}</td>
                                                    {selectedOcId !== 'manual' && (
                                                        <>
                                                            <td className="px-4 py-2 text-right text-slate-500">{item.cantidad_solicitada}</td>
                                                            <td className="px-4 py-2 text-right text-slate-500">{item.cantidad_recibida}</td>
                                                            <td className="px-4 py-2 text-right text-orange-600 font-medium">{item.cantidad_pendiente}</td>
                                                        </>
                                                    )}
                                                    <td className="px-4 py-2">
                                                        <input
                                                            type="number"
                                                            min="0"
                                                            step="0.01"
                                                            className="w-full p-1 border border-slate-300 rounded text-right focus:border-blue-500 outline-none"
                                                            value={item.cantidad}
                                                            onChange={e => selectedOcId === 'manual' ? updateManualItem(idx, 'cantidad', e.target.value) : handleItemChange(idx, 'cantidad', e.target.value)}
                                                            disabled={selectedOcId !== 'manual' && item.cantidad_pendiente === 0}
                                                            required
                                                        />
                                                    </td>
                                                    {selectedOcId === 'manual' && (
                                                        <td className="px-4 py-2 text-center">
                                                            <button type="button" onClick={() => removeManualItem(idx)} className="text-red-500 hover:text-red-700">×</button>
                                                        </td>
                                                    )}
                                                </tr>
                                            ))}
                                            {formData.items.length === 0 && selectedOcId === 'manual' && (
                                                <tr>
                                                    <td colSpan="5" className="px-4 py-8 text-center text-slate-400">
                                                        Agregue productos a la guía
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        <div className="flex justify-end gap-3 pt-4">
                            <button
                                type="button"
                                onClick={() => setActiveTab('list')}
                                className="px-6 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 text-sm font-medium"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                disabled={loading || !selectedOcId}
                                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50 shadow-lg shadow-blue-200"
                            >
                                {loading ? 'Guardando...' : 'Registrar Recepción'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Guide Detail Modal (unchanged logic) */}
            {selectedGuide && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h3 className="font-bold text-lg text-slate-800">Detalle de Guía {selectedGuide.numero_guia}</h3>
                            <button onClick={() => setSelectedGuide(null)} className="text-slate-400 hover:text-slate-600">
                                <FileText size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-slate-500">Proveedor</p>
                                    <p className="font-medium text-slate-800">{selectedGuide.proveedor_nombre || selectedGuide.proveedor}</p>
                                </div>
                                <div>
                                    <p className="text-slate-500">Fecha Recepción</p>
                                    <p className="font-medium text-slate-800">{selectedGuide.fecha || selectedGuide.fecha_recepcion}</p>
                                </div>
                                <div>
                                    <p className="text-slate-500">Orden de Compra</p>
                                    <p className="font-medium text-blue-600">
                                        {(selectedGuide.oc_id || selectedGuide.orden_compra_id) ? (
                                            <a href={`/purchase?ocId=${selectedGuide.oc_id || selectedGuide.orden_compra_id}&guideId=${selectedGuide.id}`} className="hover:underline flex items-center gap-1">
                                                OC-{String(selectedGuide.oc_id || selectedGuide.orden_compra_id).padStart(6, '0')} <Truck size={14} />
                                            </a>
                                        ) : '-'}
                                    </p>
                                </div>
                            </div>

                            <div className="border rounded-lg overflow-hidden">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-slate-50 text-slate-600">
                                        <tr>
                                            <th className="px-4 py-2">Producto</th>
                                            <th className="px-4 py-2 text-center">U.M.</th>
                                            <th className="px-4 py-2 text-right">Cant. Recibida</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {selectedGuide.items?.map((item, idx) => (
                                            <tr key={idx}>
                                                <td className="px-4 py-2">{item.producto}</td>
                                                <td className="px-4 py-2 text-center text-slate-500">{item.unidad_medida || item.um}</td>
                                                <td className="px-4 py-2 text-right font-medium">{Number(item.cantidad_recibida || item.cantidad || 0).toFixed(2)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
                            <button
                                onClick={() => setSelectedGuide(null)}
                                className="px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 text-sm font-medium"
                            >
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
