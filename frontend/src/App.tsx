import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  GraduationCap,
  LogOut,
  Menu,
  Plus,
  Sparkles,
  Target,
  Users,
  X,
} from "lucide-react";
import { api, getToken, setToken, setTokens, type Attempt, type NewStudent, type Progress, type Question, type Report, type SchoolClass, type Subject, type Topic, type User } from "./api";

type Screen =
  | { name: "home" }
  | { name: "topics"; subject: Subject }
  | { name: "lesson"; subject: Subject; topic: Topic }
  | { name: "quiz"; topic: Topic; questions: Question[] }
  | { name: "progress" }
  | { name: "reports" };

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [screen, setScreen] = useState<Screen>({ name: "home" });
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [mobileMenu, setMobileMenu] = useState(false);

  const loadSubjects = useCallback(async () => {
    const rows = await api.subjects();
    setSubjects(rows);
  }, []);

  const finishLogin = useCallback(async (loggedInUser: User) => {
    setUser(loggedInUser);
    setScreen({ name: "home" });
    setError("");
    if (loggedInUser.role === "student" || loggedInUser.role === "school_admin") {
      await loadSubjects();
    }
  }, [loadSubjects]);

  useEffect(() => {
    if (!getToken()) return;
    api.me()
      .then(finishLogin)
      .catch(() => setToken(null));
  }, [finishLogin]);

  async function signOut() {
    setToken(null);
    setUser(null);
    setScreen({ name: "home" });
    setSubjects([]);
  }

  async function openTopics(subject: Subject) {
    setBusy(true);
    setError("");
    try {
      setScreen({ name: "topics", subject });
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  }

  async function openQuiz(topic: Topic) {
    setBusy(true);
    setError("");
    try {
      const questions = await api.questions(topic.id);
      if (!questions.length) {
        setError("There are no published practice questions for this topic yet.");
        return;
      }
      setScreen({ name: "quiz", topic, questions });
    } catch (reason) {
      setError(errorText(reason));
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return <Login onLogin={finishLogin} onError={setError} error={error} />;
  }

  const isAdmin = user.role === "school_admin";
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand"><span className="brand-mark"><GraduationCap size={22} /></span><span>Suku<span className="brand-dot">.</span></span></div>
        <div className="school-tag">{user.school_name ?? "Suku learning"}</div>
        <nav className="nav-list">
          <button className={screen.name === "home" || screen.name === "topics" || screen.name === "lesson" || screen.name === "quiz" ? "nav-link active" : "nav-link"} onClick={() => { setScreen({ name: "home" }); setMobileMenu(false); }}>
            <BookOpen size={18} /> {isAdmin ? "Learning library" : "My learning"}
          </button>
          {isAdmin ? (
            <button className={screen.name === "reports" ? "nav-link active" : "nav-link"} onClick={() => { setScreen({ name: "reports" }); setMobileMenu(false); }}>
              <Users size={18} /> School reports
            </button>
          ) : (
            <button className={screen.name === "progress" ? "nav-link active" : "nav-link"} onClick={() => { setScreen({ name: "progress" }); setMobileMenu(false); }}>
              <Target size={18} /> My progress
            </button>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-mini"><span className="avatar">{(user.first_name || user.username).slice(0, 1).toUpperCase()}</span><span><strong>{user.first_name || user.username}</strong><small>{isAdmin ? "School admin" : "Student"}</small></span></div>
          <button className="signout" onClick={signOut}><LogOut size={17} /> Sign out</button>
        </div>
      </aside>
      {mobileMenu && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileMenu(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileMenu(true)}><Menu size={22} /></button>
          <span className="topbar-context">{isAdmin ? "School workspace" : "Your study space"}</span>
          <div className="topbar-profile"><span className="status-dot" /> {user.first_name || user.username}</div>
        </header>
        <section className="page-content">
          {error && <div className="alert" role="alert"><CircleHelp size={17} />{error}<button aria-label="Dismiss" onClick={() => setError("")}><X size={16} /></button></div>}
          {busy && <div className="loading-line">Loading…</div>}
          {screen.name === "home" && <Home user={user} subjects={subjects} onSubject={openTopics} onAdminReports={() => setScreen({ name: "reports" })} />}
          {screen.name === "topics" && <Topics subject={screen.subject} onBack={() => setScreen({ name: "home" })} onOpen={(topic) => setScreen({ name: "lesson", subject: screen.subject, topic })} />}
          {screen.name === "lesson" && <Lesson topic={screen.topic} onBack={() => setScreen({ name: "topics", subject: screen.subject })} onPractice={openQuiz} />}
          {screen.name === "quiz" && <Quiz key={screen.topic.id} topic={screen.topic} questions={screen.questions} onBack={() => setScreen({ name: "home" })} onError={setError} />}
          {screen.name === "progress" && <ProgressPage />}
          {screen.name === "reports" && <ReportsPage onError={setError} />}
          {isAdmin && screen.name === "home" && <StudentCreator onError={setError} />}
        </section>
      </main>
    </div>
  );
}

function Login({ onLogin, onError, error }: { onLogin: (user: User) => Promise<void>; onError: (value: string) => void; error: string }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [working, setWorking] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setWorking(true);
    onError("");
    try {
      const tokens = await api.login(username, password);
      setTokens(tokens.access, tokens.refresh);
      await onLogin(tokens.user);
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
        <span className="eyebrow">WELCOME BACK</span><h2>Ready to learn?</h2><p className="form-intro">Sign in with the account your school gave you.</p>
        {error && <div className="alert login-alert" role="alert">{error}</div>}
        <label htmlFor="username">Username</label><input id="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required placeholder="Your school username" />
        <label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required placeholder="Your password" />
        <button className="button button-primary login-submit" disabled={working}>{working ? "Signing in…" : "Sign in"}<ArrowRight size={17} /></button>
        <p className="login-help">Need help getting in? Ask your school administrator.</p>
      </form></div>
    </div>
  );
}

function Home({ user, subjects, onSubject, onAdminReports }: { user: User; subjects: Subject[]; onSubject: (subject: Subject) => void; onAdminReports: () => void }) {
  const isAdmin = user.role === "school_admin";
  const greeting = user.first_name ? `Hi, ${user.first_name}` : `Hi, ${user.username}`;
  return (
    <>
      <div className="welcome-row"><div><span className="eyebrow">{isAdmin ? "SCHOOL OVERVIEW" : "YOUR LEARNING SPACE"}</span><h1>{greeting} <span className="wave">✳</span></h1><p>{isAdmin ? "A quick look at your school's learning space." : "Every question is a step forward. What will you learn today?"}</p></div></div>
      {isAdmin ? <div className="admin-banner"><div><span className="eyebrow light-eyebrow">SCHOOL ADMIN</span><h2>Help your students find their stride.</h2><p>Review learning activity and add student accounts for your school.</p><button className="button button-light" onClick={onAdminReports}>View school reports <ArrowRight size={16} /></button></div><div className="banner-illustration"><Users size={46} /></div></div> : <StudentWelcome />}
      <div className="section-heading"><div><span className="eyebrow">{isAdmin ? "CONTENT LIBRARY" : "PICK UP WHERE YOU LIKE"}</span><h2>{isAdmin ? "Study subjects" : "Explore your subjects"}</h2></div><span className="subject-count">{subjects.length} {subjects.length === 1 ? "subject" : "subjects"}</span></div>
      {subjects.length ? <div className="subject-grid">{subjects.map((subject, index) => <button className={`subject-card card-tone-${index % 3}`} key={subject.id} onClick={() => onSubject(subject)}><span className="subject-icon">{subject.name.toLowerCase().includes("math") ? "∑" : subject.name.toLowerCase().includes("science") ? "✳" : "Aa"}</span><span className="card-arrow"><ArrowRight size={18} /></span><span className="subject-name">{subject.name}</span><span className="subject-description">{subject.description || "Explore lessons and practice questions."}</span><span className="subject-meta"><BookOpen size={14} /> {subject.topic_count} {subject.topic_count === 1 ? "topic" : "topics"}</span></button>)}</div> : <div className="empty-state"><BookOpen size={27} /><h3>Your learning library is getting ready</h3><p>Published subjects will appear here when your school adds syllabus content.</p></div>}
    </>
  );
}

function StudentWelcome() {
  return <div className="study-banner"><div className="study-banner-copy"><span className="eyebrow light-eyebrow">A LITTLE PROGRESS ADDS UP</span><h2>Curiosity looks good on you.</h2><p>Pick a subject and take one small step today.</p></div><div className="banner-stamp"><Sparkles size={26} /><span>YOU'VE<br />GOT THIS</span></div><div className="banner-swoop" /></div>;
}

function Topics({ subject, onBack, onOpen }: { subject: Subject; onBack: () => void; onOpen: (topic: Topic) => void }) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api.topics(subject.id).then(setTopics).catch((reason) => setError(errorText(reason))).finally(() => setLoading(false));
  }, [subject.id]);
  return <><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> All subjects</button><div className="page-title-row"><div><span className="eyebrow">{subject.name.toUpperCase()}</span><h1>Choose a topic</h1><p>Work through a topic at your own pace.</p></div></div>{error && <div className="alert">{error}</div>}{loading ? <div className="loading-line">Loading topics…</div> : topics.length ? <div className="topic-list">{topics.map((topic, index) => <button className="topic-card" key={topic.id} onClick={() => onOpen(topic)}><span className="topic-number">{String(index + 1).padStart(2, "0")}</span><span className="topic-copy"><strong>{topic.title}</strong><small>{topic.summary || "Read the lesson, then practise what you learned."}</small></span><span className="topic-question-count">{topic.question_count} questions</span><ChevronRight size={19} /></button>)}</div> : <div className="empty-state"><BookOpen size={27} /><h3>No topics published just yet</h3><p>Your school will add learning content here soon.</p></div>}</>;
}

