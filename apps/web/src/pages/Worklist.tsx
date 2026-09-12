import {FormEvent,useMemo,useRef,useState} from 'react'
import {useQuery} from '@tanstack/react-query'
import {CheckCircle2,ListChecks,Search,UploadCloud} from 'lucide-react'
import {Link} from 'react-router-dom'
import {api,DicomElement,Endpoint,Result,WorklistEntry} from '../api/client'
import {TargetSelector} from '../components/dicom/TargetSelector'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {Column,DataTable} from '../components/ui/DataTable'
import {CollapsiblePanel,CopyButton} from '../components/ui/Disclosure'
import {AlertBox} from '../components/ui/Feedback'
import {DateInput,FormField,Select,TextInput} from '../components/ui/Form'
import {Modal} from '../components/ui/Overlay'
import {StatusBadge} from '../components/ui/Status'
import {SaveTargetButton} from '../components/SaveTargetButton'
import {loadLocalSettings} from '../settings/localSettings'
import {localDateString} from '../utils/dates'

function DicomTree({items,depth=0}:{items:DicomElement[];depth?:number}){
 return <div className="dicom-tree">{items.map((item,index)=><div className="dicom-element" style={{paddingLeft:depth*15}} key={`${item.tag}-${index}`}><span>{item.tag}</span><b>{item.name}</b>{Array.isArray(item.value)?item.value.map((children,i)=><DicomTree key={i} items={children} depth={depth+1}/>):<code>{item.value||'—'}</code>}</div>)}</div>
}

