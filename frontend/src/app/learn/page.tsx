"use client";

import { useEffect, useState } from "react";
import { getConcepts } from "@/lib/api";

interface Concept {
  name: string;
  short: string;
  explanation: string;
  formula: string;
}

export default function LearnPage() {
  const [concepts, setConcepts] = useState<Record<string, Concept>>({});
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getConcepts()
      .then((data) => setConcepts(data.concepts))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full" />
      </div>
    );
  }

  const selected = selectedConcept ? concepts[selectedConcept] : null;

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-2">Belajar Trading</h2>
      <p className="text-gray-500 text-sm mb-6">
        Faham setiap indicator dan concept yang bot guna untuk buat keputusan trading.
        Semua explanation dalam Bahasa Melayu.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Concept List */}
        <div className="space-y-2">
          {Object.entries(concepts).map(([key, concept]) => (
            <button
              key={key}
              onClick={() => setSelectedConcept(key)}
              className={`w-full text-left p-3 rounded-lg transition ${
                selectedConcept === key
                  ? "bg-accent-blue/20 border border-accent-blue/50"
                  : "bg-bg-secondary border border-border hover:border-gray-600"
              }`}
            >
              <p className="font-medium text-sm">{concept.name}</p>
              <p className="text-xs text-gray-500 mt-1">{concept.short}</p>
            </button>
          ))}
        </div>

        {/* Concept Detail */}
        <div className="lg:col-span-2">
          {selected ? (
            <div className="card">
              <h3 className="text-xl font-bold mb-2 text-accent-blue">
                {selected.name}
              </h3>
              <p className="text-sm text-accent-yellow mb-4">{selected.short}</p>

              <div className="prose prose-invert max-w-none">
                {selected.explanation.split("\n\n").map((paragraph, i) => (
                  <div key={i} className="mb-4">
                    {paragraph.split("\n").map((line, j) => {
                      if (line.startsWith("- ") || line.startsWith("* ")) {
                        return (
                          <p key={j} className="text-sm text-gray-300 ml-4 mb-1">
                            {line}
                          </p>
                        );
                      }
                      if (line.match(/^[A-Z]+:/)) {
                        return (
                          <p key={j} className="text-sm font-semibold text-gray-200 mt-3 mb-1">
                            {line}
                          </p>
                        );
                      }
                      return (
                        <p key={j} className="text-sm text-gray-300 leading-relaxed">
                          {line}
                        </p>
                      );
                    })}
                  </div>
                ))}
              </div>

              {selected.formula && (
                <div className="bg-bg-tertiary rounded p-3 mt-4">
                  <p className="text-xs text-gray-500 mb-1">Formula</p>
                  <p className="text-sm font-mono text-accent-purple">{selected.formula}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-20">
              <p className="text-gray-500">
                Pilih mana-mana concept di sebelah untuk belajar
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