function Lesson({ topic, onBack, onPractice }: { topic: Topic; onBack: () => void; onPractice: (topic: Topic) => void }) {
  return <><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to topics</button><article className="lesson-card"><span className="eyebrow">TAKE YOUR TIME · LEARN AT YOUR PACE</span><h1>{topic.title}</h1>{topic.summary && <p className="lesson-summary">{topic.summary}</p>}<div className="lesson-content">{topic.content || "This lesson is being prepared. You can still practise any published questions below."}</div><div className="lesson-footer"><span><BookOpen size={15} /> {topic.question_count} practice questions</span><button className="button button-primary" onClick={() => onPractice(topic)}>Start practice <ArrowRight size={17} /></button></div></article></>;
}

function Quiz({ topic, questions, onBack, onError }: { topic: Topic; questions: Question[]; onBack: () => void; onError: (message: string) => void }) {
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState("");
  const [result, setResult] = useState<Attempt | null>(null);
  const [working, setWorking] = useState(false);
  const [finished, setFinished] = useState(false);
  const question = questions[index];

  async function submit() {
    if (!selected || !question) return;
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

  function next() {
    if (index + 1 >= questions.length) {
      setFinished(true);
      return;
    }
    setIndex(index + 1);
    setSelected("");
    setResult(null);
  }

  if (finished) return <div className="completion-card"><span className="completion-icon"><Check size={30} /></span><span className="eyebrow">PRACTICE COMPLETE</span><h1>Nice work showing up.</h1><p>You finished {questions.length} {questions.length === 1 ? "question" : "questions"} in {topic.title}. Every bit of practice counts.</p><button className="button button-primary" onClick={onBack}>Back to learning <ArrowRight size={17} /></button></div>;
  return <><button className="back-link" onClick={onBack}><ArrowLeft size={16} /> Back to topics</button><div className="quiz-layout"><div className="quiz-top"><div><span className="eyebrow">{topic.title.toUpperCase()}</span><h1>Practice time</h1></div><span className="question-progress">{index + 1} <span>of</span> {questions.length}</span></div><div className="progress-track"><div style={{ width: `${((index + (result ? 1 : 0)) / questions.length) * 100}%` }} /></div><article className="question-card"><div className="question-label"><span>QUESTION {String(index + 1).padStart(2, "0")}</span><span className={`difficulty difficulty-${question.difficulty}`}>{question.difficulty}</span></div><h2>{question.prompt}</h2><div className="answer-list">{question.options.map((option, optionIndex) => { const isSelected = selected === option; const isCorrect = result?.correct_answer === option; const className = result ? (isCorrect ? "answer-option answer-correct" : isSelected ? "answer-option answer-wrong" : "answer-option") : isSelected ? "answer-option answer-selected" : "answer-option"; return <button key={`${question.id}-${option}`} className={className} disabled={!!result} onClick={() => setSelected(option)}><span className="option-letter">{String.fromCharCode(65 + optionIndex)}</span><span>{option}</span>{result && isCorrect && <Check size={18} className="answer-check" />}</button>; })}</div>{result ? <div className={`feedback-box ${result.is_correct ? "feedback-good" : "feedback-review"}`}><strong>{result.is_correct ? "That's right!" : "Let's learn from this one."}</strong><p>{result.feedback}</p>{!result.is_correct && <p className="correct-answer"><strong>Correct answer:</strong> {result.correct_answer}</p>}<button className="button button-primary" onClick={next}>{index + 1 === questions.length ? "Finish practice" : "Next question"} <ArrowRight size={16} /></button></div> : <button className="button button-primary submit-answer" disabled={!selected || working} onClick={submit}>{working ? "Checking…" : "Check my answer"} <ArrowRight size={16} /></button>}</article></div></>;
}

function ProgressPage() {
  const [data, setData] = useState<Progress | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.progress().then(setData).catch((reason) => setError(errorText(reason))); }, []);
  if (error) return <div className="alert">{error}</div>;
  if (!data) return <div className="loading-line">Loading your progress…</div>;
  const accuracy = data.summary.total_attempts ? Math.round((data.summary.correct_attempts / data.summary.total_attempts) * 100) : 0;
  return <><div className="page-title-row"><div><span className="eyebrow">YOUR JOURNEY</span><h1>My progress</h1><p>Every practice session is something to be proud of.</p></div></div><div className="stat-grid"><Stat icon={<Target size={19} />} label="Questions tried" value={String(data.summary.total_attempts)} tone="green" /><Stat icon={<Check size={19} />} label="Answers right" value={String(data.summary.correct_attempts)} tone="yellow" /><Stat icon={<Sparkles size={19} />} label="Accuracy" value={`${accuracy}%`} tone="peach" /></div><div className="panel"><div className="panel-heading"><div><span className="eyebrow">KEEP GOING</span><h2>Recent practice</h2></div></div>{data.attempts.length ? <div className="attempt-list">{data.attempts.map((attempt) => <div className="attempt-row" key={attempt.id}><span className={`result-icon ${attempt.is_correct ? "result-good" : "result-bad"}`}>{attempt.is_correct ? <Check size={16} /> : <X size={16} />}</span><span className="attempt-copy"><strong>{attempt.subject} · {attempt.topic}</strong><small>{attempt.question_prompt}</small></span><span className="attempt-score">{attempt.score ?? 0}%</span></div>)}</div> : <div className="empty-inline">Your practice history will show up here after your first question.</div>}</div></>;
}

