import {ChangeEvent,FormEvent,useState} from 'react'
import {useQuery,useQueryClient} from '@tanstack/react-query'
import {Database,Download,Save,Trash2,Upload} from 'lucide-react'
import {api,ConfigurationExport} from '../api/client'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {AlertBox} from '../components/ui/Feedback'
import {FormField,NumberInput,TextInput,Toggle} from '../components/ui/Form'
import {KeyValueList} from '../components/ui/KeyValueList'
import {loadLocalSettings,LocalSettings,saveLocalSettings} from '../settings/localSettings'

function download(blob:Blob,name:string){const url=URL.createObjectURL(blob);const anchor=document.createElement('a');anchor.href=url;anchor.download=name;anchor.click();URL.revokeObjectURL(url)}

export function SettingsPage(){
 const queryClient=useQueryClient()
 const [section,setSection]=useState('DICOM')
 const [saved,setSaved]=useState(false)
 const [busy,setBusy]=useState(false)
 const [notice,setNotice]=useState<{tone:'success'|'error';text:string}>()
 const [value,setValue]=useState<LocalSettings>(loadLocalSettings)
 const runtime=useQuery({queryKey:['runtime-settings'],queryFn:api.runtimeSettings})
 const submit=(event:FormEvent)=>{event.preventDefault();saveLocalSettings(value);setSaved(true);setTimeout(()=>setSaved(false),2000)}
 const run=async(action:()=>Promise<void>)=>{setBusy(true);setNotice(undefined);try{await action()}catch(error){setNotice({tone:'error',text:error instanceof Error?error.message:'Aktion fehlgeschlagen.'})}finally{setBusy(false)}}
 const exportConfig=()=>run(async()=>{const configuration=await api.exportConfiguration();download(new Blob([JSON.stringify(configuration,null,2)],{type:'application/json'}),`dcmsim-config-${new Date().toISOString().slice(0,10)}.json`);setNotice({tone:'success',text:'Konfiguration wurde exportiert.'})})
 const backup=()=>run(async()=>{download(await api.databaseBackup(),`dcmsim-backup-${new Date().toISOString().slice(0,10)}.sqlite3`);setNotice({tone:'success',text:'Datenbank-Backup wurde erstellt.'})})
 const importConfig=(event:ChangeEvent<HTMLInputElement>)=>{const file=event.target.files?.[0];event.target.value='';if(!file)return;void run(async()=>{const configuration=JSON.parse(await file.text()) as ConfigurationExport;const summary=await api.importConfiguration(configuration);await Promise.all([queryClient.invalidateQueries({queryKey:['targets']}),queryClient.invalidateQueries({queryKey:['modality-profiles']})]);setNotice({tone:'success',text:`Import abgeschlossen: ${summary.created_targets} Ziele und ${summary.created_profiles} Profile neu angelegt.`})})}
 const purge=()=>{if(!confirm(`Historieneinträge löschen, die älter als ${value.retention} Tage sind?`))return;void run(async()=>{saveLocalSettings(value);const result=await api.purgeHistory(value.retention);await queryClient.invalidateQueries({queryKey:['runs']});setNotice({tone:'success',text:`${result.deleted_count} alte Historieneinträge wurden gelöscht.`})})}
 return <>
  <PageHeader title="Einstellungen" subtitle="Lokale Standardwerte, Datensicherung und Aufbewahrung konfigurieren"/>
  <div className="settings-layout"><SectionCard className="settings-nav">{['Allgemein','DICOM','Logging','Retention','Datensicherung','UI'].map(item=><button type="button" className={section===item?'active':''} aria-pressed={section===item} onClick={()=>{setSection(item);setNotice(undefined)}} key={item}>{item}</button>)}</SectionCard><SectionCard title={section}><form className="settings-panel" onSubmit={submit}>
   {section==='DICOM'&&<><FormField label="Default Calling AE" htmlFor="setting-ae"><TextInput id="setting-ae" className="mono" maxLength={16} pattern="[A-Za-z0-9 _.-]{1,16}" required value={value.callingAe} onChange={e=>setValue({...value,callingAe:e.target.value.toUpperCase()})}/></FormField><div className="span-all"><strong>Wirksame Server-Timeouts</strong>{runtime.isPending?<p>Serverkonfiguration wird geladen …</p>:runtime.isError?<AlertBox tone="error">Serverkonfiguration konnte nicht geladen werden.</AlertBox>:<KeyValueList items={[{label:'Connect Timeout',value:`${runtime.data.connect_timeout} s`},{label:'Association Timeout',value:`${runtime.data.association_timeout} s`},{label:'DIMSE Timeout',value:`${runtime.data.dimse_timeout} s`}]}/>}</div><AlertBox tone="info">Das Default Calling AE wird nur in diesem Browser für neue Tests, Ziele und Modalitätsprofile vorbelegt. Timeouts werden über DCMSIM_CONNECT_TIMEOUT, DCMSIM_ASSOCIATION_TIMEOUT und DCMSIM_DIMSE_TIMEOUT im Container gesetzt; Änderungen erfordern einen Neustart.</AlertBox></>}
   {section==='Logging'&&<><div className="span-all"><strong>Wirksames Server-Log-Level</strong>{runtime.isPending?<p>Serverkonfiguration wird geladen …</p>:runtime.isError?<AlertBox tone="error">Serverkonfiguration konnte nicht geladen werden.</AlertBox>:<KeyValueList items={[{label:'Log Level',value:runtime.data.log_level}]}/>}</div><AlertBox tone="info">Das Log Level wird über DCMSIM_LOG_LEVEL im Container gesetzt; Änderungen erfordern einen Neustart. Patientendatensätze werden nicht automatisch in das Application Log geschrieben.</AlertBox></>}
   {section==='Retention'&&<><FormField label="History Retention (Tage)" htmlFor="retention"><NumberInput id="retention" min={1} max={3650} value={value.retention} onChange={e=>setValue({...value,retention:Number(e.target.value)})}/></FormField><AlertBox tone="warning">Die Bereinigung wird bewusst manuell ausgeführt. Es gibt keinen Scheduler.</AlertBox><div className="form-actions span-all"><Button type="button" variant="danger" loading={busy} icon={<Trash2 size={16}/>} onClick={purge}>Alte Historie bereinigen</Button></div></>}
   {section==='Datensicherung'&&<><div className="backup-actions span-all"><Button type="button" variant="outline" loading={busy} icon={<Download size={16}/>} onClick={exportConfig}>Konfiguration exportieren</Button><label className="ui-button ui-button--outline"><Upload size={16}/>Konfiguration importieren<input type="file" aria-label="Konfigurationsdatei auswählen" accept="application/json,.json" onChange={importConfig}/></label><Button type="button" variant="outline" loading={busy} icon={<Database size={16}/>} onClick={backup}>SQLite-Backup erstellen</Button></div><AlertBox tone="info">Der Import aktualisiert gleichnamige Ziele und Profile oder legt sie neu an. Nicht enthaltene Einträge werden nicht gelöscht.</AlertBox></>}
   {section==='UI'&&<><Toggle label="Kompakte Tabellenansicht" checked={value.compact} onChange={e=>setValue({...value,compact:e.target.checked})}/><AlertBox tone="info">Die kompakte Ansicht wird nach dem Speichern sofort auf alle Tabellen angewendet. Dark Mode ist für eine spätere Version vorgesehen.</AlertBox></>}
   {section==='Allgemein'&&<><FormField label="Produktname" htmlFor="product"><TextInput id="product" value="DCMSim" disabled/></FormField><FormField label="Betriebsart" htmlFor="deployment"><TextInput id="deployment" value="On-Premise / Lokal" disabled/></FormField><AlertBox tone="success">Keine Telemetrie und keine externe Cloud-Verbindung.</AlertBox></>}
   {notice&&<div className="span-all"><AlertBox tone={notice.tone}>{notice.text}</AlertBox></div>}
   {(section==='DICOM'||section==='UI')&&<div className="settings-actions span-all"><Button type="submit" icon={<Save size={16}/>}>Einstellungen speichern</Button>{saved&&<span className="success-text" role="status">Gespeichert</span>}</div>}
  </form></SectionCard></div>
 </>
}
