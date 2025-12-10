
import React, { useState } from 'react';
import { Modal } from '../../../components/ui/Modal';
import { Button } from '../../../components/ui/Button';
import { UserProfile } from '../../../types';
import { User, Sparkles, Settings, RotateCw, ImageIcon } from 'lucide-react';
import { GoogleGenAI } from "@google/genai";

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  profile: UserProfile;
  onSave: (newProfile: UserProfile) => void;
}

export const UserProfileModal: React.FC<UserProfileModalProps> = ({ isOpen, onClose, profile, onSave }) => {
  const [formData, setFormData] = useState<UserProfile>(profile);
  const [isPromptConfigOpen, setIsPromptConfigOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Sync internal state when prop updates (e.g. reopening)
  React.useEffect(() => {
    if (isOpen) {
      setFormData(profile);
      setIsPromptConfigOpen(false);
    }
  }, [isOpen, profile]);

  const handleChange = (field: keyof UserProfile, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleGenerateAvatar = async () => {
    if (!formData.name) {
      alert("请先输入用户名称");
      return;
    }

    const apiKey = process.env.API_KEY;
    if (!apiKey) {
      alert("请先在设置页配置 API Key");
      return;
    }

    setIsGenerating(true);
    try {
      const ai = new GoogleGenAI({ apiKey });
      
      const prompt = (formData.avatarPrompt || 'A professional portrait...')
        .replace('{name}', formData.name);

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash-image',
        contents: { parts: [{ text: prompt }] }
      });

      if (response.candidates?.[0]?.content?.parts) {
        for (const part of response.candidates[0].content.parts) {
          if (part.inlineData) {
            const base64Data = part.inlineData.data;
            const mimeType = part.inlineData.mimeType || 'image/png';
            const imageUrl = `data:${mimeType};base64,${base64Data}`;
            handleChange('avatarImage', imageUrl);
            break;
          }
        }
      }
    } catch (e: any) {
      console.error("Avatar Gen Failed", e);
      alert("头像生成失败，请检查网络或 Key");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = () => {
    onSave(formData);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="编辑个人资料"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>取消</Button>
          <Button variant="primary" onClick={handleSave}>保存</Button>
        </>
      }
    >
      <div className="space-y-5">
        
        {/* Avatar Section */}
        <div className="flex items-center space-x-4">
          <div className="w-20 h-20 rounded-full bg-slate-100 border-2 border-slate-200 overflow-hidden flex-shrink-0 relative">
             {formData.avatarImage ? (
                <img src={formData.avatarImage} alt="Avatar" className="w-full h-full object-cover" />
             ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-300">
                   <User className="w-8 h-8" />
                </div>
             )}
             {isGenerating && (
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                   <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                </div>
             )}
          </div>
          
          <div className="flex flex-col space-y-2">
             <div className="flex items-center space-x-1">
               <Button 
                 variant="secondary"
                 className="h-8 text-xs px-3" 
                 onClick={handleGenerateAvatar}
                 isLoading={isGenerating}
                 icon={<ImageIcon className="w-3 h-3"/>}
               >
                 生成头像
               </Button>
               <button 
                  onClick={() => setIsPromptConfigOpen(!isPromptConfigOpen)}
                  className={`p-2 rounded-lg transition-colors ${isPromptConfigOpen ? 'bg-medical-50 text-medical-600' : 'text-slate-400 hover:bg-slate-100'}`}
                  title="配置生成提示词"
               >
                  <Settings className="w-4 h-4" />
               </button>
             </div>
             
             {formData.avatarImage && (
               <button 
                 onClick={() => handleChange('avatarImage', '')}
                 className="text-[10px] text-slate-400 hover:text-red-500 flex items-center pl-1"
               >
                 <RotateCw className="w-3 h-3 mr-1" /> 重置默认
               </button>
             )}
          </div>
        </div>

        {/* Prompt Config (Collapsible) */}
        {isPromptConfigOpen && (
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 animate-in slide-in-from-top-2">
             <label className="text-[10px] font-bold text-slate-500 mb-1 block">
                头像生成提示词 (Prompt Template)
             </label>
             <textarea 
                value={formData.avatarPrompt}
                onChange={(e) => handleChange('avatarPrompt', e.target.value)}
                className="w-full h-20 text-xs p-2 border border-slate-200 rounded focus:ring-1 focus:ring-medical-500 outline-none resize-none"
                placeholder="Describe your desired avatar..."
             />
             <p className="text-[10px] text-slate-400 mt-1">支持变量: <code>{`{name}`}</code></p>
          </div>
        )}

        {/* Name Input */}
        <div>
           <label className="text-xs font-bold text-slate-700 block mb-1">用户名称 (Display Name)</label>
           <div className="relative">
             <User className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
             <input 
               type="text" 
               value={formData.name}
               onChange={(e) => handleChange('name', e.target.value)}
               className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent outline-none"
               placeholder="e.g. Dr. Wang"
             />
           </div>
        </div>

      </div>
    </Modal>
  );
};
