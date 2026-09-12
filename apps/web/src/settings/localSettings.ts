export type LocalSettings={
 callingAe:string
 retention:number
 compact:boolean
}

export const localSettingsDefaults:LocalSettings={callingAe:'DCMSIM',retention:90,compact:false}
const storageKey='dcmsim-settings'
const aePattern=/^[A-Z0-9 _.-]{1,16}$/

function numberInRange(value:unknown,fallback:number,min:number,max:number){return typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max?value:fallback}

export function loadLocalSettings():LocalSettings{
 try{
  const stored=JSON.parse(localStorage.getItem(storageKey)??'{}') as Partial<LocalSettings>
  const callingAe=typeof stored.callingAe==='string'?stored.callingAe.trim().toUpperCase():''
  return {
   callingAe:aePattern.test(callingAe)?callingAe:localSettingsDefaults.callingAe,
   retention:numberInRange(stored.retention,localSettingsDefaults.retention,1,3650),
   compact:typeof stored.compact==='boolean'?stored.compact:localSettingsDefaults.compact,
  }
 }catch{return {...localSettingsDefaults}}
}

export function applyLocalAppearance(settings:LocalSettings){document.documentElement.classList.toggle('compact-tables',settings.compact)}

export function saveLocalSettings(settings:LocalSettings){
 localStorage.setItem(storageKey,JSON.stringify(settings))
 applyLocalAppearance(settings)
}
