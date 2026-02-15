const API_URL = 'http://localhost:8000/api';

export const api = {
    // --- KPIs ---
    getKpis: async () => {
        const res = await fetch(`${API_URL}/kpis`);
        if (!res.ok) throw new Error('Failed to fetch KPIs');
        return res.json();
    },

    // --- Products ---
    getProducts: async () => {
        const res = await fetch(`${API_URL}/products`);
        if (!res.ok) throw new Error('Failed to fetch products');
        return res.json();
    },

    // --- Inventory ---
    getInventoryDetailed: async () => {
        const res = await fetch(`${API_URL}/inventory/detailed`);
        if (!res.ok) throw new Error('Failed to fetch inventory');
        return res.json();
    },

    getInventoryFifo: async (includeIgv = true) => {
        const res = await fetch(`${API_URL}/inventory/fifo?include_igv=${includeIgv}`);
        if (!res.ok) throw new Error('Failed to fetch FIFO inventory');
        return res.json();
    },

    // --- Transactions ---
    registerPurchase: async (data) => {
        const res = await fetch(`${API_URL}/purchase`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error registering purchase');
        return result;
    },

    registerMovement: async (data) => {
        const res = await fetch(`${API_URL}/movements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error registering movement');
        return result;
    },

    // --- Providers ---
    getProviders: async () => {
        const res = await fetch(`${API_URL}/providers`);
        if (!res.ok) throw new Error('Failed to fetch providers');
        return res.json();
    },

    // --- Orders ---
    getOrders: async () => {
        const res = await fetch(`${API_URL}/orders`);
        if (!res.ok) throw new Error('Failed to fetch orders');
        return res.json();
    },

    createOrder: async (data) => {
        const res = await fetch(`${API_URL}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error creating order');
        return result;
    },

    updateOrderStatus: async (id, status) => {
        const res = await fetch(`${API_URL}/orders/${id}/status?status=${status}`, {
            method: 'PUT'
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error updating order status');
        return result;
    },

    convertOrder: async (id, data) => {
        const res = await fetch(`${API_URL}/orders/${id}/convert?serie=${data.serie}&numero=${data.numero}&fecha=${data.fecha}`, {
            method: 'POST'
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error converting order');
        return result;
    },

    // --- Guides ---
    getGuides: async () => {
        const res = await fetch(`${API_URL}/guides`);
        if (!res.ok) throw new Error('Failed to fetch guides');
        return res.json();
    },

    // --- Warehouses ---
    getWarehouses: async () => {
        const res = await fetch(`${API_URL}/warehouses`);
        if (!res.ok) throw new Error('Failed to fetch warehouses');
        return res.json();
    }
};
