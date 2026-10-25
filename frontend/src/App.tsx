import { useCallback, useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  FileText,
  GraduationCap,
  LogOut,
  Menu,
  Plus,
  Sparkles,
  Target,
  Users,
  X,
} from "lucide-react";
import { api, getToken, setToken, setTokens, type Attempt, type NewStudent, type Progress, type Question, type Report, type SchoolClass, type SchoolStudent, type StudentPerformance, type Subject, type Topic, type User, type WorkCheck } from "./api";

const DJANGO_ADMIN_URL = `${(import.meta.env.VITE_API_URL ?? "http://localhost:8000/api").replace(/\/api\/?$/, "")}/admin/`;

function App() {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [error, setError] = useState("");

  const loadSubjects = useCallback(async () => {
    const rows = await api.subjects();
    setSubjects(rows);
  }, []);

  const finishLogin = useCallback(async (loggedInUser: User, redirect = true) => {
    setUser(loggedInUser);
    setError("");
    if (loggedInUser.role === "student" || loggedInUser.role === "school_admin") {
      await loadSubjects();
    }
    if (redirect) navigate(loggedInUser.role === "teacher" ? "/reports" : "/");
  }, [loadSubjects, navigate]);

  useEffect(() => {
    if (!getToken()) return;
    api.me()
      .then((currentUser) => finishLogin(currentUser, false))
      .catch(() => setToken(null));
  }, [finishLogin]);

  async function signOut() {
    setToken(null);
    setUser(null);
    setSubjects([]);
    navigate("/");
  }

  if (!user) {
    return <Login onLogin={finishLogin} onError={setError} error={error} />;
  }

  const isAdmin = user.role === "school_admin";
  const isTeacher = user.role === "teacher";
  const isPlatformAdmin = isAdmin && !user.school_code;
  return (
    <AppLayout
      user={user}
      subjects={subjects}
      error={error}
      setError={setError}
      onSignOut={signOut}
      isAdmin={isAdmin}
      isTeacher={isTeacher}
      isPlatformAdmin={isPlatformAdmin}
    />
  );
}

