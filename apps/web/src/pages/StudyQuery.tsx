import {FormEvent,useState} from 'react'
import {useMutation,useQuery} from '@tanstack/react-query'
import {Search} from 'lucide-react'
import {api,DicomElement,Endpoint,StudyEntry} from '../api/client'
import {TargetSelector} from '../components/dicom/TargetSelector'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {Column,DataTable} from '../components/ui/DataTable'
import {AlertBox} from '../components/ui/Feedback'
import {DateInput,FormField,Select,TextInput} from '../components/ui/Form'
import {Modal} from '../components/ui/Overlay'
import {StatusBadge} from '../components/ui/Status'
import {loadLocalSettings} from '../settings/localSettings'
import {localDateString} from '../utils/dates'

const blankEndpoint=():Endpoint=>({host:'',port:104,called_ae:'',calling_ae:loadLocalSettings().callingAe})
const blankFilters={patient_name:'',patient_id:'',accession_number:'',study_date:'',modality:''}

function DicomTree({items}:{items:DicomElement[]}){return <div className="dicom-tree">{items.map((item,index)=><div className="dicom-element" key={`${item.tag}-${index}`}><span>{item.tag}</span><b>{item.name}</b><code>{Array.isArray(item.value)?JSON.stringify(item.value):item.value||'—'}</code></div>)}</div>}

export function StudyQuery(){
 const {data:targets=[]}=useQuery({queryKey:['targets'],queryFn:api.targets})
 const [endpoint,setEndpoint]=useState<Endpoint>(blankEndpoint)
 const [filters,setFilters]=useState(()=>({...blankFilters,study_date:localDateString()}))
 const [selected,setSelected]=useState<StudyEntry>()
 const mutation=useMutation({mutationFn:()=>api.studies({
  ...endpoint,
  filters:Object.fromEntries(Object.entries(filters).map(([key,value])=>[key,value||null])),
 })})
 const submit=(event:FormEvent)=>{event.preventDefault();mutation.mutate()}
 const entries=mutation.data?.entries??[]
 const columns:Column<StudyEntry>[]=[
  {key:'patient',header:'Patient',render:row=><strong>{row.patient_name||'—'}</strong>},
  {key:'id',header:'Patient ID',className:'mono',render:row=>row.patient_id||'—'},
  {key:'date',header:'Studien­datum',render:row=>row.study_date||'—'},
  {key:'modality',header:'Modalitäten',render:row=>row.modalities||'—'},
  {key:'accession',header:'Accession',className:'mono',render:row=>row.accession_number||'—'},
  {key:'description',header:'Beschreibung',render:row=>row.study_description||'—'},
  {key:'counts',header:'Serien / Instanzen',render:row=>`${row.series_count} / ${row.instance_count}`},
 ]
 return <>
  <PageHeader title="PACS-Suche" subtitle="Studien per DICOM Study Root C-FIND suchen und Antworten analysieren"/>
  <div className="worklist-layout">
   <SectionCard title="Studienabfrage" subtitle="Mindestens ein Suchkriterium ist erforderlich"><form onSubmit={submit}><TargetSelector value={endpoint} onChange={setEndpoint} targets={targets} service="qr"/><div className="form-divider"/><div className="query-fields"><FormField label="Studien­datum" htmlFor="study-date"><DateInput id="study-date" value={filters.study_date} onChange={event=>setFilters({...filters,study_date:event.target.value})}/></FormField><FormField label="Modalität" htmlFor="study-modality"><Select id="study-modality" value={filters.modality} onChange={event=>setFilters({...filters,modality:event.target.value})}><option value="">Beliebig</option>{['CT','MR','US','CR','DX','XA','MG','NM','PT'].map(item=><option key={item}>{item}</option>)}</Select></FormField><FormField label="Patientenname" htmlFor="study-patient-name"><TextInput id="study-patient-name" value={filters.patient_name} placeholder="z. B. MUSTER*" onChange={event=>setFilters({...filters,patient_name:event.target.value})}/></FormField><FormField label="Patient ID" htmlFor="study-patient-id"><TextInput id="study-patient-id" className="mono" value={filters.patient_id} onChange={event=>setFilters({...filters,patient_id:event.target.value})}/></FormField><FormField label="Accession Number" htmlFor="study-accession" className="span-all"><TextInput id="study-accession" className="mono" value={filters.accession_number} onChange={event=>setFilters({...filters,accession_number:event.target.value})}/></FormField></div><div className="form-actions"><Button type="submit" loading={mutation.isPending} icon={<Search size={17}/>}>Studien suchen</Button></div></form>
   </SectionCard>
   <SectionCard title="Suchergebnis" action={mutation.data&&<StatusBadge tone={mutation.data.success?'success':'error'}>{mutation.data.success?'Erfolgreich':'Fehler'}</StatusBadge>}>
    {!mutation.data&&!mutation.isPending&&<div className="empty-state"><Search size={30}/><strong>Noch keine Studienabfrage</strong><span>Ein Ziel und sichere Suchkriterien auswählen.</span></div>}
    {mutation.isPending&&<div className="loading-state" role="status"><span className="loader"/>Study Root C-FIND wird ausgeführt …</div>}
    {mutation.error&&<AlertBox tone="error">{mutation.error.message}</AlertBox>}
    {mutation.data&&!mutation.data.success&&<AlertBox tone="error" title={mutation.data.message??'Studienabfrage fehlgeschlagen'}><span className="mono">{mutation.data.code??mutation.data.status}</span>{mutation.data.recommendation&&<p>{mutation.data.recommendation}</p>}</AlertBox>}
    {mutation.data?.success&&<><AlertBox tone={entries.length?'success':'info'} title={`${entries.length} Studien gefunden`}>Association und Study Root C-FIND erfolgreich · Status <span className="mono">{mutation.data.status}</span> · {mutation.data.duration_ms} ms</AlertBox><DataTable columns={columns} rows={entries} getKey={(row,index)=>row.study_instance_uid||index} onRowClick={setSelected} empty="Keine Studien für diese Kriterien gefunden."/></>}
   </SectionCard>
  </div>
  <Modal open={Boolean(selected)} title="DICOM-Studienantwort" size="lg" onClose={()=>setSelected(undefined)}>{selected&&<><div className="result-summary result-summary--success"><strong>{selected.study_description||'Studie ohne Beschreibung'}</strong><div className="mono">{selected.study_instance_uid}</div></div><DicomTree items={selected.dataset}/></>}</Modal>
 </>
}
