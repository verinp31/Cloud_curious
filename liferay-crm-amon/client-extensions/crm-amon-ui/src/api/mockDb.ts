import type {
  CrmAccount, CrmCompany, CrmNote, CrmOffice, CrmOpportunity,
  CrmPerson, CrmTask, CrmUser, CrmView,
} from '../types/crm';

const now = () => new Date().toISOString();

export interface MockDb {
  accounts: CrmAccount[];
  offices: CrmOffice[];
  users: CrmUser[];
  companies: CrmCompany[];
  people: CrmPerson[];
  opportunities: CrmOpportunity[];
  tasks: CrmTask[];
  notes: CrmNote[];
  views: CrmView[];
}

function seed(): MockDb {
  const agency: CrmAccount = {
    id: 'acc-agency', name: 'Oxygen RP', accountType: 'AGENCY',
    defaultLanguage: 'fr', defaultCurrency: 'EUR',
  };
  const freelance: CrmAccount = {
    id: 'acc-freelance', name: 'Studio Verin', accountType: 'FREELANCE',
    defaultLanguage: 'fr', defaultCurrency: 'EUR',
  };
  return {
    accounts: [agency, freelance],
    offices: [
      { id: 'off-paris', accountId: agency.id, name: 'Paris', city: 'Paris', country: 'FR', managerUserId: 'usr-alice', active: true },
      { id: 'off-lyon', accountId: agency.id, name: 'Lyon', city: 'Lyon', country: 'FR', managerUserId: 'usr-bob', active: true },
    ],
    users: [
      { id: 'usr-alice', accountId: agency.id, name: 'Alice Dupont', email: 'alice@oxygen.fr', role: 'ADMIN', officeIds: ['off-paris'] },
      { id: 'usr-bob', accountId: agency.id, name: 'Bob Martin', email: 'bob@oxygen.fr', role: 'SALES', officeIds: ['off-lyon'] },
      { id: 'usr-carla', accountId: agency.id, name: 'Carla Vue', email: 'carla@oxygen.fr', role: 'VIEWER', officeIds: ['off-paris'] },
      { id: 'usr-patrice', accountId: freelance.id, name: 'Patrice Verin', email: 'patrice@studioverin.fr', role: 'ADMIN', officeIds: [] },
    ],
    companies: [
      { id: 'co-media', accountId: agency.id, name: 'MediaCorp', domainName: 'mediacorp.fr', employees: 120, addressCity: 'Paris', addressCountry: 'FR', idealCustomerProfile: true, accountOwnerId: 'usr-alice', officeId: 'off-paris', deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'co-startup', accountId: agency.id, name: 'StartupX', domainName: 'startupx.io', employees: 8, addressCity: 'Lyon', addressCountry: 'FR', idealCustomerProfile: false, accountOwnerId: 'usr-bob', officeId: 'off-lyon', deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'co-boutique', accountId: freelance.id, name: 'Boutique Lumiere', domainName: 'boutiquelumiere.fr', employees: 3, addressCity: 'Toulouse', addressCountry: 'FR', idealCustomerProfile: true, accountOwnerId: 'usr-patrice', deleted: false, createdAt: now(), updatedAt: now() },
    ],
    people: [
      { id: 'pe-jean', accountId: agency.id, firstName: 'Jean', lastName: 'Martin', jobTitle: 'Dircom', primaryEmail: 'j.martin@mediacorp.fr', phoneNumber: '+33601020304', companyId: 'co-media', personType: 'PROSPECT', officeId: 'off-paris', deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'pe-sophie', accountId: agency.id, firstName: 'Sophie', lastName: 'Bernard', jobTitle: 'CEO', primaryEmail: 'sophie@startupx.io', companyId: 'co-startup', personType: 'PROSPECT', officeId: 'off-lyon', deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'pe-lea', accountId: freelance.id, firstName: 'Lea', lastName: 'Moreau', jobTitle: 'Fondatrice', primaryEmail: 'lea@boutiquelumiere.fr', companyId: 'co-boutique', personType: 'PROSPECT', deleted: false, createdAt: now(), updatedAt: now() },
    ],
    opportunities: [
      { id: 'op-q2', accountId: agency.id, name: 'Campagne Q2 MediaCorp', stage: 'PROPOSAL', amount: 12000, currencyCode: 'EUR', closeDate: '2026-06-30', companyId: 'co-media', pointOfContactId: 'pe-jean', ownerId: 'usr-alice', probability: 60, officeId: 'off-paris', position: 1, deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'op-audit', accountId: agency.id, name: 'Audit digital StartupX', stage: 'QUALIFYING', amount: 4500, currencyCode: 'EUR', companyId: 'co-startup', pointOfContactId: 'pe-sophie', ownerId: 'usr-bob', probability: 30, officeId: 'off-lyon', position: 1, deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'op-new', accountId: agency.id, name: 'Lancement produit MediaCorp', stage: 'NEW', amount: 8000, currencyCode: 'EUR', companyId: 'co-media', ownerId: 'usr-alice', officeId: 'off-paris', position: 2, deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'op-freelance', accountId: freelance.id, name: 'Relations presse printemps', stage: 'NEGOTIATION', amount: 2500, currencyCode: 'EUR', companyId: 'co-boutique', pointOfContactId: 'pe-lea', ownerId: 'usr-patrice', probability: 70, position: 1, deleted: false, createdAt: now(), updatedAt: now() },
    ],
    tasks: [
      { id: 'tk-1', accountId: agency.id, title: 'Relancer Jean Martin', status: 'TODO', dueAt: new Date().toISOString().slice(0, 10), assigneeId: 'usr-alice', targetType: 'OPPORTUNITY', targetId: 'op-q2', deleted: false, createdAt: now(), updatedAt: now() },
      { id: 'tk-2', accountId: agency.id, title: 'Envoyer proposition StartupX', status: 'IN_PROGRESS', dueAt: new Date().toISOString().slice(0, 10), assigneeId: 'usr-bob', targetType: 'OPPORTUNITY', targetId: 'op-audit', deleted: false, createdAt: now(), updatedAt: now() },
    ],
    notes: [
      { id: 'nt-1', accountId: agency.id, title: 'Call discovery', body: 'Besoin RP product launch Q2.', targetType: 'OPPORTUNITY', targetId: 'op-q2', createdBy: 'usr-alice', deleted: false, createdAt: now(), updatedAt: now() },
    ],
    views: [
      { id: 'vw-icp', accountId: agency.id, name: 'ICP', objectType: 'COMPANY', filtersJson: '{"idealCustomerProfile":true}', columnsJson: '["name","domainName"]', isShared: true, ownerUserId: 'usr-alice' },
    ],
  };
}

const KEY = 'crm-amon-mock-db-v2';
export function loadDb(): MockDb {
  const raw = localStorage.getItem(KEY);
  if (raw) { try { return JSON.parse(raw) as MockDb; } catch { /* ignore */ } }
  const db = seed(); saveDb(db); return db;
}
export function saveDb(db: MockDb): void { localStorage.setItem(KEY, JSON.stringify(db)); }
export function resetDb(): MockDb { localStorage.removeItem(KEY); return loadDb(); }
export function uid(prefix: string): string { return `${prefix}-${Math.random().toString(36).slice(2, 10)}`; }
