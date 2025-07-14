import React, { useState, useEffect } from 'react';

// Enhanced Admin Dashboard Component
const AdminDashboard = ({ user, onLogout, apiService }) => {
  const [activeTab, setActiveTab] = useState('orders');
  const [ordersByClient, setOrdersByClient] = useState([]);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Modal states for create/edit
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showCreateService, setShowCreateService] = useState(false);
  const [showEditService, setShowEditService] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingService, setEditingService] = useState(null);

  useEffect(() => {
    loadOrdersByClient();
    loadUsers();
    loadServices();
  }, []);

  const loadOrdersByClient = async () => {
    try {
      const data = await apiService.adminGetOrdersByClient();
      setOrdersByClient(data);
    } catch (error) {
      console.error('Erreur lors du chargement des commandes par client:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const usersData = await apiService.adminGetUsers();
      setUsers(usersData);
    } catch (error) {
      console.error('Erreur lors du chargement des utilisateurs:', error);
    }
  };

  const loadServices = async () => {
    try {
      const servicesData = await apiService.adminGetServices();
      setServices(servicesData);
    } catch (error) {
      console.error('Erreur lors du chargement des services:', error);
    }
  };

  const handlePaymentStatusChange = async (orderId, newStatus) => {
    try {
      await apiService.adminUpdatePaymentStatus(orderId, newStatus);
      await loadOrdersByClient(); // Reload to update totals
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut de paiement:', error);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (window.confirm('Êtes-vous sûr de vouloir annuler cette commande ?')) {
      try {
        await apiService.adminCancelOrder(orderId);
        await loadOrdersByClient(); // Reload to update totals
      } catch (error) {
        console.error('Erreur lors de l\'annulation de la commande:', error);
      }
    }
  };

  const handleUserStatusChange = async (userId, isActive) => {
    try {
      await apiService.adminUpdateUserStatus(userId, isActive);
      await loadUsers();
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut utilisateur:', error);
    }
  };

  const handleServiceStatusChange = async (serviceId, isActive) => {
    try {
      await apiService.adminUpdateService(serviceId, { is_active: isActive });
      await loadServices();
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut service:', error);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ?')) {
      try {
        await apiService.adminDeleteUser(userId);
        await loadUsers();
      } catch (error) {
        console.error('Erreur lors de la suppression de l\'utilisateur:', error);
      }
    }
  };

  const handleDeleteService = async (serviceId) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce service ?')) {
      try {
        await apiService.adminDeleteService(serviceId);
        await loadServices();
      } catch (error) {
        console.error('Erreur lors de la suppression du service:', error);
      }
    }
  };

  const handleDownload = async (orderId, fileId, filename) => {
    try {
      const response = await apiService.adminDownloadFile(orderId, fileId);
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

  const getPaymentStatusColor = (paymentStatus) => {
    return paymentStatus === 'paid' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  const getPaymentStatusText = (paymentStatus) => {
    return paymentStatus === 'paid' ? 'Payé' : 'Non payé';
  };

  const getVersionText = (versionType) => {
    switch (versionType) {
      case 'original': return 'Original';
      case 'v1': return 'Version 1';
      case 'v2': return 'Version 2';
      case 'v3': return 'Version 3';
      case 'SAV': return 'SAV';
      default: return versionType;
    }
  };

  const truncateFilename = (filename, maxLength = 20) => {
    if (!filename || filename.length <= maxLength) return filename;
    const extension = filename.split('.').pop();
    const name = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = name.substring(0, maxLength - extension.length - 4) + '...';
    return `${truncatedName}.${extension}`;
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg fixed top-0 left-0 right-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">DMR DEVELOPPEMENT - Admin</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">Admin: {user.first_name}!</span>
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

      <div className="pt-16"></div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
              Commandes par Client
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'users'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Utilisateurs
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
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'orders' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Commandes par Client</h2>
            {ordersByClient.length > 0 ? (
              <div className="space-y-8">
                {ordersByClient.map((clientData) => (
                  <div key={clientData.user.id} className="bg-white rounded-lg shadow-lg p-6">
                    {/* Client Header */}
                    <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200">
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900">
                          {clientData.user.first_name} {clientData.user.last_name}
                        </h3>
                        <p className="text-gray-600">{clientData.user.email}</p>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full mt-1 ${
                          clientData.user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {clientData.user.is_active ? 'Actif' : 'Inactif'}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-red-600">
                          Solde dû: {clientData.total_unpaid}€
                        </div>
                        <div className="text-sm text-gray-500">
                          {clientData.orders.length} commande(s)
                        </div>
                      </div>
                    </div>

                    {/* Orders */}
                    <div className="space-y-4">
                      {clientData.orders.map((order) => (
                        <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900">{order.service_name}</h4>
                              <p className="text-sm text-gray-500">
                                Commande du {new Date(order.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="flex items-center space-x-4">
                              {/* Payment Status Dropdown */}
                              <select
                                value={order.payment_status || 'unpaid'}
                                onChange={(e) => handlePaymentStatusChange(order.id, e.target.value)}
                                className="text-sm border border-gray-300 rounded px-2 py-1"
                                disabled={order.status === 'cancelled'}
                              >
                                <option value="unpaid">Non payé</option>
                                <option value="paid">Payé</option>
                              </select>
                              
                              {/* Order Status */}
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
                                {getStatusText(order.status)}
                              </span>
                              
                              {/* Price */}
                              <div className="text-lg font-bold text-gray-900">{order.price}€</div>
                              
                              {/* Cancel Button */}
                              {order.status !== 'cancelled' && order.status !== 'completed' && (
                                <button
                                  onClick={() => handleCancelOrder(order.id)}
                                  className="text-red-600 hover:text-red-800 text-sm font-medium"
                                >
                                  Annuler
                                </button>
                              )}
                            </div>
                          </div>
                          
                          {/* Files */}
                          {order.files && order.files.length > 0 && (
                            <div className="mt-3 p-3 bg-gray-50 rounded-md">
                              <h5 className="font-medium text-gray-900 mb-2">📁 Fichiers</h5>
                              <div className="grid gap-2">
                                {order.files.map((file) => (
                                  <div key={file.id} className="flex items-center justify-between p-2 bg-white rounded border">
                                    <div className="flex items-center space-x-3 min-w-0 flex-1">
                                      <span className="text-sm font-medium text-gray-900 whitespace-nowrap">
                                        {getVersionText(file.version_type)}
                                      </span>
                                      <span className="text-sm text-gray-500 truncate" title={file.filename}>
                                        {truncateFilename(file.filename)}
                                      </span>
                                    </div>
                                    <div className="flex-shrink-0 ml-4">
                                      <button
                                        onClick={() => handleDownload(order.id, file.id, file.filename)}
                                        className="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 rounded border border-blue-200 hover:border-blue-300"
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
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Aucune commande trouvée</p>
              </div>
            )}
          </div>
        )}

        {/* Users Tab - Implementation continues... */}
        {activeTab === 'users' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Gestion des utilisateurs</h2>
              <button
                onClick={() => setShowCreateUser(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Créer un utilisateur
              </button>
            </div>
            
            {users.length > 0 ? (
              <div className="bg-white shadow-md rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Utilisateur
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Rôle
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Statut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name} {user.last_name}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {user.email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleUserStatusChange(user.id, !user.is_active)}
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full cursor-pointer ${
                              user.is_active ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-red-100 text-red-800 hover:bg-red-200'
                            }`}
                          >
                            {user.is_active ? 'Actif' : 'Inactif'}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => {
                              setEditingUser(user);
                              setShowEditUser(true);
                            }}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Éditer
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Supprimer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Aucun utilisateur trouvé</p>
              </div>
            )}
          </div>
        )}

        {/* Services Tab */}
        {activeTab === 'services' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Gestion des services</h2>
              <button
                onClick={() => setShowCreateService(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Créer un service
              </button>
            </div>
            
            {services.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {services.map((service) => (
                  <div key={service.id} className="bg-white rounded-lg shadow-md p-6">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                      <button
                        onClick={() => handleServiceStatusChange(service.id, !service.is_active)}
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full cursor-pointer ${
                          service.is_active ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-red-100 text-red-800 hover:bg-red-200'
                        }`}
                      >
                        {service.is_active ? 'Visible' : 'Masqué'}
                      </button>
                    </div>
                    <p className="text-gray-600 mb-4">{service.description}</p>
                    <div className="text-xl font-bold text-blue-600 mb-4">{service.price}€</div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => {
                          setEditingService(service);
                          setShowEditService(true);
                        }}
                        className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700 text-sm"
                      >
                        Éditer
                      </button>
                      <button
                        onClick={() => handleDeleteService(service.id)}
                        className="flex-1 bg-red-600 text-white px-3 py-2 rounded-md hover:bg-red-700 text-sm"
                      >
                        Supprimer
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Aucun service trouvé</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;