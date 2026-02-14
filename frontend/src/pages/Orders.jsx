import React, { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Plus, Check, X, ArrowRight, Printer, Edit, Eye, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import ProductSearch from '../components/ProductSearch'

export default function Orders() {
    const navigate = useNavigate()
    // ... (rest of imports)

    const [view, setView] = useState('list') // 'list' | 'create' | 'detail'
    const [selectedOrder, setSelectedOrder] = useState(null)
    const [orders, setOrders] = useState([])
    const [suppliers, setSuppliers] = useState([])
    const [products, setProducts] = useState([])
    const [loading, setLoading] = useState(false)

    // Form State
    const [formData, setFormData] = useState({
        id: null,
        proveedor_id: '',
        fecha: new Date().toISOString().split('T')[0],
        fecha_entrega: new Date().toISOString().split('T')[0],
        moneda: 'PEN',
        items: []
    })

    useEffect(() => {
        fetchAllData()
    }, [])

    const fetchAllData = async () => {
        try {
            const [ords, provs, prods] = await Promise.all([
                api.getOrders(),
                api.getProviders(),
                api.getProducts()
            ])
            setOrders(Array.isArray(ords) ? ords : [])
            setSuppliers(Array.isArray(provs) ? provs : [])
            setProducts(Array.isArray(prods) ? prods : [])
        } catch (error) {
            console.error('Error fetching data:', error)
        }
    }

    const resetForm = () => {
        setFormData({
            id: null,
            proveedor_id: '',
            fecha: new Date().toISOString().split('T')[0],
            fecha_entrega: new Date().toISOString().split('T')[0],
            moneda: 'PEN',
            items: []
        })
    }

    const handleCreateWrapper = () => {
        resetForm()
        setView('create')
    }

    const handleEdit = async (orderId) => {
        try {
            const res = await fetch(`http://localhost:8000/api/orders/${orderId}`)
            if (!res.ok) throw new Error('Error al obtener orden')
            const data = await res.json()

            setFormData({
                id: data.id,
                proveedor_id: data.proveedor_id,
                fecha: data.fecha,
                fecha_entrega: data.fecha_entrega || data.fecha,
                moneda: data.moneda,
                items: data.items.map(i => ({
                    pid: i.pid,
                    cantidad: i.cantidad,
                    precio_unitario: i.precio_unitario,
                    um: i.um
                }))
            })
            setView('create')
        } catch (error) {
            alert(error.message)
        }
    }

    const handleViewDetail = async (orderId) => {
        try {
            const res = await fetch(`http://localhost:8000/api/orders/${orderId}`)
            if (!res.ok) throw new Error('Error al obtener orden')
            const data = await res.json()
            setSelectedOrder(data)
            setView('detail')
        } catch (error) {
            alert(error.message)
        }
    }

    const handleProcess = (orderId) => {
        navigate('/purchase', { state: { ocId: orderId } })
    }

    const handlePrint = async (orderId) => {
        try {
            const res = await fetch(`http://localhost:8000/api/orders/${orderId}`)
            const data = await res.json()

            const doc = new jsPDF()

            // Header: Logo placeholder
            doc.setFillColor(240, 240, 240)
            doc.rect(0, 0, 210, 40, 'F')

            doc.setFontSize(22)
            doc.setTextColor(40, 40, 40)
            doc.text("ORDEN DE COMPRA", 105, 25, { align: 'center' })

            // Info Line
            doc.setFontSize(10)
            doc.setTextColor(0, 0, 0)
            const yStart = 50

            doc.setFont(undefined, 'bold')
            doc.text("DATOS DEL PROVEEDOR:", 14, yStart)
            doc.setFont(undefined, 'normal')
            doc.text(data.proveedor_nombre || "N/A", 14, yStart + 5)
            doc.text(`RUC: ${data.proveedor_ruc || '-'}`, 14, yStart + 10)

            doc.setFont(undefined, 'bold')
            doc.text("DETALLES OC:", 140, yStart)
            doc.setFont(undefined, 'normal')
            doc.text(`Número: OC-${String(data.id || 0).padStart(6, '0')}`, 140, yStart + 5)
            doc.text(`Fecha Emisión: ${data.fecha || '-'}`, 140, yStart + 10)
            doc.text(`Fecha Entrega: ${data.fecha_entrega || '-'}`, 140, yStart + 15)
            doc.text(`Moneda: ${data.moneda || 'PEN'}`, 140, yStart + 20)

            // Table
            const columns = ["#", "Producto", "Cant.", "U.M.", "P. Unit (S/ IGV)", "Total"]
            const rows = (data.items || []).map((item, idx) => [
                idx + 1,
                item.Producto || 'Item',
                Number(item.cantidad || 0).toFixed(2),
                item.um || 'NIU',
                Number(item.precio_unitario || 0).toFixed(2),
                (Number(item.cantidad || 0) * Number(item.precio_unitario || 0)).toFixed(2)
            ])

            autoTable(doc, {
                startY: yStart + 30,
                head: [columns],
                body: rows,
                theme: 'striped',
                headStyles: { fillColor: [41, 128, 185] },
                styles: { fontSize: 9 }
            })

            const finalY = (doc.lastAutoTable?.finalY || yStart + 30) + 10

            // Totals
            doc.setFontSize(11)
            doc.setFont(undefined, 'bold')
            const symbol = data.moneda === 'USD' ? '$' : 'S/'
            doc.text(`Total General: ${symbol} ${Number(data.total || 0).toFixed(2)}`, 190, finalY, { align: 'right' })

            // Footer
            doc.setFontSize(8)
            doc.text("Documento generado por ERP Moderno v2", 105, 280, { align: 'center' })

            window.open(doc.output('bloburl'), '_blank')
        } catch (error) {
            console.error(error)
            alert(`Error al generar PDF: ${error.message}`)
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

        if (field === 'cantidad' || field === 'precio_unitario') {
            // Handle numeric inputs and empty strings
            newItems[index][field] = value === '' ? '' : parseFloat(value)
        } else {
            newItems[index][field] = value
        }

        if (field === 'pid') {
            const prod = products.find(p => p.id === parseInt(value))
            if (prod) {
                newItems[index].um = prod.unidad_medida || 'UN'
                // Auto-populate price from last purchase or average cost
                newItems[index].precio_unitario = prod.ultimo_precio_compra || prod.costo_promedio || 0
            }
        }
        setFormData({ ...formData, items: newItems })
    }

    const removeItem = (index) => {
        setFormData({
            ...formData,
            items: formData.items.filter((_, i) => i !== index)
        })
    }

    const calculateTotal = () => {
        return formData.items.reduce((acc, item) => acc + ((item.cantidad || 0) * (item.precio_unitario || 0)), 0)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.proveedor_id || formData.items.length === 0) {
            alert('Complete los campos requeridos (Proveedor e Items)')
            return
        }

        setLoading(true)
        try {
            let res
            if (formData.id) {
                // Update
                res = await fetch(`http://localhost:8000/api/orders/${formData.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                })
            } else {
                // Create
                res = await fetch('http://localhost:8000/api/orders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                })
            }

            const data = await res.json()

            if (res.ok) {
                alert(formData.id ? 'Orden actualizada' : `Orden creada: ${data.correlativo}`)
                setView('list')
                fetchAllData()
            } else {
                alert(data.detail || 'Error al guardar')
            }
        } catch (error) {
            alert(`Error de conexión: ${error.message}`)
        } finally {
            setLoading(false)
        }
    }

    const handleStatusChange = async (id, status) => {
        if (!confirm(`¿Cambiar estado a ${status}?`)) return
        try {
            await api.updateOrderStatus(id, status)
            fetchAllData()
        } catch (error) {
            alert(error.message)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex space-x-2 border-b border-slate-200">
                <button
                    onClick={() => setView('list')}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'list' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    📋 Listado
                </button>
                <button
                    onClick={handleCreateWrapper}
                    className={`px-4 py-2 font-medium transition-colors ${view === 'create' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    ➕ Nueva Orden (OC)
                </button>
            </div>

            {view === 'list' && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-50 text-slate-700 font-semibold">
                                <tr>
                                    <th className="px-6 py-4">Orden #</th>
                                    <th className="px-6 py-4">Proveedor</th>
                                    <th className="px-6 py-4">Fecha</th>
                                    <th className="px-6 py-4">Total</th>
                                    <th className="px-6 py-4">Estado</th>
                                    <th className="px-6 py-4 text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {orders.length > 0 ? (
                                    orders.map((order) => (
                                        <tr key={order.id} className="hover:bg-slate-50">
                                            <td className="px-6 py-4 font-mono text-xs">OC-{String(order.id).padStart(6, '0')}</td>
                                            <td className="px-6 py-4 font-medium">{order.proveedor_nombre}</td>
                                            <td className="px-6 py-4 text-slate-600">{order.fecha}</td>
                                            <td className="px-6 py-4 font-bold text-slate-800">
                                                {order.moneda === 'USD' ? '$' : 'S/'} {parseFloat(order.total).toFixed(2)}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${order.estado === 'PENDIENTE' ? 'bg-amber-100 text-amber-700' :
                                                    order.estado === 'APROBADA' ? 'bg-blue-100 text-blue-700' :
                                                        order.estado === 'COMPLETADA' ? 'bg-green-100 text-green-700' :
                                                            'bg-slate-100 text-slate-700'
                                                    }`}>
                                                    {order.estado}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-center space-x-2">
                                                <button onClick={() => handleViewDetail(order.id)} className="p-1 text-slate-400 hover:text-slate-600" title="Ver Detalle">
                                                    <Eye size={16} />
                                                </button>
                                                {order.estado === 'PENDIENTE' && (
                                                    <button onClick={() => handleStatusChange(order.id, 'APROBADA')} className="p-1 text-blue-400 hover:text-blue-600" title="Aprobar">
                                                        <Check size={16} />
                                                    </button>
                                                )}
                                                {order.estado === 'APROBADA' && (
                                                    <button onClick={() => handleProcess(order.id)} className="p-1 text-emerald-400 hover:text-emerald-600" title="Procesar Compra">
                                                        <ArrowRight size={16} />
                                                    </button>
                                                )}
                                                {order.estado === 'ANULADA' && (
                                                    <span className="text-gray-400 text-xs">Anulada</span>
                                                )}
                                                {order.estado === 'PENDIENTE' && (
                                                    <button onClick={() => handleStatusChange(order.id, 'ANULADA')} className="p-1 text-red-600 hover:text-red-800" title="Anular">
                                                        <X size={16} />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr><td colSpan="6" className="px-6 py-8 text-center text-slate-400">No hay órdenes registradas</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {view === 'create' && (
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Proveedor *</label>
                                <select required className="w-full p-2 border border-slate-200 rounded-lg" value={formData.proveedor_id} onChange={e => setFormData({ ...formData, proveedor_id: e.target.value })}>
                                    <option value="">Seleccionar...</option>
                                    {suppliers.map(p => <option key={p.id} value={p.id}>{p.razon_social}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Fecha Emisión</label>
                                <input type="date" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.fecha} onChange={e => setFormData({ ...formData, fecha: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Fecha Entrega Est.</label>
                                <input type="date" className="w-full p-2 border border-slate-200 rounded-lg" value={formData.fecha_entrega} onChange={e => setFormData({ ...formData, fecha_entrega: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Moneda</label>
                                <select className="w-full p-2 border border-slate-200 rounded-lg" value={formData.moneda} onChange={e => setFormData({ ...formData, moneda: e.target.value })}>
                                    <option value="PEN">Soles (PEN)</option>
                                    <option value="USD">Dólares (USD)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <table className="w-full text-left text-sm mb-4">
                            <thead>
                                <tr className="text-slate-500 border-b border-slate-200">
                                    <th className="pb-3 w-1/3">Producto</th>
                                    <th className="pb-3 w-24">Cantidad</th>
                                    <th className="pb-3 w-32">Precio (Sin IGV)</th>
                                    <th className="pb-3 w-20">U.M.</th>
                                    <th className="pb-3 w-32 text-right">Subtotal</th>
                                    <th className="pb-3 w-10"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {formData.items.map((item, index) => (
                                    <tr key={index}>
                                        <td className="py-2">
                                            <ProductSearch
                                                products={products}
                                                value={item.pid}
                                                onChange={(val) => updateItem(index, 'pid', val)}
                                                required={true}
                                            />
                                        </td>
                                        <td className="py-2">
                                            <input
                                                type="number"
                                                min="0.1"
                                                step="0.1"
                                                className="w-full p-2 border border-slate-200 rounded"
                                                value={item.cantidad}
                                                onChange={(e) => updateItem(index, 'cantidad', e.target.value)}
                                                required
                                            />
                                        </td>
                                        <td className="py-2">
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                className="w-full p-2 border border-slate-200 rounded"
                                                value={item.precio_unitario}
                                                onChange={(e) => updateItem(index, 'precio_unitario', e.target.value)}
                                                onBlur={(e) => {
                                                    const val = parseFloat(e.target.value);
                                                    if (!isNaN(val)) {
                                                        updateItem(index, 'precio_unitario', val.toFixed(2));
                                                    }
                                                }}
                                                required
                                            />
                                        </td>
                                        <td className="py-2 text-slate-500">{item.um}</td>
                                        <td className="py-2 text-right font-medium">
                                            {((item.cantidad || 0) * (item.precio_unitario || 0)).toFixed(2)}
                                        </td>
                                        <td className="py-2 text-right">
                                            <button type="button" onClick={() => removeItem(index)} className="text-red-500 hover:text-red-700">
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colSpan="4" className="pt-4 text-right font-bold text-slate-700">Total Orden ({formData.moneda}):</td>
                                    <td className="pt-4 text-right font-bold text-blue-600 text-lg">
                                        {calculateTotal().toFixed(2)}
                                    </td>
                                    <td></td>
                                </tr>
                            </tfoot>
                        </table>

                        <button type="button" onClick={addRow} className="flex items-center text-blue-600 font-medium hover:text-blue-700">
                            <Plus size={16} className="mr-1" /> Agregar Item
                        </button>
                    </div>

                    <div className="flex justify-end gap-3">
                        <button type="button" onClick={() => setView('list')} className="px-6 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 font-medium">
                            Cancelar
                        </button>
                        <button type="submit" disabled={loading} className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow-lg shadow-blue-200 transition-all">
                            {loading ? 'Guardando...' : 'Guardar Orden'}
                        </button>
                    </div>
                </form>
            )}

            {view === 'detail' && selectedOrder && (
                <div className="space-y-6 animate-in fade-in duration-300">
                    <div className="bg-slate-800 text-white p-6 rounded-xl shadow-lg flex justify-between items-center">
                        <div>
                            <p className="text-blue-200 text-sm font-semibold uppercase tracking-wider mb-1">Orden de Compra</p>
                            <h2 className="text-3xl font-bold">OC-{String(selectedOrder.id).padStart(6, '0')}</h2>
                        </div>
                        <div className="text-right">
                            <p className="text-sm opacity-80">Fecha: {selectedOrder.fecha}</p>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase mt-2 inline-block ${selectedOrder.estado === 'PENDIENTE' ? 'bg-amber-500 text-amber-900' :
                                selectedOrder.estado === 'APROBADA' ? 'bg-blue-500 text-white' :
                                    'bg-emerald-500 text-white'
                                }`}>
                                {selectedOrder.estado}
                            </span>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <h3 className="font-bold text-slate-700 mb-4 border-b border-slate-100 pb-2">Información del Proveedor</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <p className="text-xs text-slate-400 uppercase">Razón Social</p>
                                <p className="font-medium text-slate-800 text-lg">{selectedOrder.proveedor_nombre}</p>
                            </div>
                            <div>
                                <p className="text-xs text-slate-400 uppercase">RUC / ID</p>
                                <p className="font-medium text-slate-800">{selectedOrder.proveedor_ruc || 'N/A'}</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <h3 className="font-bold text-slate-700 mb-4 border-b border-slate-100 pb-2">Detalle de Items</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 text-slate-600">
                                    <tr>
                                        <th className="px-4 py-3">#</th>
                                        <th className="px-4 py-3">Producto</th>
                                        <th className="px-4 py-3 text-center">U.M.</th>
                                        <th className="px-4 py-3 text-right">Cantidad</th>
                                        <th className="px-4 py-3 text-right">Precio Unit.</th>
                                        <th className="px-4 py-3 text-right">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {(selectedOrder.items || []).map((item, idx) => (
                                        <tr key={idx}>
                                            <td className="px-4 py-3 text-slate-400 font-mono text-xs">{idx + 1}</td>
                                            <td className="px-4 py-3 font-medium text-slate-800">{item.Producto || item.producto}</td>
                                            <td className="px-4 py-3 text-center text-slate-500">{item.um || item.UM}</td>
                                            <td className="px-4 py-3 text-right font-medium">{Number(item.cantidad).toFixed(2)}</td>
                                            <td className="px-4 py-3 text-right text-slate-600">
                                                {selectedOrder.moneda === 'USD' ? '$' : 'S/'} {Number(item.precio_unitario).toFixed(2)}
                                            </td>
                                            <td className="px-4 py-3 text-right font-bold text-slate-800">
                                                {selectedOrder.moneda === 'USD' ? '$' : 'S/'} {(Number(item.cantidad) * Number(item.precio_unitario)).toFixed(2)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <td colSpan="5" className="pt-4 text-right">Subtotal:</td>
                                        <td className="pt-4 text-right font-medium text-slate-600">
                                            {selectedOrder.moneda === 'USD' ? '$' : 'S/'} {(Number(selectedOrder.total || 0) / 1.18).toFixed(2)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colSpan="5" className="text-right">IGV (18%):</td>
                                        <td className="text-right font-medium text-slate-600">
                                            {selectedOrder.moneda === 'USD' ? '$' : 'S/'} {(Number(selectedOrder.total || 0) - (Number(selectedOrder.total || 0) / 1.18)).toFixed(2)}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td colSpan="5" className="pt-2 text-right font-bold text-xl text-slate-800">TOTAL:</td>
                                        <td className="pt-2 text-right font-bold text-xl text-blue-600">
                                            {selectedOrder.moneda === 'USD' ? '$' : 'S/'} {Number(selectedOrder.total || 0).toFixed(2)}
                                        </td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>

                    <div className="flex justify-between items-center pt-4">
                        <button
                            onClick={() => setView('list')}
                            className="px-6 py-2.5 border border-slate-300 rounded-lg text-slate-600 font-medium hover:bg-slate-50 transition-colors"
                        >
                            ← Volver al Listado
                        </button>
                        <div className="flex gap-3">
                            {selectedOrder.estado === 'PENDIENTE' && (
                                <button
                                    onClick={() => handleStatusChange(selectedOrder.id, 'APROBADA')}
                                    className="px-6 py-2.5 bg-blue-100 text-blue-700 rounded-lg font-medium hover:bg-blue-200 transition-colors flex items-center gap-2"
                                >
                                    <Check size={18} /> Aprobar Orden
                                </button>
                            )}
                            <button
                                onClick={() => handlePrint(selectedOrder.id)}
                                className="px-6 py-2.5 bg-slate-800 text-white rounded-lg font-medium hover:bg-slate-900 transition-colors flex items-center gap-2 shadow-lg shadow-slate-200"
                            >
                                <Printer size={18} /> Imprimir / Descargar PDF
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
