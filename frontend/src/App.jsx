import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Link, Navigate, NavLink, Outlet, Route, BrowserRouter as Router, Routes, useNavigate, useParams } from "react-router-dom";
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Building2,
  Download,
  FileText,
  Gauge,
  History,
  Lock,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Upload,
  Users
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis
} from "recharts";
import { api, clearSession, getStoredUser, getToken, setSession } from "./api";
import "./styles.css";

function useAsync(loader, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: "" });
  useEffect(() => {
    let alive = true;
    setState((prev) => ({ ...prev, loading: true, error: "" }));
    loader()
      .then((data) => alive && setState({ loading: false, data, error: "" }))
      .catch((error) => alive && setState({ loading: false, data: null, error: error.message }));
    return () => {
      alive = false;
    };
  }, deps);
  return state;
}

function Protected() {
  return getToken() ? <Outlet /> : <Navigate to="/login" replace />;
}

function AdminOnly({ children }) {
  const user = getStoredUser();
  return user?.role === "admin" ? children : <Navigate to="/dashboard" replace />;
}

function Shell() {
  const navigate = useNavigate();
  const user = getStoredUser();
  const baseNav = [
    ["Dashboard", "/dashboard", Gauge],
    ["Startup", "/analysis/startup", BrainCircuit],
    ["Compare", "/analysis/company_comparison", Building2],
    ["Reports", "/reports", FileText],
    ["Settings", "/settings", Settings]
  ];
  const adminNav = [
    ["Analytics", "/analytics", BarChart3],
    ["Evaluation", "/evaluation", Activity],
    ["Security", "/security", ShieldCheck]
  ];
  const nav =
    user?.role === "admin"
      ? [...baseNav.slice(0, 4), ...adminNav, baseNav[4]].filter(Boolean)
      : baseNav;
  const navClass = ({ isActive }) =>
    `flex min-h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition ${
      isActive
        ? "bg-rose-50 text-ocean ring-1 ring-rose-100"
        : "text-steel hover:bg-slate-100 hover:text-ink"
    }`;
  return (
    <div className="min-h-screen bg-paper">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ocean text-white shadow-glow"><BrainCircuit size={19} /></div>
          <div>
            <p className="text-sm font-bold">VentureMind AI</p>
            <p className="text-xs text-steel">AI research workspace</p>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {nav.map(([label, href, Icon]) => (
            <NavLink key={href} to={href} className={navClass}>
              <Icon size={17} /> {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:px-8">
          <div className="flex min-h-16 items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ocean text-white lg:hidden"><BrainCircuit size={18} /></div>
              <div>
                <p className="text-sm font-semibold text-ink">{user?.full_name || "Workspace"}</p>
                <p className="text-xs text-steel">{user?.role === "admin" ? "Admin console" : "Founder workspace"}</p>
              </div>
            </div>
            <button
              className="btn-secondary"
              onClick={() => {
                clearSession();
                navigate("/login");
              }}
            >
              <LogOut size={16} /> <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
          <nav className="flex gap-2 overflow-x-auto pb-3 lg:hidden">
            {nav.map(([label, href, Icon]) => (
              <NavLink
                key={href}
                to={href}
                className={({ isActive }) =>
                  `flex min-h-10 shrink-0 items-center gap-2 rounded-md px-3 text-sm font-medium transition ${
                    isActive ? "bg-rose-50 text-ocean ring-1 ring-rose-100" : "text-steel hover:bg-slate-100"
                  }`
                }
              >
                <Icon size={16} /> {label}
              </NavLink>
            ))}
          </nav>
        </header>
        <div className="p-4 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function Landing() {
  return (
    <div className="min-h-screen bg-paper">
      <section className="relative min-h-[88vh] overflow-hidden bg-[url('https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1800&q=80')] bg-cover bg-center">
        <div className="absolute inset-0 bg-slate-950/60" />
        <div className="absolute inset-x-0 top-0 h-1 bg-aurora" />
        <div className="relative mx-auto flex min-h-[88vh] max-w-6xl flex-col justify-center px-6 text-white">
          <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-amber-200">Multi-agent business intelligence</p>
          <h1 className="max-w-3xl text-5xl font-bold leading-tight md:text-7xl">VentureMind AI</h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-100">
            Analyze startup ideas, benchmark competitors, generate cited reports, and track research quality from one SaaS workspace.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="btn-primary" to="/register"><BrainCircuit size={17} /> Start analysis</Link>
            <Link className="btn-secondary !bg-white/95" to="/login"><Lock size={17} /> Login</Link>
          </div>
        </div>
      </section>
      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-6 py-10 md:grid-cols-3">
        {["RAG citations", "LangGraph agents", "Evaluation metrics"].map((item) => (
          <div className="panel p-5" key={item}>
            <p className="font-semibold">{item}</p>
            <p className="mt-2 text-sm text-steel">Production workflow support for capstone-grade business research.</p>
          </div>
        ))}
      </section>
    </div>
  );
}

function AuthPage({ mode }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", full_name: "" });
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const session = mode === "login" ? await api.login(form) : await api.register(form);
      setSession(session);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper p-4">
      <form onSubmit={submit} className="panel w-full max-w-md border-rose-100 p-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ocean text-white shadow-glow"><BrainCircuit size={20} /></div>
          <div>
            <p className="text-sm font-bold text-ink">VentureMind AI</p>
            <p className="text-xs text-steel">Research workspace</p>
          </div>
        </div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold">{mode === "login" ? "Welcome back" : "Create workspace"}</h1>
          <p className="mt-1 text-sm text-steel">Secure access with JWT and role-based permissions.</p>
        </div>
        {mode === "register" && <Field label="Full name" value={form.full_name} onChange={(full_name) => setForm({ ...form, full_name })} />}
        <Field label="Email" type="email" value={form.email} onChange={(email) => setForm({ ...form, email })} />
        <Field label="Password" type="password" value={form.password} onChange={(password) => setForm({ ...form, password })} />
        {error && <p className="mb-3 rounded-md bg-rose-50 px-3 py-2 text-sm text-coral">{error}</p>}
        <button className="btn-primary w-full" type="submit">{mode === "login" ? "Login" : "Register"}</button>
        <p className="mt-4 text-center text-sm text-steel">
          {mode === "login" ? <Link to="/register">Need an account?</Link> : <Link to="/login">Already registered?</Link>}
        </p>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <label className="mb-4 block">
      <span className="label mb-1 block">{label}</span>
      <input className="input" type={type} value={value} onChange={(event) => onChange(event.target.value)} required />
    </label>
  );
}

function Stat({ label, value, Icon }) {
  return (
    <div className="panel relative overflow-hidden p-5">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-ocean to-aurora" />
      <div className="flex items-center justify-between">
        <p className="text-sm text-steel">{label}</p>
        {Icon && <span className="relative flex h-9 w-9 items-center justify-center rounded-md bg-rose-50 text-ocean"><Icon size={18} /></span>}
      </div>
      <p className="mt-3 text-3xl font-bold">{value}</p>
    </div>
  );
}

function Dashboard() {
  const user = getStoredUser();
  const { data, loading, error } = useAsync(() => (user?.role === "admin" ? api.adminDashboard() : api.userDashboard()), []);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  if (user?.role === "admin") return <AdminDashboard data={data} />;
  return <UserDashboard data={data} />;
}

function UserDashboard({ data }) {
  return (
    <Page title="User Dashboard" subtitle="Saved projects, reports, research evidence, and recent analysis.">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Saved Projects" value={data.saved_projects} Icon={FileText} />
        <Stat label="Reports" value={data.generated_reports} Icon={Download} />
        <Stat label="Avg Viability" value={`${data.average_viability}%`} Icon={Gauge} />
        <Stat label="Downloads" value={data.downloads} Icon={History} />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Sources Collected" value={data.research_summary?.sources_collected || 0} Icon={Search} />
        <Stat label="Rejected Sources" value={data.research_summary?.rejected_sources || 0} Icon={ShieldCheck} />
        <Stat label="Evidence Count" value={data.research_summary?.final_evidence_count || 0} Icon={FileText} />
        <Stat label="Report Confidence" value={`${Math.round((data.research_summary?.report_confidence || 0) * 100)}%`} Icon={Activity} />
      </div>
      <AgentStatusPanel rows={data.agent_status || []} />
      <ReportList rows={data.recent_reports || []} />
    </Page>
  );
}

function AdminDashboard({ data }) {
  return (
    <Page title="Admin Dashboard" subtitle="Platform health, usage, quality, and security controls.">
      <div className="grid gap-4 md:grid-cols-3">
        <Link className="panel p-5 hover:border-ocean" to="/analytics">
          <p className="font-semibold">Analytics</p>
          <p className="mt-2 text-sm text-steel">Agent usage and report volume.</p>
        </Link>
        <Link className="panel p-5 hover:border-ocean" to="/evaluation">
          <p className="font-semibold">Evaluation</p>
          <p className="mt-2 text-sm text-steel">Accuracy, relevance, citations, and latency.</p>
        </Link>
        <Link className="panel p-5 hover:border-ocean" to="/security">
          <p className="font-semibold">Security</p>
          <p className="mt-2 text-sm text-steel">Blocked prompts, validation, and audit events.</p>
        </Link>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Stat label="Total Users" value={data.total_users} Icon={Users} />
        <Stat label="Total Reports" value={data.total_reports} Icon={FileText} />
        <Stat label="Security Events" value={data.security_events} Icon={ShieldCheck} />
        <Stat label="Web Sources" value={data.web_sources || 0} Icon={Search} />
        <Stat label="Research Sessions" value={data.research_sessions || 0} Icon={Activity} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <ChartPanel title="Agent Usage" data={(data.agent_usage || []).map((x) => ({ name: x.name, score: x.count }))} />
        <ChartPanel title="Analyzed Industries" data={(data.most_analyzed_industries || []).map((x) => ({ name: x.industry, score: x.count }))} />
      </div>
    </Page>
  );
}

function Page({ title, subtitle, children }) {
  return (
    <div className="space-y-6">
      <div className="border-l-4 border-aurora pl-4">
        <h1 className="text-3xl font-bold tracking-tight text-ink">{title}</h1>
        <p className="mt-1 text-sm text-steel">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}

function ChartPanel({ title, data }) {
  return (
    <div className="panel h-80 p-5">
      <h2 className="mb-4 text-lg font-semibold">{title}</h2>
      <ResponsiveContainer width="100%" height="82%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="score" fill="#be185d" radius={[4, 4, 0, 0]} />
          <Bar dataKey="revenue" fill="#d97706" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function AgentStatusPanel({ rows }) {
  const uniqueRows = uniqueAgentStatuses(rows);
  if (!uniqueRows.length) return null;
  return (
    <div className="panel p-5">
      <h2 className="mb-4 text-lg font-semibold">Agent Status</h2>
      <div className="grid gap-2 md:grid-cols-4">
        {uniqueRows.map((row, index) => (
          <div className="rounded-md border border-slate-200 p-3 text-sm" key={`${row.agent}-${index}`}>
            <p className="font-semibold capitalize">{row.agent.replaceAll("_", " ")}</p>
            <p className="mt-1 text-steel">{row.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function uniqueAgentStatuses(rows) {
  const priority = { completed: 3, failed: 2, running: 1, pending: 0 };
  const order = ["web_research", "research", "competitor", "swot", "market_sizing", "strategy", "critic", "report"];
  const map = new Map();
  for (const row of rows || []) {
    const key = String(row.agent || "").toLowerCase().replaceAll(" ", "_");
    if (!key || key === "financial") continue;
    const current = map.get(key);
    const rowPriority = priority[String(row.status || "").toLowerCase()] ?? 0;
    const currentPriority = priority[String(current?.status || "").toLowerCase()] ?? -1;
    if (!current || rowPriority > currentPriority) {
      map.set(key, { ...row, agent: key });
    }
  }
  return Array.from(map.values()).sort((a, b) => {
    const aIndex = order.indexOf(a.agent);
    const bIndex = order.indexOf(b.agent);
    return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex);
  });
}

function AnalysisPage({ mode }) {
  const navigate = useNavigate();
  const labels = {
    startup: ["Startup Idea Analysis", "AI Recruitment Platform"],
    company_comparison: ["Company Comparison", "Zomato vs Swiggy"]
  };
  const [query, setQuery] = useState(labels[mode][1]);
  const [industry, setIndustry] = useState("SaaS");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const report = await api.createAnalysis({ mode, query, industry, project_name: query });
      navigate(`/reports/${report.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <Page title={labels[mode][0]} subtitle="Generate a quick cited market, competitor, SWOT, pricing, and strategy report.">
      <form className="panel space-y-4 p-5" onSubmit={submit}>
        <label className="block">
          <span className="label mb-1 block">Business question</span>
          <textarea className="input min-h-36" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <Field label="Industry" value={industry} onChange={setIndustry} />
        {error && <ErrorBox message={error} />}
        <button disabled={loading} className="btn-primary" type="submit"><BrainCircuit size={17} /> {loading ? "Running agents..." : "Generate analysis"}</button>
      </form>
      <RagPanel />
    </Page>
  );
}

function RagPanel() {
  const [file, setFile] = useState(null);
  const [collection, setCollection] = useState("Market Reports");
  const [query, setQuery] = useState("pricing strategy market growth");
  const [url, setUrl] = useState("");
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append("collection", collection);
    form.append("file", file);
    const result = await api.upload(form);
    setMessage(`${result.filename} indexed into ${result.collection} with ${result.chunk_count} chunks.`);
  }
  async function search() {
    const result = await api.search({ query, collection, limit: 5 });
    setResults(result.results);
  }
  async function ingestUrl() {
    if (!url) return;
    const result = await api.ingestUrl({ url, collection });
    setMessage(`${result.filename} indexed into ${result.collection} with ${result.chunk_count} chunks.`);
  }
  return (
    <div className="panel p-5">
      <div className="mb-4 flex items-center gap-2"><Upload size={18} className="text-ocean" /><h2 className="text-lg font-semibold">Knowledge Base</h2></div>
      <div className="grid gap-3 md:grid-cols-4">
        <select className="input" value={collection} onChange={(event) => setCollection(event.target.value)}>
          {["Market Reports", "Industry Reports", "Competitor Profiles", "Startup Case Studies", "Business Frameworks", "Pricing Models", "SWOT Templates"].map((x) => <option key={x}>{x}</option>)}
        </select>
        <input className="input md:col-span-2" type="file" onChange={(event) => setFile(event.target.files[0])} />
        <button className="btn-secondary" type="button" onClick={upload}><Upload size={16} /> Upload</button>
      </div>
      {message && <p className="mt-3 text-sm text-ocean">{message}</p>}
      <div className="mt-4 flex gap-3">
        <input className="input" value={query} onChange={(event) => setQuery(event.target.value)} />
        <button className="btn-secondary" type="button" onClick={search}><Search size={16} /> Search</button>
      </div>
      <div className="mt-4 flex gap-3">
        <input className="input" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://example.com/report-or-page" />
        <button className="btn-secondary" type="button" onClick={ingestUrl}><Upload size={16} /> Ingest URL</button>
      </div>
      <div className="mt-4 space-y-2">
        {results.map((hit, index) => (
          <div className="rounded-md border border-slate-200 p-3 text-sm" key={index}>
            <p className="font-semibold">{hit.source} · {Math.round(hit.confidence * 100)}%</p>
            <p className="mt-1 text-steel">{hit.text.slice(0, 220)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportsPage() {
  const { data, loading, error } = useAsync(api.reports, []);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  return <Page title="Reports" subtitle="Download PDF/DOCX reports or inspect source-backed strategy findings."><ReportList rows={data} /></Page>;
}

function ReportList({ rows }) {
  return (
    <div className="panel overflow-hidden">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-steel">
          <tr><th className="p-3">Report</th><th className="p-3">Mode</th><th className="p-3">Score</th><th className="p-3">Created</th><th className="p-3">Actions</th></tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr className="border-t border-slate-200" key={row.id}>
              <td className="p-3 font-medium">{row.title}</td>
              <td className="p-3">{row.mode}</td>
              <td className="p-3">{row.score || row.viability_score}</td>
              <td className="p-3">{new Date(row.created_at).toLocaleString()}</td>
              <td className="p-3"><Link className="text-ocean font-semibold" to={`/reports/${row.id}`}>Open</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReportViewer() {
  const { id } = useParams();
  const { data, loading, error } = useAsync(() => api.report(id), [id]);
  const [rating, setRating] = useState(5);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  const sections = data.content.sections || {};
  const isCompanyComparison = data.mode === "company_comparison" || data.content.mode === "company_comparison";
  const orderedSections = [
    ["company_idea_overview", "Company / Idea Overview"],
    ["market_analysis", "Market Analysis"],
    ["competitor_analysis", "Competitor Analysis"],
    ["product_comparison", "Product Comparison"],
    ["pricing_comparison", "Pricing Comparison"],
    ...(!isCompanyComparison ? [
      ["swot_analysis", "SWOT Analysis"],
      ["risks", "Risks"],
      ["strategic_recommendations", "Strategic Recommendations"],
    ] : []),
    ["sources_used", "Sources Used"]
  ];
  return (
    <Page title={data.title} subtitle={isCompanyComparison ? `Company comparison · Confidence ${Math.round(data.confidence_score * 100)}%` : `Viability ${data.viability_score}/100 · Confidence ${Math.round(data.confidence_score * 100)}%`}>
      <div className="flex flex-wrap gap-3">
        <a className="btn-primary" href={api.downloadUrl(data.id, "pdf")}><Download size={16} /> PDF</a>
        <a className="btn-secondary" href={api.downloadUrl(data.id, "docx")}><Download size={16} /> DOCX</a>
      </div>
      {!isCompanyComparison && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Object.entries(data.content.scorecard || {}).map(([key, value]) => (
            <ScoreCard key={key} label={key.replaceAll("_", " ")} value={value} />
          ))}
        </div>
      )}
      <div className="panel p-5"><h2 className="text-lg font-semibold">Executive Summary</h2><p className="mt-2 text-sm leading-6 text-steel">{data.content.executive_summary}</p></div>
      {orderedSections.filter(([key]) => sections[key]).map(([key, title]) => (
        <div className="panel p-5" key={key}>
          <h2 className="text-lg font-semibold">{title}</h2>
          <FormattedSection section={sections[key]} />
        </div>
      ))}
      <EvidencePanel evidence={data.content.evidence_panel || {}} />
      <AgentPanel statuses={data.content.agent_panel?.statuses || data.content.agent_statuses || []} />
      <div className="panel p-5">
        <h2 className="text-lg font-semibold">Feedback</h2>
        <div className="mt-3 flex max-w-sm gap-3">
          <input className="input" type="number" min="1" max="5" value={rating} onChange={(event) => setRating(event.target.value)} />
          <button className="btn-secondary" onClick={() => api.feedback(data.id, { rating: Number(rating), comment: "Reviewed in dashboard" })}>Submit</button>
        </div>
      </div>
    </Page>
  );
}

function VisualAnalytics({ content }) {
  const scorecard = content.scorecard || {};
  const radarData = Object.entries(scorecard).map(([key, value]) => ({
    metric: key.replaceAll("_", " "),
    score: scoreValue(value)
  }));
  const entities = content.entities || [];
  const positionData = content.sections?.product_comparison?.positioning_matrix || [];
  const confidenceData = (content.agent_trace || content.agent_statuses || []).map((item, index) => ({
    name: (item.agent || `A${index + 1}`).replaceAll("_", " "),
    confidence: item.evidence_collected ? Math.min(100, item.evidence_collected * 8) : item.status === "completed" ? Math.round((content.critic?.confidence_score || 0) * 100) : 0
  }));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="panel h-80 p-5">
        <h2 className="mb-4 text-lg font-semibold">SWOT Radar</h2>
        <ResponsiveContainer width="100%" height="82%">
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis angle={30} domain={[0, 100]} />
            <Radar dataKey="score" stroke="#be185d" fill="#be185d" fillOpacity={0.25} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="panel h-80 p-5">
        <h2 className="mb-4 text-lg font-semibold">Competitive Position Matrix</h2>
        <ResponsiveContainer width="100%" height="82%">
          <ScatterChart>
            <CartesianGrid />
            <XAxis type="number" dataKey="x_value" name="Product breadth" domain={[0, 100]} />
            <YAxis type="number" dataKey="y_value" name="Evidence visibility" domain={[0, 100]} />
            <ZAxis type="category" dataKey="company" name="Company" />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={positionData.length ? positionData : entities.map((company, i) => ({ company, x_value: 50 + i * 10, y_value: Math.round((content.critic?.confidence_score || 0) * 100) }))} fill="#d97706" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <ChartPanel title="Agent Confidence" data={confidenceData.map((x) => ({ name: x.name, score: x.confidence }))} />
      <ChartPanel title="Revenue Comparison" data={entities.map((name) => ({ name, score: 0 }))} />
    </div>
  );
}

function AgentReasoningPanel({ content }) {
  const rows = content.agent_trace || [];
  if (!rows.length) return (
    <div className="panel p-5">
      <h2 className="text-lg font-semibold">Agent Workflow</h2>
      <AgentStatusPanel rows={content.agent_statuses || []} />
    </div>
  );
  return (
    <div className="panel p-5">
      <h2 className="text-lg font-semibold">Agent Reasoning</h2>
      <div className="mt-3 space-y-3">
        {rows.map((row) => (
          <details className="rounded-md border border-slate-200 p-3" key={row.agent}>
            <summary className="cursor-pointer text-sm font-semibold capitalize">{row.agent.replaceAll("_", " ")} · {row.status}</summary>
            <div className="mt-3 space-y-2 text-sm text-steel">
              <p><strong>Evidence Collected:</strong> {row.evidence_collected}</p>
              <p><strong>Reasoning Summary:</strong> {row.reasoning_summary}</p>
              <ReadableSection value={row.output} />
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}

function scoreValue(value) {
  return typeof value === "object" && value !== null ? value.score || 0 : value || 0;
}

function ScoreCard({ label, value }) {
  const score = scoreValue(value);
  const title = value?.title || label;
  const evidence = Array.isArray(value?.evidence) ? value.evidence : value?.evidence ? [value.evidence] : [];
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm capitalize text-steel">{title}</p>
        <Gauge className="text-ocean" size={18} />
      </div>
      <p className="mt-3 text-3xl font-bold">{score}/100</p>
      {typeof value === "object" && value !== null && (
        <div className="mt-3 space-y-1 text-xs leading-5 text-steel">
          <p><strong>Explanation:</strong> {value.explanation || value.reason}</p>
          {evidence.length > 0 && (
            <div>
              <p><strong>Evidence:</strong></p>
              <ul className="mt-1 list-disc space-y-1 pl-4">
                {evidence.slice(0, 3).map((item, index) => <li key={index}>{item}</li>)}
              </ul>
            </div>
          )}
          <p>Confidence: {Math.round((value.confidence || 0) * 100)}%</p>
        </div>
      )}
    </div>
  );
}

function FormattedSection({ section }) {
  if (!section) return <p className="mt-2 text-sm text-steel">Not publicly verified from collected sources.</p>;
  return (
    <div className="mt-3 space-y-4 text-sm leading-6 text-steel">
      {(section.paragraphs || []).map((paragraph, index) => <p key={`p-${index}`}>{paragraph}</p>)}
      {(section.bullets || []).length > 0 && (
        <ul className="list-disc space-y-2 pl-5">
          {section.bullets.map((item, index) => <li key={`b-${index}`}>{item}</li>)}
        </ul>
      )}
      {["strengths", "weaknesses", "opportunities", "threats"].map((key) => (
        section[key]?.length ? (
          <div key={key}>
            <p className="font-semibold capitalize text-ink">{key}</p>
            <ul className="mt-2 list-disc space-y-2 pl-5">
              {section[key].map((item, index) => <li key={index}>{item}</li>)}
            </ul>
          </div>
        ) : null
      ))}
      {section.table?.length ? <CleanTable rows={section.table} /> : null}
      {section.sources?.length ? (
        <ul className="list-disc space-y-2 pl-5">
          {section.sources.map((source, index) => (
            <li key={index}>
              {source.url ? <a className="font-semibold text-ocean" href={source.url} target="_blank" rel="noreferrer">{source.title}</a> : source.title}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

function CleanTable({ rows }) {
  const rawColumns = Array.from(rows.reduce((set, row) => {
    Object.keys(row).forEach((key) => set.add(key));
    return set;
  }, new Set()));
  const preferred = ["item", "metric", "competitor", "evidence", "value", "source", "citation"];
  const columns = [...preferred.filter((key) => rawColumns.includes(key)), ...rawColumns.filter((key) => !preferred.includes(key))];
  return (
    <div className="overflow-x-auto rounded-md border border-slate-200">
      <table className="w-full min-w-[680px] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase text-steel">
          <tr>{columns.map((column) => <th className="p-3" key={column}>{friendlyLabel(column)}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr className="border-t border-slate-200" key={index}>
              {columns.map((column) => <td className="p-3 align-top" key={column}>{formatCell(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvidencePanel({ evidence }) {
  const sources = evidence.sources || [];
  const chunks = evidence.retrieved_chunks || [];
  if (!sources.length && !chunks.length) return null;
  return (
    <div className="panel p-5">
      <h2 className="text-lg font-semibold">Evidence Panel</h2>
      <p className="mt-2 text-sm text-steel">Sources, citations, and retrieved evidence used to support the report.</p>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {sources.map((source, index) => (
          <div className="rounded-md border border-slate-200 p-3 text-sm" key={`${source.url}-${index}`}>
            <p className="font-semibold">{source.url ? <a className="text-ocean" href={source.url} target="_blank" rel="noreferrer">{source.title}</a> : source.title}</p>
            <p className="mt-1 text-steel">{source.snippet}</p>
            <p className="mt-2 text-xs text-steel">Confidence: {Math.round((source.confidence || 0) * 100)}%</p>
          </div>
        ))}
      </div>
      {chunks.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="text-sm font-semibold">Retrieved Chunks</h3>
          {chunks.map((chunk, index) => (
            <div className="rounded-md border border-slate-200 p-3 text-sm" key={index}>
              <p className="font-semibold">{chunk.source}</p>
              <p className="mt-1 text-steel">{chunk.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AgentPanel({ statuses }) {
  if (!statuses.length) return null;
  return (
    <div className="panel p-5">
      <h2 className="text-lg font-semibold">Agent Panel</h2>
      <div className="mt-4 grid gap-2 md:grid-cols-3">
        {statuses.map((row, index) => (
          <div className="rounded-md border border-slate-200 p-3 text-sm" key={`${row.agent}-${index}`}>
            <p className="font-semibold">{row.agent}</p>
            <p className="mt-1 text-steel">{row.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function friendlyLabel(value) {
  if (value === "item" || value === "metric") return "Item";
  if (value === "citation") return "Citation";
  return String(value).replaceAll("_", " ");
}

function formatCell(value) {
  if (value?.url) return <a className="font-semibold text-ocean" href={value.url} target="_blank" rel="noreferrer">{value.label || "Source"}</a>;
  if (value && typeof value === "object") return value.value || value.title || "Not publicly verified from collected sources.";
  return value || "Not publicly verified from collected sources.";
}

function ReadableSection({ value }) {
  if (!value) return <p className="mt-2 text-sm text-steel">No evidence collected for this section.</p>;
  if (typeof value === "string") return <p className="mt-2 text-sm leading-6 text-steel">{value}</p>;
  if (Array.isArray(value)) {
    return <div className="mt-3 space-y-3">{value.map((item, index) => <ReadableSection key={index} value={item} />)}</div>;
  }
  if (typeof value === "object") {
    return (
      <div className="mt-3 space-y-3">
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <p className="text-sm font-semibold capitalize">{key.replaceAll("_", " ")}</p>
            <ReadableSection value={item} />
          </div>
        ))}
      </div>
    );
  }
  return <p className="mt-2 text-sm text-steel">{String(value)}</p>;
}

function AnalyticsPage() {
  const { data } = useAsync(api.adminDashboard, []);
  const rows = data?.agent_usage?.map((x) => ({ name: x.name, score: x.count })) || [];
  return (
    <Page title="Admin Analytics" subtitle="Simple usage summary for reports, research sessions, and agents.">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Reports" value={data?.total_reports || 0} Icon={FileText} />
        <Stat label="Research Sessions" value={data?.research_sessions || 0} Icon={Activity} />
        <Stat label="Web Sources" value={data?.web_sources || 0} Icon={Search} />
        <Stat label="Feedback" value={data?.feedback_count || 0} Icon={History} />
      </div>
      <ChartPanel title="Agent Usage" data={rows} />
    </Page>
  );
}

function EvaluationPage() {
  const { data, loading, error } = useAsync(api.evaluation, []);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={`${error}. Evaluation metrics are admin-only.`} />;
  const rows = (data.history || []).map((x, i) => ({
    name: `E${i + 1}`,
    accuracy: x.accuracy,
    faithfulness: x.faithfulness,
    citation: x.citation_correctness,
    hallucination: x.hallucination_rate
  }));
  const latest = data.summary || data.history?.[0] || {};
  return (
    <Page title="Evaluation Dashboard" subtitle="Quality metrics for generated reports. Admin only.">
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Accuracy" value={`${Math.round((latest.accuracy || 0) * 100)}%`} Icon={Gauge} />
        <Stat label="Relevance" value={`${Math.round((latest.relevance || 0) * 100)}%`} Icon={Search} />
        <Stat label="Citation Quality" value={`${Math.round((latest.citation_correctness || 0) * 100)}%`} Icon={FileText} />
        <Stat label="Latency" value={`${latest.latency_ms || 0} ms`} Icon={Activity} />
      </div>
      <div className="panel h-96 p-5">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip />
            <Line type="monotone" dataKey="accuracy" stroke="#be185d" />
            <Line type="monotone" dataKey="faithfulness" stroke="#d97706" />
            <Line type="monotone" dataKey="citation" stroke="#7c2d12" />
            <Line type="monotone" dataKey="hallucination" stroke="#e11d48" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Page>
  );
}

function SecurityPage() {
  const { data, loading, error } = useAsync(api.security, []);
  if (loading) return <Loading />;
  if (error) return <ErrorBox message={`${error}. Security logs are admin-only.`} />;
  return (
    <Page title="Security Dashboard" subtitle="Blocked prompts, validation failures, and security events. Admin only.">
      <div className="panel overflow-hidden">
        {(data.events || []).length === 0 ? (
          <p className="p-5 text-sm text-steel">No security events recorded.</p>
        ) : (
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-steel">
              <tr><th className="p-3">Severity</th><th className="p-3">Event</th><th className="p-3">Description</th><th className="p-3">Time</th></tr>
            </thead>
            <tbody>
              {(data.events || []).map((event, index) => (
                <tr className="border-t border-slate-200" key={index}>
                  <td className="p-3 font-semibold">{event.severity}</td>
                  <td className="p-3">{event.event_type}</td>
                  <td className="p-3 text-steel">{event.description}</td>
                  <td className="p-3">{new Date(event.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Page>
  );
}

function SettingsPage() {
  const user = getStoredUser();
  return <Page title="Profile Settings" subtitle="Workspace identity and role permissions."><div className="panel p-5"><pre className="text-sm">{JSON.stringify(user, null, 2)}</pre></div></Page>;
}

function Loading() {
  return (
    <div className="space-y-6">
      <div className="space-y-2 border-l-4 border-rose-200 pl-4">
        <div className="skeleton h-8 w-72 max-w-full" />
        <div className="skeleton h-4 w-96 max-w-full" />
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div className="panel p-5" key={item}>
            <div className="flex items-center justify-between">
              <div className="skeleton h-4 w-24" />
              <div className="skeleton h-9 w-9" />
            </div>
            <div className="skeleton mt-5 h-9 w-20" />
          </div>
        ))}
      </div>
      <div className="panel p-5">
        <div className="skeleton h-5 w-44" />
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((item) => <div className="skeleton h-16" key={item} />)}
        </div>
      </div>
    </div>
  );
}

function ErrorBox({ message }) {
  return <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-coral">{message}</div>;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route element={<Protected />}>
          <Route element={<Shell />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analysis/:unused" element={<AnalysisRoute />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/:id" element={<ReportViewer />} />
            <Route path="/analytics" element={<AdminOnly><AnalyticsPage /></AdminOnly>} />
            <Route path="/evaluation" element={<AdminOnly><EvaluationPage /></AdminOnly>} />
            <Route path="/security" element={<AdminOnly><SecurityPage /></AdminOnly>} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  );
}

function AnalysisRoute() {
  const { unused } = useParams();
  const mode = ["startup", "company_comparison"].includes(unused) ? unused : "startup";
  return <AnalysisPage mode={mode} />;
}

createRoot(document.getElementById("root")).render(<App />);