function ReportsPage({ onError }: { onError: (message: string) => void }) {
  const [data, setData] = useState<Report | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [className, setClassName] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [working, setWorking] = useState(false);
  useEffect(() => {
    api.report({
      ...(classId ? { class_id: Number(classId) } : {}),
      ...(subjectId ? { subject_id: Number(subjectId) } : {}),
    }).then(setData).catch((reason) => onError(errorText(reason)));
  }, [onError, classId, subjectId, refresh]);
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
  const accuracy = data.summary.total_attempts ? Math.round((data.summary.correct_attempts / data.summary.total_attempts) * 100) : 0;
  return <>
    <div className="page-title-row report-title"><div><span className="eyebrow">SCHOOL OVERVIEW</span><h1>Learning at a glance</h1><p>Progress across {data.school}.</p></div><button className="button button-primary" onClick={() => setShowForm(!showForm)}>{showForm ? <X size={17} /> : <Plus size={17} />}{showForm ? "Close" : "Add students"}</button></div>
    {showForm && <StudentCreator onError={onError} />}
    <div className="report-filters">
      <label>Class<select value={classId} onChange={(event) => setClassId(event.target.value)}><option value="">All classes</option>{data.classes.map((schoolClass) => <option key={schoolClass.id} value={schoolClass.id}>{schoolClass.name}</option>)}</select></label>
      <label>Subject<select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}><option value="">All subjects</option>{data.available_subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></label>
      <form className="class-create-form" onSubmit={createClass}><input aria-label="New class name" placeholder="e.g. JHS 1A" value={className} onChange={(event) => setClassName(event.target.value)} required /><button className="button button-outline" disabled={working}>{working ? "Adding…" : <><Plus size={15} /> Add class</>}</button></form>
    </div>
    <div className="stat-grid"><Stat icon={<Users size={19} />} label="Students" value={String(data.student_count)} tone="green" /><Stat icon={<BookOpen size={19} />} label="Questions answered" value={String(data.summary.total_attempts)} tone="yellow" /><Stat icon={<Target size={19} />} label="Average accuracy" value={`${accuracy}%`} tone="peach" /></div>
    <div className="subscription-card"><div><span className="eyebrow">SCHOOL SUBSCRIPTION</span><strong>{data.subscription?.term_name ?? "No term on record"}</strong><small>{data.subscription ? `${data.subscription.starts_at} to ${data.subscription.ends_at}` : "Contact your platform administrator to set up a term."}</small></div><span className={`subscription-status ${data.subscription?.is_current ? "subscription-current" : ""}`}>{data.subscription?.is_current ? "Active" : data.subscription?.status ?? "Not set"}</span><span className="subscription-seats">{data.subscription ? `${data.total_student_count} / ${data.subscription.seat_limit} seats` : "—"}</span></div>
    <div className="panel"><div className="panel-heading"><div><span className="eyebrow">BY SUBJECT</span><h2>Practice performance</h2></div></div>{data.subjects.length ? <div className="subject-report-list">{data.subjects.map((subject) => { const ratio = subject.attempts ? Math.round((subject.correct / subject.attempts) * 100) : 0; return <div className="subject-report" key={subject.question__topic__subject__id}><div className="subject-report-head"><strong>{subject.question__topic__subject__name}</strong><span>{subject.attempts} attempts · {ratio}% correct</span></div><div className="progress-track"><div style={{ width: `${ratio}%` }} /></div></div>; })}</div> : <div className="empty-inline">Subject results will appear as students practise.</div>}</div>
    <div className="panel student-panel"><div className="panel-heading"><div><span className="eyebrow">YOUR SCHOOL</span><h2>Student activity</h2></div></div>{data.students.length ? <div className="table-wrap"><table><thead><tr><th>Student</th><th>Username</th><th>Attempts</th><th>Avg. score</th></tr></thead><tbody>{data.students.map((student) => <tr key={student.id}><td>{student.first_name || student.last_name ? `${student.first_name} ${student.last_name}`.trim() : "—"}</td><td>{student.username}</td><td>{student.total_attempts}</td><td>{student.average_score == null ? "—" : `${Math.round(student.average_score)}%`}</td></tr>)}</tbody></table></div> : <div className="empty-inline">Add student accounts to get started.</div>}</div>
  </>;
}

