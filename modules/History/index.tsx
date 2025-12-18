
import React, { useState, useEffect } from 'react';
import { History as HistoryIcon, Trash2, Edit2, User, AlertTriangle, LogOut } from 'lucide-react';
import { SessionReportData, Scenario, Role, UserProfile } from '../../types';
import { HistoryItem } from './components/HistoryItem';
import { UserProfileModal } from './components/UserProfileModal';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { useAuth } from '../../contexts/AuthContext';

interface HistoryModuleProps {
   userProfile: UserProfile;
   onUpdateProfile: (profile: UserProfile) => void;
   onViewReport: (data: SessionReportData) => void;
   onResume: (data: SessionReportData) => void;
}

export const HistoryModule: React.FC<HistoryModuleProps> = ({ userProfile, onUpdateProfile, onViewReport, onResume }) => {
   const { token, logout } = useAuth();
   const [sessions, setSessions] = useState<SessionReportData[]>([]);
   const [scenarios, setScenarios] = useState<Scenario[]>([]);
   const [roles, setRoles] = useState<Role[]>([]);

   // UI State
   const [isManageMode, setIsManageMode] = useState(false);
   const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
   const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
   const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);

   // Load Data
   const loadHistory = async () => {
      if (!token) return;
      try {
         const res = await fetch('/api/history', {
            headers: { 'Authorization': `Bearer ${token}` }
         });
         if (res.ok) {
            const data = await res.json();
            setSessions(data);
         }
      } catch (e) {
         console.error("Failed to load history", e);
      }
   };

   useEffect(() => {
      const loadMetadata = async () => {
         if (!token) return;
         try {
            const [sRes, rRes] = await Promise.all([
               fetch('/api/data/scenarios', { headers: { 'Authorization': `Bearer ${token}` } }),
               fetch('/api/data/roles', { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (sRes.ok) setScenarios(await sRes.json());
            if (rRes.ok) setRoles(await rRes.json());
         } catch (e) {
            console.error("Failed to load metadata", e);
         }
      };

      if (token) {
         loadHistory();
         loadMetadata();
      }
   }, [token]);

   const handleSeedData = async () => {
      if (!token) return;
      try {
         await fetch('/api/history/seed', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
         });
         loadHistory();
         alert("测试数据已生成！");
      } catch (e) {
         alert("生成失败");
      }
   }

   const handleDeleteOne = async (id: string) => {
      if (!token) return;
      if (window.confirm("确定要删除这条记录吗？")) {
         try {
            await fetch(`/api/history/${id}`, {
               method: 'DELETE',
               headers: { 'Authorization': `Bearer ${token}` }
            });
            // Optimistic update
            setSessions(sessions.filter(s => s.id !== id));
         } catch (e) {
            alert("删除失败");
         }
      }
   };

   const handleBatchDelete = () => {
      setIsDeleteModalOpen(true);
   };

   const confirmBatchDelete = async () => {
      if (!token) return;
      // Concurrent delete
      const idsToDelete = Array.from(selectedIds);
      await Promise.all(idsToDelete.map(id =>
         fetch(`/api/history/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
         })
      ));

      loadHistory();
      setIsManageMode(false);
      setSelectedIds(new Set());
      setIsDeleteModalOpen(false);
   };

   const toggleSelect = (id: string) => {
      const newSet = new Set(selectedIds);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      setSelectedIds(newSet);
   };

   const toggleManageMode = () => {
      setIsManageMode(!isManageMode);
      setSelectedIds(new Set());
   };

   return (
      <div className="flex flex-col h-full bg-slate-50 relative">
         {/* Header */}
         <div className="bg-white border-b border-slate-200 px-4 py-4 flex items-center justify-between shadow-sm sticky top-0 z-20">
            <div className="flex items-center space-x-3">
               {/* Profile Avatar / Icon */}
               <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 overflow-hidden flex-shrink-0">
                  {userProfile.avatarImage ? (
                     <img src={userProfile.avatarImage} alt="User" className="w-full h-full object-cover" />
                  ) : (
                     <div className="w-full h-full flex items-center justify-center text-slate-400">
                        <User className="w-5 h-5" />
                     </div>
                  )}
               </div>

               <div>
                  <div className="flex items-center gap-1.5">
                     <h2 className="text-base font-bold text-slate-800">{userProfile.name}</h2>
                     <button
                        onClick={() => setIsProfileModalOpen(true)}
                        className="p-1 text-slate-400 hover:text-medical-600 hover:bg-slate-100 rounded-full transition-colors"
                        aria-label="Edit Profile"
                     >
                        <Edit2 className="w-3.5 h-3.5" />
                     </button>
                  </div>
                  <p className="text-[10px] text-slate-400">Review your past simulations</p>
               </div>

               {/* Logout Button */}
               <button
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                  title="退出登录"
               >
                  <LogOut className="w-5 h-5" />
               </button>
            </div>

            <div className="flex items-center gap-2">
               {userProfile.role === 'admin' && (
                  <button
                     onClick={handleSeedData}
                     className="text-xs text-slate-400 hover:text-medical-600 px-2 py-1 bg-slate-50 rounded"
                     title="Generate Test Data"
                  >
                     +测试数据
                  </button>
               )}
               {sessions.length > 0 && (
                  <button
                     onClick={toggleManageMode}
                     className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${isManageMode ? 'bg-slate-100 text-slate-600' : 'text-medical-600 hover:bg-medical-50'}`}
                  >
                     {isManageMode ? '完成' : '管理'}
                  </button>
               )}
            </div>
         </div>

         {/* List */}
         <div className="flex-1 overflow-y-auto p-4 pb-24">
            {sessions.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-20 text-center opacity-60">
                  <HistoryIcon className="w-12 h-12 text-slate-300 mb-4" />
                  <p className="text-sm text-slate-500">暂无历史记录</p>
                  <p className="text-xs text-slate-400 mt-1">完成一次演练后将在此显示</p>
               </div>
            ) : (
               sessions.map(session => (
                  <HistoryItem
                     key={session.id}
                     session={session}
                     scenario={scenarios.find(s => s.id === session.scenarioId)}
                     role={roles.find(r => r.id === session.roleId)}
                     isManageMode={isManageMode}
                     isSelected={selectedIds.has(session.id)}
                     onToggleSelect={toggleSelect}
                     onDelete={handleDeleteOne}
                     onViewReport={onViewReport}
                     onResume={onResume}
                  />
               ))
            )}
         </div>

         {/* Batch Action Bar */}
         {isManageMode && (
            <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 pb-safe shadow-lg z-40 animate-in slide-in-from-bottom-5">
               <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-slate-500">已选择 {selectedIds.size} 项</span>
                  {selectedIds.size < sessions.length ? (
                     <button onClick={() => setSelectedIds(new Set(sessions.map(s => s.id)))} className="text-xs text-medical-600 font-medium">全选</button>
                  ) : (
                     <button onClick={() => setSelectedIds(new Set())} className="text-xs text-slate-400">取消全选</button>
                  )}
               </div>
               <Button
                  variant="danger"
                  className="w-full"
                  disabled={selectedIds.size === 0}
                  onClick={handleBatchDelete}
                  icon={<Trash2 className="w-4 h-4" />}
               >
                  删除选中记录
               </Button>
            </div>
         )}

         {/* Profile Edit Modal */}
         <UserProfileModal
            isOpen={isProfileModalOpen}
            onClose={() => setIsProfileModalOpen(false)}
            profile={userProfile}
            onSave={(newProfile) => {
               onUpdateProfile(newProfile);
               setIsProfileModalOpen(false);
            }}
         />

         {/* Batch Delete Confirmation Modal */}
         <Modal
            isOpen={isDeleteModalOpen}
            onClose={() => setIsDeleteModalOpen(false)}
            title="确认批量删除"
            footer={
               <>
                  <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)}>取消</Button>
                  <Button variant="danger" onClick={confirmBatchDelete}>确认删除</Button>
               </>
            }
         >
            <div className="flex items-start space-x-4">
               <div className="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
               </div>
               <div>
                  <p className="text-slate-800 font-medium text-sm mb-1">
                     您选择了 {selectedIds.size} 条训练记录
                  </p>
                  <p className="text-slate-500 text-sm leading-relaxed">
                     删除后这些数据将无法恢复。是否确认继续？
                  </p>
               </div>
            </div>
         </Modal>
      </div>
   );
};