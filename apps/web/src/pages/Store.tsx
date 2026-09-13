import {FormEvent,useMemo,useRef,useState} from 'react'
import {useQuery} from '@tanstack/react-query'
import {Clock3,FileUp,Radio,Send,Trash2} from 'lucide-react'
import {Link} from 'react-router-dom'
import {api,Endpoint,Result} from '../api/client'
import {DicomLogViewer} from '../components/dicom/DicomLogViewer'
import {DicomMetadataPanel} from '../components/dicom/DicomMetadataPanel'
import {TargetSelector} from '../components/dicom/TargetSelector'
import {TestResultSummary} from '../components/dicom/TestResultSummary'
import {TransferProgress} from '../components/dicom/TransferProgress'
import {PageHeader} from '../components/layout/PageHeader'
import {SaveTargetButton} from '../components/SaveTargetButton'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {AlertBox} from '../components/ui/Feedback'
import {Checkbox,FormField,Select} from '../components/ui/Form'
import {loadLocalSettings} from '../settings/localSettings'

const sopClasses=[['secondary_capture','Secondary Capture'],['ct','CT Image Storage'],['mr','MR Image Storage'],['ultrasound','Ultrasound Image Storage'],['cr','Computed Radiography'],['dx','Digital X-Ray']]

export function Store(){
 const {data:targets=[]}=useQuery({queryKey:['targets'],queryFn:api.targets})
 const {data:endpoints=[]}=useQuery({queryKey:['dicom-endpoints'],queryFn:api.dicomEndpoints})
 const [endpoint,setEndpoint]=useState<Endpoint>(()=>({host:'',port:104,called_ae:'',calling_ae:loadLocalSettings().callingAe}))
 const [sop,setSop]=useState('secondary_capture')
 const [syntax,setSyntax]=useState('explicit_vr_little_endian')
 const [mode,setMode]=useState<'generated'|'upload'>('generated')
 const [file,setFile]=useState<File>()
 const [uploadInfo,setUploadInfo]=useState<Record<string,string>>()
 const [uploadError,setUploadError]=useState<string>()
 const [analysisPending,setAnalysisPending]=useState(false)
 const [result,setResult]=useState<Result>()
 const [storeError,setStoreError]=useState<string>()
 const [storePending,setStorePending]=useState(false)
 const [echoResult,setEchoResult]=useState<Result>()
 const [echoError,setEchoError]=useState<string>()
 const [echoPending,setEchoPending]=useState(false)
 const storeGeneration=useRef(0)
 const echoGeneration=useRef(0)
 const analysisGeneration=useRef(0)
 const operationPending=useRef(false)
 const fileInput=useRef<HTMLInputElement>(null)

 const invalidateStore=()=>{storeGeneration.current++;setResult(undefined);setStoreError(undefined)}
 const changeEndpoint=(value:Endpoint)=>{invalidateStore();echoGeneration.current++;setEchoResult(undefined);setEchoError(undefined);setEndpoint(value)}
 const changeMode=(value:'generated'|'upload')=>{if(value===mode)return;invalidateStore();analysisGeneration.current++;setFile(undefined);setUploadInfo(undefined);setUploadError(undefined);setAnalysisPending(false);setMode(value)}
 const changeSop=(value:string)=>{invalidateStore();setSop(value)}
 const changeSyntax=(value:string)=>{invalidateStore();setSyntax(value)}

 const chooseFile=(next?:File)=>{
  invalidateStore()
  const generation=++analysisGeneration.current
  setFile(next)
  setUploadInfo(undefined)
  setUploadError(undefined)
  setAnalysisPending(Boolean(next))
  if(!next){if(fileInput.current)fileInput.current.value='';return}
  const data=new FormData()
  data.set('file',next)
  void api.analyzeUpload(data)
   .then(info=>{if(generation===analysisGeneration.current)setUploadInfo(info)})
   .catch(cause=>{if(generation===analysisGeneration.current)setUploadError(cause instanceof Error?cause.message:'DICOM-Datei konnte nicht analysiert werden.')})
   .finally(()=>{if(generation===analysisGeneration.current)setAnalysisPending(false)})
 }

 const testConnection=()=>{
  if(operationPending.current)return
  const generation=++echoGeneration.current
  const target={...endpoint}
  setEchoResult(undefined)
  setEchoError(undefined)
  operationPending.current=true
  setEchoPending(true)
  void api.echo(target)
   .then(data=>{if(generation===echoGeneration.current)setEchoResult(data)})
   .catch(cause=>{if(generation===echoGeneration.current)setEchoError(cause instanceof Error?cause.message:'C-ECHO fehlgeschlagen.')})
   .finally(()=>{operationPending.current=false;setEchoPending(false)})
 }

 const submit=(event:FormEvent)=>{
  event.preventDefault()
  if(operationPending.current)return
  invalidateStore()
  if(mode==='upload'&&!file){setStoreError('Bitte eine DICOM-Datei auswählen.');return}
  if(mode==='upload'&&(analysisPending||uploadError)){setStoreError('Bitte die Dateianalyse abschließen oder eine gültige DICOM-Datei auswählen.');return}
  const generation=storeGeneration.current
  const target={...endpoint}
  operationPending.current=true
  setStorePending(true)
  const request=mode==='generated'
   ?api.store({...target,sop_class:sop,transfer_syntax:syntax})
   :(()=>{const data=new FormData();data.set('file',file!);Object.entries(target).forEach(([key,value])=>{if(value!=null)data.set(key,String(value))});return api.storeUpload(data)})()
  void request
   .then(data=>{if(generation===storeGeneration.current)setResult(data)})
   .catch(cause=>{if(generation===storeGeneration.current)setStoreError(cause instanceof Error?cause.message:'C-STORE fehlgeschlagen.')})
   .finally(()=>{operationPending.current=false;setStorePending(false)})
 }

 const context=useMemo(()=>({target:`${endpoint.host}:${endpoint.port}`,calling:endpoint.calling_ae,called:endpoint.called_ae}),[endpoint])
 return <>
  <PageHeader title="PACS Store" subtitle="DICOM C-STORE mit Testdaten senden und die Antwort des Zielsystems analysieren." breadcrumbs={['PACS Store','Neues Senden']} actions={<Link to="/history"><Button variant="outline" icon={<Clock3 size={16}/>}>Test-Historie</Button></Link>}/>
  <form className="store-layout" onSubmit={submit}>
   <div>
    <SectionCard title="Zielsystem">
     <TargetSelector value={endpoint} onChange={changeEndpoint} targets={targets} endpoints={endpoints} service="store" compact/>
     <div className="form-actions"><Button type="button" variant="outline" loading={echoPending} disabled={storePending} icon={<Radio size={16}/>} onClick={testConnection}>Verbindung testen</Button></div>
     {echoError&&<AlertBox tone="error" title="C-ECHO fehlgeschlagen">{echoError}</AlertBox>}
     {echoResult&&<AlertBox tone={echoResult.success?'success':'error'} title={echoResult.success?'C-ECHO erfolgreich':'C-ECHO fehlgeschlagen'}>{echoResult.status??echoResult.code??'—'} · {echoResult.duration_ms} ms{echoResult.message&&` · ${echoResult.message}`}</AlertBox>}
    </SectionCard>
    <SectionCard title="Testdaten">
     <div className="segmented-control"><button type="button" className={mode==='generated'?'active':''} onClick={()=>changeMode('generated')}>Synthetisch</button><button type="button" className={mode==='upload'?'active':''} onClick={()=>changeMode('upload')}>DICOM-Datei</button></div>
     {mode==='generated'?<div className="query-fields"><FormField label="SOP Class" htmlFor="sop" className="span-all"><Select id="sop" value={sop} onChange={event=>changeSop(event.target.value)}>{sopClasses.map(item=><option value={item[0]} key={item[0]}>{item[1]}</option>)}</Select></FormField><FormField label="Transfer Syntax" htmlFor="syntax" className="span-all"><Select id="syntax" value={syntax} onChange={event=>changeSyntax(event.target.value)}><option value="explicit_vr_little_endian">Explicit VR Little Endian</option><option value="implicit_vr_little_endian">Implicit VR Little Endian</option></Select></FormField><AlertBox tone="info">Synthetische Testdaten, eindeutig als nicht diagnostisch gekennzeichnet.</AlertBox></div>:<><label className="dropzone"><input ref={fileInput} type="file" accept=".dcm,.dicom,application/dicom" onChange={event=>chooseFile(event.target.files?.[0])}/><FileUp size={30}/><span><strong>Datei hier ablegen oder auswählen</strong><small>DICOM (.dcm), maximal 50 MB</small></span></label>{file&&<div className="file-pill"><FileUp size={18}/><span><strong>{file.name}</strong><small>{(file.size/1024).toFixed(1)} KB</small></span><Button type="button" variant="ghost" aria-label="Datei entfernen" icon={<Trash2 size={16}/>} onClick={()=>chooseFile(undefined)}/></div>}{analysisPending&&<AlertBox tone="info">DICOM-Datei wird analysiert …</AlertBox>}{uploadError&&<AlertBox tone="error">{uploadError}</AlertBox>}</>}
     <div className="store-options"><Checkbox label="Metadaten vor dem Senden anzeigen" checked readOnly/><Checkbox label="Storage Commitment anfordern (nicht unterstützt)" disabled/><Checkbox label="Asynchron senden (nicht unterstützt)" disabled/></div>
     <div className="form-actions"><Button type="submit" loading={storePending} disabled={echoPending||analysisPending} icon={<Send size={17}/>}>C-STORE senden</Button></div>
    </SectionCard>
   </div>
   <div className="store-center">
    <SectionCard title="Transfer Status" action={result&&<span className={result.success?'success-text':'error-text'}>{result.success?'Erfolgreich':'Fehler'}</span>}>
     <TransferProgress loading={storePending} result={result} hasFile={mode==='generated'||Boolean(file)}/>
     {storeError&&<AlertBox tone="error" title="C-STORE Request fehlgeschlagen">{storeError}</AlertBox>}
     {result?<><TestResultSummary result={result} title={result.success?'C-STORE erfolgreich':undefined}/><div className="form-actions"><SaveTargetButton endpoint={endpoint} service="store"/></div></>:!storePending&&!storeError&&<div className="empty-state"><Send size={30}/><strong>Bereit zum Senden</strong><span>Ziel und Testdaten konfigurieren.</span></div>}
    </SectionCard>
    <SectionCard title="DICOM Log"><DicomLogViewer result={result} context={context}/></SectionCard>
   </div>
   <DicomMetadataPanel mode={mode} data={result??(mode==='upload'?uploadInfo:undefined)} file={mode==='upload'?file:undefined}/>
  </form>
 </>
}
