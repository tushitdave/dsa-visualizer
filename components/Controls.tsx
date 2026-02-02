
import React from 'react';
import { Play, Pause, SkipBack, SkipForward, RefreshCcw } from 'lucide-react';

interface ControlsProps {
  currentStep: number;
  totalSteps: number;
  isPlaying: boolean;
  onPlayPause: () => void;
  onStepChange: (step: number) => void;
  onReset: () => void;
  isBlockedByQuiz: boolean;
}

const Controls: React.FC<ControlsProps> = ({
  currentStep,
  totalSteps,
  isPlaying,
  onPlayPause,
  onStepChange,
  onReset,
  isBlockedByQuiz
}) => {
  const progress = totalSteps > 0 ? (currentStep / (totalSteps - 1)) * 100 : 0;

  return (
    <div className="h-24 border-t border-slate-800 bg-slate-950 flex flex-col items-center justify-center px-12 shrink-0">
      <div className="w-full max-w-4xl space-y-4">
        <div className="relative w-full h-1.5 bg-slate-800 rounded-full overflow-hidden group">
          <div
            className="absolute top-0 left-0 h-full bg-cyan-500 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min={0}
            max={totalSteps - 1}
            value={currentStep}
            onChange={(e) => onStepChange(parseInt(e.target.value))}
            className="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer z-10"
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <button
              onClick={onReset}
              className="p-2 text-slate-500 hover:text-slate-300 transition-colors"
              title="Restart"
            >
              <RefreshCcw size={18} />
            </button>
            <button
              onClick={() => onStepChange(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
              className="p-2 text-slate-300 hover:text-cyan-400 disabled:text-slate-700 transition-colors"
            >
              <SkipBack size={24} fill="currentColor" />
            </button>

            <button
              onClick={onPlayPause}
              disabled={isBlockedByQuiz}
              className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                isBlockedByQuiz
                    ? 'bg-slate-800 text-slate-500'
                    : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-500/20 active:scale-95'
              }`}
            >
              {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
            </button>

            <button
              onClick={() => onStepChange(Math.min(totalSteps - 1, currentStep + 1))}
              disabled={currentStep === totalSteps - 1 || isBlockedByQuiz}
              className="p-2 text-slate-300 hover:text-cyan-400 disabled:text-slate-700 transition-colors"
            >
              <SkipForward size={24} fill="currentColor" />
            </button>
          </div>

          <div className="font-mono text-sm text-slate-500 flex gap-4">
            <span className="flex items-center gap-2">
              <span className="text-cyan-400">STEP</span>
              <span className="text-slate-200">{currentStep + 1}</span> / {totalSteps}
            </span>
            {isBlockedByQuiz && (
                <span className="text-orange-400 animate-pulse font-bold tracking-widest uppercase">Quiz Active</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Controls;
