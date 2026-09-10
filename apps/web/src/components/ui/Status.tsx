import {ReactNode} from 'react'
export type StatusTone='success'|'warning'|'error'|'info'|'neutral'
export function StatusDot({tone='neutral'}:{tone?:StatusTone}){return <span aria-hidden="true" className={`status-dot status-dot--${tone}`}/>}
export function StatusBadge({tone='neutral',children}:{tone?:StatusTone;children:ReactNode}){return <span className={`status-badge status-badge--${tone}`}><StatusDot tone={tone}/>{children}</span>}
