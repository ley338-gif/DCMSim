import {describe,expect,it} from 'vitest'
import {localDateString,localDayAfterIso,localDayStartIso} from '../utils/dates'

describe('local DICOM date default',()=>{
 it('uses the browser calendar date rather than the UTC date',()=>{
  expect(localDateString(new Date(2026,8,12,0,30))).toBe('2026-09-12')
  expect(localDateString(new Date(2026,8,12,23,30))).toBe('2026-09-12')
 })
})

it('uses consecutive local midnights for history date bounds',()=>{
 expect(localDayStartIso('2026-09-12')).toBe(new Date(2026,8,12).toISOString())
 expect(localDayAfterIso('2026-09-12')).toBe(new Date(2026,8,13).toISOString())
})
