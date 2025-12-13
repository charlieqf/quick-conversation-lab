
import React, { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Settings as SettingsIcon } from 'lucide-react';
import { ScriptTab } from './components/ScriptTab';
import { ConfigTab } from './components/ConfigTab';
import { DebugConsole } from './components/DebugConsole';
import { ScenarioConfig, LogEntry, AttachedFile, AIModelId } from '../../types';

interface ScenarioEditorModuleProps {
  scenarioId?: string; // If editing existing
  onBack: () => void;
}

const DEFAULT_CONFIG: ScenarioConfig = {
  title: 'New Scenario',
  subtitle: '未命名场景',
  description: '请在脚本页生成内容...',
  tags: ['未分类'],
  theme: 'blue',
  workflow: '等待生成场景流程描述...',
  knowledgePoints: '等待生成知识点范围...',
  scoringCriteria: '等待生成评分标准...',
  scoringDimensions: []
};

const DEFAULT_SYSTEM_PROMPT = `你是一名资深医学教育专家。你的任务是阅读提供的【医学培训脚本】（可能是PDF文档或文本），并提取关键信息以构建一个结构化的模拟场景配置。

请严格遵守以下规则：
1. **深度解析文档**：分析脚本中的对话、旁白、动作指示。如果是 PDF 表格形式，请务必还原表格中定义的每一个细微步骤、分支逻辑和关键指标。
2. **生成详细提示词**：对于“流程”、“知识点”和“评分标准”，**不要**仅仅列出简单的条目。你需要生成一段完整的、详细的 Prompt（提示词）文本。这段文本将直接作为 AI 扮演病人时的指令 (System Instruction)。
3. **保留原始内容**：尽最大可能保留 PDF 中识别出的具体数值、药物剂量、操作规范等细节。
4. **输出 JSON 格式**：输出必须是合法的 JSON 格式。

JSON 结构要求（注意 workflow, knowledgePoints, scoringCriteria 必须是详细的长文本字符串，支持 Markdown 换行）：
{
  "title": "英文技术术语名称",
  "subtitle": "中文显示名称",
  "description": "场景简述，100字以内",
  "tags": ["关键词1", "关键词2"],
  "theme": "one of 'blue', 'purple', 'orange'",
  "workflow": "详细描述场景的完整流程。包含：开场设定、不同阶段的触发条件、患者在不同情境下的具体反应逻辑、对话引导方向等。请以清晰的 Markdown 格式编写，保留所有流程分支细节。",
  "knowledgePoints": "详细列出本场景考核的医学知识点范围。包含：理论依据、临床指南引用、禁忌症提醒、药物作用机理等。请以详细的文本形式呈现。",
  "scoringCriteria": "详细定义评分标准。包含：具体的考核维度、扣分项、加分项、关键行为锚点（Behavioral Anchors）。请确保每个评分点都有明确的判断依据。"
}`;

