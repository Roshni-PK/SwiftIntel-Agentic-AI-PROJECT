import React from 'react';
import { Evidence } from '../types';
import { Mail, KeyRound, UserRound, CreditCard, MessageSquare, FileText, Shield, Clock, ArrowUpRight, Trash2 } from 'lucide-react';

interface EvidenceCardProps { evidence: Evidence; onOpenDetail?: (record: Evidence) => void; onDelete?: (record: Evidence) => void; highlightId?: string; }

const sourceNames: Record<string, string> = {
  email: 'Email', access_log: 'Access log', employee_record: 'Employee record', transaction: 'Transaction',
  internal_message: 'Internal message', meeting_note: 'Meeting note', policy: 'Policy', custom: 'User added evidence'
};

const SourceIcon: React.FC<{ type: string }> = ({ type }) => {
  const props = { size: 16, strokeWidth: 1.8 };
  switch (type) {
    case 'email': return <Mail {...props} />;
    case 'access_log': return <KeyRound {...props} />;
    case 'employee_record': return <UserRound {...props} />;
    case 'transaction': return <CreditCard {...props} />;
    case 'internal_message': return <MessageSquare {...props} />;
    case 'policy': return <Shield {...props} />;
    default: return <FileText {...props} />;
  }
};

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, onOpenDetail, onDelete, highlightId }) => {
  return <article className={`evidence-card ${highlightId === evidence.record_id ? 'highlighted' : ''}`}>
    <div className="evidence-card-heading">
      <span className="evidence-source-icon"><SourceIcon type={evidence.source_type} /></span>
      <div className="evidence-title-group"><span className="evidence-type">{sourceNames[evidence.source_type] || evidence.source_type.replace(/_/g, ' ')}</span><h3>{evidence.title}</h3></div>
      <span className={`evidence-origin ${evidence.source_type === 'custom' ? 'user' : 'preloaded'}`}>{evidence.source_type === 'custom' ? 'User added' : 'Preloaded'}</span>
    </div>
    <p className="evidence-preview">{evidence.content}</p>
    <div className="evidence-card-footer"><span>{evidence.added_at ? <><Clock size={13} />Added {new Date(evidence.added_at).toLocaleDateString()}</> : evidence.timestamp ? <><Clock size={13} />{new Date(evidence.timestamp).toLocaleString()}</> : 'Date not provided'}</span>{evidence.file_name && <span>{evidence.file_name}</span>}{onDelete && evidence.source_type === 'custom' && <button className="evidence-delete" onClick={() => onDelete(evidence)}><Trash2 size={13} />Remove</button>}{onOpenDetail && <button onClick={() => onOpenDetail(evidence)}>View details <ArrowUpRight size={14} /></button>}<details className="evidence-technical"><summary>Technical details</summary><span>Record ID: {evidence.record_id}{evidence.case_id ? ` · Investigation ${evidence.case_id}` : ''}</span></details></div>
  </article>;
};
