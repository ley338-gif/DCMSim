import {FormEvent,useState} from 'react'
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query'
import {Edit3,MapPin,Network,Plus,Radio,Server,Trash2} from 'lucide-react'
import {api,Area,DicomEndpoint,DicomSystem,FilterMode,ModalityCode,Site,WorklistChannel} from '../api/client'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {LoadingState} from '../components/ui/DataTable'
import {AlertBox} from '../components/ui/Feedback'
import {FormField,NumberInput,Select,TextInput} from '../components/ui/Form'
import {Modal} from '../components/ui/Overlay'

type Kind='site'|'area'|'system'|'endpoint'|'channel'
type Dialog={kind:Kind;id?:number}
const modalities:ModalityCode[]=['CT','MR','US','CR','DX','OT','XA','MG','NM','PT']
const modeLabels:Record<FilterMode,string>={profile:'Vom Profil',fixed:'Fester Wert',omit:'Nicht senden'}
type EndpointDraft={system_id:number;name:string;service:DicomEndpoint['service'];host:string;port:number;called_ae:string}
const emptyEndpoint:EndpointDraft={system_id:0,name:'',service:'MWL',host:'',port:104,called_ae:''}
const emptyChannel={name:'',area_id:null as number|null,modality_code:'CT' as ModalityCode,mwl_endpoint_id:0,station_ae_mode:'profile' as FilterMode,station_ae_fixed_value:null as string|null,modality_filter_mode:'profile' as FilterMode,modality_filter_fixed_value:null as string|null}

