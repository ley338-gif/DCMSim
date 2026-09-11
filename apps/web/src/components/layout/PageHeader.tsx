import {ReactNode} from 'react'
import {ChevronRight} from 'lucide-react'
export function PageHeader({title,subtitle,breadcrumbs=[],actions}:{title:string;subtitle?:string;breadcrumbs?:string[];actions?:ReactNode}){return <header className="page-header"><div>{breadcrumbs.length>0&&<div className="breadcrumbs">{breadcrumbs.map((item,index)=><span key={item}>{item}{index<breadcrumbs.length-1&&<ChevronRight size={14}/>}</span>)}</div>}<h1>{title}</h1>{subtitle&&<p>{subtitle}</p>}</div>{actions&&<div className="page-header__actions">{actions}</div>}</header>}
