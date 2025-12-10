import React, { useState, useEffect } from 'react';
import { ConnectionStatus } from './components/ConnectionStatus';
import { ModelSelector } from './components/ModelSelector';
import { VoiceSelector } from './components/VoiceSelector';
import { UserSettings } from '../../types';
import { DEFAULT_SETTINGS } from '../../constants';

// Local interface to define the expected shape of aistudio object
interface AIStudioClient {
  hasSelectedApiKey: () => Promise<boolean>;
  openSelectKey: () => Promise<void>;
}

export const SettingsModule: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [isVerifying, setIsVerifying] = useState(false);

  // Helper to safely access aistudio from window
  const getAIStudio = (): AIStudioClient | undefined => {
    return (window as any).aistudio;
  };

  // Load Local Settings & Check API Status
  useEffect(() => {
    // 1. Load local preferences (model, voice selection)
    const saved = localStorage.getItem('quick_settings');
    let localSettings = DEFAULT_SETTINGS;
    
    if (saved) {
      try {
        localSettings = JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse settings', e);
      }
    }

    // 2. Check actual API Key status from the environment/window wrapper
    const checkApiConnection = async () => {
      const aiStudio = getAIStudio();
      // Safety check for development environments without the wrapper
      if (!aiStudio) {
        console.warn('Google AI Studio environment not detected. API features may be unavailable.');
        setSettings(localSettings);
        return;
      }

      try {
        const hasKey = await aiStudio.hasSelectedApiKey();
        setSettings({
          ...localSettings,
          apiKeyConfigured: hasKey
        });
      } catch (e) {
        console.error("Error checking API key status:", e);
        setSettings(localSettings);
      }
    };

    checkApiConnection();
  }, []);

  // Save Settings when changed
  const updateSettings = (updates: Partial<UserSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...updates };
      // Don't save apiKeyConfigured to local storage as it is derived from system state
      const { apiKeyConfigured, ...storageSafe } = next; 
      localStorage.setItem('quick_settings', JSON.stringify({
        ...storageSafe, 
        apiKeyConfigured: prev.apiKeyConfigured // Preserve the *current* valid state in storage logic if needed
      }));
      return next;
    });
  };

  const handleConnect = async () => {
    const aiStudio = getAIStudio();
    if (!aiStudio) {
      alert("错误：未检测到 AI Studio 环境。无法连接 API。");
      return;
    }

    setIsVerifying(true);
    try {
      // Open the Google AI Studio Key Selector
      await aiStudio.openSelectKey();
      
      // As per guidelines: Assume success after the promise resolves (race condition mitigation)
      // However, we can double check to be sure UI is consistent
      const hasKey = await aiStudio.hasSelectedApiKey();
      
      if (hasKey) {
        updateSettings({ apiKeyConfigured: true });
      } else {
        // If user cancelled or failed
        updateSettings({ apiKeyConfigured: false });
      }
    } catch (e) {
      console.error("Connection failed:", e);
      alert("连接验证失败，请重试。");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="bg-slate-50 min-h-full pb-20">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-4 sticky top-0 z-10 shadow-[0_1px_3px_0_rgba(0,0,0,0.05)]">
        <h1 className="text-xl font-bold text-slate-800">系统设置</h1>
        <p className="text-xs text-slate-500 mt-1">配置 AI 模型参数与个性化选项</p>
      </div>

      <div className="p-4">
        {/* Section 1: Connection */}
        <ConnectionStatus 
          isConnected={settings.apiKeyConfigured} 
          onConnect={handleConnect} 
        />

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 2: Model */}
        <ModelSelector 
          selectedModel={settings.selectedModel}
          onSelect={(id) => updateSettings({ selectedModel: id })}
        />

        <div className="h-px bg-slate-200 w-full mb-6 mx-auto opacity-50" />

        {/* Section 3: Voice */}
        <VoiceSelector 
          selectedVoice={settings.selectedVoice}
          onSelect={(id) => updateSettings({ selectedVoice: id })}
          apiKeyConfigured={settings.apiKeyConfigured}
        />

        <div className="mt-8 text-center">
          <p className="text-[10px] text-slate-400">
            Quick Coach v1.0.0 (Beta)
            <br />
            Designed for Medical Professionals
          </p>
        </div>
      </div>
    </div>
  );
};