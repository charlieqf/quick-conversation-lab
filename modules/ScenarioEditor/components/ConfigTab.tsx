
import React, { useState } from 'react';
import { Save, Layers, CheckSquare, BookOpen, Hash, Settings, Plus, Trash2, Sparkles, X } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { Modal } from '../../../components/ui/Modal';
import { ScenarioConfig, ThemeColor, ScoringDimension } from '../../../types';
const THEME_CONFIG: Record<string, { bg: string }> = {
  blue: { bg: 'bg-blue-50' },
  purple: { bg: 'bg-purple-50' },
  orange: { bg: 'bg-orange-50' }
};


interface ConfigTabProps {
  config: ScenarioConfig;
  onChange: (newConfig: ScenarioConfig) => void;
  onSave: () => void;
  onLog: (msg: string, type: 'info' | 'error' | 'success', detail?: string) => void;
}

const DEFAULT_DIMENSION_PROMPT = `Task: Extract scoring dimensions from the text below.
Output: A JSON array of objects.
Format: [{"id": "uuid", "label": "Dimension Name (e.g. Communication)", "weight": 10, "description": "Short desc"}]
Requirements:
- Identify 3-6 key evaluation categories.
- Assign a weight (1-100) representing importance (total doesn't need to be 100, just relative).
- Output valid JSON only.

Text:
{criteria}`;

