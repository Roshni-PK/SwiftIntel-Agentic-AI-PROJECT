import React, { useEffect, useState } from 'react';
import { CaseDetail, Evidence } from '../types';
import { api } from '../services/api';
import { EvidenceCard } from '../components/EvidenceCard';
import { AlertCircle, Database, Search, X, RefreshCw, Clock, Plus } from 'lucide-react';

const sourceName = (type: string) => type === 'custom' ? 'User Added' : type.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

export const EvidenceVaultPage: React.FC<{ currentCaseId?: string | null }> = ({ currentCaseId }) => {
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [sourceTypes, setSourceTypes] = useState<Record<string, number>>({});
  const [selectedType, setSelectedType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<Evidence | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const [cases, setCases] = useState<CaseDetail[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Evidence | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadEvidence = async (query = searchQuery, type = selectedType) => {
    setIsLoading(true); setError('');
    try {
      const [records, types] = await Promise.all([api.searchEvidence(query.trim() || undefined, type === 'all' ? undefined : type), api.getEvidenceSourceTypes()]);
      setEvidenceList(records); setSourceTypes(types);
    } catch (err) { setError(err instanceof Error ? err.message : 'Evidence records could not be loaded.'); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { void loadEvidence(searchQuery, selectedType); }, [selectedType]);
  useEffect(() => { api.getCases().then(setCases).catch(() => setError('Investigations could not be loaded.')); }, []);

  const submitUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    const latestCase = [...cases].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))[0];
    const caseId = cases.find(item => item.id === currentCaseId)?.id || latestCase?.id;
    if (!caseId) { setError('Create an investigation before adding evidence.'); return; }
    if (!uploadFile) { setError('Choose an evidence file to upload.'); return; }
    setUploading(true); setError(''); setSuccess('');
    try {
      const uploaded = await api.addCaseEvidence(caseId, uploadName, uploadDescription, uploadFile);
      setSuccess(`“${uploaded.title}” was added to the evidence library.`);
      setShowUpload(false); setUploadName(''); setUploadDescription(''); setUploadFile(null);
      setSearchQuery(''); setSelectedType('all'); await loadEvidence('', 'all');
    } catch (err) { setError(err instanceof Error ? err.message : 'Evidence could not be uploaded. Please try again.'); }
    finally { setUploading(false); }
  };

  const removeEvidence = async (record: Evidence) => {
    if (record.source_type !== 'custom' || !record.case_id) return;
    setDeleteTarget(record);
  };

  const confirmDelete = async () => {
    if (!deleteTarget?.case_id) return;
    setDeleting(true); setError('');
    try {
      await api.deleteCaseEvidence(deleteTarget.case_id, deleteTarget.record_id);
      setEvidenceList(items => items.filter(item => item.record_id !== deleteTarget.record_id));
      setDeleteTarget(null); setSuccess('User-added evidence was deleted.');
      await loadEvidence(searchQuery, selectedType);
    } catch { setError('This evidence could not be deleted. Please try again.'); }
    finally { setDeleting(false); }
  };

  const openRecord = async (record: Evidence) => {
    setSelectedRecord(record); setDetailLoading(true);
    try { setSelectedRecord(await api.getEvidenceDetail(record.record_id)); }
    catch (err) { setError(err instanceof Error ? err.message : 'The full record could not be loaded.'); }
    finally { setDetailLoading(false); }
  };

  const totalCount = Object.values(sourceTypes).reduce((sum, count) => sum + count, 0);

  return <section className="page-container evidence-page">
    <div className="page-heading-row"><div><p className="eyebrow">INVESTIGATION RECORDS</p><h1>Evidence library</h1><p className="page-description">Search preloaded records and user-added evidence attached to investigations.</p></div><button className="button-primary" onClick={() => { setError(''); setSuccess(''); setShowUpload(true); }}><Plus size={16} />Add evidence</button></div>
    <form className="evidence-search panel" onSubmit={(event) => { event.preventDefault(); void loadEvidence(); }}>
      <label htmlFor="evidence-search-input">Search evidence</label>
      <div className="search-control"><Search size={17} /><input id="evidence-search-input" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search by evidence name, topic, or text" /><button type="submit" className="button-primary" disabled={isLoading}>{isLoading ? 'Searching…' : 'Search'}</button>{searchQuery && <button className="search-clear" type="button" aria-label="Clear search" onClick={() => { setSearchQuery(''); void loadEvidence('', selectedType); }}><X size={16} /></button>}</div>
      <small>Search preloaded records and user-added evidence. Results may include fictional general records.</small>
    </form>
    {error && <div className="notice notice-error"><AlertCircle size={18} /><p>{error}</p></div>}
    {success && <div className="notice notice-success"><Database size={17} /><p>{success}</p></div>}
    <div className="evidence-filter-row"><div><strong>{isLoading ? 'Searching…' : `${evidenceList.length} records`}</strong><span> · {totalCount} available in library</span></div><div className="evidence-filters" aria-label="Filter by record type"><button className={selectedType === 'all' ? 'selected' : ''} onClick={() => setSelectedType('all')}>All types <span>{totalCount}</span></button>{Object.entries(sourceTypes).map(([type, count]) => <button className={selectedType === type ? 'selected' : ''} key={type} onClick={() => setSelectedType(type)}>{sourceName(type)} <span>{count}</span></button>)}</div></div>
    {isLoading ? <div className="panel loading-state"><RefreshCw size={18} className="spin" />Loading evidence…</div> : evidenceList.length === 0 ? <div className="panel evidence-empty"><Database size={27} /><strong>No matching evidence</strong><span>Try a different search or clear the selected source filter.</span></div> : <div className="evidence-list">{evidenceList.map((record) => <EvidenceCard key={record.record_id} evidence={record} onOpenDetail={openRecord} onDelete={removeEvidence} />)}</div>}

    {showUpload && <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget && !uploading) setShowUpload(false); }}><form className="panel evidence-modal upload-form" role="dialog" aria-modal="true" aria-labelledby="library-upload-heading" onSubmit={submitUpload}>
      <header><div><p className="eyebrow">USER-ADDED EVIDENCE</p><h2 id="library-upload-heading">Add evidence</h2></div><button type="button" className="icon-button" onClick={() => setShowUpload(false)} aria-label="Close upload form"><X size={18} /></button></header>
      <div className="evidence-modal-content upload-fields"><p>Custom evidence belongs to an investigation. It becomes available to that investigation's evidence search.</p>
        <label>Evidence / log name<input required maxLength={255} value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Server Access Log - September 28" /></label>
        <label>Description (optional)<textarea rows={3} value={uploadDescription} onChange={e => setUploadDescription(e.target.value)} placeholder="Where this evidence came from" /></label>
        <label>Evidence file<input key={uploadFile?.name || 'no-file'} required type="file" accept=".txt,.csv,.json,.log,.md,text/plain,text/csv,application/json" onChange={e => setUploadFile(e.target.files?.[0] || null)} /></label>
        {uploadFile && <div className="selected-upload"><span><strong>{uploadFile.name}</strong><small>{uploadFile.name.split('.').pop()?.toUpperCase()} · {(uploadFile.size / 1024).toFixed(1)} KB</small></span><button type="button" className="button-secondary" onClick={() => setUploadFile(null)}>Remove</button></div>}
        <p className="upload-format-note">Evidence goes to your active investigation, or your most recently updated one if none is open. Supported formats: TXT, CSV, JSON, LOG, MD · Maximum 5 MB · PDF is not supported.</p>
      </div><footer><button type="button" className="button-secondary" disabled={uploading} onClick={() => setShowUpload(false)}>Cancel</button><button className="button-primary" disabled={uploading}>{uploading ? 'Uploading…' : 'Upload evidence'}</button></footer>
    </form></div>}
    {deleteTarget && <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget && !deleting) setDeleteTarget(null); }}><section className="panel delete-confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-evidence-heading"><h2 id="delete-evidence-heading">Delete this evidence?</h2><p>“{deleteTarget.title}” will be removed from this investigation and evidence retrieval.</p><footer><button className="button-secondary" disabled={deleting} onClick={() => setDeleteTarget(null)}>Cancel</button><button className="button-danger" disabled={deleting} onClick={confirmDelete}>{deleting ? 'Deleting…' : 'Delete Evidence'}</button></footer></section></div>}

    {selectedRecord && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedRecord(null); }}><section className="evidence-modal panel" role="dialog" aria-modal="true" aria-labelledby="record-modal-title"><header><div className="evidence-source-icon"><Database size={17} /></div><div><h2 id="record-modal-title">{selectedRecord.title}</h2></div><button className="icon-button" onClick={() => setSelectedRecord(null)} aria-label="Close details"><X size={18} /></button></header>{detailLoading ? <div className="loading-state"><RefreshCw size={17} className="spin" />Loading full record…</div> : <div className="evidence-modal-content"><div className="record-metadata"><span>Origin<strong>{selectedRecord.source_type === 'custom' ? 'User added' : 'Preloaded'}</strong></span><span>Type<strong>{sourceName(selectedRecord.source_type)}</strong></span><span>Date added<strong>{selectedRecord.added_at ? new Date(selectedRecord.added_at).toLocaleString() : selectedRecord.timestamp ? <><Clock size={13} /> {new Date(selectedRecord.timestamp).toLocaleString()}</> : 'Not provided'}</strong></span><span>Investigation<strong>{selectedRecord.case_id || 'Shared record'}</strong></span>{selectedRecord.file_name && <span>File name<strong>{selectedRecord.file_name}</strong></span>}</div><section><h3>Relevant information</h3><p className="record-content">{selectedRecord.content}</p></section><details className="evidence-technical"><summary>Technical details</summary><p>Record ID: {selectedRecord.record_id}</p>{selectedRecord.metadata && Object.keys(selectedRecord.metadata).length > 0 && <pre>{JSON.stringify(selectedRecord.metadata, null, 2)}</pre>}</details></div>}<footer><button className="button-secondary" onClick={() => setSelectedRecord(null)}>Close</button></footer></section></div>}
  </section>;
};
