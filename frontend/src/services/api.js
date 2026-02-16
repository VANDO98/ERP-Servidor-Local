


const API_URL = 'http://localhost:8000/api';

const getHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
};

export const api = {
    // --- KPIs ---
    getKpis: async () => {
        const res = await fetch(`${API_URL}/kpis`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch KPIs');
        return res.json();
    },

    // --- Products ---
    getProducts: async () => {
        const res = await fetch(`${API_URL}/products`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch products');
        return res.json();
    },

    // --- Inventory ---
    getInventoryDetailed: async () => {
        const res = await fetch(`${API_URL}/inventory/detailed`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch inventory');
        return res.json();
    },


    getInventoryFifo: async (includeIgv = true) => {
        const res = await fetch(`${API_URL}/inventory/fifo?include_igv=${includeIgv}`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch FIFO inventory');
        return res.json();
    },

    getKardex: async (type, params) => {
        let url = `${API_URL}/inventory/kardex`;
        const qs = `?start_date=${params.startDate}&end_date=${params.endDate}`;

        if (type === 'general') {
            url += `/general${qs}`;
        } else if (params.productId) {
            url += `/${params.productId}${qs}`;
        } else {
            return [];
        }

        const res = await fetch(url, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch kardex');
        return res.json();
    },


    // --- Transactions ---
    registerPurchase: async (data) => {
        const res = await fetch(`${API_URL}/purchase`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error registering purchase');
        return result;
    },

    getPurchasesSummary: async () => {
        const res = await fetch(`${API_URL}/purchases/summary`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch purchases summary');
        return res.json();
    },

    getPurchasesDetailed: async () => {
        const res = await fetch(`${API_URL}/purchases/detailed`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch purchases detailed');
        return res.json();
    },

    registerMovement: async (data) => {
        const res = await fetch(`${API_URL}/movements`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error registering movement');
        return result;
    },

    // --- Providers ---
    getProviders: async () => {
        const res = await fetch(`${API_URL}/providers`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch providers');
        return res.json();
    },

    // --- Orders ---
    getOrders: async () => {
        const res = await fetch(`${API_URL}/orders`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch orders');
        return res.json();
    },

    getOrder: async (id) => {
        const res = await fetch(`${API_URL}/orders/${id}`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch order');
        return res.json();
    },

    getPendingOrders: async () => {
        const res = await fetch(`${API_URL}/orders/pending`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch pending orders');
        return res.json();
    },

    getOrderBalance: async (id) => {
        const res = await fetch(`${API_URL}/orders/${id}/balance`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch order balance');
        return res.json();
    },

    createOrder: async (data) => {
        const res = await fetch(`${API_URL}/orders`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error creating order');
        return result;
    },

    updateOrder: async (id, data) => {
        const res = await fetch(`${API_URL}/orders/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error updating order');
        return result;
    },

    updateOrderStatus: async (id, status) => {
        const res = await fetch(`${API_URL}/orders/${id}/status?status=${status}`, {
            method: 'PUT',
            headers: getHeaders()
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error updating order status');
        return result;
    },

    convertOrder: async (id, data) => {
        const res = await fetch(`${API_URL}/orders/${id}/convert?serie=${data.serie}&numero=${data.numero}&fecha=${data.fecha}`, {
            method: 'POST',
            headers: getHeaders()
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error converting order');
        return result;
    },

    // --- Guides ---
    getGuides: async () => {
        const res = await fetch(`${API_URL}/guides`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch guides');
        return res.json();
    },

    getGuide: async (id) => {
        const res = await fetch(`${API_URL}/guides/${id}`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch guide');
        return res.json();
    },

    createGuide: async (data) => {
        const res = await fetch(`${API_URL}/guides`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify(data),
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error creating guide');
        return result;
    },

    uploadData: async (endpoint, formData) => {
        // Uploads usually need multipart/form-data, which fetch handles automatically if we pass FormData body
        // and DO NOT set Content-Type header (it sets it with boundary).
        // But we DO need Authorization if we secure it later.
        const token = localStorage.getItem('token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch(`${API_URL}/${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: formData,
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || 'Error uploading data');
        return result;
    },

    // --- Warehouses ---
    getWarehouses: async () => {
        const res = await fetch(`${API_URL}/warehouses`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch warehouses');
        return res.json();
    },

    // --- Dashboard ---
    getDashboardMetrics: async (startDate, endDate) => {
        const res = await fetch(`${API_URL}/dashboard/complete?start_date=${startDate}&end_date=${endDate}`, { headers: getHeaders() });
        if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
        return res.json();
    }
};
