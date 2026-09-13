import {TargetTestStatus as TargetStatus} from '../../api/client'
import {Link} from 'react-router-dom'
import {StatusBadge} from '../ui/Status'

const testLabels:Record<string,string>={mwl_find:'Worklist C-FIND',qr_find:'PACS C-FIND',dicom_store:'C-STORE',dicom_echo:'C-ECHO'}

export function TargetTestStatus({status}:{status?:TargetStatus}){
 if(!status)return <div className="target-test-status"><StatusBadge tone="neutral">Ungeprüft</StatusBadge><small>Noch kein Einzeltest</small></div>
 const type=testLabels[status.test_type]??status.test_type
 const date=new Date(status.started_at).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'})
 const explanation=status.configuration_state==='changed'?'Ziel seit Test geändert':status.configuration_state==='unknown'?'Alten Test erneut durchführen':null
 const badge=status.configuration_state==='changed'?<StatusBadge tone="warning">Erneut prüfen</StatusBadge>:status.configuration_state==='unknown'?<StatusBadge tone="neutral">Nicht belegbar</StatusBadge>:<StatusBadge tone={status.success?'success':'error'}>{status.success?'Erfolgreich':'Fehlgeschlagen'}</StatusBadge>
 return <div className="target-test-status">{badge}<div className="target-test-status__meta">{explanation&&<small>{explanation}</small>}<Link to={`/history/${status.run_id}`} title={new Date(status.started_at).toLocaleString('de-DE')}>{type} · {date}</Link></div></div>
}
