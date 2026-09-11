import {FormEvent,useState} from 'react'
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query'
import {Edit3,Plus,RotateCcw,Square,Stethoscope,Trash2} from 'lucide-react'
import {api,ModalityCheckResult,ModalityProfile,ModalityProfileDraft,Target} from '../api/client'
import {ModalityCheckResultPanel} from '../components/dicom/ModalityCheckResult'
import {PageHeader} from '../components/layout/PageHeader'
import {Button} from '../components/ui/Button'
import {SectionCard} from '../components/ui/Card'
import {LoadingState} from '../components/ui/DataTable'
import {AlertBox} from '../components/ui/Feedback'
import {Checkbox,FormField,Select,TextInput} from '../components/ui/Form'
import {Modal} from '../components/ui/Overlay'
import {StatusBadge} from '../components/ui/Status'

const modalities=['CT','MR','US','CR','DX','OT','XA','MG','NM','PT'] as const
const blank:ModalityProfileDraft={name:'',description:null,modality:'CT',calling_ae:'DCMSIM',mwl_enabled:true,mwl_target_id:null,store_enabled:true,store_target_id:null}
const targetName=(targets:Target[],id:number|null)=>targets.find(target=>target.id===id)?.name??(id?'Gelöschtes Ziel':'Nicht konfiguriert')
const profileReady=(profile:ModalityProfile)=>(!profile.mwl_enabled||Boolean(profile.mwl_target_id))&&(!profile.store_enabled||Boolean(profile.store_target_id))

