import React from 'react';
import { Edit2, Trash2, ChevronRight } from 'lucide-react';
import { Scenario } from '../../../types';


const THEME_CONFIG: Record<string, { border: string; bg: string; badge: string }> = {
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-50',
    badge: 'bg-blue-100 text-blue-700'
  },
  purple: {
    border: 'border-purple-500',
    bg: 'bg-purple-50',
    badge: 'bg-purple-100 text-purple-700'
  },
  orange: {
    border: 'border-orange-500',
    bg: 'bg-orange-50',
    badge: 'bg-orange-100 text-orange-700'
  }
};

interface ScenarioCardProps {
  scenario: Scenario;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onSelect: (id: string) => void;
}

export const ScenarioCard: React.FC<ScenarioCardProps> = ({
  scenario,
  onEdit,
  onDelete,
  onSelect
}) => {
  const theme = THEME_CONFIG[scenario.theme];

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation(); // Stop click from reaching the card
    onEdit(scenario.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); // Stop click from reaching the card
    // Simply trigger the callback, let the parent handle the confirmation UI
    onDelete(scenario.id);
  };

  return (
    <div
      onClick={() => onSelect(scenario.id)}
      className={`
        relative flex flex-col
        bg-white rounded-xl p-4 mb-4
        border-l-[6px] ${theme.border}
        shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05)]
        active:bg-slate-50 transition-colors
        cursor-pointer
        group
      `}
    >
      {/* Header Row */}
      <div className="flex justify-between items-start mb-2">
        <div className="pr-2 flex-1">
          <h3 className="text-lg font-bold text-slate-800 leading-snug">
            {scenario.subtitle}
          </h3>
          <p className="text-xs text-slate-400 font-medium mt-0.5">
            {scenario.title}
          </p>
        </div>

        {/* Actions Menu - Increased touch targets and z-index */}
        <div className="flex items-center gap-1 pl-2 relative z-10">
          <button
            onClick={handleEdit}
            className="p-2.5 text-slate-400 hover:text-medical-600 hover:bg-medical-50 active:bg-medical-100 rounded-full transition-all"
            aria-label="编辑"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={handleDelete}
            className="p-2.5 text-slate-400 hover:text-red-600 hover:bg-red-50 active:bg-red-100 rounded-full transition-all"
            aria-label="删除"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Description */}
      <p className="text-slate-600 text-sm line-clamp-2 mb-3 leading-relaxed">
        {scenario.description}
      </p>

      {/* Footer Info */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-50">
        <div className="flex flex-wrap gap-2">
          {(scenario.tags || []).slice(0, 2).map((tag) => (
            <span
              key={tag}
              className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium ${theme.badge}`}
            >
              {tag}
            </span>
          ))}
        </div>

        <div className="flex items-center text-slate-400">
          <span className="text-[10px] mr-2 font-mono">
            {new Date(scenario.lastUpdated).toLocaleDateString('zh-CN')}
          </span>
          <ChevronRight className="w-4 h-4 text-slate-300" />
        </div>
      </div>
    </div>
  );
};