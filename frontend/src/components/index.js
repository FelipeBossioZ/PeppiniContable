// components/index.js
/**
 * Exportación centralizada de componentes
 */

// Common
export { default as Notification } from './common/Notification';
export { default as Loading } from './common/Loading';
export { default as SearchableSelect, AccountSelect, ThirdPartySelect } from './common/SearchableSelect';

// Auth
export { default as LoginForm } from './auth/LoginForm';

// Layout
export { default as Header } from './layout/Header';
export { default as Navigation } from './layout/Navigation';

// Transactions
export { default as TransactionForm } from './transactions/TransactionForm';
export { default as TransactionList } from './transactions/TransactionList';

// Dashboard
export { default as Dashboard } from './dashboard/Dashboard';
