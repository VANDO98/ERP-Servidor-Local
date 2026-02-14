import React, { useState, useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'

export default function ProductSearch({ products, value, onChange, required = false }) {
    const [searchTerm, setSearchTerm] = useState('')
    const [isOpen, setIsOpen] = useState(false)
    const wrapperRef = useRef(null)

    // Handle initial value
    useEffect(() => {
        if (value) {
            const prod = products.find(p => p.id == value)
            if (prod) {
                setSearchTerm(prod.nombre)
            }
        } else {
            setSearchTerm('')
        }
    }, [value, products])

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false)
                // If text doesn't match a selection, validation might fail upstream or we reset?
                // For now, visual only. Upstream keeps 'value' (ID).
                // If user typed garbage and clicked away, we might want to revert logic?
                // Let's rely on 'value' prop being the truth.
                if (value) {
                    const prod = products.find(p => p.id == value)
                    if (prod) setSearchTerm(prod.nombre)
                } else {
                    setSearchTerm('')
                }
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [wrapperRef, value, products])

    const filtered = products.filter(p =>
        p.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.codigo_sku?.toLowerCase().includes(searchTerm.toLowerCase())
    ).slice(0, 10) // Limit to 10 suggestions

    const handleSelect = (pid) => {
        const prod = products.find(p => p.id === pid)
        setSearchTerm(prod.nombre)
        setIsOpen(false)
        onChange(pid)
    }

    const handleChange = (e) => {
        setSearchTerm(e.target.value)
        setIsOpen(true)
        if (e.target.value === '') {
            onChange('') // Clear value
        }
    }

    return (
        <div className="relative w-full" ref={wrapperRef}>
            <div className="relative">
                <input
                    type="text"
                    className="w-full p-2 pl-8 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    placeholder="Buscar producto..."
                    value={searchTerm}
                    onChange={handleChange}
                    onFocus={() => setIsOpen(true)}
                    required={required && !value}
                />
                <Search size={16} className="absolute left-2.5 top-3 text-slate-400" />
                {value && (
                    <button
                        type="button"
                        onClick={() => { onChange(''); setSearchTerm(''); setIsOpen(true) }}
                        className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                        <X size={16} />
                    </button>
                )}
            </div>

            {isOpen && filtered.length > 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {filtered.map(p => (
                        <div
                            key={p.id}
                            onClick={() => handleSelect(p.id)}
                            className="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-slate-50 last:border-none"
                        >
                            <div className="text-sm font-medium text-slate-700">{p.nombre}</div>
                            <div className="text-xs text-slate-500 flex justify-between">
                                <span>SKU: {p.codigo_sku || '-'}</span>
                                <span>Stock: {p.stock_actual}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {isOpen && searchTerm && filtered.length === 0 && (
                <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-sm text-slate-500 text-center">
                    No se encontraron productos
                </div>
            )}
        </div>
    )
}