export const ScenarioEditorModule: React.FC<ScenarioEditorModuleProps> = ({ scenarioId, onBack }) => {
  const [activeTab, setActiveTab] = useState<'script' | 'config'>('script');
  const [scriptContent, setScriptContent] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [generatedConfig, setGeneratedConfig] = useState<ScenarioConfig>(DEFAULT_CONFIG);
  const [isGenerating, setIsGenerating] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);

  // Load existing data if editing
  useEffect(() => {
    const loadScenario = async () => {
      if (scenarioId) {
        setIsGenerating(true); // Re-use spinner or add a loading state
        try {
          const res = await fetch(`/api/data/scenarios/${scenarioId}`);
          if (res.ok) {
            const found = await res.json();
            setGeneratedConfig({
              title: found.title || '',
              subtitle: found.subtitle || '',
              description: found.description || '',
              tags: found.tags || [],
              theme: found.theme || 'blue',
              workflow: found.workflow || '',
              knowledgePoints: found.knowledgePoints || '',
              scoringCriteria: found.scoringCriteria || '',
              scoringDimensions: found.scoringDimensions || []
            });
            if (found.scriptContent) {
              setScriptContent(found.scriptContent);
            }
            if (found.generationPrompt) {
              setSystemPrompt(found.generationPrompt);
            }
          } else {
            addLog('加载场景失败: ' + res.statusText, 'error');
          }
        } catch (e) {
          console.error("Failed to load scenario data", e);
          addLog('加载场景失败', 'error');
        } finally {
          setIsGenerating(false);
        }
      }
    };
    loadScenario();
  }, [scenarioId]);

  const addLog = (message: string, type: LogEntry['type'] = 'info', detail?: string) => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [...prev, { timestamp, message, type, detail }]);
  };

  // Helper to extract JSON from mixed text and attempt repair
  const extractAndRepairJSON = (text: string): any => {
    // 1. Locate the outer braces
    const firstOpen = text.indexOf('{');
    const lastClose = text.lastIndexOf('}');

    if (firstOpen === -1 || lastClose === -1 || lastClose <= firstOpen) {
      throw new Error("Cannot find valid JSON object (missing braces).");
    }

    let jsonCandidate = text.substring(firstOpen, lastClose + 1);

    // 2. Remove Markdown code blocks
    jsonCandidate = jsonCandidate.replace(/```json/g, '').replace(/```/g, '');

    // 3. Attempt Parse
    try {
      return JSON.parse(jsonCandidate);
    } catch (e) {
      console.warn("Standard parse failed, attempting repair...");
      // Repair: Remove trailing commas
      const fixedTrailingCommas = jsonCandidate.replace(/,\s*([\]}])/g, '$1');
      try {
        return JSON.parse(fixedTrailingCommas);
      } catch (e2) {
        throw e;
      }
    }
  };

  const handleGenerate = async () => {
    if (!scriptContent.trim() && attachedFiles.length === 0) {
      addLog('错误：请至少上传文件或输入脚本内容。', 'error');
      return;
    }

    setIsGenerating(true);
    setGeneratedConfig(prev => ({ ...prev, description: 'AI 正在分析生成中...' }));

    // Determine Model from Settings (Load from API)
    let selectedModel = 'gemini-2.5-flash';
    try {
      const res = await fetch('/api/users/profile');
      if (res.ok) {
        const p = await res.json();
        if (p.settings?.selectedScenarioModel) {
          selectedModel = p.settings.selectedScenarioModel;
        }
      }
    } catch (e) {
      console.warn('Failed to load settings', e);
    }

    const modelDisplay = `${selectedModel} (Backend)`;
    addLog(`初始化 AI 模型 (${modelDisplay})...`, 'info');

    try {
      let contents: any[] = [];
      let logPromptDetail = "";

      // Smart Mode Selection:
      const hasExtractedText = scriptContent.trim().length > 50;
      const useMultimodalMode = attachedFiles.length > 0 && !hasExtractedText;

      // BRANCH 1: Multimodal File Mode
      if (useMultimodalMode) {
        addLog(`检测到附件且无提取文本，启用多模态文件分析模式 (Base64)。`, 'info');

        const fileInstruction = `
请执行以下步骤来分析提供的 PDF/文件内容：
1. **逐一识别内容**：仔细阅读附件文件，特别是如果是 PDF 表格，请还原表格中的流程步骤、对话内容和评分点。
2. **模式识别**：分析医学案例的结构，识别"病情发展"->"干预"->"反馈"的模式。
3. **生成详细配置**：根据 System Instruction 的要求，将识别到的内容转化为指定的 JSON 格式。请确保 workflow, knowledgePoints, scoringCriteria 是非常详细的文本描述，不要丢失 PDF 中的细节。

System Instruction:
${systemPrompt}
`;
        const parts: any[] = [{ text: fileInstruction }];

        // Attach files as inlineData
        attachedFiles.forEach(file => {
          parts.push({
            inlineData: {
              mimeType: file.mimeType,
              data: file.data
            }
          });
          logPromptDetail += `[File: ${file.name} (${file.mimeType})]\n`;
        });

        contents = [{ role: 'user', parts: parts }];

      } else {
        // BRANCH 2: Text Only Mode
        if (attachedFiles.length > 0) {
          addLog(`检测到 ${attachedFiles.length} 个附件的提取文本，启用纯文本分析模式 (已优化 Payload)。`, 'success');
        } else {
          addLog('启用纯文本分析模式。', 'info');
        }

        const fullUserPrompt = `
<system_instruction>
${systemPrompt}
</system_instruction>

<training_script>
${scriptContent}
</training_script>
`;
        contents = [{ role: 'user', parts: [{ text: fullUserPrompt }] }];
        logPromptDetail = fullUserPrompt.substring(0, 500) + "... (truncated)";
      }

      addLog(`Prompt 构建完成。`, 'info', logPromptDetail);
      addLog(`正在请求后端生成接口 (${selectedModel})...`, 'info');

      // Call Backend Proxy
      // Note: Backend handles API Key securely
      const response = await fetch('/api/models/tools/scenario-generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: selectedModel,
          contents: contents
        })
      });

      if (!response.ok) {
        const errDetail = await response.text();
        throw new Error(`Server Error (${response.status}): ${errDetail}`);
      }

      const data = await response.json();
      const fullText = data.text; // Backend returns { text: "..." }

      addLog(`生成完成 (共 ${fullText.length} 字符)。开始解析...`, 'info', fullText);

      try {
        const parsed = extractAndRepairJSON(fullText);

        const merged: ScenarioConfig = {
          ...DEFAULT_CONFIG,
          ...parsed,
          tags: Array.isArray(parsed.tags) ? parsed.tags : DEFAULT_CONFIG.tags,
          // Ensure strings for detailed text fields
          workflow: typeof parsed.workflow === 'string' ? parsed.workflow : JSON.stringify(parsed.workflow, null, 2),
          knowledgePoints: typeof parsed.knowledgePoints === 'string' ? parsed.knowledgePoints : JSON.stringify(parsed.knowledgePoints, null, 2),
          scoringCriteria: typeof parsed.scoringCriteria === 'string' ? parsed.scoringCriteria : JSON.stringify(parsed.scoringCriteria, null, 2),
        };

        setGeneratedConfig(merged);
        addLog('JSON 解析与验证成功！', 'success');
        addLog('自动跳转至配置页...', 'info');

        setTimeout(() => setActiveTab('config'), 1500);

      } catch (e: any) {
        let errorMsg = `JSON 解析失败: ${e.message}`;
        if (e.message.includes('position')) {
          const posMatch = e.message.match(/position (\d+)/);
          if (posMatch) {
            const pos = parseInt(posMatch[1]);
            const snippet = fullText.substring(Math.max(0, pos - 30), Math.min(fullText.length, pos + 30));
            errorMsg += `\n错误位置附近: "...${snippet}..."`;
          }
        }
        addLog(errorMsg, 'error', fullText);
      }

    } catch (error: any) {
      addLog(`生成过程异常: ${error.message}`, 'error', error.stack);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    const payload = {
      ...generatedConfig,
      scriptContent: scriptContent,
      generationPrompt: systemPrompt
    };

    try {
      addLog('正在保存场景...', 'info');
      let method = 'POST';
      let url = '/api/data/scenarios';

      if (scenarioId) {
        method = 'PUT';
        url = `/api/data/scenarios/${scenarioId}`;
      }

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const saved = await res.json();
      addLog('场景已成功保存到云端数据库。', 'success', `ID: ${saved.id}`);

      setTimeout(onBack, 1000);
    } catch (e: any) {
      console.error(e);
      addLog('保存失败: ' + e.message, 'error');
      alert('保存失败: ' + e.message);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center shadow-sm sticky top-0 z-20">
        <button onClick={onBack} className="text-slate-500 mr-3 hover:bg-slate-100 p-1.5 rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-base font-bold text-slate-800">{scenarioId ? '编辑场景' : '新建场景'}</h2>
          <p className="text-[10px] text-slate-400 font-mono">
            {scenarioId ? `ID: ${scenarioId}` : 'Draft Mode'}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center p-1 mx-4 mt-4 bg-slate-200/60 rounded-lg flex-shrink-0">
        <button
          onClick={() => setActiveTab('script')}
          className={`flex-1 flex items-center justify-center py-2 text-xs font-bold rounded-md transition-all ${activeTab === 'script'
            ? 'bg-white text-medical-700 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          <FileText className="w-3.5 h-3.5 mr-1.5" />
          场景设计 (Script)
        </button>
        <button
          onClick={() => setActiveTab('config')}
          className={`flex-1 flex items-center justify-center py-2 text-xs font-bold rounded-md transition-all ${activeTab === 'config'
            ? 'bg-white text-medical-700 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          <SettingsIcon className="w-3.5 h-3.5 mr-1.5" />
          场景描述 (Config)
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 scroll-smooth">
        {activeTab === 'script' ? (
          <ScriptTab
            content={scriptContent}
            onContentChange={setScriptContent}
            attachedFiles={attachedFiles}
            onFilesChange={setAttachedFiles}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            currentPrompt={systemPrompt}
            onPromptChange={setSystemPrompt}
            onLog={(msg, type) => addLog(msg, type)}
          />
        ) : (
          <ConfigTab
            config={generatedConfig}
            onChange={setGeneratedConfig}
            onSave={handleSave}
            onLog={(msg, type, detail) => addLog(msg, type, detail)}
          />
        )}

        {/* Debug Console - Global */}
        <DebugConsole logs={logs} onClear={() => setLogs([])} />
      </div>
    </div>
  );
};
