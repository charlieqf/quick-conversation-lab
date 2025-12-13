
import React, { useState } from 'react';
import { Settings, Users, BookOpen } from 'lucide-react';
import { ScenarioSelectionModule } from './modules/ScenarioSelection';
import { ScenarioEditorModule } from './modules/ScenarioEditor';
import { RoleSelectionModule } from './modules/RoleSelection';
import { RoleEditorModule } from './modules/RoleEditor';
import { ActiveSessionModule } from './modules/ActiveSession';
import { ReportModule } from './modules/Report';
import { SettingsModule } from './modules/Settings';
import { HistoryModule } from './modules/History';
import { AppView, SessionReportData, UserProfile } from './types';

const DEFAULT_USER_PROFILE: UserProfile = {
  name: 'Dr. User',
  avatarPrompt: 'A professional portrait of a doctor in a hospital setting, wearing a white coat, high quality, 4k, photorealistic.'
};

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('scenarios');
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);

  // User Profile State
  const [userProfile, setUserProfile] = useState<UserProfile>(DEFAULT_USER_PROFILE);

  // Load Profile from API on mount
  React.useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch('/api/users/profile');
        if (res.ok) {
          const data = await res.json();
          setUserProfile({
            name: data.username,
            avatarPrompt: data.settings?.avatarPrompt || DEFAULT_USER_PROFILE.avatarPrompt
          });
        }
      } catch (e) {
        console.error("Failed to load user profile", e);
      }
    };
    fetchProfile();
  }, []);

  const handleUpdateProfile = async (profile: UserProfile) => {
    // Optimistic Update
    setUserProfile(profile);

    try {
      // We need to fetch current settings first to not overwrite them, or we assume backend merges? 
      // Backend replaces the settings dict if provided. We should probably merge in frontend or backend.
      // For safely, let's just do a shallow merge if we had more settings.
      // But here we can't easily access other settings without fetching or lifting state.
      // STRATEGY: Fetch current profile to get settings, then update.
      const resVal = await fetch('/api/users/profile');
      let currentSettings = {};
      if (resVal.ok) {
        const d = await resVal.json();
        currentSettings = d.settings || {};
      }

      await fetch('/api/users/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: profile.name,
          settings: {
            ...currentSettings,
            avatarPrompt: profile.avatarPrompt
          }
        })
      });
    } catch (e) {
      console.error("Failed to save profile", e);
      alert("保存个人资料失败");
    }
  };

  // Unified navigation handler
  const handleNavigation = (view: AppView, id?: string) => {
    if (view === 'editor') {
      setSelectedScenarioId(id || null);
    } else if (view === 'roles') {
      setSelectedScenarioId(id || null); // Enter role selection for this scenario context
    } else if (view === 'role-editor') {
      setSelectedRoleId(id || null);
    } else if (view === 'session') {
      // Pass the selected role ID to session
      setSelectedRoleId(id || null);
    }

    setCurrentView(view);
  };

  const handleSessionComplete = async (data: SessionReportData) => {
    // Save to Backend
    try {
      const res = await fetch('/api/history', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        const savedSession = await res.json();
        setLastReportData(savedSession);
        setCurrentView('report');
      } else {
        console.error("Failed to save session", await res.text());
        // Fallback: still show report but warn?
        setLastReportData(data);
        setCurrentView('report');
        alert("保存会话失败，请检查网络连接");
      }
    } catch (e) {
      console.error("Failed to save session", e);
      setLastReportData(data);
      setCurrentView('report');
      alert("保存会话失败，请检查网络连接");
    }
  };

  const handleViewHistoryReport = (data: SessionReportData) => {
    setLastReportData(data);
    setCurrentView('report');
  };

  const handleResumeSession = (data: SessionReportData) => {
    // Resume logic if needed
    setSelectedScenarioId(data.scenarioId);
    setSelectedRoleId(data.roleId);
    setCurrentView('session');
  };

  return (
    <div className="h-screen w-full bg-slate-50 font-sans text-slate-900 flex flex-col overflow-hidden max-w-md mx-auto shadow-2xl border-x border-slate-200">

      {/* Main Content Area - Scrollable */}
      <main className="flex-1 overflow-y-auto no-scrollbar scroll-smooth bg-slate-50 relative">

        {/* Module: Scenario Selection */}
        {currentView === 'scenarios' && (
          <ScenarioSelectionModule
            userProfile={userProfile}
            onNavigate={(view, id) => handleNavigation(view, id)}
          />
        )}

        {/* Module: Scenario Editor */}
        {currentView === 'editor' && (
          <ScenarioEditorModule
            scenarioId={selectedScenarioId || undefined}
            onBack={() => setCurrentView('scenarios')}
          />
        )}

        {/* Module: Role Selection */}
        {currentView === 'roles' && (
          <RoleSelectionModule
            scenarioId={selectedScenarioId || undefined}
            onBack={() => setCurrentView('scenarios')}
            onNavigate={(view, id) => handleNavigation(view, id)}
          />
        )}

        {/* Module: Role Editor */}
        {currentView === 'role-editor' && (
          <RoleEditorModule
            roleId={selectedRoleId || undefined}
            onBack={() => setCurrentView('roles')}
          />
        )}

        {/* Module: Active Session */}
        {currentView === 'session' && selectedScenarioId && selectedRoleId && (
          <ActiveSessionModule
            scenarioId={selectedScenarioId}
            roleId={selectedRoleId}
            onExit={() => setCurrentView('scenarios')}
            onComplete={handleSessionComplete}
          />
        )}

        {/* Module: Report */}
        {currentView === 'report' && lastReportData && (
          <ReportModule
            data={lastReportData}
            onExit={() => setCurrentView('history')}
            onRetry={() => {
              // Re-enter session with same context
              handleResumeSession(lastReportData);
            }}
          />
        )}

        {/* Module: History */}
        {currentView === 'history' && (
          <HistoryModule
            userProfile={userProfile}
            onUpdateProfile={handleUpdateProfile}
            onViewReport={handleViewHistoryReport}
            onResume={handleResumeSession}
          />
        )}

        {/* Module: Settings */}
        {currentView === 'settings' && (
          <SettingsModule />
        )}
      </main>

      {/* Bottom Navigation Bar (Mobile Style) */}
      {(currentView === 'scenarios' || currentView === 'settings' || currentView === 'history') && (
        <nav className="bg-white border-t border-slate-200 h-16 flex-shrink-0 flex items-center justify-around px-2 pb-safe shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50 animate-in slide-in-from-bottom duration-300">
          <button
            onClick={() => handleNavigation('scenarios')}
            className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${currentView === 'scenarios'
              ? 'text-medical-600'
              : 'text-slate-400 hover:text-slate-600'
              }`}
          >
            <BookOpen className="w-6 h-6" strokeWidth={currentView === 'scenarios' ? 2.5 : 2} />
            <span className="text-[10px] font-medium">演练</span>
          </button>

          <button
            onClick={() => setCurrentView('history')}
            className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${currentView === 'history'
              ? 'text-medical-600'
              : 'text-slate-400 hover:text-slate-600'
              }`}
          >
            <Users className="w-6 h-6" strokeWidth={currentView === 'history' ? 2.5 : 2} />
            <span className="text-[10px] font-medium">我的</span>
          </button>

          <button
            onClick={() => handleNavigation('settings')}
            className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors ${currentView === 'settings'
              ? 'text-medical-600'
              : 'text-slate-400 hover:text-slate-600'
              }`}
          >
            <Settings className="w-6 h-6" strokeWidth={currentView === 'settings' ? 2.5 : 2} />
            <span className="text-[10px] font-medium">设置</span>
          </button>
        </nav>
      )}
    </div>
  );
};

export default App;
