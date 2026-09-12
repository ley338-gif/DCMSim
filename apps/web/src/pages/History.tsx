import {useDeferredValue,useEffect,useState} from 'react'
import {useQuery} from '@tanstack/react-query'
import {ArrowLeft,Download,Search} from 'lucide-react'
import {Link,useNavigate,useParams} from 'react-router-dom'
import {api,HistoryFilters,ModalityCheckResult,Run} from '../api/client'
import {DicomLogViewer} from '../components/dicom/DicomLogViewer'
import {ModalityCheckResultPanel} from '../components/dicom/ModalityCheckResult'
import {TestResultSummary} from '../components/dicom/TestResultSummary'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {Column,DataTable,LoadingState} from '../components/ui/DataTable'
import {CollapsiblePanel} from '../components/ui/Disclosure'
import {AlertBox} from '../components/ui/Feedback'
import {DateInput,FormField,Select,TextInput} from '../components/ui/Form'
import {KeyValueList} from '../components/ui/KeyValueList'
import {StatusBadge} from '../components/ui/Status'
import {localDayAfterIso,localDayStartIso} from '../utils/dates'

const label=(type:string)=>type==='mwl_find'?'Worklist':type==='qr_find'?'PACS-Suche':type==='dicom_store'?'PACS Store':type==='modality_check'?'Modalitätsprüfung':'C-ECHO'
const runTargetName=(run:Run)=>run.test_type==='modality_check'?String(run.result_json.profile_name??'Modalitätsprofil'):run.target_snapshot_json?.name??String(run.result_json.target_name??run.manual_target_json?.host??(run.target_id?`Ziel #${run.target_id}`:'—'))

export function History(){
 const navigate=useNavigate()
 const [type,setType]=useState('')
 const [status,setStatus]=useState('')
 const [search,setSearch]=useState('')
 const [fromDate,setFromDate]=useState('')
 const [toDate,setToDate]=useState('')
 const deferredSearch=useDeferredValue(search)
 const [offset,setOffset]=useState(0)
 const [exporting,setExporting]=useState(false)
 const [exportError,setExportError]=useState('')
 const limit=50
 const invalidRange=Boolean(fromDate&&toDate&&fromDate>toDate)
 const filters:HistoryFilters={test_type:type||undefined,success:status?status==='true':undefined,search:deferredSearch.trim()||undefined,started_from:fromDate?localDayStartIso(fromDate):undefined,started_before:toDate?localDayAfterIso(toDate):undefined,limit,offset}
 useEffect(()=>setOffset(0),[type,status,deferredSearch,fromDate,toDate])
 const query=useQuery({queryKey:['history',filters],queryFn:()=>api.history(filters),enabled:!invalidRange})
 const exportCsv=async()=>{
  setExporting(true)
  setExportError('')
  try{
   const blob=await api.exportHistory({...filters,limit:undefined,offset:undefined})
   const url=URL.createObjectURL(blob)
   const anchor=document.createElement('a')
   anchor.href=url
   anchor.download=`dcmsim-history-${new Date().toISOString().slice(0,10)}.csv`
   anchor.click()
   URL.revokeObjectURL(url)
  }catch(error){setExportError(error instanceof Error?error.message:'CSV-Export fehlgeschlagen.')}finally{setExporting(false)}
 }
 const columns:Column<Run>[]=[
  {key:'time',header:'Zeit',render:r=>new Date(r.started_at).toLocaleString('de-DE')},
  {key:'type',header:'Typ',render:r=>label(r.test_type)},
  {key:'target',header:'Ziel / Profil',className:'mono',render:runTargetName},
  {key:'status',header:'Status',render:r=><StatusBadge tone={r.success?'success':'error'}>{r.success?'Erfolgreich':'Fehler'}</StatusBadge>},
  {key:'duration',header:'Dauer',render:r=>`${r.duration_ms} ms`},
  {key:'result',header:'Ergebnis',render:r=>['mwl_find','qr_find'].includes(r.test_type)?`${r.result_json.count??0} Treffer`:r.status},
  {key:'details',header:'',render:()=> <span className="table-link">Details →</span>},
 ]
 const total=invalidRange?0:query.data?.total??0
 const from=total===0?0:offset+1
 const to=Math.min(offset+limit,total)
 return <>
  <PageHeader title="Test-Historie" subtitle="Durchgeführte DICOM-Tests filtern und technisch nachvollziehen" actions={<Button variant="outline" icon={<Download size={16}/>} loading={exporting} disabled={total===0} onClick={()=>void exportCsv()}>CSV exportieren</Button>}/>
  <SectionCard>
   {exportError&&<AlertBox tone="error">{exportError}</AlertBox>}
   <div className="history-filters">
    <FormField label="Typ" htmlFor="history-type"><Select id="history-type" value={type} onChange={e=>setType(e.target.value)}><option value="">Alle Typen</option><option value="mwl_find">Worklist</option><option value="qr_find">PACS-Suche</option><option value="dicom_store">PACS Store</option><option value="modality_check">Modalitätsprüfung</option><option value="dicom_echo">C-ECHO</option></Select></FormField>
    <FormField label="Status" htmlFor="history-status"><Select id="history-status" value={status} onChange={e=>setStatus(e.target.value)}><option value="">Alle Status</option><option value="true">Erfolgreich</option><option value="false">Fehler</option></Select></FormField>
    <FormField label="Suche" htmlFor="history-search" className="span-two"><div className="input-with-icon"><Search size={16}/><TextInput id="history-search" value={search} placeholder="Host, Profil, AE Title oder Status" onChange={e=>setSearch(e.target.value)}/></div></FormField>
    <FormField label="Von" htmlFor="history-from"><DateInput id="history-from" value={fromDate} max={toDate||undefined} onChange={e=>setFromDate(e.target.value)}/></FormField>
    <FormField label="Bis" htmlFor="history-to"><DateInput id="history-to" value={toDate} min={fromDate||undefined} onChange={e=>setToDate(e.target.value)}/></FormField>
   </div>
   {invalidRange?<AlertBox tone="warning">Das Bis-Datum muss am oder nach dem Von-Datum liegen.</AlertBox>:query.isLoading?<LoadingState/>:query.isError?<AlertBox tone="error">Die Testhistorie konnte nicht geladen werden.</AlertBox>:<>
    <DataTable columns={columns} rows={query.data?.items??[]} getKey={row=>row.id} onRowClick={row=>navigate(`/history/${row.id}`)} empty="Keine Tests für diese Filter gefunden."/>
    <div className="history-pagination"><span>{from}–{to} von {total} Tests</span><div><Button variant="outline" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-limit))}>Zurück</Button><Button variant="outline" disabled={offset+limit>=total} onClick={()=>setOffset(offset+limit)}>Weiter</Button></div></div>
   </>}
  </SectionCard>
 </>
}

