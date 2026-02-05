
import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Narrator from './components/Narrator';
import VisualizerCanvas from './components/VisualizerCanvas';
import Controls from './components/Controls';
import LearningJourney from './components/LearningJourney';
import AlgorithmDeepDive from './components/AlgorithmDeepDive';
import ErrorBoundary from './components/ErrorBoundary';
import { analyzeProblemWithBackend, learnProblemWithBackend } from './services/apiService';
import { MOCK_TRACE, DEMO_TRACE } from './services/geminiService';
import { TraceData, ContextOption, LLMConfig } from './types';
import { Loader2, AlertCircle, Database, MonitorPlay, PlayCircle } from 'lucide-react';

const App: React.FC = () => {
  const [trace, setTrace] = useState<TraceData>(MOCK_TRACE);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<'idle' | 'backend'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [quizSolved, setQuizSolved] = useState(false);
  const [backendActive, setBackendActive] = useState(false);
  const [wasPlayingBeforeQuiz, setWasPlayingBeforeQuiz] = useState(false);

  const [learningPhases, setLearningPhases] = useState<any[]>([]);
  const [showLearningJourney, setShowLearningJourney] = useState(false);
  const [isLearningModeActive, setIsLearningModeActive] = useState(false);
  const [lastProblem, setLastProblem] = useState<string>('');
  const [lastContext, setLastContext] = useState<ContextOption[]>([]);
  const [lastLLMConfig, setLastLLMConfig] = useState<LLMConfig | null>(null);

  const [showAlgorithmDeepDive, setShowAlgorithmDeepDive] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string | null>(null);

  // Current provider info for display
  const [currentProvider, setCurrentProvider] = useState<string>('');
  const [currentModel, setCurrentModel] = useState<string>('');

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      if (isLoading || showLearningJourney || showAlgorithmDeepDive) {
        return;
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch('http://localhost:8000/', {
          mode: 'cors',
          cache: 'no-cache',
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        setBackendActive(res.ok);
      } catch (err) {
        setBackendActive(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, [isLoading, showLearningJourney, showAlgorithmDeepDive]);

  const frames = trace?.frames || [];
  const activeFrame = frames.length > 0 ? (frames[currentStep] || frames[0]) : null;
  const isBlockedByQuiz = !!activeFrame?.quiz && !quizSolved;

  const handleAnalyze = async (problem: string, context: ContextOption[], isLearningMode: boolean, llmConfig: LLMConfig) => {
    if (!backendActive) {
      setError("Backend is offline. Please start the backend server at localhost:8000");
      return;
    }

    setIsLoading(true);
    setError(null);
    setIsPlaying(false);
    setCurrentStep(0);
    setQuizSolved(false);
    setShowLearningJourney(false);
    setShowAlgorithmDeepDive(false);
    setSelectedAlgorithm(null);
    setIsLearningModeActive(isLearningMode);

    // Store for later use
    setLastProblem(problem);
    setLastContext(context);
    setLastLLMConfig(llmConfig);

    // Update current provider display
    setCurrentProvider(llmConfig.provider);
    setCurrentModel(llmConfig.model);

    try {
      if (isLearningMode) {
        setAnalysisMode('backend');
        const learningData = await learnProblemWithBackend(problem, context, llmConfig);
        setLearningPhases(learningData.phases || []);
        setShowLearningJourney(true);
      } else {
        setAnalysisMode('backend');
        const data = await analyzeProblemWithBackend(problem, context, llmConfig);

        if (data && data.frames && data.frames.length > 0) {
          setTrace(data);
        } else {
          throw new Error("Trace synthesis returned an empty sequence.");
        }
      }
    } catch (err: any) {
      console.error("Synthesis Failed:", err);
      setError(err.message || "Logic engine timeout.");
      setTrace(DEMO_TRACE);
      setShowLearningJourney(false);
    } finally {
      setIsLoading(false);
      setAnalysisMode('idle');
      setIsLearningModeActive(false);
    }
  };

  const handleNext = useCallback(() => {
    if (isBlockedByQuiz) {
      setIsPlaying(false);
      return;
    }
    setCurrentStep(prev => {
      if (prev < frames.length - 1) {
        setQuizSolved(false);
        return prev + 1;
      } else {
        setIsPlaying(false);
        return prev;
      }
    });
  }, [frames.length, isBlockedByQuiz]);

  useEffect(() => {
    if (isPlaying && !isBlockedByQuiz) {
      timerRef.current = setInterval(handleNext, 1500);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, handleNext, isBlockedByQuiz]);

  const handleQuizCorrect = () => {
    setQuizSolved(true);
    if (wasPlayingBeforeQuiz) {
      setTimeout(() => {
        setIsPlaying(true);
        setWasPlayingBeforeQuiz(false);
      }, 500);
    }
  };

  const handleLearningComplete = async () => {
    const phase3 = learningPhases.find(p => p.phase === 'explore_approaches');
    const recommendedAlgo = phase3?.content?.recommended?.approach_name;
    setShowLearningJourney(false);
    await runVisualizationWithAlgorithm(recommendedAlgo);
  };

  const handleLearnAlgorithm = (algorithmName: string) => {
    setSelectedAlgorithm(algorithmName);
    setShowLearningJourney(false);
    setShowAlgorithmDeepDive(true);
  };

  const handleAlgorithmDeepDiveComplete = async () => {
    setShowAlgorithmDeepDive(false);
    const algorithmToUse = selectedAlgorithm;
    await runVisualizationWithAlgorithm(algorithmToUse);
  };

  const handleAlgorithmDeepDiveSkip = async () => {
    setShowAlgorithmDeepDive(false);
    const algorithmToUse = selectedAlgorithm;
    await runVisualizationWithAlgorithm(algorithmToUse);
  };

  const runVisualizationWithAlgorithm = async (algorithmName: string | null) => {
    if (!backendActive) {
      setError("Backend is offline. Please start the backend server at localhost:8000");
      return;
    }

    if (!lastLLMConfig) {
      setError("No LLM configuration available. Please configure your API key.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      setAnalysisMode('backend');
      const data = await analyzeProblemWithBackend(
        lastProblem,
        lastContext,
        lastLLMConfig,
        algorithmName || undefined
      );

      if (data && data.frames && data.frames.length > 0) {
        setTrace(data);
      } else {
        throw new Error("Visualization synthesis returned an empty sequence.");
      }
    } catch (err: any) {
      console.error("Visualization failed:", err);
      setError(err.message || "Failed to generate visualization.");
      setTrace(DEMO_TRACE);
    } finally {
      setIsLoading(false);
      setAnalysisMode('idle');
    }
  };

  // Format provider name for display
  const getProviderDisplay = () => {
    if (!currentProvider) return '';
    const names: Record<string, string> = {
      'azure': 'Azure OpenAI',
      'openai': 'OpenAI',
      'gemini': 'Gemini'
    };
    return `${names[currentProvider] || currentProvider} / ${currentModel}`;
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden select-none font-sans">
      <Sidebar
        onAnalyze={handleAnalyze}
        isLoading={isLoading}
        isBackendOnline={backendActive}
      />

      <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(circle_at_center,_#0f172a_0%,_#020617_100%)]">
        <div className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md z-20">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold font-mono tracking-tight flex items-center gap-3">
              <MonitorPlay className="text-cyan-500" size={20} />
              {trace?.title || "AlgoInsight"}
            </h2>
            <div className="flex gap-3 h-6 items-center">
              {backendActive ? (
                <div className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[10px] font-black border-2 border-green-500/50 bg-green-500/20 text-green-300 animate-pulse shadow-lg shadow-green-500/20">
                  <Database size={12} className="animate-bounce" />
                  BACKEND ACTIVE
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[10px] font-black border-2 border-red-500/50 bg-red-500/20 text-red-300 shadow-lg shadow-red-500/20">
                  <Database size={12} />
                  BACKEND OFFLINE
                </div>
              )}

              {analysisMode !== 'idle' && currentProvider && (
                <div className="flex items-center gap-1 px-3 py-1 rounded-md text-[8px] font-bold uppercase tracking-wider bg-green-950/50 text-green-400 border border-green-500/20">
                  {getProviderDisplay()}
                </div>
              )}
            </div>
          </div>
          {error && (
            <div className="flex items-center gap-2 text-red-400 bg-red-500/10 px-3 py-1 rounded border border-red-500/20 text-xs font-mono max-w-md truncate">
              <AlertCircle size={14} />
              {error}
            </div>
          )}
        </div>

        <div className="flex-1 flex overflow-hidden">
          {showAlgorithmDeepDive && selectedAlgorithm ? (
            <ErrorBoundary
              fallbackTitle="Algorithm Deep Dive Error"
              onReset={() => {
                setShowAlgorithmDeepDive(false);
                setSelectedAlgorithm(null);
              }}
            >
              <AlgorithmDeepDive
                algorithmId={selectedAlgorithm}
                algorithmName={selectedAlgorithm}
                onComplete={handleAlgorithmDeepDiveComplete}
                onSkip={handleAlgorithmDeepDiveSkip}
              />
            </ErrorBoundary>
          ) : showLearningJourney && learningPhases.length > 0 ? (
            <ErrorBoundary
              fallbackTitle="Learning Journey Error"
              onReset={() => {
                setShowLearningJourney(false);
                setLearningPhases([]);
              }}
            >
              <LearningJourney
                phases={learningPhases}
                totalPhases={learningPhases.length}
                onComplete={handleLearningComplete}
                onLearnAlgorithm={handleLearnAlgorithm}
              />
            </ErrorBoundary>
          ) : (
            <>
              <div className="flex-1 flex flex-col relative">
                {isLoading ? (
                  <div className="absolute inset-0 z-50 flex flex-col items-center justify-center space-y-6 bg-slate-950/80 backdrop-blur-xl">
                    <div className="relative flex items-center justify-center">
                      <Loader2 size={80} className="text-green-500 animate-spin" />
                      <Database size={32} className="absolute text-green-300 animate-pulse" />
                    </div>
                    <div className="text-center space-y-3">
                      <p className="font-mono text-lg tracking-[0.3em] animate-pulse uppercase font-black text-green-400">
                        {isLearningModeActive
                          ? 'Generating Educational Flow'
                          : 'Running 5-Agent Pipeline'}
                      </p>
                      <div className="flex items-center justify-center gap-2 px-4 py-2 rounded-full text-xs font-bold bg-green-500/10 border border-green-500/30 text-green-300">
                        <Database size={14} />
                        {currentProvider && currentModel
                          ? `${getProviderDisplay()}`
                          : 'BACKEND MODE'}
                      </div>
                      <p className="text-slate-500 text-[10px] mt-2 font-mono uppercase tracking-[0.4em] opacity-80">
                        {isLearningModeActive
                          ? 'This may take 1-2 minutes...'
                          : 'Executing Python Sandbox...'}
                      </p>
                    </div>
                  </div>
                ) : activeFrame?.state ? (
                  <ErrorBoundary
                    fallbackTitle="Visualization Render Error"
                    onReset={() => {
                      setCurrentStep(0);
                      setTrace(DEMO_TRACE);
                    }}
                  >
                    <VisualizerCanvas
                      state={activeFrame.state}
                      isBlockedByQuiz={isBlockedByQuiz}
                      commentary={activeFrame.commentary}
                      stepId={activeFrame.step_id}
                    />
                  </ErrorBoundary>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 font-mono gap-6 p-8 text-center animate-in fade-in duration-700">
                    <div className="w-24 h-24 rounded-full border-2 border-dashed border-slate-800 flex items-center justify-center bg-slate-900/10 shadow-inner">
                      <PlayCircle size={48} className="text-slate-700 opacity-50" />
                    </div>
                    <div>
                      <p className="font-bold text-slate-400 text-lg uppercase tracking-widest">Ready for Analysis</p>
                      <p className="text-[10px] text-slate-600 mt-2 uppercase tracking-[0.3em] max-w-xs leading-relaxed">
                        Configure your LLM provider and provide a problem to generate a step-by-step visual trace.
                      </p>
                    </div>
                  </div>
                )}
              </div>
              {activeFrame && !showLearningJourney && !showAlgorithmDeepDive && (
                <Narrator
                  frame={activeFrame}
                  complexity={trace?.complexity}
                  strategy={trace?.strategy}
                  strategy_details={trace?.strategy_details}
                  onQuizCorrect={handleQuizCorrect}
                  onSkipQuiz={() => {
                    setQuizSolved(true);
                    if (wasPlayingBeforeQuiz) setIsPlaying(true);
                  }}
                />
              )}
            </>
          )}
        </div>

        <Controls
          currentStep={currentStep}
          totalSteps={frames.length}
          isPlaying={isPlaying}
          onPlayPause={() => {
            if (!isPlaying && isBlockedByQuiz) setWasPlayingBeforeQuiz(true);
            setIsPlaying(!isPlaying);
          }}
          onStepChange={(s) => {
            setCurrentStep(s);
            setIsPlaying(false);
            setQuizSolved(false);
          }}
          onReset={() => {
            setCurrentStep(0);
            setIsPlaying(false);
            setQuizSolved(false);
          }}
          isBlockedByQuiz={isBlockedByQuiz}
        />
      </main>
    </div>
  );
};

export default App;
