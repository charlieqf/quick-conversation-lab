import React from 'react';
import { Edit2, Trash2, ArrowRight } from 'lucide-react';
import { Role } from '../../../types';

interface RoleCardProps {
  role: Role;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
}

export const RoleCard: React.FC<RoleCardProps> = ({ role, onEdit, onDelete, onSelect }) => {
  
  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(role.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(role.id);
  };

  // DiceBear Avatar URL (Using 9.x API) - Ghibli-esque style (adventurer)
  const diceBearUrl = `https://api.dicebear.com/9.x/adventurer/svg?seed=${role.avatarSeed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffdfbf,ffd5dc`;
  
  // Prioritize generated avatar if available
  const avatarSrc = role.avatarImage || diceBearUrl;

  return (
    <div 
      onClick={() => onSelect(role.id)}
      className="bg-white rounded-xl p-4 mb-3 border border-slate-100 shadow-sm relative overflow-hidden active:bg-slate-50 transition-all cursor-pointer group"
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-16 h-16 rounded-full bg-slate-50 border-2 border-white shadow-sm flex-shrink-0 overflow-hidden">
          <img src={avatarSrc} alt={role.name} className="w-full h-full object-cover" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-base font-bold text-slate-800 truncate">
                {role.nameCN} <span className="text-xs font-normal text-slate-400 ml-1">{role.name}</span>
              </h3>
              <p className="text-xs text-medical-600 font-medium mt-0.5 mb-2">{role.title}</p>
            </div>
          </div>
          
          {/* Tags */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {role.focusAreas.slice(0, 3).map((tag, i) => (
              <span key={i} className="px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded text-[10px] font-medium border border-slate-200">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

       {/* Bottom Info & Action */}
       <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-50">
          <div className="flex gap-2 text-[10px] text-slate-400 font-mono">
            <span>Hostility: {role.hostility}%</span>
            <span>Skepticism: {role.skepticism}%</span>
          </div>

          <div className="flex items-center gap-1">
             <button 
                onClick={handleEdit}
                className="p-2 text-slate-400 hover:text-medical-600 hover:bg-medical-50 rounded-full transition-colors"
             >
               <Edit2 className="w-3.5 h-3.5" />
             </button>
             <button 
                onClick={handleDelete}
                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
             >
               <Trash2 className="w-3.5 h-3.5" />
             </button>
             <div className="w-px h-3 bg-slate-200 mx-1"></div>
             <button className="text-xs font-bold text-medical-600 flex items-center pl-1">
                开始 <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
             </button>
          </div>
       </div>
    </div>
  );
};