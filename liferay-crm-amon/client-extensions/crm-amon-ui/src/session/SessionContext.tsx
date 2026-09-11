import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { crmApi } from '../api/crmApi';
import { t, type MessageKey } from '../i18n/messages';
import type { CrmAccount, CrmUser, Locale } from '../types/crm';

interface Session {
  authenticated: boolean;
  user: CrmUser | null;
  account: CrmAccount | null;
  locale: Locale;
  login: () => void;
  logout: () => void;
  selectAccount: (id: string) => void;
  clearAccount: () => void;
  setLocale: (locale: Locale) => void;
  tr: (key: MessageKey) => string;
  bump: () => void;
  rev: number;
}

const Ctx = createContext<Session | null>(null);
const DEMO_USER = 'usr-alice';

export function SessionProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(() => localStorage.getItem('crm-amon-auth') === '1');
  const [accountId, setAccountId] = useState<string | null>(() => localStorage.getItem('crm-amon-account'));
  const [locale, setLocaleState] = useState<Locale>(() => (localStorage.getItem('crm-amon-locale') as Locale) || 'fr');
  const [rev, setRev] = useState(0);

  const user = useMemo(() => (authenticated ? crmApi.getUser(DEMO_USER) ?? null : null), [authenticated, rev]);
  const account = useMemo(
    () => (accountId ? crmApi.listAccounts().find((a) => a.id === accountId) ?? null : null),
    [accountId, rev],
  );

  const value: Session = {
    authenticated,
    user,
    account,
    locale,
    rev,
    login: () => { localStorage.setItem('crm-amon-auth', '1'); setAuthenticated(true); },
    logout: () => {
      localStorage.removeItem('crm-amon-auth');
      localStorage.removeItem('crm-amon-account');
      setAuthenticated(false); setAccountId(null);
    },
    selectAccount: (id) => { localStorage.setItem('crm-amon-account', id); setAccountId(id); },
    clearAccount: () => { localStorage.removeItem('crm-amon-account'); setAccountId(null); },
    setLocale: (l) => { localStorage.setItem('crm-amon-locale', l); setLocaleState(l); },
    tr: (key) => t(locale, key),
    bump: () => setRev((x) => x + 1),
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useSession outside provider');
  return ctx;
}
