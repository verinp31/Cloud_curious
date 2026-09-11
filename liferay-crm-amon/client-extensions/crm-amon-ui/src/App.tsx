import { useState, type FormEvent } from 'react';
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useParams,
} from 'react-router-dom';
import { ApiError, crmApi } from './api/crmApi';
import { SessionProvider, useSession } from './session/SessionContext';
import { STAGES, type OpportunityStage } from './types/crm';
import './styles/crm.css';

function LoginPage() {
  const { login, tr } = useSession();
  return (
    <div className="center-screen">
      <div className="card narrow">
        <h1>{tr('login.title')}</h1>
        <p className="muted">{tr('login.hint')}</p>
        <button type="button" onClick={login}>{tr('login.submit')}</button>
      </div>
    </div>
  );
}

function AccountSelectPage() {
  const { selectAccount, tr } = useSession();
  const accounts = crmApi.listAccounts();
  return (
    <div className="center-screen">
      <div className="card narrow">
        <h1>{tr('account.title')}</h1>
        <div className="stack">
          {accounts.map((a) => (
            <div className="row-card" key={a.id}>
              <div>
                <strong>{a.name}</strong>
                <div className="muted">
                  {a.accountType === 'AGENCY' ? tr('account.agency') : tr('account.freelance')}
                </div>
              </div>
              <button type="button" onClick={() => selectAccount(a.id)}>{tr('account.enter')}</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ShellLayout() {
  const { account, tr, locale, setLocale, clearAccount, logout } = useSession();
  const links = [
    ['/', 'nav.home'],
    ['/companies', 'nav.companies'],
    ['/people', 'nav.people'],
    ['/opportunities', 'nav.opportunities'],
    ['/tasks', 'nav.tasks'],
    ['/admin', 'nav.admin'],
    ['/preferences', 'nav.preferences'],
  ] as const;
  return (
    <div className="shell">
      <aside>
        <div className="brand">{tr('shell.brand')}</div>
        <nav>
          {links.map(([to, key]) => (
            <NavLink key={to} to={to} end={to === '/'}>{tr(key)}</NavLink>
          ))}
        </nav>
      </aside>
      <section>
        <header className="top">
          <div>
            <strong>{account?.name}</strong>
            <div className="muted">
              {account?.accountType === 'AGENCY' ? tr('account.agency') : tr('account.freelance')}
            </div>
          </div>
          <div className="actions">
            <select value={locale} onChange={(e) => setLocale(e.target.value as 'fr' | 'en')}>
              <option value="fr">FR</option>
              <option value="en">EN</option>
            </select>
            <button type="button" className="ghost" onClick={clearAccount}>{tr('account.switch')}</button>
            <button type="button" className="ghost" onClick={logout}>Logout</button>
          </div>
        </header>
        <div className="page">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/companies" element={<CompaniesPage />} />
            <Route path="/companies/:id" element={<CompanyDetailPage />} />
            <Route path="/people" element={<PeoplePage />} />
            <Route path="/people/:id" element={<PersonDetailPage />} />
            <Route path="/opportunities" element={<OpportunitiesPage />} />
            <Route path="/opportunities/:id" element={<OpportunityDetailPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/preferences" element={<PreferencesPage />} />
          </Routes>
        </div>
      </section>
    </div>
  );
}

function HomePage() {
  const { account, tr, rev } = useSession();
  if (!account) return null;
  void rev;
  const opps = crmApi.listOpportunities(account.id);
  const open = opps.filter((o) => o.stage !== 'WON' && o.stage !== 'LOST');
  const qualifying = opps.filter((o) => o.stage === 'QUALIFYING');
  const today = new Date().toISOString().slice(0, 10);
  const tasks = crmApi.listTasks(account.id).filter((t) => t.status !== 'DONE' && t.dueAt === today);
  const companies = Object.fromEntries(crmApi.listCompanies(account.id).map((c) => [c.id, c.name]));
  return (
    <div>
      <h1>{tr('home.title')}</h1>
      <div className="metrics">
        <div><span>{tr('home.open')}</span><strong>{open.length}</strong></div>
        <div><span>{tr('home.qualifying')}</span><strong>{qualifying.length}</strong></div>
        <div><span>{tr('home.tasks')}</span><strong>{tasks.length}</strong></div>
      </div>
      <div className="card">
        <h2>{tr('home.recent')}</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>{tr('people.company')}</th>
              <th>{tr('opportunities.stage')}</th>
              <th>{tr('opportunities.amount')}</th>
            </tr>
          </thead>
          <tbody>
            {open.slice(0, 5).map((o) => (
              <tr key={o.id}>
                <td><Link to={`/opportunities/${o.id}`}>{o.name}</Link></td>
                <td>{companies[o.companyId]}</td>
                <td>{tr(`stage.${o.stage}` as 'stage.NEW')}</td>
                <td>{o.amount?.toLocaleString()} {o.currencyCode}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CompaniesPage() {
  const { account, user, tr, bump, rev } = useSession();
  const [q, setQ] = useState('');
  const [icpOnly, setIcpOnly] = useState(false);
  const [name, setName] = useState('');
  const [domainName, setDomainName] = useState('');
  const [error, setError] = useState('');
  if (!account || !user) return null;
  const currentAccount = account;
  const currentUser = user;
  void rev;
  const rows = crmApi.listCompanies(currentAccount.id, { q, icpOnly });
  function onCreate(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      crmApi.createCompany(currentAccount.id, {
        name,
        domainName: domainName || undefined,
        accountOwnerId: currentUser.id,
      }, currentUser);
      setName('');
      setDomainName('');
      bump();
    } catch (err) {
      setError(err instanceof ApiError && err.message === 'errors.uniqueName'
        ? tr('errors.uniqueName')
        : tr('errors.validation'));
    }
  }
  return (
    <div>
      <div className="toolbar">
        <h1>{tr('companies.title')}</h1>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={tr('common.search')} />
        <label><input type="checkbox" checked={icpOnly} onChange={(e) => setIcpOnly(e.target.checked)} /> ICP</label>
      </div>
      {error && <p className="error">{error}</p>}
      <form className="card form" onSubmit={onCreate}>
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder={tr('companies.name')} />
        <input value={domainName} onChange={(e) => setDomainName(e.target.value)} placeholder={tr('companies.domain')} />
        <button type="submit">{tr('companies.new')}</button>
      </form>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>{tr('companies.name')}</th>
              <th>{tr('companies.domain')}</th>
              <th>{tr('companies.city')}</th>
              <th>{tr('companies.icp')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td><Link to={`/companies/${c.id}`}>{c.name}</Link></td>
                <td>{c.domainName ?? '—'}</td>
                <td>{c.addressCity ?? '—'}</td>
                <td>{c.idealCustomerProfile ? tr('common.yes') : tr('common.no')}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4}>{tr('common.empty')}</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CompanyDetailPage() {
  const { id = '' } = useParams();
  const { account, user, tr, bump, rev } = useSession();
  const [error, setError] = useState('');
  if (!account || !user) return null;
  void rev;
  let company;
  try {
    company = crmApi.getCompany(account.id, id);
  } catch {
    return <p className="error">{tr('errors.forbidden')}</p>;
  }
  const people = crmApi.listPeople(account.id, { companyId: id });
  const opps = crmApi.listOpportunities(account.id).filter((o) => o.companyId === id);
  const notes = crmApi.listNotes(account.id, 'COMPANY', id);
  return (
    <div>
      <div className="toolbar">
        <Link to="/companies">{tr('common.back')}</Link>
        <h1>{company.name}</h1>
        <button
          type="button"
          className="danger"
          onClick={() => {
            try {
              crmApi.deleteCompany(account.id, id, user);
              window.location.href = '/companies';
            } catch {
              setError(tr('errors.openOpportunities'));
            }
          }}
        >
          {tr('common.delete')}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="card">
        <p>{tr('companies.domain')}: {company.domainName ?? '—'}</p>
        <p>{tr('companies.city')}: {company.addressCity ?? '—'}</p>
      </div>
      <div className="card">
        <h2>{tr('people.title')}</h2>
        <ul>{people.map((p) => <li key={p.id}><Link to={`/people/${p.id}`}>{p.firstName} {p.lastName}</Link></li>)}</ul>
      </div>
      <div className="card">
        <h2>{tr('opportunities.title')}</h2>
        <ul>{opps.map((o) => <li key={o.id}><Link to={`/opportunities/${o.id}`}>{o.name}</Link></li>)}</ul>
      </div>
      <div className="card">
        <h2>Notes</h2>
        {notes.map((n) => <div key={n.id}><strong>{n.title}</strong><div className="muted">{n.body}</div></div>)}
        <button
          type="button"
          onClick={() => {
            crmApi.createNote(account.id, {
              title: 'Note',
              body: 'Follow-up',
              targetType: 'COMPANY',
              targetId: id,
              createdBy: user.id,
            }, user);
            bump();
          }}
        >
          {tr('common.add')}
        </button>
      </div>
    </div>
  );
}

function PeoplePage() {
  const { account, user, tr, bump, rev } = useSession();
  const [q, setQ] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [primaryEmail, setPrimaryEmail] = useState('');
  const [companyId, setCompanyId] = useState('');
  const [error, setError] = useState('');
  if (!account || !user) return null;
  const currentAccount = account;
  const currentUser = user;
  void rev;
  const companies = crmApi.listCompanies(currentAccount.id);
  const rows = crmApi.listPeople(currentAccount.id, { q });
  function onCreate(e: FormEvent) {
    e.preventDefault();
    setError('');
    try {
      crmApi.createPerson(currentAccount.id, {
        firstName,
        lastName,
        primaryEmail,
        personType: 'PROSPECT',
        companyId: companyId || undefined,
      }, currentUser);
      setFirstName('');
      setLastName('');
      setPrimaryEmail('');
      bump();
    } catch (err) {
      setError(err instanceof ApiError && err.message === 'errors.uniqueEmail'
        ? tr('errors.uniqueEmail')
        : tr('errors.validation'));
    }
  }
  return (
    <div>
      <div className="toolbar">
        <h1>{tr('people.title')}</h1>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={tr('common.search')} />
      </div>
      {error && <p className="error">{error}</p>}
      <form className="card form" onSubmit={onCreate}>
        <input required value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="First" />
        <input required value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Last" />
        <input required type="email" value={primaryEmail} onChange={(e) => setPrimaryEmail(e.target.value)} placeholder={tr('people.email')} />
        <select value={companyId} onChange={(e) => setCompanyId(e.target.value)}>
          <option value="">—</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button type="submit">{tr('people.new')}</button>
      </form>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>{tr('people.name')}</th>
              <th>{tr('people.email')}</th>
              <th>{tr('people.company')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id}>
                <td><Link to={`/people/${p.id}`}>{p.firstName} {p.lastName}</Link></td>
                <td>{p.primaryEmail}</td>
                <td>{companies.find((c) => c.id === p.companyId)?.name ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PersonDetailPage() {
  const { id = '' } = useParams();
  const { account, tr } = useSession();
  if (!account) return null;
  let person;
  try {
    person = crmApi.getPerson(account.id, id);
  } catch {
    return <p className="error">{tr('errors.forbidden')}</p>;
  }
  return (
    <div>
      <Link to="/people">{tr('common.back')}</Link>
      <h1>{person.firstName} {person.lastName}</h1>
      <div className="card">
        <p>{tr('people.email')}: {person.primaryEmail}</p>
        <p>{person.jobTitle}</p>
      </div>
    </div>
  );
}

function OpportunitiesPage() {
  const { account, user, tr, bump, rev } = useSession();
  const [mode, setMode] = useState<'table' | 'kanban'>('kanban');
  const [name, setName] = useState('');
  const [companyId, setCompanyId] = useState('');
  const [amount, setAmount] = useState('1000');
  const [lostReason, setLostReason] = useState('');
  const [pendingLostId, setPendingLostId] = useState<string | null>(null);
  const [error, setError] = useState('');
  if (!account || !user) return null;
  const currentAccount = account;
  const currentUser = user;
  void rev;
  const companies = crmApi.listCompanies(currentAccount.id);
  const rows = crmApi.listOpportunities(currentAccount.id);

  function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    crmApi.createOpportunity(currentAccount.id, {
      name,
      companyId,
      currencyCode: currentAccount.defaultCurrency,
      amount: Number(amount) || 0,
      stage: 'NEW',
      ownerId: currentUser.id,
    }, currentUser);
    setName('');
    bump();
  }

  function move(id: string, stage: OpportunityStage) {
    setError('');
    if (stage === 'LOST') {
      setPendingLostId(id);
      return;
    }
    try {
      crmApi.updateOpportunity(currentAccount.id, id, { stage }, currentUser);
      bump();
    } catch {
      setError(tr('errors.validation'));
    }
  }

  function confirmLost(e: FormEvent) {
    e.preventDefault();
    if (!pendingLostId) return;
    try {
      crmApi.updateOpportunity(currentAccount.id, pendingLostId, { stage: 'LOST', lostReason }, currentUser);
      setPendingLostId(null);
      setLostReason('');
      bump();
    } catch {
      setError(tr('errors.lostReasonRequired'));
    }
  }

  return (
    <div>
      <div className="toolbar">
        <h1>{tr('opportunities.title')}</h1>
        <button type="button" className={mode === 'table' ? undefined : 'ghost'} onClick={() => setMode('table')}>{tr('opportunities.table')}</button>
        <button type="button" className={mode === 'kanban' ? undefined : 'ghost'} onClick={() => setMode('kanban')}>{tr('opportunities.kanban')}</button>
      </div>
      {error && <p className="error">{error}</p>}
      <form className="card form" onSubmit={onCreate}>
        <input required value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
        <select required value={companyId} onChange={(e) => setCompanyId(e.target.value)}>
          <option value="">Company</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
        <button type="submit">{tr('opportunities.new')}</button>
      </form>
      {pendingLostId && (
        <form className="card form" onSubmit={confirmLost}>
          <input required placeholder={tr('opportunities.lostReason')} value={lostReason} onChange={(e) => setLostReason(e.target.value)} />
          <button type="submit">{tr('common.save')}</button>
          <button type="button" className="ghost" onClick={() => setPendingLostId(null)}>{tr('common.cancel')}</button>
        </form>
      )}
      {mode === 'table' ? (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>{tr('people.company')}</th>
                <th>{tr('opportunities.stage')}</th>
                <th>{tr('opportunities.amount')}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <tr key={o.id}>
                  <td><Link to={`/opportunities/${o.id}`}>{o.name}</Link></td>
                  <td>{companies.find((c) => c.id === o.companyId)?.name}</td>
                  <td>{tr(`stage.${o.stage}` as 'stage.NEW')}</td>
                  <td>{o.amount?.toLocaleString()} {o.currencyCode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="kanban">
          {STAGES.map((stage) => (
            <div
              className="kanban-col"
              key={stage}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                const id = e.dataTransfer.getData('text/plain');
                if (id) move(id, stage);
              }}
            >
              <h3>{tr(`stage.${stage}` as 'stage.NEW')}</h3>
              {rows.filter((o) => o.stage === stage).map((o) => (
                <div
                  className="kanban-card"
                  key={o.id}
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData('text/plain', o.id)}
                >
                  <Link to={`/opportunities/${o.id}`}>{o.name}</Link>
                  <div className="muted">{o.amount?.toLocaleString()} {o.currencyCode}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OpportunityDetailPage() {
  const { id = '' } = useParams();
  const { account, user, tr, bump, rev } = useSession();
  if (!account || !user) return null;
  void rev;
  let opp;
  try {
    opp = crmApi.getOpportunity(account.id, id);
  } catch {
    return <p className="error">{tr('errors.forbidden')}</p>;
  }
  const notes = crmApi.listNotes(account.id, 'OPPORTUNITY', id);
  const tasks = crmApi.listTasks(account.id).filter((t) => t.targetType === 'OPPORTUNITY' && t.targetId === id);
  return (
    <div>
      <Link to="/opportunities">{tr('common.back')}</Link>
      <h1>{opp.name}</h1>
      <div className="card">
        <p>{tr('opportunities.stage')}: {tr(`stage.${opp.stage}` as 'stage.NEW')}</p>
        <p>{tr('opportunities.amount')}: {opp.amount} {opp.currencyCode}</p>
        <select
          value={opp.stage}
          onChange={(e) => {
            const stage = e.target.value as OpportunityStage;
            try {
              if (stage === 'LOST') {
                const reason = window.prompt(tr('opportunities.lostReason')) || '';
                crmApi.updateOpportunity(account.id, id, { stage, lostReason: reason }, user);
              } else {
                crmApi.updateOpportunity(account.id, id, { stage }, user);
              }
              bump();
            } catch {
              alert(tr('errors.lostReasonRequired'));
            }
          }}
        >
          {STAGES.map((s) => <option key={s} value={s}>{tr(`stage.${s}` as 'stage.NEW')}</option>)}
        </select>
      </div>
      <div className="card">
        <h2>Notes</h2>
        {notes.map((n) => <div key={n.id}><strong>{n.title}</strong><div className="muted">{n.body}</div></div>)}
        <button
          type="button"
          onClick={() => {
            crmApi.createNote(account.id, {
              title: 'Update',
              body: 'Point avance',
              targetType: 'OPPORTUNITY',
              targetId: id,
              createdBy: user.id,
            }, user);
            bump();
          }}
        >
          {tr('common.add')}
        </button>
      </div>
      <div className="card">
        <h2>{tr('tasks.title')}</h2>
        <ul>{tasks.map((t) => <li key={t.id}>{t.title} — {t.status}</li>)}</ul>
      </div>
    </div>
  );
}

function TasksPage() {
  const { account, user, tr, bump, rev } = useSession();
  const [title, setTitle] = useState('');
  if (!account || !user) return null;
  void rev;
  const rows = crmApi.listTasks(account.id);
  return (
    <div>
      <h1>{tr('tasks.title')}</h1>
      <form
        className="card form"
        onSubmit={(e) => {
          e.preventDefault();
          crmApi.createTask(account.id, {
            title,
            status: 'TODO',
            assigneeId: user.id,
            dueAt: new Date().toISOString().slice(0, 10),
          }, user);
          setTitle('');
          bump();
        }}
      >
        <input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder={tr('tasks.new')} />
        <button type="submit">{tr('common.add')}</button>
      </form>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>{tr('tasks.status')}</th>
              <th>{tr('tasks.due')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id}>
                <td>{t.title}</td>
                <td>
                  <select
                    value={t.status}
                    onChange={(e) => {
                      crmApi.updateTask(account.id, t.id, {
                        status: e.target.value as 'TODO' | 'IN_PROGRESS' | 'DONE',
                      }, user);
                      bump();
                    }}
                  >
                    <option value="TODO">TODO</option>
                    <option value="IN_PROGRESS">IN_PROGRESS</option>
                    <option value="DONE">DONE</option>
                  </select>
                </td>
                <td>{t.dueAt ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AdminPage() {
  const { account, user, tr, bump, rev } = useSession();
  const [officeName, setOfficeName] = useState('');
  const [error, setError] = useState('');
  if (!account || !user) return null;
  void rev;
  const offices = crmApi.listOffices(account.id);
  const users = crmApi.listUsers(account.id);
  return (
    <div>
      <h1>{tr('admin.title')}</h1>
      <div className="card">
        <h2>Account</h2>
        <p>{account.name} — {account.accountType === 'AGENCY' ? tr('account.agency') : tr('account.freelance')}</p>
        <p>{account.defaultLanguage} / {account.defaultCurrency}</p>
      </div>
      <div className="card">
        <h2>{tr('admin.offices')}</h2>
        {account.accountType === 'FREELANCE' ? (
          <p className="muted">{tr('admin.officesHidden')}</p>
        ) : (
          <>
            <ul>{offices.map((o) => <li key={o.id}>{o.name} — {o.city}</li>)}</ul>
            {error && <p className="error">{error}</p>}
            <form
              className="form"
              onSubmit={(e) => {
                e.preventDefault();
                setError('');
                try {
                  crmApi.createOffice(account.id, { name: officeName, city: officeName, active: true }, user);
                  setOfficeName('');
                  bump();
                } catch {
                  setError(tr('errors.uniqueName'));
                }
              }}
            >
              <input required value={officeName} onChange={(e) => setOfficeName(e.target.value)} placeholder="Bureau" />
              <button type="submit">{tr('common.add')}</button>
            </form>
          </>
        )}
      </div>
      <div className="card">
        <h2>{tr('admin.users')}</h2>
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
          <tbody>
            {users.map((u) => <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td></tr>)}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PreferencesPage() {
  const { locale, setLocale, tr } = useSession();
  return (
    <div>
      <h1>{tr('preferences.title')}</h1>
      <div className="card">
        <label>
          {tr('preferences.locale')}
          <select value={locale} onChange={(e) => setLocale(e.target.value as 'fr' | 'en')}>
            <option value="fr">Français</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>
    </div>
  );
}

function Gate() {
  const { authenticated, account } = useSession();
  if (!authenticated) return <LoginPage />;
  if (!account) return <AccountSelectPage />;
  return <ShellLayout />;
}

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Gate />
      </BrowserRouter>
    </SessionProvider>
  );
}