function StudentCreator({ onError }: { onError: (message: string) => void }) {
  const [open, setOpen] = useState(false);
  const [students, setStudents] = useState<NewStudent[]>([{ username: "", password: "", first_name: "", last_name: "", class_id: null }]);
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
      setStudents([{ username: "", password: "", first_name: "", last_name: "", class_id: null }]);
    } catch (reason) {
      onError(errorText(reason));
    } finally {
      setWorking(false);
    }
  }
  function updateStudent<K extends keyof NewStudent>(index: number, field: K, value: NewStudent[K]) {
    setStudents((current) => current.map((student, row) => row === index ? { ...student, [field]: value } : student));
  }
  return <div className="panel creator-panel"><div className="panel-heading"><div><span className="eyebrow">STUDENT ACCOUNTS</span><h2>Add students</h2></div><button type="button" className="button button-outline" onClick={() => setOpen(!open)}>{open ? "Close" : <><Plus size={16} /> Create accounts</>}</button></div>{notice && <div className="success-notice"><Check size={16} />{notice}</div>}{open && <form className="student-form" onSubmit={submit}>{students.map((student, index) => <div className="student-form-row" key={index}><span className="student-row-label">Student {index + 1}</span><label>Username<input value={student.username} onChange={(event) => updateStudent(index, "username", event.target.value)} required /></label><label>Temporary password<input type="password" minLength={8} value={student.password} onChange={(event) => updateStudent(index, "password", event.target.value)} required /></label><label>First name<input value={student.first_name} onChange={(event) => updateStudent(index, "first_name", event.target.value)} /></label><label>Last name<input value={student.last_name} onChange={(event) => updateStudent(index, "last_name", event.target.value)} /></label><label>Class<select value={student.class_id ?? ""} onChange={(event) => updateStudent(index, "class_id", event.target.value ? Number(event.target.value) : null)}><option value="">No class</option>{classes.map((schoolClass) => <option value={schoolClass.id} key={schoolClass.id}>{schoolClass.name}</option>)}</select></label>{students.length > 1 && <button type="button" className="remove-student" onClick={() => setStudents((current) => current.filter((_, row) => row !== index))}>Remove</button>}</div>)}<div className="student-form-actions"><button type="button" className="button button-outline" disabled={students.length >= 200} onClick={() => setStudents((current) => [...current, { username: "", password: "", first_name: "", last_name: "", class_id: null }])}><Plus size={15} /> Add another</button><button className="button button-primary" disabled={working}>{working ? "Creating…" : `Create ${students.length} account${students.length === 1 ? "" : "s"}`}</button></div></form>}</div>;
}

function Stat({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: string }) {
  return <div className="stat-card"><span className={`stat-icon stat-${tone}`}>{icon}</span><span className="stat-label">{label}</span><strong>{value}</strong></div>;
}

function errorText(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

export default App;
