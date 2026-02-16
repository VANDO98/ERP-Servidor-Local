import React, { useState, useEffect } from 'react'
import { Upload, Download, FileText, CheckCircle, AlertCircle, AlertTriangle, Boxes } from 'lucide-react'
import { api } from '../services/api'

export default function DataManagement() {
    const [activeTab, setActiveTab] = useState('upload')
    const [uploadType, setUploadType] = useState('products')
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [message, setMessage] = useState(null)

    // Inventory Load State
    const [warehouses, setWarehouses] = useState([])
    const [selectedWarehouse, setSelectedWarehouse] = useState('')
    const [showWarning, setShowWarning] = useState(false)

    useEffect(() => {
        loadWarehouses()
    }, [])

    const loadWarehouses = async () => {
        try {
            const data = await api.getWarehouses()
            setWarehouses(data)
            if (data.length > 0) setSelectedWarehouse(data[0].id)
        } catch (error) {
            console.error("Error loading warehouses", error)
        }
    }

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0])
            setMessage(null)
            setShowWarning(false)
        }
    }

    const handleUpload = async () => {
        if (!file) return

        // Specific check for Initial Inventory
        if (uploadType === 'initial_stock' && !showWarning) {
            setShowWarning(true)
            return
        }

        setUploading(true)
        setMessage(null)

        const formData = new FormData()
        formData.append('file', file)
        if (uploadType === 'initial_stock') {
            formData.append('almacen_id', selectedWarehouse)
        }

        try {
            // Endpoint mapping
            const endpoints = {
                'products': 'upload/products',
                'providers': 'upload/providers',
                'purchases': 'upload/purchases',
                'initial_stock': 'upload/initial_stock'
            }

            const endpoint = endpoints[uploadType]
            const queryString = uploadType === 'initial_stock' ? `?almacen_id=${selectedWarehouse}` : ''

            const data = await api.uploadData(`${endpoint}${queryString}`, formData)

            setMessage({ type: 'success', text: data.msg || 'Carga exitosa' })
            setFile(null)
            setShowWarning(false)

        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setUploading(false)
        }
    }

    const handleDownloadTemplate = (type) => {
        window.open(`/api/template/${type}`, '_blank')
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-slate-800">Gestión de Datos</h2>
                <p className="text-slate-500">Carga masiva e inicialización del sistema</p>
            </div>

            <div className="flex space-x-2 border-b border-slate-200 overflow-x-auto">
                <button
                    onClick={() => setActiveTab('upload')}
                    className={`px-4 py-2 font-medium transition-colors whitespace-nowrap ${activeTab === 'upload' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    <Upload className="inline-block w-4 h-4 mr-2" />
                    Carga Masiva (Maestros)
                </button>
                <button
                    onClick={() => { setActiveTab('inventory'); setUploadType('initial_stock'); setMessage(null); setFile(null); }}
                    className={`px-4 py-2 font-medium transition-colors whitespace-nowrap ${activeTab === 'inventory' ? 'text-amber-600 border-b-2 border-amber-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    <Boxes className="inline-block w-4 h-4 mr-2" />
                    Inventario Inicial / Ajuste
                </button>
                <button
                    onClick={() => setActiveTab('templates')}
                    className={`px-4 py-2 font-medium transition-colors whitespace-nowrap ${activeTab === 'templates' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    <Download className="inline-block w-4 h-4 mr-2" />
                    Descargar Plantillas
                </button>
            </div>

            {/* TAB: Carga Masiva (Maestros) */}
            {activeTab === 'upload' && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 max-w-2xl">
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Tipo de Datos</label>
                            <select
                                className="w-full p-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                                value={uploadType}
                                onChange={(e) => setUploadType(e.target.value)}
                            >
                                <option value="products">📦 Productos (Maestro)</option>
                                <option value="providers">🏭 Proveedores</option>
                                <option value="purchases">🧾 Compras Históricas</option>
                            </select>
                        </div>

                        <UploadArea file={file} handleFileChange={handleFileChange} />
                        <MessageArea message={message} />

                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            className={`w-full py-3 rounded-lg font-bold text-white transition-all ${!file || uploading ? 'bg-slate-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl'}`}
                        >
                            {uploading ? 'Procesando...' : 'Subir y Procesar'}
                        </button>
                    </div>
                </div>
            )}

            {/* TAB: Inventario Inicial */}
            {activeTab === 'inventory' && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 max-w-2xl border-l-4 border-l-amber-500">
                    <div className="space-y-6">
                        <div className="bg-amber-50 p-4 rounded-lg flex items-start gap-3">
                            <AlertTriangle className="text-amber-600 shrink-0 mt-0.5" />
                            <div>
                                <h3 className="font-bold text-amber-800">Advertencia: Ajuste de Inventario</h3>
                                <p className="text-sm text-amber-700 mt-1">
                                    Esta opción permite cargar el stock inicial o realizar ajustes masivos.
                                    El stock ingresado <strong>sobrescribirá</strong> la cantidad actual en el almacén seleccionado.
                                    Asegúrese de usar la plantilla correcta.
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Seleccionar Sede / Almacén</label>
                                <select
                                    className="w-full p-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-amber-500"
                                    value={selectedWarehouse}
                                    onChange={(e) => setSelectedWarehouse(e.target.value)}
                                >
                                    {warehouses.map(w => (
                                        <option key={w.id} value={w.id}>{w.nombre} - {w.ubicacion}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex items-end">
                                <button
                                    onClick={() => handleDownloadTemplate('initial_stock')}
                                    className="w-full p-3 border border-slate-200 rounded-lg hover:bg-slate-50 text-slate-600 font-medium flex items-center justify-center gap-2"
                                >
                                    <Download size={18} /> Descargar Plantilla
                                </button>
                            </div>
                        </div>

                        <UploadArea file={file} handleFileChange={handleFileChange} />

                        {showWarning && (
                            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                                <h4 className="font-bold text-red-800 flex items-center gap-2">
                                    <AlertCircle size={18} /> Confirmación Requerida
                                </h4>
                                <p className="text-sm text-red-700 my-2">
                                    ¿Está seguro que desea actualizar el inventario del almacén seleccionado con los datos del archivo?
                                    Esta acción no se puede deshacer fácilmente.
                                </p>
                                <div className="flex gap-3 mt-3">
                                    <button
                                        onClick={handleUpload}
                                        className="bg-red-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-red-700"
                                    >
                                        Sí, Actualizar Inventario
                                    </button>
                                    <button
                                        onClick={() => setShowWarning(false)}
                                        className="text-slate-600 px-4 py-2 font-medium hover:text-slate-800"
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </div>
                        )}

                        <MessageArea message={message} />

                        {!showWarning && (
                            <button
                                onClick={handleUpload}
                                disabled={!file || uploading}
                                className={`w-full py-3 rounded-lg font-bold text-white transition-all ${!file || uploading ? 'bg-slate-300 cursor-not-allowed' : 'bg-amber-600 hover:bg-amber-700 shadow-lg hover:shadow-xl'}`}
                            >
                                {uploading ? 'Procesando...' : 'Validar y Cargar'}
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* TAB: Plantillas */}
            {activeTab === 'templates' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { id: 'products', title: 'Plantilla Productos', color: 'bg-blue-50 text-blue-700' },
                        { id: 'providers', title: 'Plantilla Proveedores', color: 'bg-purple-50 text-purple-700' },
                        { id: 'purchases', title: 'Plantilla Compras', color: 'bg-green-50 text-green-700' },
                        { id: 'initial_stock', title: 'Inventario Inicial', color: 'bg-amber-50 text-amber-700' }
                    ].map(t => (
                        <div key={t.id} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 text-center space-y-4">
                            <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center ${t.color}`}>
                                <FileText size={24} />
                            </div>
                            <h3 className="font-bold text-slate-800">{t.title}</h3>
                            <button
                                onClick={() => handleDownloadTemplate(t.id)}
                                className="w-full py-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-sm font-medium transition-colors flex items-center justify-center gap-2"
                            >
                                <Download size={16} /> Descargar CSV
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

function UploadArea({ file, handleFileChange }) {
    return (
        <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100 transition-colors">
            <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".csv,.xlsx"
                onChange={handleFileChange}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                <FileText className="w-12 h-12 text-slate-400" />
                <span className="text-slate-600 font-medium">
                    {file ? file.name : "Haz clic para seleccionar o arrastra un archivo"}
                </span>
                <span className="text-xs text-slate-400">Formatos soportados: CSV, Excel</span>
            </label>
        </div>
    )
}

function MessageArea({ message }) {
    if (!message) return null
    return (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
            {message.text}
        </div>
    )
}

