import React, { useState, useEffect } from 'react';
import api from '../../api/client';
import { 
  ClipboardList, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  Hourglass, 
  MapPin, 
  CheckCircle, 
  Package
} from 'lucide-react';

export default function MyBorrowHistoryView({ onNavigateToCatalog }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  const [errorMsg, setErrorMsg] = useState('');
  const [locations, setLocations] = useState({});

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const [res, invRes] = await Promise.all([
        api.get('/transactions/mine/'),
        api.get('/inventory/').catch(() => ({ data: [] })),
      ]);
      setTransactions(res.data || []);
      const map = {};
      (invRes.data || []).forEach((i) => { map[i.item_id] = i.location; });
      setLocations(map);
    } catch (err) {
      console.error(err);
      setErrorMsg('Failed to load your borrow history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  // pending = waiting for staff approval, active = approved and still with you, returned = back
  const pendingRequests = transactions.filter((t) => !t.return_datetime && !t.approver);
  const activeBorrows = transactions.filter((t) => !t.return_datetime && t.approver);
  const returnedBorrows = transactions.filter((t) => Boolean(t.return_datetime));

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <ClipboardList className="text-orange-500" size={20} />
            My Active Loans & Custody History
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Your requests, equipment currently with you, and past returns.
          </p>
        </div>
        <button
          onClick={onNavigateToCatalog}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-orange-600 hover:bg-orange-500 text-white text-xs font-semibold shadow-sm shadow-orange-600/30 transition-all self-start sm:self-auto"
        >
          <Package size={15} />
          <span>Borrow More Apparatus</span>
        </button>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle size={15} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* SECTION 0: PENDING REQUESTS */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Hourglass size={15} className="text-sky-400" />
          <h3 className="text-xs font-semibold text-white tracking-wide uppercase">
            Waiting for Staff Approval ({pendingRequests.length})
          </h3>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-zinc-500 bg-[#12141c] rounded-xl border border-zinc-800">
            Loading requests...
          </div>
        ) : pendingRequests.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-500 bg-[#12141c] rounded-xl border border-zinc-800">
            No pending requests.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {pendingRequests.map((tx) => (
              <div
                key={tx.transaction_id}
                className="p-4 rounded-xl bg-[#12141c] border border-sky-500/30"
              >
                <div className="flex items-start justify-between">
                  <span className="font-mono text-xs text-orange-400 font-semibold">
                    Request #{tx.transaction_id}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    <Hourglass size={10} /> Pending Approval
                  </span>
                </div>
                <h4 className="text-xs font-bold text-white mt-1.5">
                  {tx.item_label || `Equipment #${tx.item_name}`}
                </h4>
                <div className="mt-2.5 space-y-1 text-xs text-zinc-400">
                  <div>
                    Quantity: <strong className="text-zinc-200">{tx.quantity} unit(s)</strong>
                  </div>
                  <div>
                    Requested On:{' '}
                    <strong className="text-zinc-200">
                      {tx.borrow_datetime ? new Date(tx.borrow_datetime).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'N/A'}
                    </strong>
                  </div>
                </div>
                <p className="mt-3 pt-2.5 border-t border-zinc-800 text-[11px] text-zinc-500">
                  Staff will approve this before you can pick it up.
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 1: ACTIVE BORROWS */}
      <div className="pt-2">
        <div className="flex items-center gap-2 mb-3">
          <Clock size={15} className="text-amber-400" />
          <h3 className="text-xs font-semibold text-white tracking-wide uppercase">
            Currently In Your Possession ({activeBorrows.length})
          </h3>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-zinc-500 bg-[#12141c] rounded-xl border border-zinc-800">
            Loading active loans...
          </div>
        ) : activeBorrows.length === 0 ? (
          <div className="py-8 text-center text-xs text-zinc-500 bg-[#12141c] rounded-xl border border-zinc-800">
            No active borrowed equipment in your possession.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {activeBorrows.map((tx) => (
              <div
                key={tx.transaction_id}
                className="p-4 rounded-xl bg-[#12141c] border border-amber-500/30 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <span className="font-mono text-xs text-orange-400 font-semibold">
                      Transaction #{tx.transaction_id}
                    </span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                      <Clock size={10} /> In Custody
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white mt-1.5">
                    {tx.item_label || `Equipment #${tx.item_name}`}
                  </h4>

                  <div className="mt-2.5 space-y-1 text-xs text-zinc-400">
                    <div>
                      Quantity: <strong className="text-zinc-200">{tx.quantity} unit(s)</strong>
                    </div>
                    <div>
                      Borrowed On:{' '}
                      <strong className="text-zinc-200">
                        {tx.borrow_datetime ? new Date(tx.borrow_datetime).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'N/A'}
                      </strong>
                    </div>
                    {locations[tx.item_name] && (
                      <div className="flex items-center gap-1">
                        <MapPin size={11} className="text-zinc-500" />
                        <span>Return location: {locations[tx.item_name]}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-2.5 border-t border-zinc-800 flex items-center justify-between gap-2">
                  <span className="text-[11px] text-zinc-500">
                    Return to custodian for check-in
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 2: RETURNED HISTORY */}
      <div className="pt-2">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle size={15} className="text-emerald-400" />
          <h3 className="text-xs font-semibold text-white tracking-wide uppercase">
            Returned Equipment History ({returnedBorrows.length})
          </h3>
        </div>

        <div className="rounded-2xl bg-[#12141c] border border-zinc-800 overflow-hidden">
          {returnedBorrows.length === 0 ? (
            <div className="py-8 text-center text-xs text-zinc-500">
              No return records yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-[10px] uppercase tracking-wider text-zinc-400 bg-zinc-900/60 border-b border-zinc-800">
                  <tr>
                    <th className="px-4 py-3">Tx ID</th>
                    <th className="px-4 py-3">Apparatus</th>
                    <th className="px-4 py-3">Qty</th>
                    <th className="px-4 py-3">Date Borrowed</th>
                    <th className="px-4 py-3">Date Returned</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800/50">
                  {returnedBorrows.map((tx) => (
                    <tr key={tx.transaction_id} className="hover:bg-zinc-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-zinc-400">
                        #{tx.transaction_id}
                      </td>
                      <td className="px-4 py-3 font-medium text-white">
                        {tx.item_label || `Equipment #${tx.item_name}`}
                      </td>
                      <td className="px-4 py-3 text-zinc-300 font-mono">
                        {tx.quantity}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {tx.borrow_datetime ? new Date(tx.borrow_datetime).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-emerald-400">
                        {tx.return_datetime ? new Date(tx.return_datetime).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'N/A'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 size={10} /> Returned
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
