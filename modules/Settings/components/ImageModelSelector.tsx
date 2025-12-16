
import React from 'react';
import { Image as ImageIcon } from 'lucide-react';

export interface ImageModel {
    id: string;
    name: string;
    description: string;
    badge?: string;
}

export const AVAILABLE_IMAGE_MODELS: ImageModel[] = [
    {
        id: 'imagen-4.0-generate-001',
        name: 'Imagen 4.0',
        description: 'Google Premium Image Generation. High fidelity and realism.',
        badge: 'High Quality'
    },
    {
        id: 'gemini-2.5-flash',
        name: 'Gemini 2.5 Flash',
        description: 'Fast and efficient generation.',
        badge: 'Budget Friendly'
    }
];

interface ImageModelSelectorProps {
    selectedModel: string;
    onSelect: (id: string) => void;
}

export const ImageModelSelector: React.FC<ImageModelSelectorProps> = ({ selectedModel, onSelect }) => {
    return (
        <div className="mb-8">
            <h3 className="text-sm font-bold text-slate-800 mb-3 flex items-center">
                <ImageIcon className="w-4 h-4 mr-2 text-medical-600" />
                图像生成模型 (Image Gen)
            </h3>

            <div className="grid grid-cols-1 gap-3">
                {AVAILABLE_IMAGE_MODELS.map((model) => {
                    const isSelected = selectedModel === model.id;
                    return (
                        <div
                            key={model.id}
                            onClick={() => onSelect(model.id)}
                            className={`
                relative flex items-center p-3 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected
                                    ? 'border-medical-500 bg-medical-50/30'
                                    : 'border-transparent bg-white shadow-sm hover:border-slate-200'}
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
                                    {model.badge && (
                                        <span className={`
                      text-[10px] px-2 py-0.5 rounded-full font-medium
                      ${model.id.includes('flash') ? 'bg-orange-100 text-orange-700' : 'bg-blue-100 text-blue-700'}
                    `}>
                                            {model.badge}
                                        </span>
                                    )}
                                </div>
                                <p className="text-xs text-slate-500">{model.description}</p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
