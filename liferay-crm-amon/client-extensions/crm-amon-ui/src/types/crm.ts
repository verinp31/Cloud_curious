export type AccountType = 'FREELANCE' | 'AGENCY';
export type Locale = 'fr' | 'en';
export type OpportunityStage = 'NEW' | 'QUALIFYING' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'DONE';
export type PersonType = 'PROSPECT' | 'PARTNER' | 'MEDIA';
export type CurrencyCode = 'EUR' | 'USD' | 'GBP';
export type TargetType = 'COMPANY' | 'PERSON' | 'OPPORTUNITY';

export interface CrmAccount {
  id: string;
  name: string;
  accountType: AccountType;
  defaultLanguage: Locale;
  defaultCurrency: CurrencyCode;
}

export interface CrmOffice {
  id: string;
  accountId: string;
  name: string;
  city?: string;
  country?: string;
  managerUserId?: string;
  active: boolean;
}

export interface CrmUser {
  id: string;
  accountId: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'MANAGER' | 'SALES' | 'VIEWER';
  officeIds: string[];
}

export interface CrmCompany {
  id: string;
  accountId: string;
  name: string;
  domainName?: string;
  linkedinUrl?: string;
  employees?: number;
  addressStreet?: string;
  addressCity?: string;
  addressCountry?: string;
  idealCustomerProfile: boolean;
  accountOwnerId?: string;
  officeId?: string;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CrmPerson {
  id: string;
  accountId: string;
  firstName: string;
  lastName: string;
  jobTitle?: string;
  primaryEmail?: string;
  phoneNumber?: string;
  linkedinUrl?: string;
  city?: string;
  companyId?: string;
  personType: PersonType;
  officeId?: string;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CrmOpportunity {
  id: string;
  accountId: string;
  name: string;
  stage: OpportunityStage;
  amount?: number;
  currencyCode: CurrencyCode;
  closeDate?: string;
  companyId: string;
  pointOfContactId?: string;
  ownerId?: string;
  probability?: number;
  lostReason?: string;
  officeId?: string;
  position: number;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CrmTask {
  id: string;
  accountId: string;
  title: string;
  body?: string;
  status: TaskStatus;
  dueAt?: string;
  assigneeId?: string;
  targetType?: TargetType;
  targetId?: string;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CrmNote {
  id: string;
  accountId: string;
  title: string;
  body?: string;
  targetType: TargetType;
  targetId: string;
  createdBy: string;
  deleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CrmView {
  id: string;
  accountId: string;
  name: string;
  objectType: 'COMPANY' | 'PERSON' | 'OPPORTUNITY' | 'TASK';
  filtersJson: string;
  columnsJson: string;
  isShared: boolean;
  ownerUserId: string;
}

export const STAGES: OpportunityStage[] = [
  'NEW', 'QUALIFYING', 'PROPOSAL', 'NEGOTIATION', 'WON', 'LOST',
];
