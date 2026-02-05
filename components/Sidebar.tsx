
import React, { useState, useEffect } from 'react';
import { Terminal, Settings, Zap, Cpu, MemoryStick, PlayCircle, Loader2, ShieldCheck, Database, GraduationCap, Eye, EyeOff, CheckCircle, XCircle, ChevronDown } from 'lucide-react';
import { ContextOption, LLMConfig, LLMProvider, ProviderInfo } from '../types';
import { fetchProviders, validateCredentials, storeSessionCredentials, checkSessionCredentials } from '../services/apiService';

interface SidebarProps {
  onAnalyze: (problem: string, context: ContextOption[], learningMode: boolean, llmConfig: LLMConfig) => void;
  isLoading: boolean;
  isBackendOnline: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  onAnalyze,
  isLoading,
  isBackendOnline
}) => {
  const [problem, setProblem] = useState(
    `Example 1:

Input: s = "babad"
Output: "bab"
Explanation: "aba" is also a valid answer.`
  );
  const [contexts, setContexts] = useState<ContextOption[]>([]);
  const [learningMode, setLearningMode] = useState(true);

  // LLM Configuration
  const [providers, setProviders] = useState<Record<LLMProvider, ProviderInfo>>({
    azure: { name: 'Azure OpenAI', models: ['gpt-4o'], requires_endpoint: true, description: '' },
    openai: { name: 'OpenAI', models: ['gpt-4o'], requires_endpoint: false, description: '' },
    gemini: { name: 'Google Gemini', models: ['gemini-2.5-flash'], requires_endpoint: false, description: '' }
  });
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('azure');
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o');
  const [apiKey, setApiKey] = useState<string>('');
  const [azureEndpoint, setAzureEndpoint] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'valid' | 'invalid'>('idle');
  const [configExpanded, setConfigExpanded] = useState(true);

  // Load providers from backend
  useEffect(() => {
    const loadProviders = async () => {
      const data = await fetchProviders();
      setProviders(data.providers);
    };
    loadProviders();
  }, []);

  // Load saved config - check backend session first, then localStorage
  useEffect(() => {
    const loadSavedConfig = async () => {
      // First, check if we have stored credentials on the backend
      const sessionCreds = await checkSessionCredentials();
      if (sessionCreds.exists && sessionCreds.provider && sessionCreds.model) {
        setSelectedProvider(sessionCreds.provider as LLMProvider);
        setSelectedModel(sessionCreds.model);
        setValidationStatus('valid');
        // Load local UI preferences (not sensitive data)
        const savedEndpoint = localStorage.getItem('algoinsight_azure_endpoint');
        if (savedEndpoint) setAzureEndpoint(savedEndpoint);
        // Note: API key is stored on backend, we don't need it in frontend state
        // for actual requests, but we still allow users to enter a new one
        return;
      }

      // Fallback to localStorage for backward compatibility
      const savedProvider = localStorage.getItem('algoinsight_provider') as LLMProvider;
      const savedModel = localStorage.getItem('algoinsight_model');
      const savedApiKey = localStorage.getItem('algoinsight_api_key');
      const savedEndpoint = localStorage.getItem('algoinsight_azure_endpoint');

      if (savedProvider && providers[savedProvider]) {
        setSelectedProvider(savedProvider);
      }
      if (savedModel) setSelectedModel(savedModel);
      if (savedApiKey) {
        setApiKey(savedApiKey);
        setValidationStatus('valid'); // Assume saved keys are valid
      }
      if (savedEndpoint) setAzureEndpoint(savedEndpoint);
    };

    loadSavedConfig();
  }, []);

  // Update model when provider changes
  useEffect(() => {
    const providerModels = providers[selectedProvider]?.models || [];
    if (providerModels.length > 0 && !providerModels.includes(selectedModel)) {
      setSelectedModel(providerModels[0]);
    }
    setValidationStatus('idle'); // Reset validation when provider changes
  }, [selectedProvider, providers]);

  // Save config to localStorage (non-sensitive preferences only)
  // API keys are stored securely on the backend via storeSessionCredentials
  const saveConfig = () => {
    localStorage.setItem('algoinsight_provider', selectedProvider);
    localStorage.setItem('algoinsight_model', selectedModel);
    // Note: We still save API key to localStorage for backward compatibility
    // and to support the "send credentials in request body" flow
    // The more secure flow uses backend-stored credentials via session ID
    localStorage.setItem('algoinsight_api_key', apiKey);
    if (azureEndpoint) {
      localStorage.setItem('algoinsight_azure_endpoint', azureEndpoint);
    }
  };

  // Validate credentials and store on backend
  const handleValidate = async () => {
    if (!apiKey) return;

    setIsValidating(true);
    setValidationStatus('idle');

    const config: LLMConfig = {
      provider: selectedProvider,
      model: selectedModel,
      apiKey: apiKey,
      azureEndpoint: selectedProvider === 'azure' ? azureEndpoint : undefined
    };

    const result = await validateCredentials(config);
    setValidationStatus(result.valid ? 'valid' : 'invalid');
    setIsValidating(false);

    if (result.valid) {
      // Store credentials securely on the backend
      const stored = await storeSessionCredentials(config);
      if (stored) {
        console.log('[Sidebar] Credentials stored securely on backend');
      }
      // Save non-sensitive preferences locally
      saveConfig();
    }
  };

  const toggleContext = (opt: ContextOption) => {
    setContexts(prev => prev.includes(opt) ? prev.filter(c => c !== opt) : [...prev, opt]);
  };

  const handleAnalyze = () => {
    if (!problem.trim()) return;
    if (!apiKey) {
      alert('Please enter an API key to use the analysis features.');
      return;
    }

    const llmConfig: LLMConfig = {
      provider: selectedProvider,
      model: selectedModel,
      apiKey: apiKey,
      azureEndpoint: selectedProvider === 'azure' ? azureEndpoint : undefined
    };

    saveConfig();
    onAnalyze(problem, contexts, learningMode, llmConfig);
  };

  const options: { label: ContextOption; icon: any; color: string }[] = [
    { label: 'Embedded System', icon: Cpu, color: 'text-orange-400' },
    { label: 'High Throughput', icon: Zap, color: 'text-yellow-400' },
    { label: 'Low Memory', icon: MemoryStick, color: 'text-blue-400' },
  ];

  const currentModels = providers[selectedProvider]?.models || [];
  const requiresEndpoint = providers[selectedProvider]?.requires_endpoint;
  const isConfigValid = apiKey && (selectedProvider !== 'azure' || azureEndpoint);

  return (
    <div className="w-80 h-full border-r border-slate-800 bg-slate-900/50 flex flex-col overflow-hidden shrink-0">
      <div className="p-6 border-b border-slate-800 flex items-center gap-3 bg-slate-950/20">
        <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.3)]">
          <Terminal className="text-slate-900" size={20} />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">AlgoInsight</h1>
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">v2.7.0-multi-provider</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        {/* LLM Configuration Section */}
        <section className="space-y-3">
          <button
            onClick={() => setConfigExpanded(!configExpanded)}
            className="flex items-center justify-between w-full text-slate-400 mb-2"
          >
            <div className="flex items-center gap-2">
              <Database size={14} />
              <span className="text-xs font-mono uppercase tracking-wider">LLM Configuration</span>
            </div>
            <ChevronDown size={14} className={`transition-transform ${configExpanded ? 'rotate-180' : ''}`} />
          </button>

          {configExpanded && (
            <div className={`p-4 rounded-xl border-2 transition-all duration-500 shadow-lg space-y-4 ${
              validationStatus === 'valid'
                ? 'border-green-500/50 bg-green-500/5'
                : validationStatus === 'invalid'
                ? 'border-red-500/50 bg-red-500/5'
                : 'border-slate-700/50 bg-slate-800/30'
            }`}>
              {/* Provider Selection */}
              <div className="space-y-2">
                <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">Provider</label>
                <div className="grid grid-cols-3 gap-2">
                  {(Object.keys(providers) as LLMProvider[]).map((provider) => (
                    <button
                      key={provider}
                      onClick={() => setSelectedProvider(provider)}
                      className={`px-3 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${
                        selectedProvider === provider
                          ? 'bg-cyan-500/20 border-2 border-cyan-500/50 text-cyan-300'
                          : 'bg-slate-800 border border-slate-700 text-slate-400 hover:border-slate-600'
                      }`}
                    >
                      {provider === 'azure' ? 'Azure' : provider === 'openai' ? 'OpenAI' : 'Gemini'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Model Selection */}
              <div className="space-y-2">
                <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                >
                  {currentModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>

              {/* Azure Endpoint (only for Azure) */}
              {requiresEndpoint && (
                <div className="space-y-2">
                  <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">Azure Endpoint</label>
                  <input
                    type="text"
                    value={azureEndpoint}
                    onChange={(e) => {
                      setAzureEndpoint(e.target.value);
                      setValidationStatus('idle');
                    }}
                    placeholder="https://your-resource.openai.azure.com/"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 placeholder:text-slate-600"
                  />
                </div>
              )}

              {/* API Key */}
              <div className="space-y-2">
                <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest">API Key</label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => {
                      setApiKey(e.target.value);
                      setValidationStatus('idle');
                    }}
                    placeholder="Enter your API key"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 pr-10 text-xs font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 placeholder:text-slate-600"
                  />
                  <button
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>

              {/* Validation Button & Status */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleValidate}
                  disabled={!isConfigValid || isValidating}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600"
                >
                  {isValidating ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : validationStatus === 'valid' ? (
                    <CheckCircle size={12} className="text-green-400" />
                  ) : validationStatus === 'invalid' ? (
                    <XCircle size={12} className="text-red-400" />
                  ) : (
                    <ShieldCheck size={12} />
                  )}
                  {isValidating ? 'Validating...' : validationStatus === 'valid' ? 'Validated' : validationStatus === 'invalid' ? 'Invalid' : 'Validate'}
                </button>
              </div>

              {/* Status Message */}
              {validationStatus !== 'idle' && (
                <div className={`text-[10px] font-mono px-2 py-1 rounded ${
                  validationStatus === 'valid'
                    ? 'text-green-400 bg-green-950/30'
                    : 'text-red-400 bg-red-950/30'
                }`}>
                  {validationStatus === 'valid'
                    ? `Using ${providers[selectedProvider]?.name} - ${selectedModel}`
                    : 'Invalid credentials. Please check your API key.'}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Backend Status */}
        <section className="space-y-3">
          <div className={`p-3 rounded-lg border transition-all ${
            isBackendOnline
              ? 'border-green-500/30 bg-green-500/5'
              : 'border-red-500/30 bg-red-500/5'
          }`}>
            <div className="flex items-center gap-2">
              {isBackendOnline ? (
                <>
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span className="text-[10px] font-mono uppercase text-green-400">Backend Online</span>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-red-400"></div>
                  <span className="text-[10px] font-mono uppercase text-red-400">Backend Offline</span>
                </>
              )}
            </div>
          </div>
        </section>

        {/* Experience Mode */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-slate-400">
            <GraduationCap size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Experience Mode</span>
          </div>
          <button
            onClick={() => setLearningMode(!learningMode)}
            className={`w-full p-3 rounded-lg border-2 transition-all flex items-center gap-3 ${
              learningMode
                ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-500/50 text-white shadow-lg shadow-cyan-500/20'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <GraduationCap size={18} className={learningMode ? 'text-cyan-400' : 'text-slate-600'} />
            <div className="flex-1 text-left">
              <div className="text-xs font-bold">
                {learningMode ? 'Learning Mode' : 'Quick Mode'}
              </div>
              <div className="text-[10px] opacity-70">
                {learningMode ? 'Step-by-step teaching' : 'Direct visualization'}
              </div>
            </div>
          </button>
        </section>

        {/* Problem Input */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-slate-400">
            <Settings size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Problem Input</span>
          </div>
          <textarea
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            placeholder="e.g., 'Explain QuickSort with an array of 8 random numbers'..."
            className="w-full h-32 bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 resize-none transition-all placeholder:text-slate-700 shadow-inner"
          />
        </section>

        {/* Contextual Toggles */}
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-slate-400">
            <Zap size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Contextual Toggles</span>
          </div>
          <div className="space-y-2">
            {options.map((opt) => (
              <button
                key={opt.label}
                onClick={() => toggleContext(opt.label)}
                className={`w-full flex items-center gap-3 p-2.5 rounded-lg border transition-all duration-200 ${
                  contexts.includes(opt.label)
                    ? 'bg-slate-800 border-slate-600 text-white'
                    : 'bg-transparent border-slate-800 text-slate-500 hover:border-slate-700'
                }`}
              >
                <opt.icon size={16} className={contexts.includes(opt.label) ? opt.color : 'text-slate-600'} />
                <span className="text-xs font-medium">{opt.label}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="p-6 border-t border-slate-800 bg-slate-950/50">
        <button
          onClick={handleAnalyze}
          disabled={isLoading || !problem.trim() || !isBackendOnline || !apiKey}
          className="w-full flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-bold py-3 rounded-lg transition-all shadow-lg shadow-cyan-500/20 active:scale-95"
        >
          {isLoading ? <Loader2 className="animate-spin" size={20} /> : <PlayCircle size={20} />}
          {isLoading ? 'GENERATING...' : 'ANALYZE & VISUALIZE'}
        </button>
        {!apiKey && (
          <p className="text-[10px] text-amber-400 mt-2 text-center">Configure API key above to enable analysis</p>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
