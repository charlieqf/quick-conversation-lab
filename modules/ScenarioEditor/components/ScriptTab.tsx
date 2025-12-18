
import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Wand2, RefreshCcw, Settings, X, Save, Paperclip, File as FileIcon } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { Modal } from '../../../components/ui/Modal';
import { AttachedFile } from '../../../types';
import * as pdfjsLib from 'pdfjs-dist';

// Set worker source for PDF.js (CDN)
if (typeof window !== 'undefined' && !(pdfjsLib as any).GlobalWorkerOptions.workerSrc) {
  (pdfjsLib as any).GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.0.379/build/pdf.worker.min.mjs';
}

interface ScriptTabProps {
  content: string;
  onContentChange: (text: string) => void;
  attachedFiles: AttachedFile[];
  onFilesChange: (files: AttachedFile[]) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  currentPrompt: string;
  onPromptChange: (prompt: string) => void;
  onLog: (msg: string, type: 'info' | 'error' | 'success') => void;
  isReadOnly?: boolean;
}

export const ScriptTab: React.FC<ScriptTabProps> = ({
  content,
  onContentChange,
  attachedFiles,
  onFilesChange,
  onGenerate,
  isGenerating,
  currentPrompt,
  onPromptChange,
  onLog,
  isReadOnly = false
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);

  // Local state for prompt editing inside modal
  const [tempPrompt, setTempPrompt] = useState(currentPrompt);

  const cleanText = (text: string) => {
    return text
      .replace(/\0/g, '')
      .replace(/[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]/g, '')
      .replace(/[ \t]+/g, ' ')
      .replace(/(\w)-\n(\w)/g, '$1$2')
      .trim();
  };

  // Convert File to Base64 string (raw data part)
  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        // Remove "data:application/pdf;base64," prefix
        const base64Data = result.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = error => reject(error);
    });
  };

  const processFiles = async (files: FileList | File[]) => {
    setIsProcessingFile(true);
    const fileArray = Array.from(files);
    let batchText = '';
    const newAttachedFiles: AttachedFile[] = [];

    onLog(`开始批量处理 ${fileArray.length} 个文件...`, 'info');

    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      onLog(`[${i + 1}/${fileArray.length}] 正在读取: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info');

      try {
        // 1. Prepare Base64 for API (Multimodal)
        const base64Data = await fileToBase64(file);
        newAttachedFiles.push({
          id: Date.now().toString() + Math.random().toString(),
          name: file.name,
          type: file.type,
          mimeType: file.type,
          data: base64Data
        });

        // 2. Extract Text for Preview (Client-side fallback/display)
        let extractedText = '';

        if (file.type === 'application/pdf') {
          const arrayBuffer = await file.arrayBuffer();
          const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

          for (let j = 1; j <= pdf.numPages; j++) {
            const page = await pdf.getPage(j);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map((item: any) => item.str).join(' ');
            extractedText += `\n--- Page ${j} ---\n` + pageText;
          }
        } else if (file.type === 'text/plain') {
          extractedText = await file.text();
        }

        // Only append text if extraction worked
        if (extractedText) {
          const cleaned = cleanText(extractedText);
          batchText += `\n\n=== 📄 FILE PREVIEW: ${file.name} ===\n${cleaned}\n`;
        }

        onLog(`  - ${file.name} 已准备就绪 (API模式 + 预览文本)`, 'success');

      } catch (err: any) {
        console.error(err);
        onLog(`  - 处理失败 ${file.name}: ${err.message}`, 'error');
      }
    }

    // Update State
    onFilesChange([...attachedFiles, ...newAttachedFiles]);

    if (batchText) {
      const prefix = content ? content + '\n' : '';
      onContentChange(prefix + batchText);
    }

    setIsProcessingFile(false);
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const removeFile = (id: string) => {
    onFilesChange(attachedFiles.filter(f => f.id !== id));
  };

  const openPromptSettings = () => {
    setTempPrompt(currentPrompt);
    setIsPromptModalOpen(true);
  };

  const savePromptSettings = () => {
    onPromptChange(tempPrompt);
    setIsPromptModalOpen(false);
    onLog('系统提示词 (System Prompt) 已更新。', 'info');
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-xl p-6 text-center transition-all mb-4 relative overflow-hidden flex-shrink-0
          ${isDragging
            ? 'border-medical-500 bg-medical-50 scale-[1.02]'
            : 'border-slate-200 bg-slate-50 hover:border-medical-300 hover:bg-slate-100'}
        `}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        {isProcessingFile ? (
          <div className="flex flex-col items-center justify-center py-2">
            <div className="w-8 h-8 border-4 border-medical-200 border-t-medical-600 rounded-full animate-spin mb-3"></div>
            <p className="text-sm text-medical-700 font-medium">正在解析文件内容...</p>
          </div>
        ) : (
          <>
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm">
              <UploadCloud className="w-5 h-5 text-medical-600" />
            </div>
            <p className="text-sm font-medium text-slate-700">点击上传 PDF/TXT (支持多选) 或拖拽文件</p>
            <p className="text-xs text-slate-400 mt-1">为了最佳效果，API 将直接读取 PDF 文件以保留表格结构</p>
            <input
              type="file"
              className="hidden"
              id="file-upload"
              accept=".pdf,.txt"
              multiple
              onChange={handleFileUpload}
            />
            <label
              htmlFor="file-upload"
              className="absolute inset-0 cursor-pointer"
              aria-label="Upload file"
            />
          </>
        )}
      </div>

      {/* File List Badge Area */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {attachedFiles.map(file => (
            <div key={file.id} className="flex items-center bg-medical-50 text-medical-700 text-xs px-2 py-1 rounded border border-medical-100 shadow-sm animate-in fade-in zoom-in duration-200">
              <Paperclip className="w-3 h-3 mr-1.5" />
              <span className="max-w-[150px] truncate font-medium">{file.name}</span>
              <button
                onClick={() => removeFile(file.id)}
                className="ml-2 p-0.5 hover:bg-medical-100 rounded-full text-medical-400 hover:text-medical-800 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
          <button
            onClick={() => onFilesChange([])}
            className="text-[10px] text-slate-400 hover:text-red-500 underline ml-1 self-center"
          >
            清空所有附件
          </button>
        </div>
      )}

      {/* Text Area */}
      <div className="flex-1 relative flex flex-col min-h-[200px]">
        <div className="flex justify-between items-center mb-1.5">
          <label className="text-xs font-bold text-slate-500 flex items-center">
            <FileIcon className="w-3 h-3 mr-1" /> 脚本内容预览 (Raw Text Preview):
          </label>
          {content && (
            <button
              onClick={() => onContentChange('')}
              className="flex items-center text-[10px] text-slate-400 hover:text-red-500 transition-colors bg-slate-100 px-2 py-1 rounded"
            >
              <RefreshCcw className="w-3 h-3 mr-1" /> 清空文本
            </button>
          )}
        </div>

        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder="上传文件后，预览文本将显示在这里。如果在无文件模式下，请直接在此粘贴脚本..."
          className="flex-1 w-full p-3 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 leading-relaxed focus:ring-2 focus:ring-medical-500 focus:border-transparent resize-none font-mono"
        />

        {attachedFiles.length > 0 && (
          <div className="absolute bottom-3 right-3 bg-blue-50 text-blue-700 text-[10px] px-2 py-1 rounded border border-blue-100 shadow-sm opacity-90 pointer-events-none">
            提示: 生成时将优先使用 PDF 原文件
          </div>
        )}
      </div>

      {/* Action Bar */}
      <div className="mt-4 flex items-center space-x-2">
        <Button
          variant="primary"
          className="flex-1 py-3 shadow-lg shadow-medical-600/20"
          onClick={onGenerate}
          isLoading={isGenerating}
          disabled={(!content && attachedFiles.length === 0) || isGenerating || isReadOnly}
          icon={<Wand2 className="w-4 h-4" />}
          title={isReadOnly ? "Only admins can generate" : "Generate Scenario Config"}
        >
          {isGenerating ? 'AI 分析生成中...' : '生成场景配置'}
        </Button>

        <button
          onClick={openPromptSettings}
          className="p-3 bg-white border border-slate-200 rounded-lg text-slate-500 hover:text-medical-600 hover:border-medical-300 shadow-sm transition-all active:scale-95"
          title="配置 System Prompt"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Prompt Settings Modal */}
      <Modal
        isOpen={isPromptModalOpen}
        onClose={() => setIsPromptModalOpen(false)}
        title="配置系统提示词 (Prompt Engineering)"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsPromptModalOpen(false)}>取消</Button>
            <Button variant="primary" onClick={savePromptSettings} icon={<Save className="w-4 h-4" />}>保存配置</Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-slate-500 leading-relaxed">
            修改 AI 用于生成场景配置的系统指令。建议保留 JSON 结构要求。
          </p>
          <div className="relative">
            <textarea
              value={tempPrompt}
              onChange={(e) => setTempPrompt(e.target.value)}
              className="w-full h-64 p-3 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700"
            />
          </div>
          <div className="bg-orange-50 p-2 rounded border border-orange-100 flex items-start">
            <div className="w-1 h-1 bg-orange-400 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
            <p className="text-[10px] text-orange-700">
              提示：如果存在 PDF 附件，系统会自动追加“优先分析 PDF 表格内容”的指令。
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
