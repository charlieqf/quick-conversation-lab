import React, { useState, useEffect } from 'react';
import { ConnectionStatus } from './components/ConnectionStatus';
import { ModelSelector } from './components/ModelSelector';
import { VoiceSelector } from './components/VoiceSelector';
import { UserSettings, APIModel, APIVoice } from '../../types';
const DEFAULT_SETTINGS: UserSettings = {
  apiKeyConfigured: false,
  apiReady: false,
  selectedModel: 'gemini',
  selectedVoice: 'Kore'
};

export const SettingsModule: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [models, setModels] = useState<APIModel[]>([]);
  const [voices, setVoices] = useState<APIVoice[]>([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [loadingVoices, setLoadingVoices] = useState(false);

  // 1. Initial Load: Settings from LocalStorage & Fetch Models
  useEffect(() => {
    const loadSettingsAndModels = async () => {
      // Load Local Settings
      const saved = localStorage.getItem('quick_settings');
      let localSettings = DEFAULT_SETTINGS;
      if (saved) {
        try {
          localSettings = JSON.parse(saved);
        } catch (e) {
          console.error('Failed to parse settings', e);
        }
      }
      setSettings(localSettings);

      // Fetch Models
      try {
        const res = await fetch('/api/models', { cache: 'no-store' }); // Uses proxy
        if (!res.ok) throw new Error('Failed to load models');
        const data: APIModel[] = await res.json();
        setModels(data);

        // Update apiReady based on gemini (or ANY enabled model)
        const isReady = data.some(m => m.isEnabled);

        // If current selected model is not in list (or empty), pick first available
        if (data.length > 0) {
          const currentExists = data.find(m => m.id === localSettings.selectedModel);
          if (!currentExists) {
            const defaultModel = data.find(m => m.isEnabled) || data[0];
            // Update settings immediately if model changed due to availability
            const newSettings = { ...localSettings, selectedModel: defaultModel.id, apiReady: isReady };
            setSettings(newSettings);
            localStorage.setItem('quick_settings', JSON.stringify(newSettings));
          } else {
            setSettings(prev => ({ ...prev, apiReady: isReady }));
          }
        }
      } catch (e) {
        console.error("Failed to fetch models:", e);
      } finally {
        setLoadingModels(false);
      }
    };

    loadSettingsAndModels();
  }, []);

  // 2. Fetch Voices when Selected Model Changes
  useEffect(() => {
    if (!settings.selectedModel) return;

    const fetchVoices = async () => {
      setLoadingVoices(true);
      try {
        // First get model details to see capabilities
        const res = await fetch(`/api/models/${settings.selectedModel}`);
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
  }, [settings.selectedModel, models]);

  // Save Settings when changed
  const updateSettings = (updates: Partial<UserSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...updates };
      // Don't save transient flags if any (apiReady is derived usually, but here we can stick it for now or ignore)
      // Actually we just save everything relevant
      localStorage.setItem('quick_settings', JSON.stringify(next));
      return next;
    });
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

        {/* Section 2: Model */}
        <ModelSelector
          selectedModel={settings.selectedModel}
          onSelect={(id) => updateSettings({ selectedModel: id })}
          models={models}
          isLoading={loadingModels}
        />

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 3: Voice */}
        <VoiceSelector
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