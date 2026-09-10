import {ReactNode} from 'react'
export function KeyValueList({items}:{items:{label:string;value:ReactNode;mono?:boolean}[]}){return <dl className="key-values">{items.map(item=><div key={item.label}><dt>{item.label}</dt><dd className={item.mono?'mono':''}>{item.value||'—'}</dd></div>)}</dl>}
