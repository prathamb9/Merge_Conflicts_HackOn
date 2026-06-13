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
  send: (message, history) => api.post('/chat', { message, history }),
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

export default api
