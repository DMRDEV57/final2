import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

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
  }
};

// Components
const Login = ({ onLogin, switchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await authService.login(email, password);
      onLogin();
    } catch (error) {
      setError('Email ou mot de passe incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">DMR Développement</h1>
          <p className="text-gray-600 mt-2">Service de cartographie moteur</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          {error && <div className="text-red-600 text-sm">{error}</div>}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <button
            onClick={switchToRegister}
            className="text-blue-600 hover:text-blue-500"
          >
            Pas encore de compte ? S'inscrire
          </button>
        </div>
        
        <div className="mt-4 text-center text-sm text-gray-600">
          <p>Compte admin de test: admin@cartomapping.com / admin123</p>
        </div>
      </div>
    </div>
  );
};

const Register = ({ onRegister, switchToLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    company: ''
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
    setLoading(true);
    setError('');
    
    try {
      await authService.register(formData);
      onRegister();
    } catch (error) {
      setError('Erreur lors de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Inscription</h1>
          <p className="text-gray-600 mt-2">Créer votre compte DMR Développement</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Prénom</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nom</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Téléphone</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Société</label>
            <input
              type="text"
              name="company"
              value={formData.company}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          {error && <div className="text-red-600 text-sm">{error}</div>}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Inscription...' : 'S\'inscrire'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <button
            onClick={switchToLogin}
            className="text-blue-600 hover:text-blue-500"
          >
            Déjà un compte ? Se connecter
          </button>
        </div>
      </div>
    </div>
  );
};

const ClientDashboard = ({ user, onLogout }) => {
  const [services, setServices] = useState([]);
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('services');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadServices();
    loadOrders();
  }, []);

  const loadServices = async () => {
    try {
      const servicesData = await apiService.getServices();
      setServices(servicesData);
    } catch (error) {
      console.error('Erreur lors du chargement des services:', error);
    }
  };

  const loadOrders = async () => {
    try {
      const ordersData = await apiService.getUserOrders();
      setOrders(ordersData);
    } catch (error) {
      console.error('Erreur lors du chargement des commandes:', error);
    }
  };

  const handleOrderService = async (serviceId) => {
    setLoading(true);
    try {
      console.log('Commande service avec ID:', serviceId); // Debug
      const orderResponse = await apiService.createOrder(serviceId);
      console.log('Réponse commande:', orderResponse); // Debug
      await loadOrders();
      setActiveTab('orders');
    } catch (error) {
      console.error('Erreur lors de la commande:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (orderId, file, notes) => {
    if (!file) return;
    
    try {
      await apiService.uploadFile(orderId, file, notes);
      await loadOrders();
    } catch (error) {
      console.error('Erreur lors de l\'upload:', error);
    }
  };

  const handleDownload = async (orderId, fileId, filename) => {
    try {
      const response = await apiService.downloadFile(orderId, fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `cartography-${orderId}.bin`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'delivered': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'En attente';
      case 'processing': return 'En cours';
      case 'completed': return 'Terminé';
      case 'delivered': return 'Livré';
      default: return status;
    }
  };

  const getVersionText = (versionType) => {
    switch (versionType) {
      case 'original': return 'Fichier original';
      case 'v1': return 'Version 1';
      case 'v2': return 'Version 2';
      case 'v3': return 'Version 3';
      case 'sav': return 'SAV';
      default: return versionType;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">DMR Développement</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Bonjour, {user.first_name}!</span>
              <button
                onClick={onLogout}
                className="text-gray-700 hover:text-gray-900"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
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
            </nav>
          </div>

          {activeTab === 'services' && (
            <div className="mt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Services disponibles</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services && services.map((service) => (
                  <div key={service.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                      <span className="text-2xl font-bold text-blue-600">{service.price}€</span>
                    </div>
                    <p className="text-gray-600 mb-4">{service.description}</p>
                    
                    <div className="space-y-2 mb-4 text-sm text-gray-500">
                      <div className="flex justify-between">
                        <span>⏱️ Délai de livraison :</span>
                        <span className="font-medium">24-48h</span>
                      </div>
                      <div className="flex justify-between">
                        <span>📁 Formats acceptés :</span>
                        <span className="font-medium">.bin, .hex, .map</span>
                      </div>
                      <div className="flex justify-between">
                        <span>📏 Taille max :</span>
                        <span className="font-medium">10 MB</span>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleOrderService(service.id)}
                      disabled={loading}
                      className="w-full bg-blue-600 text-white px-4 py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
                    >
                      {loading ? 'Commande en cours...' : 'Commander maintenant'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'orders' && (
            <div className="mt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Mes commandes</h2>
              <div className="space-y-4">
                {orders.map((order) => (
                  <div key={order.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{order.service_name}</h3>
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                            {getStatusText(order.status)}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                          <div>
                            <span className="font-medium">Commande du :</span>
                            <br />
                            {new Date(order.created_at).toLocaleDateString('fr-FR', {
                              day: '2-digit',
                              month: '2-digit', 
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          <div>
                            <span className="font-medium">Prix :</span>
                            <br />
                            <span className="text-2xl font-bold text-blue-600">{order.price}€</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {order.client_notes && (
                      <div className="mb-4 p-3 bg-blue-50 rounded-md">
                        <p className="text-sm font-medium text-blue-900">📝 Vos notes :</p>
                        <p className="text-sm text-blue-700 mt-1">{order.client_notes}</p>
                      </div>
                    )}
                    
                    {order.admin_notes && (
                      <div className="mb-4 p-3 bg-green-50 rounded-md">
                        <p className="text-sm font-medium text-green-900">💬 Réponse de l'équipe :</p>
                        <p className="text-sm text-green-700 mt-1">{order.admin_notes}</p>
                      </div>
                    )}

                    {order.status === 'pending' && (
                      <div className="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                        <div className="flex items-center mb-2">
                          <span className="text-yellow-800 font-medium">⏳ Action requise</span>
                        </div>
                        <p className="text-sm text-yellow-700 mb-3">
                          Veuillez télécharger votre fichier de cartographie originale pour démarrer le traitement.
                        </p>
                        <FileUploadComponent 
                          orderId={order.id}
                          onFileUpload={handleFileUpload}
                        />
                      </div>
                    )}
                    
                    {order.files && order.files.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                          📁 Fichiers de la commande
                        </h4>
                        <div className="space-y-3">
                          {order.files.map((file) => (
                            <div key={file.file_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-1">
                                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                    file.version_type === 'original' 
                                      ? 'bg-blue-100 text-blue-800' 
                                      : 'bg-green-100 text-green-800'
                                  }`}>
                                    {getVersionText(file.version_type)}
                                  </span>
                                  <span className="text-sm font-medium text-gray-900">{file.filename}</span>
                                </div>
                                {file.notes && (
                                  <p className="text-xs text-gray-500 mb-1">💭 {file.notes}</p>
                                )}
                                <p className="text-xs text-gray-400">
                                  Uploadé le {new Date(file.uploaded_at).toLocaleDateString('fr-FR')}
                                </p>
                              </div>
                              <button
                                onClick={() => handleDownload(order.id, file.file_id, file.filename)}
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                                  file.version_type === 'original'
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-green-600 text-white hover:bg-green-700'
                                }`}
                              >
                                📥 Télécharger
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {orders.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Aucune commande pour le moment</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const FileUploadComponent = ({ orderId, onFileUpload }) => {
  const [file, setFile] = useState(null);
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await onFileUpload(orderId, file, notes);
      setFile(null);
      setNotes('');
    } catch (error) {
      console.error('Erreur lors de l\'upload:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-dashed border-blue-300">
      <div className="text-center mb-4">
        <div className="w-16 h-16 mx-auto mb-3 bg-blue-100 rounded-full flex items-center justify-center">
          <span className="text-2xl">📁</span>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Télécharger votre fichier de cartographie
        </h3>
        <p className="text-sm text-gray-600">
          Envoyez-nous votre fichier original pour commencer le traitement
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📎 Sélectionner votre fichier
          </label>
          <div className="relative">
            <input
              type="file"
              accept=".bin,.hex,.map,.kp,.ori,.mod"
              onChange={(e) => setFile(e.target.files[0])}
              required
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer cursor-pointer"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Formats acceptés : .bin, .hex, .map, .kp, .ori, .mod (max 10MB)
          </p>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📝 Informations sur votre véhicule
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            className="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Exemple:
• Marque et modèle: BMW 320d F30
• Année: 2015
• Moteur: N47D20C 184cv
• Modifications existantes: Aucune
• Objectifs: Stage 1 + suppression EGR
• Problèmes rencontrés: Mode dégradé"
          />
          <p className="text-xs text-gray-500 mt-1">
            Plus vous donnez d'informations, plus nous pourrons optimiser précisément votre cartographie
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-blue-200">
          <h4 className="font-medium text-gray-900 mb-2">ℹ️ Informations importantes :</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Délai de traitement : 24-48h ouvrées</li>
            <li>• Vous recevrez un email de confirmation</li>
            <li>• Le fichier modifié sera disponible dans votre espace client</li>
            <li>• Support technique inclus pendant 30 jours</li>
          </ul>
        </div>
        
        <button
          type="submit"
          disabled={uploading || !file}
          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-4 rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg transition-all duration-200 transform hover:scale-105"
        >
          {uploading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Envoi en cours...
            </span>
          ) : (
            '🚀 Envoyer le fichier et démarrer le traitement'
          )}
        </button>
      </form>
    </div>
  );
};

const AdminDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('orders');
  const [orders, setOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [editingService, setEditingService] = useState(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showCreateService, setShowCreateService] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = authService.getToken();
      const [ordersRes, usersRes, servicesRes] = await Promise.all([
        axios.get(`${API}/admin/orders`, { headers: { Authorization: `Bearer ${token}` } }),
        apiService.adminGetUsers(),
        apiService.adminGetServices()
      ]);
      
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setServices(servicesRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
    }
  };

  const updateOrderStatus = async (orderId, status, adminNotes = '') => {
    try {
      const token = authService.getToken();
      await axios.put(`${API}/admin/orders/${orderId}/status`, 
        { status, admin_notes: adminNotes }, 
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await loadData();
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut:', error);
    }
  };

  const handleAdminDownload = async (orderId, fileId, filename) => {
    try {
      const response = await apiService.adminDownloadFile(orderId, fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `original-${orderId}.bin`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
    }
  };

  const handleAdminUpload = async (orderId, file, versionType, notes) => {
    try {
      await apiService.adminUploadFile(orderId, file, versionType, notes);
      await loadData();
    } catch (error) {
      console.error('Erreur lors de l\'upload admin:', error);
    }
  };

  const handleUserCreate = async (userData) => {
    try {
      await apiService.adminCreateUser(userData);
      await loadData();
      setShowCreateUser(false);
    } catch (error) {
      console.error('Erreur lors de la création du client:', error);
    }
  };

  const handleUserUpdate = async (userId, userData) => {
    try {
      await apiService.adminUpdateUser(userId, userData);
      await loadData();
      setEditingUser(null);
    } catch (error) {
      console.error('Erreur lors de la mise à jour du client:', error);
    }
  };

  const handleUserDelete = async (userId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce client ?')) {
      try {
        await apiService.adminDeleteUser(userId);
        await loadData();
      } catch (error) {
        console.error('Erreur lors de la suppression du client:', error);
      }
    }
  };

  const handleServiceCreate = async (serviceData) => {
    try {
      await apiService.adminCreateService(serviceData);
      await loadData();
      setShowCreateService(false);
    } catch (error) {
      console.error('Erreur lors de la création du service:', error);
    }
  };

  const handleServiceUpdate = async (serviceId, serviceData) => {
    try {
      await apiService.adminUpdateService(serviceId, serviceData);
      await loadData();
      setEditingService(null);
    } catch (error) {
      console.error('Erreur lors de la mise à jour du service:', error);
    }
  };

  const handleServiceDelete = async (serviceId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce service ?')) {
      try {
        await apiService.adminDeleteService(serviceId);
        await loadData();
      } catch (error) {
        console.error('Erreur lors de la suppression du service:', error);
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'delivered': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'En attente';
      case 'processing': return 'En cours';
      case 'completed': return 'Terminé';
      case 'delivered': return 'Livré';
      default: return status;
    }
  };

  const getVersionText = (versionType) => {
    switch (versionType) {
      case 'original': return 'Fichier original';
      case 'v1': return 'Version 1';
      case 'v2': return 'Version 2';
      case 'v3': return 'Version 3';
      case 'sav': return 'SAV';
      default: return versionType;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">DMR Développement - Admin</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Admin: {user.first_name}</span>
              <button
                onClick={onLogout}
                className="text-gray-700 hover:text-gray-900"
              >
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('orders')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'orders'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Commandes
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Clients
              </button>
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
            </nav>
          </div>

          {activeTab === 'orders' && (
            <div className="mt-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Gestion des commandes</h2>
              <div className="space-y-4">
                {orders.map((order) => (
                  <div key={order.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{order.service_name}</h3>
                        <p className="text-gray-600">Client: {order.user_id} | Prix: {order.price}€</p>
                        <p className="text-gray-600">Commande du {new Date(order.created_at).toLocaleDateString()}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                        {getStatusText(order.status)}
                      </span>
                    </div>
                    
                    {order.client_notes && (
                      <div className="mb-4 p-3 bg-blue-50 rounded-md">
                        <p className="text-sm font-medium text-blue-900">Notes du client :</p>
                        <p className="text-sm text-blue-700">{order.client_notes}</p>
                      </div>
                    )}
                    
                    {order.admin_notes && (
                      <div className="mb-4 p-3 bg-green-50 rounded-md">
                        <p className="text-sm font-medium text-green-900">Vos notes :</p>
                        <p className="text-sm text-green-700">{order.admin_notes}</p>
                      </div>
                    )}

                    {order.files && order.files.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900 mb-2">Fichiers :</h4>
                        <div className="space-y-2">
                          {order.files.map((file) => (
                            <div key={file.file_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                    file.version_type === 'original' 
                                      ? 'bg-blue-100 text-blue-800' 
                                      : 'bg-green-100 text-green-800'
                                  }`}>
                                    {getVersionText(file.version_type)}
                                  </span>
                                  <span className="text-sm font-medium text-gray-900">{file.filename}</span>
                                </div>
                                {file.notes && (
                                  <p className="text-xs text-gray-500 mt-1">{file.notes}</p>
                                )}
                                <p className="text-xs text-gray-400">
                                  Uploadé le {new Date(file.uploaded_at).toLocaleDateString()}
                                </p>
                              </div>
                              <button
                                onClick={() => handleAdminDownload(order.id, file.file_id, file.filename)}
                                className={`px-3 py-1 rounded-md text-sm font-medium ${
                                  file.version_type === 'original'
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-green-600 text-white hover:bg-green-700'
                                }`}
                              >
                                {file.version_type === 'original' ? 'Télécharger Original' : 'Télécharger'}
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex space-x-4 items-center">
                      <select
                        value={order.status}
                        onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                        className="text-sm border border-gray-300 rounded-md px-2 py-1"
                      >
                        <option value="pending">En attente</option>
                        <option value="processing">En cours</option>
                        <option value="completed">Terminé</option>
                        <option value="delivered">Livré</option>
                      </select>
                      
                      <button
                        onClick={() => setSelectedOrder(selectedOrder === order.id ? null : order.id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700 text-sm"
                      >
                        {selectedOrder === order.id ? 'Fermer' : 'Gérer fichiers'}
                      </button>
                    </div>
                    
                    {selectedOrder === order.id && (
                      <AdminFileUpload 
                        orderId={order.id}
                        onFileUpload={handleAdminUpload}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Gestion des clients</h2>
                <button
                  onClick={() => setShowCreateUser(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Créer un client
                </button>
              </div>
              
              {showCreateUser && (
                <UserForm
                  onSubmit={handleUserCreate}
                  onCancel={() => setShowCreateUser(false)}
                  title="Créer un client"
                />
              )}
              
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {users && users.filter(u => u.role === 'client').map((user) => (
                    <li key={user.id} className="px-6 py-4">
                      {editingUser === user.id ? (
                        <UserForm
                          user={user}
                          onSubmit={(userData) => handleUserUpdate(user.id, userData)}
                          onCancel={() => setEditingUser(null)}
                          title="Modifier le client"
                        />
                      ) : (
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {user.first_name} {user.last_name}
                            </p>
                            <p className="text-sm text-gray-500">{user.email}</p>
                            {user.company && <p className="text-sm text-gray-500">{user.company}</p>}
                            {user.phone && <p className="text-sm text-gray-500">{user.phone}</p>}
                            <p className="text-sm text-gray-500">
                              Statut: {user.is_active ? 'Actif' : 'Inactif'}
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setEditingUser(user.id)}
                              className="text-blue-600 hover:text-blue-900 text-sm"
                            >
                              Modifier
                            </button>
                            <button
                              onClick={() => handleUserDelete(user.id)}
                              className="text-red-600 hover:text-red-900 text-sm"
                            >
                              Supprimer
                            </button>
                          </div>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'services' && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Gestion des services</h2>
                <button
                  onClick={() => setShowCreateService(true)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                >
                  Créer un service
                </button>
              </div>
              
              {showCreateService && (
                <ServiceForm
                  onSubmit={handleServiceCreate}
                  onCancel={() => setShowCreateService(false)}
                  title="Créer un service"
                />
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services && services.map((service) => (
                  <div key={service.id} className="bg-white rounded-lg shadow-md p-6">
                    {editingService === service.id ? (
                      <ServiceForm
                        service={service}
                        onSubmit={(serviceData) => handleServiceUpdate(service.id, serviceData)}
                        onCancel={() => setEditingService(null)}
                        title="Modifier le service"
                      />
                    ) : (
                      <>
                        <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                        <p className="text-gray-600 mt-2">{service.description}</p>
                        <div className="mt-4 flex justify-between items-center">
                          <span className="text-2xl font-bold text-blue-600">{service.price}€</span>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            service.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {service.is_active ? 'Actif' : 'Inactif'}
                          </span>
                        </div>
                        <div className="mt-4 flex space-x-2">
                          <button
                            onClick={() => setEditingService(service.id)}
                            className="text-blue-600 hover:text-blue-900 text-sm"
                          >
                            Modifier
                          </button>
                          <button
                            onClick={() => handleServiceDelete(service.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                          >
                            Supprimer
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const UserForm = ({ user, onSubmit, onCancel, title }) => {
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    password: '',
    phone: user?.phone || '',
    company: user?.company || '',
    is_active: user?.is_active !== undefined ? user.is_active : true,
    role: user?.role || 'client'
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = { ...formData };
    if (user && !submitData.password) {
      delete submitData.password; // Don't update password if empty
    }
    onSubmit(submitData);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Prénom</label>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Nom</label>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Mot de passe {user ? '(laisser vide pour ne pas changer)' : ''}
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required={!user}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Téléphone</label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Société</label>
          <input
            type="text"
            name="company"
            value={formData.company}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div className="flex items-center">
          <input
            type="checkbox"
            name="is_active"
            checked={formData.is_active}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label className="ml-2 block text-sm text-gray-900">
            Compte actif
          </label>
        </div>
        
        <div className="flex space-x-4">
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            {user ? 'Modifier' : 'Créer'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
};

const ServiceForm = ({ service, onSubmit, onCancel, title }) => {
  const [formData, setFormData] = useState({
    name: service?.name || '',
    price: service?.price || '',
    description: service?.description || '',
    is_active: service?.is_active !== undefined ? service.is_active : true
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (name === 'price' ? parseFloat(value) || 0 : value)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Nom du service</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Prix (€)</label>
          <input
            type="number"
            name="price"
            value={formData.price}
            onChange={handleChange}
            step="0.01"
            min="0"
            required
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div className="flex items-center">
          <input
            type="checkbox"
            name="is_active"
            checked={formData.is_active}
            onChange={handleChange}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label className="ml-2 block text-sm text-gray-900">
            Service actif
          </label>
        </div>
        
        <div className="flex space-x-4">
          <button
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            {service ? 'Modifier' : 'Créer'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700"
          >
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
};

const AdminFileUpload = ({ orderId, onFileUpload }) => {
  const [file, setFile] = useState(null);
  const [versionType, setVersionType] = useState('v1');
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await onFileUpload(orderId, file, versionType, notes);
      setFile(null);
      setNotes('');
    } catch (error) {
      console.error('Erreur lors de l\'upload:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 className="font-medium text-gray-900 mb-4">Upload fichier modifié</h4>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Fichier modifié :
          </label>
          <input
            type="file"
            accept=".bin,.hex,.map"
            onChange={(e) => setFile(e.target.files[0])}
            required
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type de version :
          </label>
          <select
            value={versionType}
            onChange={(e) => setVersionType(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="v1">Version 1</option>
            <option value="v2">Version 2</option>
            <option value="v3">Version 3</option>
            <option value="sav">SAV</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Notes (optionnel) :
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Décrivez les modifications apportées..."
          />
        </div>
        
        <button
          type="submit"
          disabled={uploading || !file}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {uploading ? 'Envoi en cours...' : 'Envoyer le fichier'}
        </button>
      </form>
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
      <Login 
        onLogin={handleLogin} 
        switchToRegister={() => setShowLogin(false)} 
      />
    ) : (
      <Register 
        onRegister={() => setShowLogin(true)} 
        switchToLogin={() => setShowLogin(true)} 
      />
    );
  }

  return user.role === 'admin' ? (
    <AdminDashboard user={user} onLogout={handleLogout} />
  ) : (
    <ClientDashboard user={user} onLogout={handleLogout} />
  );
};

export default App;