export function HistoryDetail(){
 const {id=''}=useParams()
 const query=useQuery({queryKey:['run',id],queryFn:()=>api.run(id)})
 if(query.isLoading)return <LoadingState/>
 if(!query.data)return <SectionCard><p>Historieneintrag nicht gefunden.</p></SectionCard>
 const run=query.data
 const endpoint=run.target_snapshot_json??run.manual_target_json
 const header=<PageHeader title={`${label(run.test_type)} · Test #${run.id}`} subtitle={new Date(run.started_at).toLocaleString('de-DE')} breadcrumbs={['Test-Historie',`Test #${run.id}`]} actions={<Link to="/history"><Button variant="outline" icon={<ArrowLeft size={16}/>}>Zurück</Button></Link>}/>
 if(run.test_type==='modality_check'){
  const result={...(run.result_json as ModalityCheckResult),run_id:run.id}
  return <>{header}<SectionCard title={result.profile_name}><ModalityCheckResultPanel result={result} showHistoryLink={false}/></SectionCard></>
 }
 return <>{header}<div className="dashboard-grid"><SectionCard title="Testergebnis"><TestResultSummary result={run.result_json}/></SectionCard><SectionCard title="Testparameter"><KeyValueList items={[{label:'Testtyp',value:label(run.test_type)},{label:'Ziel',value:runTargetName(run)},{label:'Host',value:endpoint?.host??'Für ältere Tests nicht gespeichert',mono:true},{label:'Port',value:endpoint?.port,mono:true},{label:'Calling AE',value:endpoint?.calling_ae,mono:true},{label:'Called AE',value:endpoint?.called_ae,mono:true},{label:'Dauer',value:`${run.duration_ms} ms`}]} /></SectionCard></div><SectionCard title="Technisches Log"><DicomLogViewer result={run.result_json} context={{target:endpoint?`${endpoint.host}:${endpoint.port}`:undefined,calling:endpoint?.calling_ae,called:endpoint?.called_ae}}/><CollapsiblePanel title="Gespeicherte Request-/Response-Daten"><pre className="mono">{JSON.stringify(run.result_json,null,2)}</pre></CollapsiblePanel></SectionCard></>
}
