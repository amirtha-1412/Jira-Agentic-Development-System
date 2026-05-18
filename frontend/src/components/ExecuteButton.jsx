import React from 'react'

const RocketIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
    <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
    <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
  </svg>
)

const SpinnerIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
    style={{ animation: 'spin 0.8s linear infinite' }}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
  </svg>
)

const CheckCircleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
  </svg>
)

export default function ExecuteButton({ onClick, isLoading, isComplete, progress = 0, disabled }) {
  return (
    <div className="flex flex-col gap-3">
      <button
        id="execute-pipeline-btn"
        onClick={onClick}
        disabled={isLoading || disabled}
        className="btn-primary relative w-full py-4 px-8 text-base font-bold tracking-wide flex items-center justify-center gap-3 z-10"
        style={{ minHeight: '56px' }}
      >
        {/* Shimmer sweep */}
        {!isLoading && !isComplete && (
          <span className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none">
            <span className="absolute top-0 -left-full w-full h-full"
              style={{
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)',
                animation: 'shimmer 2.5s infinite',
              }} />
          </span>
        )}

        <span className="relative z-10 flex items-center gap-2.5">
          {isLoading   && <SpinnerIcon />}
          {isComplete  && <CheckCircleIcon />}
          {!isLoading && !isComplete && <RocketIcon />}

          <span>
            {isLoading  ? 'Running Pipeline…'  : isComplete ? 'Pipeline Complete' : 'Execute AI Pipeline'}
          </span>
        </span>
      </button>

      {/* Progress bar */}
      {(isLoading || isComplete) && (
        <div className="relative h-1.5 rounded-full overflow-hidden"
          style={{ background: 'rgba(100,116,139,0.2)' }}>
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${progress}%`,
              background: isComplete
                ? 'linear-gradient(90deg, #10b981, #06b6d4)'
                : 'linear-gradient(90deg, #06b6d4, #818cf8)',
              boxShadow: `0 0 8px ${isComplete ? '#10b981' : '#06b6d4'}80`,
            }}
          />
          {isLoading && !isComplete && (
            <div className="absolute inset-0 rounded-full"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(6,182,212,0.3) 50%, transparent 100%)',
                animation: 'shimmer 1.5s infinite',
              }} />
          )}
        </div>
      )}

      {/* Stage label */}
      {isLoading && (
        <p className="text-center text-xs text-slate-500 font-mono animate-pulse">
          ⚡ Agents working autonomously…
        </p>
      )}
      {isComplete && (
        <p className="text-center text-xs text-emerald-400 font-mono">
          ✔ All agents completed successfully
        </p>
      )}

      <style>{`
        @keyframes shimmer {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
