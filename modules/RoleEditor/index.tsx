import React, { useState, useEffect } from 'react';
import { ArrowLeft, User, Sparkles, Hash, Save, Settings, Image as ImageIcon, RotateCw } from 'lucide-react';
import { Role, LogEntry, AIModelId } from '../../types';
import { PersonalitySliders } from './components/PersonalitySliders';
import { DebugConsole } from '../ScenarioEditor/components/DebugConsole'; // Reuse console
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { GoogleGenAI } from "@google/genai";

interface RoleEditorModuleProps {
  roleId?: string;
  onBack: () => void;
}

const DEFAULT_ROLE: Role = {
  id: '',
  name: '',
  nameCN: '',
  title: '',
  avatarSeed: Math.random().toString(36).substring(7),
  focusAreas: [],
  description: '',
  hostility: 50,
  verbosity: 50,
  skepticism: 50,
  systemPromptAddon: '',
  lastUpdated: new Date().toISOString()
};

const DEFAULT_GENERATION_INSTRUCTION = `Task: Create a specialized System Instruction for an AI roleplaying a medical professional.

Requirement:
Write a concise but potent paragraph (in Chinese) acting as a system instruction ("You are..."). 
1. Adopt the persona immediately.
2. Incorporate the personality traits defined by the sliders.
   - If Hostility is low (<30), be aggressive/strict.
   - If Skepticism is high (>70), constantly question the trainee's decisions.
3. Emphasize the focus areas.
4. Output ONLY the instruction text, no explanations.`;

const DEFAULT_AVATAR_PROMPT = `A professional, realistic photo portrait of a Chinese doctor named {name}, {title}. 
Appearance: professional medical white coat, stethoscope around neck, hospital setting background. 
Style: High quality, photorealistic, 4k, confident expression, head and shoulders shot. 
Context/Personality: {description}`;

