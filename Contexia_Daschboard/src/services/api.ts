const API_BASE_URL = 'https://antigravity-app-production-175a.up.railway.app/api/v1/agents';
const BASE_URL = 'https://antigravity-app-production-175a.up.railway.app/api/v1';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

export const api = {
  // AUTH
  login: async (credentials: { email: string; password: string }) => {
    const response = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error de autenticación');
    }
    return response.json();
  },

  // PULSO TODAY
  getPulsoToday: async (companyId: string) => {
    const response = await fetch(`${API_BASE_URL}/pulso/today`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_id: companyId }),
    });
    if (!response.ok) throw new Error('Error fetching Pulso Today');
    return response.json();
  },

  // CENTINELA ALERTS
  getCentinelaAlerts: async (usuarioId: string) => {
    const response = await fetch(`${BASE_URL}/centinela/${usuarioId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Error fetching Centinela Alerts');
    return response.json();
  },

  // TATY ASK
  askTaty: async (companyId: string, question: string) => {
    const response = await fetch(`${BASE_URL}/agents/taty/ask`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        company_id: companyId,
        question,
        channel: 'dashboard',
      }),
    });
    if (!response.ok) throw new Error('Error in Taty Ask');
    return response.json();
  },

  // FULL PIPELINE
  runFullPipeline: async (payload: { company_url: string; campaign_objective: string; budget: number; target_channels: string[]; company_id: string }) => {
    const response = await fetch(`${BASE_URL}/agents/orchestrator/full-pipeline`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error('Error running Full Pipeline');
    return response.json();
  },

  // ONBOARDING
  getOnboardingClients: async () => {
    const response = await fetch(`${BASE_URL}/onboarding/clients`, {
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Error fetching Onboarding Clients');
    return response.json();
  },

  toggleOnboardingStep: async (clientId: string, stepId: string, completed: boolean) => {
    const response = await fetch(`${BASE_URL}/onboarding/clients/${clientId}/steps/${stepId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ completed }),
    });
    if (!response.ok) throw new Error('Error toggling Onboarding Step');
    return response.json();
  },

  sendMagicReminder: async (clientId: string) => {
    const response = await fetch(`${BASE_URL}/onboarding/clients/${clientId}/remind`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Error sending Magic Reminder');
    return response.json();
  },

  // CRM PIPELINE
  getCrmLeads: async () => {
    const response = await fetch(`${BASE_URL}/crm/leads`, {
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Error fetching CRM Leads');
    return response.json();
  },

  updateLeadStatus: async (leadId: string, newStatus: string) => {
    const response = await fetch(`${BASE_URL}/crm/leads/${leadId}/status`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ estado: newStatus }),
    });
    if (!response.ok) throw new Error('Error updating CRM Lead Status');
    return response.json();
  },

  autoQualifyLead: async (leadId: string) => {
    const response = await fetch(`${BASE_URL}/crm/leads/${leadId}/qualify`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Error qualifying CRM Lead');
    return response.json();
  },

  // SOCIAL CONTENT OPS
  getSocialDashboardMetrics: async () => {
    const response = await fetch(`${BASE_URL}/social/dashboard/metrics`, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Error fetching Social Dashboard Metrics');
    return response.json();
  },

  getSocialCampaigns: async (estado?: string, tipo?: string) => {
    let url = `${BASE_URL}/social/campaigns`;
    const params = new URLSearchParams();
    if (estado) params.append('estado', estado);
    if (tipo) params.append('tipo', tipo);
    if (params.toString()) url += `?${params.toString()}`;
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Error fetching Social Campaigns');
    return response.json();
  },

  getSocialPosts: async (campaignId: string) => {
    const response = await fetch(`${BASE_URL}/social/campaigns/${campaignId}/posts`, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Error fetching Social Posts');
    return response.json();
  },

  createSocialPost: async (postData: any) => {
    const response = await fetch(`${BASE_URL}/social/posts`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(postData),
    });
    if (!response.ok) throw new Error('Error creating Social Post');
    return response.json();
  },

  updateSocialPost: async (postId: string, postData: any) => {
    const response = await fetch(`${BASE_URL}/social/posts/${postId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(postData),
    });
    if (!response.ok) throw new Error('Error updating Social Post');
    return response.json();
  },

  getSocialCalendar: async (year: number, month: number) => {
    const response = await fetch(`${BASE_URL}/social/calendar/${year}/${month}`, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Error fetching Social Calendar');
    return response.json();
  },

  generateSocialContent: async (topic: string, platform: string) => {
    const prompt = `Escribe un post para ${platform} sobre el siguiente tema: ${topic}. El post debe ser persuasivo, profesional pero cercano, e incluir emojis apropiados y al menos 3 hashtags estratégicos al final. NO respondas con comentarios, solo entrega el copy final listo para publicar.`;
    const response = await fetch(`${BASE_URL}/llm/analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ prompt, system_prompt: "Eres Taty, una experta en marketing digital y creación de contenido." })
    });
    if (!response.ok) throw new Error('Error generando contenido con IA');
    return response.json();
  },
};
