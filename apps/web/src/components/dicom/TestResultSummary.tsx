import {AlertTriangle,CheckCircle2,XCircle} from 'lucide-react'
import {Result} from '../../api/client'
import {StatusBadge,StatusTone} from '../ui/Status'
import {KeyValueList} from '../ui/KeyValueList'

export function TestResultSummary({result,title}:{result:Result;title?:string}){const warning=result.category==='warning';const tone:StatusTone=result.success?(warning?'warning':'success'):'error';const Icon=result.success?(warning?AlertTriangle:CheckCircle2):XCircle;return <div className={`result-summary result-summary--${tone}`}><div className="result-summary__headline"><Icon size={25}/><div><strong>{title??(result.success?'Test erfolgreich':result.message??'Test fehlgeschlagen')}</strong><span>{result.success?'Die Gegenstelle hat den DICOM-Vorgang beantwortet.':'Die Gegenstelle konnte den Vorgang nicht erfolgreich abschließen.'}</span></div><StatusBadge tone={tone}>{warning?'Warnung':result.success?'Erfolgreich':'Fehler'}</StatusBadge></div><KeyValueList items={[{label:'DICOM Status',value:result.status??result.code??'—',mono:true},{label:'Dauer',value:`${result.duration_ms} ms`},{label:'Antwort',value:result.message??(result.success?'Success':'Fehlgeschlagen')}]}/></div>}
