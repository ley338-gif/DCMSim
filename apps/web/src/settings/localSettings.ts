export type LocalSettings={
 callingAe:string
 connectTimeout:number
 associationTimeout:number
 dimseTimeout:number
 logLevel:string
 retention:number
 compact:boolean
}

export const localSettingsDefaults:LocalSettings={callingAe:'DCMSIM',connectTimeout:5,associationTimeout:10,dimseTimeout:20,logLevel:'INFO',retention:90,compact:false}
const storageKey='dcmsim-settings'
const aePattern=/^[A-Z0-9 _.-]{1,16}$/
const logLevels=['DEBUG','INFO','WARNING','ERROR']

function numberInRange(value:unknown,fallback:number,min:number,max:number){return typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max?value:fallback}

export function loadLocalSettings():LocalSettings{
 try{
  const stored=JSON.parse(localStorage.getItem(storageKey)??'{}') as Partial<LocalSettings>
  const callingAe=typeof stored.callingAe==='string'?stored.callingAe.trim().toUpperCase():''
  return {
   callingAe:aePattern.test(callingAe)?callingAe:localSettingsDefaults.callingAe,
   connectTimeout:numberInRange(stored.connectTimeout,localSettingsDefaults.connectTimeout,1,120),
   associationTimeout:numberInRange(stored.associationTimeout,localSettingsDefaults.associationTimeout,1,120),
   dimseTimeout:numberInRange(stored.dimseTimeout,localSettingsDefaults.dimseTimeout,1,300),
   logLevel:typeof stored.logLevel==='string'&&logLevels.includes(stored.logLevel)?stored.logLevel:localSettingsDefaults.logLevel,
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
