import React, { useEffect, useState, useRef } from 'react';
import { knowledgeApi } from '../lib/api';
import type { KnowledgeDocument } from '../types/api';
import { getApiErrorMessage } from '../lib/errors';

function ArticleCard({ doc }: { doc: KnowledgeDocument }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 mb-2">
            {doc.category}
          </span>
          <h3 className="font-semibold text-slate-900 text-sm">{doc.title}</h3>
        </div>
      </div>
      <p className={`text-sm text-slate-600 leading-relaxed ${expanded ? '' : 'line-clamp-3'}`}>
        {doc.content}
      </p>
      <button
        onClick={() => setExpanded((v) => !v)}
        className="mt-2 text-xs text-blue-600 hover:underline"
      >
        {expanded ? 'Show less' : 'Read more'}
      </button>
      {doc.tags && (
        <div className="mt-3 flex flex-wrap gap-1">
          {doc.tags.split(' ').map((tag) => (
            <span
              key={tag}
              className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
      {doc.source && (
        <p className="text-xs text-slate-400 mt-2">Source: {doc.source}</p>
      )}
    </div>
  );
}

export default function KnowledgePage() {
  const [allDocs, setAllDocs] = useState<KnowledgeDocument[]>([]);
  const [results, setResults] = useState<KnowledgeDocument[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load all on mount
  useEffect(() => {
    knowledgeApi
      .list()
      .then((docs) => {
        setAllDocs(docs);
        setResults(docs);
      })
      .catch((e) => setError(getApiErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query.trim()) {
      setResults(allDocs);
      setHasSearched(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      setHasSearched(true);
      try {
        const data = await knowledgeApi.search(query.trim());
        setResults(data);
      } catch (e) {
        setError(getApiErrorMessage(e));
      } finally {
        setSearching(false);
      }
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, allDocs]);

  // Group by category for browse view
  const grouped: Record<string, KnowledgeDocument[]> = {};
  if (!hasSearched) {
    for (const doc of results) {
      (grouped[doc.category] ??= []).push(doc);
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Knowledge Base</h1>
        <p className="text-slate-500 text-sm mt-1">
          Search for answers or browse by category.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search knowledge base…"
          className="w-full text-sm px-4 py-2.5 pl-10 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          aria-label="Search knowledge base"
        />
        <svg
          className="absolute left-3 top-3 w-4 h-4 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <circle cx="11" cy="11" r="8" />
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-4.35-4.35" />
        </svg>
        {searching && (
          <div className="absolute right-3 top-3">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-1/4 mb-3" />
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-slate-200 rounded w-full mb-1" />
              <div className="h-3 bg-slate-200 rounded w-5/6" />
            </div>
          ))}
        </div>
      )}

      {/* Search results */}
      {hasSearched && !loading && (
        <>
          <p className="text-sm text-slate-500 mb-4">
            {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
          </p>
          {results.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <p className="text-base font-medium mb-1">No results found</p>
              <p className="text-sm">Try different keywords.</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {results.map((doc) => (
                <ArticleCard key={doc.id} doc={doc} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Browse by category */}
      {!hasSearched && !loading && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([category, docs]) => (
            <div key={category}>
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
                {category}
              </h2>
              <div className="grid gap-4 md:grid-cols-2">
                {docs.map((doc) => (
                  <ArticleCard key={doc.id} doc={doc} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
