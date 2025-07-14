import React, { useState, useEffect } from 'react';

// Enhanced Admin Dashboard Component
const AdminDashboard = ({ user, onLogout, apiService }) => {
  const [activeTab, setActiveTab] = useState('pending');
  const [ordersByClient, setOrdersByClient] = useState([]);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [users, setUsers] = useState([]);
  const [services, setServices] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [previousUnreadCount, setPreviousUnreadCount] = useState(0);
  
  // Chat states
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  
  // Modal states for create/edit
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);
  const [showCreateService, setShowCreateService] = useState(false);
  const [showEditService, setShowEditService] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingService, setEditingService] = useState(null);

  useEffect(() => {
    loadOrdersByClient();
    loadPendingOrders();
    loadUsers();
    loadServices();
    loadNotifications();
    loadConversations();
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      loadNotifications();
      if (activeTab === 'chat') {
        loadConversations();
        if (selectedConversation) {
          loadMessages(selectedConversation.user.id);
        }
      }
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadConversations = async () => {
    try {
      const data = await apiService.adminGetConversations();
      setConversations(data);
    } catch (error) {
      console.error('Erreur lors du chargement des conversations:', error);
    }
  };

  const loadMessages = async (userId) => {
    try {
      const data = await apiService.adminGetChatMessages(userId);
      setMessages(data);
    } catch (error) {
      console.error('Erreur lors du chargement des messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    
    try {
      await apiService.adminSendMessage(selectedConversation.user.id, newMessage);
      setNewMessage('');
      await loadMessages(selectedConversation.user.id);
      await loadConversations();
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
    }
  };

  const selectConversation = async (conversation) => {
    setSelectedConversation(conversation);
    await loadMessages(conversation.user.id);
  };

  const loadPendingOrders = async () => {
    try {
      const data = await apiService.adminGetPendingOrders();
      setPendingOrders(data);
    } catch (error) {
      console.error('Erreur lors du chargement des commandes en attente:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const notifs = await apiService.adminGetNotifications();
      setNotifications(notifs);
      const currentUnreadCount = notifs.filter(n => !n.is_read).length;
      
      // Play sound if new notification
      if (currentUnreadCount > previousUnreadCount && previousUnreadCount !== 0) {
        playNotificationSound();
      }
      
      setPreviousUnreadCount(currentUnreadCount);
      setUnreadCount(currentUnreadCount);
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

  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      try {
        await apiService.adminMarkNotificationRead(notification.id);
        await loadNotifications();
      } catch (error) {
        console.error('Erreur lors du marquage de la notification:', error);
      }
    }
    setShowNotifications(false);
    // Optionally navigate to the related order
    if (notification.order_id) {
      setActiveTab('orders');
    }
  };

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
      await loadPendingOrders(); // Reload pending orders too
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut de paiement:', error);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (window.confirm('Êtes-vous sûr de vouloir annuler cette commande ?')) {
      try {
        await apiService.adminCancelOrder(orderId);
        await loadOrdersByClient(); // Reload to update totals
        await loadPendingOrders(); // Reload pending orders too
      } catch (error) {
        console.error('Erreur lors de l\'annulation de la commande:', error);
      }
    }
  };

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      if (newStatus === 'cancelled') {
        if (window.confirm('Êtes-vous sûr de vouloir annuler cette commande ?')) {
          await apiService.adminCancelOrder(orderId);
          await loadOrdersByClient();
          await loadPendingOrders();
        } else {
          return; // Don't proceed if user cancels
        }
      } else {
        // Use existing status update endpoint
        await apiService.adminUpdateOrderStatus(orderId, { status: newStatus });
        await loadOrdersByClient();
        await loadPendingOrders();
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour du statut:', error);
    }
  };

  const handleFileUpload = async (orderId, file, versionType) => {
    try {
      await apiService.adminUploadFile(orderId, file, versionType);
      await loadOrdersByClient();
      await loadPendingOrders();
    } catch (error) {
      console.error('Erreur lors de l\'upload:', error);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await apiService.adminDeleteNotification(notificationId);
      await loadNotifications();
    } catch (error) {
      console.error('Erreur lors de la suppression de la notification:', error);
    }
  };

  const handleDeleteAllNotifications = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer toutes les notifications ?')) {
      try {
        await apiService.adminDeleteAllNotifications();
        await loadNotifications();
      } catch (error) {
        console.error('Erreur lors de la suppression des notifications:', error);
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

  const handleCreateUser = async (userData) => {
    try {
      await apiService.adminCreateUser(userData);
      await loadUsers();
      setShowCreateUser(false);
    } catch (error) {
      console.error('Erreur lors de la création de l\'utilisateur:', error);
      alert('Erreur lors de la création de l\'utilisateur');
    }
  };

  const handleUpdateUser = async (userData) => {
    try {
      await apiService.adminUpdateUser(editingUser.id, userData);
      await loadUsers();
      setShowEditUser(false);
      setEditingUser(null);
    } catch (error) {
      console.error('Erreur lors de la modification de l\'utilisateur:', error);
      alert('Erreur lors de la modification de l\'utilisateur');
    }
  };

  const handleCreateService = async (serviceData) => {
    try {
      await apiService.adminCreateService(serviceData);
      await loadServices();
      setShowCreateService(false);
    } catch (error) {
      console.error('Erreur lors de la création du service:', error);
      alert('Erreur lors de la création du service');
    }
  };

  const handleUpdateService = async (serviceData) => {
    try {
      await apiService.adminUpdateService(editingService.id, serviceData);
      await loadServices();
      setShowEditService(false);
      setEditingService(null);
    } catch (error) {
      console.error('Erreur lors de la modification du service:', error);
      alert('Erreur lors de la modification du service');
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
              {/* Notifications Bell */}
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative text-gray-700 hover:text-gray-900"
              >
                🔔
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>
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

      <div className="pt-16"></div>

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="fixed top-16 right-4 w-80 bg-white shadow-lg rounded-lg border border-gray-200 z-40 max-h-96 overflow-y-auto">
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

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('pending')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Fichiers à modifier
            </button>
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
              onClick={() => setActiveTab('chat')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'chat'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Chat
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
                              <h4 className="font-semibold text-gray-900">
                                {order.immatriculation ? `${order.immatriculation} - ${order.service_name}` : order.service_name}
                              </h4>
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
                              
                              {/* Order Status Dropdown */}
                              <select
                                value={order.status}
                                onChange={(e) => handleStatusChange(order.id, e.target.value)}
                                className="text-sm border border-gray-300 rounded px-2 py-1"
                                disabled={order.status === 'cancelled'}
                              >
                                <option value="pending">En attente</option>
                                <option value="processing">En cours</option>
                                <option value="completed">Terminé</option>
                                <option value="cancelled">Annulé</option>
                              </select>
                              
                              {/* Price */}
                              <div className="text-lg font-bold text-gray-900">{order.price}€</div>
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
                              
                              {/* Admin File Upload */}
                              <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                                <h6 className="font-medium text-blue-900 mb-2">📤 Uploader un fichier modifié</h6>
                                <AdminFileUploadComponent 
                                  orderId={order.id} 
                                  onFileUpload={handleFileUpload}
                                />
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

        {activeTab === 'pending' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Fichiers à modifier</h2>
            {pendingOrders.length > 0 ? (
              <div className="space-y-4">
                {pendingOrders.map((order) => (
                  <div key={order.id} className="bg-white rounded-lg shadow-lg p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {order.immatriculation ? `${order.immatriculation} - ${order.service_name}` : order.service_name}
                        </h3>
                        <p className="text-sm text-gray-600">
                          Client: {order.user.first_name} {order.user.last_name} ({order.user.email})
                        </p>
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
                        
                        {/* Order Status Dropdown */}
                        <select
                          value={order.status}
                          onChange={(e) => handleStatusChange(order.id, e.target.value)}
                          className="text-sm border border-gray-300 rounded px-2 py-1"
                          disabled={order.status === 'cancelled'}
                        >
                          <option value="pending">En attente</option>
                          <option value="processing">En cours</option>
                          <option value="completed">Terminé</option>
                          <option value="cancelled">Annulé</option>
                        </select>
                        
                        {/* Price */}
                        <div className="text-lg font-bold text-gray-900">{order.price}€</div>
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
                        
                        {/* Admin File Upload */}
                        <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                          <h6 className="font-medium text-blue-900 mb-2">📤 Uploader un fichier modifié</h6>
                          <AdminFileUploadComponent 
                            orderId={order.id} 
                            onFileUpload={handleFileUpload}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">Aucune commande en attente de traitement</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Chat</h2>
            <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{height: '600px'}}>
              <div className="flex h-full">
                {/* Conversations List */}
                <div className="w-1/3 border-r border-gray-200">
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <h3 className="font-semibold text-gray-900">Conversations</h3>
                  </div>
                  <div className="overflow-y-auto h-full">
                    {conversations.length > 0 ? (
                      conversations.map((conversation) => (
                        <div
                          key={conversation.user.id}
                          onClick={() => selectConversation(conversation)}
                          className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                            selectedConversation?.user.id === conversation.user.id ? 'bg-blue-50' : ''
                          }`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="font-semibold text-gray-900">
                                {conversation.user.first_name} {conversation.user.last_name}
                              </div>
                              <div className="text-sm text-gray-600">{conversation.user.email}</div>
                              <div className="text-sm text-gray-500 truncate mt-1">
                                {conversation.last_message?.message || 'Pas de message'}
                              </div>
                            </div>
                            {conversation.unread_count > 0 && (
                              <div className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                                {conversation.unread_count}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-gray-500 text-center">Aucune conversation</div>
                    )}
                  </div>
                </div>
                
                {/* Chat Interface */}
                <div className="flex-1 flex flex-col">
                  {selectedConversation ? (
                    <>
                      {/* Chat Header */}
                      <div className="p-4 border-b border-gray-200 bg-gray-50">
                        <div className="font-semibold text-gray-900">
                          {selectedConversation.user.first_name} {selectedConversation.user.last_name}
                        </div>
                        <div className="text-sm text-gray-600">{selectedConversation.user.email}</div>
                      </div>
                      
                      {/* Messages */}
                      <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex ${message.sender_role === 'admin' ? 'justify-end' : 'justify-start'}`}
                          >
                            <div
                              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                                message.sender_role === 'admin'
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-200 text-gray-900'
                              }`}
                            >
                              <div>{message.message}</div>
                              <div className={`text-xs mt-1 ${
                                message.sender_role === 'admin' ? 'text-blue-100' : 'text-gray-500'
                              }`}>
                                {new Date(message.created_at).toLocaleString()}
                              </div>
                            </div>
                          </div>
                        ))}
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
                    </>
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500">
                      Sélectionnez une conversation pour commencer
                    </div>
                  )}
                </div>
              </div>
            </div>
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

      {/* User Create/Edit Modal */}
      {(showCreateUser || showEditUser) && (
        <UserModal
          user={editingUser}
          onSubmit={showCreateUser ? handleCreateUser : handleUpdateUser}
          onCancel={() => {
            setShowCreateUser(false);
            setShowEditUser(false);
            setEditingUser(null);
          }}
          title={showCreateUser ? "Créer un utilisateur" : "Éditer l'utilisateur"}
        />
      )}

      {/* Service Create/Edit Modal */}
      {(showCreateService || showEditService) && (
        <ServiceModal
          service={editingService}
          onSubmit={showCreateService ? handleCreateService : handleUpdateService}
          onCancel={() => {
            setShowCreateService(false);
            setShowEditService(false);
            setEditingService(null);
          }}
          title={showCreateService ? "Créer un service" : "Éditer le service"}
        />
      )}
    </div>
  );
};

// User Modal Component
const UserModal = ({ user, onSubmit, onCancel, title }) => {
  const [formData, setFormData] = useState({
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    password: '',
    role: user?.role || 'client',
    discount_percentage: user?.discount_percentage || 0
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <h3 className="text-lg font-bold text-gray-900 mb-4">{title}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              name="email"
              required
              value={formData.email}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Prénom</label>
              <input
                type="text"
                name="first_name"
                required
                value={formData.first_name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Nom</label>
              <input
                type="text"
                name="last_name"
                required
                value={formData.last_name}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          {!user && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Mot de passe</label>
              <input
                type="password"
                name="password"
                required={!user}
                value={formData.password}
                onChange={handleChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700">Rôle</label>
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="client">Client</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Remise (%)</label>
            <input
              type="number"
              name="discount_percentage"
              min="0"
              max="30"
              value={formData.discount_percentage}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {user ? 'Modifier' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Service Modal Component
const ServiceModal = ({ service, onSubmit, onCancel, title }) => {
  const [formData, setFormData] = useState({
    name: service?.name || '',
    price: service?.price || '',
    description: service?.description || '',
    is_active: service?.is_active !== undefined ? service.is_active : true
  });

  const handleChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      price: parseFloat(formData.price)
    });
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <h3 className="text-lg font-bold text-gray-900 mb-4">{title}</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Nom du service</label>
            <input
              type="text"
              name="name"
              required
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Prix (€)</label>
            <input
              type="number"
              name="price"
              required
              min="0"
              step="0.01"
              value={formData.price}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Service visible aux clients</span>
            </label>
          </div>
          <div className="flex justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {service ? 'Modifier' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Admin File Upload Component
const AdminFileUploadComponent = ({ orderId, onFileUpload }) => {
  const [file, setFile] = useState(null);
  const [versionType, setVersionType] = useState('v1');
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    try {
      await onFileUpload(orderId, file, versionType);
      setFile(null);
      setVersionType('v1');
      // Reset file input
      e.target.reset();
    } catch (error) {
      console.error('Erreur upload:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleUpload} className="space-y-3">
      <div className="flex space-x-3">
        <select
          value={versionType}
          onChange={(e) => setVersionType(e.target.value)}
          className="text-sm border border-gray-300 rounded px-2 py-1"
        >
          <option value="v1">Nouvelle version</option>
          <option value="SAV">SAV</option>
        </select>
        <input
          type="file"
          accept=".bin,.ori,.ecu,.hex,.dat"
          onChange={(e) => setFile(e.target.files[0])}
          className="text-sm border border-gray-300 rounded px-2 py-1 flex-1"
        />
        <button
          type="submit"
          disabled={!file || uploading}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {uploading ? 'Upload...' : 'Uploader'}
        </button>
      </div>
    </form>
  );
};

export default AdminDashboard;