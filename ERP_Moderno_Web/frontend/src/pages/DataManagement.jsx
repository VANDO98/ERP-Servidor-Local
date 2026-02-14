import React, { useState } from 'react'
import { Upload, Download, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '../services/api'

export default function DataManagement() {
    const [activeTab, setActiveTab] = useState('upload')
    const [uploadType, setUploadType] = useState('products')
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [message, setMessage] = useState(null)

    const handleFileChange = (e) => {
        if (e.target.files) {
            setFile(e.target.files[0])
            setMessage(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setMessage(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            // Endpoint mapping
            const endpoints = {
                'products': 'upload/products',
                'providers': 'upload/providers',
                'purchases': 'upload/purchases'
            }

            const endpoint = endpoints[uploadType]
            const res = await fetch(`http://localhost:8000/api/${endpoint}`, {
                method: 'POST',
                body: formData
            })

            const data = await res.json()
            if (res.ok) {
                setMessage({ type: 'success', text: data.msg || 'Carga exitosa' })
                setFile(null)
            } else {
                setMessage({ type: 'error', text: data.detail || 'Error en la carga' })
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Error de conexión: ' + error.message })
        } finally {
            setUploading(false)
        }
    }

    const handleDownloadTemplate = (type) => {
        window.open(`http://localhost:8000/api/template/${type}`, '_blank')
    }

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold text-slate-800">Carga Masiva de Datos</h2>
                <p className="text-slate-500">Importación de registros y plantillas</p>
            </div>

            <div className="flex space-x-2 border-b border-slate-200">
                <button
                    onClick={() => setActiveTab('upload')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'upload' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    <Upload className="inline-block w-4 h-4 mr-2" />
                    Importar Datos
                </button>
                <button
                    onClick={() => setActiveTab('templates')}
                    className={`px-4 py-2 font-medium transition-colors ${activeTab === 'templates' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:text-slate-900'}`}
                >
                    <Download className="inline-block w-4 h-4 mr-2" />
                    Descargar Plantillas
                </button>
            </div>

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
                                <option value="products">📦 Productos (Inventario Inicial)</option>
                                <option value="providers">🏭 Proveedores</option>
                                <option value="purchases">🧾 Compras Históricas</option>
                            </select>
                        </div>

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

                        {message && (
                            <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                                {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
                                {message.text}
                            </div>
                        )}

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

            {activeTab === 'templates' && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { id: 'products', title: 'Plantilla Productos', color: 'bg-blue-50 text-blue-700' },
                        { id: 'providers', title: 'Plantilla Proveedores', color: 'bg-purple-50 text-purple-700' },
                        { id: 'purchases', title: 'Plantilla Compras', color: 'bg-green-50 text-green-700' }
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