function AppLayout({
  user,
  subjects,
  error,
  setError,
  onSignOut,
  isAdmin,
  isTeacher,
  isPlatformAdmin,
}: {
  user: User;
  subjects: Subject[];
  error: string;
  setError: (value: string) => void;
  onSignOut: () => void;
  isAdmin: boolean;
  isTeacher: boolean;
  isPlatformAdmin: boolean;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenu, setMobileMenu] = useState(false);
  const activeLearning = location.pathname === "/" || location.pathname.startsWith("/subjects/") || location.pathname.startsWith("/topics/");
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand"><span className="brand-mark"><GraduationCap size={22} /></span><span>Suku<span className="brand-dot">.</span></span></div>
        <div className="school-tag">{user.school_name ?? "Suku learning"}</div>
        <nav className="nav-list">
          {!isTeacher && <button className={activeLearning ? "nav-link active" : "nav-link"} onClick={() => { navigate("/"); setMobileMenu(false); }}>
            <BookOpen size={18} /> {isAdmin ? "Learning library" : "My learning"}
          </button>}
          {isPlatformAdmin ? (
            <button className={location.pathname === "/reports" ? "nav-link active" : "nav-link"} onClick={() => { window.location.assign(DJANGO_ADMIN_URL); setMobileMenu(false); }}>
              <Users size={18} /> Manage schools
            </button>
          ) : isAdmin || isTeacher ? (
            <button className={location.pathname === "/reports" ? "nav-link active" : "nav-link"} onClick={() => { navigate("/reports"); setMobileMenu(false); }}>
              <Users size={18} /> School reports
            </button>
          ) : (
            <button className={location.pathname === "/progress" ? "nav-link active" : "nav-link"} onClick={() => { navigate("/progress"); setMobileMenu(false); }}>
              <Target size={18} /> My progress
            </button>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-mini"><span className="avatar">{(user.first_name || user.username).slice(0, 1).toUpperCase()}</span><span><strong>{user.first_name || user.username}</strong><small>{isAdmin ? "School admin" : isTeacher ? "Teacher" : user.grade_label ?? "Student"}</small></span></div>
          <button className="signout" onClick={onSignOut}><LogOut size={17} /> Sign out</button>
        </div>
      </aside>
      {mobileMenu && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileMenu(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileMenu(true)}><Menu size={22} /></button>
          <span className="topbar-context">{isPlatformAdmin ? "Platform administration" : isAdmin || isTeacher ? "School workspace" : "Your study space"}</span>
          <div className="topbar-profile"><span className="status-dot" /> {user.first_name || user.username}</div>
        </header>
        <section className="page-content">
          {error && <div className="alert" role="alert"><CircleHelp size={17} />{error}<button aria-label="Dismiss" onClick={() => setError("")}><X size={16} /></button></div>}
        <Routes>
          <Route path="/" element={isTeacher ? <Navigate to="/reports" replace /> : <Home user={user} subjects={subjects} onSubject={(subject) => navigate(`/subjects/${subject.id}`)} onAdminReports={() => isPlatformAdmin ? window.location.assign(DJANGO_ADMIN_URL) : navigate("/reports")} />} />
          <Route path="/subjects/:subjectId" element={isTeacher ? <Navigate to="/reports" replace /> : <TopicsRoute subjects={subjects} />} />
          <Route path="/topics/:topicId" element={isTeacher ? <Navigate to="/reports" replace /> : <LessonRoute user={user} />} />
          <Route path="/topics/:topicId/practice" element={isAdmin || isTeacher ? <Navigate to={isTeacher ? "/reports" : "/"} replace /> : <PracticeRoute onError={setError} />} />
          <Route path="/progress" element={user.role !== "student" ? <Navigate to={isTeacher ? "/reports" : "/"} replace /> : <ProgressPage />} />
          <Route path="/reports" element={isPlatformAdmin ? <Navigate to="/" replace /> : isAdmin || isTeacher ? <ReportsPage canManage={isAdmin} onError={setError} /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </section>
      </main>
    </div>
  );
}

function Login({ onLogin, onError, error }: { onLogin: (user: User) => Promise<void>; onError: (value: string) => void; error: string }) {
  const [mode, setMode] = useState<"login" | "school" | "student">("login");
  const [schoolCode, setSchoolCode] = useState("");
  const [schoolName, setSchoolName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [grade, setGrade] = useState(7);
  const [working, setWorking] = useState(false);
  const [notice, setNotice] = useState<{ detail: string; schoolName: string; schoolCode: string } | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setWorking(true);
    onError("");
    try {
      if (mode === "login") {
        const tokens = await api.login(schoolCode, username, password);
        setTokens(tokens.access, tokens.refresh);
        await onLogin(tokens.user);
      } else if (mode === "school") {
        const result = await api.registerSchool({
          school_name: schoolName,
          first_name: firstName,
          last_name: lastName,
          username,
          password,
        });
        setNotice({ detail: result.detail, schoolName: result.school_name, schoolCode: result.school_code });
        setPassword("");
      } else {
        const tokens = await api.registerStudent({
          school_code: schoolCode,
          first_name: firstName,
          last_name: lastName,
          username,
          password,
          grade,
        });
        setTokens(tokens.access, tokens.refresh);
        await onLogin(tokens.user);
      }
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-decoration"><div className="login-orb orb-one" /><div className="login-orb orb-two" /><div className="login-copy"><div className="brand brand-light"><span className="brand-mark"><GraduationCap size={22} /></span><span>Suku<span className="brand-dot">.</span></span></div><div className="login-manifesto"><span className="eyebrow light-eyebrow"><Sparkles size={14} /> YOUR NEXT CHAPTER STARTS HERE</span><h1>Little by little,<br />you learn a lot.</h1><p>A brighter way to build confidence, one question at a time.</p></div><div className="login-footnote">Made for curious minds in Ghana <span>✳</span></div></div></div>
      <div className="login-form-wrap"><form className="login-form" onSubmit={submit}>
        <div className="mobile-brand brand"><span className="brand-mark"><GraduationCap size={22} /></span><span>Suku<span className="brand-dot">.</span></span></div>
        <span className="eyebrow">{mode === "login" ? "WELCOME BACK" : "JOIN SUKU"}</span><h2>{mode === "login" ? "Ready to learn?" : mode === "school" ? "Register your school" : "Create your student account"}</h2><p className="form-intro">{mode === "login" ? "Sign in with the account your school gave you." : mode === "school" ? "Your school account will be reviewed before it can sign in." : "Use the school code shared by your administrator."}</p>
        {error && <div className="alert login-alert" role="alert">{error}</div>}
        {notice && <div className="success-notice registration-notice"><Check size={16} /><span>{notice.detail}<br /><strong>School code: {notice.schoolCode}</strong><br />Keep this code safe and share it with your students after approval.</span></div>}
        {mode === "school" && <><label htmlFor="school-name">School name</label><input id="school-name" autoComplete="organization" value={schoolName} onChange={(event) => setSchoolName(event.target.value)} required maxLength={200} /></>}
        {mode === "student" && <><label htmlFor="school-code">School code</label><input id="school-code" autoComplete="organization" value={schoolCode} onChange={(event) => setSchoolCode(event.target.value)} required placeholder="Ask your school administrator" /></>}
        {mode !== "login" && <div className="name-fields"><div><label htmlFor="first-name">First name</label><input id="first-name" autoComplete="given-name" value={firstName} onChange={(event) => setFirstName(event.target.value)} required maxLength={150} /></div><div><label htmlFor="last-name">Last name</label><input id="last-name" autoComplete="family-name" value={lastName} onChange={(event) => setLastName(event.target.value)} required maxLength={150} /></div></div>}
        {mode === "student" && <><label htmlFor="student-grade">Grade</label><select id="student-grade" className="auth-select" value={grade} onChange={(event) => setGrade(Number(event.target.value))}><option value={7}>Grade 7 / JHS 1</option><option value={8}>Grade 8 / JHS 2</option><option value={9}>Grade 9 / JHS 3</option></select></>}
        <label htmlFor="username">Username</label><input id="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required maxLength={150} placeholder={mode === "login" ? "Your school username" : "Choose a username"} />
        <label htmlFor="password">Password</label><input id="password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required maxLength={256} placeholder={mode === "login" ? "Your password" : "At least 8 characters"} />
        <button className="button button-primary login-submit" disabled={working}>{working ? "Please wait…" : mode === "login" ? "Sign in" : mode === "school" ? "Request school registration" : "Create student account"}<ArrowRight size={17} /></button>
        {mode === "login" ? <div className="auth-mode-toggle"><span>New to Suku?</span><button type="button" className="auth-link" onClick={() => { setMode("student"); setNotice(null); onError(""); }}>Sign up as a student</button><button type="button" className="auth-link" onClick={() => { setMode("school"); setNotice(null); onError(""); }}>Register a school</button></div> : <button type="button" className="auth-link auth-back" onClick={() => { setMode("login"); setNotice(null); onError(""); }}>Back to sign in</button>}
        {mode === "login" && <p className="login-help">Need help getting in? Ask your school administrator.</p>}
      </form></div>
    </div>
  );
}

function Home({ user, subjects, onSubject, onAdminReports }: { user: User; subjects: Subject[]; onSubject: (subject: Subject) => void; onAdminReports: () => void }) {
  const isAdmin = user.role === "school_admin";
  const isPlatformAdmin = isAdmin && !user.school_code;
  const greeting = user.first_name ? `Hi, ${user.first_name}` : `Hi, ${user.username}`;
  return (
    <>
      <div className="welcome-row"><div><span className="eyebrow">{isPlatformAdmin ? "PLATFORM OVERVIEW" : isAdmin ? "SCHOOL OVERVIEW" : "YOUR LEARNING SPACE"}</span><h1>{greeting} <span className="wave">✳</span></h1><p>{isPlatformAdmin ? "Browse published learning content or manage school access." : isAdmin ? "A quick look at your school's learning space." : "Every question is a step forward. What will you learn today?"}</p></div></div>
      {isAdmin ? <div className="admin-banner"><div><span className="eyebrow light-eyebrow">{isPlatformAdmin ? "PLATFORM ADMIN" : "SCHOOL ADMIN"}</span><h2>{isPlatformAdmin ? "Manage schools and learning access." : "Help your students find their stride."}</h2><p>{isPlatformAdmin ? "Open the admin console to activate schools and set up their term subscriptions." : "Review learning activity and add student accounts for your school."}</p><button className="button button-light" onClick={onAdminReports}>{isPlatformAdmin ? "Manage schools" : "View school reports"} <ArrowRight size={16} /></button></div><div className="banner-illustration"><Users size={46} /></div></div> : <StudentWelcome />}
      <div className="section-heading"><div><span className="eyebrow">{isAdmin ? "CONTENT LIBRARY" : "PICK UP WHERE YOU LIKE"}</span><h2>{isAdmin ? "Study subjects" : "Explore your subjects"}</h2></div><span className="subject-count">{subjects.length} {subjects.length === 1 ? "subject" : "subjects"}</span></div>
      {subjects.length ? <div className="subject-grid">{subjects.map((subject, index) => <button className={`subject-card card-tone-${index % 3}`} key={subject.id} onClick={() => onSubject(subject)}><span className="subject-icon">{subject.name.toLowerCase().includes("math") ? "∑" : subject.name.toLowerCase().includes("science") ? "✳" : "Aa"}</span><span className="card-arrow"><ArrowRight size={18} /></span><span className="subject-name">{subject.name}</span><span className="subject-description">{subject.description || "Explore lessons and practice questions."}</span><span className="subject-meta"><BookOpen size={14} /> {subject.topic_count} {subject.topic_count === 1 ? "topic" : "topics"}</span></button>)}</div> : <div className="empty-state"><BookOpen size={27} /><h3>Your learning library is getting ready</h3><p>Published subjects will appear here when your school adds syllabus content.</p></div>}
    </>
  );
}

function StudentWelcome() {
  return <div className="study-banner"><div className="study-banner-copy"><span className="eyebrow light-eyebrow">A LITTLE PROGRESS ADDS UP</span><h2>Curiosity looks good on you.</h2><p>Pick a subject and take one small step today.</p></div><div className="banner-stamp"><Sparkles size={26} /><span>YOU'VE<br />GOT THIS</span></div><div className="banner-swoop" /></div>;
}

function Topics({ subject, initialGrade, onBack, onOpen }: { subject: Subject; initialGrade: number | null; onBack: () => void; onOpen: (topic: Topic) => void }) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [grade, setGrade] = useState<number | null>(initialGrade);
  const isMathematics = subject.name.toLowerCase().includes("math");
  useEffect(() => {
    if (isMathematics && grade === null) {
      setTopics([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    api.topics(subject.id, grade ?? undefined)
      .then(setTopics)
      .catch((reason) => setError(errorText(reason)))
      .finally(() => setLoading(false));
  }, [subject.id, grade, isMathematics]);
  return <>
    <button className="back-link" onClick={grade !== null && isMathematics ? () => setGrade(null) : onBack}><ArrowLeft size={16} /> {grade !== null && isMathematics ? "Choose another grade" : "All subjects"}</button>
    <div className="page-title-row"><div><span className="eyebrow">{subject.name.toUpperCase()}</span><h1>{isMathematics && grade === null ? "Choose your grade" : "Choose a topic"}</h1><p>{isMathematics && grade === null ? "Pick the level you want to practise." : "Work through a topic at your own pace."}</p></div></div>
    {isMathematics && grade === null ? <div className="grade-grid">{[7, 8, 9].map((level) => <button className="grade-card" key={level} onClick={() => { setError(""); setGrade(level); }}><span className="grade-card-number">{level}</span><span><strong>Grade {level}</strong><small>JHS {level - 6}</small></span><ChevronRight size={19} /></button>)}</div> : <>
      {error && <div className="alert" role="alert">{error}</div>}
      {loading ? <div className="loading-line">Loading topics…</div> : topics.length ? <div className="topic-list">{topics.map((topic, index) => <button className="topic-card" key={topic.id} onClick={() => onOpen(topic)}><span className="topic-number">{String(index + 1).padStart(2, "0")}</span><span className="topic-copy"><strong>{topic.title}</strong><small>{topic.summary || "Read the lesson, then practise what you learned."}</small></span>{topic.term && <span className="topic-term">Term {topic.term}</span>}<span className="topic-question-count">{topic.question_count} questions</span><ChevronRight size={19} /></button>)}</div> : <div className="empty-state"><BookOpen size={27} /><h3>No topics published just yet</h3><p>Your school will add learning content here soon.</p></div>}
    </>}
  </>;
}

function TopicsRoute({ subjects }: { subjects: Subject[] }) {
  const { subjectId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const subject = subjects.find((item) => item.id === Number(subjectId));
  if (!subject) return subjects.length ? <div className="empty-state"><BookOpen size={27} /><h3>Subject not found</h3><button className="button button-outline" onClick={() => navigate("/")}>All subjects</button></div> : <div className="loading-line">Loading subject…</div>;
  const gradeParam = Number(searchParams.get("grade"));
  const initialGrade = [7, 8, 9].includes(gradeParam) ? gradeParam : null;
  return <Topics subject={subject} initialGrade={initialGrade} onBack={() => navigate("/")} onOpen={(topic) => navigate(`/topics/${topic.id}${topic.grade ? `?grade=${topic.grade}` : ""}`)} />;
}

function LessonRoute({ user }: { user: User }) {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const [topic, setTopic] = useState<Topic | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    setTopic(null);
    setQuestions([]);
    Promise.all([api.topic(Number(topicId)), api.questions(Number(topicId))])
      .then(([loadedTopic, loadedQuestions]) => {
        setTopic(loadedTopic);
        setQuestions(loadedQuestions);
      })
      .catch((reason) => setError(errorText(reason)));
  }, [topicId]);
  if (error) return <div className="alert" role="alert">{error}</div>;
  if (!topic) return <div className="loading-line">Loading lesson…</div>;
  const objectiveCount = questions.filter((question) => question.kind === "mcq").length;
  const theoryCount = questions.filter((question) => question.kind === "theory").length;
  return (
    <Lesson
      topic={topic}
      canPractice={user.role === "student"}
      objectiveCount={objectiveCount}
      theoryCount={theoryCount}
      onBack={() => navigate(`/subjects/${topic.subject}${topic.grade ? `?grade=${topic.grade}` : ""}`)}
      onPractice={(kind) => navigate(`/topics/${topic.id}/practice?kind=${kind}`)}
    />
  );
}

function PracticeRoute({ onError }: { onError: (message: string) => void }) {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const selectedKind = searchParams.get("kind");
  const [topic, setTopic] = useState<Topic | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    setTopic(null);
    setQuestions([]);
    Promise.all([api.topic(Number(topicId)), api.questions(Number(topicId))])
      .then(([loadedTopic, loadedQuestions]) => {
        setTopic(loadedTopic);
        const matchingQuestions = selectedKind === "mcq" || selectedKind === "theory"
          ? loadedQuestions.filter((question) => question.kind === selectedKind)
          : loadedQuestions;
        setQuestions(loadedTopic.slug === "g9-paper-2-written-practice"
          ? matchingQuestions
          : mixQuestions(matchingQuestions));
      })
      .catch((reason) => setError(errorText(reason)));
  }, [topicId, selectedKind]);
  if (error) return <div className="alert" role="alert">{error}</div>;
  if (!topic) return <div className="loading-line">Loading practice…</div>;
  if (!questions.length) return <div className="empty-state"><BookOpen size={27} /><h3>No practice questions available</h3><p>Published questions for this topic will appear here.</p><button className="button button-outline" onClick={() => navigate(`/topics/${topic.id}`)}>Back to lesson</button></div>;
  return <Quiz key={`${topic.id}-${selectedKind ?? "all"}`} topic={topic} questions={questions} onBack={() => navigate(`/topics/${topic.id}${topic.grade ? `?grade=${topic.grade}` : ""}`)} onError={onError} />;
}

function mixQuestions(questions: Question[]) {
  const shuffle = <T,>(items: T[]) => {
    const shuffled = [...items];
    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const other = Math.floor(Math.random() * (index + 1));
      [shuffled[index], shuffled[other]] = [shuffled[other], shuffled[index]];
    }
    return shuffled;
  };
  const mcq = shuffle(questions.filter((question) => question.kind === "mcq"));
  const theory = shuffle(questions.filter((question) => question.kind === "theory"));
  const mixed: Question[] = [];
  const firstKind = Math.random() < 0.5 ? "mcq" : "theory";
  while (mcq.length || theory.length) {
    const preferred = mixed.length % 2 === 0
      ? (firstKind === "mcq" ? mcq : theory)
      : (firstKind === "mcq" ? theory : mcq);
    const fallback = preferred === mcq ? theory : mcq;
    const next = preferred.length ? preferred.pop() : fallback.pop();
    if (next) mixed.push(next);
  }
  return mixed;
}

function Lesson({ topic, canPractice, objectiveCount, theoryCount, onBack, onPractice }: {
  topic: Topic;
  canPractice: boolean;
  objectiveCount: number;
  theoryCount: number;
  onBack: () => void;
  onPractice: (kind: "mcq" | "theory") => void;
}) {
  return <>
    <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to topics</button>
    <article className="lesson-card">
      <span className="eyebrow">{topic.grade ? `GRADE ${topic.grade} · TERM ${topic.term}` : "TAKE YOUR TIME · LEARN AT YOUR PACE"}</span>
      <h1>{topic.title}</h1>
      {topic.summary && <p className="lesson-summary">{topic.summary}</p>}
      <section className="lesson-section">
        <span className="lesson-step">STEP 1 · LEARN THE IDEA</span>
        <h2>Lesson and key ideas</h2>
        <div className="lesson-content">{topic.content || "This lesson is being prepared. Read the key ideas, then practise below."}</div>
      </section>
      {canPractice && <section className="topic-practice-section">
        <span className="lesson-step">STEP 2 · PRACTISE ON PAPER</span>
        <h2>Choose how you want to practise</h2>
        <p>Work each question out with pen and paper first. Then choose the answer in Suku and study the steps in the solution.</p>
        <div className="topic-practice-grid">
          <button className="topic-practice-card objective-practice" disabled={!objectiveCount} onClick={() => onPractice("mcq")}>
            <span className="practice-card-icon"><Target size={19} /></span>
            <span className="practice-card-copy"><strong>Objective practice</strong><small>Short questions · choose A, B, C or D</small></span>
            <span className="practice-card-count">{objectiveCount} questions</span>
            <ArrowRight size={17} />
          </button>
          <button className="topic-practice-card theory-practice" disabled={!theoryCount} onClick={() => onPractice("theory")}>
            <span className="practice-card-icon"><FileText size={19} /></span>
            <span className="practice-card-copy"><strong>Theory practice</strong><small>Show every step on paper · choose A, B, C or D</small></span>
            <span className="practice-card-count">{theoryCount} questions</span>
            <ArrowRight size={17} />
          </button>
        </div>
      </section>}
    </article>
  </>;
}

function WorkedSolution({ text }: { text: string }) {
  return (
    <div className="worked-solution">
      {text.split(/\r?\n/).map((line, index) => {
        const content = line.trim();
        if (!content) return <div key={index} className="solution-spacing" aria-hidden="true" />;

        const step = content.match(/^Step\s+(\d+)\s*:\s*(.*)$/i);
        if (step) {
          return (
            <div className="solution-step" key={index}>
              <span className="solution-step-number">{step[1]}</span>
              <p>{step[2]}</p>
            </div>
          );
        }

        const note = content.match(/^(Check|Answer)\s*:\s*(.*)$/i);
        if (note) {
          const isAnswer = note[1].toLowerCase() === "answer";
          return (
            <div className={`solution-note ${isAnswer ? "solution-answer" : "solution-check"}`} key={index}>
              <strong>{isAnswer ? "Answer" : "Check"}</strong>
              <span>{note[2]}</span>
            </div>
          );
        }

        const section = content.match(/^([A-Z][A-Z -]{1,})\s*:\s*(.*)$/);
        if (section) {
          return (
            <div className="solution-section" key={index}>
              <strong>{section[1]}</strong>
              <span>{section[2]}</span>
            </div>
          );
        }

        if (/^(Question\s+\d+|\([a-d]\)|\[[a-d]\])/i.test(content)) {
          return <h3 className="solution-heading" key={index}>{content}</h3>;
        }

        return <p className="solution-paragraph" key={index}>{content}</p>;
      })}
    </div>
  );
}

function Quiz({ topic, questions, onBack, onError }: { topic: Topic; questions: Question[]; onBack: () => void; onError: (message: string) => void }) {
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState("");
  const [paperStarted, setPaperStarted] = useState(false);
  const [paperQuestionIds, setPaperQuestionIds] = useState<number[]>([]);
  const [result, setResult] = useState<Attempt | null>(null);
  const [workFile, setWorkFile] = useState<File | null>(null);
  const [workCheck, setWorkCheck] = useState<WorkCheck | null>(null);
  const [working, setWorking] = useState(false);
  const [checkingWork, setCheckingWork] = useState(false);
  const [finished, setFinished] = useState(false);
  const isWrittenPaper = topic.slug === "g9-paper-2-written-practice";
  const practiceQuestions = isWrittenPaper
    ? questions.filter((item) => paperQuestionIds.includes(item.id))
    : questions;
  const practiceTitle = isWrittenPaper
    ? "Paper 2 · Written practice"
    : practiceQuestions.every((item) => item.kind === "theory")
      ? "Theory practice"
      : practiceQuestions.every((item) => item.kind === "mcq")
        ? "Objective practice"
        : "Practice time";
  const question = practiceQuestions[index];
  const questionNumber = isWrittenPaper
    ? question?.prompt.match(/^\d+/)?.[0] ?? String(index + 1).padStart(2, "0")
    : String(index + 1).padStart(2, "0");

  async function submit() {
    if (!selected.trim() || !question) return;
    setWorking(true);
    onError("");
    try {
      setResult(await api.submit(question.id, selected));
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }

  async function checkWork(event: React.FormEvent) {
    event.preventDefault();
    if (!workFile || !result) return;
    setCheckingWork(true);
    onError("");
    try {
      setWorkCheck(await api.checkWork(result.id, workFile));
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setCheckingWork(false);
    }
  }

  function next() {
    if (index + 1 >= practiceQuestions.length) {
      setFinished(true);
      return;
    }
    setIndex(index + 1);
    setSelected("");
    setResult(null);
    setWorkFile(null);
    setWorkCheck(null);
  }

  if (isWrittenPaper && !paperStarted) return <div className="paper-start-card">
    <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to topics</button>
    <section className="panel paper-instructions">
      <span className="eyebrow">MATHEMATICS · PAPER 2 PRACTICE</span>
      <h1>Choose four questions</h1>
      <p>This practice set has six longer, multi-step problems. Select any four to answer.</p>
      <p>Work each problem out with pen and paper first, then select the A–D answer that matches your result. After submitting, compare your working with the step-by-step solution and mark guide.</p>
      <div className="paper-choice-list">{questions.map((item, itemIndex) => {
        const checked = paperQuestionIds.includes(item.id);
        const disabled = !checked && paperQuestionIds.length >= 4;
        return <label className={`paper-choice ${disabled ? "paper-choice-disabled" : ""}`} key={item.id}>
          <input
            type="checkbox"
            checked={checked}
            disabled={disabled}
            onChange={() => setPaperQuestionIds((current) => checked
              ? current.filter((id) => id !== item.id)
              : [...current, item.id])}
          />
          <span><strong>Question {itemIndex + 1}</strong><small>{item.prompt.split("\n")[0]}</small></span>
          <span className={`difficulty difficulty-${item.difficulty}`}>{item.difficulty}</span>
        </label>;
      })}</div>
      <p className="paper-selection-count">{paperQuestionIds.length} of 4 selected</p>
      <button className="button button-primary" disabled={paperQuestionIds.length !== 4} onClick={() => setPaperStarted(true)}>
        Start selected questions <ArrowRight size={16} />
      </button>
    </section>
  </div>;

  if (finished) return <div className="completion-card"><span className="completion-icon"><Check size={30} /></span><span className="eyebrow">{isWrittenPaper ? "PAPER 2 PRACTICE COMPLETE" : "PRACTICE COMPLETE"}</span><h1>Nice work showing up.</h1><p>You finished {practiceQuestions.length} {practiceQuestions.length === 1 ? "question" : "questions"} in {topic.title}. Every bit of practice counts.</p><button className="button button-primary" onClick={onBack}>Back to learning <ArrowRight size={17} /></button></div>;
  return <>
    <button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to topics</button>
    <div className="quiz-layout">
      <div className="quiz-top"><div><span className="eyebrow">{topic.title.toUpperCase()}</span><h1>{practiceTitle}</h1></div><span className="question-progress">{index + 1} <span>of</span> {practiceQuestions.length}</span></div>
      <div className="progress-track"><div style={{ width: `${((index + (result ? 1 : 0)) / practiceQuestions.length) * 100}%` }} /></div>
      <article className="question-card">
        <div className="question-label"><span>QUESTION {questionNumber}</span><span className={`question-kind ${question.kind}`}>{question.kind === "theory" ? "Theory · show your working" : "Objective question"}</span><span className={`difficulty difficulty-${question.difficulty}`}>{question.difficulty}</span></div>
        {question.options.length > 0 && <p className="paper-reminder">{question.kind === "theory" ? "Work the question out with pen and paper first. Then choose the A–D answer that matches your result." : "Try the question with pen and paper first, then choose the answer that matches your working."}</p>}
        <h2>{question.prompt}</h2>
        {question.kind === "theory" && question.options.length > 0 && <div className="theory-working-guide">
          <strong>Show these steps in your exercise book:</strong>
          <ol>
            <li>Write the rule, method or formula you need.</li>
            <li>Put the given numbers into it and show each calculation.</li>
            <li>Check your result, then choose the matching A–D answer.</li>
          </ol>
        </div>}
        {question.kind === "theory" && question.options.length === 0 ? <label className="written-answer-label" htmlFor="written-answer">Write your working for all parts here
          <textarea id="written-answer" className="written-answer" value={selected} onChange={(event) => setSelected(event.target.value)} disabled={!!result} placeholder={"Example:\n(a) Formula: ...\nWorking: ...\nAnswer: ..."} />
        </label> : <div className="answer-list">{question.options.map((option, optionIndex) => {
          const isSelected = selected === option;
          const isCorrect = result?.correct_answer === option;
          const className = result ? (isCorrect ? "answer-option answer-correct" : isSelected ? "answer-option answer-wrong" : "answer-option") : isSelected ? "answer-option answer-selected" : "answer-option";
          return <button key={`${question.id}-${option}`} className={className} disabled={!!result} onClick={() => setSelected(option)}><span className="option-letter">{String.fromCharCode(65 + optionIndex)}</span><span>{option}</span>{result && isCorrect && <Check size={18} className="answer-check" />}</button>;
        })}</div>}
        {result ? <>
          <div className={`feedback-box ${result.is_correct === null ? "feedback-written" : result.is_correct ? "feedback-good" : "feedback-review"}`}>
            <strong>{result.is_correct === null ? "Your written work is saved." : result.is_correct ? "That's right!" : "Let's learn from this one."}</strong>
            <p>{result.feedback}</p>
            {result.correct_answer && <p className="correct-answer"><strong>Correct answer:</strong> {result.correct_answer}</p>}
            {question.kind === "theory" && result.mark_guide && <div className="solution-copy"><strong>Mark guide</strong><p>{result.mark_guide}</p></div>}
            {result.worked_solution && <div className="solution-copy"><strong>Worked solution</strong><WorkedSolution text={result.worked_solution} /></div>}
            {question.kind === "theory" && !isWrittenPaper && question.work_check_available && <form className="work-upload" onSubmit={checkWork}>
              <label htmlFor="written-work"><FileText size={16} /> Optional: upload your working as a PDF for AI feedback</label>
              <input id="written-work" type="file" accept="application/pdf,.pdf" onChange={(event) => { setWorkFile(event.target.files?.[0] ?? null); setWorkCheck(null); }} />
              <small>Your PDF is sent to Google Gemini for checking. Suku does not retain a copy after checking. Do not include your name or school details.</small>
              <button className="button button-outline" disabled={!workFile || checkingWork}>{checkingWork ? "Checking your work…" : "Check my PDF"}</button>
              {workCheck && <div className="work-check-result"><strong>AI work check: {workCheck.status.replace("_", " ")}</strong><p>{workCheck.feedback}</p>{workCheck.worked_solution && <p className="worked-solution">{workCheck.worked_solution}</p>}</div>}
            </form>}
            {question.kind === "theory" && !isWrittenPaper && question.options.length > 0 && <p className="work-check-unavailable">Your working stays in your exercise book. Compare each step with the worked solution and mark guide below.</p>}
            <button className="button button-primary" onClick={next}>{index + 1 === practiceQuestions.length ? "Finish practice" : "Next question"} <ArrowRight size={16} /></button>
          </div>
        </> : <button className="button button-primary submit-answer" disabled={!selected || working} onClick={submit}>{working ? "Checking…" : "Check my answer"} <ArrowRight size={16} /></button>}
      </article>
    </div>
  </>;
}

function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.progress().then(setData).catch((reason) => setError(errorText(reason))); }, []);
  if (error) return <div className="alert">{error}</div>;
  if (!data) return <div className="loading-line">Loading your progress…</div>;
  const accuracy = data.summary.scored_attempts ? Math.round((data.summary.correct_attempts / data.summary.scored_attempts) * 100) : null;
  return <><div className="page-title-row"><div><span className="eyebrow">YOUR JOURNEY</span><h1>My progress</h1><p>Every practice session is something to be proud of.</p></div></div><div className="stat-grid"><Stat icon={<Target size={19} />} label="Questions tried" value={String(data.summary.total_attempts)} tone="green" /><Stat icon={<Check size={19} />} label="Answers right" value={String(data.summary.correct_attempts)} tone="yellow" /><Stat icon={<Sparkles size={19} />} label="Objective accuracy" value={accuracy === null ? "—" : `${accuracy}%`} tone="peach" /></div><div className="panel"><div className="panel-heading"><div><span className="eyebrow">KEEP GOING</span><h2>Recent practice</h2></div></div>{data.attempts.length ? <div className="attempt-list">{data.attempts.map((attempt) => <div className="attempt-row" key={attempt.id}><span className={`result-icon ${attempt.is_correct === null ? "result-pending" : attempt.is_correct ? "result-good" : "result-bad"}`}>{attempt.is_correct === null ? <FileText size={16} /> : attempt.is_correct ? <Check size={16} /> : <X size={16} />}</span><span className="attempt-copy"><strong>{attempt.subject} · {attempt.topic}</strong><small>{attempt.question_prompt}</small></span><span className="attempt-score">{attempt.score === null ? "Written" : `${attempt.score}%`}</span></div>)}</div> : <div className="empty-inline">Your practice history will show up here after your first question.</div>}</div></>;
}

