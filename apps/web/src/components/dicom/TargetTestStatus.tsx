import {TargetTestStatus as TargetStatus} from '../../api/client'
import {StatusBadge} from '../ui/Status'

export function TargetTestStatus({status}:{status?:TargetStatus}){
 if(!status)return <div className="target-test-status"><StatusBadge tone="neutral">Ungeprüft</StatusBadge><small>Noch kein Einzeltest</small></div>
 return <div className="target-test-status"><StatusBadge tone={status.success?'success':'error'}>{status.success?'Erfolgreich':'Fehlgeschlagen'}</StatusBadge><small title={new Date(status.started_at).toLocaleString('de-DE')}>{new Date(status.started_at).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'})}</small></div>
}
