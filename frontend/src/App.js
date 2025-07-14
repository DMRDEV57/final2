import React, { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import AdminDashboard from './AdminDashboard';
import './App.css';

// Theme Context
const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('darkMode');
    return savedTheme ? JSON.parse(savedTheme) : false;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleDarkMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Service
const authService = {
  login: async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem('token', response.data.access_token);
    return response.data;
  },
  register: async (userData) => {
    const response = await axios.post(`${API}/auth/register`, userData);
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
  },
  getToken: () => {
    return localStorage.getItem('token');
  },
  getCurrentUser: async () => {
    const token = authService.getToken();
    if (!token) return null;
    
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      authService.logout();
      return null;
    }
  }
};

// API Service
const apiService = {
  // Services
  getServices: async () => {
    const response = await axios.get(`${API}/services`);
    return response.data;
  },
  
  // Orders
  createOrder: async (serviceId) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/orders`, 
      { service_id: serviceId },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
  createCombinedOrder: async (orderData) => {
    const token = authService.getToken();
    const formData = new FormData();
    formData.append('service_name', orderData.service_name);
    formData.append('price', orderData.price);
    formData.append('combined_services', orderData.combined_services);
    
    const response = await axios.post(`${API}/orders/combined`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  getUserOrders: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/orders`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  
  // Files
  uploadFile: async (orderId, file, notes = '') => {
    const token = authService.getToken();
    const formData = new FormData();
    formData.append('file', file);
    if (notes) formData.append('notes', notes);
    
    const response = await axios.post(`${API}/orders/${orderId}/upload`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  downloadFile: async (orderId, fileId) => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/orders/${orderId}/download/${fileId}`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob'
    });
    return response;
  },
  
  // Admin APIs
  adminGetUsers: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminCreateUser: async (userData) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/admin/users`, userData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdateUser: async (userId, userData) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/users/${userId}`, userData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminDeleteUser: async (userId) => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/admin/users/${userId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminGetServices: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/services`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminCreateService: async (serviceData) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/admin/services`, serviceData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdateService: async (serviceId, serviceData) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/services/${serviceId}`, serviceData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminDeleteService: async (serviceId) => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/admin/services/${serviceId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  
  // New Admin APIs for enhanced functionality
  adminGetOrdersByClient: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/orders/by-client`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdatePaymentStatus: async (orderId, paymentStatus) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/orders/${orderId}/payment`, 
      { payment_status: paymentStatus },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
  adminCancelOrder: async (orderId) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/orders/${orderId}/cancel`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdateUserStatus: async (userId, isActive) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/users/${userId}/status`, 
      { is_active: isActive },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
  getClientBalance: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/client/balance`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdateOrderStatus: async (orderId, statusData) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/orders/${orderId}/status`, statusData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminUpdateOrderPrice: async (orderId, priceData) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/orders/${orderId}/price`, priceData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminGetNotifications: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/notifications`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminMarkNotificationRead: async (notificationId) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/admin/notifications/${notificationId}/read`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  createSAVRequest: async (orderId) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/orders/${orderId}/sav-request`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminDownloadFile: async (orderId, fileId) => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/orders/${orderId}/download/${fileId}`, {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob'
    });
    return response;
  },
  adminUploadFile: async (orderId, file, versionType, notes = '') => {
    const token = authService.getToken();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('version_type', versionType);
    if (notes) formData.append('notes', notes);
    
    const response = await axios.post(`${API}/admin/orders/${orderId}/upload`, formData, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  adminDeleteNotification: async (notificationId) => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/admin/notifications/${notificationId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminDeleteAllNotifications: async () => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/admin/notifications`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminGetPendingOrders: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/orders/pending`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  
  // Chat APIs
  adminGetConversations: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/chat/conversations`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminGetChatMessages: async (userId) => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/admin/chat/${userId}/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  adminSendMessage: async (userId, message) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/admin/chat/${userId}/messages`, 
      { message },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
  clientGetMessages: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/client/chat/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  clientSendMessage: async (message) => {
    const token = authService.getToken();
    const response = await axios.post(`${API}/client/chat/messages`, 
      { message },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
  },
  clientGetUnreadCount: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/client/chat/unread-count`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  clientGetNotifications: async () => {
    const token = authService.getToken();
    const response = await axios.get(`${API}/client/notifications`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  clientMarkNotificationRead: async (notificationId) => {
    const token = authService.getToken();
    const response = await axios.put(`${API}/client/notifications/${notificationId}/read`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  clientDeleteNotification: async (notificationId) => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/client/notifications/${notificationId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  },
  clientDeleteAllNotifications: async () => {
    const token = authService.getToken();
    const response = await axios.delete(`${API}/client/notifications`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};

// Login Component
const Login = ({ onLogin, switchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(email, password);
      onLogin();
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          {/* Logo */}
          <div className="mx-auto h-24 w-auto flex items-center justify-center">
            <img 
              src="/logo.png" 
              alt="DMR DEVELOPPEMENT" 
              className="h-20 w-auto"
              onError={(e) => {
                // Fallback si l'image ne charge pas
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'block';
              }}
            />
            {/* Fallback si pas de logo */}
            <div className="bg-blue-600 text-white text-2xl font-bold px-6 py-3 rounded-lg" style={{display: 'none'}}>
              DMR
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Connexion à votre compte
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Connexion...' : 'Se connecter'}
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={switchToRegister}
              className="text-indigo-600 hover:text-indigo-500"
            >
              Pas encore de compte ? S'inscrire
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Register Component
const Register = ({ onRegister, switchToLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    country: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.register(formData);
      await authService.login(formData.email, formData.password);
      onRegister();
    } catch (error) {
      setError(error.response?.data?.detail || 'Erreur lors de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            DMR DEVELOPPEMENT
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Créez votre compte
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                Prénom
              </label>
              <input
                id="first_name"
                name="first_name"
                type="text"
                required
                value={formData.first_name}
                onChange={handleChange}
                className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              />
            </div>
            <div>
              <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                Nom
              </label>
              <input
                id="last_name"
                name="last_name"
                type="text"
                required
                value={formData.last_name}
                onChange={handleChange}
                className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                Téléphone <span className="text-red-500">*</span>
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                required
                value={formData.phone}
                onChange={handleChange}
                className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="ex: +33 1 23 45 67 89"
              />
            </div>
            <div>
              <label htmlFor="country" className="block text-sm font-medium text-gray-700">
                Pays <span className="text-red-500">*</span>
              </label>
              <select
                id="country"
                name="country"
                required
                value={formData.country}
                onChange={handleChange}
                className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
              >
                <option value="">Sélectionnez un pays</option>
                <option value="France">France</option>
                <option value="Belgique">Belgique</option>
                <option value="Suisse">Suisse</option>
                <option value="Canada">Canada</option>
                <option value="Luxembourg">Luxembourg</option>
                <option value="Allemagne">Allemagne</option>
                <option value="Espagne">Espagne</option>
                <option value="Italie">Italie</option>
                <option value="Portugal">Portugal</option>
                <option value="Autre">Autre</option>
              </select>
            </div>
          </div>
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={handleChange}
              className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={handleChange}
              className="mt-1 appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Inscription...' : 'S\'inscrire'}
            </button>
          </div>
          <div className="text-center">
            <button
              type="button"
              onClick={switchToLogin}
              className="text-indigo-600 hover:text-indigo-500"
            >
              Déjà un compte ? Se connecter
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Order Form Component (Vehicle info + File upload)
const OrderFormComponent = ({ user, selectedServices, onComplete, onBack, onLogout }) => {
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  
  // Vehicle identification fields
  const [vehicleData, setVehicleData] = useState({
    marque: '',
    modele: '',
    annee: '',
    immatriculation: '',
    puissance_din: '',
    marque_modele_calculateur: '',
    kilometrage: '',
    boite_vitesse: '',
    nom_client: '',
    fichier_modifie: false,
    commentaire: ''
  });

  const handleVehicleChange = (field, value) => {
    setVehicleData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const totalPrice = selectedServices.reduce((total, service) => total + service.price, 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation du fichier
    if (!file) {
      alert('Veuillez sélectionner un fichier');
      return;
    }
    
    // Validation de tous les champs obligatoires
    const requiredFields = [
      { field: 'marque', label: 'Marque' },
      { field: 'modele', label: 'Modèle' },
      { field: 'annee', label: 'Année' },
      { field: 'immatriculation', label: 'Immatriculation' },
      { field: 'puissance_din', label: 'Puissance DIN' },
      { field: 'marque_modele_calculateur', label: 'Marque/Modèle calculateur' },
      { field: 'kilometrage', label: 'Kilométrage' },
      { field: 'boite_vitesse', label: 'Boîte de vitesse' },
      { field: 'nom_client', label: 'Référence client' }
    ];
    
    for (const { field, label } of requiredFields) {
      if (!vehicleData[field] || vehicleData[field].trim() === '') {
        alert(`Veuillez remplir le champ: ${label}`);
        return;
      }
    }

    setLoading(true);
    try {
      // Create order first
      const serviceNames = selectedServices.map(s => s.name).join(' + ');
      
      const orderData = {
        service_name: serviceNames,
        price: totalPrice,
        combined_services: JSON.stringify(selectedServices.map(s => ({ id: s.id, name: s.name, price: s.price })))
      };
      
      console.log('Création de la commande combinée...', orderData);
      const orderResponse = await apiService.createCombinedOrder(orderData);
      console.log('Commande créée avec succès:', orderResponse);
      
      // Combine vehicle data with notes
      const completeNotes = `
IDENTITÉ DU VÉHICULE:
• Marque: ${vehicleData.marque}
• Modèle: ${vehicleData.modele}
• Année: ${vehicleData.annee}
• Immatriculation: ${vehicleData.immatriculation}
• Puissance (DIN): ${vehicleData.puissance_din}
• Calculateur: ${vehicleData.marque_modele_calculateur}
• Kilométrage: ${vehicleData.kilometrage}
• Boîte de vitesse: ${vehicleData.boite_vitesse}
• Référence client: ${vehicleData.nom_client}
• Fichier déjà modifié: ${vehicleData.fichier_modifie ? 'Oui' : 'Non'}

COMMENTAIRES:
${vehicleData.commentaire}
      `.trim();
      
      // Upload file to the created order
      console.log('Upload du fichier vers la commande...');
      await apiService.uploadFile(orderResponse.id, file, completeNotes);
      console.log('Fichier uploadé avec succès');
      
      console.log('Appel de onComplete()...');
      onComplete();
    } catch (error) {
      console.error('Erreur lors de la création de la commande:', error);
      alert('Erreur lors de la création de la commande: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={onBack}
                className="mr-4 text-blue-600 hover:text-blue-800"
              >
                ← Retour
              </button>
              <h1 className="text-xl font-bold text-gray-900">DMR DEVELOPPEMENT - Nouvelle commande</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Bonjour, {user.first_name}!</span>
              <button
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Add padding to account for fixed header */}
      <div className="pt-16"></div>

      <div className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Services summary */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">Récapitulatif de votre commande :</h3>
            <div className="space-y-2">
              {selectedServices.map((service) => (
                <div key={service.id} className="flex justify-between items-center p-2 bg-white rounded">
                  <span className="text-sm">{service.name}</span>
                  <span className="font-medium">{service.price}€</span>
                </div>
              ))}
              <div className="border-t pt-2 flex justify-between items-center">
                <span className="font-semibold">Total:</span>
                <span className="font-bold text-blue-900">{totalPrice}€</span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Vehicle Information */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Informations du véhicule</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Marque</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.marque}
                    onChange={(e) => handleVehicleChange('marque', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: BMW, Mercedes, Audi..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Modèle</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.modele}
                    onChange={(e) => handleVehicleChange('modele', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: 320d, A4, C220..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Année</label>
                  <input
                    type="number"
                    required
                    min="1990"
                    max="2025"
                    value={vehicleData.annee}
                    onChange={(e) => handleVehicleChange('annee', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: 2020"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Immatriculation <span className="text-red-500">*</span></label>
                  <input
                    type="text"
                    required
                    value={vehicleData.immatriculation}
                    onChange={(e) => handleVehicleChange('immatriculation', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: AB-123-CD"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Puissance (DIN)</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.puissance_din}
                    onChange={(e) => handleVehicleChange('puissance_din', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: 150 CV"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Calculateur (marque/modèle)</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.marque_modele_calculateur}
                    onChange={(e) => handleVehicleChange('marque_modele_calculateur', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: Bosch EDC17"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Kilométrage</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.kilometrage}
                    onChange={(e) => handleVehicleChange('kilometrage', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="ex: 45000 km"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Boîte de vitesse</label>
                  <select
                    required
                    value={vehicleData.boite_vitesse}
                    onChange={(e) => handleVehicleChange('boite_vitesse', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Choisir...</option>
                    <option value="Manuelle">Manuelle</option>
                    <option value="Automatique">Automatique</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Référence client</label>
                  <input
                    type="text"
                    required
                    value={vehicleData.nom_client}
                    onChange={(e) => handleVehicleChange('nom_client', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Nom complet du client"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">État du fichier</label>
                  <select
                    required
                    value={vehicleData.fichier_modifie ? 'modifie' : 'origine'}
                    onChange={(e) => handleVehicleChange('fichier_modifie', e.target.value === 'modifie')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="origine">Origine</option>
                    <option value="modifie">Fichier modifié</option>
                  </select>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Fichier de cartographie</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fichier de cartographie (.bin, .ori, .ecu, etc.)
                  </label>
                  <input
                    type="file"
                    required
                    accept=".bin,.ori,.ecu,.hex,.dat"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Commentaires/Instructions (optionnel)
                  </label>
                  <textarea
                    value={vehicleData.commentaire}
                    onChange={(e) => handleVehicleChange('commentaire', e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ajoutez ici vos commentaires, instructions spécifiques ou toute information utile..."
                  />
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={loading}
                className="bg-green-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Traitement en cours...' : '🚀 Créer la commande et envoyer le fichier'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Client Dashboard Component
const ClientDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('services');
  const [services, setServices] = useState([]);
  const [orders, setOrders] = useState([]);
  const [selectedServices, setSelectedServices] = useState([]);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [balance, setBalance] = useState(0);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [chatUnreadCount, setChatUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [notificationUnreadCount, setNotificationUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [previousNotificationCount, setPreviousNotificationCount] = useState(0);
  const [showSAVConfirmation, setShowSAVConfirmation] = useState(false);
  const [expandedOrders, setExpandedOrders] = useState({});
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadServices();
    loadOrders();
    loadBalance();
    loadChatMessages();
    loadChatUnreadCount();
    loadNotifications();
    
    // Poll for new messages and notifications every 30 seconds
    const interval = setInterval(() => {
      if (activeTab === 'chat') {
        loadChatMessages();
      }
      loadChatUnreadCount();
      loadNotifications();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      const data = await apiService.clientGetNotifications();
      setNotifications(data);
      const currentUnreadCount = data.filter(n => !n.is_read).length;
      
      // Play sound if new notification
      if (currentUnreadCount > previousNotificationCount && previousNotificationCount !== 0) {
        playNotificationSound();
      }
      
      setPreviousNotificationCount(currentUnreadCount);
      setNotificationUnreadCount(currentUnreadCount);
    } catch (error) {
      console.error('Erreur lors du chargement des notifications:', error);
    }
  };

  const playNotificationSound = () => {
    // Create a simple notification sound
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'sine';
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      try {
        await apiService.clientMarkNotificationRead(notification.id);
        await loadNotifications();
      } catch (error) {
        console.error('Erreur lors du marquage de la notification:', error);
      }
    }
    setShowNotifications(false);
    // Navigate to relevant section
    if (notification.type === 'new_file' || notification.type === 'sav_request') {
      setActiveTab('orders');
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await apiService.clientDeleteNotification(notificationId);
      await loadNotifications();
    } catch (error) {
      console.error('Erreur lors de la suppression de la notification:', error);
    }
  };

  const handleDeleteAllNotifications = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer toutes les notifications ?')) {
      try {
        await apiService.clientDeleteAllNotifications();
        await loadNotifications();
      } catch (error) {
        console.error('Erreur lors de la suppression des notifications:', error);
      }
    }
  };

  const toggleOrderExpansion = (orderId) => {
    setExpandedOrders(prev => ({
      ...prev,
      [orderId]: !prev[orderId]
    }));
  };

  // Close notifications when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showNotifications && !event.target.closest('.notifications-panel') && !event.target.closest('.notifications-bell')) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotifications]);

  const loadChatMessages = async () => {
    try {
      const data = await apiService.clientGetMessages();
      setMessages(data);
    } catch (error) {
      console.error('Erreur lors du chargement des messages:', error);
    }
  };

  const loadChatUnreadCount = async () => {
    try {
      const data = await apiService.clientGetUnreadCount();
      setChatUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Erreur lors du chargement du nombre de messages non lus:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    
    try {
      await apiService.clientSendMessage(newMessage);
      setNewMessage('');
      await loadChatMessages();
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
    }
  };

  const loadBalance = async () => {
    try {
      const balanceData = await apiService.getClientBalance();
      setBalance(balanceData.balance);
    } catch (error) {
      console.error('Erreur lors du chargement du solde:', error);
    }
  };

  const loadServices = async () => {
    try {
      const servicesData = await apiService.getServices();
      setServices(servicesData.filter(service => service.is_active));
    } catch (error) {
      console.error('Erreur lors du chargement des services:', error);
    }
  };

  const loadOrders = async () => {
    try {
      console.log('Chargement des commandes...');
      const ordersData = await apiService.getUserOrders();
      console.log('Commandes reçues:', ordersData);
      setOrders(ordersData);
    } catch (error) {
      console.error('Erreur lors du chargement des commandes:', error);
    }
  };

  const addServiceToCart = (service) => {
    if (!selectedServices.find(s => s.id === service.id)) {
      setSelectedServices([...selectedServices, service]);
    }
  };

  const removeServiceFromCart = (serviceId) => {
    setSelectedServices(selectedServices.filter(s => s.id !== serviceId));
  };

  const getTotalPrice = () => {
    return selectedServices.reduce((total, service) => total + service.price, 0);
  };

  const handleSingleServiceOrder = (service) => {
    setSelectedServices([service]);
    setShowOrderForm(true);
  };

  const proceedToOrderForm = () => {
    if (selectedServices.length === 0) return;
    setShowOrderForm(true);
  };

  const handleOrderComplete = async () => {
    try {
      console.log('Commande terminée, rechargement des commandes...');
      await loadOrders();
      await loadBalance(); // Reload balance after order completion
      setSelectedServices([]);
      setShowOrderForm(false);
      setActiveTab('orders');
      console.log('Redirection vers onglet commandes effectuée');
    } catch (error) {
      console.error('Erreur lors de la finalisation de la commande:', error);
    }
  };

  const handleDownload = async (orderId, fileId, filename) => {
    try {
      console.log(`Downloading file: ${filename} (Order: ${orderId}, File: ${fileId})`);
      
      // Try programmatic download first
      const response = await apiService.downloadFile(orderId, fileId);
      
      // Check if response is successful
      if (response.status === 200) {
        // Create blob from response data
        const blob = new Blob([response.data], { 
          type: response.headers['content-type'] || 'application/octet-stream' 
        });
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || `cartography-${orderId}.bin`;
        
        // Force download
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        
        // Cleanup
        setTimeout(() => {
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        }, 100);
        
        console.log(`✅ Download completed: ${filename}`);
      } else {
        console.error(`❌ Download failed with status: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ Erreur lors du téléchargement:', error);
      
      // Fallback: try direct link download
      if (error.response?.status === 404) {
        console.log('🔄 Trying fallback direct download...');
        try {
          const token = authService.getToken();
          const fallbackUrl = `${API}/orders/${orderId}/download/${fileId}?token=${token}`;
          
          const link = document.createElement('a');
          link.href = fallbackUrl;
          link.download = filename || `cartography-${orderId}.bin`;
          link.target = '_blank';
          link.style.display = 'none';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          console.log(`✅ Fallback download attempted: ${filename}`);
        } catch (fallbackError) {
          console.error('❌ Fallback download failed:', fallbackError);
        }
      }
    }
  };

  const handleSAVRequest = async (orderId) => {
    try {
      await apiService.createSAVRequest(orderId);
      // Show confirmation message
      setShowSAVConfirmation(true);
      setTimeout(() => setShowSAVConfirmation(false), 4000);
      await loadOrders(); // Reload to see any changes
    } catch (error) {
      console.error('Erreur lors de la demande de SAV:', error);
      alert('Erreur lors de l\'envoi de la demande de SAV');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'En attente';
      case 'processing': return 'En cours';
      case 'completed': return 'Terminé';
      case 'cancelled': return 'Annulé';
      default: return status;
    }
  };

  const getVersionText = (versionType) => {
    switch (versionType) {
      case 'original': return 'Fichier original';
      case 'v1': return 'Version 1';
      case 'v2': return 'Version 2';
      case 'v3': return 'Version 3';
      case 'SAV': return 'SAV';
      default: return versionType;
    }
  };

  const truncateFilename = (filename, maxLength = 25) => {
    if (filename.length <= maxLength) return filename;
    return filename.substring(0, maxLength) + '...';
  };

  // Filter orders by immatriculation
  const filteredOrders = orders.filter(order => 
    !searchTerm || (order.immatriculation && order.immatriculation.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (showOrderForm) {
    return (
      <OrderFormComponent
        user={user}
        selectedServices={selectedServices}
        onComplete={handleOrderComplete}
        onBack={() => setShowOrderForm(false)}
        onLogout={onLogout}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">DMR DEVELOPPEMENT</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* Notifications Bell */}
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative text-gray-700 hover:text-gray-900 notifications-bell"
              >
                🔔
                {notificationUnreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {notificationUnreadCount}
                  </span>
                )}
              </button>
              
              {selectedServices.length > 0 && (
                <button
                  onClick={proceedToOrderForm}
                  className="relative bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  🛒 Commander maintenant ({selectedServices.length})
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {selectedServices.length}
                  </span>
                </button>
              )}
              <span className="text-gray-700">Bonjour, {user.first_name}!</span>
              <span className="text-red-600 font-semibold">
                Solde dû: {balance}€
              </span>
              <button
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Add padding to account for fixed header */}
      <div className="pt-16"></div>

      {/* SAV Confirmation Message */}
      {showSAVConfirmation && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg max-w-md text-center">
          ✅ Votre demande de SAV à été envoyée avec succès. Merci de nous donner plus de précisions dans le chat de l'application.
        </div>
      )}

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed top-16 right-4 w-80 bg-white shadow-lg rounded-lg border border-gray-200 z-40 max-h-96 overflow-y-auto notifications-panel">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="font-semibold text-gray-900">Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={handleDeleteAllNotifications}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Tout supprimer
              </button>
            )}
          </div>
          <div className="divide-y divide-gray-200">
            {notifications.length > 0 ? (
              notifications.slice(0, 10).map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-gray-50 cursor-pointer ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{notification.title}</div>
                      <div className="text-sm text-gray-600">{notification.message}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(notification.created_at).toLocaleString()}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteNotification(notification.id);
                      }}
                      className="text-red-600 hover:text-red-800 text-xs ml-2"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 text-gray-500 text-center">Aucune notification</div>
            )}
          </div>
        </div>
      )}

      {/* Shopping Cart */}
      {selectedServices.length > 0 && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="font-medium text-blue-900">Panier:</h3>
                <div className="flex space-x-2">
                  {selectedServices.map((service) => (
                    <div key={service.id} className="bg-white rounded-md px-3 py-1 text-sm flex items-center">
                      <span>{service.name}</span>
                      <button
                        onClick={() => removeServiceFromCart(service.id)}
                        className="ml-2 text-red-600 hover:text-red-800"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              <div className="text-blue-900 font-semibold">
                Total: {getTotalPrice()}€
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('services')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'services'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Services
            </button>
            <button
              onClick={() => setActiveTab('orders')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'orders'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Mes commandes
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`py-2 px-1 border-b-2 font-medium text-sm relative ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chat
              {chatUnreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {chatUnreadCount}
                </span>
              )}
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'services' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Services disponibles</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((service) => (
                <div key={service.id} className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{service.name}</h3>
                  <p className="text-gray-600 mb-4">{service.description}</p>
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between">
                      <span>💰 Prix :</span>
                      <span className="font-medium">{service.price}€</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={() => addServiceToCart(service)}
                      disabled={selectedServices.find(s => s.id === service.id)}
                      className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
                        selectedServices.find(s => s.id === service.id)
                          ? 'bg-green-600 text-white'
                          : 'bg-blue-600 text-white hover:bg-blue-700'
                      }`}
                    >
                      {selectedServices.find(s => s.id === service.id) ? '✓ Ajouté' : '+ Ajouter'}
                    </button>
                    <button
                      onClick={() => handleSingleServiceOrder(service)}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
                    >
                      Commander
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div>
            {/* Search bar */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Rechercher par immatriculation..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <svg
                  className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
            
            {filteredOrders.length > 0 ? (
              <div className="space-y-6">
                {filteredOrders.map((order) => (
                  <div key={order.id} className="bg-white rounded-lg shadow-md">
                    
                    {/* Order Header - Always visible */}
                    <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                      <div className="flex justify-between items-center">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {order.immatriculation ? `${order.immatriculation} - ${order.service_name}` : order.service_name}
                          </h3>
                          <p className="text-xs text-gray-500">
                            Commande #{order.order_number || order.id.slice(0, 8).toUpperCase()}
                          </p>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span className="font-medium">Commande du :</span>
                            <span>{new Date(order.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
                              {getStatusText(order.status)}
                            </span>
                            <div className="text-lg font-bold text-gray-900 mt-1">{order.price}€</div>
                            
                            {/* SAV Request Button for completed orders */}
                            {order.status === 'completed' && (
                              <button
                                onClick={() => handleSAVRequest(order.id)}
                                className="mt-2 bg-orange-600 text-white px-3 py-1 rounded text-sm hover:bg-orange-700"
                              >
                                Demande SAV
                              </button>
                            )}
                          </div>
                          <button
                            onClick={() => toggleOrderExpansion(order.id)}
                            className="flex items-center space-x-2 text-blue-600 hover:text-blue-800"
                          >
                            <span>{expandedOrders[order.id] ? 'Réduire' : 'Voir détails'}</span>
                            <svg 
                              className={`w-4 h-4 transform transition-transform ${expandedOrders[order.id] ? 'rotate-180' : ''}`}
                              fill="none" 
                              viewBox="0 0 24 24" 
                              stroke="currentColor"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Order Details - Expandable */}
                    {expandedOrders[order.id] && (
                      <div className="p-4">
                        {order.files && order.files.length > 0 && (
                          <div className="mt-4 p-4 bg-gray-50 rounded-md">
                            <h4 className="font-medium text-gray-900 mb-2">📁 Fichiers de la commande</h4>
                            <div className="space-y-2">
                              {order.files.map((file) => (
                                <div key={file.id} className="flex items-center justify-between p-2 bg-white rounded border">
                                  <div className="flex items-center space-x-3">
                                    <span className="text-sm font-medium text-gray-900">
                                      {getVersionText(file.version_type)}
                                    </span>
                                    <span className="text-sm text-gray-500">
                                      {truncateFilename(file.filename)}
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <button
                                      onClick={() => handleDownload(order.id, file.file_id, file.filename)}
                                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                    >
                                      Télécharger
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-gray-500 mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-4m-4 0H6m0 0h4m4 0h4" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900">
                  {searchTerm ? 'Aucune commande trouvée' : 'Aucune commande'}
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm ? 'Essayez une autre recherche' : 'Vous n\'avez pas encore passé de commande'}
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <div>
            <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{height: '600px'}}>
              <div className="flex flex-col h-full">
                {/* Chat Header */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="font-semibold text-gray-900">Support DMR DEVELOPPEMENT</div>
                  <div className="text-sm text-gray-600">Posez vos questions, nous vous répondrons rapidement</div>
                </div>
                
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length > 0 ? (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.sender_role === 'client' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                            message.sender_role === 'client'
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-900'
                          }`}
                        >
                          <div>{message.message}</div>
                          <div className={`text-xs mt-1 ${
                            message.sender_role === 'client' ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {new Date(message.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <div className="text-6xl mb-4">💬</div>
                        <div className="text-lg font-medium">Aucun message pour le moment</div>
                        <div className="text-sm">Commencez une conversation avec notre équipe</div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Message Input */}
                <div className="p-4 border-t border-gray-200">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      placeholder="Tapez votre message..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!newMessage.trim()}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                      Envoyer
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLogin, setShowLogin] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Erreur lors de la vérification du statut d\'authentification:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    await checkAuthStatus();
  };

  const handleLogout = () => {
    authService.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return showLogin ? (
      <Login onLogin={handleLogin} switchToRegister={() => setShowLogin(false)} />
    ) : (
      <Register onRegister={handleLogin} switchToLogin={() => setShowLogin(true)} />
    );
  }

  return user.role === 'admin' ? (
    <AdminDashboard user={user} onLogout={handleLogout} apiService={apiService} />
  ) : (
    <ClientDashboard user={user} onLogout={handleLogout} />
  );
};

export default App;