function ReportsPage({ canManage, onError }: { canManage: boolean; onError: (message: string) => void }) {
  const [data, setData] = useState<Report | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [studentRefresh, setStudentRefresh] = useState(0);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [grade, setGrade] = useState("");
  const [className, setClassName] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [working, setWorking] = useState(false);
  useEffect(() => {
    api.report({
      ...(classId ? { class_id: Number(classId) } : {}),
      ...(subjectId ? { subject_id: Number(subjectId) } : {}),
      ...(grade ? { grade: Number(grade) } : {}),
    }).then(setData).catch((reason) => onError(errorText(reason)));
  }, [onError, classId, subjectId, grade, refresh, studentRefresh]);
  async function createClass(event: React.FormEvent) {
    event.preventDefault();
    setWorking(true);
    onError("");
    try {
      await api.createClass(className);
      setClassName("");
      setRefresh((value) => value + 1);
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }
  if (!data) return <div className="loading-line">Loading school report…</div>;
  const accuracy = Math.round(data.summary.average_score);
  return <>
    <div className="page-title-row report-title"><div><span className="eyebrow">{canManage ? "SCHOOL OVERVIEW" : "TEACHER REPORTS"}</span><h1>Learning at a glance</h1><p>Progress across {data.school}.</p></div>{canManage && <button className="button button-primary" onClick={() => setShowForm(!showForm)}>{showForm ? <X size={17} /> : <Plus size={17} />}{showForm ? "Close" : "Add students"}</button>}</div>
    {showForm && canManage && <StudentCreator onError={onError} onCreated={() => setStudentRefresh((value) => value + 1)} />}
    <div className="report-filters">
      <label>Class<select value={classId} onChange={(event) => setClassId(event.target.value)}><option value="">All classes</option>{data.classes.map((schoolClass) => <option key={schoolClass.id} value={schoolClass.id}>{schoolClass.name}</option>)}</select></label>
      <label>Grade<select value={grade} onChange={(event) => setGrade(event.target.value)}><option value="">All grades</option><option value="7">Grade 7 / JHS 1</option><option value="8">Grade 8 / JHS 2</option><option value="9">Grade 9 / JHS 3</option></select></label>
      <label>Subject<select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}><option value="">All subjects</option>{data.available_subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></label>
      {canManage && <form className="class-create-form" onSubmit={createClass}><input aria-label="New class name" placeholder="e.g. JHS 1A" value={className} onChange={(event) => setClassName(event.target.value)} required /><button className="button button-outline" disabled={working}>{working ? "Adding…" : <><Plus size={15} /> Add class</>}</button></form>}
    </div>
    <div className="stat-grid"><Stat icon={<Users size={19} />} label="Students" value={String(data.student_count)} tone="green" /><Stat icon={<BookOpen size={19} />} label="Questions answered" value={String(data.summary.total_attempts)} tone="yellow" /><Stat icon={<Target size={19} />} label="Average accuracy" value={`${accuracy}%`} tone="peach" /></div>
    {canManage && <div className="subscription-card"><div><span className="eyebrow">SCHOOL SUBSCRIPTION</span><strong>{data.subscription?.term_name ?? "No term on record"}</strong><small>{data.subscription ? `${data.subscription.starts_at} to ${data.subscription.ends_at}` : "Contact your platform administrator to set up a term."}</small></div><span className={`subscription-status ${data.subscription?.is_current ? "subscription-current" : ""}`}>{data.subscription?.is_current ? "Active" : data.subscription?.status ?? "Not set"}</span><span className="subscription-seats">{data.subscription ? `${data.total_student_count} / ${data.subscription.seat_limit} seats` : "—"}</span></div>}
    <div className="panel"><div className="panel-heading"><div><span className="eyebrow">BY SUBJECT</span><h2>Practice performance</h2></div></div>{data.subjects.length ? <div className="subject-report-list">{data.subjects.map((subject) => { const ratio = subject.attempts ? Math.round((subject.correct / subject.attempts) * 100) : 0; return <div className="subject-report" key={subject.question__topic__subject__id}><div className="subject-report-head"><strong>{subject.question__topic__subject__name}</strong><span>{subject.attempts} attempts · {ratio}% correct</span></div><div className="progress-track"><div style={{ width: `${ratio}%` }} /></div></div>; })}</div> : <div className="empty-inline">Subject results will appear as students practise.</div>}</div>
    {canManage ? <><TeacherCreator onError={onError} /><StudentManager key={studentRefresh} onError={onError} onChanged={() => setStudentRefresh((value) => value + 1)} /></> : <TeacherStudentReports students={data.students} onError={onError} />}
  </>;
}

function StudentCreator({ onError, onCreated }: { onError: (message: string) => void; onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [students, setStudents] = useState<NewStudent[]>([{ username: "", password: "", first_name: "", last_name: "", grade: 7, class_id: null }]);
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [notice, setNotice] = useState("");
  const [working, setWorking] = useState(false);
  useEffect(() => {
    api.schoolClasses().then(setClasses).catch((reason) => onError(errorText(reason)));
  }, [onError]);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setWorking(true);
    setNotice("");
    onError("");
    try {
      const result = await api.createStudents(students);
      setNotice(`${result.created} student account${result.created === 1 ? "" : "s"} created. Share usernames and temporary passwords securely with students.`);
      setStudents([{ username: "", password: "", first_name: "", last_name: "", grade: 7, class_id: null }]);
      onCreated();
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }
  function updateStudent<K extends keyof NewStudent>(index: number, field: K, value: NewStudent[K]) {
    setStudents((current) => current.map((student, row) => row === index ? { ...student, [field]: value } : student));
  }
  async function importCsv(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setWorking(true);
    setNotice("");
    onError("");
    try {
      const result = await api.importStudents(file);
      setNotice(`${result.created} student account${result.created === 1 ? "" : "s"} imported. Securely delete the CSV containing temporary passwords.`);
      onCreated();
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }
  return <div className="panel creator-panel"><div className="panel-heading"><div><span className="eyebrow">STUDENT ACCOUNTS</span><h2>Add students</h2></div><div className="creator-actions"><label className={`button button-outline ${working ? "button-disabled" : ""}`}>Import CSV<input className="visually-hidden" type="file" accept=".csv,text/csv" disabled={working} onChange={importCsv} /></label><button type="button" className="button button-outline" onClick={() => setOpen(!open)}>{open ? "Close" : <><Plus size={16} /> Create accounts</>}</button></div></div><p className="csv-help">CSV columns: username, password, first_name, last_name, grade, class_name. Grade must be 7, 8, or 9. Create classes first; delete files with temporary passwords after importing.</p>{notice && <div className="success-notice"><Check size={16} />{notice}</div>}{open && <form className="student-form" onSubmit={submit}>{students.map((student, index) => <div className="student-form-row" key={index}><span className="student-row-label">Student {index + 1}</span><label>Username<input value={student.username} onChange={(event) => updateStudent(index, "username", event.target.value)} required /></label><label>Temporary password<input type="password" minLength={8} value={student.password} onChange={(event) => updateStudent(index, "password", event.target.value)} required /></label><label>First name<input value={student.first_name} onChange={(event) => updateStudent(index, "first_name", event.target.value)} required /></label><label>Last name<input value={student.last_name} onChange={(event) => updateStudent(index, "last_name", event.target.value)} required /></label><label>Grade<select value={student.grade} onChange={(event) => updateStudent(index, "grade", Number(event.target.value))}><option value={7}>Grade 7 / JHS 1</option><option value={8}>Grade 8 / JHS 2</option><option value={9}>Grade 9 / JHS 3</option></select></label><label>Class<select value={student.class_id ?? ""} onChange={(event) => updateStudent(index, "class_id", event.target.value ? Number(event.target.value) : null)}><option value="">No class</option>{classes.map((schoolClass) => <option value={schoolClass.id} key={schoolClass.id}>{schoolClass.name}</option>)}</select></label>{students.length > 1 && <button type="button" className="remove-student" onClick={() => setStudents((current) => current.filter((_, row) => row !== index))}>Remove</button>}</div>)}<div className="student-form-actions"><button type="button" className="button button-outline" disabled={students.length >= 200} onClick={() => setStudents((current) => [...current, { username: "", password: "", first_name: "", last_name: "", grade: 7, class_id: null }])}><Plus size={15} /> Add another</button><button className="button button-primary" disabled={working}>{working ? "Creating…" : `Create ${students.length} account${students.length === 1 ? "" : "s"}`}</button></div></form>}</div>;
}

function TeacherCreator({ onError }: { onError: (message: string) => void }) {
  const [open, setOpen] = useState(false);
  const [teacher, setTeacher] = useState({ username: "", password: "", first_name: "", last_name: "" });
  const [notice, setNotice] = useState("");
  const [working, setWorking] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setWorking(true);
    setNotice("");
    onError("");
    try {
      const created = await api.createTeacher(teacher);
      setNotice(`Teacher account for ${created.first_name} ${created.last_name} created. Share the username and temporary password securely.`);
      setTeacher({ username: "", password: "", first_name: "", last_name: "" });
      setOpen(false);
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }

  return <div className="panel creator-panel"><div className="panel-heading"><div><span className="eyebrow">SCHOOL STAFF</span><h2>Instructor accounts</h2></div><button type="button" className="button button-outline" onClick={() => setOpen(!open)}>{open ? "Close" : <><Plus size={16} /> Add instructor</>}</button></div>{notice && <div className="success-notice"><Check size={16} />{notice}</div>}{open && <form className="student-form teacher-form" onSubmit={submit}><label>First name<input value={teacher.first_name} onChange={(event) => setTeacher({ ...teacher, first_name: event.target.value })} required maxLength={150} /></label><label>Last name<input value={teacher.last_name} onChange={(event) => setTeacher({ ...teacher, last_name: event.target.value })} required maxLength={150} /></label><label>Username<input value={teacher.username} onChange={(event) => setTeacher({ ...teacher, username: event.target.value })} required maxLength={150} /></label><label>Temporary password<input type="password" minLength={8} value={teacher.password} onChange={(event) => setTeacher({ ...teacher, password: event.target.value })} required /></label><button className="button button-primary" disabled={working}>{working ? "Creating…" : "Create instructor account"}</button></form>}</div>;
}

function TeacherStudentReports({ students, onError }: { students: Report["students"]; onError: (message: string) => void }) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [performance, setPerformance] = useState<StudentPerformance | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedId === null) {
      setPerformance(null);
      return;
    }
    let current = true;
    setPerformance(null);
    setLoading(true);
    api.studentPerformance(selectedId)
      .then((result) => { if (current) setPerformance(result); })
      .catch((reason) => { if (current) onError(errorText(reason)); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [selectedId, onError]);

  return <div className="panel student-panel"><div className="panel-heading"><div><span className="eyebrow">SCHOOL LEARNERS</span><h2>Student performance</h2></div></div>{students.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>Grade</th><th>Class</th><th>Attempts</th><th>Average</th><th>Details</th></tr></thead><tbody>{students.map((student) => <tr key={student.id}><td>{`${student.first_name} ${student.last_name}`.trim() || student.username}</td><td>{student.grade ? `Grade ${student.grade}` : "—"}</td><td>{student.class_name ?? "—"}</td><td>{student.total_attempts}</td><td>{student.average_score == null ? "—" : `${Math.round(student.average_score)}%`}</td><td><button type="button" className="table-action" aria-expanded={selectedId === student.id} onClick={() => setSelectedId(selectedId === student.id ? null : student.id)}>{selectedId === student.id ? "Hide details" : "View details"}</button></td></tr>)}</tbody></table></div> : <div className="empty-inline">No students match these filters.</div>}{selectedId !== null && <StudentPerformancePanel loading={loading} performance={performance} />}</div>;
}

function StudentManager({ onError, onChanged }: { onError: (message: string) => void; onChanged: () => void }) {
  const [students, setStudents] = useState<SchoolStudent[] | null>(null);
  const [performanceStudentId, setPerformanceStudentId] = useState<number | null>(null);
  const [performance, setPerformance] = useState<StudentPerformance | null>(null);
  const [performanceLoading, setPerformanceLoading] = useState(false);
  const [resetId, setResetId] = useState<number | null>(null);
  const [password, setPassword] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    api.students().then(setStudents).catch((reason) => onError(errorText(reason)));
  }, [onError]);

  useEffect(() => {
    if (performanceStudentId === null) {
      setPerformance(null);
      return;
    }
    let current = true;
    setPerformance(null);
    setPerformanceLoading(true);
    api.studentPerformance(performanceStudentId)
      .then((result) => { if (current) setPerformance(result); })
      .catch((reason) => { if (current) onError(errorText(reason)); })
      .finally(() => { if (current) setPerformanceLoading(false); });
    return () => { current = false; };
  }, [performanceStudentId, onError]);

  async function toggleActive(student: SchoolStudent) {
    setBusyId(student.id);
    onError("");
    try {
      const updated = await api.updateStudent(student.id, !student.is_active);
      setStudents((current) => current?.map((row) => row.id === updated.id ? { ...row, ...updated } : row) ?? null);
      setNotice(updated.is_active ? "Student account activated." : "Student account deactivated; their seat is now available.");
      onChanged();
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setBusyId(null);
    }
  }

  async function resetPassword(event: React.FormEvent) {
    event.preventDefault();
    if (resetId === null) return;
    setBusyId(resetId);
    onError("");
    try {
      await api.resetStudentPassword(resetId, password);
      setNotice("Student password reset. Share the new temporary password securely.");
      setPassword("");
      setResetId(null);
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setBusyId(null);
    }
  }

  return <div className="panel student-panel">
    <div className="panel-heading"><div><span className="eyebrow">YOUR SCHOOL</span><h2>Student accounts</h2></div></div>
    {notice && <div className="success-notice"><Check size={16} />{notice}</div>}
    {students === null ? <div className="loading-line">Loading student accounts…</div> : students.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>Username</th><th>Grade</th><th>Class</th><th>Status</th><th>Attempts</th><th>Avg. score</th><th>Actions</th></tr></thead><tbody>{students.map((student) => <tr key={student.id}>
      <td>{`${student.first_name} ${student.last_name}`.trim() || "—"}</td><td>{student.username}</td><td>{student.grade_label ?? "—"}</td><td>{student.class_name ?? "—"}</td>
      <td><span className={`student-status ${student.is_active ? "student-active" : "student-inactive"}`}>{student.is_active ? "Active" : "Inactive"}</span></td>
      <td>{student.total_attempts}</td><td>{student.average_score == null ? "—" : `${Math.round(student.average_score)}%`}</td>
      <td><div className="student-actions"><button type="button" className="table-action" aria-expanded={performanceStudentId === student.id} onClick={() => setPerformanceStudentId(performanceStudentId === student.id ? null : student.id)}>{performanceStudentId === student.id ? "Hide performance" : "View performance"}</button><button type="button" className="table-action" disabled={busyId === student.id} onClick={() => void toggleActive(student)}>{student.is_active ? "Deactivate" : "Activate"}</button><button type="button" className="table-action" onClick={() => { setResetId(resetId === student.id ? null : student.id); setPassword(""); }}>Reset password</button></div>{resetId === student.id && <form className="reset-password-form" onSubmit={resetPassword}><input type="password" minLength={8} autoComplete="new-password" placeholder="New temporary password" value={password} onChange={(event) => setPassword(event.target.value)} required /><button className="button button-outline" disabled={busyId === student.id}>{busyId === student.id ? "Saving…" : "Save"}</button></form>}</td>
    </tr>)}</tbody></table></div> : <div className="empty-inline">Add student accounts to get started.</div>}
    {performanceStudentId !== null && <StudentPerformancePanel loading={performanceLoading} performance={performance} />}
  </div>;
}

