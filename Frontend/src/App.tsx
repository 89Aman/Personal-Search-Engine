import { useState, type ChangeEvent, type KeyboardEvent } from "react";
import axios from "axios";
import {
  Search,
  Upload,
  FileText,
  Sparkles,
  Filter,
  Clock,
  ChevronRight,
  AlertCircle,
  Loader2,
  Database
} from "lucide-react";

/**
 * Personal Semantic Search Engine - Knowledge Vault Premium UI
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ResultItem = {
  id: string;
  type?: string;
  source: string;
  score: number;
  text: string;
  snippets?: string[];
};

const DOC_TYPES = ["pdf", "markdown", "notes"] as const;

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<ResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [types, setTypes] = useState<string[]>([...DOC_TYPES]);
  const [maxAgeDays, setMaxAgeDays] = useState(0);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const toggleType = (t: string): void => {
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  };

  const runSearch = async (): Promise<void> => {
    if (!query.trim() || loading) return;
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const payload = {
        query,
        top_k: 20,
        types: types.length ? types : null,
        max_age_days: maxAgeDays > 0 ? maxAgeDays : null,
        recency_boost: 0.3,
      };

      const res = await axios.post<{ results: ResultItem[] }>(
        `${API_BASE}/search`,
        payload,
        {
          timeout: 15000
        }
      );

      const rawResults = res.data.results || [];
      const seenText = new Set();
      const sourceCount: Record<string, number> = {};
      const filteredResults: ResultItem[] = [];

      for (const item of rawResults) {
        const normalizedText = item.text.trim().toLowerCase().substring(0, 80);
        const textKey = `${item.source}-${normalizedText}`;
        if (seenText.has(textKey)) continue;

        const currentSourceCount = sourceCount[item.source] || 0;
        if (currentSourceCount >= 3) continue;

        seenText.add(textKey);
        sourceCount[item.source] = currentSourceCount + 1;
        filteredResults.push(item);

        if (filteredResults.length >= 8) break;
      }

      setResults(filteredResults);
    } catch (err) {
      console.error(err);
      setError("Search failed. Check backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>): void => {
    if (!e.target.files) return;
    setFiles(Array.from(e.target.files));
    setError(null);
    setSuccess(null);
  };

  const uploadFiles = async (): Promise<void> => {
    if (!files.length || uploading) return;
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));

      await axios.post(`${API_BASE}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000
      });
      setFiles([]);
      setSuccess("Upload Complete! Processing in background...");
    } catch (err) {
      console.error(err);
      const msg = axios.isAxiosError(err) ? (err.response?.data?.detail || err.message) : "Upload failed";
      setError(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter") runSearch();
  };

  const textToHighlight = (text: string, q: string) => {
    const words = q.trim().split(/\s+/).filter(word => word.length > 1);
    if (words.length === 0) return text;

    const pattern = new RegExp(`(${words.join("|")})`, "gi");
    const parts = text.split(pattern);

    return parts.map((part, i) =>
      pattern.test(part) ? (
        <span key={i} className="text-zinc-100 font-medium bg-zinc-800/50 px-0.5 rounded-sm shadow-[0_0_10px_rgba(255,255,255,0.05)]">
          {part}
        </span>
      ) : (
        part
      )
    );
  };
  const synthesizeAnswer = async (): Promise<void> => {
    if (!results.length || generating) return;
    setGenerating(true);
    setAiAnswer(null);

    try {
      const res = await axios.post<{ answer: string }>(`${API_BASE}/ask`, {
        query,
        context: results.map((r) => r.text),
      });
      setAiAnswer(res.data.answer);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "AI synthesis failed. Ensure API key is set.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-zinc-100 font-sans selection:bg-zinc-100 selection:text-zinc-900">
      {/* Visual background accents */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-40">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-zinc-800/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-zinc-800/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative w-full px-6 md:px-16 lg:px-24 py-12 md:py-20 lg:py-24 space-y-12 md:space-y-20">
        {/* Header Section */}
        <header className="flex flex-col items-center text-center space-y-4 md:space-y-6 animate-in fade-in zoom-in duration-1000">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-900/50 border border-zinc-800 rounded-full backdrop-blur-md">
            <Sparkles className="w-3.5 h-3.5 text-zinc-400" />
            <span className="text-[9px] md:text-[10px] uppercase font-bold tracking-[0.2em] text-zinc-400">Personal AI Search</span>
          </div>
          <h1 className="text-5xl md:text-8xl font-bold tracking-tighter text-white">
            Knowledge <span className="text-zinc-500 italic">Vault</span>
          </h1>
          <p className="text-zinc-500 max-w-xl mx-auto text-sm md:text-lg font-light tracking-wide leading-relaxed px-4">
            Private semantic intelligence for your documents.
            Zero noise, absolute focus.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Main Search Area */}
          <main className="lg:col-span-8 space-y-10 order-1 lg:order-2">
            <div className="relative group animate-in fade-in slide-in-from-bottom-6 duration-1000">
              <div className="absolute -inset-1 bg-gradient-to-r from-zinc-800 to-zinc-900 rounded-[2rem] blur opacity-25 group-focus-within:opacity-50 transition-opacity duration-1000"></div>
              <div className="relative flex items-center bg-[#050505] border border-zinc-800 focus-within:border-zinc-500 rounded-[1.5rem] md:rounded-[2rem] overflow-hidden transition-all duration-500 shadow-2xl">
                <Search className="ml-6 w-5 h-5 md:w-6 md:h-6 text-zinc-600 group-focus-within:text-zinc-300 transition-colors" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Query your knowledge..."
                  className="w-full bg-transparent px-5 py-5 md:py-7 text-base md:text-xl outline-none transition-all placeholder:text-zinc-800 text-zinc-100 font-light"
                />
                <button
                  onClick={runSearch}
                  disabled={loading || !query.trim()}
                  className="mr-3 md:mr-4 px-6 md:px-8 py-3 md:py-4 bg-white text-black hover:bg-zinc-200 disabled:bg-zinc-900 disabled:text-zinc-700 rounded-xl md:rounded-2xl text-[10px] md:text-xs font-black tracking-widest transition-all active:scale-95"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "EXECUTE"}
                </button>
              </div>
            </div>

            <div className="space-y-8">
              {error && (
                <div className="p-4 bg-red-900/20 border border-red-800 text-red-400 rounded-2xl text-[11px] font-medium flex items-center gap-3">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  {error}
                </div>
              )}
              {success && (
                <div className="p-4 bg-green-900/20 border border-green-800 text-green-400 rounded-2xl text-[11px] font-medium flex items-center gap-3">
                  <Sparkles className="w-4 h-4 text-green-600" />
                  {success}
                </div>
              )}

              <div className="flex items-end justify-between px-2">
                <h3 className="text-[10px] md:text-xs font-black tracking-[0.3em] uppercase text-zinc-600">
                  {loading ? "SEARCHING VAULT..." : results.length > 0 ? "TOP RELEVANT FRAGMENTS" : "IDLE ENGINE"}
                </h3>
                {results.length > 0 && (
                  <button
                    onClick={synthesizeAnswer}
                    disabled={generating}
                    className="flex items-center gap-2 px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-xl text-[9px] font-black uppercase tracking-widest hover:border-zinc-400 hover:text-white transition-all disabled:opacity-50"
                  >
                    {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                    {generating ? "Synthesizing..." : "Synthesize with AI"}
                  </button>
                )}
              </div>

              {aiAnswer && (
                <div className="relative group/ai animate-in fade-in slide-in-from-top-4 duration-700">
                  <div className="absolute -inset-0.5 bg-gradient-to-r from-zinc-500 to-zinc-800 rounded-3xl blur opacity-10"></div>
                  <div className="relative bg-[#0a0a0a] border border-zinc-700/50 p-8 rounded-3xl space-y-4 shadow-2xl">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-zinc-900 rounded-lg">
                        <Sparkles className="w-4 h-4 text-zinc-300" />
                      </div>
                      <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400">Vault Intelligence</span>
                    </div>
                    <p className="text-zinc-100 text-base md:text-lg leading-relaxed font-light whitespace-pre-wrap">
                      {aiAnswer}
                    </p>
                  </div>
                </div>
              )}

              {!results.length && !loading && (
                <div className="py-24 md:py-32 flex flex-col items-center justify-center space-y-6 border border-zinc-900/30 rounded-[3rem] bg-zinc-900/[0.02]">
                  <Database className="w-12 h-12 text-zinc-900" />
                  <div className="text-center space-y-2">
                    <p className="text-zinc-700 text-[10px] font-bold uppercase tracking-[0.3em]">Knowledge Awaits</p>
                    <p className="text-zinc-800 text-[10px] max-w-xs">Your semantic index is ready for retrieval.</p>
                  </div>
                </div>
              )}

              {loading && (
                <div className="space-y-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-40 bg-zinc-900/10 border border-zinc-900/50 animate-pulse rounded-[2.5rem]" />
                  ))}
                </div>
              )}

              <div className="grid grid-cols-1 gap-8">
                {results.map((r) => (
                  <article
                    key={r.id}
                    className="group relative bg-[#070707] border border-zinc-800/40 p-6 md:p-10 rounded-[2.5rem] hover:border-zinc-600 transition-all duration-700 hover:bg-[#090909]"
                  >
                    <div className="space-y-6">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center justify-center text-zinc-600 group-hover:text-zinc-300">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="text-[9px] font-black uppercase text-zinc-500 tracking-widest">{r.type || "DOC"}</span>
                              <ChevronRight className="w-3 h-3 text-zinc-800" />
                              <span className="text-sm font-bold text-zinc-200">{r.source.split(/[/\\]/).pop()}</span>
                            </div>
                            <div className="flex items-center gap-2 opacity-50">
                              <Clock className="w-3 h-3 text-zinc-700" />
                              <span className="text-[8px] text-zinc-700 font-bold uppercase tracking-widest">Semantic Match</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-[10px] font-black font-mono text-zinc-700">
                          {(r.score * 100).toFixed(1)}%
                        </div>
                      </div>
                      {r.snippets && r.snippets.length > 0 && (
                        <div className="space-y-3 mb-6">
                          <p className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-600">Primary Match</p>
                          <div className="space-y-2">
                            {r.snippets.map((snip, idx) => (
                              <div key={idx} className="p-3 bg-zinc-900/40 border-l-2 border-zinc-500 rounded-r-xl text-zinc-100 text-sm md:text-base leading-relaxed">
                                {textToHighlight(snip, query)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="space-y-3">
                        {r.snippets && r.snippets.length > 0 && (
                          <p className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-600">Full Context</p>
                        )}
                        <p className="text-zinc-400 text-sm md:text-base leading-relaxed md:leading-loose tracking-wide font-light opacity-60">
                          {query.trim() ? (
                            textToHighlight(r.text, query)
                          ) : (
                            r.text
                          )}
                        </p>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </main>

          {/* Sidebar Area */}
          <aside className="lg:col-span-4 space-y-8 order-2 lg:order-1 lg:sticky lg:top-12">
            <div className="bg-[#070707]/30 border border-zinc-800/50 rounded-[2rem] p-8 space-y-8 backdrop-blur-xl">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-zinc-600" />
                <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Vault Ingestion</h2>
              </div>
              <div className="space-y-4">
                <div className="relative border border-zinc-900 border-dashed rounded-2xl p-8 hover:bg-zinc-900/20 transition-all text-center cursor-pointer">
                  <input type="file" multiple onChange={onFileChange} className="absolute inset-0 opacity-0 cursor-pointer" />
                  <Upload className="w-8 h-8 text-zinc-800 mx-auto mb-3" />
                  <p className="text-[10px] font-black text-zinc-700 uppercase tracking-widest">
                    {files.length > 0 ? `${files.length} Ready` : "Drop PDF / MD"}
                  </p>
                </div>
                <button
                  onClick={uploadFiles}
                  disabled={uploading || !files.length}
                  className="w-full py-4 bg-zinc-900/50 text-zinc-400 hover:text-white rounded-2xl text-[10px] font-black tracking-widest border border-zinc-800/50 transition-all"
                >
                  {uploading ? "SYNCING..." : "SYNC TO VAULT"}
                </button>
              </div>
            </div>

            <div className="bg-[#070707]/30 border border-zinc-800/50 rounded-[2rem] p-8 space-y-8 backdrop-blur-xl">
              <div className="flex items-center gap-3">
                <Filter className="w-4 h-4 text-zinc-600" />
                <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Constraints</h2>
              </div>
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-2">
                  {DOC_TYPES.map((t) => (
                    <button
                      key={t}
                      onClick={() => toggleType(t)}
                      className={`px-3 py-3 rounded-xl text-[9px] font-black tracking-widest uppercase border transition-all ${types.includes(t)
                        ? "bg-zinc-100 border-zinc-100 text-black"
                        : "bg-transparent border-zinc-900 text-zinc-700 hover:border-zinc-700"
                        }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between text-[10px] font-black uppercase text-zinc-700 tracking-widest">
                    <span>Age</span>
                    <span>{maxAgeDays > 0 ? `${maxAgeDays}D` : "∞"}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={180}
                    value={maxAgeDays}
                    onChange={(e) => setMaxAgeDays(Number(e.target.value))}
                    className="w-full h-1 bg-zinc-900 rounded-full appearance-none accent-zinc-100"
                  />
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default App;
