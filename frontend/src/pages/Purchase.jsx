import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Trash2, Save, AlertCircle, History, FileText } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import ProductSearch from '../components/ProductSearch'
import ExportButton from '../components/ExportButton'
import ModalProvider from '../components/ModalProvider' // Import Modal

export default function Purchase() {
    const location = useLocation()
    const [view, setView] = useState('register') // 'register' | 'history' | 'detailed'
    const [suppliers, setSuppliers] = useState([])
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [loading, setLoading] = useState(false)
    const [successMsg, setSuccessMsg] = useState('')
    const [errorMsg, setErrorMsg] = useState('')
    const [isProviderModalOpen, setIsProviderModalOpen] = useState(false) // Modal State

    // History data
    const [purchaseHistory, setPurchaseHistory] = useState([])
    const [detailedHistory, setDetailedHistory] = useState([])

    const [formData, setFormData] = useState({
        proveedor_id: '',
        fecha: new Date().toISOString().split('T')[0],
        moneda: 'PEN',
        serie: '',
        numero: '',
        tc: 3.85,
        tasa_igv: 18,
        almacen_id: '',
        items: [],
        orden_compra_id: null, // Link to OC
        guia_remision_id: null // Track guide reference
    })

    const [guides, setGuides] = useState([]) // Available guides
    const [selectedGuideId, setSelectedGuideId] = useState('')


    const loadInitialData = () => {
        Promise.all([
            api.getProducts(),
            api.getGuides(), // Fetch guides
            api.getProviders(),
            api.getWarehouses()
        ]).then(([prods, guidesData, provs, whs]) => {
            setProducts(prods)
            setGuides(guidesData) // Set guides
            setSuppliers(provs)
            setWarehouses(whs)
            if (whs.length > 0) {
                setFormData(prev => ({ ...prev, almacen_id: whs[0].id }))
            }
        }).catch(console.error)
    }

    useEffect(() => {
        loadInitialData()

        // Handle URL Parameters (Query String)
        const params = new URLSearchParams(location.search)
        const gid = params.get('guideId')
        const oid = params.get('ocId')

        if (gid && oid) {
            loadInvoiceFromGuide(gid, oid)
            setSelectedGuideId(gid)
        } else if (oid) {
            loadOcData(oid)
        } else if (gid) {
            handleImportGuide(gid)
        } else if (location.state?.ocId) {
            // Support previous state navigation if any
            loadOcData(location.state.ocId)
        }
    }, [])

    // New: Fetch history when view changes
    useEffect(() => {
        if (view === 'history') {
            api.getPurchasesSummary()
                .then(setPurchaseHistory)
                .catch(err => console.error("Error loading purchase history:", err))
        } else if (view === 'detailed') {
            api.getPurchasesDetailed()
                .then(setDetailedHistory)
                .catch(err => console.error("Error loading detailed history:", err))
        }
    }, [view])

    // Load Data from OC (navigated from Orders)
    // This useEffect is now redundant due to the combined useEffect above, but keeping it for context if needed elsewhere.
    // It will be effectively overridden by the new logic.
    // useEffect(() => {
    //     if (location.state?.ocId) {
    //         loadOcData(location.state.ocId)
    //     }
    // }, [location.state])

    const loadOcData = async (oid) => {
        setLoading(true)
        try {
            const data = await api.getOrder(oid)
            const order = data.header ? { ...data.header, items: data.items } : data;

            setFormData(prev => ({
                ...prev,
                proveedor_id: order.proveedor_id,
                fecha: new Date().toISOString().split('T')[0],
                moneda: order.moneda,
                tasa_igv: order.tasa_igv || 18,
                orden_compra_id: oid,
                almacen_id: order.almacen_id || prev.almacen_id || (warehouses.length > 0 ? warehouses[0].id : ''),
                observaciones: `Facturación de OC-${String(oid).padStart(6, '0')}`,
                items: (order.items || []).map(i => ({
                    pid: i.producto_id || i.pid,
                    cantidad: i.cantidad,
                    precio_unitario: i.precio_unitario || 0,
                    um: i.um || 'UN'
                }))
            }))
            setSuccessMsg(`Datos cargados de OC-${String(oid).padStart(6, '0')}`)
        } catch (error) {
            console.error(error)
            setErrorMsg("Error al cargar OC: " + error.message)
        } finally {
            setLoading(false)
        }
    }

    // ... (keep loadInvoiceFromGuide and loadOcData)

    // ...



    // New: Load Data safely merging OC Header + Guide Items
    const loadInvoiceFromGuide = async (gid, oid) => {
        setLoading(true)

        try {
            const [ocData, guideData] = await Promise.all([
                api.getOrder(oid),
                api.getGuide(gid)
            ])

            const gCab = guideData.cabecera || guideData
            const gItems = guideData.detalles || guideData.items || []
            const orderDoc = ocData.header ? { ...ocData.header, items: ocData.items } : ocData;

            const mergedItems = gItems.map(gItem => {
                const ocItem = (orderDoc.items || []).find(oItem => (oItem.producto_id || oItem.pid) === gItem.producto_id)
                const price = ocItem ? (ocItem.precio_unitario || ocItem.precio_unitario_pactado) : 0

                return {
                    pid: gItem.producto_id,
                    cantidad: gItem.cantidad_recibida,
                    precio_unitario: price,
                    um: gItem.unidad_medida || 'UN',
                    almacen_id: gItem.almacen_destino_id || 1
                }
            })

            setFormData(prev => ({
                ...prev,
                proveedor_id: orderDoc.proveedor_id,
                fecha: new Date().toISOString().split('T')[0],
                moneda: orderDoc.moneda,
                tasa_igv: orderDoc.tasa_igv || 18,
                orden_compra_id: oid,
                guia_remision_id: gid,
                almacen_id: gCab.almacen_destino_id || orderDoc.almacen_id || prev.almacen_id || (warehouses.length > 0 ? warehouses[0].id : ''),
                observaciones: `Facturación de Guía ${gCab.numero_guia} (OC-${String(oid).padStart(6, '0')})`,
                items: mergedItems
            }))

            setSuccessMsg(`Datos cargados: Guía ${gCab.numero_guia} + OC-${String(oid).padStart(6, '0')}`)

        } catch (error) {
            console.error(error)
            setErrorMsg("Error al cargar datos de Guía/OC: " + error.message)
        } finally {
            setLoading(false)
        }
    }

    const addRow = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { pid: '', cantidad: 1, precio_unitario: 0, um: '' }]
        })
    }

    const updateItem = (index, field, value) => {
        const newItems = [...formData.items]

        // Handle numeric inputs properly for cantidad and precio_unitario
        if (field === 'cantidad' || field === 'precio_unitario') {
            newItems[index][field] = value === '' ? '' : parseFloat(value)
        } else {
            newItems[index][field] = value
        }

        // Auto-fill UM and last price when product is selected
        if (field === 'pid' && value) {
            const product = products.find(p => p.id === parseInt(value))
            if (product) {
                newItems[index].um = product.unidad_medida || ''
                // Auto-populate price from last purchase or average cost, rounded to 2 decimals
                const price = product.ultimo_precio_compra || product.costo_promedio || 0
                newItems[index].precio_unitario = parseFloat(price.toFixed(2))
            }
        }

        setFormData({ ...formData, items: newItems })
    }

    const removeItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index)
        setFormData({ ...formData, items: newItems })
    }

    const handleImportGuide = async (gid) => {
        if (!gid) {
            setSelectedGuideId('')
            return
        }

        if (formData.items.length > 0 && !window.confirm("Esto reemplazará los items actuales. ¿Desea continuar? (Si desea facturar varias guías para una OC, límpielas primero o impórtelas una a una)")) {
            return
        }

        try {
            const data = await api.getGuide(gid)
            const cab = data.cabecera || data
            const items = data.detalles || data.items || []

            const newItems = items.map(i => {
                // Try to find price from existing items (likely loaded from OC)
                const existingItem = formData.items.find(ei => parseInt(ei.pid) === parseInt(i.producto_id))
                const price = existingItem ? (existingItem.precio_unitario || 0) : 0

                return {
                    pid: i.producto_id,
                    cantidad: i.cantidad_recibida,
                    precio_unitario: price,
                    um: i.unidad_medida || 'UN'
                }
            })

            setFormData({
                ...formData,
                items: newItems,
                guia_remision_id: gid,
                proveedor_id: cab.proveedor_id || formData.proveedor_id,
                observaciones: (formData.observaciones || '') + ` [Ref: Guía ${cab.numero_guia}]`
            })
            setSelectedGuideId(gid)
        } catch (error) {
            console.error("Error importing guide:", error)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.proveedor_id || formData.items.length === 0) {
            setErrorMsg('Proveedor e items son requeridos')
            return
        }

        if (!formData.almacen_id) {
            setErrorMsg('Debe seleccionar un almacén de destino (Sede)')
            return
        }

        setLoading(true)
        setErrorMsg('')
        setSuccessMsg('')

        try {
            const subtotalNeto = formData.items.reduce((sum, i) => sum + (parseFloat(i.cantidad || 0) * parseFloat(i.precio_unitario || 0)), 0)
            const grandTotal = subtotalNeto * (1 + (parseFloat(formData.tasa_igv) || 18) / 100)

            const payload = {
                ...formData,
                total: grandTotal,
                itemsToRegister: formData.items.map(i => ({
                    pid: parseInt(i.pid),
                    cantidad: parseFloat(i.cantidad),
                    precio_unitario: parseFloat(i.precio_unitario)
                }))
            }

            const res = await api.registerPurchase(payload)
            if (res.status === 'success') {
                setSuccessMsg('Compra registrada correctamente')
                setFormData({
                    proveedor_id: '',
                    fecha: new Date().toISOString().split('T')[0],
                    moneda: 'PEN',
                    serie: '',
                    numero: '',
                    tc: 3.85,
                    tasa_igv: 18,
                    items: [],
                    orden_compra_id: null
                })
                // Clear location state?
            }
        } catch (error) {
            setErrorMsg(error.message || 'Error al guardar')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <ModalProvider
                isOpen={isProviderModalOpen}
                onClose={() => setIsProviderModalOpen(false)}
                onProviderSaved={loadInitialData}
            />

            {/* Tabs */}
            <div className="flex space-x-2 border-b border-slate-200 dark:border-slate-700">
                <button
                    onClick={() => setView('register')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'register' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
                >
                    📝 Registrar Compra
                </button>
                <button
                    onClick={() => setView('history')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
                >
                    📜 Historial (Resumen)
                </button>
                <button
                    onClick={() => setView('detailed')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'detailed' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'}`}
                >
                    🔍 Historial (Detallado)
                </button>
            </div>

            {/* Register View */}
            {view === 'register' && (
                <form onSubmit={handleSubmit} className="space-y-6">
                    {successMsg && <div className="p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-lg">{successMsg}</div>}
                    {errorMsg && <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-lg">{errorMsg}</div>}

                    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Proveedor *</label>
                                <div className="flex gap-2">
                                    <select
                                        required
                                        className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        value={formData.proveedor_id}
                                        onChange={e => setFormData({ ...formData, proveedor_id: e.target.value })}
                                    >
                                        <option value="">Seleccionar...</option>
                                        {suppliers.map(s => <option key={s.id} value={s.id}>{s.razon_social}</option>)}
                                    </select>
                                    <button
                                        type="button"
                                        onClick={() => setIsProviderModalOpen(true)}
                                        className="p-2 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                                        title="Nuevo Proveedor"
                                    >
                                        <Plus size={20} />
                                    </button>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Fecha</label>
                                <input type="date" className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" value={formData.fecha} onChange={e => setFormData({ ...formData, fecha: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Serie *</label>
                                <input required type="text" placeholder="F001" className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400" value={formData.serie} onChange={e => setFormData({ ...formData, serie: e.target.value.toUpperCase() })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Número *</label>
                                <input required type="text" placeholder="000123" className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-400" value={formData.numero} onChange={e => setFormData({ ...formData, numero: e.target.value.toUpperCase() })} onBlur={e => setFormData({ ...formData, numero: e.target.value.padStart(6, '0') })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">📦 Sede / Almacén Destino *</label>
                                <select
                                    required
                                    className={`w-full p-2 border rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 ${warehouses.length === 0 ? 'border-amber-500 ring-amber-200' : 'border-slate-200 dark:border-slate-600 focus:ring-blue-500'}`}
                                    value={formData.almacen_id}
                                    onChange={e => setFormData({ ...formData, almacen_id: e.target.value })}
                                >
                                    <option value="">Seleccionar Sede...</option>
                                    {warehouses.map(w => <option key={w.id} value={w.id}>{w.nombre} {w.ubicacion ? `(${w.ubicacion})` : ''}</option>)}
                                </select>
                                {warehouses.length === 0 && (
                                    <p className="text-[10px] text-amber-600 mt-1 flex items-center gap-1">
                                        <AlertCircle size={10} /> No hay almacenes creados. Cree uno primero.
                                    </p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Moneda</label>
                                <select className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" value={formData.moneda} onChange={e => setFormData({ ...formData, moneda: e.target.value })}>
                                    <option value="PEN">Soles (PEN)</option>
                                    <option value="USD">Dólares (USD)</option>
                                </select>
                            </div>
                            {formData.moneda === 'USD' && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tipo de Cambio</label>
                                    <input type="number" step="0.001" className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" value={formData.tc} onChange={e => setFormData({ ...formData, tc: e.target.value })} />
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tasa IGV (%)</label>
                                <input type="number" step="0.01" className="w-full p-2 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" value={formData.tasa_igv} onChange={e => setFormData({ ...formData, tasa_igv: e.target.value })} />
                            </div>
                        </div>
                    </div>

                    {formData.proveedor_id && (
                        <div className="bg-blue-50 dark:bg-blue-900/10 p-4 rounded-lg border border-blue-100 dark:border-blue-900/30 flex items-center gap-4 transition-colors">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-blue-800 dark:text-blue-300 mb-1">
                                    Importar desde Guía de Remisión (Opcional)
                                </label>
                                <select
                                    className="w-full p-2 border border-blue-200 dark:border-blue-800 rounded text-sm bg-white dark:bg-slate-800 text-slate-800 dark:text-white"
                                    value={selectedGuideId}
                                    onChange={(e) => handleImportGuide(e.target.value)}
                                >
                                    <option value="">-- Seleccionar Guía --</option>
                                    {guides
                                        .filter(g => {
                                            const matchesProv = g.proveedor_nombre === suppliers.find(s => s.id == formData.proveedor_id)?.razon_social;
                                            const matchesOc = formData.orden_compra_id ? g.oc_id == formData.orden_compra_id : true;
                                            return matchesProv && matchesOc;
                                        })
                                        .map(g => (
                                            <option key={g.id} value={g.id}>
                                                {g.numero_guia} | {g.fecha} | {g.proveedor_nombre} {g.oc_id ? `(OC-${g.oc_id})` : ''}
                                            </option>
                                        ))}
                                </select>
                            </div>
                            <div className="text-xs text-blue-600 dark:text-blue-400 max-w-md">
                                Seleccione una guía para cargar automáticamente los productos recibidos y vincular la factura.
                            </div>
                        </div>
                    )}

                    {/* GRID FOR ITEMS */}
                    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-slate-800 dark:text-white">Items de Compra</h3>
                            <button type="button" onClick={addRow} className="flex items-center px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
                                <Plus size={16} className="mr-1" /> Agregar Producto
                            </button>
                        </div>

                        {formData.items.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-300 font-semibold">
                                        <tr>
                                            <th className="px-4 py-3 text-left">Producto *</th>
                                            <th className="px-4 py-3 text-left">U.M.</th>
                                            <th className="px-4 py-3 text-right">Cantidad *</th>
                                            <th className="px-4 py-3 text-right">Precio Unit. (Sin IGV) *</th>
                                            <th className="px-4 py-3 text-right">Subtotal (Neto)</th>
                                            <th className="px-4 py-3"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                        {formData.items.map((item, idx) => {
                                            const subtotal = (item.cantidad || 0) * (item.precio_unitario || 0)
                                            return (
                                                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                                    <td className="px-4 py-3 w-[400px]">
                                                        <ProductSearch
                                                            products={products}
                                                            value={item.pid}
                                                            onChange={(val) => updateItem(idx, 'pid', val)}
                                                            required={true}
                                                            isDark={true}
                                                        />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input type="text" disabled className="w-20 p-2 border border-slate-200 dark:border-slate-600 rounded text-sm bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400" value={item.um} readOnly />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input required type="number" step="0.01" min="0.01" className="w-24 p-2 border border-slate-200 dark:border-slate-600 rounded text-sm text-right bg-white dark:bg-slate-700 text-slate-800 dark:text-white" value={item.cantidad} onChange={e => updateItem(idx, 'cantidad', e.target.value)} onBlur={e => { const val = parseFloat(e.target.value); if (!isNaN(val)) updateItem(idx, 'cantidad', val.toFixed(2)) }} />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input required type="number" step="0.01" min="0" className="w-28 p-2 border border-slate-200 dark:border-slate-600 rounded text-sm text-right bg-white dark:bg-slate-700 text-slate-800 dark:text-white" value={item.precio_unitario} onChange={e => updateItem(idx, 'precio_unitario', e.target.value)} onBlur={e => { const val = parseFloat(e.target.value); if (!isNaN(val)) updateItem(idx, 'precio_unitario', val.toFixed(2)) }} />
                                                    </td>
                                                    <td className="px-4 py-3 text-right font-medium text-slate-800 dark:text-slate-200">
                                                        {formData.moneda === 'USD' ? '$' : 'S/'} {subtotal.toFixed(2)}
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <button type="button" onClick={() => removeItem(idx)} className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                    <tfoot className="bg-slate-50 dark:bg-slate-700/50 font-bold border-t-2 border-slate-200 dark:border-slate-600 text-slate-800 dark:text-white">
                                        <tr>
                                            <td colSpan="4" className="px-4 py-3 text-right">SUBTOTAL (Valor Neto):</td>
                                            <td className="px-4 py-3 text-right">
                                                {formData.moneda === 'USD' ? '$' : 'S/'} {(() => {
                                                    const subtotal = formData.items.reduce((sum, i) => {
                                                        return sum + ((i.cantidad || 0) * (i.precio_unitario || 0))
                                                    }, 0)
                                                    return subtotal.toFixed(2)
                                                })()}
                                            </td>
                                            <td></td>
                                        </tr>
                                        <tr>
                                            <td colSpan="4" className="px-4 py-3 text-right">IGV ({formData.tasa_igv}%):</td>
                                            <td className="px-4 py-3 text-right">
                                                {formData.moneda === 'USD' ? '$' : 'S/'} {(() => {
                                                    const subtotal = formData.items.reduce((sum, i) => {
                                                        return sum + ((i.cantidad || 0) * (i.precio_unitario || 0))
                                                    }, 0)
                                                    const igv = subtotal * (formData.tasa_igv / 100)
                                                    return igv.toFixed(2)
                                                })()}
                                            </td>
                                            <td></td>
                                        </tr>
                                        <tr className="text-lg">
                                            <td colSpan="4" className="px-4 py-3 text-right">TOTAL:</td>
                                            <td className="px-4 py-3 text-right text-blue-600 dark:text-blue-400">
                                                {formData.moneda === 'USD' ? '$' : 'S/'} {(() => {
                                                    const subtotal = formData.items.reduce((sum, i) => {
                                                        return sum + ((i.cantidad || 0) * (i.precio_unitario || 0))
                                                    }, 0)
                                                    const total = subtotal * (1 + formData.tasa_igv / 100)
                                                    return total.toFixed(2)
                                                })()}
                                            </td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-slate-400 dark:text-slate-500">
                                Haz clic en "Agregar Producto" para empezar
                            </div>
                        )}
                    </div>

                    <div className="flex justify-end">
                        <button type="submit" disabled={loading} className="px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center">
                            <Save size={18} className="mr-2" />
                            {loading ? 'Guardando...' : 'Registrar Compra'}
                        </button>
                    </div>
                </form>
            )
            }

            {/* History Summary */}
            {
                view === 'history' && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <ExportButton data={purchaseHistory} filename="historial_compras_resumen" />
                        </div>
                        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden transition-colors">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-100 dark:border-slate-700">
                                        <tr>
                                            <th className="px-6 py-4">Fecha</th>
                                            <th className="px-6 py-4">Documento</th>
                                            <th className="px-6 py-4">OC Ref</th>
                                            <th className="px-6 py-4">Proveedor</th>
                                            <th className="px-6 py-4">Moneda</th>
                                            <th className="px-6 py-4 text-right">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                        {purchaseHistory.map((p, idx) => (
                                            <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                                <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{p.fecha}</td>
                                                <td className="px-6 py-4 font-mono text-slate-600 dark:text-slate-400">{p.numero_documento}</td>
                                                <td className="px-6 py-4 font-mono text-blue-600 dark:text-blue-400">
                                                    {p.oc_id ? `OC-${String(p.oc_id).padStart(6, '0')}` : '-'}
                                                </td>
                                                <td className="px-6 py-4 text-slate-800 dark:text-slate-200">{p.proveedor}</td>
                                                <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{p.moneda}</td>
                                                <td className="px-6 py-4 text-right font-medium text-slate-800 dark:text-slate-200">{p.moneda === 'USD' ? '$' : 'S/'} {p.total_final?.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                        {purchaseHistory.length === 0 && (
                                            <tr><td colSpan="6" className="px-6 py-8 text-center text-slate-400 dark:text-slate-500">No hay registros</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )
            }

            {/* Detailed History */}
            {
                view === 'detailed' && (
                    <div className="space-y-4">
                        <div className="flex justify-end">
                            <ExportButton data={detailedHistory} filename="historial_compras_detallado" />
                        </div>
                        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden transition-colors">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 dark:bg-slate-700/50 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-100 dark:border-slate-700">
                                        <tr>
                                            <th className="px-6 py-4">Fecha</th>
                                            <th className="px-6 py-4">Documento</th>
                                            <th className="px-6 py-4">Proveedor</th>
                                            <th className="px-6 py-4">Producto</th>
                                            <th className="px-6 py-4 text-right">Cantidad</th>
                                            <th className="px-6 py-4 text-right">P. Unit.</th>
                                            <th className="px-6 py-4 text-right">Subtotal</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                        {detailedHistory.map((d, idx) => (
                                            <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                                <td className="px-6 py-4 text-slate-600 dark:text-slate-400">{d.fecha}</td>
                                                <td className="px-6 py-4 font-mono text-xs text-slate-600 dark:text-slate-400">{d.serie}-{d.numero}</td>
                                                <td className="px-6 py-4 text-slate-800 dark:text-slate-200">{d.proveedor}</td>
                                                <td className="px-6 py-4 text-slate-800 dark:text-slate-200">{d.producto}</td>
                                                <td className="px-6 py-4 text-right text-slate-700 dark:text-slate-300">{d.cantidad?.toFixed(2)}</td>
                                                <td className="px-6 py-4 text-right text-slate-600 dark:text-slate-400">{d.moneda === 'USD' ? '$' : 'S/'} {d.precio_unitario?.toFixed(2)}</td>
                                                <td className="px-6 py-4 text-right font-medium text-slate-800 dark:text-slate-200">{d.moneda === 'USD' ? '$' : 'S/'} {d.subtotal?.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                        {detailedHistory.length === 0 && (
                                            <tr><td colSpan="7" className="px-6 py-8 text-center text-slate-400 dark:text-slate-500">No hay registros</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    )
}
