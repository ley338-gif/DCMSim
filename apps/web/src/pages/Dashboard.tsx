import {useQuery} from '@tanstack/react-query'
import {Activity,ArrowRight,CheckCircle2,Clock3,ListChecks,Network,Search,Server,Target,UploadCloud} from 'lucide-react'
import {Link} from 'react-router-dom'
import {api,Run,Target as DicomTarget} from '../api/client'
import {TargetTestStatus} from '../components/dicom/TargetTestStatus'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {Column,DataTable,LoadingState} from '../components/ui/DataTable'
import {MetricCard} from '../components/ui/MetricCard'
import {StatusBadge,StatusDot} from '../components/ui/Status'

const labels:Record<string,string>={mwl_find:'Worklist',qr_find:'PACS-Suche',dicom_store:'PACS Store',modality_check:'Modalitätsprüfung',dicom_echo:'C-ECHO'}
const typeLabel=(type:string)=>labels[type]??type
const runDetails=(run:Run)=>['mwl_find','qr_find'].includes(run.test_type)?`${run.result_json.count??0} Treffer`:run.test_type==='modality_check'?(run.success?'PASS':'FAIL'):`${run.duration_ms} ms`
const localDayBounds=()=>{const now=new Date();return [new Date(now.getFullYear(),now.getMonth(),now.getDate()).toISOString(),new Date(now.getFullYear(),now.getMonth(),now.getDate()+1).toISOString()] as const}

