import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Lightbulb,
  CheckCircle,
  XCircle,
  ChevronRight,
  RotateCcw,
  Trophy,
  HelpCircle,
  ArrowRight
} from 'lucide-react';

interface ExerciseProps {
  exercise: {
    title: string;
    description: string;
    array: number[];
    target: number;
    steps: {
      question: string;
      hint: string;
      options: string[];
      correct: number;
      explanation: string;
    }[];
  };
  onComplete: () => void;
}

const AlgorithmExercise: React.FC<ExerciseProps> = ({ exercise, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [correctAnswers, setCorrectAnswers] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [answeredSteps, setAnsweredSteps] = useState<Set<number>>(new Set());

  const step = exercise.steps[currentStep];
  const isAnswered = answeredSteps.has(currentStep);
  const isCorrect = selectedAnswer === step?.correct;
  const totalSteps = exercise.steps.length;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  const handleAnswer = (answerIndex: number) => {
    if (isAnswered) return;

    setSelectedAnswer(answerIndex);
    setShowExplanation(true);
    setAnsweredSteps(new Set([...answeredSteps, currentStep]));

    if (answerIndex === step.correct) {
      setCorrectAnswers(prev => prev + 1);
    }
  };

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1);
      setSelectedAnswer(null);
      setShowHint(false);
      setShowExplanation(false);
    } else {
      setIsComplete(true);
      onComplete();
    }
  };

  const handleReset = () => {
    setCurrentStep(0);
    setSelectedAnswer(null);
    setShowHint(false);
    setShowExplanation(false);
    setCorrectAnswers(0);
    setIsComplete(false);
    setAnsweredSteps(new Set());
  };

  if (isComplete) {
    const percentage = Math.round((correctAnswers / totalSteps) * 100);
    const isPerfect = correctAnswers === totalSteps;

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-12"
      >
        <div className={`w-32 h-32 rounded-full flex items-center justify-center mb-6 ${
          isPerfect
            ? 'bg-gradient-to-br from-yellow-500 to-orange-500'
            : percentage >= 60
            ? 'bg-gradient-to-br from-green-500 to-emerald-500'
            : 'bg-gradient-to-br from-blue-500 to-cyan-500'
        }`}>
          <Trophy size={64} className="text-white" />
        </div>

        <h2 className="text-3xl font-bold text-white mb-2">
          {isPerfect ? 'Perfect Score!' : percentage >= 60 ? 'Great Job!' : 'Good Effort!'}
        </h2>

        <p className="text-slate-400 text-lg mb-6">
          You got {correctAnswers} out of {totalSteps} correct ({percentage}%)
        </p>

        <div className="flex gap-4">
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-bold transition-colors flex items-center gap-2"
          >
            <RotateCcw size={18} />
            Try Again
          </button>
        </div>

        <div className="mt-8 w-full max-w-md">
          <div className="flex justify-between text-sm text-slate-400 mb-2">
            <span>Score</span>
            <span>{correctAnswers}/{totalSteps}</span>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${percentage}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className={`h-full rounded-full ${
                isPerfect
                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                  : percentage >= 60
                  ? 'bg-gradient-to-r from-green-500 to-emerald-500'
                  : 'bg-gradient-to-r from-blue-500 to-cyan-500'
              }`}
            />
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-2xl p-6"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
            <Lightbulb size={24} className="text-purple-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">{exercise.title}</h3>
            <p className="text-slate-400 text-sm">{exercise.description}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center justify-center p-4 bg-slate-900/50 rounded-xl">
          {exercise.array.map((val, idx) => (
            <div key={idx} className="flex flex-col items-center">
              <div className="w-12 h-12 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-white">
                {val}
              </div>
              <span className="text-xs text-slate-500 mt-1">{idx}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Target:</span>
            <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded font-mono font-bold">
              {exercise.target}
            </span>
          </div>
        </div>
      </motion.div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Question {currentStep + 1} of {totalSteps}</span>
          <span className="text-cyan-400 font-mono">{correctAnswers} correct</span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
          />
        </div>
      </div>

      <motion.div
        key={currentStep}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
      >
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-cyan-400 font-bold">{currentStep + 1}</span>
            </div>
            <div>
              <h4 className="text-lg font-bold text-white mb-2">{step.question}</h4>
              {!showHint && !isAnswered && (
                <button
                  onClick={() => setShowHint(true)}
                  className="text-sm text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
                >
                  <HelpCircle size={14} />
                  Show Hint
                </button>
              )}
            </div>
          </div>
        </div>

        <AnimatePresence>
          {showHint && !isAnswered && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6"
            >
              <div className="px-4 py-3 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
                <div className="flex items-center gap-2 text-cyan-400 text-sm">
                  <Lightbulb size={14} />
                  <span className="font-medium">Hint:</span>
                  <span className="text-slate-300">{step.hint}</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="grid gap-3">
          {step.options.map((option, idx) => {
            const isSelected = selectedAnswer === idx;
            const isCorrectAnswer = idx === step.correct;
            const showResult = isAnswered;

            return (
              <button
                key={idx}
                onClick={() => handleAnswer(idx)}
                disabled={isAnswered}
                className={`
                  w-full p-4 rounded-xl border-2 text-left transition-all flex items-center gap-4
                  ${!showResult
                    ? 'border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/50 cursor-pointer'
                    : isCorrectAnswer
                    ? 'border-green-500 bg-green-500/10'
                    : isSelected
                    ? 'border-red-500 bg-red-500/10'
                    : 'border-slate-700 opacity-50'
                  }
                `}
              >
                <div className={`
                  w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0
                  ${!showResult
                    ? 'bg-slate-800 text-slate-400'
                    : isCorrectAnswer
                    ? 'bg-green-500 text-white'
                    : isSelected
                    ? 'bg-red-500 text-white'
                    : 'bg-slate-800 text-slate-400'
                  }
                `}>
                  {showResult && isCorrectAnswer ? (
                    <CheckCircle size={18} />
                  ) : showResult && isSelected ? (
                    <XCircle size={18} />
                  ) : (
                    String.fromCharCode(65 + idx)
                  )}
                </div>
                <span className={`font-medium ${
                  showResult && isCorrectAnswer ? 'text-green-400' :
                  showResult && isSelected ? 'text-red-400' :
                  'text-white'
                }`}>
                  {option}
                </span>
              </button>
            );
          })}
        </div>

        <AnimatePresence>
          {showExplanation && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6"
            >
              <div className={`p-4 rounded-xl border ${
                isCorrect
                  ? 'bg-green-500/10 border-green-500/30'
                  : 'bg-orange-500/10 border-orange-500/30'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {isCorrect ? (
                    <CheckCircle size={18} className="text-green-400" />
                  ) : (
                    <XCircle size={18} className="text-orange-400" />
                  )}
                  <span className={`font-bold ${isCorrect ? 'text-green-400' : 'text-orange-400'}`}>
                    {isCorrect ? 'Correct!' : 'Not quite!'}
                  </span>
                </div>
                <p className="text-slate-300">{step.explanation}</p>
              </div>

              <div className="flex justify-end mt-4">
                <button
                  onClick={handleNext}
                  className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg font-bold transition-colors flex items-center gap-2"
                >
                  {currentStep < totalSteps - 1 ? (
                    <>
                      Next Question
                      <ChevronRight size={18} />
                    </>
                  ) : (
                    <>
                      See Results
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <div className="flex items-center justify-center gap-2">
        {exercise.steps.map((_, idx) => (
          <div
            key={idx}
            className={`w-3 h-3 rounded-full transition-all ${
              idx === currentStep
                ? 'bg-cyan-500 scale-125'
                : answeredSteps.has(idx)
                ? 'bg-green-500/50'
                : 'bg-slate-700'
            }`}
          />
        ))}
      </div>
    </div>
  );
};

export default AlgorithmExercise;