function StudentPerformancePanel({ loading, performance }: { loading: boolean; performance: StudentPerformance | null }) {
  if (loading) return <div className="loading-line">Loading student performance…</div>;
  if (!performance) return null;
  const { student, summary, subjects } = performance;
  const fullName = `${student.first_name} ${student.last_name}`.trim() || student.username;
  return <section className="student-performance">
    <div className="panel-heading"><div><span className="eyebrow">INDIVIDUAL REPORT</span><h2>{fullName}{student.grade_label ? ` · ${student.grade_label}` : ""}{student.class_name ? ` · ${student.class_name}` : ""}</h2></div></div>
    <div className="performance-summary">
      <div><span>Questions attempted</span><strong>{summary.total_attempts}</strong></div>
      <div><span>Correct answers</span><strong>{summary.correct_attempts}</strong></div>
      <div><span>Average score</span><strong>{summary.average_score === null ? "—" : `${Math.round(summary.average_score)}%`}</strong></div>
    </div>
    {!subjects.length ? <div className="empty-inline">Subject and topic performance will appear after this student answers practice questions.</div> : <div className="performance-subjects">{subjects.map((subject) => <article className="performance-subject" key={subject.subject_id}>
      <div className="performance-subject-heading"><strong>{subject.subject}</strong><PerformanceScore score={subject.average_score} attempts={subject.attempts} /></div>
      <div className="performance-topics">{subject.topics.map((topic) => <div className="performance-topic" key={topic.topic_id}><span>{topic.topic}<small>{topic.attempts} {topic.attempts === 1 ? "attempt" : "attempts"}</small></span><PerformanceScore score={topic.average_score} attempts={topic.attempts} /></div>)}</div>
    </article>)}</div>}
  </section>;
}

function PerformanceScore({ score, attempts }: { score: number | null; attempts: number }) {
  const label = score === null ? "Not scored" : score >= 80 ? "Strength" : score >= 50 ? "Building" : "Needs support";
  const percent = score === null ? 0 : Math.max(0, Math.min(100, score));
  const tone = score === null ? "performance-unscored" : score >= 80 ? "performance-strong" : score >= 50 ? "performance-building" : "performance-support";
  return <div className="performance-score"><div className="performance-score-label"><span className={`performance-badge ${tone}`}>{label}</span><strong>{score === null ? "—" : `${Math.round(score)}%`}</strong></div><div className="progress-track"><div style={{ width: `${percent}%` }} /></div>{score === null && attempts > 0 && <small>Answers recorded; score unavailable</small>}</div>;
}

function Stat({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: string }) {
  return <div className="stat-card"><span className={`stat-icon stat-${tone}`}>{icon}</span><span className="stat-label">{label}</span><strong>{value}</strong></div>;
}

function errorText(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export default App;
