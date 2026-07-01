# Frontend Integration Guide - Contexia MVP

**Status:** Production Ready  
**Last Updated:** 2026-05-24  
**Environment:** https://contexia.online  
**API Base URL:** https://antigravity-app-production-175a.up.railway.app/api/v1

---

## Table of Contents

1. [Setup](#setup)
2. [API Client Configuration](#api-client-configuration)
3. [Connecting Each Service](#connecting-each-service)
4. [Error Handling](#error-handling)
5. [Authentication](#authentication)
6. [Testing Integration](#testing-integration)
7. [Troubleshooting](#troubleshooting)

---

## SETUP

### Step 1: Install Dependencies

```bash
npm install axios  # or fetch, whatever you prefer
# or
yarn add axios
```

### Step 2: Create API Client File

Create `src/services/contexiaAPI.ts`:

```typescript
import axios, { AxiosError } from 'axios';

const API_BASE_URL = 'https://antigravity-app-production-175a.up.railway.app/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Step 3: Create Service Hooks

Create `src/hooks/useContextiaServices.ts`:

```typescript
import { useState, useEffect } from 'react';
import apiClient from '@/services/contexiaAPI';

// Health Check
export const useHealth = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    apiClient
      .get('/health')
      .then((res) => setHealth(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { health, loading, error };
};

// Centinela Alerts
export const useCentinelaAlerts = (companyId: string) => {
  const [alerts, setAlerts] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/centinela/alerts', {
        params: { company_id: companyId },
      });
      setAlerts(res.data);
    } catch (err) {
      console.error('Centinela error:', err);
    } finally {
      setLoading(false);
    }
  };

  return { alerts, loading, fetch };
};

// Pulso Today
export const usePulsoToday = (companyId: string) => {
  const [pulso, setPulso] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await apiClient.post('/pulso/today', {
        company_id: companyId,
      });
      setPulso(res.data);
    } catch (err) {
      console.error('Pulso error:', err);
    } finally {
      setLoading(false);
    }
  };

  return { pulso, loading, fetch };
};

// Taty Q&A
export const useTatyAsk = () => {
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const ask = async (companyId: string, question: string) => {
    setLoading(true);
    try {
      const res = await apiClient.post('/taty/ask', {
        question,
        company_id: companyId,
      });
      setResponse(res.data);
      return res.data;
    } catch (err) {
      console.error('Taty error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { response, loading, ask };
};

// Full Pipeline (Agents)
export const useFullPipeline = () => {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const execute = async (
    companyId: string,
    companyUrl: string,
    campaignObjective: string,
    budget: number
  ) => {
    setLoading(true);
    try {
      const res = await apiClient.post(
        '/agents/orchestrator/full-pipeline',
        {
          company_id: companyId,
          company_url: companyUrl,
          campaign_objective: campaignObjective,
          budget,
        }
      );
      setResult(res.data);
      return res.data;
    } catch (err) {
      console.error('Pipeline error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, execute };
};
```

---

## API CLIENT CONFIGURATION

### Using with React Query (Recommended)

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import apiClient from '@/services/contexiaAPI';

// Query for Centinela
export const useCentinelaQuery = (companyId: string) => {
  return useQuery({
    queryKey: ['centinela', companyId],
    queryFn: async () => {
      const res = await apiClient.get('/centinela/alerts', {
        params: { company_id: companyId },
      });
      return res.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3,
  });
};

// Mutation for Taty
export const useTatyMutation = () => {
  return useMutation({
    mutationFn: async ({
      companyId,
      question,
    }: {
      companyId: string;
      question: string;
    }) => {
      const res = await apiClient.post('/taty/ask', {
        company_id: companyId,
        question,
      });
      return res.data;
    },
    onError: (error) => {
      console.error('Taty error:', error);
    },
  });
};
```

---

## CONNECTING EACH SERVICE

### 1. Health Check (Status Page)

```typescript
// components/StatusIndicator.tsx
import { useHealth } from '@/hooks/useContextiaServices';

export const StatusIndicator = () => {
  const { health, loading } = useHealth();

  if (loading) return <div>Checking...</div>;
  if (!health) return <div className="text-red-500">Down</div>;

  return (
    <div className="flex items-center gap-2">
      <div className="w-3 h-3 bg-green-500 rounded-full" />
      <span>Contexia API {health.status}</span>
    </div>
  );
};
```

### 2. Centinela Alerts (Dashboard Widget)

```typescript
// components/CentinelaWidget.tsx
import { useCentinelaQuery } from '@/hooks/useContextiaServices';

export const CentinelaWidget = ({ companyId }: { companyId: string }) => {
  const { data, isLoading, error } = useCentinelaQuery(companyId);

  if (isLoading) return <div>Loading alerts...</div>;
  if (error) return <div className="text-red-500">Error loading alerts</div>;

  return (
    <div className="border rounded-lg p-4">
      <h3 className="font-bold mb-4">Risk Alerts</h3>
      <div className="space-y-2">
        <div>
          <strong>Total Alerts:</strong> {data?.total_alerts || 0}
        </div>
        <div>
          <strong>Critical:</strong>{' '}
          {data?.alerts_by_severity?.critical?.length || 0}
        </div>
        <div>
          <strong>Warnings:</strong>{' '}
          {data?.alerts_by_severity?.warning?.length || 0}
        </div>
        <div>
          <strong>Info:</strong> {data?.alerts_by_severity?.info?.length || 0}
        </div>
      </div>
    </div>
  );
};
```

### 3. Pulso Today (KPI Dashboard)

```typescript
// components/PulsoDashboard.tsx
import { usePulsoQuery } from '@/hooks/useContextiaServices';

export const PulsoDashboard = ({ companyId }: { companyId: string }) => {
  const { data, isLoading } = usePulsoQuery(companyId);

  if (isLoading) return <div>Loading KPIs...</div>;

  const kpis = data?.kpis || {};

  return (
    <div className="grid grid-cols-2 gap-4">
      <KPICard
        title="Tax Filings Pending"
        value={kpis.tax_filings_pending}
        icon="📋"
      />
      <KPICard
        title="Compliance Status"
        value={kpis.compliance_status}
        icon="✅"
      />
      <KPICard title="Active Alerts" value={kpis.alerts_count} icon="🚨" />
      <KPICard
        title="Audit Risk Score"
        value={(kpis.audit_risk_score * 100).toFixed(0) + '%'}
        icon="📊"
      />
    </div>
  );
};

const KPICard = ({
  title,
  value,
  icon,
}: {
  title: string;
  value: any;
  icon: string;
}) => (
  <div className="bg-white border rounded-lg p-4">
    <div className="text-2xl mb-2">{icon}</div>
    <div className="text-sm text-gray-600">{title}</div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
);
```

### 4. Taty Q&A (Chat Interface)

```typescript
// components/TatyChat.tsx
import { useState } from 'react';
import { useTatyMutation } from '@/hooks/useContextiaServices';

export const TatyChat = ({ companyId }: { companyId: string }) => {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<any[]>([]);
  const { mutate: ask, isPending } = useTatyMutation();

  const handleAsk = async () => {
    if (!question) return;

    ask(
      { companyId, question },
      {
        onSuccess: (data) => {
          setHistory([
            ...history,
            {
              q: question,
              a: data.answer,
              confidence: data.confidence,
            },
          ]);
          setQuestion('');
        },
      }
    );
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask Taty something..."
          className="flex-1 border rounded px-3 py-2"
          disabled={isPending}
        />
        <button
          onClick={handleAsk}
          disabled={isPending}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          {isPending ? 'Asking...' : 'Ask'}
        </button>
      </div>

      <div className="space-y-3">
        {history.map((item, i) => (
          <div key={i} className="border-l-4 border-blue-500 pl-4">
            <p className="font-bold text-sm">{item.q}</p>
            <p className="text-gray-700 mt-1">{item.a}</p>
            <p className="text-xs text-gray-500 mt-1">
              Confidence: {(item.confidence * 100).toFixed(0)}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 5. Full Pipeline (Campaign Orchestrator)

```typescript
// components/CampaignOrchestrator.tsx
import { useFullPipeline } from '@/hooks/useContextiaServices';

export const CampaignOrchestrator = () => {
  const [formData, setFormData] = useState({
    companyId: '',
    companyUrl: '',
    campaignObjective: '',
    budget: 5000,
  });

  const { execute, isLoading, result } = useFullPipeline();

  const handleExecute = async () => {
    await execute(
      formData.companyId,
      formData.companyUrl,
      formData.campaignObjective,
      formData.budget
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Campaign Orchestrator</h2>

      <div className="space-y-4 mb-6">
        <input
          type="text"
          placeholder="Company ID"
          value={formData.companyId}
          onChange={(e) =>
            setFormData({ ...formData, companyId: e.target.value })
          }
          className="w-full border rounded px-3 py-2"
        />
        <input
          type="url"
          placeholder="Company URL"
          value={formData.companyUrl}
          onChange={(e) =>
            setFormData({ ...formData, companyUrl: e.target.value })
          }
          className="w-full border rounded px-3 py-2"
        />
        <input
          type="text"
          placeholder="Campaign Objective"
          value={formData.campaignObjective}
          onChange={(e) =>
            setFormData({ ...formData, campaignObjective: e.target.value })
          }
          className="w-full border rounded px-3 py-2"
        />
        <input
          type="number"
          placeholder="Budget"
          value={formData.budget}
          onChange={(e) =>
            setFormData({ ...formData, budget: Number(e.target.value) })
          }
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <button
        onClick={handleExecute}
        disabled={isLoading}
        className="w-full bg-green-500 text-white py-2 rounded font-bold"
      >
        {isLoading ? 'Processing...' : 'Execute Pipeline'}
      </button>

      {result && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded p-4">
          <h3 className="font-bold mb-2">Pipeline Result</h3>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
```

---

## ERROR HANDLING

### Global Error Boundary

```typescript
// components/ErrorBoundary.tsx
import { ReactNode } from 'react';

export class ErrorBoundary extends React.Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('API Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h2 className="font-bold text-red-700">API Error</h2>
          <p className="text-red-600 text-sm mt-1">
            {this.state.error?.message}
          </p>
          <button
            onClick={() => location.reload()}
            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm"
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Codes

| Status Code | Meaning | What to Do |
|-------------|---------|-----------|
| **200** | Success ✅ | Process response data |
| **400** | Bad Request ❌ | Check request parameters |
| **401** | Unauthorized ❌ | Redirect to login |
| **404** | Not Found ❌ | Check URL/endpoint |
| **405** | Method Not Allowed ❌ | Check HTTP method (GET/POST) |
| **500** | Server Error ❌ | Show retry button |

---

## AUTHENTICATION

Currently, authentication is handled via:
- `verify_resource_ownership()` in core/deps.py
- Check ownership before showing sensitive data

Future implementation:
```typescript
// Store JWT token after login
localStorage.setItem('token', jwtToken);

// Add to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## TESTING INTEGRATION

### Manual Test Script

```typescript
// scripts/test-api-integration.ts
import apiClient from '@/services/contexiaAPI';

async function testAPIIntegration() {
  console.log('Testing Contexia API Integration...\n');

  const companyId = 'ff1a8b7c-b0a1-422e-bc48-fac6242be027';

  try {
    // 1. Health
    console.log('1️⃣  Testing Health Check...');
    const health = await apiClient.get('/health');
    console.log('✅ Health:', health.data.status);

    // 2. Centinela
    console.log('\n2️⃣  Testing Centinela Alerts...');
    const alerts = await apiClient.get('/centinela/alerts', {
      params: { company_id: companyId },
    });
    console.log('✅ Alerts:', alerts.data.total_alerts);

    // 3. Pulso
    console.log('\n3️⃣  Testing Pulso Today...');
    const pulso = await apiClient.post('/pulso/today', {
      company_id: companyId,
    });
    console.log('✅ Pulso:', pulso.data.kpis);

    // 4. Taty
    console.log('\n4️⃣  Testing Taty Q&A...');
    const taty = await apiClient.post('/taty/ask', {
      question: 'Cual es el vencimiento de renta',
      company_id: companyId,
    });
    console.log('✅ Taty:', taty.data.answer.substring(0, 50) + '...');

    // 5. Full Pipeline
    console.log('\n5️⃣  Testing Full Pipeline...');
    const pipeline = await apiClient.post(
      '/agents/orchestrator/full-pipeline',
      {
        company_id: companyId,
        company_url: 'https://test.com',
        campaign_objective: 'test',
        budget: 5000,
      }
    );
    console.log('✅ Pipeline: Orchestration complete');

    console.log('\n✅ ALL TESTS PASSED');
  } catch (err) {
    console.error('❌ Test failed:', err);
  }
}

testAPIIntegration();
```

---

## TROUBLESHOOTING

### CORS Issues

If you see: `Access to XMLHttpRequest blocked by CORS policy`

**Solution:** CORS is already enabled in the backend for:
- http://localhost:5173 (Vite)
- http://localhost:3000 (Next.js)
- https://contexia.online (Production)

If you're using a different port, update `apps/backend/middleware_config.py`:

```python
ALLOWED_ORIGINS = [
    "http://localhost:YOUR_PORT",
    "https://contexia.online",
]
```

### Timeout Issues

If requests timeout:

1. Check backend health: `https://antigravity-app-production-175a.up.railway.app/api/v1/health`
2. Increase timeout in apiClient:
   ```typescript
   timeout: 30000, // 30 seconds
   ```
3. Add retry logic:
   ```typescript
   apiClient.defaults.httpAgent.maxRetries = 3;
   ```

### 400 Bad Request on Taty

**Important:** Send Taty request fields in this order:
```json
{
  "question": "your question",
  "company_id": "company-id"
}
```

NOT:
```json
{
  "company_id": "company-id",
  "question": "your question"
}
```

---

## Quick Start Template

```typescript
// pages/dashboard.tsx
import { CentinelaWidget } from '@/components/CentinelaWidget';
import { PulsoDashboard } from '@/components/PulsoDashboard';
import { TatyChat } from '@/components/TatyChat';
import { StatusIndicator } from '@/components/StatusIndicator';

export default function Dashboard() {
  const companyId = 'ff1a8b7c-b0a1-422e-bc48-fac6242be027';

  return (
    <div className="p-6 space-y-6">
      <StatusIndicator />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PulsoDashboard companyId={companyId} />
        <CentinelaWidget companyId={companyId} />
      </div>

      <TatyChat companyId={companyId} />
    </div>
  );
}
```

---

**Ready to connect!** Start with `useHealth()` to verify the connection works. 🚀
