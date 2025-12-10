import React from 'react';
import { APIModel } from '../../../types';
import { Cpu } from 'lucide-react';

interface ModelSelectorProps {
  selectedModel: string;
  onSelect: (id: string) => void;
  models: APIModel[];
  isLoading?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({ selectedModel, onSelect, models, isLoading }) => {
  if (isLoading) {
    return (
      <div className="mb-8 animate-pulse text-slate-400 text-sm">
        Loading models...
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="mb-8 p-4 bg-slate-50 border border-slate-200 rounded-lg text-center text-slate-500 text-sm">
        <p>No models available. Please check backend connection.</p>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
        <Cpu className="w-4 h-4 mr-2 text-medical-600" />
        生成模型 (Generation Model)
      </h3>

      <div className="grid grid-cols-1 gap-3">
        {models.map((model) => {
          const isSelected = selectedModel === model.id;
          const isEnabled = model.isEnabled;

          return (
            <div
              key={model.id}
              onClick={() => isEnabled && onSelect(model.id)}
              className={`
                relative flex items-center p-3 rounded-lg border-2 transition-all
                ${isEnabled ? 'cursor-pointer' : 'opacity-50 cursor-not-allowed bg-slate-100'}
                ${isSelected
                  ? 'border-medical-500 bg-medical-50/30'
                  : isEnabled ? 'border-transparent bg-white shadow-sm hover:border-slate-200' : 'border-transparent'}
              `}
            >
              {/* Radio Indicator */}
              <div className={`
                w-4 h-4 rounded-full border mr-3 flex items-center justify-center flex-shrink-0
                ${isSelected ? 'border-medical-500' : 'border-slate-300'}
              `}>
                {isSelected && <div className="w-2 h-2 rounded-full bg-medical-500" />}
              </div>

              <div className="flex-1">
                <div className="flex justify-between items-center mb-0.5">
                  <span className={`text-sm font-bold ${isSelected ? 'text-medical-800' : 'text-slate-700'}`}>
                    {model.name}
                  </span>
                  <span className={`
                    text-[10px] px-2 py-0.5 rounded-full font-medium
                    ${model.provider === 'Google' ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}
                  `}>
                    {model.provider}
                  </span>
                </div>
                {/* Description not always available in list API, rely on name/provider */}
                {!isEnabled && (
                  <p className="text-xs text-red-500 font-medium mt-1">
                    Not Configured (Missing API Key)
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};