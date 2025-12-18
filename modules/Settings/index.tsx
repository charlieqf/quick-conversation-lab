import React, { useState, useEffect } from 'react';
import { ConnectionStatus } from './components/ConnectionStatus';
import { ModelSelector } from './components/ModelSelector';
import { VoiceSelector } from './components/VoiceSelector';
import { ImageModelSelector } from './components/ImageModelSelector';
import { UserSettings, APIModel, APIVoice } from '../../types';
import { useAuth } from '../../contexts/AuthContext';

const DEFAULT_SETTINGS: UserSettings = {
  apiKeyConfigured: false,
  apiReady: false,
  selectedModel: 'gemini',
  selectedVoice: 'Kore',
  selectedScenarioModel: 'gemini-2.5-flash',
  selectedImageModel: 'imagen-4.0-generate-001'
};

const SCENARIO_MODELS_FALLBACK: APIModel[] = [
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google', isEnabled: true, defaultVoice: '', supportsTranscription: false, description: 'Latest fast model (Fallback)' },
];

export const SettingsModule: React.FC = () => {
  const { token, user } = useAuth();
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [models, setModels] = useState<APIModel[]>([]);
  const [scenarioModels, setScenarioModels] = useState<APIModel[]>([]);
  const [voices, setVoices] = useState<APIVoice[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [loadingVoices, setLoadingVoices] = useState(false);

  // 1. Initial Load: Settings from API & Fetch Models
  useEffect(() => {
    if (!token) return;

    const loadSettingsAndModels = async () => {
      // Load Settings from API
      let apiSettings = {};
      try {
        const res = await fetch('/api/users/profile', {
          cache: 'no-store',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const profile = await res.json();
          apiSettings = profile.settings || {};
        }
      } catch (e) {
        console.error('Failed to load user profile settings', e);
      }

      const loadedSettings = {
        ...DEFAULT_SETTINGS,
        ...apiSettings
      };

      setSettings(prev => ({ ...prev, ...loadedSettings }));

      // Fetch Voice Models
      try {
        const res = await fetch('/api/models', {
          cache: 'no-store',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to load models');
        const data: APIModel[] = await res.json();
        setModels(data);

        // Update apiReady based on gemini (or ANY enabled model)
        const isReady = data.some(m => m.isEnabled);

        // If current selected model is not in list (or empty), pick first available
        if (data.length > 0) {
          const currentExists = data.find(m => m.id === loadedSettings.selectedModel);
          if (!currentExists) {
            const defaultModel = data.find(m => m.isEnabled) || data[0];
            // Update settings immediately if model changed due to availability
            const newSettings = { ...loadedSettings, selectedModel: defaultModel.id, apiReady: isReady };
            setSettings(newSettings);
            // Auto-save the fix
            updateSettings({ selectedModel: defaultModel.id });
          } else {
            setSettings(prev => ({ ...prev, apiReady: isReady }));
          }
        }
      } catch (e) {
        console.error("Failed to fetch models:", e);
      }

      // Fetch Scenario Models (New)
      try {
        const res = await fetch('/api/models/scenario', {
          cache: 'no-store',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          // Map simple dict to APIModel structure if needed, backend currently returns id, name, description
          // We need to ensure it matches APIModel interface
          const formatted: APIModel[] = data.map((m: any) => ({
            id: m.id,
            name: m.name,
            provider: 'Google', // Hardcoded for now as backend only lists Gemini
            isEnabled: true,
            defaultVoice: '',
            supportsTranscription: false,
            description: m.description,
            badge: m.badge
          }));
          setScenarioModels(formatted);
        } else {
          setScenarioModels(SCENARIO_MODELS_FALLBACK);
        }
      } catch (e) {
        console.warn("Failed to fetch scenario models, using fallback", e);
        setScenarioModels(SCENARIO_MODELS_FALLBACK);
      } finally {
        setLoadingModels(false);
      }
    };

    loadSettingsAndModels();
  }, [token]);

  // 2. Fetch Voices when Selected Model Changes
  useEffect(() => {
    if (!settings.selectedModel || !token) return;

    const fetchVoices = async () => {
      setLoadingVoices(true);
      try {
        // First get model details to see capabilities
        const res = await fetch(`/api/models/${settings.selectedModel}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const details = await res.json();
          // If model provides availableVoices in details
          if (details.availableVoices) {
            setVoices(details.availableVoices);

            // Ensure selected voice exists, else default
            const currentVoiceExists = details.availableVoices.find((v: any) => v.id === settings.selectedVoice);
            if (!currentVoiceExists && details.defaultVoice) {
              updateSettings({ selectedVoice: details.defaultVoice });
            }
          } else {
            setVoices([]);
          }
        }
      } catch (e) {
        console.error("Failed to fetch voices:", e);
      } finally {
        setLoadingVoices(false);
      }
    };

    if (models.length > 0) { // Only fetch if we have models loaded
      fetchVoices();
    }
  }, [settings.selectedModel, models, token]);

  // Save Settings when changed
  const updateSettings = async (updates: Partial<UserSettings>) => {
    if (!token) return;

    // 1. Optimistic Update
    const nextSettings = { ...settings, ...updates };
    setSettings(nextSettings);

    try {
      // 2. Fetch current profile settings to merge (safe update)
      const resGet = await fetch('/api/users/profile', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      let currentSettings = {};
      if (resGet.ok) {
        const p = await resGet.json();
        currentSettings = p.settings || {};
      }

      // 3. Construct Payload with Fallbacks
      // We prioritize: updates > nextSettings (Local State) > currentSettings (DB)
      // This ensures that our local state (what the user sees) is the source of truth for managed fields,
      // while currentSettings preserves any unmanaged fields from the DB.
      const payloadSettings = {
        ...currentSettings, // Base: DB state (preserves unknown/server-side-only fields)
        ...nextSettings,    // Overwrite: Local state (Model, Voice, Keys - ensures consistency)
        ...updates          // Overwrite: Explicit updates (redundant if in nextSettings, but safe)
      };

      // Ensure critical fields are present (redundant safety check, but harmless)
      if (!payloadSettings.selectedModel) payloadSettings.selectedModel = nextSettings.selectedModel;
      if (!payloadSettings.selectedVoice) payloadSettings.selectedVoice = nextSettings.selectedVoice;
      if (!payloadSettings.selectedImageModel) payloadSettings.selectedImageModel = nextSettings.selectedImageModel;
      if (!payloadSettings.selectedScenarioModel) payloadSettings.selectedScenarioModel = nextSettings.selectedScenarioModel;

      // 4. Push update
      await fetch('/api/users/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          settings: payloadSettings
        })
      });
    } catch (e) {
      console.error("Failed to save settings to API", e);
    }
  };

  const handleRefreshToken = () => {
    // Logic to trigger backend check or refresh
    // For now just reload page or re-fetch models
    window.location.reload();
  }

  return (
    <div className="bg-slate-50 min-h-full pb-20">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-4 sticky top-0 z-10 shadow-[0_1px_3px_0_rgba(0,0,0,0.05)]">
        <h1 className="text-xl font-bold text-slate-800">系统设置</h1>
        <p className="text-xs text-slate-500 mt-1">配置 AI 模型参数与个性化选项</p>
      </div>

      <div className="p-4">
        {/* Section 0: API Keys (BYOK) */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Custom API Keys (Optional)</h3>
          <div className="bg-white border rounded-lg p-3 space-y-3">

            {/* Google Gemini */}
            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-1">Google Gemini (API Key)</label>
              <input
                type="password"
                value={settings.customApiKey || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, customApiKey: e.target.value }))}
                onBlur={() => updateSettings({ customApiKey: settings.customApiKey })}
                placeholder="AIza..."
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono bg-slate-50"
              />
            </div>

            {/* OpenAI */}
            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-1">OpenAI (sk-...)</label>
              <input
                type="password"
                value={settings.customOpenaiKey || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, customOpenaiKey: e.target.value }))}
                onBlur={() => updateSettings({ customOpenaiKey: settings.customOpenaiKey })}
                placeholder="sk-..."
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono bg-slate-50"
              />
            </div>

            {/* Doubao */}
            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-1">ByteDance Doubao (Volcengine Key)</label>
              <input
                type="password"
                value={settings.customDoubaoKey || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, customDoubaoKey: e.target.value }))}
                onBlur={() => updateSettings({ customDoubaoKey: settings.customDoubaoKey })}
                placeholder="Standard API Key"
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono bg-slate-50"
              />
            </div>

            {/* Qwen */}
            <div>
              <label className="text-xs font-semibold text-slate-500 block mb-1">Alibaba Qwen (DashScope Key)</label>
              <input
                type="password"
                value={settings.customQwenKey || ''}
                onChange={(e) => setSettings(prev => ({ ...prev, customQwenKey: e.target.value }))}
                onBlur={() => updateSettings({ customQwenKey: settings.customQwenKey })}
                placeholder="sk-..."
                className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono bg-slate-50"
              />
            </div>

            <p className="text-[10px] text-slate-400 pt-1">
              Changes are saved automatically when you leave the field (lose focus).
              <br />
              Keys are stored securely in your database user profile.
            </p>
          </div>
        </div>

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 1: Connection */}
        {/* We reuse ConnectionStatus but with different logic or just hide it if unnecessary? 
            PRD says we should show connection status. 
            Let's pass isConnected based on apiReady */}
        <ConnectionStatus
          models={models}
          isLoading={loadingModels}
        />
        {/* Note: ConnectionStatus component might need slight text update but it is generic enough ("点击重试" vs "Connect") */}

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 1.5: Scenario Model (Moved to Top) */}
        {user?.role === 'admin' && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center">
              场景生成模型 (Scenario Gen)
              <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-600 text-[10px] rounded">Text/Multimodal</span>
            </h3>
            <ModelSelector
              selectedModel={settings.selectedScenarioModel || 'gemini-2.5-flash'}
              onSelect={(id) => updateSettings({ selectedScenarioModel: id })}
              models={scenarioModels}
              isLoading={loadingModels}
            />
            <p className="text-[10px] text-slate-400 mt-2">
              用于读取 PDF 和生成场景配置的纯文本/多模态模型。推荐使用 Gemini 2.5 Flash。
            </p>
          </div>
        )}

        {user?.role === 'admin' && <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />}

        {/* Section 1.8: Image Model (New) */}
        <ImageModelSelector
          selectedModel={settings.selectedImageModel || 'imagen-4.0-generate-001'}
          onSelect={(id) => updateSettings({ selectedImageModel: id })}
        />

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 2: Real-time Voice Model */}
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center">
            实时语音模型 (Real-time Voice)
            <span className="ml-2 px-1.5 py-0.5 bg-green-100 text-green-600 text-[10px] rounded">Audio Native</span>
          </h3>
          <ModelSelector
            selectedModel={settings.selectedModel}
            onSelect={(id) => updateSettings({ selectedModel: id })}
            models={models}
            isLoading={loadingModels}
          />
        </div>

        {/* Section 3: Voice (Legacy 2.5 was here, moved up) */}

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 3: Voice */}
        <VoiceSelector
          modelId={settings.selectedModel}
          selectedVoice={settings.selectedVoice}
          onSelect={(id) => updateSettings({ selectedVoice: id })}
          voices={voices}
          isLoading={loadingVoices}
        />

        <div className="mt-8 text-center">
          <p className="text-[10px] text-slate-400">
            Quick Coach v1.1.0
            <br />
            Powered by Gemini Native Audio (Python Backend)
          </p>
        </div>
      </div>
    </div>
  );
};