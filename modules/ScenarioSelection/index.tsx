import React, { useState, useEffect } from 'react';
import { ScenarioHeader } from './components/ScenarioHeader';
import { ScenarioCard } from './components/ScenarioCard';
import { Scenario, UserProfile } from '../../types';
import { INITIAL_SCENARIOS } from '../../constants';
import { FileText, RefreshCw, AlertTriangle } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';

interface ScenarioSelectionModuleProps {
  userProfile: UserProfile;
  onNavigate: (view: 'editor' | 'roles', scenarioId?: string) => void;
}

export const ScenarioSelectionModule: React.FC<ScenarioSelectionModuleProps> = ({ userProfile, onNavigate }) => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  // State for delete confirmation modal
  const [deleteModalState, setDeleteModalState] = useState<{isOpen: boolean, scenarioId: string | null}>({
    isOpen: false,
    scenarioId: null
  });

  // Load data (simulating persistence)
  useEffect(() => {
    const saved = localStorage.getItem('quick_scenarios');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setScenarios(parsed);
      } catch (e) {
        // Fallback if JSON is corrupt
        setScenarios(INITIAL_SCENARIOS);
      }
    } else {
      setScenarios(INITIAL_SCENARIOS);
      localStorage.setItem('quick_scenarios', JSON.stringify(INITIAL_SCENARIOS));
    }
  }, []);

  const handleCreateNew = () => {
    onNavigate('editor');
  };

  const handleEdit = (id: string) => {
    onNavigate('editor', id);
  };

  // Step 1: Trigger Modal
  const handleRequestDelete = (id: string) => {
    setDeleteModalState({ isOpen: true, scenarioId: id });
  };

  // Step 2: Execute Delete
  const handleConfirmDelete = () => {
    if (!deleteModalState.scenarioId) return;
    
    setScenarios((prevScenarios) => {
      const updated = prevScenarios.filter(s => s.id !== deleteModalState.scenarioId);
      localStorage.setItem('quick_scenarios', JSON.stringify(updated));
      return updated;
    });
    
    setDeleteModalState({ isOpen: false, scenarioId: null });
  };

  const handleSelect = (id: string) => {
    onNavigate('roles', id);
  };

  const handleResetDefaults = () => {
    if (window.confirm('确定要恢复所有默认场景吗？这将覆盖您当前的操作。')) {
      setScenarios(INITIAL_SCENARIOS);
      localStorage.setItem('quick_scenarios', JSON.stringify(INITIAL_SCENARIOS));
    }
  };

  // Helper to get scenario title for the modal
  const scenarioToDelete = scenarios.find(s => s.id === deleteModalState.scenarioId);

  return (
    <div className="min-h-full pb-20">
      <ScenarioHeader userProfile={userProfile} onNewScenario={handleCreateNew} />

      <div className="px-4 py-4">
        {scenarios.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
            <div className="bg-slate-100 w-20 h-20 rounded-full flex items-center justify-center mb-6 shadow-inner">
              <FileText className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">暂无场景</h3>
            <p className="text-slate-500 mt-2 mb-8 text-sm leading-relaxed max-w-xs">
              您已删除了所有场景。您可以创建新场景，或恢复系统默认的演示数据。
            </p>
            <div className="flex flex-col w-full max-w-[200px] gap-3">
              <button 
                onClick={handleCreateNew}
                className="bg-medical-600 text-white px-6 py-3 rounded-full text-sm font-semibold shadow-md shadow-medical-600/30 active:scale-95 transition-all"
              >
                创建新场景
              </button>
              <button 
                onClick={handleResetDefaults}
                className="flex items-center justify-center text-slate-500 py-2 text-sm hover:text-medical-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-1.5" />
                恢复默认数据
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col">
            {scenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.id}
                scenario={scenario}
                onEdit={handleEdit}
                onDelete={handleRequestDelete}
                onSelect={handleSelect}
              />
            ))}
            <div className="text-center py-6">
              <span className="inline-block px-3 py-1 bg-slate-100 text-slate-400 text-[10px] rounded-full">
                共 {scenarios.length} 个场景
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deleteModalState.isOpen}
        onClose={() => setDeleteModalState({ isOpen: false, scenarioId: null })}
        title="确认删除"
        footer={
          <>
            <Button 
              variant="ghost" 
              onClick={() => setDeleteModalState({ isOpen: false, scenarioId: null })}
            >
              取消
            </Button>
            <Button 
              variant="danger" 
              onClick={handleConfirmDelete}
            >
              确认删除
            </Button>
          </>
        }
      >
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-slate-800 font-medium text-sm mb-1">
              您即将删除“{scenarioToDelete?.subtitle || '该场景'}”
            </p>
            <p className="text-slate-500 text-sm leading-relaxed">
              删除后将无法恢复相关的配置和历史记录。请确认是否继续？
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};