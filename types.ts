

export type ThemeColor = 'blue' | 'purple' | 'orange';

export interface ScoringItem {
  criteria: string;
  points: number;
}

export interface ScoringDimension {
  id: string;
  label: string;
  weight: number; // 1-10 or 1-100
  description?: string;
}

export interface AttachedFile {
  id: string;
  name: string;
  type: string;
  data: string; // Base64 string (without data: application/pdf;base64, prefix for API)
  mimeType: string;
}

export interface Scenario {
  id: string;
  title: string;
  subtitle: string; // Chinese subtitle as requested
  description: string;
  tags: string[];
  theme: ThemeColor;
  lastUpdated: string;
  author?: string;

  // Extended fields for persistence
  scriptContent?: string;
  workflow?: string; // Changed to string for full text description
  knowledgePoints?: string; // Changed to string for full text description
  scoringCriteria?: string; // Changed to string for full text description
  scoringDimensions?: ScoringDimension[]; // Configured scoring dimensions
}

export interface UserProfile {
  name: string;
  avatarImage?: string;
  avatarPrompt?: string; // Custom prompt for avatar generation
}

export interface Role {
  id: string;
  name: string; // English Name e.g. Dr. House
  nameCN: string; // Chinese Name e.g. 豪斯医生
  title: string; // Job Title e.g. 主任医师
  avatarSeed: string; // For DiceBear API
  avatarImage?: string; // Base64 Data URL for generated realistic avatar
  focusAreas: string[]; // e.g. "副作用", "费用"
  description: string; // Natural language description

  // Personality Dimensions (0-100)
  // 0 = Left extreme, 100 = Right extreme
  hostility: number; // 0 (Hostile) <-> 100 (Friendly)
  verbosity: number; // 0 (Brief) <-> 100 (Verbose)
  skepticism: number; // 0 (Gullible) <-> 100 (Skeptic)

  systemPromptAddon: string; // The generated instruction
  lastUpdated: string;
}

// Navigation View State
export type AppView = 'scenarios' | 'editor' | 'settings' | 'roles' | 'role-editor' | 'session' | 'report' | 'history';

export interface AppState {
  currentView: AppView;
  selectedScenarioId: string | null;
}

// --- Report Types ---

export interface AiEvaluationResult {
  totalScore: number;
  summary: string;
  dimensions: { label: string; score: number; comment: string }[];
}

export interface SessionReportData {
  id: string; // Unique Session ID
  scenarioId: string;
  roleId: string;
  score: number;
  messages: ChatMessage[];
  startTime: string;
  endTime: string;
  durationSeconds: number;
  aiAnalysis?: AiEvaluationResult; // Stores the detailed AI re-evaluation
}

// --- Settings Types ---

export type AIModelId = string;

export interface APIModel {
  id: string;
  name: string;
  provider: string;
  isEnabled: boolean;
  defaultVoice: string;
  supportsTranscription: boolean;
  // UI helper fields
  badge?: string;
  description?: string;
}

export interface ModelConfig {
  id: string;
  name: string;
  badge: string;
  description: string;
}

export type VoiceId = string;

export interface APIVoice {
  id: string;
  name: string;
  gender: 'Male' | 'Female';
  // UI helper fields
  style?: string;
  icon?: string;
}

export interface VoiceConfig {
  id: VoiceId;
  name: string; // Display name
  gender: 'Male' | 'Female';
  style: string; // e.g., "Calm & Professional"
  icon: string; // Emoji char
}

export interface UserSettings {
  apiKeyConfigured: boolean; // Flag for UI state (legacy/client-side)
  apiReady: boolean; // Flag for Backend connection status
  selectedModel: AIModelId;
  selectedVoice: VoiceId;
  selectedScenarioModel?: AIModelId; // New field for Scenario Generation (Text/Multimodal)
}

// --- Session Configuration Types ---

export interface AudioConfig {
  bufferSize: number;
  sampleRate: 16000 | 24000;
  autoReconnect?: boolean; // New Stability Option
}

export type InterruptionStrategy = 'handshake' | 'inner_monologue' | 'constraints';

export interface InterruptionConfig {
  mode: InterruptionStrategy;
  customConstraint?: string; // For 'constraints' mode
  customHandshake?: string; // For 'handshake' mode
}

// --- Editor Types ---

export interface LogEntry {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'stream' | 'thought'; // Added thought type
  detail?: string; // For long content like JSON payload or stack trace
}

export interface ScenarioConfig {
  title: string;
  subtitle: string;
  description: string;
  tags: string[];
  theme: ThemeColor;
  workflow: string; // Changed to string
  knowledgePoints: string; // Changed to string
  scoringCriteria: string; // Changed to string
  scoringDimensions?: ScoringDimension[];
}

// --- Session Types ---

export interface ChatMessage {
  id: string;
  role: 'user' | 'model' | 'system';
  type: 'text' | 'feedback'; // feedback is for tool outputs
  content: string;

  // For feedback types
  scoreDelta?: number;
  reason?: string;
  dimension?: string; // The dynamic dimension category (e.g. "Clinical Judgment")
  sentiment?: 'positive' | 'negative' | 'neutral';
}