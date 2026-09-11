import {KeyboardEvent as ReactKeyboardEvent,ReactNode,useEffect,useRef} from 'react'
import {X} from 'lucide-react'
import {Button} from './Button'

const focusable='button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])'

export function Modal({open,title,children,onClose,size='md'}:{open:boolean;title:string;children:ReactNode;onClose:()=>void;size?:'sm'|'md'|'lg'}){
 const panel=useRef<HTMLElement>(null)
 const closeRef=useRef(onClose)
 closeRef.current=onClose
 useEffect(()=>{
  if(!open)return
  const previous=document.activeElement as HTMLElement|null
  const close=(event:KeyboardEvent)=>event.key==='Escape'&&closeRef.current()
  window.addEventListener('keydown',close)
  const frame=requestAnimationFrame(()=>{const target=panel.current?.querySelector<HTMLElement>('[autofocus]')??panel.current?.querySelector<HTMLElement>(focusable);target?.focus()})
  return()=>{cancelAnimationFrame(frame);window.removeEventListener('keydown',close);previous?.focus()}
 },[open])
 const trapFocus=(event:ReactKeyboardEvent)=>{
  if(event.key!=='Tab'||!panel.current)return
  const elements=[...panel.current.querySelectorAll<HTMLElement>(focusable)]
  if(!elements.length)return
  const first=elements[0],last=elements[elements.length-1]
  if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus()}
  else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus()}
 }
 if(!open)return null
 return <div className="modal-backdrop" role="presentation" onMouseDown={event=>event.target===event.currentTarget&&onClose()}><section ref={panel} className={`modal-panel modal-panel--${size}`} role="dialog" aria-modal="true" aria-labelledby="modal-title" onKeyDown={trapFocus}><div className="modal-header"><h2 id="modal-title">{title}</h2><Button variant="ghost" aria-label="Dialog schließen" onClick={onClose} icon={<X size={20}/>}/></div>{children}</section></div>
}
