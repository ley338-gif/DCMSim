export function localDateString(date=new Date()):string{
 const year=date.getFullYear()
 const month=String(date.getMonth()+1).padStart(2,'0')
 const day=String(date.getDate()).padStart(2,'0')
 return `${year}-${month}-${day}`
}

export function localDayStartIso(value:string):string{
 const [year,month,day]=value.split('-').map(Number)
 return new Date(year,month-1,day).toISOString()
}

export function localDayAfterIso(value:string):string{
 const [year,month,day]=value.split('-').map(Number)
 return new Date(year,month-1,day+1).toISOString()
}