export const RoleEditorModule: React.FC<RoleEditorModuleProps> = ({ roleId, onBack }) => {
  const [role, setRole] = useState<Role>(DEFAULT_ROLE);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGeneratingAvatar, setIsGeneratingAvatar] = useState(false);
  
  // Settings State for System Prompt
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [generationInstruction, setGenerationInstruction] = useState(DEFAULT_GENERATION_INSTRUCTION);

  // Settings State for Avatar Prompt
  const [isAvatarSettingsOpen, setIsAvatarSettingsOpen] = useState(false);
  const [avatarPromptTemplate, setAvatarPromptTemplate] = useState(DEFAULT_AVATAR_PROMPT);

  // Tag Modal State
  const [isTagModalOpen, setIsTagModalOpen] = useState(false);
  const [newTagValue, setNewTagValue] = useState('');

  useEffect(() => {
    if (roleId) {
      const saved = localStorage.getItem('quick_roles');
      if (saved) {
        const roles: Role[] = JSON.parse(saved);
        const found = roles.find(r => r.id === roleId);
        if (found) setRole(found);
      }
    } else {
      setRole({ ...DEFAULT_ROLE, id: Date.now().toString() });
    }
  }, [roleId]);

  const addLog = (message: string, type: LogEntry['type'] = 'info', detail?: string) => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [...prev, { timestamp, message, type, detail }]);
  };

  const updateField = (field: keyof Role, value: any) => {
    setRole(prev => ({ ...prev, [field]: value }));
  };

  const handleGeneratePrompt = async () => {
    if (!role.description && !role.nameCN) {
      addLog('请至少填写中文姓名或性格描述', 'error');
      return;
    }

    setIsGenerating(true);
    addLog('开始构建 System Prompt...', 'info');

    try {
      // 1. Config
      const apiKey = process.env.API_KEY;
      if (!apiKey) throw new Error("API Key required. Please configure in Settings.");
      
      let selectedModel: AIModelId = 'gemini-2.5-flash';
      // Try to read settings
      try {
         const settings = JSON.parse(localStorage.getItem('quick_settings') || '{}');
         if (settings.selectedModel) selectedModel = settings.selectedModel;
      } catch(e) {}

      const ai = new GoogleGenAI({ apiKey });

      // 2. Construct Prompt using the dynamic template
      // Note: role.focusAreas is explicitly included here
      const userPrompt = `${generationInstruction}

Context Data:
- Name: ${role.nameCN} (${role.name})
- Job Title: ${role.title}
- Personality Parameters (0-100):
  - Hostility (Low=Hostile, High=Friendly): ${role.hostility}
  - Verbosity (Low=Brief, High=Verbose): ${role.verbosity}
  - Skepticism (Low=Gullible, High=Skeptic): ${role.skepticism}
- Key Focus Areas: ${role.focusAreas.join(', ')}
- Natural Language Description: "${role.description}"
`;
      
      addLog('发送请求至 Wanyi API...', 'info', userPrompt);

      // 3. Call API (Stream)
      const responseStream = await ai.models.generateContentStream({
        model: selectedModel,
        contents: [{ role: 'user', parts: [{ text: userPrompt }] }]
      });

      let fullText = '';
      for await (const chunk of responseStream) {
        if (chunk.text) {
           fullText += chunk.text;
        }
      }
      
      addLog('生成完成', 'success', fullText);
      updateField('systemPromptAddon', fullText.trim());

    } catch (e: any) {
      addLog(`生成失败: ${e.message}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateAvatar = async () => {
    if (!role.nameCN && !role.title) {
      addLog('请先填写姓名或职位，以便生成准确的形象', 'error');
      alert('请先填写姓名或职位');
      return;
    }

    setIsGeneratingAvatar(true);
    addLog('正在调用 Wanyi Image Gen 生成真实头像...', 'info');

    try {
      const apiKey = process.env.API_KEY;
      if (!apiKey) throw new Error("API Key required. Please configure in Settings.");
      
      const ai = new GoogleGenAI({ apiKey });
      
      // Construct prompt using template and placeholders
      const prompt = avatarPromptTemplate
        .replace(/{name}/g, role.nameCN || '')
        .replace(/{title}/g, role.title || '')
        .replace(/{description}/g, role.description || 'Professional and experienced');

      addLog(`Sending Image Generation Request...`, 'info', prompt);

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash-image',
        contents: { parts: [{ text: prompt }] }
      });

      let foundImage = false;
      if (response.candidates?.[0]?.content?.parts) {
          for (const part of response.candidates[0].content.parts) {
            if (part.inlineData) {
                const base64Data = part.inlineData.data;
                const mimeType = part.inlineData.mimeType || 'image/png';
                const imageUrl = `data:${mimeType};base64,${base64Data}`;
                
                updateField('avatarImage', imageUrl);
                addLog('头像生成成功并已保存到角色', 'success');
                foundImage = true;
                break;
            }
          }
      }
      
      if (!foundImage) {
          throw new Error("模型未返回图片数据");
      }

    } catch (e: any) {
      addLog(`头像生成失败: ${e.message}`, 'error');
      console.error(e);
    } finally {
      setIsGeneratingAvatar(false);
    }
  };

  const handleSave = () => {
    if (!role.nameCN) {
      alert("请输入中文姓名");
      return;
    }

    const saved = localStorage.getItem('quick_roles');
    let roles: Role[] = saved ? JSON.parse(saved) : [];
    
    if (roleId) {
      roles = roles.map(r => r.id === role.id ? { ...role, lastUpdated: new Date().toISOString() } : r);
    } else {
      roles.push({ ...role, lastUpdated: new Date().toISOString() });
    }

    localStorage.setItem('quick_roles', JSON.stringify(roles));
    onBack();
  };

  const handleAddTag = () => {
    if (newTagValue.trim()) {
      updateField('focusAreas', [...role.focusAreas, newTagValue.trim()]);
      setNewTagValue('');
      setIsTagModalOpen(false);
    }
  };

  const diceBearUrl = `https://api.dicebear.com/9.x/adventurer/svg?seed=${role.avatarSeed}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffdfbf,ffd5dc`;
  const currentAvatar = role.avatarImage || diceBearUrl;

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-sm sticky top-0 z-20">
        <div className="flex items-center">
          <button onClick={onBack} className="text-slate-500 mr-3 hover:bg-slate-100 p-1.5 rounded-full transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h2 className="text-base font-bold text-slate-800">{roleId ? '编辑角色' : '新建角色'}</h2>
        </div>
        <Button variant="ghost" className="text-medical-600" onClick={handleSave}>保存</Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-10">
        
        {/* 1. Identity */}
        <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm space-y-5">
           <h3 className="text-sm font-bold text-slate-800 flex items-center">
             <User className="w-4 h-4 mr-2 text-medical-600" /> 基础信息 (Identity)
           </h3>

           {/* Avatar Section */}
           <div className="flex items-center space-x-4">
              <div className="w-20 h-20 rounded-full border-2 border-slate-100 shadow-inner overflow-hidden flex-shrink-0 bg-slate-50 relative group">
                <img src={currentAvatar} alt="Avatar" className="w-full h-full object-cover" />
                {isGeneratingAvatar && (
                   <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                      <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                   </div>
                )}
              </div>
              
              <div className="flex flex-col space-y-2">
                 <div className="flex items-center space-x-1">
                   <Button 
                     variant="secondary" 
                     onClick={handleGenerateAvatar}
                     isLoading={isGeneratingAvatar}
                     className="text-xs h-8 px-3"
                     icon={<ImageIcon className="w-3 h-3" />}
                   >
                     生成头像
                   </Button>
                   <button
                      onClick={() => setIsAvatarSettingsOpen(true)}
                      className="p-1.5 text-slate-400 hover:text-medical-600 hover:bg-slate-100 rounded-md transition-colors"
                      title="配置头像生成提示词"
                   >
                      <Settings className="w-4 h-4" />
                   </button>
                 </div>
                 
                 <button 
                   onClick={() => updateField('avatarImage', undefined)} // Reset to dicebear
                   className="text-[10px] text-slate-400 hover:text-red-500 flex items-center pl-1"
                 >
                   <RotateCw className="w-3 h-3 mr-1" /> 重置为卡通头像
                 </button>
              </div>
           </div>
           
           <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-500 block mb-1">中文姓名</label>
                <input 
                  type="text" 
                  value={role.nameCN} 
                  onChange={(e) => updateField('nameCN', e.target.value)}
                  className="w-full border-b border-slate-200 py-1 text-sm focus:border-medical-500 outline-none" 
                  placeholder="e.g. 张主任"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">英文代号</label>
                <input 
                   type="text" 
                   value={role.name} 
                   onChange={(e) => updateField('name', e.target.value)}
                   className="w-full border-b border-slate-200 py-1 text-sm focus:border-medical-500 outline-none" 
                   placeholder="e.g. Dr. Zhang"
                />
              </div>
           </div>
           
           <div>
              <label className="text-xs text-slate-500 block mb-1">职位/头衔</label>
              <input 
                 type="text" 
                 value={role.title} 
                 onChange={(e) => updateField('title', e.target.value)}
                 className="w-full border-b border-slate-200 py-1 text-sm focus:border-medical-500 outline-none" 
                 placeholder="e.g. 心内科主任医师"
              />
           </div>

           <div>
              <label className="text-xs text-slate-500 block mb-1">主要关注点 (Tags)</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {role.focusAreas.map((tag, i) => (
                  <span key={i} className="bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded flex items-center">
                    {tag} <button onClick={() => updateField('focusAreas', role.focusAreas.filter(t => t !== tag))} className="ml-1 text-slate-400">×</button>
                  </span>
                ))}
                <button 
                  onClick={() => setIsTagModalOpen(true)}
                  className="bg-medical-50 text-medical-600 text-xs px-2 py-1 rounded border border-dashed border-medical-200 hover:bg-medical-100"
                >
                  + Add
                </button>
              </div>
              <p className="text-[10px] text-slate-400">例如: 治疗费用, 副作用, 依从性。AI 将在对话中重点关注这些方面。</p>
           </div>
        </div>

        {/* 2. Personality Sliders */}
        <PersonalitySliders 
          hostility={role.hostility}
          verbosity={role.verbosity}
          skepticism={role.skepticism}
          onChange={(k, v) => updateField(k, v)}
        />

        {/* 3. Description & AI Generation */}
        <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm space-y-4">
           <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-slate-800 flex items-center">
                <Sparkles className="w-4 h-4 mr-2 text-purple-600" /> AI 指令生成
              </h3>
              <button 
                onClick={() => setIsSettingsOpen(true)}
                className="p-1.5 text-slate-400 hover:text-medical-600 hover:bg-slate-50 rounded-lg transition-colors"
                title="配置生成模板"
              >
                <Settings className="w-4 h-4" />
              </button>
           </div>
           
           <div>
              <label className="text-xs text-slate-500 block mb-1">自然语言描述 (用于生成指令)</label>
              <textarea 
                value={role.description}
                onChange={(e) => updateField('description', e.target.value)}
                className="w-full h-20 p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent resize-none"
                placeholder="例如：非常老派，讨厌新技术，喜欢打断别人说话..."
              />
           </div>

           <Button 
             variant="primary" 
             className="w-full" 
             onClick={handleGeneratePrompt}
             isLoading={isGenerating}
             icon={<Sparkles className="w-4 h-4" />}
           >
             更新 AI 指令 (System Prompt)
           </Button>

           {role.systemPromptAddon && (
             <div className="mt-4 animate-in fade-in duration-300">
               <label className="text-xs text-slate-500 block mb-1">生成的 System Prompt Preview:</label>
               <textarea 
                  value={role.systemPromptAddon}
                  onChange={(e) => updateField('systemPromptAddon', e.target.value)}
                  className="w-full h-32 p-3 text-xs font-mono bg-purple-50/30 border border-purple-100 rounded-lg text-slate-700 leading-relaxed resize-none focus:outline-none focus:border-purple-300"
               />
             </div>
           )}
        </div>

        {/* 4. Debug Console */}
        <DebugConsole logs={logs} onClear={() => setLogs([])} />
        
        <div className="h-8"></div>
      </div>

      {/* Settings Modal (System Prompt) */}
      <Modal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        title="AI 指令生成模板配置"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsSettingsOpen(false)}>关闭</Button>
            <Button variant="primary" onClick={() => setIsSettingsOpen(false)}>确认</Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
             定义 AI 在将您的角色参数转化为 System Prompt 时的逻辑模板。
          </p>
          <textarea 
             value={generationInstruction}
             onChange={(e) => setGenerationInstruction(e.target.value)}
             className="w-full h-64 p-3 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700 leading-relaxed"
          />
        </div>
      </Modal>

      {/* Settings Modal (Avatar Prompt) */}
      <Modal
        isOpen={isAvatarSettingsOpen}
        onClose={() => setIsAvatarSettingsOpen(false)}
        title="头像生成提示词配置"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsAvatarSettingsOpen(false)}>关闭</Button>
            <Button variant="primary" onClick={() => setIsAvatarSettingsOpen(false)}>确认</Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
             修改用于生成真实头像的 Prompt 模板。支持变量：<code className="bg-slate-100 px-1 rounded">{`{name}`}</code>, <code className="bg-slate-100 px-1 rounded">{`{title}`}</code>, <code className="bg-slate-100 px-1 rounded">{`{description}`}</code>
          </p>
          <textarea 
             value={avatarPromptTemplate}
             onChange={(e) => setAvatarPromptTemplate(e.target.value)}
             className="w-full h-64 p-3 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700 leading-relaxed"
          />
        </div>
      </Modal>

      {/* Add Tag Modal */}
      <Modal
        isOpen={isTagModalOpen}
        onClose={() => setIsTagModalOpen(false)}
        title="添加主要关注点 (Tag)"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsTagModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={handleAddTag}>添加</Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
             请输入该角色在对话中应重点关注的方面 (例如: "费用敏感", "注重循证", "情绪化")。
          </p>
          <input 
             type="text"
             value={newTagValue}
             onChange={(e) => setNewTagValue(e.target.value)}
             onKeyDown={(e) => { if (e.key === 'Enter') handleAddTag(); }}
             className="w-full border-b border-slate-200 py-2 text-sm focus:border-medical-500 outline-none"
             placeholder="输入标签名称..."
             autoFocus
          />
        </div>
      </Modal>
    </div>
  );
};