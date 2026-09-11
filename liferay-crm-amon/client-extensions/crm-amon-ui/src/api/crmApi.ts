import { loadDb, saveDb, uid } from './mockDb';
import type {
  CrmAccount, CrmCompany, CrmNote, CrmOffice, CrmOpportunity,
  CrmPerson, CrmTask, CrmUser, CrmView, OpportunityStage,
} from '../types/crm';

export class ApiError extends Error {
  code: 'FORBIDDEN' | 'VALIDATION' | 'NOT_FOUND' | 'CONFLICT';
  constructor(code: ApiError['code'], message: string) {
    super(message);
    this.code = code;
  }
}

const stamp = () => new Date().toISOString();
const alive = <T extends { accountId: string; deleted?: boolean }>(rows: T[], accountId: string) =>
  rows.filter((r) => r.accountId === accountId && !r.deleted);
const assertWrite = (user: CrmUser) => {
  if (user.role === 'VIEWER') throw new ApiError('FORBIDDEN', 'errors.forbidden');
};

export const crmApi = {
  listAccounts: (): CrmAccount[] => loadDb().accounts,
  getUser: (id: string) => loadDb().users.find((u) => u.id === id),
  listUsers: (accountId: string) => loadDb().users.filter((u) => u.accountId === accountId),
  listOffices: (accountId: string) => loadDb().offices.filter((o) => o.accountId === accountId),

  updateAccount(accountId: string, patch: Partial<CrmAccount>, user: CrmUser): CrmAccount {
    if (user.role !== 'ADMIN' && user.role !== 'MANAGER') throw new ApiError('FORBIDDEN', 'errors.forbidden');
    const db = loadDb();
    const idx = db.accounts.findIndex((a) => a.id === accountId);
    if (idx < 0) throw new ApiError('NOT_FOUND', 'errors.validation');
    if (patch.accountType === 'FREELANCE' && db.accounts[idx].accountType === 'AGENCY') {
      if (db.users.filter((u) => u.accountId === accountId).length > 1 ||
          db.offices.some((o) => o.accountId === accountId)) {
        throw new ApiError('VALIDATION', 'errors.validation');
      }
    }
    db.accounts[idx] = { ...db.accounts[idx], ...patch, id: accountId };
    saveDb(db);
    return db.accounts[idx];
  },

  createOffice(accountId: string, data: Omit<CrmOffice, 'id' | 'accountId'>, user: CrmUser): CrmOffice {
    if (user.role !== 'ADMIN' && user.role !== 'MANAGER') throw new ApiError('FORBIDDEN', 'errors.forbidden');
    const db = loadDb();
    const account = db.accounts.find((a) => a.id === accountId);
    if (!account || account.accountType !== 'AGENCY') throw new ApiError('VALIDATION', 'errors.validation');
    if (db.offices.some((o) => o.accountId === accountId && o.name === data.name)) {
      throw new ApiError('CONFLICT', 'errors.uniqueName');
    }
    const office: CrmOffice = { ...data, id: uid('off'), accountId };
    db.offices.push(office); saveDb(db); return office;
  },

  listCompanies(accountId: string, opts?: { q?: string; icpOnly?: boolean }): CrmCompany[] {
    let rows = alive(loadDb().companies, accountId);
    if (opts?.icpOnly) rows = rows.filter((c) => c.idealCustomerProfile);
    if (opts?.q) {
      const q = opts.q.toLowerCase();
      rows = rows.filter((c) => c.name.toLowerCase().includes(q) || (c.domainName ?? '').toLowerCase().includes(q));
    }
    return rows;
  },
  getCompany(accountId: string, id: string) {
    const row = alive(loadDb().companies, accountId).find((c) => c.id === id);
    if (!row) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    return row;
  },
  createCompany(accountId: string, data: Pick<CrmCompany, 'name'> & Partial<CrmCompany>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    if (db.companies.some((c) => c.accountId === accountId && !c.deleted && c.name === data.name)) {
      throw new ApiError('CONFLICT', 'errors.uniqueName');
    }
    const row: CrmCompany = {
      idealCustomerProfile: false, deleted: false, createdAt: stamp(), updatedAt: stamp(),
      ...data, id: uid('co'), accountId, name: data.name,
    };
    db.companies.push(row); saveDb(db); return row;
  },
  deleteCompany(accountId: string, id: string, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    if (db.opportunities.some((o) => o.accountId === accountId && o.companyId === id && !o.deleted && o.stage !== 'WON' && o.stage !== 'LOST')) {
      throw new ApiError('VALIDATION', 'errors.openOpportunities');
    }
    const idx = db.companies.findIndex((c) => c.id === id && c.accountId === accountId);
    if (idx < 0) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    db.companies[idx].deleted = true; db.companies[idx].updatedAt = stamp(); saveDb(db);
  },

  listPeople(accountId: string, opts?: { q?: string; companyId?: string }): CrmPerson[] {
    let rows = alive(loadDb().people, accountId);
    if (opts?.companyId) rows = rows.filter((p) => p.companyId === opts.companyId);
    if (opts?.q) {
      const q = opts.q.toLowerCase();
      rows = rows.filter((p) => `${p.firstName} ${p.lastName}`.toLowerCase().includes(q) || (p.primaryEmail ?? '').toLowerCase().includes(q));
    }
    return rows;
  },
  getPerson(accountId: string, id: string) {
    const row = alive(loadDb().people, accountId).find((p) => p.id === id);
    if (!row) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    return row;
  },
  createPerson(accountId: string, data: Pick<CrmPerson, 'firstName' | 'lastName' | 'personType'> & Partial<CrmPerson>, user: CrmUser) {
    assertWrite(user);
    if (!data.primaryEmail && !data.phoneNumber) throw new ApiError('VALIDATION', 'errors.validation');
    const db = loadDb();
    if (data.primaryEmail && db.people.some((p) => p.accountId === accountId && !p.deleted && p.primaryEmail === data.primaryEmail)) {
      throw new ApiError('CONFLICT', 'errors.uniqueEmail');
    }
    if (data.companyId && !db.companies.some((c) => c.id === data.companyId && c.accountId === accountId && !c.deleted)) {
      throw new ApiError('VALIDATION', 'errors.validation');
    }
    const row: CrmPerson = {
      deleted: false, createdAt: stamp(), updatedAt: stamp(),
      ...data, id: uid('pe'), accountId, firstName: data.firstName, lastName: data.lastName, personType: data.personType,
    };
    db.people.push(row); saveDb(db); return row;
  },

  listOpportunities(accountId: string) { return alive(loadDb().opportunities, accountId); },
  getOpportunity(accountId: string, id: string) {
    const row = alive(loadDb().opportunities, accountId).find((o) => o.id === id);
    if (!row) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    return row;
  },
  createOpportunity(accountId: string, data: Pick<CrmOpportunity, 'name' | 'companyId' | 'currencyCode'> & Partial<CrmOpportunity>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    if (!db.companies.some((c) => c.id === data.companyId && c.accountId === accountId && !c.deleted)) {
      throw new ApiError('VALIDATION', 'errors.validation');
    }
    const stage = data.stage ?? 'NEW';
    const position = db.opportunities.filter((o) => o.accountId === accountId && o.stage === stage && !o.deleted).length + 1;
    const row: CrmOpportunity = {
      deleted: false, createdAt: stamp(), updatedAt: stamp(), position, stage,
      ...data, id: uid('op'), accountId, name: data.name, companyId: data.companyId, currencyCode: data.currencyCode,
    };
    db.opportunities.push(row); saveDb(db); return row;
  },
  updateOpportunity(accountId: string, id: string, patch: Partial<CrmOpportunity>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    const idx = db.opportunities.findIndex((o) => o.id === id && o.accountId === accountId);
    if (idx < 0) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    const next = patch.stage as OpportunityStage | undefined;
    if (next === 'LOST' && !(patch.lostReason || db.opportunities[idx].lostReason)) {
      throw new ApiError('VALIDATION', 'errors.lostReasonRequired');
    }
    if (next === 'WON' && !patch.closeDate && !db.opportunities[idx].closeDate) {
      patch = { ...patch, closeDate: new Date().toISOString().slice(0, 10) };
    }
    const { accountId: _a, id: _i, ...rest } = patch;
    db.opportunities[idx] = { ...db.opportunities[idx], ...rest, accountId, id, updatedAt: stamp() };
    saveDb(db); return db.opportunities[idx];
  },

  listTasks(accountId: string) { return alive(loadDb().tasks, accountId); },
  createTask(accountId: string, data: Pick<CrmTask, 'title' | 'status'> & Partial<CrmTask>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    const row: CrmTask = { deleted: false, createdAt: stamp(), updatedAt: stamp(), ...data, id: uid('tk'), accountId, title: data.title, status: data.status };
    db.tasks.push(row); saveDb(db); return row;
  },
  updateTask(accountId: string, id: string, patch: Partial<CrmTask>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    const idx = db.tasks.findIndex((t) => t.id === id && t.accountId === accountId);
    if (idx < 0) throw new ApiError('NOT_FOUND', 'errors.forbidden');
    const { accountId: _a, id: _i, ...rest } = patch;
    db.tasks[idx] = { ...db.tasks[idx], ...rest, accountId, id, updatedAt: stamp() };
    saveDb(db); return db.tasks[idx];
  },

  listNotes(accountId: string, targetType?: string, targetId?: string) {
    let rows = alive(loadDb().notes, accountId);
    if (targetType && targetId) rows = rows.filter((n) => n.targetType === targetType && n.targetId === targetId);
    return rows;
  },
  createNote(accountId: string, data: Pick<CrmNote, 'title' | 'targetType' | 'targetId' | 'createdBy'> & Partial<CrmNote>, user: CrmUser) {
    assertWrite(user);
    const db = loadDb();
    const row: CrmNote = { deleted: false, createdAt: stamp(), updatedAt: stamp(), ...data, id: uid('nt'), accountId, title: data.title, targetType: data.targetType, targetId: data.targetId, createdBy: data.createdBy };
    db.notes.push(row); saveDb(db); return row;
  },
  listViews(accountId: string): CrmView[] { return loadDb().views.filter((v) => v.accountId === accountId); },
};
