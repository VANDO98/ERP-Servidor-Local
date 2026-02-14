import React from 'react'
import { Download } from 'lucide-react'

export default function ExportButton({ data, filename = 'export', label = 'Exportar Excel' }) {
    const handleDownload = () => {
        if (!data || data.length === 0) {
            alert('No hay datos para exportar')
            return
        }

        // Get headers from first object
        const headers = Object.keys(data[0])

        // Create CSV content with BOM for Excel UTF-8
        const bom = '\uFEFF'
        const csvContent = [
            headers.join(';'),
            ...data.map(row => headers.map(fieldName => {
                let val = row[fieldName]
                // Handle potential null/undefined
                if (val === null || val === undefined) val = ''
                // Escape semicolons or newlines
                const str = String(val).replace(/"/g, '""')
                return `"${str}"`
            }).join(';'))
        ].join('\r\n')

        const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `${filename}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }

    return (
        <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm"
            title="Descargar CSV compatible con Excel"
        >
            <Download size={16} />
            {label}
        </button>
    )
}