export function Modalities(){
 const client=useQueryClient()
 const profiles=useQuery({queryKey:['modality-profiles'],queryFn:api.modalityProfiles})
 const targets=useQuery({queryKey:['targets'],queryFn:api.targets})
 const [draft,setDraft]=useState<ModalityProfileDraft>(blank)
 const [editing,setEditing]=useState<number>()
 const [open,setOpen]=useState(false)
 const [result,setResult]=useState<ModalityCheckResult>()
 const [selected,setSelected]=useState<ModalityProfile>()
 const [controller,setController]=useState<AbortController>()
 const [cancelled,setCancelled]=useState(false)
 const close=()=>{setOpen(false);setEditing(undefined);setDraft(blank)}
 const save=useMutation({mutationFn:()=>editing?api.updateModalityProfile(editing,draft):api.createModalityProfile(draft),onSuccess:()=>{client.invalidateQueries({queryKey:['modality-profiles']});close()}})
 const remove=useMutation({mutationFn:api.deleteModalityProfile,onSuccess:()=>client.invalidateQueries({queryKey:['modality-profiles']})})
 const check=useMutation({
  mutationFn:({profile,signal}:{profile:ModalityProfile;signal:AbortSignal})=>api.checkModalityProfile(profile.id,'explicit_vr_little_endian',signal),
  onMutate:({profile})=>{setSelected(profile);setResult(undefined);setCancelled(false)},
  onSuccess:value=>{setResult(value);client.invalidateQueries({queryKey:['runs']})},
  onSettled:()=>setController(undefined),
 })
 const startCheck=(profile:ModalityProfile)=>{const next=new AbortController();setController(next);check.mutate({profile,signal:next.signal})}
 const cancelCheck=()=>{controller?.abort();check.reset();setCancelled(true)}
 const edit=(profile:ModalityProfile)=>{const {id,created_at:_,updated_at:__,...value}=profile;void _;void __;setEditing(id);setDraft(value);setOpen(true)}
 const submit=(event:FormEvent)=>{event.preventDefault();save.mutate()}
 const availableTargets=targets.data??[]
 return <>
  <PageHeader title="Modalitäten" subtitle="Geräteprofile anlegen und Worklist sowie PACS Store gemeinsam prüfen" actions={<Button icon={<Plus size={17}/>} onClick={()=>setOpen(true)}>Neue Modalität</Button>}/>
  {profiles.isLoading||targets.isLoading?<LoadingState/>:<div className="modality-grid">{(profiles.data??[]).map(profile=>{const ready=profileReady(profile);return <SectionCard key={profile.id} className="modality-card"><div className="modality-card__header"><div className="modality-icon"><Stethoscope size={23}/></div><div><h2>{profile.name}</h2><span>{profile.modality}</span></div><StatusBadge tone={ready?'success':'warning'}>{ready?'Konfiguriert':'Ziel fehlt'}</StatusBadge></div>{profile.description&&<p>{profile.description}</p>}<dl className="profile-details"><div><dt>Calling AE</dt><dd className="mono">{profile.calling_ae}</dd></div><div><dt>Worklist</dt><dd>{profile.mwl_enabled?targetName(availableTargets,profile.mwl_target_id):'Inaktiv'}</dd></div><div><dt>PACS Store</dt><dd>{profile.store_enabled?targetName(availableTargets,profile.store_target_id):'Inaktiv'}</dd></div></dl>{!ready&&<AlertBox tone="warning" title="Konfiguration unvollständig">Profil bearbeiten und für jeden aktiven Dienst ein Ziel auswählen.</AlertBox>}<div className="form-actions"><Button disabled={!ready} loading={check.isPending&&selected?.id===profile.id} icon={<Stethoscope size={16}/>} onClick={()=>startCheck(profile)}>Modalität prüfen</Button><Button variant="outline" icon={<Edit3 size={16}/>} onClick={()=>edit(profile)}>Bearbeiten</Button><Button variant="ghost" aria-label={`${profile.name} löschen`} icon={<Trash2 size={16}/>} onClick={()=>{if(confirm(`Modalität „${profile.name}“ löschen?`))remove.mutate(profile.id)}}/></div></SectionCard>})}{profiles.data?.length===0&&<SectionCard className="modality-empty"><Stethoscope size={34}/><strong>Noch keine Modalitätsprofile</strong><span>Lege ein Geräteprofil an und verknüpfe vorhandene DICOM-Ziele.</span></SectionCard>}</div>}
  {check.isPending&&<SectionCard><div className="loading-state" role="status" aria-live="polite"><span className="loader"/><strong>{selected?.name} wird geprüft</strong><span>Worklist und PACS Store werden nacheinander getestet …</span><Button variant="outline" icon={<Square size={14}/>} onClick={cancelCheck}>Anzeige abbrechen</Button></div></SectionCard>}
  {cancelled&&!check.isPending&&<AlertBox tone="info" title="Anzeige abgebrochen">Der laufende Netzwerkvorgang kann serverseitig noch beendet und in der Historie gespeichert werden.</AlertBox>}
  {check.error&&!cancelled&&<AlertBox tone="error" title="Modalitätsprüfung konnte nicht gestartet werden">{check.error.message}</AlertBox>}
  {result&&<SectionCard title="Prüfergebnis" action={selected&&<Button variant="outline" icon={<RotateCcw size={16}/>} onClick={()=>startCheck(selected)}>Erneut prüfen</Button>}><div aria-live="polite"><ModalityCheckResultPanel result={result}/></div></SectionCard>}
  <Modal open={open} title={editing?'Modalität bearbeiten':'Neue Modalität'} size="lg" onClose={close}><form className="target-form" onSubmit={submit}><FormField label="Name" htmlFor="profile-name" className="span-all"><TextInput id="profile-name" autoFocus required value={draft.name} placeholder="z. B. Aplio 300 – Sono 2" onChange={event=>setDraft({...draft,name:event.target.value})}/></FormField><FormField label="Beschreibung (optional)" htmlFor="profile-description" className="span-all"><TextInput id="profile-description" value={draft.description??''} onChange={event=>setDraft({...draft,description:event.target.value||null})}/></FormField><FormField label="Modalität" htmlFor="profile-modality"><Select id="profile-modality" value={draft.modality} onChange={event=>setDraft({...draft,modality:event.target.value as ModalityProfileDraft['modality']})}>{modalities.map(modality=><option key={modality}>{modality}</option>)}</Select></FormField><FormField label="Calling AE" htmlFor="profile-calling"><TextInput id="profile-calling" required maxLength={16} pattern="[A-Za-z0-9 _.-]{1,16}" className="mono" value={draft.calling_ae} onChange={event=>setDraft({...draft,calling_ae:event.target.value.toUpperCase()})}/></FormField><div className="profile-service span-all"><Checkbox label="Worklist aktiv" checked={draft.mwl_enabled} onChange={event=>setDraft({...draft,mwl_enabled:event.target.checked,mwl_target_id:event.target.checked?draft.mwl_target_id:null})}/><FormField label="Worklist Target" htmlFor="profile-mwl"><Select id="profile-mwl" disabled={!draft.mwl_enabled} required={draft.mwl_enabled} value={draft.mwl_target_id??''} onChange={event=>setDraft({...draft,mwl_target_id:Number(event.target.value)||null})}><option value="">Ziel auswählen</option>{availableTargets.filter(target=>target.mwl_enabled).map(target=><option value={target.id} key={target.id}>{target.name}</option>)}</Select></FormField></div><div className="profile-service span-all"><Checkbox label="Store aktiv" checked={draft.store_enabled} onChange={event=>setDraft({...draft,store_enabled:event.target.checked,store_target_id:event.target.checked?draft.store_target_id:null})}/><FormField label="Store Target" htmlFor="profile-store"><Select id="profile-store" disabled={!draft.store_enabled} required={draft.store_enabled} value={draft.store_target_id??''} onChange={event=>setDraft({...draft,store_target_id:Number(event.target.value)||null})}><option value="">Ziel auswählen</option>{availableTargets.filter(target=>target.store_enabled).map(target=><option value={target.id} key={target.id}>{target.name}</option>)}</Select></FormField></div>{availableTargets.length===0&&<AlertBox tone="warning">Lege zuerst unter „Ziele“ mindestens einen DICOM-Endpunkt an.</AlertBox>}{save.error&&<AlertBox tone="error">{save.error.message}</AlertBox>}<div className="form-actions span-all"><span className="flex-spacer"/><Button type="button" variant="ghost" onClick={close}>Abbrechen</Button><Button type="submit" loading={save.isPending}>Speichern</Button></div></form></Modal>
 </>
}
