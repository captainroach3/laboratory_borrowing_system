import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import Modal from '../../components/Modal';
import { 
  Receipt, 
  Search, 
  CheckCircle, 
  Clock, 
  Hourglass, 
  Trash2, 
  AlertTriangle, 
  CheckCircle2, 
  UserCheck
} from 'lucide-react';

export default function TransactionsView() {
  const { user: currentUser, isAdmin } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Modals
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const txRes = await api.get('/transactions/');
      setTransactions(txRes.data || []);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to fetch transactions.');
    } finally {
      setLoading(false);
    }
  };

  // pending = waiting for staff, active = approved and still out, returned = back
  const getState = (tx) => {
    if (tx.return_datetime) return 'returned';
    if (tx.approver) return 'active';
    return 'pending';
  };

  const apiError = (err, fallback) => {
    const data = err.response?.data;
    return data?.message || (data ? JSON.stringify(data) : fallback);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredTransactions = transactions.filter((tx) => {
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      (tx.item_label || '').toLowerCase().includes(term) ||
      (tx.user_label || '').toLowerCase().includes(term) ||
      String(tx.transaction_id).includes(searchTerm);
    if (statusFilter === 'all') return matchesSearch;
    return matchesSearch && getState(tx) === statusFilter;
  });

  const handleOpenApproveModal = (tx) => {
    setSelectedTx(tx);
    setIsApproveOpen(true);
  };

  const handleConfirmApprove = async () => {
    if (!selectedTx) return;
    setFormSubmitting(true);
    setErrorMsg('');
    try {
      await api.post(`/transactions/${selectedTx.transaction_id}/approve/`);
      setSuccessMsg(`Request #${selectedTx.transaction_id} approved. Stock updated.`);
      setIsApproveOpen(false);
      fetchData();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      console.error(err);
      setErrorMsg(apiError(err, 'Error approving request.'));
      setIsApproveOpen(false);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleOpenReturnModal = (tx) => {
    setSelectedTx(tx);
    setIsReturnModalOpen(true);
  };

  const handleConfirmReturn = async () => {
    if (!selectedTx) return;
    setFormSubmitting(true);
    setErrorMsg('');
    try {
      await api.post(`/transactions/${selectedTx.transaction_id}/return/`);
      setSuccessMsg(`Transaction #${selectedTx.transaction_id} marked as returned.`);
      setIsReturnModalOpen(false);
      fetchData();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      console.error(err);
      setErrorMsg(apiError(err, 'Error marking item as returned.'));
      setIsReturnModalOpen(false);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleOpenDelete = (tx) => {
    setSelectedTx(tx);
    setIsDeleteOpen(true);
  };

  const handleDeleteSubmit = async () => {
    if (!selectedTx) return;
    setFormSubmitting(true);
    try {
      await api.delete(`/transactions/${selectedTx.transaction_id}/delete/`);
      setSuccessMsg('Transaction record deleted.');
      setIsDeleteOpen(false);
      fetchData();
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      console.error(err);
      setErrorMsg(apiError(err, 'Failed to delete transaction.'));
      setIsDeleteOpen(false);
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Receipt className="text-orange-500" size={20} />
            Borrowing Records & Custody Logs
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Approve borrow requests, track equipment currently out, and check items back in.
          </p>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 size={15} />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="p-3.5 rounded-xl bg-[#12141c] border border-zinc-800 flex flex-col sm:flex-row gap-2.5 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
            <Search size={14} />
          </div>
          <input
            type="text"
            placeholder="Search apparatus, borrower, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-white placeholder-zinc-500 text-xs focus:outline-none focus:border-orange-500"
          />
        </div>

        <div className="flex rounded-lg bg-zinc-900 p-1 border border-zinc-800 w-full sm:w-auto">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              statusFilter === 'all'
                ? 'bg-orange-600 text-white'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            All ({transactions.length})
          </button>
          <button
            onClick={() => setStatusFilter('pending')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              statusFilter === 'pending'
                ? 'bg-sky-600 text-white'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Pending ({transactions.filter((t) => getState(t) === 'pending').length})
          </button>
          <button
            onClick={() => setStatusFilter('active')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              statusFilter === 'active'
                ? 'bg-amber-600 text-white'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Active ({transactions.filter((t) => getState(t) === 'active').length})
          </button>
          <button
            onClick={() => setStatusFilter('returned')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
              statusFilter === 'returned'
                ? 'bg-emerald-600 text-white'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Returned ({transactions.filter((t) => getState(t) === 'returned').length})
          </button>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="rounded-2xl bg-[#12141c] border border-zinc-800 overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-xs text-zinc-500">
            <div className="w-5 h-5 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading transaction logs...
          </div>
        ) : filteredTransactions.length === 0 ? (
          <div className="py-16 text-center text-xs text-zinc-500">
            <Receipt size={32} className="mx-auto text-zinc-600 mb-2" />
            No transaction records found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[10px] uppercase tracking-wider text-zinc-400 bg-zinc-900/60 border-b border-zinc-800">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Apparatus</th>
                  <th className="px-4 py-3">Borrower</th>
                  <th className="px-4 py-3">Qty</th>
                  <th className="px-4 py-3">Borrowed At</th>
                  <th className="px-4 py-3">Returned At</th>
                  <th className="px-4 py-3">Custodian</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {filteredTransactions.map((tx) => {
                  const state = getState(tx);
                  const isReturned = state === 'returned';
                  return (
                    <tr key={tx.transaction_id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-zinc-400 font-medium">
                        #{tx.transaction_id}
                      </td>
                      <td className="px-4 py-3 font-semibold text-white">
                        {tx.item_label || `Item #${tx.item_name}`}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-zinc-200 font-medium">
                          {tx.user_label || `User #${tx.user}`}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-zinc-300">
                        {tx.quantity}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {tx.borrow_datetime
                          ? new Date(tx.borrow_datetime).toLocaleString([], {
                              dateStyle: 'short',
                              timeStyle: 'short',
                            })
                          : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {isReturned ? (
                          new Date(tx.return_datetime).toLocaleString([], {
                            dateStyle: 'short',
                            timeStyle: 'short',
                          })
                        ) : state === 'active' ? (
                          <span className="text-amber-400/80 italic text-[11px]">
                            Pending check-in
                          </span>
                        ) : (
                          <span className="text-zinc-500 text-[11px]">&mdash;</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-zinc-300">
                        {tx.approver_label ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-orange-400">
                            <UserCheck size={11} /> {tx.approver_label}
                          </span>
                        ) : (
                          <span className="text-zinc-500 text-[11px]">&mdash;</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {isReturned ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle size={10} /> Returned
                          </span>
                        ) : state === 'pending' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                            <Hourglass size={10} /> Pending Approval
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <Clock size={10} /> Active Loan
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {state === 'pending' && (
                            <button
                              onClick={() => handleOpenApproveModal(tx)}
                              className="px-2.5 py-1 rounded-md bg-sky-600 hover:bg-sky-500 text-white text-[11px] font-semibold transition-all flex items-center gap-1"
                              title="Approve Request"
                            >
                              <CheckCircle size={11} />
                              <span>Approve</span>
                            </button>
                          )}
                          {state === 'active' && (
                            <button
                              onClick={() => handleOpenReturnModal(tx)}
                              className="px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition-all flex items-center gap-1"
                              title="Check-in Returned Item"
                            >
                              <CheckCircle size={11} />
                              <span>Check In</span>
                            </button>
                          )}
                          {isAdmin && (
                            <button
                              onClick={() => handleOpenDelete(tx)}
                              className="p-1 rounded text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                              title="Delete Record"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* APPROVE MODAL */}
      <Modal
        isOpen={isApproveOpen}
        onClose={() => setIsApproveOpen(false)}
        title="Approve Borrow Request"
        maxWidth="max-w-md"
      >
        <div className="space-y-3.5">
          <p className="text-xs text-zinc-300">
            Approve{' '}
            <strong className="text-white">{selectedTx?.user_label || 'the borrower'}</strong>'s request for{' '}
            <strong className="text-white">
              {selectedTx?.quantity}x "{selectedTx?.item_label}"
            </strong>
            ? Stock will go down by {selectedTx?.quantity}.
          </p>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setIsApproveOpen(false)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmApprove}
              disabled={formSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold transition-all disabled:opacity-50"
            >
              {formSubmitting ? 'Approving...' : 'Confirm Approval'}
            </button>
          </div>
        </div>
      </Modal>

      {/* CHECK-IN RETURN MODAL */}
      <Modal
        isOpen={isReturnModalOpen}
        onClose={() => setIsReturnModalOpen(false)}
        title="Check-in Returned Equipment"
        maxWidth="max-w-md"
      >
        <div className="space-y-3.5">
          <p className="text-xs text-zinc-300">
            Confirm that{' '}
            <strong className="text-white">{selectedTx?.user_label || 'the borrower'}</strong> has returned{' '}
            <strong className="text-white">
              {selectedTx?.quantity}x "{selectedTx?.item_label}"
            </strong>?
          </p>
          <div className="p-3 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs space-y-1">
            <div>
              <span className="text-zinc-500">Transaction ID:</span> #{selectedTx?.transaction_id}
            </div>
            <div>
              <span className="text-zinc-500">Loan Date:</span>{' '}
              {selectedTx?.borrow_datetime ? new Date(selectedTx.borrow_datetime).toLocaleString() : 'N/A'}
            </div>
            <div>
              <span className="text-zinc-500">Return Date:</span> Recorded automatically as current timestamp
            </div>
          </div>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setIsReturnModalOpen(false)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmReturn}
              disabled={formSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all disabled:opacity-50"
            >
              {formSubmitting ? 'Checking in...' : 'Confirm Return'}
            </button>
          </div>
        </div>
      </Modal>

      {/* DELETE MODAL */}
      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete Record"
        maxWidth="max-w-md"
      >
        <div className="space-y-3.5">
          <p className="text-xs text-zinc-300">
            Permanently delete transaction record <strong className="text-white">#{selectedTx?.transaction_id}</strong>?
          </p>
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-zinc-800">
            <button
              type="button"
              onClick={() => setIsDeleteOpen(false)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeleteSubmit}
              disabled={formSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-all disabled:opacity-50"
            >
              {formSubmitting ? 'Deleting...' : 'Delete'}
            </button>
          </div>
        </div>
      </Modal>

    </div>
  );
}