export function Worklist(){
 const {data:targets=[]}=useQuery({queryKey:['targets'],queryFn:api.targets})
 const [endpoint,setEndpoint]=useState<Endpoint>(()=>({host:'',port:104,called_ae:'',calling_ae:loadLocalSettings().callingAe}))
 const [filters,setFilters]=useState(()=>({date:localDateString(),modality:'',station_ae:'',patient_id:'',accession_number:'',patient_name:''}))
 const [result,setResult]=useState<Result>()
 const [error,setError]=useState<string>()
 const [pending,setPending]=useState(false)
 const [selected,setSelected]=useState<WorklistEntry>()
 const generation=useRef(0)
 const pendingRef=useRef(false)

 const invalidate=()=>{generation.current++;setResult(undefined);setError(undefined);setSelected(undefined)}
 const changeEndpoint=(value:Endpoint)=>{invalidate();setEndpoint(value)}
 const changeFilters=(value:typeof filters)=>{invalidate();setFilters(value)}
 const run=(broad:boolean,nextFilters=filters)=>{
  if(pendingRef.current)return
  invalidate()
  const requestGeneration=generation.current
  const payload={...endpoint,broad,filters:nextFilters}
  pendingRef.current=true
  setPending(true)
  void api.mwl(payload)
   .then(data=>{if(requestGeneration===generation.current)setResult(data)})
   .catch(cause=>{if(requestGeneration===generation.current)setError(cause instanceof Error?cause.message:'Worklist-Abfrage fehlgeschlagen.')})
   .finally(()=>{pendingRef.current=false;setPending(false)})
 }
 const submit=(event:FormEvent)=>{event.preventDefault();run(false)}
 const retry=(key:'station_ae'|'modality')=>{const next={...filters,[key]:''};changeFilters(next);run(false,next)}
 const technical=useMemo(()=>JSON.stringify({association:{called_ae:endpoint.called_ae,calling_ae:endpoint.calling_ae,target:`${endpoint.host}:${endpoint.port}`},query:{broad:result?.broad??false,filters:result?.active_filters},response:{status:result?.status,count:result?.count,duration_ms:result?.duration_ms}},null,2),[endpoint,result])
 const columns:Column<WorklistEntry>[]= [
  {key:'patient',header:'Patientenname',render:row=>row.patient_name||'—'},
  {key:'id',header:'Patient ID',className:'mono',render:row=>row.patient_id},
  {key:'birth',header:'Geburtsdatum',render:row=>row.birth_date||'—'},
  {key:'modality',header:'Modalität',render:row=>row.modality},
  {key:'time',header:'Geplante Zeit',className:'mono',render:row=>`${row.start_date} ${row.start_time}`},
  {key:'accession',header:'Accession',className:'mono',render:row=>row.accession_number},
 ]

 return <>
  <PageHeader title="Worklist" subtitle="DICOM Worklist testen und Ergebnisse analysieren" actions={<Link to="/pacs-store"><Button variant="outline" icon={<UploadCloud size={16}/>}>PACS Store testen</Button></Link>}/>
  <div className="worklist-layout">
   <SectionCard title="Worklist Test" subtitle="Abfrageparameter konfigurieren und Worklist abrufen">
    <form onSubmit={submit}>
     <TargetSelector value={endpoint} onChange={changeEndpoint} targets={targets} service="mwl"/>
     <div className="form-divider"/>
     <div className="query-fields">
      <FormField label="Datum" htmlFor="filter-date"><DateInput id="filter-date" value={filters.date} onChange={event=>changeFilters({...filters,date:event.target.value})}/></FormField>
      <FormField label="Modalität" htmlFor="filter-modality"><Select id="filter-modality" value={filters.modality} onChange={event=>changeFilters({...filters,modality:event.target.value})}><option value="">Beliebig</option>{['CT','MR','US','CR','DX','OT'].map(item=><option key={item}>{item}</option>)}</Select></FormField>
      <FormField label="Station AE" htmlFor="filter-station"><TextInput id="filter-station" className="mono" value={filters.station_ae} placeholder="leer für beliebig" onChange={event=>changeFilters({...filters,station_ae:event.target.value.toUpperCase()})}/></FormField>
      <FormField label="Patient ID" htmlFor="filter-patient-id"><TextInput id="filter-patient-id" className="mono" value={filters.patient_id} placeholder="leer für beliebig" onChange={event=>changeFilters({...filters,patient_id:event.target.value})}/></FormField>
      <FormField label="Accession Number" htmlFor="filter-accession"><TextInput id="filter-accession" className="mono" value={filters.accession_number} placeholder="leer für beliebig" onChange={event=>changeFilters({...filters,accession_number:event.target.value})}/></FormField>
      <FormField label="Patientenname" htmlFor="filter-name"><TextInput id="filter-name" value={filters.patient_name} placeholder="leer für beliebig" onChange={event=>changeFilters({...filters,patient_name:event.target.value})}/></FormField>
     </div>
     <div className="form-actions"><Button type="submit" loading={pending} icon={<ListChecks size={17}/>}>Worklist abfragen</Button><Button type="button" variant="outline" disabled={pending} icon={<Search size={17}/>} onClick={()=>run(true)}>Broad Query</Button></div>
    </form>
   </SectionCard>
   <div className="worklist-result-stack">
    <SectionCard title="Ergebnis" action={result&&<StatusBadge tone={result.success?'success':'error'}>{result.success?'Erfolgreich':'Fehler'}</StatusBadge>}>
     {!result&&!error&&!pending&&<div className="empty-state"><ListChecks size={32}/><strong>Noch keine Abfrage ausgeführt</strong><span>Konfiguration prüfen und Worklist abfragen.</span></div>}
     {pending&&<div className="loading-state"><span className="loader"/>Association wird aufgebaut und C-FIND ausgeführt …</div>}
     {error&&<AlertBox tone="error" title="Request fehlgeschlagen">{error}</AlertBox>}
     {result&&<>
      {result.success?<div className="result-checks">{(result.steps??[]).map(step=><span key={step}><CheckCircle2 size={16}/>{step}</span>)}<span><CheckCircle2 size={16}/>Antwortzeit: {result.duration_ms} ms</span><span><CheckCircle2 size={16}/>{result.count??0} Worklist-Einträge gefunden</span></div>:<AlertBox tone="error" title={result.message??'DICOM-Test fehlgeschlagen'}><span className="mono">{result.code??result.status}</span></AlertBox>}
      {result.success&&result.count===0&&<div className="diagnosis-box"><h3>Keine Worklist-Einträge gefunden</h3><p>Die DICOM-Verbindung funktioniert. Mindestens ein aktiver Filter liefert keine Treffer.</p><div className="form-actions">{filters.station_ae&&<Button variant="outline" onClick={()=>retry('station_ae')}>Ohne Station AE testen</Button>}{filters.modality&&<Button variant="outline" onClick={()=>retry('modality')}>Ohne Modalität testen</Button>}<Button variant="ghost" onClick={()=>run(true)}>Broad Query</Button></div></div>}
      <div className="form-actions"><SaveTargetButton endpoint={endpoint} service="mwl"/></div>
     </>}
    </SectionCard>
    {result?.entries&&result.entries.length>0&&<SectionCard title={`Worklist Ergebnisse (${result.entries.length})`}><DataTable columns={columns} rows={result.entries} getKey={(row,index)=>`${row.patient_id}-${index}`} onRowClick={setSelected}/><CollapsiblePanel title="Technische Details (DICOM)" action={<CopyButton value={technical}/>}><pre className="mono">{technical}</pre></CollapsiblePanel></SectionCard>}
   </div>
  </div>
  <Modal open={Boolean(selected)} title="Worklist Dataset" size="lg" onClose={()=>setSelected(undefined)}>{selected&&<><div className="result-summary result-summary--success"><strong>{selected.patient_name||'Unbekannter Patient'}</strong><div className="mono">{selected.patient_id} · {selected.accession_number}</div></div><DicomTree items={selected.dataset}/></>}</Modal>
 </>
}
