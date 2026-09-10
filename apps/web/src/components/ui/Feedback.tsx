import {ReactNode} from 'react'
import {AlertTriangle,CheckCircle2,Info,XCircle} from 'lucide-react'
import {StatusTone} from './Status'
const icons={success:CheckCircle2,warning:AlertTriangle,error:XCircle,info:Info,neutral:Info}
export function AlertBox({tone='info',title,children}:{tone?:StatusTone;title?:string;children:ReactNode}){const Icon=icons[tone];return <div className={`alert-box alert-box--${tone}`}><Icon size={19}/><div>{title&&<strong>{title}</strong>}<div>{children}</div></div></div>}
