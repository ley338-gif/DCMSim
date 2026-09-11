import {ChangeEvent,FormEvent,useState} from 'react'
import {useQueryClient} from '@tanstack/react-query'
import {Database,Download,Save,Trash2,Upload} from 'lucide-react'
import {api,ConfigurationExport} from '../api/client'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {AlertBox} from '../components/ui/Feedback'
import {FormField,NumberInput,Select,TextInput,Toggle} from '../components/ui/Form'

type Settings={callingAe:string;connectTimeout:number;associationTimeout:number;dimseTimeout:number;logLevel:string;retention:number;compact:boolean}
const defaults:Settings={callingAe:'DCMSIM',connectTimeout:5,associationTimeout:10,dimseTimeout:20,logLevel:'INFO',retention:90,compact:false}

function download(blob:Blob,name:string){const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();URL.revokeObjectURL(url)}

export function SettingsPage(){
 const queryClient=useQueryClient()
 const [section,setSection]=useState('DICOM')
 const [saved,setSaved]=useState(false)
 const [busy,setBusy]=useState(false)
 const [notice,setNotice]=useState<{tone:'success'|'error';text:string}>()
 const [value,setValue]=useState<Settings>(()=>{try{return {...defaults,...JSON.parse(localStorage.getItem('dcmsim-settings')??'{}')}}catch{return defaults}})
 const submit=(event:FormEvent)=>{event.preventDefault();localStorage.setItem('dcmsim-settings',JSON.stringify(value));setSaved(true);setTimeout(()=>setSaved(false),2000)}
 const run=async(action:()=>Promise<void>)=>{setBusy(true);setNotice(undefined);try{await action()}catch(error){setNotice({tone:'error',text:error instanceof Error?error.message:'Aktion fehlgeschlagen.'})}finally{setBusy(false)}}
 const exportConfig=()=>run(async()=>{const configuration=await api.exportConfiguration();download(new Blob([JSON.stringify(configuration,null,2)],{type:'application/json'}),`dcmsim-config-${new Date().toISOString().slice(0,10)}.json`);setNotice({tone:'success',text:'Konfiguration wurde exportiert.'})})
 const backup=()=>run(async()=>{download(await api.databaseBackup(),`dcmsim-backup-${new Date().toISOString().slice(0,10)}.sqlite3`);setNotice({tone:'success',text:'Datenbank-Backup wurde erstellt.'})})
 const importConfig=(event:ChangeEvent<HTMLInputElement>)=>{const file=event.target.files?.[0];event.target.value='';if(!file)return;void run(async()=>{const configuration=JSON.parse(await file.text()) as ConfigurationExport;const summary=await api.importConfiguration(configuration);await Promise.all([queryClient.invalidateQueries({queryKey:['targets']}),queryClient.invalidateQueries({queryKey:['modality-profiles']})]);setNotice({tone:'success',text:`Import abgeschlossen: ${summary.created_targets} Ziele und ${summary.created_profiles} Profile neu angelegt.`})})}
 const purge=()=>{if(!confirm(`Historieneinträge löschen, die älter als ${value.retention} Tage sind?`))return;void run(async()=>{localStorage.setItem('dcmsim-settings',JSON.stringify(value));const result=await api.purgeHistory(value.retention);await queryClient.invalidateQueries({queryKey:['runs']});setNotice({tone:'success',text:`${result.deleted_count} alte Historieneinträge wurden gelöscht.`})})}
 return <>
  <PageHeader title="Einstellungen" subtitle="Lokale Standardwerte, Datensicherung und Aufbewahrung konfigurieren"/>
  <div className="settings-layout"><SectionCard className="settings-nav">{['Allgemein','DICOM','Logging','Retention','Datensicherung','UI'].map(item=><button type="button" className={section===item?'active':''} aria-pressed={section===item} onClick={()=>{setSection(item);setNotice(undefined)}} key={item}>{item}</button>)}</SectionCard><SectionCard title={section}><form className="settings-panel" onSubmit={submit}>
   {section==='DICOM'&&<><FormField label="Default Calling AE" htmlFor="setting-ae"><TextInput id="setting-ae" className="mono" maxLength={16} value={value.callingAe} onChange={e=>setValue({...value,callingAe:e.target.value.toUpperCase()})}/></FormField><FormField label="Connect Timeout (Sekunden)" htmlFor="connect-timeout"><NumberInput id="connect-timeout" min={1} value={value.connectTimeout} onChange={e=>setValue({...value,connectTimeout:Number(e.target.value)})}/></FormField><FormField label="Association Timeout (Sekunden)" htmlFor="association-timeout"><NumberInput id="association-timeout" min={1} value={value.associationTimeout} onChange={e=>setValue({...value,associationTimeout:Number(e.target.value)})}/></FormField><FormField label="DIMSE Timeout (Sekunden)" htmlFor="dimse-timeout"><NumberInput id="dimse-timeout" min={1} value={value.dimseTimeout} onChange={e=>setValue({...value,dimseTimeout:Number(e.target.value)})}/></FormField><AlertBox tone="info">Serverseitige Timeouts werden über die lokale Container-Konfiguration gesetzt. Diese Werte sind lokale Benutzerstandards.</AlertBox></>}
   {section==='Logging'&&<><FormField label="Log Level" htmlFor="log-level"><Select id="log-level" value={value.logLevel} onChange={e=>setValue({...value,logLevel:e.target.value})}>{['DEBUG','INFO','WARNING','ERROR'].map(item=><option key={item}>{item}</option>)}</Select></FormField><AlertBox tone="info">Patientendatensätze werden nicht automatisch in das Application Log geschrieben.</AlertBox></>}
   {section==='Retention'&&<><FormField label="History Retention (Tage)" htmlFor="retention"><NumberInput id="retention" min={1} max={3650} value={value.retention} onChange={e=>setValue({...value,retention:Number(e.target.value)})}/></FormField><AlertBox tone="warning">Die Bereinigung wird bewusst manuell ausgeführt. Es gibt keinen Scheduler.</AlertBox><div className="form-actions span-all"><Button type="button" variant="danger" loading={busy} icon={<Trash2 size={16}/>} onClick={purge}>Alte Historie bereinigen</Button></div></>}
   {section==='Datensicherung'&&<><div className="backup-actions span-all"><Button type="button" variant="outline" loading={busy} icon={<Download size={16}/>} onClick={exportConfig}>Konfiguration exportieren</Button><label className="ui-button ui-button--outline"><Upload size={16}/>Konfiguration importieren<input type="file" aria-label="Konfigurationsdatei auswählen" accept="application/json,.json" onChange={importConfig}/></label><Button type="button" variant="outline" loading={busy} icon={<Database size={16}/>} onClick={backup}>SQLite-Backup erstellen</Button></div><AlertBox tone="info">Der Import aktualisiert gleichnamige Ziele und Profile oder legt sie neu an. Nicht enthaltene Einträge werden nicht gelöscht.</AlertBox></>}
   {section==='UI'&&<><Toggle label="Kompakte Tabellenansicht vorbereiten" checked={value.compact} onChange={e=>setValue({...value,compact:e.target.checked})}/><AlertBox tone="info">Dark Mode ist für eine spätere Version vorgesehen.</AlertBox></>}
   {section==='Allgemein'&&<><FormField label="Produktname" htmlFor="product"><TextInput id="product" value="DCMSim" disabled/></FormField><FormField label="Betriebsart" htmlFor="deployment"><TextInput id="deployment" value="On-Premise / Lokal" disabled/></FormField><AlertBox tone="success">Keine Telemetrie und keine externe Cloud-Verbindung.</AlertBox></>}
   {notice&&<div className="span-all"><AlertBox tone={notice.tone}>{notice.text}</AlertBox></div>}
   {section!=='Datensicherung'&&section!=='Retention'&&<div className="settings-actions span-all"><Button type="submit" icon={<Save size={16}/>}>Einstellungen speichern</Button>{saved&&<span className="success-text" role="status">Gespeichert</span>}</div>}
  </form></SectionCard></div>
 </>
}
