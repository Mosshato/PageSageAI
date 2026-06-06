import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "http://localhost:8000/api";

function AIBtn({ children, onClick, color = "#6366f1", disabled = false, small = false, outline = false }) {
  const bg     = outline ? "transparent" : disabled ? "rgba(255,255,255,0.05)" : color;
  const fg     = outline ? color : disabled ? "rgba(255,255,255,0.2)" : "#fff";
  const border = outline ? `1px solid ${color}88` : "none";
  return (
    <button onClick={onClick} disabled={disabled}
      style={{ padding: small ? "6px 14px" : "9px 18px", background: bg, color: fg, border, fontSize: small ? "10px" : "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: disabled ? "not-allowed" : "pointer", borderRadius: "5px", transition: "opacity 0.15s", whiteSpace: "nowrap" }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.opacity = "0.8"; }}
      onMouseLeave={e => { e.currentTarget.style.opacity = "1"; }}
    >{children}</button>
  );
}

export default function AITeachDashboard() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const audioRef         = useRef(null);
  const chatEndRef       = useRef(null);
  const questionInputRef = useRef(null);
  const animPollRef      = useRef(null);

  const [courseInfo, setCourseInfo] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageData, setPageData]     = useState(null);
  const [pageLoading, setPageLoading] = useState(true);

  // phase: idle | playing | paused | questioning | loading | answered | deciding | finished
  const [phase, setPhase]           = useState("idle");
  const [messages, setMessages]     = useState([]);
  const [question, setQuestion]     = useState("");
  const [showInput, setShowInput]   = useState(false);
  const [savedTimestamp, setSavedTimestamp] = useState(0);
  const [lastAnswer, setLastAnswer] = useState("");
  const [ragLoading, setRagLoading] = useState(false);

  // Tab
  const [activeTab, setActiveTab] = useState("lecture");

  // Animation generation
  const [showAnimInput, setShowAnimInput]   = useState(false);
  const [animConcept, setAnimConcept]       = useState("");
  const [animSubmitting, setAnimSubmitting] = useState(false);
  const [animPollStatus, setAnimPollStatus] = useState(null); // null|'polling'|'ready'|'error'
  const [animError, setAnimError]           = useState(null);

  // Animations library
  const [animLibrary, setAnimLibrary]       = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [selectedAnim, setSelectedAnim]     = useState(null);

  // Quiz tab
  const [quizStatus, setQuizStatus]           = useState(null);
  const [quizQuestions, setQuizQuestions]     = useState([]);
  const [shuffledQuestions, setShuffledQuestions] = useState([]);
  const [quizAnswers, setQuizAnswers]         = useState({});
  const [quizSubmitting, setQuizSubmitting]   = useState(false);
  const [quizResult, setQuizResult]           = useState(null);
  const [quizLoading, setQuizLoading]         = useState(false);
  const quizPollRef                           = useRef(null);

  // ── Fetch page (messages nu se resetează la schimbarea paginii) ─────────────
  useEffect(() => {
    let active = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPageLoading(true);
    fetch(`${API}/ai-courses/${courseId}/page/${currentPage}/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => {
        if (!active) return;
        setPageData(data);
        if (data.total_pages) setCourseInfo({ total_pages: data.total_pages });
        if (audioRef.current) {
          audioRef.current.src = data.audio_url ?? "";
          audioRef.current.load();
          audioRef.current.currentTime = 0;
        }
        setPageLoading(false);
        setPhase("idle");
        setSavedTimestamp(0);
      })
      .catch(() => { if (active) setPageLoading(false); });
    return () => { active = false; };
  }, [currentPage, courseId, token]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, ragLoading]);

  useEffect(() => {
    if (showInput) questionInputRef.current?.focus();
  }, [showInput]);

  // Cleanup animation poll on unmount
  useEffect(() => {
    return () => clearInterval(animPollRef.current);
  }, []);

  // Load library on mount
  useEffect(() => {
    fetchAnimationsLibrary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  // ── Audio handlers ──────────────────────────────────────────────────────────
  function handlePlay() {
    audioRef.current?.play();
    setPhase("playing");
  }
  function handlePause() {
    audioRef.current?.pause();
    setPhase("paused");
  }
  function handleAudioEnded() { setPhase("deciding"); }

  // ── Navigare între pagini ────────────────────────────────────────────────────
  function goToPage(n) {
    const total = courseInfo?.total_pages ?? 1;
    if (n < 1 || n > total) return;
    audioRef.current?.pause();
    setShowInput(false);
    setCurrentPage(n);
    // messages NU se resetează
  }

  // ── Question flow ────────────────────────────────────────────────────────────
  function handleAskQuestion() {
    const ts = audioRef.current?.currentTime ?? 0;
    setSavedTimestamp(ts);
    audioRef.current?.pause();
    setShowInput(true);
    if (phase !== "deciding") setPhase("questioning");
  }

  async function submitQuestion() {
    const q = question.trim();
    if (!q) return;
    setQuestion("");
    setShowInput(false);
    setMessages(prev => [...prev, { role: "student", content: q }]);
    setRagLoading(true);
    setPhase("loading");

    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/ask/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      const answer = data.answer ?? data.error ?? "Could not get an answer.";
      setLastAnswer(answer);
      setMessages(prev => [...prev, { role: "ai", content: answer, showUnderstandButtons: true }]);
      setPhase("answered");
    } catch {
      setMessages(prev => [...prev, { role: "ai", content: "Could not reach the AI assistant. Please try again." }]);
      setPhase("paused");
    }
    setRagLoading(false);
  }

  function removeLastButtons() {
    setMessages(prev =>
      prev.map((m, i) => i === prev.length - 1 ? { ...m, showUnderstandButtons: false } : m)
    );
  }

  function handleUnderstood() {
    removeLastButtons();
    setPhase("deciding");
  }

  async function handleNotUnderstood() {
    removeLastButtons();
    setRagLoading(true);
    const lastStudentMsg = [...messages].reverse().find(m => m.role === "student");
    const q = lastStudentMsg?.content ?? "";
    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/reformulate/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question: q, previous_answer: lastAnswer }),
      });
      const data = await res.json();
      const answer = data.answer ?? "Could not reformulate.";
      setLastAnswer(answer);
      setMessages(prev => [...prev, { role: "ai", content: answer, showUnderstandButtons: true }]);
      setPhase("answered");
    } catch {
      setMessages(prev => [...prev, { role: "ai", content: "Could not reach the AI assistant." }]);
      setPhase("deciding");
    }
    setRagLoading(false);
  }

  // ── Continue / next page ─────────────────────────────────────────────────────
  function handleContinue() {
    if (audioRef.current) {
      audioRef.current.currentTime = savedTimestamp;
      audioRef.current.play();
    }
    setPhase("playing");
  }

  function handleNextPage() {
    const total = courseInfo?.total_pages ?? 0;
    if (currentPage >= total) { setPhase("finished"); return; }
    goToPage(currentPage + 1);
  }

  // ── Animation helpers ────────────────────────────────────────────────────────
  async function fetchAnimationsLibrary() {
    setLibraryLoading(true);
    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/animations/list/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setAnimLibrary(Array.isArray(data) ? data : []);
    } catch {
      // silent fail
    }
    setLibraryLoading(false);
  }

  async function submitAnimationRequest() {
    const concept = animConcept.trim();
    if (!concept) return;
    setAnimSubmitting(true);
    setAnimError(null);
    setAnimPollStatus(null);
    clearInterval(animPollRef.current);
    console.log("Token curent la poll:", token);
    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/animations/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ concept }),
      });
      const data = await res.json();

      if (data.status === "READY") {
        setAnimPollStatus("ready");
        setShowAnimInput(false);
        setAnimConcept("");
        setActiveTab("animations");
        fetchAnimationsLibrary();
      } else if (data.status === "ERROR") {
        setAnimPollStatus("error");
        setAnimError("Animation could not be generated, please try again later.");
      } else {
        const animId = data.animation_id;
        setAnimPollStatus("polling");
        animPollRef.current = setInterval(async () => {
          try {
            const pr = await fetch(`${API}/animations/${animId}/status/`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const pd = await pr.json();
            if (pd.status === "READY") {
              clearInterval(animPollRef.current);
              setAnimPollStatus("ready");
              setShowAnimInput(false);
              setAnimConcept("");
              setActiveTab("animations");
              fetchAnimationsLibrary();
            } else if (pd.status === "ERROR") {
              clearInterval(animPollRef.current);
              setAnimPollStatus("error");
              setAnimError(pd.error || "Animation could not be generated, please try again later.");
            }
          } catch { /* ignore poll errors */ }
        }, 4000);
      }
    } catch {
      setAnimPollStatus("error");
      setAnimError("Could not connect to the server. Please try again.");
    }
    setAnimSubmitting(false);
  }

  // ── Quiz helpers ─────────────────────────────────────────────────────────────
  function shuffleArray(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function buildShuffled(questions) {
    const qIndices = shuffleArray(questions.map((_, i) => i));
    return qIndices.map(origQIdx => {
      const q = questions[origQIdx];
      const optIndices = shuffleArray(q.options.map((_, i) => i));
      return {
        question: q.question,
        options: optIndices.map(oi => q.options[oi]),
        origQIdx,
        origOptMap: optIndices, // origOptMap[displayOptIdx] = originalOptIdx
      };
    });
  }

  async function fetchQuizStatus() {
    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/quiz/status/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setQuizStatus(data.status);
      return data;
    } catch { return null; }
  }

  async function fetchQuizQuestions() {
    setQuizLoading(true);
    try {
      const res = await fetch(`${API}/ai-courses/${courseId}/quiz/questions/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setQuizQuestions(data.questions);
        setShuffledQuestions(buildShuffled(data.questions));
        setQuizAnswers({});
        setQuizResult(null);
      }
    } catch { /* silent */ }
    setQuizLoading(false);
  }

  async function submitQuizAnswers() {
    if (Object.keys(quizAnswers).length < shuffledQuestions.length) return;
    setQuizSubmitting(true);
    try {
      // Reconstruct answers in original question/option order for backend
      const answers = new Array(quizQuestions.length).fill(0);
      shuffledQuestions.forEach((sq, displayIdx) => {
        const selectedDisplayOpt = quizAnswers[displayIdx] ?? 0;
        answers[sq.origQIdx] = sq.origOptMap[selectedDisplayOpt];
      });
      const res = await fetch(`${API}/ai-courses/${courseId}/quiz/attempt/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ answers }),
      });
      if (res.ok) {
        const data = await res.json();
        setQuizResult(data);
      }
    } catch { /* silent */ }
    setQuizSubmitting(false);
  }

  // Fetch quiz status when Quiz tab opens; poll if generating
  useEffect(() => {
    if (activeTab !== "quiz") return;
    fetchQuizStatus().then(data => {
      if (data?.status === "READY" && quizQuestions.length === 0) {
        fetchQuizQuestions();
      } else if (data?.status === "GENERATING" || data?.status === "PENDING") {
        quizPollRef.current = setInterval(async () => {
          const fresh = await fetchQuizStatus();
          if (fresh?.status === "READY") {
            clearInterval(quizPollRef.current);
            fetchQuizQuestions();
          } else if (fresh?.status === "ERROR") {
            clearInterval(quizPollRef.current);
          }
        }, 4000);
      }
    });
    return () => clearInterval(quizPollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, courseId]);

  // ── Derived ──────────────────────────────────────────────────────────────────
  const isPlaying  = phase === "playing";
  const canPlay    = ["idle", "paused"].includes(phase);
  const canAsk     = ["playing", "paused", "deciding"].includes(phase);
  const isDeciding = phase === "deciding";
  const isLoading  = phase === "loading";
  const isFinished = phase === "finished";
  const total      = courseInfo?.total_pages ?? 0;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#0a0a0a", display: "flex", flexDirection: "column", fontFamily: "monospace" }}>

      {/* Top bar */}
      <div style={{ height: "52px", background: "#111111", borderBottom: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", padding: "0 20px", gap: "16px", flexShrink: 0 }}>
        <button onClick={() => navigate(-1)}
          style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.5)", padding: "5px 12px", borderRadius: "4px", fontSize: "11px", fontFamily: "monospace", cursor: "pointer" }}
          onMouseEnter={e => e.currentTarget.style.color = "#fff"}
          onMouseLeave={e => e.currentTarget.style.color = "rgba(255,255,255,0.5)"}
        >← Back</button>

        <span style={{ fontSize: "13px", color: "#fff", fontWeight: 700, fontFamily: "'Georgia', serif", flex: 1 }}>Teach using AI</span>

        {/* Navigare pagini */}
        {total > 0 && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage <= 1}
              style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: currentPage <= 1 ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.6)", padding: "4px 10px", borderRadius: "4px", fontSize: "14px", fontFamily: "monospace", cursor: currentPage <= 1 ? "not-allowed" : "pointer" }}
            >‹</button>
            <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", letterSpacing: "0.1em", minWidth: "70px", textAlign: "center" }}>
              {currentPage} / {total}
            </span>
            <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage >= total}
              style={{ background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: currentPage >= total ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.6)", padding: "4px 10px", borderRadius: "4px", fontSize: "14px", fontFamily: "monospace", cursor: currentPage >= total ? "not-allowed" : "pointer" }}
            >›</button>
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

        {/* Left panel — imaginea paginii */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "24px", background: "#0d0d0d", borderRight: "1px solid rgba(255,255,255,0.07)", gap: "16px", overflow: "hidden" }}>
          {pageLoading ? (
            <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px" }}>Loading page...</div>
          ) : pageData ? (
            <>
              <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.35)", letterSpacing: "0.15em" }}>
                PAGE {currentPage} / {total || "?"}
              </div>
              <img src={pageData.image_url} alt={`Page ${currentPage}`}
                style={{ maxWidth: "100%", maxHeight: "calc(100vh - 140px)", objectFit: "contain", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}
              />
            </>
          ) : (
            <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px" }}>Could not load page.</div>
          )}
        </div>

        {/* Right panel — control AI */}
        <div style={{ width: "460px", flexShrink: 0, display: "flex", flexDirection: "column", background: "#111111" }}>

          {/* Tab switcher */}
          <div style={{
            display: "flex", height: "36px", flexShrink: 0,
            borderBottom: "1px solid rgba(255,255,255,0.07)", background: "#111111"
          }}>
            {["lecture", "animations", "quiz"].map(tab => (
              <button key={tab} onClick={() => {
                setActiveTab(tab);
                if (tab === "animations") fetchAnimationsLibrary();
              }}
                style={{
                  flex: 1, background: "transparent", border: "none",
                  borderBottom: activeTab === tab ? "2px solid #6366f1" : "2px solid transparent",
                  color: activeTab === tab ? "#6366f1" : "rgba(255,255,255,0.3)",
                  fontSize: "10px", fontFamily: "monospace", fontWeight: 700,
                  letterSpacing: "0.15em", textTransform: "uppercase", cursor: "pointer",
                  transition: "color 0.15s"
                }}
              >
                {tab === "lecture" ? "◉ Lecture" : tab === "animations" ? "⬡ Animations" : "◈ Quiz"}
              </button>
            ))}
          </div>

          <audio ref={audioRef} onEnded={handleAudioEnded} style={{ display: "none" }} />

          {activeTab === "lecture" && (
            <>
              {/* Controale audio */}
              <div style={{ padding: "14px 18px", borderBottom: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", gap: "10px", flexShrink: 0, flexWrap: "wrap" }}>
                {canPlay && (
                  <AIBtn onClick={handlePlay} disabled={!pageData?.audio_url || pageLoading}>
                    {phase === "idle" ? "▶ Start" : "▶ Resume"}
                  </AIBtn>
                )}
                {isPlaying && (
                  <AIBtn onClick={handlePause} color="#f59e0b">⏸ Pause</AIBtn>
                )}
                {canAsk && !showInput && (
                  <AIBtn onClick={handleAskQuestion} color="#10b981" outline small>Ask a Question</AIBtn>
                )}
                {canAsk && !showInput && !showAnimInput && (
                  <AIBtn onClick={() => setShowAnimInput(true)} color="#8b5cf6" outline small>
                    ⊕ Animate
                  </AIBtn>
                )}
                {isLoading && (
                  <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>AI is thinking...</span>
                )}
                {isFinished && (
                  <span style={{ fontSize: "11px", color: "#10b981" }}>✓ Course completed!</span>
                )}
                {animPollStatus === "polling" && (
                  <span style={{ fontSize: "10px", color: "#8b5cf6", letterSpacing: "0.05em" }}>
                    ⏳ Rendering animation...
                  </span>
                )}
                {animPollStatus === "error" && (
                  <span style={{ fontSize: "10px", color: "#ef4444", letterSpacing: "0.05em" }}>
                    ✗ {animError}
                  </span>
                )}
              </div>

              {/* Chat global */}
              <div style={{ flex: 1, overflowY: "auto", padding: "16px 18px", display: "flex", flexDirection: "column", gap: "12px" }}>
                {messages.length === 0 && (
                  <div style={{ textAlign: "center", padding: "32px 0", color: "rgba(255,255,255,0.15)", fontSize: "12px", lineHeight: 1.8 }}>
                    Press Start to begin the AI lecture.<br />
                    You can pause and ask questions at any time.
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "student" ? "flex-end" : "flex-start" }}>
                    <div style={{ fontSize: "9px", letterSpacing: "0.15em", color: "rgba(255,255,255,0.25)", marginBottom: "4px" }}>
                      {msg.role === "student" ? "YOU" : "AI PROFESSOR"}
                    </div>
                    <div style={msg.role === "student"
                      ? { maxWidth: "85%", background: "#3b82f618", border: "1px solid #3b82f633", borderRadius: "12px 12px 2px 12px", padding: "10px 14px", fontSize: "13px", color: "#fff", lineHeight: 1.6 }
                      : { maxWidth: "95%", background: "#0d0d0d", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px 12px 12px 2px", padding: "10px 14px", fontSize: "13px", color: "rgba(255,255,255,0.85)", lineHeight: 1.6 }
                    }>{msg.content}</div>

                    {msg.showUnderstandButtons && i === messages.length - 1 && (
                      <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
                        <button onClick={handleUnderstood}
                          style={{ padding: "7px 16px", background: "#10b981", color: "#fff", border: "none", borderRadius: "5px", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: "pointer" }}
                          onMouseEnter={e => e.currentTarget.style.opacity = "0.8"}
                          onMouseLeave={e => e.currentTarget.style.opacity = "1"}
                        >✓ Understood</button>
                        <button onClick={handleNotUnderstood} disabled={ragLoading}
                          style={{ padding: "7px 16px", background: "transparent", color: "#f97316", border: "1px solid #f9731688", borderRadius: "5px", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", cursor: ragLoading ? "not-allowed" : "pointer", opacity: ragLoading ? 0.5 : 1 }}
                          onMouseEnter={e => { if (!ragLoading) e.currentTarget.style.background = "#f9731618"; }}
                          onMouseLeave={e => { e.currentTarget.style.background = "transparent"; }}
                        >✗ Explain differently</button>
                      </div>
                    )}
                  </div>
                ))}

                {ragLoading && (
                  <div style={{ alignSelf: "flex-start" }}>
                    <div style={{ fontSize: "9px", letterSpacing: "0.15em", color: "rgba(255,255,255,0.25)", marginBottom: "4px" }}>AI PROFESSOR</div>
                    <div style={{ background: "#0d0d0d", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "12px 12px 12px 2px", padding: "10px 14px", fontSize: "13px", color: "rgba(255,255,255,0.3)", fontStyle: "italic" }}>Thinking...</div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Deciding: opțiuni după terminarea narației */}
              {isDeciding && (
                <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.07)", display: "flex", flexDirection: "column", gap: "8px", flexShrink: 0 }}>
                  <div style={{ fontSize: "10px", letterSpacing: "0.15em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase" }}>What would you like to do?</div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    {savedTimestamp > 0 && (
                      <AIBtn onClick={handleContinue} color="#3b82f6">↩ Continue</AIBtn>
                    )}
                    {currentPage < total ? (
                      <AIBtn onClick={handleNextPage} color="#6366f1">→ Next Page</AIBtn>
                    ) : (
                      <AIBtn onClick={() => setPhase("finished")} color="#10b981">✓ Finish</AIBtn>
                    )}
                  </div>
                </div>
              )}

              {/* Input întrebare */}
              {showInput && (
                <div style={{ padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.07)", display: "flex", gap: "8px", flexShrink: 0 }}>
                  <input
                    ref={questionInputRef}
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && submitQuestion()}
                    placeholder="Ask your question..."
                    style={{ flex: 1, padding: "9px 12px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.12)", color: "#fff", fontSize: "13px", fontFamily: "monospace", outline: "none", borderRadius: "6px" }}
                    onFocus={e => e.currentTarget.style.borderColor = "#6366f1"}
                    onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"}
                  />
                  <AIBtn onClick={submitQuestion} disabled={!question.trim()} small>Send</AIBtn>
                  <button onClick={() => { setShowInput(false); if (phase === "questioning") setPhase("paused"); }}
                    style={{ padding: "6px 10px", background: "transparent", border: "1px solid rgba(255,255,255,0.1)", color: "rgba(255,255,255,0.35)", fontSize: "10px", fontFamily: "monospace", borderRadius: "5px", cursor: "pointer" }}>✕</button>
                </div>
              )}

              {/* Animation concept input */}
              {showAnimInput && (
                <div style={{
                  padding: "12px 16px", borderTop: "1px solid rgba(255,255,255,0.07)",
                  display: "flex", flexDirection: "column", gap: "10px", flexShrink: 0
                }}>
                  {/* Info callout */}
                  <div style={{
                    fontSize: "11px", color: "rgba(255,255,255,0.45)", lineHeight: 1.7,
                    background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.2)",
                    borderRadius: "6px", padding: "10px 12px"
                  }}>
                    <strong style={{ color: "rgba(139,92,246,0.9)" }}>ℹ What is a concept?</strong>
                    <br />
                    A concept can be a <em>mathematical function</em> (e.g. Binary Search, Fourier Transform,
                    Gradient Descent), an <em>algorithm visualization</em> (e.g. Bubble Sort step-by-step,
                    BFS/DFS traversal, Dijkstra&apos;s shortest path), or any computational process that benefits
                    from a visual, step-by-step explanation. The animation is generated and rendered
                    automatically — this typically takes 1–3 minutes.
                  </div>

                  {/* Input row */}
                  <div style={{ display: "flex", gap: "8px" }}>
                    <input
                      value={animConcept}
                      onChange={e => setAnimConcept(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && submitAnimationRequest()}
                      placeholder="Describe the concept to animate..."
                      disabled={animSubmitting}
                      style={{
                        flex: 1, padding: "9px 12px",
                        background: "rgba(255,255,255,0.04)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        color: "#fff", fontSize: "13px", fontFamily: "monospace",
                        outline: "none", borderRadius: "6px",
                        opacity: animSubmitting ? 0.5 : 1
                      }}
                      onFocus={e => e.currentTarget.style.borderColor = "#8b5cf6"}
                      onBlur={e => e.currentTarget.style.borderColor = "rgba(255,255,255,0.12)"}
                    />
                    <AIBtn
                      onClick={submitAnimationRequest}
                      disabled={!animConcept.trim() || animSubmitting}
                      color="#8b5cf6"
                      small
                    >
                      {animSubmitting ? "..." : "Generate"}
                    </AIBtn>
                    <button
                      onClick={() => { setShowAnimInput(false); setAnimConcept(""); }}
                      style={{
                        padding: "6px 10px", background: "transparent",
                        border: "1px solid rgba(255,255,255,0.1)",
                        color: "rgba(255,255,255,0.35)", fontSize: "10px",
                        fontFamily: "monospace", borderRadius: "5px", cursor: "pointer"
                      }}
                    >✕</button>
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === "animations" && (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

              {/* Header + generate button */}
              <div style={{ padding: "12px 16px", borderBottom: "1px solid rgba(255,255,255,0.07)", flexShrink: 0 }}>
                <div style={{ fontSize: "10px", color: "rgba(255,255,255,0.3)", letterSpacing: "0.15em", marginBottom: "10px" }}>
                  ANIMATION LIBRARY — {animLibrary.length} CONCEPT{animLibrary.length !== 1 ? "S" : ""}
                </div>
                <AIBtn
                  onClick={() => { setActiveTab("lecture"); setShowAnimInput(true); }}
                  color="#8b5cf6"
                  small
                >
                  + Generate New Animation
                </AIBtn>
              </div>

              {/* Library list */}
              <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px", display: "flex", flexDirection: "column", gap: "8px" }}>

                {libraryLoading && (
                  <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px", textAlign: "center", paddingTop: "24px" }}>
                    Loading animations...
                  </div>
                )}

                {!libraryLoading && animLibrary.length === 0 && (
                  <div style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px", textAlign: "center", paddingTop: "24px", lineHeight: 1.8 }}>
                    No animations yet.<br />Generate your first one!
                  </div>
                )}

                {animLibrary.map(anim => {
                  const isSelected = selectedAnim?.id === anim.id;
                  const statusColor = anim.status === "READY" ? "#10b981"
                    : anim.status === "ERROR" ? "#ef4444"
                    : "#f59e0b";
                  const statusBg = anim.status === "READY" ? "rgba(16,185,129,0.08)"
                    : anim.status === "ERROR" ? "rgba(239,68,68,0.08)"
                    : "rgba(245,158,11,0.08)";

                  return (
                    <div key={anim.id}
                      onClick={() => { if (anim.status === "READY") setSelectedAnim(isSelected ? null : anim); }}
                      style={{
                        background: isSelected ? "rgba(99,102,241,0.1)" : "rgba(255,255,255,0.03)",
                        border: `1px solid ${isSelected ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.08)"}`,
                        borderRadius: "8px", padding: "10px 12px",
                        cursor: anim.status === "READY" ? "pointer" : "default",
                        transition: "border-color 0.15s, background 0.15s"
                      }}
                    >
                      {/* Concept label + status */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px" }}>
                        <span style={{
                          fontSize: "13px", color: "#fff", flex: 1,
                          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
                        }}>
                          {anim.concept}
                        </span>
                        <span style={{
                          fontSize: "9px", fontWeight: 700, letterSpacing: "0.1em",
                          textTransform: "uppercase", padding: "2px 7px", borderRadius: "4px",
                          background: statusBg, color: statusColor,
                          border: `1px solid ${statusColor}44`, flexShrink: 0
                        }}>
                          {anim.status}
                        </span>
                      </div>

                      {/* Date */}
                      <div style={{ fontSize: "10px", color: "rgba(255,255,255,0.25)", marginTop: "4px" }}>
                        {new Date(anim.created_at).toLocaleDateString("en-US", {
                          month: "short", day: "numeric", year: "numeric",
                          hour: "2-digit", minute: "2-digit"
                        })}
                      </div>

                      {/* Error message */}
                      {anim.status === "ERROR" && (
                        <div style={{ fontSize: "11px", color: "#ef444488", marginTop: "6px" }}>
                          {anim.error}
                        </div>
                      )}

                      {/* Video player (only when selected) */}
                      {isSelected && anim.video_url && (
                        <video
                          controls
                          src={anim.video_url}
                          style={{
                            width: "100%", marginTop: "10px", borderRadius: "6px",
                            border: "1px solid rgba(255,255,255,0.1)", background: "#000"
                          }}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === "quiz" && (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

              {/* NOT_GENERATED */}
              {(quizStatus === "NOT_GENERATED" || quizStatus === null) && !quizLoading && (
                <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "12px", padding: "32px", textAlign: "center" }}>
                  <div style={{ fontSize: "32px", opacity: 0.3 }}>◈</div>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", lineHeight: 1.8 }}>
                    No quiz has been generated for this course yet.<br />
                    Your teacher can generate one from the class dashboard.
                  </div>
                </div>
              )}

              {/* Loading */}
              {quizLoading && (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>Loading quiz...</span>
                </div>
              )}

              {/* Generating / Pending */}
              {(quizStatus === "GENERATING" || quizStatus === "PENDING") && (
                <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "12px", padding: "32px", textAlign: "center" }}>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#f59e0b", letterSpacing: "0.1em" }}>⏳ AI is generating the quiz...</div>
                  <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>This may take a minute. The page will update automatically.</div>
                </div>
              )}

              {/* Error */}
              {quizStatus === "ERROR" && (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "32px" }}>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#ef4444", textAlign: "center" }}>
                    The quiz could not be generated. Please ask your teacher to try again.
                  </div>
                </div>
              )}

              {/* Quiz questions */}
              {quizStatus === "READY" && shuffledQuestions.length > 0 && !quizResult && (
                <div style={{ flex: 1, overflowY: "auto", padding: "16px 18px", display: "flex", flexDirection: "column", gap: "20px" }}>
                  <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.4)", letterSpacing: "0.1em" }}>
                    QUIZ — {shuffledQuestions.length} QUESTIONS · Select one answer per question
                  </div>

                  {shuffledQuestions.map((q, qi) => (
                    <div key={qi} style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${quizAnswers[qi] !== undefined ? "rgba(99,102,241,0.3)" : "rgba(255,255,255,0.07)"}`, borderRadius: "8px", padding: "14px 16px" }}>
                      <div style={{ fontSize: "13px", color: "#fff", lineHeight: 1.6, marginBottom: "12px" }}>
                        <span style={{ color: "rgba(255,255,255,0.35)", fontFamily: "monospace", fontSize: "11px" }}>{qi + 1}.{" "}</span>
                        {q.question}
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                        {q.options.map((opt, oi) => (
                          <div key={oi}
                            onClick={() => setQuizAnswers(prev => ({ ...prev, [qi]: oi }))}
                            style={{ padding: "8px 12px", borderRadius: "6px", cursor: "pointer", fontSize: "12px", fontFamily: "monospace", lineHeight: 1.5, background: quizAnswers[qi] === oi ? "rgba(99,102,241,0.15)" : "rgba(255,255,255,0.02)", border: `1px solid ${quizAnswers[qi] === oi ? "rgba(99,102,241,0.5)" : "rgba(255,255,255,0.07)"}`, color: quizAnswers[qi] === oi ? "#fff" : "rgba(255,255,255,0.6)", transition: "all 0.12s" }}
                          >
                            <span style={{ color: "rgba(255,255,255,0.3)", marginRight: "8px" }}>{["A", "B", "C", "D"][oi]}.</span>
                            {opt}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Submit bar */}
                  <div style={{ position: "sticky", bottom: 0, background: "linear-gradient(to top, #111111 70%, transparent)", padding: "16px 0 8px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)" }}>
                      {Object.keys(quizAnswers).length} / {shuffledQuestions.length} answered
                    </div>
                    <button
                      onClick={submitQuizAnswers}
                      disabled={quizSubmitting || Object.keys(quizAnswers).length < shuffledQuestions.length}
                      style={{ width: "100%", padding: "11px", background: Object.keys(quizAnswers).length < shuffledQuestions.length ? "rgba(255,255,255,0.05)" : "#6366f1", color: Object.keys(quizAnswers).length < shuffledQuestions.length ? "rgba(255,255,255,0.2)" : "#fff", border: "none", borderRadius: "6px", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", cursor: quizSubmitting ? "not-allowed" : "pointer" }}
                    >
                      {quizSubmitting ? "Submitting..." : "Submit Quiz"}
                    </button>
                  </div>
                </div>
              )}

              {/* Results */}
              {quizResult && (
                <div style={{ flex: 1, overflowY: "auto", padding: "16px 18px", display: "flex", flexDirection: "column", gap: "16px" }}>
                  {/* Score card */}
                  <div style={{ background: quizResult.score >= 70 ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)", border: `1px solid ${quizResult.score >= 70 ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`, borderRadius: "10px", padding: "20px", textAlign: "center" }}>
                    <div style={{ fontSize: "40px", fontWeight: 700, fontFamily: "monospace", color: quizResult.score >= 70 ? "#10b981" : "#ef4444", marginBottom: "4px" }}>
                      {quizResult.score}%
                    </div>
                    <div style={{ fontSize: "12px", fontFamily: "monospace", color: "rgba(255,255,255,0.5)" }}>
                      {quizResult.correct_count} correct out of {quizResult.total}
                    </div>
                  </div>

                  <button onClick={() => { setShuffledQuestions(buildShuffled(quizQuestions)); setQuizAnswers({}); setQuizResult(null); }}
                    style={{ padding: "9px", background: "transparent", border: "1px solid rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.5)", borderRadius: "6px", fontSize: "11px", fontFamily: "monospace", fontWeight: 700, letterSpacing: "0.1em", cursor: "pointer" }}>
                    ↩ Try Again
                  </button>

                  <div style={{ fontSize: "10px", fontFamily: "monospace", color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em" }}>QUESTION REVIEW</div>

                  {quizResult.results.map((r, i) => (
                    <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${r.is_correct ? "rgba(16,185,129,0.25)" : "rgba(239,68,68,0.25)"}`, borderRadius: "8px", padding: "12px 14px" }}>
                      <div style={{ fontSize: "12px", color: "#fff", lineHeight: 1.6, marginBottom: "8px", display: "flex", gap: "8px" }}>
                        <span style={{ color: r.is_correct ? "#10b981" : "#ef4444", flexShrink: 0 }}>{r.is_correct ? "✓" : "✗"}</span>
                        <span>{i + 1}. {r.question}</span>
                      </div>
                      {!r.is_correct && (
                        <div style={{ fontSize: "11px", fontFamily: "monospace", color: "rgba(255,255,255,0.4)", lineHeight: 1.7 }}>
                          <span style={{ color: "#ef4444" }}>Your answer: </span>{r.options[r.selected_index]}<br />
                          <span style={{ color: "#10b981" }}>Correct answer: </span>{r.options[r.correct_index]}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
