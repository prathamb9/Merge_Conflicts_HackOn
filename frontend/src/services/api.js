import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for local dev
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token from localStorage to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally — clear token and redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

export const chatAPI = {
  send: (message, history, lastRecommendedIds = [], checkout = null) =>
    api.post('/chat', {
      message,
      history,
      last_recommended_ids: lastRecommendedIds,
      checkout,
    }),
}

export const productsAPI = {
  list: (params) => api.get('/products', { params }),
  categories: () => api.get('/products/categories'),
  departments: () => api.get('/products/departments'),
  get: (id) => api.get(`/products/${id}`),
}

export const cartAPI = {
  get: () => api.get('/cart'),
  add: (product_id, quantity = 1) => api.post('/cart/add', { product_id, quantity }),
  update: (product_id, quantity) => api.put(`/cart/update/${product_id}`, { quantity }),
  remove: (product_id) => api.delete(`/cart/remove/${product_id}`),
  clear: () => api.delete('/cart/clear'),
  checkout: () => api.post('/cart/checkout'),
}

export const profileAPI = {
  get: () => api.get('/profile'),
  update: (data) => api.put('/profile', data),
}

export const recipeAPI = {
  parse: (recipe, servings = 2) => api.post('/recipe/parse', { recipe, servings }),
}

export const addressAPI = {
  list: () => api.get('/addresses'),
  create: (data) => api.post('/addresses', data),
  setDefault: (id) => api.put(`/addresses/${id}/default`),
  remove: (id) => api.delete(`/addresses/${id}`),
}

export const paymentAPI = {
  list: () => api.get('/payment-methods'),
  create: (data) => api.post('/payment-methods', data),
  setDefault: (id) => api.put(`/payment-methods/${id}/default`),
  remove: (id) => api.delete(`/payment-methods/${id}`),
}

export const ordersAPI = {
  list: () => api.get('/orders'),
  get: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  pay: (id, paymentMethodId = '') =>
    api.post(`/orders/${id}/pay`, { payment_method_id: paymentMethodId }),
}

export const bargainAPI = {
  haggle: (productIds, offer) =>
    api.post('/bargain', { product_ids: productIds, offer }),
}

export const pairingAPI = {
  get: (productIds, filters = {}) =>
    api.post('/pairing', { product_ids: productIds, ...filters }),
}

export const mealPlanAPI = {
  generate: (goal, days = 7, servings = 2) =>
    api.post('/meal-plan', { goal, days, servings }),
  consolidate: (ingredients, servings = 2) =>
    api.post('/meal-plan/consolidate', { ingredients, servings }),
}

export const groupAPI = {
  create: (name) => api.post('/group/create', { name }),
  join: (code) => api.post(`/group/${code}/join`),
  get: (code) => api.get(`/group/${code}`),
  addItem: (code, productId) => api.post(`/group/${code}/items`, { product_id: productId }),
  vote: (code, itemId) => api.post(`/group/${code}/items/${itemId}/vote`),
  removeItem: (code, itemId) => api.delete(`/group/${code}/items/${itemId}`),
  checkoutToCart: (code) => api.post(`/group/${code}/checkout-to-cart`),
}

export default api
