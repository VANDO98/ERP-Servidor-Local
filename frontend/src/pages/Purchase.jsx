import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Trash2, Save, AlertCircle, History, FileText } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import ProductSearch from '../components/ProductSearch'
import ExportButton from '../components/ExportButton'

export default function Purchase() {
    const location = useLocation()
    const [view, setView] = useState('register') // 'register' | 'history' | 'detailed'
    const [suppliers, setSuppliers] = useState([])
    const [products, setProducts] = useState([])
    const [warehouses, setWarehouses] = useState([])
    const [loading, setLoading] = useState(false)
    const [successMsg, setSuccessMsg] = useState('')
    const [errorMsg, setErrorMsg] = useState('')

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
        items: [],
        orden_compra_id: null, // Link to OC
        guia_remision_id: null // Track guide reference
    })

    const [guides, setGuides] = useState([]) // Available guides
    const [selectedGuideId, setSelectedGuideId] = useState('')

    useEffect(() => {
        Promise.all([
            api.getProducts(),
            api.getGuides(), // Fetch guides
            api.getProviders(),
            fetch('http://localhost:8000/api/warehouses').then(r => r.json())
        ]).then(([prods, guidesData, provs, whs]) => {
            setProducts(prods)
            setGuides(guidesData) // Set guides
            setSuppliers(provs)
            setWarehouses(whs)
        }).catch(console.error)
    }, [])

    useEffect(() => {
        const params = new URLSearchParams(location.search)
        const ocId = params.get('ocId')
        const guideId = params.get('guideId')

        if (guideId && ocId) {
            loadInvoiceFromGuide(guideId, ocId)
        } else if (ocId) {
            loadOcData(ocId)
        } else if (view !== 'register') {
            fetchHistory()
        }
    }, [location.search, view])

    // New: Load Data safely merging OC Header + Guide Items
    const loadInvoiceFromGuide = async (gid, oid) => {
        setLoading(true)
        try {
            // 1. Fetch both in parallel
            const [resOc, resGuide] = await Promise.all([
                fetch(`http://localhost:8000/api/orders/${oid}`),
                fetch(`http://localhost:8000/api/guides/${gid}`)
            ])

            if (!resOc.ok) throw new Error("Error cargando OC")
            if (!resGuide.ok) throw new Error("Error cargando Guía")

            const ocData = await resOc.json()
            const guideData = await resGuide.json()

            // 2. Prepare items from GUIDE (received quantities)
            // Note: Guide items might not have price, so we try to match with OC items to get price
            const mergedItems = guideData.items.map(gItem => {
                // Find matching item in OC to get requested price
                // Match by Product ID
                const ocItem = ocData.items.find(oItem => oItem.pid === gItem.producto_id)
                const price = ocItem ? ocItem.precio_unitario : 0

                return {
                    pid: gItem.producto_id,
                    cantidad: gItem.cantidad_recibida, // Use RECEIVED quantity
                    precio_unitario: price,
                    um: gItem.unidad_medida || 'UN',
                    almacen_id: gItem.almacen_destino_id || 1
                }
            })

            // 3. Set Form Data: OC Header + Guide Items
            setFormData(prev => ({
                ...prev,
                proveedor_id: ocData.proveedor_id,
                fecha: new Date().toISOString().split('T')[0],
                moneda: ocData.moneda,
                tasa_igv: ocData.tasa_igv,
                orden_compra_id: oid,
                guia_remision_id: gid,
                observaciones: `Facturación de Guía ${guideData.numero_guia} (OC-${String(oid).padStart(6, '0')})`,
                items: mergedItems
            }))

            setSuccessMsg(`Datos cargados: Guía ${guideData.numero_guia} + OC-${String(oid).padStart(6, '0')}`)

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

        if (formData.items.length > 0 && !window.confirm("Esto reemplazará los items actuales. ¿Desea continuar?")) {
            return
        }

        try {
            const res = await fetch(`http://localhost:8000/api/guides/${gid}`)
            const data = await res.json()

            const newItems = data.items.map(i => ({
                pid: i.producto_id,
                cantidad: i.cantidad_recibida,
                precio_unitario: 0, // User must enter price
                um: i.unidad_medida || 'UN'
            }))

            setFormData({
                ...formData,
                items: newItems,
                guia_remision_id: gid,
                proveedor_id: data.proveedor_id || formData.proveedor_id, // Auto-select provider if possible
                observaciones: (formData.observaciones || '') + ` [Ref: Guía ${data.numero_guia}]`
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

        setLoading(true)
        setErrorMsg('')
        setSuccessMsg('')

        try {
            const payload = {
                ...formData,
                items: formData.items.map(i => ({
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
            {/* Tabs */}
            <div className="flex space-x-2 border-b border-slate-200">
                <button
                    onClick={() => setView('register')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'register' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    📝 Registrar Compra
                </button>
                <button
                    onClick={() => setView('history')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    📜 Historial (Resumen)
                </button>
                <button
                    onClick={() => setView('detailed')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'detailed' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    🔍 Historial (Detallado)
                </button>
            </div>

            {/* Register View */}
            {view === 'register' && (
                <form onSubmit={handleSubmit} className="space-y-6">
                    {successMsg && <div className="p-4 bg-green-50 text-green-700 rounded-lg">{successMsg}</div>}
                    {errorMsg && <div className="p-4 bg-red-50 text-red-700 rounded-lg">{errorMsg}</div>}

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Proveedor *</label>
                                <select required className="w-full p-2 border border-slate-200 rounded-lg" value={formData.proveedor_id} onChange={e => setFormData({ ...formData, proveedor_id: e.target.value })}>
                                    <option value="">Seleccionar...</option>
                                    {suppliers.map(s => <option key={s.id} value={s.id}>{s.razon_social}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Fecha</label>
                                <input type="date" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.fecha} onChange={e => setFormData({ ...formData, fecha: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Serie *</label>
                                <input required type="text" placeholder="F001" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.serie} onChange={e => setFormData({ ...formData, serie: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Número *</label>
                                <input required type="text" placeholder="000123" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.numero} onChange={e => setFormData({ ...formData, numero: e.target.value })} />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Moneda</label>
                                <select className="w-full p-2 border border-slate-200 rounded-lg" value={formData.moneda} onChange={e => setFormData({ ...formData, moneda: e.target.value })}>
                                    <option value="PEN">Soles (PEN)</option>
                                    <option value="USD">Dólares (USD)</option>
                                </select>
                            </div>
                            {formData.moneda === 'USD' && (
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Cambio</label>
                                    <input type="number" step="0.001" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.tc} onChange={e => setFormData({ ...formData, tc: e.target.value })} />
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Tasa IGV (%)</label>
                                <input type="number" step="0.01" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.tasa_igv} onChange={e => setFormData({ ...formData, tasa_igv: e.target.value })} />
                            </div>
                        </div>
                    </div>

                    {/* Guide Import Section */}
                    {formData.proveedor_id && (
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 flex items-center gap-4">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-blue-800 mb-1">
                                    Importar desde Guía de Remisión (Opcional)
                                </label>
                                <select
                                    className="w-full p-2 border border-blue-200 rounded text-sm"
                                    value={selectedGuideId}
                                    onChange={(e) => handleImportGuide(e.target.value)}
                                >
                                    <option value="">-- Seleccionar Guía --</option>
                                    {guides
                                        .filter(g => g.proveedor == suppliers.find(s => s.id == formData.proveedor_id)?.razon_social) // Filter by provider name logic matching
                                        // Note: guides endpoint returns 'proveedor' name, not ID. suppliers has 'razon_social'.
                                        // Wait, backend 'obtener_guias' returns 'proveedor' (name).
                                        // Ideally we filter by ID if available, but list endpoint didn't verify ID return.
                                        // Let's verify backend 'obtener_guias' -> returns g.id, g.fecha..., p.razon_social as proveedor.
                                        // It DOES NOT return p.id as provider_id. 
                                        // So filtering by name is risky but necessary unless I update backend.
                                        // OR I just show all guides. 
                                        // Let's check backend code again?
                                        // Backend line 2470: p.razon_social as proveedor.
                                        // It does not select p.id.
                                        // I'll filter by name for now, or just show all if no match.
                                        .map(g => (
                                            <option key={g.id} value={g.id}>
                                                {g.numero_guia} | {g.fecha_recepcion} | {g.proveedor}
                                            </option>
                                        ))}
                                </select>
                            </div>
                            <div className="text-xs text-blue-600 max-w-md">
                                Seleccione una guía para cargar automáticamente los productos recibidos y vincular la factura.
                            </div>
                        </div>
                    )}

                    {/* GRID FOR ITEMS */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-slate-800">Items de Compra</h3>
                            <button type="button" onClick={addRow} className="flex items-center px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
                                <Plus size={16} className="mr-1" /> Agregar Producto
                            </button>
                        </div>

                        {formData.items.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-slate-50 text-slate-700 font-semibold">
                                        <tr>
                                            <th className="px-4 py-3 text-left">Producto *</th>
                                            <th className="px-4 py-3 text-left">U.M.</th>
                                            <th className="px-4 py-3 text-right">Cantidad *</th>
                                            <th className="px-4 py-3 text-right">Precio Unit. *</th>
                                            <th className="px-4 py-3 text-right">Subtotal</th>
                                            <th className="px-4 py-3"></th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {formData.items.map((item, idx) => {
                                            const subtotal = (item.cantidad || 0) * (item.precio_unitario || 0)
                                            return (
                                                <tr key={idx} className="hover:bg-slate-50">
                                                    <td className="px-4 py-3 w-[400px]">
                                                        <ProductSearch
                                                            products={products}
                                                            value={item.pid}
                                                            onChange={(val) => updateItem(idx, 'pid', val)}
                                                            required={true}
                                                        />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input type="text" disabled className="w-20 p-2 border border-slate-200 rounded text-sm bg-slate-50" value={item.um} readOnly />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input required type="number" step="0.01" min="0.01" className="w-24 p-2 border border-slate-200 rounded text-sm text-right" value={item.cantidad} onChange={e => updateItem(idx, 'cantidad', e.target.value)} onBlur={e => { const val = parseFloat(e.target.value); if (!isNaN(val)) updateItem(idx, 'cantidad', val.toFixed(2)) }} />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input required type="number" step="0.01" min="0" className="w-28 p-2 border border-slate-200 rounded text-sm text-right" value={item.precio_unitario} onChange={e => updateItem(idx, 'precio_unitario', e.target.value)} onBlur={e => { const val = parseFloat(e.target.value); if (!isNaN(val)) updateItem(idx, 'precio_unitario', val.toFixed(2)) }} />
                                                    </td>
                                                    <td className="px-4 py-3 text-right font-medium">
                                                        S/ {subtotal.toFixed(2)}
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <button type="button" onClick={() => removeItem(idx)} className="text-red-500 hover:text-red-700">
                                                            <Trash2 size={16} />
                                                        </button>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                    <tfoot className="bg-slate-50 font-bold border-t-2 border-slate-200">
                                        <tr>
                                            <td colSpan="4" className="px-4 py-3 text-right">SUBTOTAL (Valor Neto):</td>
                                            <td className="px-4 py-3 text-right">
                                                S/ {(() => {
                                                    const subtotal = formData.items.reduce((sum, i) => {
                                                        const precioInclIGV = parseFloat(i.precio_unitario) || 0
                                                        const precioNeto = precioInclIGV / (1 + formData.tasa_igv / 100)
                                                        return sum + ((i.cantidad || 0) * precioNeto)
                                                    }, 0)
                                                    return subtotal.toFixed(2)
                                                })()}
                                            </td>
                                            <td></td>
                                        </tr>
                                        <tr>
                                            <td colSpan="4" className="px-4 py-3 text-right">IGV ({formData.tasa_igv}%):</td>
                                            <td className="px-4 py-3 text-right">
                                                S/ {(() => {
                                                    const subtotal = formData.items.reduce((sum, i) => {
                                                        const precioInclIGV = parseFloat(i.precio_unitario) || 0
                                                        const precioNeto = precioInclIGV / (1 + formData.tasa_igv / 100)
                                                        return sum + ((i.cantidad || 0) * precioNeto)
                                                    }, 0)
                                                    const igv = subtotal * (formData.tasa_igv / 100)
                                                    return igv.toFixed(2)
                                                })()}
                                            </td>
                                            <td></td>
                                        </tr>
                                        <tr className="text-lg">
                                            <td colSpan="4" className="px-4 py-3 text-right">TOTAL:</td>
                                            <td className="px-4 py-3 text-right text-blue-600">
                                                S/ {formData.items.reduce((sum, i) => sum + ((i.cantidad || 0) * (i.precio_unitario || 0)), 0).toFixed(2)}
                                            </td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-slate-400">
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
                        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-100">
                                        <tr>
                                            <th className="px-6 py-4">Fecha</th>
                                            <th className="px-6 py-4">Documento</th>
                                            <th className="px-6 py-4">OC Ref</th>
                                            <th className="px-6 py-4">Proveedor</th>
                                            <th className="px-6 py-4">Moneda</th>
                                            <th className="px-6 py-4 text-right">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {purchaseHistory.map((p, idx) => (
                                            <tr key={idx} className="hover:bg-slate-50">
                                                <td className="px-6 py-4">{p.fecha}</td>
                                                <td className="px-6 py-4 font-mono">{p.numero_documento}</td>
                                                <td className="px-6 py-4 font-mono text-blue-600">
                                                    {p.oc_id ? `OC-${String(p.oc_id).padStart(6, '0')}` : '-'}
                                                </td>
                                                <td className="px-6 py-4">{p.proveedor}</td>
                                                <td className="px-6 py-4">{p.moneda}</td>
                                                <td className="px-6 py-4 text-right font-medium">{p.moneda === 'USD' ? '$' : 'S/'} {p.total_final?.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                        {purchaseHistory.length === 0 && (
                                            <tr><td colSpan="5" className="px-6 py-8 text-center text-slate-400">No hay registros</td></tr>
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
                        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left text-sm">
                                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-100">
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
                                    <tbody className="divide-y divide-slate-100">
                                        {detailedHistory.map((d, idx) => (
                                            <tr key={idx} className="hover:bg-slate-50">
                                                <td className="px-6 py-4">{d.fecha}</td>
                                                <td className="px-6 py-4 font-mono text-xs">{d.serie}-{d.numero}</td>
                                                <td className="px-6 py-4">{d.proveedor}</td>
                                                <td className="px-6 py-4">{d.producto}</td>
                                                <td className="px-6 py-4 text-right">{d.cantidad?.toFixed(2)}</td>
                                                <td className="px-6 py-4 text-right">{d.moneda === 'USD' ? '$' : 'S/'} {d.precio_unitario?.toFixed(2)}</td>
                                                <td className="px-6 py-4 text-right font-medium">{d.moneda === 'USD' ? '$' : 'S/'} {d.subtotal?.toFixed(2)}</td>
                                            </tr>
                                        ))}
                                        {detailedHistory.length === 0 && (
                                            <tr><td colSpan="7" className="px-6 py-8 text-center text-slate-400">No hay registros</td></tr>
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
