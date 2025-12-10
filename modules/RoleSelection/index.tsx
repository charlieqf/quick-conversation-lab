
import React, { useState, useEffect } from 'react';
import { ArrowLeft, Plus, Users, AlertTriangle, Loader2 } from 'lucide-react';
import { RoleCard } from './components/RoleCard';
import { Role } from '../../types';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';

interface RoleSelectionModuleProps {
  onBack: () => void;
  onNavigate: (view: 'role-editor' | 'session', roleId?: string) => void;
  scenarioId?: string; // The context scenario
}

export const RoleSelectionModule: React.FC<RoleSelectionModuleProps> = ({ onBack, onNavigate, scenarioId }) => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [deleteModalState, setDeleteModalState] = useState<{ isOpen: boolean, roleId: string | null }>({
    isOpen: false,
    roleId: null
  });

  const fetchRoles = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/data/roles');
      if (!res.ok) throw new Error('Failed to load roles');
      const data = await res.json();
      setRoles(data);
    } catch (err) {
      setError('无法加载角色数据');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleCreate = () => {
    onNavigate('role-editor');
  };

  const handleEdit = (id: string) => {
    onNavigate('role-editor', id);
  };

  const handleDeleteRequest = (id: string) => {
    setDeleteModalState({ isOpen: true, roleId: id });
  };

  const handleConfirmDelete = async () => {
    if (!deleteModalState.roleId) return;

    try {
      const res = await fetch(`/api/data/roles/${deleteModalState.roleId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        setRoles(prev => prev.filter(r => r.id !== deleteModalState.roleId));
      } else {
        alert('删除失败');
      }
    } catch (e) {
      console.error(e);
      alert('删除出错');
    }
    setDeleteModalState({ isOpen: false, roleId: null });
  };

  const handleSelectRole = (id: string) => {
    onNavigate('session', id);
  };

  const roleToDelete = roles.find(r => r.id === deleteModalState.roleId);

  if (loading && roles.length === 0) {
    return (
      <div className="flex flex-col h-full bg-slate-50 items-center justify-center">
        <Loader2 className="w-8 h-8 text-medical-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-full bg-slate-50 items-center justify-center">
        <AlertTriangle className="w-8 h-8 text-red-500 mb-2" />
        <p className="text-slate-500">{error}</p>
        <Button onClick={fetchRoles} variant="ghost" className="mt-4">重试</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-sm sticky top-0 z-10">
        <div className="flex items-center">
          <button onClick={onBack} className="text-slate-500 mr-3 hover:bg-slate-100 p-1.5 rounded-full transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-base font-bold text-slate-800">角色选择</h2>
            <p className="text-[10px] text-slate-400">选择陪练对象 (Doctor Persona)</p>
          </div>
        </div>
        <button
          onClick={handleCreate}
          className="w-8 h-8 bg-medical-50 text-medical-600 rounded-full flex items-center justify-center border border-medical-100 shadow-sm active:scale-95 transition-all"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 pb-20">
        {roles.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center opacity-60">
            <Users className="w-12 h-12 text-slate-300 mb-4" />
            <p className="text-sm text-slate-500">暂无角色，请点击右上角创建</p>
          </div>
        ) : (
          roles.map(role => (
            <RoleCard
              key={role.id}
              role={role}
              onEdit={handleEdit}
              onDelete={handleDeleteRequest}
              onSelect={handleSelectRole}
            />
          ))
        )}
      </div>

      {/* Delete Modal */}
      <Modal
        isOpen={deleteModalState.isOpen}
        onClose={() => setDeleteModalState({ isOpen: false, roleId: null })}
        title="删除角色"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDeleteModalState({ isOpen: false, roleId: null })}>取消</Button>
            <Button variant="danger" onClick={handleConfirmDelete}>确认删除</Button>
          </>
        }
      >
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <p className="text-slate-800 font-medium text-sm mb-1">
              确认删除“{roleToDelete?.nameCN}”?
            </p>
            <p className="text-slate-500 text-sm">
              此操作不可逆。相关的历史对话记录可能也会受到影响。
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