export const ConfigTab: React.FC<ConfigTabProps> = ({ config, onChange, onSave, onLog }) => {
  const [isDimensionModalOpen, setIsDimensionModalOpen] = useState(false);
  const [tempDimensions, setTempDimensions] = useState<ScoringDimension[]>([]);
  const [isGeneratingDims, setIsGeneratingDims] = useState(false);

  // Prompt Configuration State
  const [dimensionPromptTemplate, setDimensionPromptTemplate] = useState(DEFAULT_DIMENSION_PROMPT);
  const [isDimPromptSettingsOpen, setIsDimPromptSettingsOpen] = useState(false);

  const updateField = (field: keyof ScenarioConfig, value: any) => {
    onChange({ ...config, [field]: value });
  };

  const openDimensionModal = () => {
    setTempDimensions(config.scoringDimensions || []);
    setIsDimensionModalOpen(true);
  };

  const handleGenerateDimensions = async () => {
    if (!config.scoringCriteria) {
      alert("请先在下方文本框填写评分标准，AI 将基于内容生成维度。");
      return;
    }

    setIsGeneratingDims(true);
    onLog("开始分析评分标准并提取维度...", 'info');

    try {
      const prompt = dimensionPromptTemplate.replace('{criteria}', config.scoringCriteria);

      let selectedModel = 'gemini-2.5-flash';
      try {
        const res = await fetch('/api/users/profile');
        if (res.ok) {
          const p = await res.json();
          if (p.settings?.selectedScenarioModel) selectedModel = p.settings.selectedScenarioModel;
        }
      } catch (e) {
        console.warn("Failed to load settings", e);
      }
      onLog(`发送请求至 Backend API (Model: ${selectedModel})...`, 'info');

      const res = await fetch('/api/models/tools/scenario-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          contents: [{ parts: [{ text: prompt }] }],
          generation_config: { response_mime_type: 'application/json' }
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `API Error: ${res.status}`);
      }

      const data = await res.json();
      const text = data.text || '[]';
      onLog("接收到 API 响应", 'success', text);

      const parsed = JSON.parse(text);

      // Validate and format
      const newDims: ScoringDimension[] = parsed.map((d: any) => ({
        id: d.id || Date.now().toString() + Math.random(),
        label: d.label || 'Unknown',
        weight: Number(d.weight) || 10,
        description: d.description || ''
      }));

      setTempDimensions(newDims);
      onLog(`成功生成 ${newDims.length} 个维度`, 'success');

    } catch (e: any) {
      console.error("Failed to generate dimensions", e);
      onLog(`生成维度失败: ${e.message}`, 'error');
      alert("生成失败，请检查 Debug Console 获取详细信息。");
    } finally {
      setIsGeneratingDims(false);
    }
  };

  const handleAddDimension = () => {
    setTempDimensions([...tempDimensions, {
      id: Date.now().toString(),
      label: '',
      weight: 10,
      description: ''
    }]);
  };

  const handleRemoveDimension = (id: string) => {
    setTempDimensions(tempDimensions.filter(d => d.id !== id));
  };

  const handleUpdateDimension = (id: string, field: keyof ScoringDimension, value: any) => {
    setTempDimensions(tempDimensions.map(d =>
      d.id === id ? { ...d, [field]: value } : d
    ));
  };

  const handleSaveDimensions = () => {
    // Filter out empty ones
    const valid = tempDimensions.filter(d => d.label.trim() !== '');
    updateField('scoringDimensions', valid);
    onLog(`维度配置已更新 (${valid.length} items)`, 'info');
    setIsDimensionModalOpen(false);
  };

  return (
    <div className="space-y-6 pb-20 animate-in fade-in slide-in-from-right-4 duration-300">

      {/* 1. Basic Info */}
      <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm space-y-4 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1 h-full bg-slate-200"></div>
        <h3 className="text-sm font-bold text-slate-800 border-b border-slate-50 pb-2">元数据 (Metadata)</h3>

        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">标题 (Title)</label>
            <input
              type="text"
              value={config.title}
              onChange={(e) => updateField('title', e.target.value)}
              className="w-full border-b border-slate-200 py-1 text-sm focus:border-medical-500 focus:outline-none bg-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">中文副标题 (Subtitle)</label>
            <input
              type="text"
              value={config.subtitle}
              onChange={(e) => updateField('subtitle', e.target.value)}
              className="w-full border-b border-slate-200 py-1 text-base font-bold text-slate-800 focus:border-medical-500 focus:outline-none bg-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">场景描述 (Description)</label>
            <textarea
              rows={3}
              value={config.description}
              onChange={(e) => updateField('description', e.target.value)}
              className="w-full border border-slate-200 rounded p-2 text-xs text-slate-600 focus:border-medical-500 focus:outline-none bg-slate-50/50"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">标签 (Tags)</label>
            <div className="flex flex-wrap gap-2">
              {config.tags.map((tag, idx) => (
                <span key={idx} className="bg-slate-100 text-slate-600 px-2 py-1 rounded text-[10px] flex items-center">
                  <Hash className="w-3 h-3 mr-0.5 opacity-50" /> {tag}
                </span>
              ))}
              <button
                onClick={() => {
                  const newTag = prompt("输入新标签:");
                  if (newTag) updateField('tags', [...config.tags, newTag]);
                }}
                className="text-[10px] text-medical-600 border border-dashed border-medical-300 px-2 py-1 rounded hover:bg-medical-50"
              >
                + Add
              </button>
            </div>
          </div>

          {/* Theme Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">主题色 (Theme)</label>
            <div className="flex gap-3">
              {(['blue', 'purple', 'orange'] as ThemeColor[]).map(theme => (
                <button
                  key={theme}
                  onClick={() => updateField('theme', theme)}
                  className={`
                     w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all
                     ${THEME_CONFIG[theme].bg}
                     ${config.theme === theme ? `border-${theme}-500 scale-110 shadow-md` : 'border-transparent opacity-60'}
                   `}
                >
                  <div className={`w-3 h-3 rounded-full ${config.theme === theme ? `bg-${theme}-500` : `bg-${theme}-400`}`} />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 2. AI Config Sections - Detailed Text Prompts */}
      <div className="space-y-4">

        {/* Section A: Workflow */}
        <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-medical-500"></div>
          <h3 className="text-sm font-bold text-slate-800 mb-2 flex items-center">
            <Layers className="w-4 h-4 mr-2 text-medical-600" />
            1. 陪练会话流程 (Workflow Prompt)
          </h3>
          <p className="text-[10px] text-slate-400 mb-3">
            详细描述场景的各个阶段流转逻辑，包括每个阶段的触发条件、关键对话节点和预期行为。这将作为 AI 的核心指令。
          </p>
          <textarea
            value={config.workflow}
            onChange={(e) => updateField('workflow', e.target.value)}
            className="w-full h-48 p-3 text-xs bg-medical-50/20 border border-medical-100 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700 font-mono leading-relaxed resize-none"
            placeholder="等待生成详细流程描述..."
          />
        </div>

        {/* Section B: Knowledge Scope */}
        <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
          <h3 className="text-sm font-bold text-slate-800 mb-2 flex items-center">
            <BookOpen className="w-4 h-4 mr-2 text-blue-600" />
            2. 知识范围 (Knowledge Scope Prompt)
          </h3>
          <p className="text-[10px] text-slate-400 mb-3">
            定义本场景考核的所有医学知识点，包含理论依据和临床指南引用。
          </p>
          <textarea
            value={config.knowledgePoints}
            onChange={(e) => updateField('knowledgePoints', e.target.value)}
            className="w-full h-40 p-3 text-xs bg-blue-50/20 border border-blue-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-700 font-mono leading-relaxed resize-none"
            placeholder="等待生成知识点范围..."
          />
        </div>

        {/* Section C: Scoring */}
        <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-orange-500"></div>
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-800 flex items-center">
                <CheckSquare className="w-4 h-4 mr-2 text-orange-600" />
                3. 评分标准 (Scoring Prompt)
              </h3>
              <p className="text-[10px] text-slate-400 mb-1 mt-1">
                详细定义评分逻辑，包含具体扣分项和加分项的判断依据。
              </p>
            </div>
            <button
              onClick={openDimensionModal}
              className="p-1.5 text-slate-400 hover:text-medical-600 hover:bg-slate-100 rounded-md transition-colors"
              title="配置维度"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>

          <textarea
            value={config.scoringCriteria}
            onChange={(e) => updateField('scoringCriteria', e.target.value)}
            className="w-full h-40 p-3 text-xs bg-orange-50/20 border border-orange-100 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-slate-700 font-mono leading-relaxed resize-none"
            placeholder="等待生成评分标准..."
          />

          {config.scoringDimensions && config.scoringDimensions.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {config.scoringDimensions.map(d => (
                <span key={d.id} className="inline-flex items-center px-2 py-1 rounded bg-orange-100 text-orange-700 text-[10px] font-medium border border-orange-200">
                  {d.label} <span className="opacity-50 ml-1">({d.weight})</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Save Action */}
      <Button
        variant="primary"
        className="w-full py-3 sticky bottom-4 shadow-xl shadow-medical-900/10"
        icon={<Save className="w-4 h-4" />}
        onClick={onSave}
      >
        保存并退出
      </Button>

      {/* Dimensions Modal */}
      <Modal
        isOpen={isDimensionModalOpen}
        onClose={() => setIsDimensionModalOpen(false)}
        title="配置评分维度 (Scoring Dimensions)"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsDimensionModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={handleSaveDimensions} icon={<Save className="w-4 h-4" />}>确认并保存</Button>
          </>
        }
      >
        <div className="flex flex-col h-[60vh]">
          <div className="flex items-center justify-between mb-4 flex-shrink-0">
            <p className="text-xs text-slate-500">
              定义 Report 报告中使用的雷达图维度。
            </p>
            <div className="flex items-center space-x-1">
              <Button
                variant="secondary"
                onClick={handleGenerateDimensions}
                isLoading={isGeneratingDims}
                className="text-xs py-1 h-8 bg-purple-50 text-purple-700 hover:bg-purple-100 border-purple-100"
                icon={<Sparkles className="w-3 h-3" />}
              >
                生成
              </Button>
              <button
                onClick={() => setIsDimPromptSettingsOpen(true)}
                className="p-1.5 text-slate-400 hover:text-medical-600 hover:bg-slate-100 rounded-md transition-colors"
                title="配置生成提示词"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {tempDimensions.length === 0 && (
              <div className="text-center py-10 text-slate-400 text-xs border border-dashed rounded-lg">
                暂无维度，请点击“生成”或手动添加。
              </div>
            )}
            {tempDimensions.map((dim, index) => (
              <div key={dim.id} className="flex items-center space-x-2 bg-slate-50 p-2 rounded border border-slate-200 animate-in slide-in-from-left-2" style={{ animationDelay: `${index * 50}ms` }}>
                <div className="flex-1">
                  <input
                    type="text"
                    value={dim.label}
                    onChange={(e) => handleUpdateDimension(dim.id, 'label', e.target.value)}
                    className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-medical-500 outline-none"
                    placeholder="维度名称 (e.g. 沟通能力)"
                  />
                </div>
                <div className="w-16">
                  <input
                    type="number"
                    value={dim.weight}
                    onChange={(e) => handleUpdateDimension(dim.id, 'weight', Number(e.target.value))}
                    className="w-full bg-white border border-slate-200 rounded px-2 py-1 text-xs focus:ring-1 focus:ring-medical-500 outline-none text-center"
                    placeholder="权重"
                  />
                </div>
                <button
                  onClick={() => handleRemoveDimension(dim.id)}
                  className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex-shrink-0">
            <Button
              variant="ghost"
              onClick={handleAddDimension}
              className="w-full border border-dashed border-slate-300 text-slate-500 hover:text-medical-600 hover:border-medical-300"
              icon={<Plus className="w-4 h-4" />}
            >
              添加新维度
            </Button>
          </div>
        </div>
      </Modal>

      {/* Dimension Prompt Settings Modal */}
      <Modal
        isOpen={isDimPromptSettingsOpen}
        onClose={() => setIsDimPromptSettingsOpen(false)}
        title="配置维度生成提示词"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsDimPromptSettingsOpen(false)}>关闭</Button>
            <Button variant="primary" onClick={() => setIsDimPromptSettingsOpen(false)}>确认</Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-500">
            定义 AI 从评分标准中提取维度的 Prompt 模板。支持变量：<code className="bg-slate-100 px-1 rounded">{`{criteria}`}</code>
          </p>
          <textarea
            value={dimensionPromptTemplate}
            onChange={(e) => setDimensionPromptTemplate(e.target.value)}
            className="w-full h-64 p-3 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700 leading-relaxed"
          />
        </div>
      </Modal>
    </div>
  );
};
