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
        orden_compra_id: null // Link to OC
    })

    useEffect(() => {
        Promise.all([
            api.getProducts(),
            api.getProviders(),
            fetch('http://localhost:8000/api/warehouses').then(r => r.json())
        ]).then(([prods, provs, whs]) => {
            setProducts(prods)
            setSuppliers(provs)
            setWarehouses(whs)
        }).catch(console.error)
    }, [])

    // Check for linked OC
    useEffect(() => {
        if (location.state && location.state.ocId) {
            loadOcData(location.state.ocId)
        }
    }, [location.state])

    const loadOcData = async (ocId) => {
        try {
            const res = await fetch(`http://localhost:8000/api/orders/${ocId}`)
            if (!res.ok) throw new Error("Error cargando OC")
            const data = await res.json()

            setFormData(prev => ({
                ...prev,
                proveedor_id: data.proveedor_id,
                fecha: new Date().toISOString().split('T')[0], // Use current date for invoice, or OC date? Usually invoice date.
                moneda: data.moneda,
                tasa_igv: data.tasa_igv,
                orden_compra_id: ocId,
                items: data.items.map(i => ({
                    pid: i.pid,
                    cantidad: i.cantidad,
                    precio_unitario: i.precio_unitario,
                    um: i.um
                }))
            }))
            setSuccessMsg(`Cargados datos de OC-${String(ocId).padStart(6, '0')}`)
        } catch (error) {
            setErrorMsg(error.message)
        }
    }

    const fetchHistory = async () => {
        try {
            const [summary, detailed] = await Promise.all([
                fetch('http://localhost:8000/api/purchases/summary').then(r => r.json()),
                fetch('http://localhost:8000/api/purchases/detailed').then(r => r.json())
            ])
            setPurchaseHistory(summary)
            setDetailedHistory(detailed)
        } catch (error) {
            console.error('Error fetching history:', error)
        }
    }

    useEffect(() => {
        if (view !== 'register') {
            fetchHistory()
        }
    }, [view])

    const addRow = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { pid: '', cantidad: 1, precio_unitario: 0, um: '' }]
        })
    }

    const updateItem = (index, field, value) => {
        const newItems = [...formData.items]
        newItems[index][field] = value

        // Auto-fill UM and last price when product is selected
        if (field === 'pid' && value) {
            const product = products.find(p => p.id === parseInt(value))
            if (product) {
                newItems[index].um = product.unidad_medida || ''
                // Only if not already set (e.g. from OC) logic? 
                // Careful not to overwrite price if loaded from OC but user changes product? 
                // If user changes product, we should fetch new price.
                newItems[index].precio_unitario = parseFloat(product.ultimo_precio_compra || 0).toFixed(2)
            }
        }

        setFormData({ ...formData, items: newItems })
    }

    const removeItem = (index) => {
        const newItems = formData.items.filter((_, i) => i !== index)
        setFormData({ ...formData, items: newItems })
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
                                                        <input required type="number" step="0.01" min="0.01" className="w-24 p-2 border border-slate-200 rounded text-sm text-right" value={item.cantidad} onChange={e => updateItem(idx, 'cantidad', e.target.value)} />
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <input required type="number" step="0.01" min="0" className="w-28 p-2 border border-slate-200 rounded text-sm text-right" value={item.precio_unitario} onChange={e => updateItem(idx, 'precio_unitario', e.target.value)} />
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
            )}

            {/* History Summary */}
            {view === 'history' && (
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
                                        <th className="px-6 py-4">Proveedor</th>
                                        <th className="px-6 py-4">Moneda</th>
                                        <th className="px-6 py-4 text-right">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {purchaseHistory.map((p, idx) => (
                                        <tr key={idx} className="hover:bg-slate-50">
                                            <td className="px-6 py-4">{p.fecha}</td>
                                            <td className="px-6 py-4 font-mono">{p.serie}-{p.numero}</td>
                                            <td className="px-6 py-4">{p.proveedor}</td>
                                            <td className="px-6 py-4">{p.moneda}</td>
                                            <td className="px-6 py-4 text-right font-medium">{p.moneda === 'USD' ? '$' : 'S/'} {p.total?.toFixed(2)}</td>
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
            )}

            {/* Detailed History */}
            {view === 'detailed' && (
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
            )}
        </div>
    )
}