export function Topology(){
 const queryClient=useQueryClient()
 const sites=useQuery({queryKey:['sites'],queryFn:api.sites})
 const areas=useQuery({queryKey:['areas'],queryFn:api.areas})
 const systems=useQuery({queryKey:['dicom-systems'],queryFn:api.dicomSystems})
 const endpoints=useQuery({queryKey:['dicom-endpoints'],queryFn:api.dicomEndpoints})
 const channels=useQuery({queryKey:['worklist-channels'],queryFn:api.worklistChannels})
 const [dialog,setDialog]=useState<Dialog>()
 const [name,setName]=useState('')
 const [siteId,setSiteId]=useState(0)
 const [endpoint,setEndpoint]=useState(emptyEndpoint)
 const [channel,setChannel]=useState(emptyChannel)
 const invalidate=()=>Promise.all(['sites','areas','dicom-systems','dicom-endpoints','worklist-channels','modality-profiles'].map(key=>queryClient.invalidateQueries({queryKey:[key]})))
 const close=()=>{setDialog(undefined);setName('');setSiteId(0);setEndpoint(emptyEndpoint);setChannel(emptyChannel)}
 const save=useMutation({mutationFn:async()=>{
  if(!dialog)throw new Error('Kein Dialog geöffnet')
  if(dialog.kind==='site')return dialog.id?api.updateSite(dialog.id,{name}):api.createSite({name})
  if(dialog.kind==='area')return dialog.id?api.updateArea(dialog.id,{name,site_id:siteId}):api.createArea({name,site_id:siteId})
  if(dialog.kind==='system')return dialog.id?api.updateDicomSystem(dialog.id,{name}):api.createDicomSystem({name})
  if(dialog.kind==='endpoint'){
   const {system_id,...value}=endpoint
   return dialog.id?api.updateDicomEndpoint(dialog.id,value):api.createDicomEndpoint(system_id,value)
  }
  return dialog.id?api.updateWorklistChannel(dialog.id,channel):api.createWorklistChannel(channel)
 },onSuccess:async()=>{await invalidate();close()}})
 const remove=useMutation({mutationFn:async({kind,id}:{kind:Kind;id:number})=>{
  if(kind==='site')return api.deleteSite(id)
  if(kind==='area')return api.deleteArea(id)
  if(kind==='system')return api.deleteDicomSystem(id)
  if(kind==='endpoint')return api.deleteDicomEndpoint(id)
  return api.deleteWorklistChannel(id)
 },onSuccess:invalidate})
 const openNew=(kind:Kind,parentId?:number)=>{close();if(kind==='area')setSiteId(parentId??sites.data?.[0]?.id??0);if(kind==='endpoint')setEndpoint({...emptyEndpoint,system_id:parentId??systems.data?.[0]?.id??0});if(kind==='channel')setChannel({...emptyChannel,area_id:parentId??areas.data?.[0]?.id??null,mwl_endpoint_id:endpoints.data?.find(item=>item.service==='MWL')?.id??0});setDialog({kind})}
 const edit=(kind:Kind,item:Site|Area|DicomSystem|DicomEndpoint|WorklistChannel)=>{close();if(kind==='site'||kind==='system')setName(item.name);if(kind==='area'){const value=item as Area;setName(value.name);setSiteId(value.site_id)}if(kind==='endpoint'){const value=item as DicomEndpoint;setEndpoint({system_id:value.system_id,name:value.name,service:value.service,host:value.host,port:value.port,called_ae:value.called_ae})}if(kind==='channel'){const {id:_,created_at:__,updated_at:___,...value}=item as WorklistChannel;void _;void __;void ___;setChannel(value)}setDialog({kind,id:item.id})}
 const destroy=(kind:Kind,id:number,label:string)=>{if(confirm(`„${label}“ löschen? Verknüpfte Profile bleiben erhalten und werden entkoppelt.`))remove.mutate({kind,id})}
 const submit=(event:FormEvent)=>{event.preventDefault();save.mutate()}
 const loading=[sites,areas,systems,endpoints,channels].some(query=>query.isLoading)
 const failed=[sites,areas,systems,endpoints,channels].find(query=>query.error)
 const mwlEndpoints=(endpoints.data??[]).filter(item=>item.service==='MWL')
 const dialogTitle={site:'Standort',area:'Bereich',system:'DICOM-System',endpoint:'Endpoint',channel:'Worklist-Kanal'}[dialog?.kind??'site']
 return <>
  <PageHeader title="Standorte und DICOM-Systeme" subtitle="Organisation, technische Endpoints und Worklist-Zuordnung getrennt verwalten" actions={<div className="form-actions topology-actions"><Button icon={<MapPin size={16}/>} onClick={()=>openNew('site')}>Standort hinzufügen</Button><Button variant="outline" icon={<Server size={16}/>} onClick={()=>openNew('system')}>DICOM-System hinzufügen</Button></div>}/>
  {failed&&<AlertBox tone="error" title="Topologie konnte nicht geladen werden">{failed.error?.message}</AlertBox>}
  {loading?<LoadingState/>:!failed&&<div className="topology-layout">
   <SectionCard title="Standorte und Bereiche" subtitle="Organisatorische Struktur; Löschen entkoppelt Profile und Kanäle">
    {(sites.data??[]).map(site=><section className="topology-group" key={site.id}><div className="topology-heading"><h2><MapPin size={18}/>{site.name}</h2><div className="table-actions"><Button variant="ghost" aria-label={`${site.name} bearbeiten`} icon={<Edit3 size={15}/>} onClick={()=>edit('site',site)}/><Button variant="ghost" aria-label={`${site.name} löschen`} icon={<Trash2 size={15}/>} onClick={()=>destroy('site',site.id,site.name)}/><Button variant="outline" icon={<Plus size={15}/>} onClick={()=>openNew('area',site.id)}>Bereich</Button></div></div>{(areas.data??[]).filter(area=>area.site_id===site.id).map(area=><div className="topology-node" key={area.id}><div><strong>{area.name}</strong><small>{(channels.data??[]).filter(item=>item.area_id===area.id).length} Worklist-Kanäle</small></div><div className="table-actions"><Button variant="ghost" aria-label={`${area.name} bearbeiten`} icon={<Edit3 size={15}/>} onClick={()=>edit('area',area)}/><Button variant="ghost" aria-label={`${area.name} löschen`} icon={<Trash2 size={15}/>} onClick={()=>destroy('area',area.id,area.name)}/><Button variant="outline" icon={<Plus size={15}/>} onClick={()=>openNew('channel',area.id)}>Kanal</Button></div>{(channels.data??[]).filter(item=>item.area_id===area.id).map(item=><ChannelRow key={item.id} item={item} endpoint={endpoints.data?.find(value=>value.id===item.mwl_endpoint_id)} onEdit={()=>edit('channel',item)} onDelete={()=>destroy('channel',item.id,item.name)}/>)}</div>)}{!(areas.data??[]).some(area=>area.site_id===site.id)&&<p className="muted">Noch keine Bereiche.</p>}</section>)}
    {(sites.data??[]).length===0&&<div className="empty-state"><MapPin size={30}/><strong>Noch keine Standorte</strong><span>Lege zuerst einen Standort an.</span></div>}
    {(channels.data??[]).some(item=>item.area_id===null)&&<section className="topology-group"><div className="topology-heading"><h2>Nicht zugeordnet</h2></div>{(channels.data??[]).filter(item=>item.area_id===null).map(item=><ChannelRow key={item.id} item={item} endpoint={endpoints.data?.find(value=>value.id===item.mwl_endpoint_id)} onEdit={()=>edit('channel',item)} onDelete={()=>destroy('channel',item.id,item.name)}/>)}</section>}
   </SectionCard>
   <SectionCard title="Technische DICOM-Systeme" subtitle="Endpoints sind nach Dienst, Host, Port und Called AE definiert">
    {(systems.data??[]).map(system=><section className="topology-group" key={system.id}><div className="topology-heading"><h2><Server size={18}/>{system.name}</h2><div className="table-actions"><Button variant="ghost" aria-label={`${system.name} bearbeiten`} icon={<Edit3 size={15}/>} onClick={()=>edit('system',system)}/><Button variant="ghost" aria-label={`${system.name} löschen`} icon={<Trash2 size={15}/>} onClick={()=>destroy('system',system.id,system.name)}/><Button variant="outline" icon={<Plus size={15}/>} onClick={()=>openNew('endpoint',system.id)}>Endpoint</Button></div></div>{(endpoints.data??[]).filter(item=>item.system_id===system.id).map(item=><div className="topology-node topology-endpoint" key={item.id}><Network size={17}/><div><strong>{item.name} · {item.service}</strong><small><span className="mono">{item.host}:{item.port}</span> · Called AE <span className="mono">{item.called_ae}</span></small></div><div className="table-actions"><Button variant="ghost" aria-label={`${item.name} bearbeiten`} icon={<Edit3 size={15}/>} onClick={()=>edit('endpoint',item)}/><Button variant="ghost" aria-label={`${item.name} löschen`} icon={<Trash2 size={15}/>} onClick={()=>destroy('endpoint',item.id,item.name)}/></div></div>)}{!(endpoints.data??[]).some(item=>item.system_id===system.id)&&<p className="muted">Noch keine Endpoints.</p>}</section>)}
    {(systems.data??[]).length===0&&<div className="empty-state"><Server size={30}/><strong>Noch keine DICOM-Systeme</strong><span>Lege ein System und seine technischen Endpoints an.</span></div>}
   </SectionCard>
  </div>}
  <Modal open={Boolean(dialog)} title={`${dialog?.id?'Bearbeiten':'Neu'}: ${dialogTitle}`} size="lg" onClose={close}><form className="target-form" onSubmit={submit}>
   {(dialog?.kind==='site'||dialog?.kind==='system')&&<FormField label={dialog.kind==='site'?'Standortname':'Systemname'} htmlFor="node-name" className="span-all"><TextInput id="node-name" autoFocus required value={name} onChange={event=>setName(event.target.value)}/></FormField>}
   {dialog?.kind==='area'&&<><FormField label="Bereichsname" htmlFor="node-name"><TextInput id="node-name" autoFocus required value={name} onChange={event=>setName(event.target.value)}/></FormField><FormField label="Standort" htmlFor="area-site"><Select id="area-site" required value={siteId||''} onChange={event=>setSiteId(Number(event.target.value))}><option value="">Auswählen</option>{sites.data?.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</Select></FormField></>}
   {dialog?.kind==='endpoint'&&<><FormField label="DICOM-System" htmlFor="endpoint-system"><Select id="endpoint-system" required disabled={Boolean(dialog.id)} value={endpoint.system_id||''} onChange={event=>setEndpoint({...endpoint,system_id:Number(event.target.value)})}><option value="">Auswählen</option>{systems.data?.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</Select></FormField><FormField label="Endpointname" htmlFor="endpoint-name"><TextInput id="endpoint-name" required value={endpoint.name} onChange={event=>setEndpoint({...endpoint,name:event.target.value})}/></FormField><FormField label="Dienst" htmlFor="endpoint-service"><Select id="endpoint-service" value={endpoint.service} onChange={event=>setEndpoint({...endpoint,service:event.target.value as DicomEndpoint['service']})}>{['MWL','STORE','QR'].map(value=><option key={value}>{value}</option>)}</Select></FormField><FormField label="Host" htmlFor="endpoint-host"><TextInput id="endpoint-host" className="mono" required value={endpoint.host} onChange={event=>setEndpoint({...endpoint,host:event.target.value})}/></FormField><FormField label="Port" htmlFor="endpoint-port"><NumberInput id="endpoint-port" min={1} max={65535} required value={endpoint.port} onChange={event=>setEndpoint({...endpoint,port:Number(event.target.value)})}/></FormField><FormField label="Called AE" htmlFor="endpoint-ae"><TextInput id="endpoint-ae" className="mono" maxLength={16} required value={endpoint.called_ae} onChange={event=>setEndpoint({...endpoint,called_ae:event.target.value.toUpperCase()})}/></FormField></>}
   {dialog?.kind==='channel'&&<><FormField label="Kanalname" htmlFor="channel-name"><TextInput id="channel-name" required value={channel.name} onChange={event=>setChannel({...channel,name:event.target.value})}/></FormField><FormField label="Bereich" htmlFor="channel-area"><Select id="channel-area" value={channel.area_id??''} onChange={event=>setChannel({...channel,area_id:Number(event.target.value)||null})}><option value="">Nicht zugeordnet</option>{areas.data?.map(item=><option value={item.id} key={item.id}>{sites.data?.find(site=>site.id===item.site_id)?.name} · {item.name}</option>)}</Select></FormField><FormField label="Modalität" htmlFor="channel-modality"><Select id="channel-modality" value={channel.modality_code} onChange={event=>setChannel({...channel,modality_code:event.target.value as ModalityCode})}>{modalities.map(value=><option key={value}>{value}</option>)}</Select></FormField><FormField label="MWL-Endpoint" htmlFor="channel-endpoint"><Select id="channel-endpoint" required value={channel.mwl_endpoint_id||''} onChange={event=>setChannel({...channel,mwl_endpoint_id:Number(event.target.value)})}><option value="">Auswählen</option>{mwlEndpoints.map(item=><option value={item.id} key={item.id}>{systems.data?.find(system=>system.id===item.system_id)?.name} · {item.name}</option>)}</Select></FormField><ModeField id="station" label="Station AE" mode={channel.station_ae_mode} value={channel.station_ae_fixed_value} onChange={(mode,value)=>setChannel({...channel,station_ae_mode:mode,station_ae_fixed_value:value})}/><ModeField id="modality-filter" label="Modalitätsfilter" mode={channel.modality_filter_mode} value={channel.modality_filter_fixed_value} onChange={(mode,value)=>setChannel({...channel,modality_filter_mode:mode,modality_filter_fixed_value:value})}/></>}
   {save.error&&<div className="span-all"><AlertBox tone="error">{save.error.message}</AlertBox></div>}{remove.error&&<div className="span-all"><AlertBox tone="error">{remove.error.message}</AlertBox></div>}<div className="form-actions span-all"><Button type="button" variant="ghost" onClick={close}>Abbrechen</Button><Button type="submit" loading={save.isPending}>Speichern</Button></div>
  </form></Modal>
 </>
}

function ChannelRow({item,endpoint,onEdit,onDelete}:{item:WorklistChannel;endpoint?:DicomEndpoint;onEdit:()=>void;onDelete:()=>void}){return <div className="topology-node topology-channel"><Radio size={17}/><div><strong>{item.name} · {item.modality_code}</strong><small>{endpoint?`${endpoint.name} (${endpoint.host}:${endpoint.port})`:'MWL-Endpoint fehlt'} · Station AE: {modeLabels[item.station_ae_mode]} · Modalität: {modeLabels[item.modality_filter_mode]}</small></div><div className="table-actions"><Button variant="ghost" aria-label={`${item.name} bearbeiten`} icon={<Edit3 size={15}/>} onClick={onEdit}/><Button variant="ghost" aria-label={`${item.name} löschen`} icon={<Trash2 size={15}/>} onClick={onDelete}/></div></div>}
function ModeField({id,label,mode,value,onChange}:{id:string;label:string;mode:FilterMode;value:string|null;onChange:(mode:FilterMode,value:string|null)=>void}){return <div className="service-config"><FormField label={`${label}-Modus`} htmlFor={`${id}-mode`}><Select id={`${id}-mode`} value={mode} onChange={event=>onChange(event.target.value as FilterMode,event.target.value==='fixed'?value:null)}>{Object.entries(modeLabels).map(([key,text])=><option value={key} key={key}>{text}</option>)}</Select></FormField>{mode==='fixed'&&<FormField label={`${label}-Wert`} htmlFor={`${id}-value`}><TextInput id={`${id}-value`} maxLength={16} required value={value??''} onChange={event=>onChange(mode,event.target.value.toUpperCase())}/></FormField>}</div>}
