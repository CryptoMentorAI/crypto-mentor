"use client";

interface ExplanationData {
  full_text: string;
  reasons: string[];
  learning_points: string[];
  risk_reward_ratio: number | null;
  indicators: Record<string, number>;
}

interface PostAnalysisData {
  result_summary: string;
  what_went_right: string[] | null;
  what_went_wrong: string[] | null;
  improvements: string[] | null;
  lesson: string;
}

interface Props {
  explanation: ExplanationData | null;
  postAnalysis?: PostAnalysisData | null;
}

export default function ExplanationCard({ explanation, postAnalysis }: Props) {
  if (!explanation) {
    return (
      <div className="card">
        <h3 className="font-semibold mb-3">Explanation</h3>
        <p className="text-gray-500 text-sm">Pilih trade untuk tengok explanation</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Entry Explanation */}
      <div className="card">
        <h3 className="font-semibold mb-4 text-accent-blue">Kenapa Trade Ni Dibuat?</h3>

        {/* Reasons */}
        <div className="space-y-3 mb-6">
          {explanation.reasons.map((reason, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-accent-yellow font-bold text-sm shrink-0">
                {i + 1}.
              </span>
              <p className="text-sm text-gray-300 leading-relaxed">{reason}</p>
            </div>
          ))}
        </div>

        {/* Risk/Reward */}
        {explanation.risk_reward_ratio && (
          <div className="bg-bg-tertiary rounded p-3 mb-4">
            <p className="text-xs text-gray-500 mb-1">Risk : Reward Ratio</p>
            <p className="text-lg font-bold">
              1 : {explanation.risk_reward_ratio}
              {explanation.risk_reward_ratio >= 2 && (
                <span className="text-accent-green text-xs ml-2">Good!</span>
              )}
            </p>
          </div>
        )}

        {/* Learning Points */}
        {explanation.learning_points.length > 0 && (
          <div className="border-t border-border pt-4">
            <h4 className="text-sm font-semibold text-accent-purple mb-3">
              Apa Kau Boleh Belajar
            </h4>
            <div className="space-y-3">
              {explanation.learning_points.map((point, i) => (
                <div key={i} className="bg-accent-purple/5 border border-accent-purple/20 rounded p-3">
                  <p className="text-sm text-gray-300 leading-relaxed">{point}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Indicators */}
        <div className="border-t border-border pt-4 mt-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-3">Indicator Values</h4>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(explanation.indicators)
              .filter(([key]) => ["rsi", "macd", "adx", "ema_9", "ema_21", "volume"].includes(key))
              .map(([key, value]) => (
                <div key={key} className="bg-bg-tertiary rounded p-2">
                  <p className="text-xs text-gray-500 uppercase">{key.replace("_", " ")}</p>
                  <p className="text-sm font-mono">
                    {typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(value)}
                  </p>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Post-Trade Analysis */}
      {postAnalysis && (
        <div className="card">
          <h3 className="font-semibold mb-4 text-accent-yellow">Post-Trade Analysis</h3>

          <p className="text-sm mb-4 font-mono bg-bg-tertiary rounded p-3">
            {postAnalysis.result_summary}
          </p>

          {postAnalysis.what_went_right && postAnalysis.what_went_right.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs text-accent-green font-semibold mb-2">Apa Yang Betul</h4>
              {postAnalysis.what_went_right.map((item, i) => (
                <p key={i} className="text-sm text-gray-300 ml-4">+ {item}</p>
              ))}
            </div>
          )}

          {postAnalysis.what_went_wrong && postAnalysis.what_went_wrong.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs text-accent-red font-semibold mb-2">Apa Yang Tak Kena</h4>
              {postAnalysis.what_went_wrong.map((item, i) => (
                <p key={i} className="text-sm text-gray-300 ml-4">- {item}</p>
              ))}
            </div>
          )}

          {postAnalysis.improvements && postAnalysis.improvements.length > 0 && (
            <div className="mb-3">
              <h4 className="text-xs text-accent-blue font-semibold mb-2">Boleh Improve</h4>
              {postAnalysis.improvements.map((item, i) => (
                <p key={i} className="text-sm text-gray-300 ml-4">* {item}</p>
              ))}
            </div>
          )}

          <div className="bg-accent-yellow/10 border border-accent-yellow/20 rounded p-3 mt-4">
            <p className="text-xs text-accent-yellow font-semibold mb-1">LESSON</p>
            <p className="text-sm text-gray-300 leading-relaxed">{postAnalysis.lesson}</p>
          </div>
        </div>
      )}
    </div>
  );
}