export function Dashboard(){
 const [dayStart,dayEnd]=localDayBounds()
 const targets=useQuery({queryKey:['targets'],queryFn:api.targets})
 const systems=useQuery({queryKey:['dicom-systems'],queryFn:api.dicomSystems})
 const endpoints=useQuery({queryKey:['dicom-endpoints'],queryFn:api.dicomEndpoints})
 const runs=useQuery({queryKey:['runs'],queryFn:api.runs})
 const summaryQuery=useQuery({queryKey:['dashboard-summary',dayStart,dayEnd],queryFn:()=>api.dashboardSummary(dayStart,dayEnd)})
 const targetStatuses=useQuery({queryKey:['target-statuses'],queryFn:api.targetStatuses,staleTime:0})
 const allTargets=targets.data??[]
 const allRuns=runs.data??[]
 const statusByTarget=new Map((targetStatuses.data??[]).map(status=>[status.target_id,status]))
 const summary=summaryQuery.data
 const success=summary?.today_total?Math.round(summary.today_success/summary.today_total*100):0
 const last=allRuns[0]
 const targetColumns:Column<DicomTarget>[]=[
  {key:'name',header:'Name',render:t=><strong>{t.name}</strong>},
  {key:'host',header:'Host',className:'mono',render:t=>t.host},
  {key:'port',header:'Port',className:'mono',render:t=>t.mwl_port??t.store_port??t.qr_port??'—'},
  {key:'ae',header:'Called AE',className:'mono',render:t=>t.mwl_called_ae??t.store_called_ae??t.qr_called_ae??'—'},
  {key:'services',header:'Dienste',render:t=>[t.mwl_enabled?'MWL':'',t.store_enabled?'Store':'',t.qr_enabled?'PACS-Suche':''].filter(Boolean).join(', ')||'—'},
  {key:'status',header:'Letzter Einzeltest',render:t=><TargetTestStatus status={statusByTarget.get(t.id)}/>},
 ]
 const runColumns:Column<Run>[]=[
  {key:'time',header:'Zeit',render:r=>new Date(r.started_at).toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'})},
  {key:'type',header:'Typ',render:r=>typeLabel(r.test_type)},
  {key:'target',header:'Ziel',className:'mono',render:r=>r.test_type==='modality_check'?String(r.result_json.profile_name??'Modalitätsprofil'):String(r.result_json.target_name??r.manual_target_json?.host??(r.target_id?`Ziel #${r.target_id}`:'—'))},
  {key:'status',header:'Status',render:r=><StatusBadge tone={r.success?'success':'error'}>{r.success?'Erfolgreich':'Fehler'}</StatusBadge>},
  {key:'details',header:'Details',render:runDetails},
 ]
 return <>
  <PageHeader title="Übersicht" subtitle="Systemstatus, letzte Tests und DICOM-Konnektivität auf einen Blick"/>
  <div className="metric-grid"><MetricCard label="DICOM-Systeme" value={systems.data?.length??'—'} caption={`${endpoints.data?.length??0} technische Endpoints`} icon={<Target size={26}/>}/><MetricCard label="Tests heute" value={summary?summary.today_total:'—'} caption={summary?`${summary.today_success} erfolgreich`:'Kennzahl nicht verfügbar'} icon={<Activity size={26}/>} tone="navy"/><MetricCard label="Erfolgsquote" value={summary?`${success} %`:'—'} caption={summary?(summary.today_total?'für heutige Tests':'noch keine Tests'):'Kennzahl nicht verfügbar'} icon={<CheckCircle2 size={27}/>} tone="teal"/><MetricCard label="Letzte Antwortzeit" value={last?`${last.duration_ms} ms`:'—'} caption={last?typeLabel(last.test_type):'noch kein Ergebnis'} icon={<Clock3 size={26}/>} tone="blue"/></div>
  <div className="dashboard-grid"><SectionCard title="Schnelltests" subtitle="Häufig verwendete Tests direkt ausführen"><div className="quick-grid"><div className="quick-action"><span className="quick-action__icon"><ListChecks size={28}/></span><div><h3>Worklist testen</h3><p>DICOM Modality Worklist abfragen und Ergebnisse prüfen.</p><Link to="/worklist"><Button icon={<ArrowRight size={16}/>}>Jetzt testen</Button></Link></div></div><div className="quick-action"><span className="quick-action__icon"><UploadCloud size={28}/></span><div><h3>PACS Store testen</h3><p>DICOM C-STORE mit synthetischem Testobjekt senden.</p><Link to="/pacs-store"><Button variant="outline" icon={<ArrowRight size={16}/>}>PACS Store testen</Button></Link></div></div><div className="quick-action"><span className="quick-action__icon"><Search size={28}/></span><div><h3>PACS-Studien suchen</h3><p>Study Root C-FIND mit sicheren Filtern ausführen.</p><Link to="/pacs-query"><Button variant="outline" icon={<ArrowRight size={16}/>}>Studien suchen</Button></Link></div></div></div></SectionCard><SectionCard title="Systemstatus" subtitle="Lokale Komponenten und Dienste"><div className="system-list"><div className="system-row"><span><Network size={16}/> API Service</span><StatusBadge tone="success">Online</StatusBadge><small>lokal erreichbar</small></div><div className="system-row"><span><ListChecks size={16}/> Worklist SCU</span><StatusBadge tone="success">Bereit</StatusBadge><small>bei Bedarf</small></div><div className="system-row"><span><UploadCloud size={16}/> Store SCU</span><StatusBadge tone="success">Bereit</StatusBadge><small>bei Bedarf</small></div><div className="system-row"><span><Search size={16}/> Query/Retrieve SCU</span><StatusBadge tone="success">Bereit</StatusBadge><small>Study Root C-FIND</small></div><div className="system-row"><span><Server size={16}/> Audit Logging</span><StatusBadge tone="success">Aktiv</StatusBadge><small>SQLite lokal</small></div></div></SectionCard></div>
  <div className="dashboard-grid"><SectionCard title="Legacy-Zielstatus" subtitle="Bestehende manuelle Testziele bleiben kompatibel" action={<Link to="/systems">Systeme verwalten →</Link>}>{targets.isLoading?<LoadingState/>:<DataTable columns={targetColumns} rows={allTargets.slice(0,5)} getKey={row=>row.id} empty="Noch keine Legacy-Ziele konfiguriert."/>}</SectionCard><SectionCard title="Letzte Tests" action={<Link to="/history">Alle anzeigen →</Link>}>{runs.isLoading?<LoadingState/>:<DataTable columns={runColumns} rows={allRuns.slice(0,6)} getKey={row=>row.id} onRowClick={row=>location.assign(`/history/${row.id}`)} empty="Noch keine Tests durchgeführt."/>}</SectionCard></div>
  <div className="bottom-grid"><SectionCard title="Testverteilung"><div className="activity-list"><div className="activity-item"><StatusDot tone="info"/><div><strong>Worklist</strong><small>{summary?.by_type.mwl_find??'—'} Tests</small></div></div><div className="activity-item"><StatusDot tone="success"/><div><strong>PACS Store</strong><small>{summary?.by_type.dicom_store??'—'} Tests</small></div></div><div className="activity-item"><StatusDot tone="info"/><div><strong>PACS-Suche</strong><small>{summary?.by_type.qr_find??'—'} Tests</small></div></div><div className="activity-item"><StatusDot tone="success"/><div><strong>Modalitätsprüfung</strong><small>{summary?.by_type.modality_check??'—'} Tests</small></div></div><div className="activity-item"><StatusDot tone="info"/><div><strong>C-ECHO</strong><small>{summary?.by_type.dicom_echo??'—'} Tests</small></div></div></div></SectionCard><SectionCard title="Konfigurierte Dienste"><div className="activity-list"><div className="activity-item"><StatusDot tone="success"/><div><strong>Worklist-Endpoints</strong><small>{endpoints.data?.filter(t=>t.service==='MWL').length??0} aktiv</small></div></div><div className="activity-item"><StatusDot tone="info"/><div><strong>Store-Endpoints</strong><small>{endpoints.data?.filter(t=>t.service==='STORE').length??0} aktiv</small></div></div><div className="activity-item"><StatusDot tone="info"/><div><strong>Query/Retrieve-Endpoints</strong><small>{endpoints.data?.filter(t=>t.service==='QR').length??0} aktiv</small></div></div></div></SectionCard><SectionCard title="Hinweise"><div className="activity-list">{allRuns.slice(0,3).map(run=><div className="activity-item" key={run.id}><StatusDot tone={run.success?'success':'error'}/><div><strong>{typeLabel(run.test_type)} {run.success?'erfolgreich':'fehlgeschlagen'}</strong><small>{new Date(run.started_at).toLocaleString('de-DE')}</small></div></div>)}{!allRuns.length&&<div className="activity-item"><StatusDot tone="info"/><div><strong>DCMSim ist bereit</strong><small>Ersten Test starten</small></div></div>}</div></SectionCard></div>
 </>
}
