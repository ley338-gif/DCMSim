import {InputHTMLAttributes,ReactNode,SelectHTMLAttributes} from 'react'
export function FormField({label,htmlFor,hint,error,children,className=''}:{label:string;htmlFor?:string;hint?:string;error?:string;children:ReactNode;className?:string}){return <div className={`form-field ${className}`}><label htmlFor={htmlFor}>{label}</label>{children}{(hint||error)&&<small className={error?'field-error':''}>{error||hint}</small>}</div>}
export function TextInput(props:InputHTMLAttributes<HTMLInputElement>){return <input {...props} className={`text-input ${props.className??''}`}/>}
export function NumberInput(props:InputHTMLAttributes<HTMLInputElement>){return <TextInput type="number" {...props}/>}
export function DateInput(props:InputHTMLAttributes<HTMLInputElement>){return <TextInput type="date" {...props}/>}
export function Select({children,...props}:SelectHTMLAttributes<HTMLSelectElement>){return <select {...props} className={`select-input ${props.className??''}`}>{children}</select>}
export function Checkbox({label,...props}:InputHTMLAttributes<HTMLInputElement>&{label:string}){return <label className="checkbox"><input type="checkbox" {...props}/><span>{label}</span></label>}
export function Toggle({label,...props}:InputHTMLAttributes<HTMLInputElement>&{label:string}){return <label className="toggle"><input type="checkbox" {...props}/><span aria-hidden="true"/><b>{label}</b></label>}
