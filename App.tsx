
import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Narrator from './components/Narrator';
import VisualizerCanvas from './components/VisualizerCanvas';
import Controls from './components/Controls';
import LearningJourney from './components/LearningJourney';
import AlgorithmDeepDive from './components/AlgorithmDeepDive';
import ErrorBoundary from './components/ErrorBoundary';
import { analyzeProblemWithBackend, learnProblemWithBackend } from './services/apiService';
import { generateAlgorithmTrace, generateLearningPhases, MOCK_TRACE, DEMO_TRACE } from './services/geminiService';
import { TraceData, ContextOption, ModelName } from './types';
import { Loader2, AlertCircle, Database, MonitorPlay, Zap, Cloud, PlayCircle } from 'lucide-react';

const App: React.FC = () => {
  const [trace, setTrace] = useState<TraceData>(MOCK_TRACE);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<'idle' | 'backend' | 'cloud'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [quizSolved, setQuizSolved] = useState(false);
  const [backendActive, setBackendActive] = useState(false);
  const [wasPlayingBeforeQuiz, setWasPlayingBeforeQuiz] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelName>('gemini-2.5-flash');

  const [learningPhases, setLearningPhases] = useState<any[]>([]);
  const [showLearningJourney, setShowLearningJourney] = useState(false);
  const [isLearningModeActive, setIsLearningModeActive] = useState(false);
  const [lastProblem, setLastProblem] = useState<string>('');
  const [lastContext, setLastContext] = useState<ContextOption[]>([]);

  const [showAlgorithmDeepDive, setShowAlgorithmDeepDive] = useState(false);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<string | null>(null);

  // Track the mode we started with for the current operation
  const [sessionBackendMode, setSessionBackendMode] = useState<boolean | null>(null);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const savedModel = localStorage.getItem('algo_insight_model') as ModelName;
    if (savedModel) setSelectedModel(savedModel);

    const checkBackend = async () => {
      // Don't check backend status while loading - it might be busy processing
      if (isLoading || showLearningJourney || showAlgorithmDeepDive) {
        return;
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000); // Increased timeout
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
    const interval = setInterval(checkBackend, 10000); // Reduced frequency
    return () => clearInterval(interval);
  }, [isLoading, showLearningJourney, showAlgorithmDeepDive]);

  const handleModelChange = (model: ModelName) => {
    setSelectedModel(model);
    localStorage.setItem('algo_insight_model', model);
  };

  const frames = trace?.frames || [];
  const activeFrame = frames.length > 0 ? (frames[currentStep] || frames[0]) : null;
  const isBlockedByQuiz = !!activeFrame?.quiz && !quizSolved;

  const handleAnalyze = async (problem: string, context: ContextOption[], isLearningMode: boolean) => {
    setIsLoading(true);
    setError(null);
    setIsPlaying(false);
    setCurrentStep(0);
    setQuizSolved(false);
    setShowLearningJourney(false);
    setShowAlgorithmDeepDive(false);
    setSelectedAlgorithm(null);
    setIsLearningModeActive(isLearningMode);

    // Save the current backend mode for this entire session/flow
    // This ensures we stay in the same mode throughout learning -> visualization
    setSessionBackendMode(backendActive);
    console.log(`🔒 [Session] Locking mode to: ${backendActive ? 'BACKEND' : 'CLOUD'}`);

    setLastProblem(problem);
    setLastContext(context);

    try {
      if (isLearningMode) {
        if (backendActive) {
          setAnalysisMode('backend');
          const learningData = await learnProblemWithBackend(problem, context);
          setLearningPhases(learningData.phases || []);
          setShowLearningJourney(true);
        } else {
          setAnalysisMode('cloud');
          const learningData = await generateLearningPhases(problem, context, selectedModel);
          if (learningData.phases && learningData.phases.length > 0) {
            setLearningPhases(learningData.phases);
            setShowLearningJourney(true);
          } else {
            throw new Error("Learning phase generation returned empty.");
          }
        }
      } else {
        let data: TraceData;

        if (backendActive) {
          setAnalysisMode('backend');
          data = await analyzeProblemWithBackend(problem, context);
        } else {
          setAnalysisMode('cloud');
          data = await generateAlgorithmTrace(problem, context, selectedModel);
        }

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
      // Note: Don't reset sessionBackendMode here for learning mode,
      // as we need it for the subsequent visualization call
      if (!isLearningMode) {
        setSessionBackendMode(null);
        console.log('🔓 [Session] Mode lock released (non-learning)');
      }
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
    console.log('🎓 [Learning Complete] Phase 3 data:', JSON.stringify(phase3, null, 2));
    console.log('🎓 [Learning Complete] Recommended object:', phase3?.content?.recommended);
    const recommendedAlgo = phase3?.content?.recommended?.approach_name;
    console.log('🎯 [Learning Complete] Extracted algorithm:', recommendedAlgo);
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
    console.log('🚀 [Visualization] Starting with algorithm:', algorithmName);
    console.log('🚀 [Visualization] Last problem:', lastProblem?.substring(0, 100));

    // Use the session mode (locked when analysis started) instead of current backendActive state
    // This prevents mode switching mid-flow if health check temporarily fails
    const useBackend = sessionBackendMode !== null ? sessionBackendMode : backendActive;
    console.log(`🔒 [Visualization] Using locked session mode: ${useBackend ? 'BACKEND' : 'CLOUD'} (sessionBackendMode=${sessionBackendMode}, backendActive=${backendActive})`);

    setIsLoading(true);
    setError(null);

    try {
      let data: TraceData;

      if (useBackend) {
        setAnalysisMode('backend');
        console.log('🔹 [Visualization] Calling backend with algorithm:', algorithmName || 'undefined');
        data = await analyzeProblemWithBackend(lastProblem, lastContext, algorithmName || undefined);
      } else {
        setAnalysisMode('cloud');
        data = await generateAlgorithmTrace(lastProblem, lastContext, selectedModel, algorithmName || undefined);
      }

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
      // Reset session mode after visualization completes
      setSessionBackendMode(null);
      console.log('🔓 [Session] Mode lock released');
    }
  };

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden select-none font-sans">
      <Sidebar
        onAnalyze={handleAnalyze}
        isLoading={isLoading}
        selectedModel={selectedModel}
        onModelChange={handleModelChange}
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
                <div className="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-[10px] font-black border-2 border-cyan-500/50 bg-cyan-500/20 text-cyan-300 shadow-lg shadow-cyan-500/20">
                  <Cloud size={12} />
                  CLOUD MODE
                </div>
              )}

              {analysisMode !== 'idle' && (
                <div className={`flex items-center gap-1 px-3 py-1 rounded-md text-[8px] font-bold uppercase tracking-wider ${
                  analysisMode === 'backend'
                    ? 'bg-green-950/50 text-green-400 border border-green-500/20'
                    : 'bg-cyan-950/50 text-cyan-400 border border-cyan-500/20'
                }`}>
                  {analysisMode === 'backend' ? '🧠 5-Agent Pipeline' : '⚡ Direct LLM'}
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
                      <Loader2 size={80} className={`${analysisMode === 'backend' ? 'text-green-500' : 'text-cyan-500'} animate-spin`} />
                      {analysisMode === 'backend' ? (
                        <Database size={32} className="absolute text-green-300 animate-pulse" />
                      ) : (
                        <Zap size={32} className="absolute text-cyan-300 animate-pulse" />
                      )}
                    </div>
                    <div className="text-center space-y-3">
                      <p className={`font-mono text-lg tracking-[0.3em] animate-pulse uppercase font-black ${
                        analysisMode === 'backend' ? 'text-green-400' : 'text-cyan-400'
                      }`}>
                        {isLearningModeActive
                          ? 'Generating Educational Flow'
                          : (analysisMode === 'backend' ? 'Running 5-Agent Pipeline' : 'Synthesizing Trace')}
                      </p>
                      <div className={`flex items-center justify-center gap-2 px-4 py-2 rounded-full text-xs font-bold ${
                        analysisMode === 'backend'
                          ? 'bg-green-500/10 border border-green-500/30 text-green-300'
                          : 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-300'
                      }`}>
                        {analysisMode === 'backend' ? (
                          <>
                            <Database size={14} />
                            {isLearningModeActive ? 'LEARNING MODE • 3 Phases' : 'BACKEND MODE • Python Agents • Azure OpenAI'}
                          </>
                        ) : (
                          <>
                            <Cloud size={14} />
                            CLOUD MODE • Direct Gemini API
                          </>
                        )}
                      </div>
                      <p className="text-slate-500 text-[10px] mt-2 font-mono uppercase tracking-[0.4em] opacity-80">
                        {isLearningModeActive
                          ? 'This may take 1-2 minutes...'
                          : (analysisMode === 'backend'
                            ? 'Executing Python Sandbox...'
                            : `Requesting Gemini ${selectedModel.includes('pro') ? 'Pro' : 'Flash'}...`)}
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
                        Provide a problem to generate a step-by-step visual trace.
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
