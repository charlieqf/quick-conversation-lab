import React, { useState, useEffect } from 'react';
import { ScenarioHeader } from './components/ScenarioHeader';
import { ScenarioCard } from './components/ScenarioCard';
import { Scenario, UserProfile } from '../../types';
import { FileText, RefreshCw, AlertTriangle, Loader2 } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';

interface ScenarioSelectionModuleProps {
  userProfile: UserProfile;
  onNavigate: (view: 'editor' | 'roles', scenarioId?: string) => void;
}

export const ScenarioSelectionModule: React.FC<ScenarioSelectionModuleProps> = ({ userProfile, onNavigate }) => {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for delete confirmation modal
  const [deleteModalState, setDeleteModalState] = useState<{ isOpen: boolean, scenarioId: string | null }>({
    isOpen: false,
    scenarioId: null
  });

  const fetchScenarios = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/data/scenarios');
      if (!res.ok) throw new Error('Failed to load scenarios');
      const data = await res.json();
      setScenarios(data);
    } catch (err) {
      setError('无法加载场景数据，请重试');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const handleCreateNew = () => {
    onNavigate('editor'); // Editor will need to handle POST/PUT
  };

  const handleEdit = (id: string) => {
    onNavigate('editor', id);
  };

  const handleRequestDelete = (id: string) => {
    setDeleteModalState({ isOpen: true, scenarioId: id });
  };

  const handleConfirmDelete = async () => {
    if (!deleteModalState.scenarioId) return;

    try {
      const res = await fetch(`/api/data/scenarios/${deleteModalState.scenarioId}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        setScenarios(prev => prev.filter(s => s.id !== deleteModalState.scenarioId));
      } else {
        alert('删除失败');
      }
    } catch (e) {
      console.error(e);
      alert('删除出错');
    }

    setDeleteModalState({ isOpen: false, scenarioId: null });
  };

  const handleSelect = (id: string) => {
    onNavigate('roles', id);
  };

  const handleResetDefaults = async () => {
    if (window.confirm('确定要恢复所有默认场景吗？这将覆盖您当前的操作并重置数据。')) {
      try {
        setLoading(true);
        // Call backend seed with reset
        const res = await fetch('/api/data/seed_defaults?reset=true', { method: 'POST' });
        if (res.ok) {
          fetchScenarios(); // Reload
        } else {
          alert('重置失败');
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
  };

  const scenarioToDelete = scenarios.find(s => s.id === deleteModalState.scenarioId);

  if (loading && scenarios.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-medical-600 animate-spin" />
        <span className="ml-3 text-slate-500">加载中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px] flex-col">
        <AlertTriangle className="w-10 h-10 text-red-500 mb-2" />
        <p className="text-slate-600">{error}</p>
        <Button onClick={fetchScenarios} className="mt-4" variant="primary">重试</Button>
      </div>
    );
  }

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