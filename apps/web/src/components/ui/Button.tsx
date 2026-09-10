import {ButtonHTMLAttributes,ReactNode} from 'react'
import {LoaderCircle} from 'lucide-react'

export type ButtonVariant='primary'|'secondary'|'outline'|'ghost'|'danger'
export function Button({variant='primary',loading=false,icon,children,className='',...props}:ButtonHTMLAttributes<HTMLButtonElement>&{variant?:ButtonVariant;loading?:boolean;icon?:ReactNode}){
 return <button className={`ui-button ui-button--${variant} ${className}`} disabled={loading||props.disabled} {...props}>{loading?<LoaderCircle className="spin" size={16}/>:icon}{children}</button>
}
